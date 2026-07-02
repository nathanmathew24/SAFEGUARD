"""
Pure-Python validator for extracted document fields.
No Claude calls here — just schema/type validation.
"""
from datetime import date as _date


_MONEY_FIELDS = {
    "total_amount", "subtotal_amount", "tax_amount", "amount",
    "amount_paid", "discount_amount", "unit_price",
}
_DATE_FIELDS = {
    "document_date", "due_date", "cheque_date", "delivery_date",
    "valid_until", "delivery_expected_date",
}
_PAYMENT_METHODS = {"cash", "bank_transfer", "cheque", "pdc"}


def validate_fields(fields: dict, doc_type: str) -> tuple[bool, list[str]]:
    """
    Validate extracted field values (not confidences).
    Returns (is_valid, [error_messages]).
    """
    errors = []

    for field_name, entry in fields.items():
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if value is None:
            continue

        if field_name in _MONEY_FIELDS:
            try:
                v = int(value)
                if v < 0:
                    errors.append(f"{field_name} must be >= 0 fils")
            except (TypeError, ValueError):
                errors.append(f"{field_name} must be an integer (fils)")

        elif field_name in _DATE_FIELDS:
            if isinstance(value, str):
                try:
                    _date.fromisoformat(value)
                except ValueError:
                    errors.append(f"{field_name} must be YYYY-MM-DD, got '{value}'")

        elif field_name == "payment_method":
            if str(value).lower() not in _PAYMENT_METHODS:
                errors.append(
                    f"payment_method '{value}' must be one of {sorted(_PAYMENT_METHODS)}"
                )

    return len(errors) == 0, errors


def flatten_values(fields: dict) -> dict:
    """Extract just the values from {field: {value, confidence}} structure."""
    return {k: v.get("value") for k, v in fields.items() if isinstance(v, dict)}
