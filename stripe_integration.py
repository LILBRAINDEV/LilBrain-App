from flask import Flask, request, redirect, render_template
import stripe

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lilbrain_api_key'

# Replace with your Stripe test secret key
stripe.api_key = 'sk_test_XXXXXXXXXXXXXXXXXXXXXXXX'

@app.route("/subscribe")
def subscribe_page():
    return render_template("subscribe.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    username = request.form.get("username")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Lil Brain Premium"},
                    "unit_amount": 299,  # $2.99
                    "recurring": {"interval": "month"}
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"http://localhost:5000/confirm?username={username}",
            cancel_url="http://localhost:5000/",
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e)

@app.route("/confirm")
def confirm_subscription():
    username = request.args.get("username")
    conn = sqlite3.connect('lilbrain.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = 1 WHERE username = ?", (username,))
    conn.commit()
    return f"<h2>{username} is now a Premium member!</h2><a href='/'>Back to Home</a>"
