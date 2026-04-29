from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import os
from datetime import datetime
from num2words import num2words
import arabic_reshaper
from bidi.algorithm import get_display

COMPANY_NAME   = "Career Catalyst Venture LLC"
TAX_REG        = "104888097300001"
WEBSITE        = "www.thejobworkshop.com"
ADDRESS_L1     = "Shams Business Centre, Sharjah Media City Free Zone,"
ADDRESS_L2     = "Al Messaned, Sharjah, UAE"
LICENCE_NO     = "2535552.01"
INVOICE_PREFIX = "TJW"

PROGRAMS = {
    1: "Five Modules Advisory Program (Interview Assurance Program)",
    2: ("Comprehensive End to End Job Search Management and Advisory "
        "(LinkedIn Management, Engagement, Applications and Outreach)"),
}

NAVY        = colors.HexColor('#1B3A5C')
LIGHT_GRAY  = colors.HexColor('#F5F5F5')
MID_GRAY    = colors.HexColor('#CCCCCC')
NOTE_BG     = colors.HexColor('#FFF8E1')
NOTE_BORDER = colors.HexColor('#FFB300')
NOTE_TEXT   = colors.HexColor('#4E3200')

# Register Arabic-capable font from Windows
_ARABIC_FONT = 'Helvetica'
for _fp, _fn in [
    (r'C:\Windows\Fonts\tahoma.ttf',  'Tahoma'),
    (r'C:\Windows\Fonts\arial.ttf',   'Arial'),
]:
    if os.path.exists(_fp):
        try:
            pdfmetrics.registerFont(TTFont(_fn, _fp))
            _ARABIC_FONT = _fn
        except Exception:
            pass
        break


def _next_invoice_number() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'counter.json')
    now = datetime.now()
    y, m = now.year, now.month
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = {}
    if data.get('year') != y or data.get('month') != m:
        data = {'year': y, 'month': m, 'counter': 0}
    data['counter'] += 1
    with open(path, 'w') as f:
        json.dump(data, f)
    return f"{INVOICE_PREFIX}/{y}/{m:02d}/{data['counter']:03d}"


def _to_words(amount: float) -> str:
    whole = int(amount)
    frac  = round((amount - whole) * 100)
    w = num2words(whole).replace(',', '').title()
    if frac:
        return f"AED {w} and {num2words(frac).title()} Fils Only"
    return f"AED {w} Only"


def _to_arabic_words(amount: float) -> str:
    try:
        whole = int(amount)
        ar = num2words(whole, lang='ar')
        full = f"{ar} درهم إماراتي فقط"
        return get_display(arabic_reshaper.reshape(full))
    except Exception:
        return ""


def _draw_label_value(c, x, y, label: str, value: str,
                      label_font='Helvetica-Bold', value_font='Helvetica', size=10):
    c.setFont(label_font, size)
    c.setFillColor(colors.black)
    label_w = c.stringWidth(label, label_font, size)
    c.drawString(x, y, label)
    c.setFont(value_font, size)
    c.drawString(x + label_w + 2, y, value)


