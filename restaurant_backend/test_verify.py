from app.db.database import SessionLocal
from app.db.models import Order
from app.services.payment_service import verify_payment

db = SessionLocal()
orders = db.query(Order).order_by(Order.id.desc()).limit(3).all()
for o in orders:
    print(f'Order {o.id}: status={o.status}, payment_status={o.payment_status}, tx_ref={o.payment_reference}, ext_id={o.external_transaction_id}, total={o.total_price}')
    
    if o.external_transaction_id:
        print('Verifying with external ID:', o.external_transaction_id)
        res = verify_payment(o.external_transaction_id, o.total_price)
        print('Result:', res)
    else:
        # Search flutterwave for it by tx_ref
        import httpx
        from app.config import FLUTTERWAVE_SECRET_KEY, FLUTTERWAVE_BASE_URL
        headers = {"Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"}
        try:
            with httpx.Client() as c:
                r = c.get(f"{FLUTTERWAVE_BASE_URL}/transactions", headers=headers, params={"tx_ref": o.payment_reference})
                d = r.json()
                if 'data' in d and len(d['data']) > 0:
                    tx_id = d['data'][0]['id']
                    print('Found on FLW! ID:', tx_id)
                    res = verify_payment(tx_id, o.total_price)
                    print('Verify Result:', res)
                else:
                    print('Not found on FLW for tx_ref', o.payment_reference)
        except Exception as e:
            print(e)
