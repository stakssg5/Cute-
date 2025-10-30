import os
from typing import Any, Dict, Optional

import stripe
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, validator

try:
    # Load environment variables from .env if present (optional convenience)
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # Safe to continue if python-dotenv isn't available
    pass


def get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


STRIPE_SECRET_KEY = get_env("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = get_env("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = get_env("STRIPE_WEBHOOK_SECRET")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class CreatePaymentIntentRequest(BaseModel):
    amount: int = Field(..., description="Amount in the smallest currency unit (e.g., cents)")
    currency: str = Field("usd", description="Currency code, e.g. 'usd'")

    @validator("amount")
    def amount_must_be_positive(cls, v: int) -> int:  # noqa: N805
        if v <= 0:
            raise ValueError("amount must be > 0")
        return v


app = FastAPI(title="Stripe Wiring (Test Mode)")

# Allow local dev from any origin (frontend demos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"]
)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Very small demo page using Stripe Elements in test mode.

    Set STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY in your environment.
    """
    if not STRIPE_PUBLISHABLE_KEY:
        return (
            "<h3>Stripe demo</h3>"
            "<p>Set <code>STRIPE_PUBLISHABLE_KEY</code> and restart, then reload this page.</p>"
        )

    return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>Stripe Test Payment</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'; margin: 2rem; }}
    #container {{ max-width: 560px; margin: auto; }}
    .row {{ margin: 12px 0; }}
    button {{ padding: 10px 14px; font-size: 16px; }}
  </style>
  <script src=\"https://js.stripe.com/v3/\"></script>
</head>
<body>
  <div id=\"container\">
    <h2>Stripe Test Payment</h2>
    <p>Use Stripe test card <b>4242 4242 4242 4242</b> with any future expiry and CVC.</p>

    <div class=\"row\">
      <label>Amount (USD cents): <input id=\"amount\" type=\"number\" value=\"1999\" min=\"50\" step=\"1\" /></label>
    </div>

    <form id=\"payment-form\">
      <div id=\"payment-element\"></div>
      <div class=\"row\"><button id=\"submit\" type=\"submit\">Pay</button></div>
      <div id=\"message\" class=\"row\"></div>
    </form>
  </div>

  <script>
    const stripe = Stripe('{STRIPE_PUBLISHABLE_KEY}');
    let elements;

    async function setup(amountCents) {{
      const res = await fetch('/create-payment-intent', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ amount: amountCents, currency: 'usd' }})
      }});
      const data = await res.json();
      if (!data.clientSecret) {{
        document.getElementById('message').textContent = 'Failed to create PaymentIntent';
        return;
      }}
      elements = stripe.elements({{ clientSecret: data.clientSecret }});
      const paymentElement = elements.create('payment');
      paymentElement.mount('#payment-element');
    }}

    setup(parseInt(document.getElementById('amount').value, 10));

    document.getElementById('payment-form').addEventListener('submit', async (e) => {{
      e.preventDefault();
      const {{error}} = await stripe.confirmPayment({{
        elements,
        confirmParams: {{
          return_url: window.location.href
        }}
      }});
      const msg = document.getElementById('message');
      if (error) {{ msg.textContent = error.message; }} else {{ msg.textContent = 'Processing…'; }}
    }});
  </script>
</body>
</html>
"""


@app.post("/create-payment-intent")
async def create_payment_intent(payload: CreatePaymentIntentRequest) -> JSONResponse:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY not configured")

    try:
        intent = stripe.PaymentIntent.create(
            amount=payload.amount,
            currency=payload.currency,
            automatic_payment_methods={"enabled": True},
        )
        return JSONResponse({"clientSecret": intent["client_secret"]})
    except stripe.error.StripeError as e:  # type: ignore[attr-defined]
        # Return a safe error to the client; log full error on server if desired
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    # Optional: secure webhook endpoint
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=STRIPE_WEBHOOK_SECRET,
            )
        except Exception as e:  # pragma: no cover - signature verification branch
            raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")
    else:
        # For quickstart without a webhook secret, parse as JSON (not secure for prod)
        try:
            event = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)

    # Minimal demo handling
    if event_type == "payment_intent.succeeded":
        # In real apps, fulfill the purchase here
        pass

    return JSONResponse({"received": True})


# Convenience for `python -m app.stripe_server`
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.stripe_server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
