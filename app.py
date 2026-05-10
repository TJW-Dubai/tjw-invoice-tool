import io
import os
import csv
import zipfile
from typing import Optional
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from invoice_generator import generate_invoice, INVOICE_PREFIX

app = Flask(__name__)

SAMPLE_CSV_ROWS = [
    ["Name", "Email", "Program", "Amount", "Invoice Number",
     "Invoice Date", "Balance Due", "Terms", "Due Date",
     "Payment Method", "Foreign Amount"],
    ["Arindam Sengupta", "arindam@email.com", "1", "1800",
     "TJW/2026/03/001", "15 March 2026", "NA", "Net 30",
     "15 April 2026", "1", ""],
    ["Priya Sharma", "priya@email.com", "2", "3500",
     "TJW/2026/03/002", "20 March 2026", "AED 1750", "Net 30",
     "20 April 2026", "2", "953"],
]


def _parse_float(val: str) -> Optional[float]:
    val = (val or '').strip().replace(',', '')
    try:
        return float(val) if val else None
    except ValueError:
        return None


def _suggested_invoice_number() -> str:
    """Return a suggested next invoice number without incrementing the counter."""
    from invoice_generator import _next_invoice_number as _get
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'counter.json')
    now = datetime.now()
    y, m = now.year, now.month
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
            if data.get('year') == y and data.get('month') == m:
                next_n = data.get('counter', 0) + 1
            else:
                next_n = 1
        except Exception:
            next_n = 1
    else:
        next_n = 1
    return f"{INVOICE_PREFIX}/{y}/{m:02d}/{next_n:03d}"


@app.route('/')
def index():
    suggested = _suggested_invoice_number()
    return render_template('index.html', suggested_invoice_no=suggested)


@app.route('/api/next-invoice-number')
def next_invoice_number():
    return jsonify(number=_suggested_invoice_number())


@app.route('/generate', methods=['POST'])
def generate():
    try:
        name           = request.form['name'].strip()
        email          = request.form['email'].strip()
        program        = int(request.form['program'])
        amount_raw     = request.form['amount'].strip().replace(',', '')
        amount         = float(amount_raw)
        balance_due    = request.form.get('balance_due', '').strip() or 'NA'
        terms          = request.form.get('terms', '').strip() or 'NA'
        due_date       = request.form.get('due_date', '').strip() or 'NA'
        payment_method = int(request.form.get('payment_method', 1))
        foreign_raw    = request.form.get('foreign_amount', '').strip()
        foreign_amount = _parse_float(foreign_raw)
        custom_inv_no  = request.form.get('invoice_number', '').strip() or None

        if not name or not email or amount <= 0:
            return jsonify(error="Name, email and a positive amount are required."), 400

        path, inv_no = generate_invoice(
            name=name, email=email, program=program, amount=amount,
            balance_due=balance_due, terms=terms, due_date=due_date,
            payment_method=payment_method, foreign_amount=foreign_amount,
            custom_invoice_number=custom_inv_no,
        )

        return send_file(
            path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=os.path.basename(path),
        )
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        return jsonify(error=f"Unexpected error: {e}"), 500


@app.route('/bulk')
def bulk():
    return render_template('bulk.html')


@app.route('/bulk/upload', methods=['POST'])
def bulk_upload():
    file = request.files.get('csv_file')
    if not file or not file.filename:
        return "No file uploaded.", 400

    try:
        content = file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        return "Could not read file. Please save the CSV as UTF-8.", 400

    reader  = csv.DictReader(io.StringIO(content))
    errors  = []
    count   = 0

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, row in enumerate(reader, start=2):
            try:
                name    = row.get('Name', '').strip()
                email   = row.get('Email', '').strip()
                prog_raw = row.get('Program', '').strip()
                program  = int(prog_raw) if prog_raw else 1
                amount   = _parse_float(row.get('Amount', ''))

                if not name or not email:
                    raise ValueError("Name and Email are required.")
                if amount is None or amount <= 0:
                    raise ValueError("Amount is required and must be a positive number.")

                balance_due    = row.get('Balance Due', '').strip() or 'NA'
                terms          = row.get('Terms', '').strip() or 'NA'
                due_date       = row.get('Due Date', '').strip() or 'NA'
                payment_method = int(row.get('Payment Method', '1').strip() or '1')
                foreign_amount = _parse_float(row.get('Foreign Amount', ''))
                custom_inv_no  = row.get('Invoice Number', '').strip() or None
                inv_date       = row.get('Invoice Date', '').strip() or None

                # Generate entirely in memory — no disk writes, no cleanup needed
                pdf_bytes, filename, inv_no = generate_invoice(
                    name=name, email=email, program=program, amount=amount,
                    balance_due=balance_due, terms=terms, due_date=due_date,
                    payment_method=payment_method, foreign_amount=foreign_amount,
                    custom_invoice_number=custom_inv_no, invoice_date=inv_date,
                    return_bytes=True,
                )
                zf.writestr(filename, pdf_bytes)
                count += 1

            except Exception as e:
                errors.append(f"Row {i}: {e}")

        if errors:
            zf.writestr("ERRORS.txt", "\n".join(errors))

    if count == 0:
        return "No invoices could be generated.\n\n" + "\n".join(errors), 400

    zip_buf.seek(0)
    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name='TJW_Invoices_Bulk.zip',
    )


@app.route('/sample-csv')
def sample_csv():
    buf = io.StringIO()
    csv.writer(buf).writerows(SAMPLE_CSV_ROWS)
    output = io.BytesIO(buf.getvalue().encode('utf-8'))
    return send_file(output, mimetype='text/csv', as_attachment=True,
                     download_name='TJW_Invoice_Template.csv')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

