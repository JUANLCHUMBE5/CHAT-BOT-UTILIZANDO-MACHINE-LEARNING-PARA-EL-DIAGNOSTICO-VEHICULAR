import psutil
import datetime

print("=== PROCESS AUDIT ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cwd']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        name = p.info['name'] or ''
        if any(k in cmd.lower() or k in name.lower() for k in ['uvicorn', 'worker', 'ngrok', 'carbot', 'postgres', 'python']):
            if 'conhost' in name.lower() or 'code' in name.lower():
                continue
            ctime = datetime.datetime.fromtimestamp(p.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
            cwd = p.info.get('cwd') or 'N/A'
            pid = p.info['pid']
            print(f"PID={pid:5d} | Created={ctime} | Name={name:15s} | CWD={cwd}")
            print(f"   CMD: {cmd[:150]}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
