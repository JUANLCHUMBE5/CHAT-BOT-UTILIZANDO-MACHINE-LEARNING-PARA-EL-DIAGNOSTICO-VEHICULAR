import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url_runtime = "https://www.alertasdeconsumo.gob.pe/runtime.4127263559b71878.js"
req = urllib.request.Request(url_runtime, headers={"User-Agent": "Mozilla/5.0"})
js = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode("utf-8", errors="ignore")

chunks = re.findall(r'(\d+):["\']([a-f0-9]+)["\']', js)

for chunk_id, chunk_hash in chunks:
    chunk_file = f"{chunk_id}.{chunk_hash}.js"
    chunk_url = f"https://www.alertasdeconsumo.gob.pe/{chunk_file}"
    try:
        c_req = urllib.request.Request(chunk_url, headers={"User-Agent": "Mozilla/5.0"})
        c_js = urllib.request.urlopen(c_req, context=ctx, timeout=15).read().decode("utf-8", errors="ignore")
        # Search for endpoints or http calls
        calls = re.findall(r'(\.get\([^)]+\)|\.post\([^)]+\))', c_js)
        if calls or 'alerta' in c_js:
            apis = re.findall(r'["\'`](/[a-zA-Z0-9_\-\./]+)["\'`]', c_js)
            api_cand = [a for a in apis if 'alerta' in a or 'busc' in a or 'api' in a or 'vehic' in a or 'categoria' in a]
            if api_cand or calls:
                print(f"Chunk {chunk_file}:")
                for c in calls[:5]:
                    print(f"  Call: {c[:120]}")
                for a in set(api_cand[:10]):
                    print(f"  API: {a}")
    except Exception as e:
        print(f"Error {chunk_file}: {e}")
