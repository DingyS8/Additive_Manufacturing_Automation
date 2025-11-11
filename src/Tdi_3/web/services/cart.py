from datetime import datetime
from .db import get_db

def get_cart(user_id):
    db=get_db()
    cart=db.carts.find_one({"user_id": user_id})
    if not cart:
        cart={"user_id": user_id, "items": [], "created_at": datetime.utcnow()}
        db.carts.insert_one(cart)
    return cart

def add_item(user_id, item):
    db=get_db()
    db.carts.update_one({"user_id":user_id}, {"$push":{"items":item}, "$set":{"updated_at": datetime.utcnow()}}, upsert=True)

def remove_item(user_id, item_id):
    db=get_db()
    db.carts.update_one({"user_id":user_id}, {"$pull":{"items":{"id":item_id}}, "$set":{"updated_at": datetime.utcnow()}})

def clear_cart(user_id):
    db=get_db()
    db.carts.update_one({"user_id":user_id}, {"$set":{"items":[], "updated_at": datetime.utcnow()}}, upsert=True)
