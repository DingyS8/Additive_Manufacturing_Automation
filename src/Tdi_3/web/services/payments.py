from datetime import datetime
from .db import get_db

def create_boleto_mock(order_id):
    db=get_db()
    pay={"order_id": str(order_id), "method":"BOLETO", "status":"PENDENTE",
         "linha_digitavel":"00190.00009 01234.567890 12345.678901 1 12340000012345",
         "pdf_url":"https://example.com/boleto.pdf","created_at":datetime.utcnow()}
    db.payments.insert_one(pay)
    return pay

def confirm_payment_mock(order_id):
    db=get_db()
    db.payments.update_many({"order_id": str(order_id)}, {"$set":{"status":"PAGO"}})
