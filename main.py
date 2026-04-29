import os
import sys
from dotenv import load_dotenv
from invoice_generator import generate_invoice
from email_sender import send_onboarding_email

load_dotenv()


def prompt(text: str, required: bool = True, default: str = 'NA') -> str:
    suffix = ": " if required else f" (press Enter for '{default}'): "
    while True:
        val = input(text + suffix).strip()
        if val:
            return val
        if not required:
            return default
        print("  This field is required.")


def main() -> None:
    print()
    print("=" * 56)
    print("   THE JOB WORKSHOP  -  Invoice & Onboarding Tool")
    print("=" * 56)
    print()

    name  = prompt("Customer Name")
    email = prompt("Customer Email")

    print()
    print("  Programs:")
    print("  1. Five Modules Advisory Program (Interview Assurance Program)")
    print("  2. Comprehensive End to End Job Search Management and Advisory")
    print("     (LinkedIn Management, Engagement, Applications and Outreach)")

    while True:
        choice = prompt("\nSelect Program (1 or 2)")
        if choice in ('1', '2'):
            program = int(choice)
            break
        print("  Please enter 1 or 2.")

    while True:
        raw = prompt("Amount (AED)")
        try:
            amount = float(raw.replace(',', ''))
            if amount <= 0:
                raise ValueError
            break
        except ValueError:
            print("  Please enter a valid positive number.")

    print()
    balance_due = prompt("Balance Due",  required=False, default='NA')
    terms       = prompt("Terms",        required=False, default='NA')
    due_date    = prompt("Due Date",     required=False, default='NA')

    # ── Payment method ────────────────────────────────────────
    print()
    print("  Payment Method:")
    print("  1. AED (direct)")
    print("  2. USD via PayPal")
    print("  3. INR via Google Pay")

    while True:
        pm = prompt("\nSelect Payment Method (1 / 2 / 3)")
        if pm in ('1', '2', '3'):
            payment_method = int(pm)
            break
        print("  Please enter 1, 2, or 3.")

    foreign_amount = None
    if payment_method == 2:
        while True:
            raw = prompt("Amount paid in USD")
            try:
                foreign_amount = float(raw.replace(',', ''))
                if foreign_amount <= 0:
                    raise ValueError
                break
            except ValueError:
                print("  Please enter a valid positive number.")
    elif payment_method == 3:
        while True:
            raw = prompt("Amount paid in INR")
            try:
                foreign_amount = float(raw.replace(',', ''))
                if foreign_amount <= 0:
                    raise ValueError
                break
            except ValueError:
                print("  Please enter a valid positive number.")

    # ── Generate PDF invoice ──────────────────────────────────
    print()
    print("  Generating invoice...")
    try:
        path, inv_no = generate_invoice(
            name=name,
            email=email,
            program=program,
            amount=amount,
            balance_due=balance_due,
            terms=terms,
            due_date=due_date,
            payment_method=payment_method,
            foreign_amount=foreign_amount,
        )
        print(f"  Invoice saved : {path}")
        print(f"  Invoice No.   : {inv_no}")
    except Exception as e:
        print(f"  ERROR - Failed to generate invoice: {e}")
        sys.exit(1)

    # ── Send onboarding email ─────────────────────────────────
    print()
    send = prompt("Send onboarding email to customer? (y/n)", required=False, default='n').lower()
    if send == 'y':
        print("  Sending email...")
        try:
            send_onboarding_email(
                recipient_email=email,
                recipient_name=name,
                program=program,
                invoice_path=path,
                invoice_number=inv_no,
                amount=amount,
                payment_method=payment_method,
                foreign_amount=foreign_amount,
            )
            print(f"  Email sent to {email}")
        except EnvironmentError as e:
            print(f"  ERROR - {e}")
        except Exception as e:
            print(f"  ERROR - Failed to send email: {e}")

    print()
    print("  Done!")
    print()


if __name__ == '__main__':
    main()
