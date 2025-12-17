import time
import requests

API = "https://robo-global-api-v2.onrender.com"

while True:
    try:
        r = requests.post(f"{API}/ping", timeout=10)
        print("PING ENVIADO", r.status_code)
    except Exception as e:
        print("ERRO", e)
    time.sleep(30)
