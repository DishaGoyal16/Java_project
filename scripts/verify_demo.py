"""Verify fresh and repeated demo setup; refuse to touch an existing demo database."""
import os, secrets, sqlite3, subprocess, sys
from contextlib import closing
from pathlib import Path
root=Path(__file__).resolve().parents[1]
db=root/'.local/demo.db';db.parent.mkdir(exist_ok=True)
if db.exists():raise SystemExit('Existing demo.db found; refusing to overwrite it')
env=os.environ.copy();password=secrets.token_urlsafe(24)
env.update(DATABASE_URL='sqlite:///'+db.as_posix(),SCMS_DEMO_DATABASE='1',SCMS_DEMO_PASSWORD=password,APP_ENV='production')
try:
    for _ in range(2):
        result=subprocess.run([sys.executable,str(root/'scripts/init_demo.py')],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert password not in result.stdout
    with closing(sqlite3.connect(db)) as connection:
        for table,count in [('users',2),('students',1),('equipment',4),('slots',4),('fairness_config',1)]:
            assert connection.execute('select count(*) from '+table).fetchone()[0]==count
    print('PASS: demo setup, repeat setup without duplicates, four equipment slots, no plaintext password output')
finally:
    if db.exists():db.unlink()
