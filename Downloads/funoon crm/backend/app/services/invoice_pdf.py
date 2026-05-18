"""
Overlay invoice content onto the Funoon letterhead PDF.
All measurements taken directly from the letterhead via pymupdf:
  Header rule:  y=153 pts from top  (from_bottom=689)
  Footer rule:  y=752 pts from top  (from_bottom=90)
  Left margin:  x=62.3 pts
  Right margin: x=533.5 pts
  Page:         595.5 x 842.25 pts (A4)

Fonts: Inter (all text), IBM Plex Sans (all numbers/amounts)
The footer label style (spaced caps, small, light) is matched for labels.
"""
import io
import os
from datetime import date
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.doctemplate import BaseDocTemplate, Frame, PageTemplate

# ── Exact measurements from letterhead ───────────────────────────────────────
PW, PH     = 595.5, 842.25          # page size in pts
LM         = 62.3                   # left margin (matches letterhead x0)
RM         = 595.5 - 533.5          # right margin = 62.0
CW         = 533.5 - 62.3          # = 471.2 pts content width

HEADER_RULE_Y  = 153.1             # rule from top
FOOTER_RULE_Y  = 752.5             # rule from top
FOOTER_LABEL_Y = 769.2             # "LOCATION EMAIL PHONE WEB" from top

# Content runs from just below header rule to just above footer rule
# Add 6pt padding below header rule, 8pt above footer rule
CONTENT_TOP_FROM_BOTTOM = PH - HEADER_RULE_Y - 6    # = 683 pts from bottom
CONTENT_BOT_FROM_BOTTOM = PH - FOOTER_RULE_Y + 8    # = 98 pts from bottom

# ── Paths ─────────────────────────────────────────────────────────────────────
_SVC_DIR  = os.path.dirname(os.path.abspath(__file__))
_APP_DIR  = os.path.dirname(_SVC_DIR)
_BASE     = os.path.dirname(_APP_DIR)
_FONTS    = os.path.join(_BASE, "fonts")
_UPLOADS  = os.path.join(_BASE, "uploads")

# ── Exact brand colours sampled directly from letterhead PDF ──────────────────
C_INK     = colors.HexColor("#0E1A1F")   # exact dark ink from letterhead text
C_MID     = colors.HexColor("#7F837F")   # exact secondary grey (".ai" tone)
C_LIGHT   = colors.HexColor("#A8A59D")   # light labels (footer label tone)
C_RULE    = colors.HexColor("#D9D6CB")   # exact rule colour from letterhead
C_BG      = colors.HexColor("#F1ECDF")   # exact page background
C_ROW_ALT = colors.HexColor("#E8E3D8")   # slightly darker than BG for alt rows
C_TH_BG   = colors.HexColor("#0E1A1F")   # table header = exact ink colour
C_TH_RULE = colors.HexColor("#D9D6CB")   # rule under header
C_WHITE   = colors.white

# ── Font registration ─────────────────────────────────────────────────────────
_fonts_ok = False

def _reg():
    global _fonts_ok
    if _fonts_ok:
        return
    ok = True
    for name, file in [
        ("Inter",    "Inter-Regular.ttf"),
        ("Inter-Md", "Inter-Medium.ttf"),
        ("Inter-Bd", "Inter-Bold.ttf"),
        ("Plex",     "IBMPlexSans-Regular.ttf"),
        ("Plex-Md",  "IBMPlexSans-Medium.ttf"),
        ("Plex-Bd",  "IBMPlexSans-Bold.ttf"),
    ]:
        path = os.path.join(_FONTS, file)
        if not os.path.exists(path):
            ok = False
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            pass  # already registered
    _fonts_ok = ok

def _f(name):
    """Return font name, fall back to Helvetica if not loaded."""
    if _fonts_ok:
        return name
    return {"Inter":"Helvetica","Inter-Md":"Helvetica","Inter-Bd":"Helvetica-Bold",
            "Plex":"Helvetica","Plex-Md":"Helvetica","Plex-Bd":"Helvetica-Bold"}.get(name,"Helvetica")

