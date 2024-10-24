# send_emails.py

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class SendEmail():
    def __init__(self):
        # Load credentials from environment variables
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.port = int(os.getenv("SMTP_PORT", 465))  # Default to 465 if not set in .env
        self.receiver_email = os.getenv("EMAIL_RECEIVER")

        if not all([self.sender_email, self.password, self.smtp_server, self.receiver_email]):
            raise ValueError("Missing one or more environment variables (EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, EMAIL_RECEIVER)")

        # Define attributes for subject and body
        self.subject = ""
        self.body = ""

    def set_subject(self, subject):
        self.subject = subject

    def set_body(self, body):
        self.body = body

    def send_email(self):
        # Create a secure SSL context
        context = ssl.create_default_context()

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.receiver_email
        msg["Subject"] = self.subject

        # Attach the email body to the email
        msg.attach(MIMEText(self.body, "plain"))

        try:
            # Connect to the SMTP server and send the email
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")



    