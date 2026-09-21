import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://www.alertasdeconsumo.gob.pe/969.36f5fdefcefdcff0.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
js = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode("utf-8", errors="ignore")

idx = js.find("return{page:this.currentPage()")
print(js[idx:idx+400])
