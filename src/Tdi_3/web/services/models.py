from datetime import datetime

def user_doc(name, email, phone="", document="", notes=""):
    return {"name": name, "email": email, "phone": phone, "document": document, "notes": notes, "created_at": datetime.utcnow()}

def file_doc(owner_id, kind, path, original_name, size_bytes):
    return {"owner_id": owner_id, "kind": kind, "path": path, "original_name": original_name, "size": size_bytes, "created_at": datetime.utcnow()}

def conversion_doc(owner_id, input_file_id, output_file_id, method, meta=None):
    return {"owner_id": owner_id, "input_file_id": input_file_id, "output_file_id": output_file_id, "method": method, "meta": meta or {}, "created_at": datetime.utcnow()}

def cart_doc(user_id, items):
    return {"user_id": user_id, "items": items, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}

def order_doc(user_id, items, total, status="PENDENTE_PAGAMENTO", gcode_file_ids=None):
    return {"user_id": user_id, "items": items, "total": total, "status": status, "gcodes": gcode_file_ids or [], "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
