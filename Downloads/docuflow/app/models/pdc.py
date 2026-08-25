"""
PDC — Post-Dated Cheque.

4-state lifecycle enforced as a state machine (not free-text):
  received → pending_deposit → deposited → cleared  (terminal)
                             → bounced   → pending_deposit  (re-presentation)

Illegal transitions raise ValueError → caught → 400 Bad Request.

Every transition is appended to the JSON `history` column:
  [{"from": "received", "to": "pending_deposit", "at": "ISO8601", "by": <user_id>, "note": "..."}]
"""
from datetime import datetime, timezone
from app.extensions import db


_TRANSITIONS = {
    "received":         {"pending_deposit"},
    "pending_deposit":  {"deposited"},
    "deposited":        {"cleared", "bounced"},
    "bounced":          {"pending_deposit"},
    "cleared":          set(),  # terminal
}


class PDC(db.Model):
    __tablename__ = "pdcs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)

    cheque_number = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(255), nullable=False)
    cheque_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(20, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="AED", server_default="AED")
    drawer_name = db.Column(db.String(255), nullable=True)

    pdc_status = db.Column(
        db.Enum("received", "pending_deposit", "deposited", "cleared", "bounced",
                name="pdc_status_enum"),
        nullable=False, default="received", server_default="received",
    )
    history = db.Column(db.JSON, nullable=False, default=list, server_default="[]")

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    invoice = db.relationship("Invoice", back_populates="pdcs")
    customer = db.relationship("Customer", lazy="joined")

    def transition(self, to_status: str, user_id: int, note: str = ""):
        allowed = _TRANSITIONS.get(self.pdc_status, set())
        if to_status not in allowed:
            raise ValueError(
                f"PDC {self.id}: cannot transition from '{self.pdc_status}' to '{to_status}'. "
                f"Allowed: {sorted(allowed) or 'none (terminal)'}"
            )
        event = {
            "from": self.pdc_status,
            "to": to_status,
            "at": datetime.now(timezone.utc).isoformat(),
            "by": user_id,
            "note": note,
        }
        history = list(self.history or [])
        history.append(event)
        self.history = history
        self.pdc_status = to_status

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "cheque_number": self.cheque_number,
            "bank_name": self.bank_name,
            "cheque_date": self.cheque_date.isoformat() if self.cheque_date else None,
            "amount": float(self.amount),
            "currency": self.currency,
            "drawer_name": self.drawer_name,
            "pdc_status": self.pdc_status,
            "history": self.history,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
