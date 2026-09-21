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
req = urllib.request.Request(
    token_url,
    data=urllib.parse.urlencode(data).encode("utf-8"),
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
token = json.loads(urllib.request.urlopen(req, context=ctx).read().decode("utf-8"))["access_token"]

payload = {
    "page": 1,
    "size": 10,
    "vcCriterio": "",
    "nuIdTipoProducto": None,
    "nuIdsCategorias": [15],
    "nuIdsRiesgo": [],
    "nuIdsMedidaMitigacion": [],
    "vcFechaInicio": "",
    "vcFechaFin": ""
}

url = "https://servicios.indecopi.gob.pe/alerta-consumo-api/alerta/bandeja"
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
)
res = urllib.request.urlopen(req, context=ctx)
print("Status:", res.status)
raw = res.read().decode("utf-8")
resp = json.loads(raw)
data = resp.get("datas", {})
print("Total records found for Category 15 (Vehicles):", data.get("total"))
print("First item preview:")
sample = data.get("list", [])[0] if data.get("list") else {}
print(json.dumps(sample, indent=2, ensure_ascii=False)[:600])
