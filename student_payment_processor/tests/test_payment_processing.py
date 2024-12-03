import unittest
from src.backend.app import app, db
import stripe

class PaymentProcessingTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()

    def test_payment_processing(self):
        payment_data = {
            'user_id': 1,
            'amount': 100.00,
            'currency': 'usd'
        }
        response = self.app.post('/payment', json=payment_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('client_secret', response.json)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    unittest.main()
