
from flask import current_app
from flask_mail import Message
from app import mail


def send_order_confirmation_email(user, orders, total_amount, payment_id):

    if not user.email:
        current_app.logger.warning(
            "Order email skipped: user %s has no email address.",
            user.id
        )
        return False

    lines = [
        f"Hi {user.name or user.username},",
        "",
        "Thank you for shopping with SnapCart <3",
        "Your payment has been verified and your order is confirmed.",
        "",
        "Order details:",
        "-" * 45,
    ]

    for order in orders:
        product_name = order.product.name if order.product else "Product"
        subtotal = order.price * order.quantity

        lines.append(
            f"{product_name} | Quantity: {order.quantity} | "
            f"Unit price: Rs. {order.price:.2f} | "
            f"Subtotal: Rs. {subtotal:.2f}"
        )

    lines.extend([
        "-" * 45,
        f"Total paid: Rs. {total_amount:.2f}",
        f"Razorpay payment ID: {payment_id}",
        "",
        "Thank you for choosing SnapCart :)",
    ])

    message = Message(
        subject="Yay! Your SnapCart order is confirmed",
        recipients=[user.email],
        body="\n".join(lines),
    )

    try:
        mail.send(message)
        current_app.logger.info(
            "Order confirmation email sent to %s for user %s.",
            user.email,
            user.id
        )
        return True

    except Exception:
        current_app.logger.exception(
            "Failed to send order confirmation email to user %s.",
            user.id
        )
        return False
