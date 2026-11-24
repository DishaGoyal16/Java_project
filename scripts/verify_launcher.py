"""Exercise the real Windows launcher and Vite-to-API-to-Java path, without production data."""
import json, os, secrets, subprocess, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
root=Path(__file__).resolve().parents[1]
local=root/'.local';local.mkdir(exist_ok=True)
db=local/'launcher-smoke.db'
if db.exists():raise SystemExit('Refusing to overwrite an existing launcher-smoke.db')
env=os.environ.copy();env['DATABASE_URL']='sqlite:///'+db.as_posix();env['SECRET_KEY']=secrets.token_urlsafe(48)
ps=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
log=open(local/'launcher-verification.log','w')
p=subprocess.Popen([ps,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'scripts/Start-SCMS.ps1'),'-Diagnostics'],env=env,stdin=subprocess.PIPE,stdout=log,stderr=log,text=True)
def req(path,data=None,token=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    with urlopen(Request('http://127.0.0.1:5173'+path,data=json.dumps(data).encode() if data is not None else None,headers=headers),timeout=4) as r:
        raw=r.read();return r.status,raw
try:
    for _ in range(100):
        if p.poll() is not None:raise RuntimeError('Launcher exited; inspect .local/launcher-verification.log')
        try:
            if req('/api/health')[0]==200:break
        except (URLError,TimeoutError):time.sleep(.3)
    else:raise RuntimeError('Launcher startup timed out')
    assert b'<div id="root">' in req('/')[1]
    password=secrets.token_urlsafe(24)
    status,raw=req('/api/auth/student/register',{'name':'Proxy Test','email':'proxy@example.com','student_id':'PROXY001','department':'CS','password':password})
    assert status==201
    token=json.loads(raw)['data']['token']
    try:req('/api/bookings',{'slot_id':999999},token)
    except HTTPError as ex:
        assert ex.code==404
        assert json.load(ex)['error']['code']=='SLOT_NOT_FOUND'
    else:raise AssertionError('Expected missing-slot rejection')
    time.sleep(.2)
    assert 'operation=booking handler=WorkflowRules.validate status=404 fallback=false' in (local/'java.out.log').read_text()
    assert 'INSERT INTO' not in (local/'api.out.log').read_text()
    print('PASS: launcher startup; dashboard HTML; Vite proxy; registration; authenticated booking -> Java; exact error; Java diagnostic evidence')
finally:
    if p.poll() is None:
        try:p.communicate('\n',timeout=20)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);p.wait()
    log.close()
    if db.exists():db.unlink()
    print('Stopped verification services; removed disposable launcher database')
