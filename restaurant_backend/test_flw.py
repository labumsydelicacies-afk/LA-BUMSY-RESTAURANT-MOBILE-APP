import httpx
from app.config import FLUTTERWAVE_SECRET_KEY, FLUTTERWAVE_BASE_URL
print(f'Using key starting with {FLUTTERWAVE_SECRET_KEY[:8]}')
headers = {"Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"}
with httpx.Client() as client:
    res = client.get(f"{FLUTTERWAVE_BASE_URL}/transactions", headers=headers, params={"status": "successful"})
    data = res.json()
    if 'data' in data and len(data['data']) > 0:
        latest = data['data'][0]
        print('Latest TX ID:', latest['id'])
        print('Status:', latest['status'])
        print('Amount:', latest['amount'])
        print('Currency:', latest['currency'])
        
        # Now verify it
        v_res = client.get(f"{FLUTTERWAVE_BASE_URL}/transactions/{latest['id']}/verify", headers=headers)
        print('Verify Response:', v_res.json())
    else:
        print('No transactions found or error:', data)
