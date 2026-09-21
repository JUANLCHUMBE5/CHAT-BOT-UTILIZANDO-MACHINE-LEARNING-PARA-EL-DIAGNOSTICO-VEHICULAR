import urllib.request
import urllib.parse
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = "https://servicios.indecopi.gob.pe/alerta-consumo-api/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.alertasdeconsumo.gob.pe",
    "Referer": "https://www.alertasdeconsumo.gob.pe/",
}

endpoints_to_test = [
    ("categoria/listar", {}),
    ("tipoProducto/listar", {}),
    ("alerta/listar", {"page": 1, "size": 10}),
]

for ep, params in endpoints_to_test:
    qs = urllib.parse.urlencode(params)
    url = f"{base}{ep}{'?' + qs if qs else ''}"
    print(f"Testing {url} ...")
    try:
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        raw = res.read().decode("utf-8")
        print(f"  Status {res.status}, len={len(raw)}")
        data = json.loads(raw)
        print("  Parsed preview:", str(data)[:200])
    except Exception as e:
        print(f"  Error: {e}")