def generate_invoice(
    name: str,
    email: str,
    program: int,
    amount: float,
    balance_due: str = 'NA',
    terms: str = 'NA',
    due_date: str = 'NA',
    payment_method: int = 1,
    foreign_amount: float | None = None,
    custom_invoice_number: str | None = None,
    invoice_date: str | None = None,
    output_dir: str | None = None,
) -> tuple[str, str]:

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices')
    os.makedirs(output_dir, exist_ok=True)

    inv_no   = custom_invoice_number.strip() if custom_invoice_number and custom_invoice_number.strip() else _next_invoice_number()
    date_str = invoice_date.strip() if invoice_date and invoice_date.strip() else datetime.now().strftime("%d %B %Y")
    fmt_amt  = f"{amount:,.0f}"
    words_en = _to_words(amount)
    words_ar = _to_arabic_words(amount)

    safe     = "".join(ch for ch in name if ch.isalnum() or ch == ' ').strip().replace(' ', '_')
    filepath = os.path.join(output_dir, f"Invoice_{inv_no.replace('/', '_')}_{safe}.pdf")

    c = rl_canvas.Canvas(filepath, pagesize=A4)
    W, H = A4
    LM = 15 * mm
    RM = W - 15 * mm

    # ── Header band ──────────────────────────────────────────
    HDR_H = 38 * mm
    c.setFillColor(NAVY)
    c.rect(0, H - HDR_H, W, HDR_H, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 15)
    c.drawString(LM, H - 10 * mm, COMPANY_NAME)
    c.setFont('Helvetica', 9)
    c.drawString(LM, H - 17 * mm, f"Corporate Tax Registration Number : {TAX_REG}")
    c.drawString(LM, H - 23 * mm, WEBSITE)
    c.drawString(LM, H - 29 * mm, ADDRESS_L1)
    c.drawString(LM, H - 35 * mm, ADDRESS_L2)

    c.setFont('Helvetica-Bold', 32)
    c.drawRightString(RM, H - 22 * mm, "INVOICE")

    # ── Invoice meta (right side) ─────────────────────────────
    c.setFillColor(colors.black)
    mx = 118 * mm
    my = H - 46 * mm
    for label, value in [
        ("Invoice # :",   inv_no),
        ("Date # :",      date_str),
        ("Balance Due :", str(balance_due)),
        ("Terms :",       str(terms)),
        ("Due date :",    str(due_date)),
    ]:
        c.setFont('Helvetica-Bold', 10)
        c.drawString(mx, my, label)
        c.setFont('Helvetica', 10)
        c.drawRightString(RM, my, value)
        my -= 7.5 * mm

    # ── Bill To ───────────────────────────────────────────────
    bty = H - 90 * mm
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(LM, bty, "Bill To :")

    c.setFillColor(colors.black)
    _draw_label_value(c, LM, bty - 9 * mm,  "Name :   ", name,  size=10)
    _draw_label_value(c, LM, bty - 17 * mm, "Email ID :   ", email, size=10)

    rule_y = bty - 22 * mm
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(0.5)
    c.line(LM, rule_y, RM, rule_y)

    # ── Line-item table ───────────────────────────────────────
    ph = ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9,
                        textColor=colors.white, alignment=TA_CENTER, leading=12)
    pb = ParagraphStyle('b', fontName='Helvetica', fontSize=9,
                        textColor=colors.black, alignment=TA_CENTER, leading=12)
    pd = ParagraphStyle('d', fontName='Helvetica', fontSize=9,
                        textColor=colors.black, alignment=TA_LEFT,  leading=12)
    ps = ParagraphStyle('s', fontName='Helvetica-Bold', fontSize=9,
                        textColor=colors.black, alignment=TA_LEFT,  leading=12)

    def H_(t): return Paragraph(t, ph)
    def C(t):  return Paragraph(str(t), pb)
    def D(t):  return Paragraph(str(t), pd)

    col_w = [8*mm, 65*mm, 12*mm, 18*mm, 20*mm, 20*mm, 15*mm, 22*mm]

    tbl_data = [
        [H_('Sl\nNo'), H_('Descriptions'), H_('Unit'), H_('Qty\n(Days/Month)'),
         H_('Rate'), H_('S. Total'), H_('VAT\n(5%)'), H_('Amount\n(AED)')],
        [C('1'), D(PROGRAMS[program]), C('1'), C(''),
         C(fmt_amt), C(fmt_amt), C('NA'), C(fmt_amt)],
        [C('2'), D(''), C(''), C(''), C(''), C(''), C('-'), C('-')],
        [C('3'), D(''), C(''), C(''), C(''), C(''), C('-'), C('-')],
        [C('4'), D(''), C(''), C(''), C(''), C(''), C('-'), C('-')],
        [C(''), Paragraph('Sub Total', ps), C(''), C(''),
         C(''), C(fmt_amt), C('-'), C(fmt_amt)],
    ]

    tbl = Table(tbl_data, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0),  (-1, 0),  NAVY),
        ('BACKGROUND',    (0, 2),  (-1, 2),  LIGHT_GRAY),
        ('BACKGROUND',    (0, 4),  (-1, 4),  LIGHT_GRAY),
        ('BACKGROUND',    (0, -1), (-1, -1), LIGHT_GRAY),
        ('GRID',          (0, 0),  (-1, -1), 0.4, MID_GRAY),
        ('VALIGN',        (0, 0),  (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0),  (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0),  (-1, -1), 4),
        ('LEFTPADDING',   (0, 0),  (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0),  (-1, -1), 4),
    ]))

    tbl_top = rule_y - 3 * mm
    tbl_w, tbl_h = tbl.wrapOn(c, sum(col_w), H)
    tbl.drawOn(c, LM, tbl_top - tbl_h)

    # ── Amount in words (English + Arabic) + Total ───────────
    aw_y = tbl_top - tbl_h - 9 * mm
    c.setFont('Helvetica-Oblique', 9)
    c.setFillColor(colors.black)
    c.drawString(LM, aw_y, f"(Amount in words: {words_en})")
    c.setFont('Helvetica-Bold', 11)
    c.drawRightString(RM, aw_y, f"Total AED   {fmt_amt}")

    next_y = aw_y - 7 * mm
    if words_ar:
        c.setFont(_ARABIC_FONT, 9)
        c.setFillColor(colors.black)
        c.drawRightString(RM, next_y, words_ar)
        next_y -= 7 * mm

    # ── Payment note box ─────────────────────────────────────
    if payment_method in (2, 3) and foreign_amount is not None:
        currency = "USD" if payment_method == 2 else "INR"
        method   = "PayPal" if payment_method == 2 else "Google Pay"
        fmt_foreign = f"{foreign_amount:,.0f}"
        note_line1 = "Payment Note"
        note_line2 = (f"An amount of {currency} {fmt_foreign} was received via {method}, "
                      f"equivalent to AED {fmt_amt}.")

        box_top  = next_y - 4 * mm
        box_h    = 18 * mm
        box_x    = LM
        box_w    = RM - LM

        c.setFillColor(NOTE_BG)
        c.setStrokeColor(NOTE_BORDER)
        c.setLineWidth(1)
        c.roundRect(box_x, box_top - box_h, box_w, box_h, 4, fill=1, stroke=1)

        c.setFillColor(NOTE_TEXT)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(box_x + 5 * mm, box_top - 6 * mm, note_line1)
        c.setFont('Helvetica', 9)
        c.drawString(box_x + 5 * mm, box_top - 13 * mm, note_line2)

    # ── Footer band ───────────────────────────────────────────
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica', 8)
    c.drawCentredString(
        W / 2, 5 * mm,
        f"{COMPANY_NAME}   Licence No. {LICENCE_NO}   {ADDRESS_L1} {ADDRESS_L2}"
    )

    c.save()
    return filepath, inv_no
