import subprocess

try:
    out = subprocess.check_output("wmic process where \"name='python.exe'\" get processid,commandline", shell=True, text=True, errors="replace")
    for line in out.splitlines():
        if "src.application.jobs.worker" in line:
            print("WORKER LINE:", line.strip())
        elif "uvicorn" in line:
            print("UVICORN LINE:", line.strip())
except Exception as e:
    print("Error:", e)
