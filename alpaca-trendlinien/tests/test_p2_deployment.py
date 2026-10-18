"""Real subprocess deployment: read-only code, external state, proxy auth and offline worker."""
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from datasets import save_dataset
from test_research import fixture_sources


class DeploymentTests(unittest.TestCase):
    def test_internal_proxy_preserves_login_free_ui_and_backend_origin_checks(self):
        source=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);code=base/"code";code.mkdir();state=base/"state"
            for path in source.glob("*.py"): shutil.copyfile(path,code/path.name)
            shutil.copyfile(source/"requirements.txt",code/"requirements.txt")
            shutil.copytree(source/"static",code/"static")
            env={**os.environ,"TORI_DATA_DIR":str(state),"TORI_AUTO_ENABLED":"0","PYTHONDONTWRITEBYTECODE":"1",
                 "TORI_API_TOKEN":"deployment-test-only","ALPACA_CREDENTIALS_FILE":str(base/"absent.txt"),"PYTHONPATH":str(code),"PYTHONUTF8":"1"}
            env.pop("APCA_API_KEY_ID",None)
            env.pop("APCA_API_SECRET_KEY",None)
            with patch.dict(os.environ,env): identity=save_dataset("TEST",fixture_sources())
            token=env["TORI_API_TOKEN"]
            backend=[None]
            class Proxy(BaseHTTPRequestHandler):
                def log_message(self,*args): pass
                def forward(self):
                    body=self.rfile.read(int(self.headers.get("Content-Length","0"))) if self.command=="POST" else None
                    headers={key:self.headers[key] for key in ("Host","Origin","Content-Type") if key in self.headers}
                    headers["Authorization"]="Bearer "+token
                    request=urllib.request.Request(backend[0]+self.path,data=body,headers=headers,method=self.command)
                    try: result=urllib.request.urlopen(request)
                    except urllib.error.HTTPError as error: result=error
                    with result:
                        content=result.read();self.send_response(result.status)
                        self.send_header("Content-Length",str(len(content)));self.end_headers();self.wfile.write(content)
                do_GET=forward
                do_POST=forward
            proxy=ThreadingHTTPServer(("127.0.0.1",0),Proxy)
            proxy_url=f"http://127.0.0.1:{proxy.server_port}"
            thread=threading.Thread(target=proxy.serve_forever,daemon=True);thread.start()
            child=None
            try:
                for path in code.rglob("*"): path.chmod(0o555 if path.is_dir() else 0o444)
                code.chmod(0o555)
                child=subprocess.Popen([sys.executable,"-u",str(code/"server.py"),"--port","0","--no-worker","--allowed-host",f"127.0.0.1:{proxy.server_port}"],
                    cwd=code,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                line=child.stdout.readline()
                match=re.search(r"http://127\.0\.0\.1:\d+",line)
                self.assertIsNotNone(match,line)
                backend[0]=match.group(0)
                with urllib.request.urlopen(proxy_url+"/") as response:
                    text=response.read().decode();self.assertEqual(response.status,200)
                    self.assertNotIn(token,text)
                with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(backend[0]+"/api/health")
                self.assertEqual(error.exception.code,401)
                bad=urllib.request.Request(proxy_url+"/api/research/jobs",data=b"{}",headers={"Origin":"https://foreign.example","Content-Type":"application/json"})
                with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(bad)
                self.assertEqual(error.exception.code,403)
                spec={"symbols":["TEST"],"samples":1,"dataset_ids":{"TEST":identity}}
                request=urllib.request.Request(proxy_url+"/api/research/jobs",data=json.dumps(spec).encode(),headers={"Origin":proxy_url,"Content-Type":"application/json"})
                with urllib.request.urlopen(request) as response: job=json.load(response)
                subprocess.run([sys.executable,str(code/"tori.py"),"worker","--once"],cwd=code,env=env,check=True,
                    stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=30,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                with urllib.request.urlopen(proxy_url+"/api/research/jobs/"+job["id"]) as response:
                    self.assertEqual(json.load(response)["status"],"succeeded")
                self.assertTrue((state/"research/jobs.sqlite3").exists())
                self.assertFalse((code/"data").exists())
                self.assertFalse((code/"__pycache__").exists())
                if os.name!="nt" and os.geteuid()!=0:
                    with self.assertRaises(PermissionError): (code/"forbidden.txt").write_text("no")
            finally:
                if child:
                    child.terminate();child.wait(timeout=10)
                    child.stdout.close();child.stderr.close()
                proxy.shutdown();proxy.server_close();thread.join()
                code.chmod(0o755)
                for path in code.rglob("*"): path.chmod(0o755 if path.is_dir() else 0o644)


if __name__=="__main__": unittest.main()