def _s(nm, font="Inter", size=8.5, color=None, align=0, leading=None, **kw):
    _reg()
    return ParagraphStyle(
        nm, fontName=_f(font), fontSize=size,
        textColor=color or C_INK,
        alignment=align,
        leading=leading or round(size * 1.5),
        **kw,
    )

def _p(txt, st):
    return Paragraph(str(txt), st)

def _cur(n, ccy="AED"):
    return f"{ccy} {int(n):,}"

def _fmt(d):
    if not d:
        return "—"
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(d)).strftime("%d %b %Y")
    except Exception:
        return str(d)


def generate_invoice_pdf(
    invoice: dict[str, Any],
    client: dict[str, Any] | None,
    company: dict[str, Any] | None = None,
) -> bytes:
    _reg()
    co = company or {}

    bank_name    = co.get("bank_name")           or "Emirates NBD"
    bank_acct    = co.get("bank_account_name")   or "Funoon FZC"
    bank_iban    = co.get("bank_iban")            or "AE00 0000 0000 0000 0000 000"
    bank_acct_no = co.get("bank_account_number") or ""
    bank_swift   = co.get("bank_swift")          or ""
    bank_ccy     = co.get("bank_currency")        or "AED"
    pay_terms    = co.get("invoice_payment_terms") or "Payment due within 30 days of issue."
    vat_rate     = int(co.get("vat_rate") or 5)

    doc_type = (invoice.get("_doc_type") or "INVOICE").upper()
    inv_num  = (invoice.get("number")    or f"INV-{invoice['id'][:8].upper()}").upper()
    issued   = invoice.get("issued_date") or date.today().isoformat()
    due      = invoice.get("due_date")   or ""
    status   = (invoice.get("status")   or "draft").upper()

    # ── Styles ────────────────────────────────────────────────────────────────
    # "Footer label" style — matches the letterhead LOCATION/EMAIL caps style
    # Label caps — matches letterhead footer label style (LOCATION, EMAIL etc)
    s_cap    = _s("cap",  "Inter",    6.5, C_MID,    leading=10, spaceAfter=3)
    # Body text — exact ink colour from letterhead
    s_body   = _s("body", "Inter",    8.5, C_INK,    leading=13)
    s_bold   = _s("bold", "Inter-Bd", 8.5, C_INK,    leading=13)
    s_sub    = _s("sub",  "Inter",    8,   C_MID,    leading=12)
    # Table header text
    s_th     = _s("th",   "Inter-Md", 7,   C_WHITE,  align=1, leading=10)
    s_th_l   = _s("thl",  "Inter-Md", 7,   C_WHITE,  align=0, leading=10)
    # Numbers — IBM Plex Sans, exact ink colour
    s_num    = _s("num",  "Plex",     8.5, C_INK,    align=2, leading=13)
    s_num_b  = _s("numb", "Plex-Bd",  9.5, C_INK,    align=2, leading=14)
    # Subtotal/VAT labels
    s_sub_l  = _s("subl", "Inter",    8,   C_MID,    align=2, leading=12)
    # Total label + value
    s_tot_l  = _s("totl", "Inter-Bd", 9.5, C_INK,    align=2, leading=14)
    # Payment details — keys same light as footer labels, values = full ink
    s_pk     = _s("pk",   "Inter",    8,   C_MID,    leading=13)
    s_pv     = _s("pv",   "Inter",    8.5, C_INK,    leading=13)
    # Payment terms / notes — light secondary
    s_terms  = _s("trm",  "Inter",    7.5, C_MID,    leading=11)
    s_doc    = _s("doc",  "Inter-Md", 8.5, C_MID,    align=2)

    # ── Build overlay ─────────────────────────────────────────────────────────
    overlay_buf = io.BytesIO()
    content_h   = CONTENT_TOP_FROM_BOTTOM - CONTENT_BOT_FROM_BOTTOM

    frame = Frame(
        LM, CONTENT_BOT_FROM_BOTTOM,
        CW, content_h,
        leftPadding=0, rightPadding=0,
        topPadding=0,  bottomPadding=0,
    )

    def _on_page(canvas, doc):
        """Draw doc-type label (INVOICE/RECEIPT/QUOTE) right-aligned, just below header rule."""
        canvas.saveState()
        canvas.setFont(_f("Inter-Md"), 8)
        canvas.setFillColor(C_MID)
        # Position: right-aligned, 4pts below the header rule
        label_y = PH - HEADER_RULE_Y - 15
        canvas.drawRightString(533.5, label_y, doc_type)
        canvas.restoreState()

    tmpl = PageTemplate(id="main", frames=[frame], onPage=_on_page)
    doc  = BaseDocTemplate(
        overlay_buf, pagesize=(PW, PH),
        pageTemplates=[tmpl],
        leftMargin=LM, rightMargin=RM,
        topMargin=PH - CONTENT_TOP_FROM_BOTTOM - CONTENT_BOT_FROM_BOTTOM,
        bottomMargin=CONTENT_BOT_FROM_BOTTOM,
    )

    story: list = []
    story.append(Spacer(1, 8))

    # ── Bill To + Invoice Details ─────────────────────────────────────────────
    # Left: BILL TO block
    to_col = [_p("BILL TO", s_cap)]
    if client and client.get("name"):
        to_col.append(_p(f"<b>{client['name']}</b>", s_bold))
        if client.get("contact_name"):
            to_col.append(_p(client["contact_name"], s_sub))
        if client.get("email"):
            to_col.append(_p(client["email"], s_sub))
        if client.get("whatsapp"):
            to_col.append(_p(client["whatsapp"], s_sub))
    else:
        to_col.append(_p("—", s_sub))

    # Right: INVOICE DETAILS key/value
    kv = TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 1.5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1.5),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (1,0),(1,-1),  0),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ])
    detail_tbl = Table([
        [_p("Invoice #", s_pk), _p(f"<b>{inv_num}</b>", s_bold)],
        [_p("Date",      s_pk), _p(_fmt(issued), s_body)],
        [_p("Due",       s_pk), _p(_fmt(due),    s_body)],
        [_p("Status",    s_pk), _p(status,       s_bold)],
    ], colWidths=[CW*0.14, CW*0.36], style=kv)

    inv_col = [_p("INVOICE DETAILS", s_cap), detail_tbl]

    meta = Table(
        [[to_col, inv_col]],
        colWidths=[CW * 0.45, CW * 0.55],
        style=TableStyle([
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 0),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ]),
    )
    story.append(meta)
    story.append(Spacer(1, 10))

    # ── Line items ────────────────────────────────────────────────────────────
    line_items: list[dict] = invoice.get("line_items") or []
    if not line_items:
        line_items = [{
            "description": invoice.get("notes") or "Professional services",
            "qty": 1,
            "unit_price": invoice.get("amount", 0),
        }]

    cw = [CW*0.50, CW*0.12, CW*0.19, CW*0.19]

    rows = [[
        _p("DESCRIPTION", s_th_l),
        _p("QTY",         s_th),
        _p("UNIT PRICE",  s_th),
        _p("AMOUNT",      s_th),
    ]]

    subtotal = 0
    for i, item in enumerate(line_items):
        qty = int(item.get("qty", 1))
        up  = int(item.get("unit_price", 0))
        amt = qty * up
        subtotal += amt
        rows.append([
            _p(item.get("description","—"), s_body),
            _p(str(qty), _s(f"q{i}", "Plex", 8.5, C_MID, align=1)),
            _p(_cur(up,  bank_ccy), s_num),
            _p(_cur(amt, bank_ccy), s_num),
        ])

    vat_amt = round(subtotal * vat_rate / 100)
    total   = subtotal + vat_amt
    data_n  = len(rows)

    rows.append(["","", _p("Subtotal",           s_sub_l), _p(_cur(subtotal, bank_ccy), s_num)])
    rows.append(["","", _p(f"VAT ({vat_rate}%)", s_sub_l), _p(_cur(vat_amt,  bank_ccy), s_num)])
    rows.append(["","", _p("TOTAL",              s_tot_l), _p(_cur(total,    bank_ccy), s_num_b)])

    n     = len(rows)
    sub_r = n - 3
    tot_r = n - 1

    tbl = Table(rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header row — exact ink colour, white text, no border
        ("BACKGROUND",    (0,0),    (-1,0),            C_TH_BG),
        ("LINEBELOW",     (0,0),    (-1,0),            0,    C_TH_BG),  # no line under header
        # Padding
        ("TOPPADDING",    (0,0),    (-1,-1),           7),
        ("BOTTOMPADDING", (0,0),    (-1,-1),           7),
        ("LEFTPADDING",   (0,0),    (-1,-1),           8),
        ("RIGHTPADDING",  (0,0),    (-1,-1),           8),
        ("LEFTPADDING",   (0,1),    (0,-1),            0),    # description flush left
        # Data rows — beige base, slightly darker alt
        ("ROWBACKGROUNDS",(0,1),    (-1,data_n-1),    [C_BG, C_ROW_ALT]),
        # Subtotal/VAT rows — plain BG, no fill
        ("BACKGROUND",    (0,sub_r),(-1,tot_r-1),     C_BG),
        # Rule above subtotal block
        ("LINEABOVE",     (0,sub_r),(-1,sub_r),        0.4, C_RULE),
        # Total row — thin ink rule above, beige background
        ("BACKGROUND",    (0,tot_r),(-1,tot_r),        C_BG),
        ("LINEABOVE",     (0,tot_r),(-1,tot_r),        0.8, C_INK),
        ("LINEBELOW",     (0,tot_r),(-1,tot_r),        0.4, C_RULE),
        ("TOPPADDING",    (0,tot_r),(-1,tot_r),        9),
        ("BOTTOMPADDING", (0,tot_r),(-1,tot_r),        9),
        # No grid lines on data rows — clean open look
        ("INNERGRID",     (0,1),    (-1,data_n-1),     0,    C_BG),
        ("BOX",           (0,0),    (-1,-1),            0,    C_BG),
        ("VALIGN",        (0,0),    (-1,-1),           "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # ── Payment details ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.4, color=C_RULE))
    story.append(Spacer(1, 8))
    story.append(_p("PAYMENT DETAILS", s_cap))
    story.append(Spacer(1, 5))

    bank_rows = [
        [_p("Bank",         s_pk), _p(bank_name,  s_pv)],
        [_p("Account name", s_pk), _p(bank_acct,  s_pv)],
        [_p("IBAN",         s_pk), _p(bank_iban,  s_pv)],
    ]
    if bank_acct_no:
        bank_rows.append([_p("Account #", s_pk), _p(bank_acct_no, s_pv)])
    if bank_swift:
        bank_rows.append([_p("SWIFT",     s_pk), _p(bank_swift,   s_pv)])
    bank_rows.append([_p("Currency",  s_pk), _p(bank_ccy,    s_pv)])

    pd_tbl = Table(bank_rows, colWidths=[CW*0.20, CW*0.80],
        style=TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 2),
            ("BOTTOMPADDING", (0,0),(-1,-1), 2),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 4),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
    story.append(pd_tbl)
    story.append(Spacer(1, 7))
    story.append(_p(pay_terms, s_terms))

    if invoice.get("notes"):
        story.append(Spacer(1, 4))
        story.append(_p(f"Note: {invoice['notes']}", s_terms))

    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=0.4, color=C_RULE))
    story.append(Spacer(1, 10))

    # ── Signature + Stamp ─────────────────────────────────────────────────────
    sig_path   = co.get("signature_path")
    stamp_path = co.get("stamp_path")
    col_w      = CW * 0.38
    img_max_w  = col_w          # full column width
    img_max_h  = 72             # tall enough to overlap label

    def _asset_block(label, img_path):
        """
        Image sits at the bottom of the block, overlapping the rule + label.
        We achieve this by using a negative spacer trick via a canvas-drawn
        overlay — instead, we draw the rule/label FIRST then place the image
        on top using a zero-height spacer + absolute positioning via a custom
        Flowable.
        """
        from reportlab.platypus import Image as RLImage, Flowable

        class SigBlock(Flowable):
            """
            Layout (bottom to top):
              y=0            bottom pad
              y=6            label text baseline
              y=18           rule line
              y=18..18+img_h image sits here, centred, overlapping the rule+label

            The image is drawn LAST so it renders on top of the label.
            """
            def __init__(self, path, max_w, max_h, label_txt, label_style):
                super().__init__()
                self.path        = path
                self.max_w       = max_w
                self.max_h       = max_h
                self.label_txt   = label_txt
                self.label_style = label_style

                self.draw_w = 0
                self.draw_h = 0
                if path and os.path.exists(path):
                    try:
                        from PIL import Image as PILImg
                        with PILImg.open(path) as pil:
                            iw, ih = pil.size
                        scale = min(max_w / iw, max_h / ih)
                        self.draw_w = iw * scale
                        self.draw_h = ih * scale
                    except Exception:
                        pass

                # Total height = label (6) + rule gap (12) + label text height (10) + bottom (4)
                self.height = 32
                self.width  = max_w

            def draw(self):
                c   = self.canv
                w   = self.max_w
                RULE_Y  = 20   # rule sits 20pts from bottom of this flowable
                LABEL_Y = 6    # label baseline

                # 1. Rule line
                c.setStrokeColor(C_RULE)
                c.setLineWidth(0.4)
                c.line(0, RULE_Y, w, RULE_Y)

                # 2. Label text below rule
                from reportlab.platypus import Paragraph
                p = Paragraph(self.label_txt, self.label_style)
                p.wrapOn(c, w, 20)
                p.drawOn(c, 0, LABEL_Y)

                # 3. Image drawn ON TOP of rule+label, centred horizontally
                #    bottom of image = RULE_Y - img_h/2  (overlaps into rule+label area)
                if self.draw_w and self.path and os.path.exists(self.path):
                    img_x = 0                              # flush left
                    img_y = LABEL_Y - 2                   # bottom of image sits just above label baseline
                    c.drawImage(
                        self.path,
                        x=img_x,
                        y=img_y,
                        width=self.draw_w,
                        height=self.draw_h,
                        preserveAspectRatio=True,
                        mask='auto',
                    )

        block = [
            Spacer(1, img_max_h + 8),   # space for image to grow into above
            SigBlock(img_path, img_max_w, img_max_h, label, s_cap),
        ]
        return block

    sig_tbl = Table(
        [[_asset_block("AUTHORISED SIGNATURE", sig_path),
          "",
          _asset_block("COMPANY STAMP", stamp_path)]],
        colWidths=[col_w, CW * 0.24, col_w],
        style=TableStyle([
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 0),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ]),
    )
    story.append(sig_tbl)

    doc.build(story)

    # ── Merge onto letterhead ─────────────────────────────────────────────────
    lh_path = os.path.join(_UPLOADS, "letterhead_template.pdf")
    if not os.path.exists(lh_path):
        return overlay_buf.getvalue()

    from pypdf.generic import ArrayObject, FloatObject

    lh_page = PdfReader(lh_path).pages[0]
    ov_page = PdfReader(overlay_buf).pages[0]
    lh_page.merge_page(ov_page)

    # Force exact A4 mediabox (595.28 x 841.89 pts)
    a4 = ArrayObject([FloatObject(0), FloatObject(0),
                      FloatObject(595.28), FloatObject(841.89)])
    lh_page.mediabox.lower_left  = (0, 0)
    lh_page.mediabox.upper_right = (595.28, 841.89)

    writer = PdfWriter()
    writer.add_page(lh_page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
