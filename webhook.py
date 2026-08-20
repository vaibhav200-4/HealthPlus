import requests

WEBHOOK_URL = "https://vaibhavsoni.app.n8n.cloud/webhook-test/951f0d2a-a035-4e7b-8af2-8c0b450445b8"

text = "Hello"
session_id = "test-session-1"

response = requests.post(
    WEBHOOK_URL,
    json={
        "text": text,
        "sessionId": session_id
    }
)

print("Status:", response.status_code)

if response.ok:
    data = response.json()
    print("AI Response:", data.get("output", data))
else:
    print("Error:", response.text)