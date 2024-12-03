from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import stripe
import os

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/student_payments')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = app.config['STRIPE_SECRET_KEY']

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(10), default='en')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

@app.route('/payment', methods=['POST'])
def process_payment():
    try:
        data = request.json
        # Validate payment details
        payment_intent = stripe.PaymentIntent.create(
            amount=int(data['amount'] * 100),  # Convert to cents
            currency=data['currency']
        )
        
        # Save transaction
        transaction = Transaction(
            user_id=data['user_id'],
            amount=data['amount'],
            currency=data['currency'],
            status='pending'
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            'client_secret': payment_intent.client_secret,
            'transaction_id': transaction.id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
