import time
import requests

url = 'http://127.0.0.1:5000/api/jobs?page=1'

for i in range(3):
    t0 = time.perf_counter()
    r = requests.get(url, timeout=20)
    dt = (time.perf_counter() - t0) * 1000
    print(f'call {i+1}: {r.status_code} in {dt:.1f} ms')
