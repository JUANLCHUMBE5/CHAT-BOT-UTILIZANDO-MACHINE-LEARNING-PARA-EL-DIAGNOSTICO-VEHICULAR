import urllib.request
import urllib.parse
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

token_url = "https://apiconnect.indecopi.gob.pe/auth/realms/RLM-Indecopi-Produccion/protocol/openid-connect/token"
data = {
    "grant_type": "password",
    "client_id": "CLI_appDPCAlertasConsumoExt",
    "username": "usr_appdpcalertasconsumoext",
    "password": "iN@%26",
    "scope": "openid"
}
req = urllib.request.Request(token_url, data=urllib.parse.urlencode(data).encode("utf-8"), headers={"Content-Type": "application/x-www-form-urlencoded"})
token = json.loads(urllib.request.urlopen(req, context=ctx).read().decode("utf-8"))["access_token"]

det_url = "https://servicios.indecopi.gob.pe/alerta-consumo-api/alerta/detalle?nuIdAlerta=1155"
req = urllib.request.Request(det_url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
res = urllib.request.urlopen(req, context=ctx)
det = json.loads(res.read().decode("utf-8"))
print("Productos:")
print(json.dumps(det.get("datas", {}).get("productos", []), indent=2, ensure_ascii=False))
