import urllib.request
import urllib.parse
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

token_url = "https://apiconnect.indecopi.gob.pe/auth/realms/RLM-Indecopi-Produccion/protocol/openid-connect/token"

for pw in ["iN@%26", "iN@&"]:
    data = {
        "grant_type": "password",
        "client_id": "CLI_appDPCAlertasConsumoExt",
        "username": "usr_appdpcalertasconsumoext",
        "password": pw,
        "scope": "openid"
    }
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.alertasdeconsumo.gob.pe",
        "Referer": "https://www.alertasdeconsumo.gob.pe/"
    }
    print(f"Testing password={pw} ...")
    try:
        req = urllib.request.Request(token_url, data=encoded, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        raw = res.read().decode("utf-8")
        token_data = json.loads(raw)
        print("SUCCESS! Got access token:", token_data.get("access_token")[:40], "...")
        break
    except Exception as e:
        print("Error:", e)
        if hasattr(e, "read"):
            print("Response:", e.read().decode("utf-8", errors="ignore"))
