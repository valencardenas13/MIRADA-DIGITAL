import os
import urllib.request
import json

token = os.environ.get("TELEGRAM_TOKEN", "").strip()
chat  = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

print(f"Token primeros 10 chars: {token[:10]}")
print(f"Chat ID length: {len(chat)}")

if not token or not chat:
    print("ERROR: Faltan credenciales")
    raise SystemExit(1)

url  = f"https://api.telegram.org/bot{token}/sendMessage"
data = json.dumps({"chat_id": chat, "text": "Mirada Digital - GitHub Actions conectado!"}).encode()
req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    r = urllib.request.urlopen(req, timeout=10)
    print("OK:", r.status)
except Exception as e:
    print("ERROR:", e)
    raise SystemExit(1)
