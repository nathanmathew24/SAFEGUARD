from datetime import datetime

from pydantic import BaseModel


class CompanySettingsOut(BaseModel):
    id: str
    company_name: str
    tagline: str | None
    address_line1: str | None
    address_line2: str | None
    trn: str | None
    email: str | None
    phone: str | None
    website: str | None
    bank_name: str | None
    bank_account_name: str | None
    bank_iban: str | None
    bank_account_number: str | None
    bank_swift: str | None
    bank_currency: str
    invoice_payment_terms: str | None
    invoice_notes: str | None
    invoice_prefix: str
    vat_rate: str
    letterhead_path: str | None
    signature_path: str | None
    stamp_path: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanySettingsUpdate(BaseModel):
    company_name: str | None = None
    tagline: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    trn: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    bank_name: str | None = None
    bank_account_name: str | None = None
    bank_iban: str | None = None
    bank_account_number: str | None = None
    bank_swift: str | None = None
    bank_currency: str | None = None
    invoice_payment_terms: str | None = None
    invoice_notes: str | None = None
    invoice_prefix: str | None = None
    vat_rate: str | None = None
