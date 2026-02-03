import stripe, os
from dotenv import load_dotenv
import os
import stripe

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")



stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[{
        "price_data": {
            "currency": "usd",
            "product_data": {"name": "Test"},
            "unit_amount": 900,
        },
        "quantity": 1,
    }],
    mode="payment",
    success_url="http://localhost:8000",
    cancel_url="http://localhost:8000",
)
