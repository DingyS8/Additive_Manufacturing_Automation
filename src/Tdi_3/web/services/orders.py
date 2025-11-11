from datetime import datetime
from bson import ObjectId
from .db import get_db

ORDER_STATES = ["PENDENTE_PAGAMENTO","PAGO","IMPRIMINDO","FINALIZADO","ENVIADO","ENTREGUE","CANCELADO"]

def create_order(user_id, items, total):
    db=get_db()
    order={"user_id":user_id,"items":items,"total":total,"status":"PENDENTE_PAGAMENTO",
           "created_at":datetime.utcnow(),"updated_at":datetime.utcnow()}
    db.orders.insert_one(order)
    return order

def cancel_order(order_id, user_id=None, is_admin=False):
    db=get_db(); query={"_id": ObjectId(order_id)}
    if not is_admin: query["user_id"] = user_id
    db.orders.update_one(query, {"$set":{"status":"CANCELADO","updated_at":datetime.utcnow()}})

def update_status(order_id, new_status):
    assert new_status in ORDER_STATES
    db=get_db()
    db.orders.update_one({"_id": ObjectId(order_id)}, {"$set":{"status":new_status,"updated_at":datetime.utcnow()}})

def list_orders_by_user(user_id):
    return list(get_db().orders.find({"user_id": user_id}).sort("created_at",-1))

def list_all_orders():
    return list(get_db().orders.find().sort("created_at",-1))
