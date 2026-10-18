import json
import os
import subprocess
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from server import Handler
import test_lab_execution_reviews as fixtures


class LabApiTests(unittest.TestCase):
    def setUp(self):
        fixtures.BlindReviewTests.setUp(self)
        self.server=ThreadingHTTPServer(("127.0.0.1",0),Handler);self.server.api_token="lab-test-token"
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        fixtures.BlindReviewTests.tearDown(self)

    def request(self,path,body=None,headers=None):
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,
              headers={"Authorization":"Bearer lab-test-token","Content-Type":"application/json",**(headers or {})})
        with urllib.request.urlopen(req) as r:return r.status,json.load(r)

    def test_profile_experiment_audit_and_review_cli_parity_without_provider(self):
        with patch("alpaca._request",side_effect=AssertionError("no provider access")):
            for command,path in (("lab-profiles","/api/lab/profiles"),("lab-experiments","/api/lab/experiments"),("lab-reviews","/api/lab/reviews")):
                response=self.request(path)[1]
                result=json.loads(subprocess.check_output([sys.executable,"tori.py",command],env=os.environ))
                self.assertEqual(response,result)
            pack=self.pack["id"];case=self.pack["cases"][0]["id"]
            view=self.request(f"/api/lab/reviews/{pack}/{case}")[1]
            self.assertNotIn("engine",view)
            self.request(f"/api/lab/reviews/{pack}/{case}/label",{"entry":"wait","red":None,"green":None,"reason":"Waiting for convincing structure"})
            self.assertIn("engine",self.request(f"/api/lab/reviews/{pack}/{case}/reveal",{})[1])
            self.assertEqual(self.request(f"/api/lab/reviews/{pack}/compare")[1]["counts"]["wait"],1)
            identity=self.job["spec"]["lab"]["experiment_id"]
            self.assertEqual(self.request(f"/api/lab/experiments/{identity}")[1]["id"],identity)
            journal=self.request(f"/api/lab/experiments/{identity}/audit?limit=1")[1]
            self.assertEqual(len(journal["items"]),1)

    def test_new_routes_retain_auth_origin_limits_and_reject_unknown_operations(self):
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(self.url+"/api/lab/profiles")
        self.assertEqual(error.exception.code,401)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request("/api/lab/reviews",{"job":self.job["id"]},{"Origin":"https://foreign.example"})
        self.assertEqual(error.exception.code,403)
        cases=[("/api/lab/reviews",{"job":self.job["id"],"count":1001},400),
               ("/api/lab/reviews",[],400),("/api/lab/unknown",{},404),
               (f"/api/lab/reviews/{self.pack['id']}/{self.pack['cases'][0]['id']}/reveal",{},409)]
        for path,body,status in cases:
            with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as error:self.request(path,body)
            self.assertEqual(error.exception.code,status)
        for path in ("/lab_registry.py","/lab_execution.py","/data/research/jobs.sqlite3"):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path)
            self.assertEqual(error.exception.code,404)
        for path in ("/lab","/lab.js","/lab.css"):
            req=urllib.request.Request(self.url+path,headers={"Authorization":"Bearer lab-test-token"})
            with urllib.request.urlopen(req) as response:self.assertEqual(response.status,200)


if __name__=="__main__":unittest.main()
