import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.nhtsa.gov/nhtsa-datasets-and-apis', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8', errors='ignore')

zips = re.findall(r'https?://[^\s"\'<>]+\.zip', html)
print("ZIP links found on NHTSA page:")
for z in sorted(set(zips)):
    print(" ", z)
