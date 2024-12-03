from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = 'payments@studentprocessor.com'

    def send_receipt(self, to_email, transaction_details):
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject='Payment Receipt',
            html_content=f'''
            <strong>Payment Receipt</strong>
            <p>Amount: {transaction_details['amount']} {transaction_details['currency']}</p>
            <p>Transaction ID: {transaction_details['transaction_id']}</p>
            '''
        )
        try:
            response = self.sg.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
