import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_PRE_2010.zip",
    "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2025-2026.zip",
]

for u in urls:
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req, context=ctx)
    cl = res.headers.get("Content-Length")
    filename = u.split("/")[-1]
    if cl:
        print(f"{filename}: {int(cl)/(1024*1024):.2f} MB")
    else:
        print(f"{filename}: Content-Length not set, testing stream...")
        data = res.read()
        print(f"  Downloaded {len(data)/(1024*1024):.2f} MB")
