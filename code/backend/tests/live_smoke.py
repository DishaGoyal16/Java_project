"""Isolated process-level startup and login smoke; never uses the configured production DB."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

def run():
    with tempfile.TemporaryDirectory(prefix="scms-smoke-") as tmp:
        env = os.environ.copy()
        env.update(DATABASE_URL="sqlite:///"+str(Path(tmp)/"smoke.db").replace("\\", "/"),
                   SECRET_KEY=secrets.token_urlsafe(48), APP_ENV="test")
        with open(Path(tmp)/"server.log","w+") as log:
            process=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--host","127.0.0.1","--port","18000"],env=env,stdout=log,stderr=log)
            def request(path,data=None,token=None):
                headers={"Content-Type":"application/json"}
                if token:headers["Authorization"]="Bearer "+token
                req=Request("http://127.0.0.1:18000"+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
                with urlopen(req,timeout=3) as response:return response.status,json.load(response)
            try:
                for _ in range(100):
                    if process.poll() is not None:raise RuntimeError("API startup failed")
                    try:
                        if request("/api/health")[0]==200:break
                    except (URLError,TimeoutError):time.sleep(.2)
                else:raise RuntimeError("API startup timed out")
                password=secrets.token_urlsafe(24)
                data={"name":"Smoke Student","email":"smoke@example.com","student_id":"SMOKE001","department":"CS","password":password}
                status,body=request("/api/auth/student/register",data)
                assert status==201
                status,body=request("/api/auth/student/login",{"email":data["email"],"password":password})
                assert status==200
                token=body["data"]["token"]
                assert request("/api/equipment",token=token)[0]==200
                assert request("/api/notifications",token=token)[0]==200
                try:request("/api/admin/staff",token=token)
                except HTTPError as ex:assert ex.code==403
                else:raise AssertionError("Student accessed admin route")
                print("Live smoke passed: startup, SQLite connectivity, registration, login, authenticated reads and admin denial")
            finally:
                if os.name == "nt":
                    subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                else:
                    process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()

if __name__=="__main__":run()
