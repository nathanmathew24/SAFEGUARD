"""
Tenant-scoping helper.

Every route that looks up a document by ID must go through get_scoped_or_404.
This is the single fix for the cross-tenant read/write vulnerability where any
authenticated user could access another company's documents by knowing the UUID.

Returns 404 (not 403) when the record exists but belongs to another company
so the caller cannot infer whether the ID is valid.
"""
import uuid
from flask import abort
from app.extensions import db


def get_scoped_or_404(model, doc_id, company_id):
    """
    Fetch model row by primary key AND company_id.
    Both IDs are coerced to the correct Python type before querying.
    """
    try:
        if isinstance(model.__table__.c.id.type, db.Integer):
            pk = int(doc_id)
            cid = int(company_id)
        else:
            pk = uuid.UUID(str(doc_id))
            cid = uuid.UUID(str(company_id))
    except (ValueError, AttributeError):
        abort(404)

    row = db.session.get(model, pk)
    if row is None or row.company_id != cid:
        abort(404)
    return row
