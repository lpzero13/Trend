import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from models import DataError
from strategy_run_lock import study_lock


class StrategyLockTests(unittest.TestCase):
    def test_lock_rejects_second_writer_and_releases_after_exception(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name)/"study"
            with self.assertRaises(RuntimeError):
                with study_lock(output):
                    with self.assertRaises(DataError):
                        with study_lock(output):
                            pass
                    raise RuntimeError("simulated worker failure")
            with study_lock(output):
                self.assertFalse(output.exists())

    def test_killed_process_does_not_leave_stale_lock(self):
        with tempfile.TemporaryDirectory() as name:
            output = str(Path(name)/"study")
            code = "import sys,time\nfrom strategy_run_lock import study_lock\nwith study_lock(sys.argv[1]):\n print('ready',flush=True)\n time.sleep(60)\n"
            proc = subprocess.Popen([sys.executable,"-c",code,output],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
            try:
                self.assertEqual(proc.stdout.readline().strip(),"ready")
                with self.assertRaises(DataError):
                    with study_lock(output):
                        pass
            finally:
                proc.kill()
                proc.communicate(timeout=10)
            with study_lock(output):
                pass


if __name__ == "__main__":
    unittest.main()
