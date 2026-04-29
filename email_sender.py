import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

SENDER = "athejobworkshop@gmail.com"

PROGRAM_NAMES = {
    1: "Five Modules Advisory Program (Interview Assurance Program)",
    2: "Comprehensive End to End Job Search Management and Advisory",
}


def send_onboarding_email(
    recipient_email: str,
    recipient_name: str,
    program: int,
    invoice_path: str,
    invoice_number: str,
    amount: float,
    payment_method: int = 1,
    foreign_amount: float | None = None,
) -> None:
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    if not app_password:
        raise EnvironmentError(
            "GMAIL_APP_PASSWORD is not set. Please add it to your .env file."
        )

    program_name = PROGRAM_NAMES[program]
    fmt_amount   = f"{amount:,.0f}"
    date_str     = datetime.now().strftime("%d %B %Y")

    # Build payment note strings
    payment_note_plain = ""
    payment_note_html  = ""
    if payment_method in (2, 3) and foreign_amount is not None:
        currency     = "USD" if payment_method == 2 else "INR"
        method       = "PayPal" if payment_method == 2 else "Google Pay"
        fmt_foreign  = f"{foreign_amount:,.0f}"
        note_text    = (f"An amount of {currency} {fmt_foreign} was received via {method}, "
                        f"equivalent to AED {fmt_amount}.")
        payment_note_plain = f"\nPayment Note: {note_text}\n"
        payment_note_html  = f"""
      <div style="background: #FFF8E1; border: 1px solid #FFB300; border-radius: 6px;
                  padding: 14px 18px; margin: 20px 0;">
        <strong style="color: #4E3200;">Payment Note</strong><br>
        <span style="color: #4E3200;">{note_text}</span>
      </div>"""

    msg = MIMEMultipart('alternative')
    msg['From']    = f"The Job Workshop <{SENDER}>"
    msg['To']      = recipient_email
    msg['Subject'] = f"Welcome to The Job Workshop – Invoice {invoice_number}"

    plain = f"""\
Dear {recipient_name},

Welcome to The Job Workshop! We are truly delighted to have you on board.

You have enrolled in:
  {program_name}

Please find your invoice attached (Invoice No. {invoice_number}, AED {fmt_amount}).
{payment_note_plain}
Our team will be reaching out to you shortly with your onboarding details and next steps.

Should you have any questions in the meantime, please feel free to reply to this email.

Warm regards,
The Job Workshop Team
Career Catalyst Venture LLC
Shams Business Centre, Sharjah Media City Free Zone,
Al Messaned, Sharjah, UAE
"""

    html = f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; padding: 0 20px;">

    <div style="background: #1B3A5C; padding: 24px 28px; border-radius: 6px 6px 0 0;">
      <h2 style="color: white; margin: 0; font-size: 20px;">Welcome to The Job Workshop</h2>
    </div>

    <div style="border: 1px solid #ddd; border-top: none; padding: 32px 28px; border-radius: 0 0 6px 6px;">
      <p>Dear <strong>{recipient_name}</strong>,</p>

      <p>We are truly delighted to welcome you on board at <strong>The Job Workshop</strong>!</p>

      <p>You have successfully enrolled in:</p>
      <div style="background: #F5F5F5; padding: 14px 18px; border-left: 4px solid #1B3A5C;
                  border-radius: 0 4px 4px 0; margin: 0 0 20px 0; font-style: italic;">
        {program_name}
      </div>

      <p>Please find your invoice attached to this email.</p>

      <table style="width: 100%; background: #F9F9F9; border-collapse: collapse;
                    border-radius: 4px; overflow: hidden; margin-bottom: 20px;">
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 10px 16px; font-weight: bold; width: 40%;">Invoice No.</td>
          <td style="padding: 10px 16px;">{invoice_number}</td>
        </tr>
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 10px 16px; font-weight: bold;">Amount</td>
          <td style="padding: 10px 16px;">AED {fmt_amount}</td>
        </tr>
        <tr>
          <td style="padding: 10px 16px; font-weight: bold;">Date</td>
          <td style="padding: 10px 16px;">{date_str}</td>
        </tr>
      </table>
{payment_note_html}
      <p>Our team will reach out to you shortly with your onboarding details and the next steps
         to kick-start your journey.</p>

      <p>Should you have any questions, please don't hesitate to reply to this email.</p>

      <p style="margin-top: 32px;">
        Warm regards,<br>
        <strong>The Job Workshop Team</strong><br>
        Career Catalyst Venture LLC
      </p>
    </div>

    <p style="color: #aaa; font-size: 11px; text-align: center; margin-top: 20px;">
      Career Catalyst Venture LLC &nbsp;|&nbsp; Licence No. 2535552.01<br>
      Shams Business Centre, Sharjah Media City Free Zone, Al Messaned, Sharjah, UAE
    </p>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html,  'html'))

    with open(invoice_path, 'rb') as f:
        pdf = MIMEApplication(f.read(), _subtype='pdf')
        pdf.add_header('Content-Disposition', 'attachment',
                       filename=os.path.basename(invoice_path))
        msg.attach(pdf)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER, app_password)
        server.sendmail(SENDER, recipient_email, msg.as_string())
