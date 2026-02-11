import httpx

r = httpx.get('http://127.0.0.1:8000/healthz', timeout=3)
print(r.json())
