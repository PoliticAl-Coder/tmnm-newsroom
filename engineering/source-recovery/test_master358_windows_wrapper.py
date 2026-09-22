import os, pathlib, subprocess, tempfile, shutil, sys, re

ROOT=pathlib.Path(__file__).resolve().parent
WRAPPER=ROOT/"RUN_MASTER358_STATIC_REVIEW_ONLY_DO_NOT_RUN.cmd"

def run_case(success):
    with tempfile.TemporaryDirectory(prefix="TMNM Master358 Wrapper ") as td:
        t=pathlib.Path(td); local=t/"Local App Data"; work=t/"Package With Spaces"; work.mkdir(parents=True)
        shutil.copy2(WRAPPER,work/WRAPPER.name)
        env=os.environ.copy(); env["LOCALAPPDATA"]=str(local); env["TEMP"]=str(t/"Temp With Spaces"); pathlib.Path(env["TEMP"]).mkdir()
        if success:
            py=local/"TMNM"/"LocalWorker"/".venv"/"Scripts"; py.mkdir(parents=True)
            shutil.copy2(sys.executable,py/"python.exe")
            (work/"acquire_and_transfer.py").write_text("import pathlib,sys\np=pathlib.Path(sys.argv[1]);p.write_text('STATUS=PASS\\nTOKEN=synthetic\\n');print('STATUS=PASS');raise SystemExit(0)\n")
        p=subprocess.run(["cmd","/d","/c",str(work/WRAPPER.name)],cwd=work,env=env,input="\n",text=True,capture_output=True,timeout=30)
        out=p.stdout+p.stderr
        assert "Window will remain open for inspection." in out
        assert "RESULT_FILE=" in out
        m=re.search(r"RESULT_FILE=(.+)",out); assert m
        rp=pathlib.Path(m.group(1).strip()); assert rp.exists()
        clip=subprocess.run(["powershell","-NoProfile","-Command","Get-Clipboard -Raw"],env=env,text=True,capture_output=True)
        if success:
            assert p.returncode==0,(p.returncode,out)
            assert "STATUS=PASS" in rp.read_text()
            assert "CLIPBOARD=PASS" in out
            assert "STATUS=PASS" in clip.stdout
        else:
            assert p.returncode==2,(p.returncode,out)
            assert "INSTALLED_LOCALWORKER_PYTHON_NOT_FOUND" in rp.read_text()
            assert "CLIPBOARD=PASS" in out
            assert "INSTALLED_LOCALWORKER_PYTHON_NOT_FOUND" in clip.stdout

run_case(False)
run_case(True)
print("MASTER358_NATIVE_WINDOWS_WRAPPER=PASS 2/2")
