from datetime import datetime
from .db import get_db

def issue_nfe_mock(order_id):
    db=get_db()
    inv={"order_id": str(order_id), "nfe_number":"12345", "nfe_pdf_url":"https://example.com/nfe.pdf",
         "nfe_xml_url":"https://example.com/nfe.xml", "created_at": datetime.utcnow()}
    db.invoices.insert_one(inv)
    return inv
