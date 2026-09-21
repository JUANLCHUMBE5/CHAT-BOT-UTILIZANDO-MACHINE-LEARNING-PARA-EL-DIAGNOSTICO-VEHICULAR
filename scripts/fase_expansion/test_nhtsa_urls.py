import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_PRE_2010.zip",
    "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2025-2026.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2015-2019.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2010-2014.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2005-2009.zip",
    "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2000-2004.zip",
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        res = urllib.request.urlopen(req, context=ctx, timeout=10)
        size_mb = int(res.headers.get("Content-Length", 0)) / (1024 * 1024)
        print(f"OK: {u.split('/')[-1]} -> Status {res.status}, Size: {size_mb:.2f} MB")
    except Exception as e:
        print(f"FAIL: {u.split('/')[-1]} -> {e}")
