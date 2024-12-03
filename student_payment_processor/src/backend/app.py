from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import relationship
from sqlalchemy import func
import stripe
import os
import re
import phonenumbers
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/student_payments')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = app.config['STRIPE_SECRET_KEY']

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    language = db.Column(db.String(10), default='en')
    stripe_customer_id = db.Column(db.String(50), unique=True, nullable=True)
    
    # Relationships
    transactions = relationship('Transaction', back_populates='user')
    
    @classmethod
    def validate_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError:
            return None
    
    @classmethod
    def validate_phone(cls, phone_number):
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            return phonenumbers.is_valid_number(parsed_number)
        except:
            return False

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    stripe_payment_intent_id = db.Column(db.String(50), unique=True, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    user = relationship('User', back_populates='transactions')
    
    @classmethod
    def validate_amount(cls, amount):
        return amount > 0

class PaymentService:
    @staticmethod
    def create_stripe_customer(user):
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name
            )
            return customer.id
        except stripe.error.StripeError as e:
            print(f"Stripe customer creation error: {e}")
            return None
    
    @staticmethod
    def create_payment_intent(amount, currency, customer_id=None):
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                customer=customer_id,
                payment_method_types=['card']
            )
            return payment_intent
        except stripe.error.StripeError as e:
            print(f"Payment intent creation error: {e}")
            return None

@app.route('/user', methods=['POST'])
def create_user():
    try:
        data = request.json
        email = User.validate_email(data.get('email'))
        
        if not email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        user = User(
            email=email,
            name=data.get('name'),
            language=data.get('language', 'en')
        )
        
        if data.get('phone_number'):
            if not User.validate_phone(data['phone_number']):
                return jsonify({'error': 'Invalid phone number'}), 400
            user.phone_number = data['phone_number']
        
        db.session.add(user)
        db.session.commit()
        
        # Create Stripe customer
        stripe_customer_id = PaymentService.create_stripe_customer(user)
        if stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
            db.session.commit()
        
        return jsonify({
            'user_id': user.id,
            'stripe_customer_id': stripe_customer_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/payment', methods=['POST'])
def process_payment():
    try:
        data = request.json
        user = User.query.get(data.get('user_id'))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not Transaction.validate_amount(data.get('amount')):
            return jsonify({'error': 'Invalid payment amount'}), 400
        
        payment_intent = PaymentService.create_payment_intent(
            amount=data['amount'], 
            currency=data['currency'],
            customer_id=user.stripe_customer_id
        )
        
        if not payment_intent:
            return jsonify({'error': 'Payment processing failed'}), 500
        
        transaction = Transaction(
            user_id=user.id,
            amount=data['amount'],
            currency=data['currency'],
            status='pending',
            stripe_payment_intent_id=payment_intent.id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'client_secret': payment_intent.client_secret,
            'transaction_id': transaction.id,
            'stripe_payment_intent_id': payment_intent.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
