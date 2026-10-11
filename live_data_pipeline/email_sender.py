from dotenv import load_dotenv
from os import environ
import smtplib
import logging
import sys

# Configure logging
logger = logging.getLogger(__name__)


def verify_smtp_vars(config: dict) -> bool:
    """
    Verify that all required SMTP environment variables are present.

    Parameters:
    config (dict): A dictionary containing environment variables.

    Returns:
    bool: True if all required variables are present, False otherwise.
    """
    required_vars = [
        'SMTP_SERVER',
        'SMTP_PORT',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'EMAIL_FROM_ADDRESS',
        'ALERTS_RECIPIENT_EMAIL_ADDRESS'
    ]
    missing_vars = [var for var in required_vars if not config.get(var)]
    if missing_vars:
        logger.error(
            f"Missing required SMTP environment variables: {', '.join(missing_vars)}")
        return False
    if not config.get('SMTP_PORT').isdigit():
        logger.error("SMTP_PORT must be a valid integer.")
        return False
    return True


def send_email(config: dict, subject: str, body: str) -> None:
    """
    Sends an email to the specified address with the given subject and body.

    Parameters:
    config (dict): A dictionary containing SMTP configuration.
    subject (str): The subject of the email.
    body (str): The body content of the email.

    Returns:
    None
    """
    from email.mime.text import MIMEText

    # Create a MIMEText object to represent the email
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['EMAIL_FROM_ADDRESS']
    msg['To'] = config['ALERTS_RECIPIENT_EMAIL_ADDRESS']

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(config['SMTP_SERVER'], int(config['SMTP_PORT'])) as server:
            server.starttls()
            server.login(config['SMTP_USERNAME'], config['SMTP_PASSWORD'])
            server.send_message(msg)
    except Exception as e:
        raise RuntimeError(f"Error sending email: {e}")


if __name__ == "__main__":
    load_dotenv()
    config = environ

    # verify SMTP vars
    if not verify_smtp_vars(config):
        logger.error("Missing required SMTP environment variables.")
        sys.exit(1)
    send_email(config, "Test Subject", "This is a test email.")
