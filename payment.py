import os
import razorpay

from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not KEY_ID or not KEY_SECRET:
    raise RuntimeError(
        "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env"
    )

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))


def create_payment_order(amount_paise):
    """Create a Razorpay order; amount_paise must be an integer."""
    if not isinstance(amount_paise, int) or amount_paise <= 0:
        raise ValueError("Payment amount must be positive paise.")

    return client.order.create(
        data={
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"snapcart_{os.urandom(8).hex()}",
        }
    )


def verify_payment_signature(
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature,
):
    """Verify the signature returned by Razorpay Checkout."""
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def fetch_payment(razorpay_payment_id):
    """Fetch payment details directly from Razorpay."""
    return client.payment.fetch(razorpay_payment_id)