from app.db.database import SessionLocal
from app.db.models import Order
from app.services.payment_service import verify_payment

db = SessionLocal()
orders = db.query(Order).order_by(Order.id.desc()).limit(3).all()
for o in orders:
    print(f'Order {o.id}: status={o.status}, payment_status={o.payment_status}, tx_ref={o.payment_reference}, ext_id={o.external_transaction_id}')
