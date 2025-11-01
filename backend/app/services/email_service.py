"""
Email service for sending notifications.
"""
import aiosmtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)

        Returns:
            True if successful, False otherwise
        """
        try:
            message = EmailMessage()
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(body)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
            )
            print(f"✓ Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            print(f"✗ Error sending email to {to_email}: {e}")
            return False

    async def send_prospect_confirmation(
        self,
        prospect_email: str,
        first_name: str
    ) -> bool:
        """
        Send confirmation email to prospect after lead submission.

        Args:
            prospect_email: Prospect's email address
            first_name: Prospect's first name

        Returns:
            True if successful, False otherwise
        """
        subject = "Thank you for your submission"
        body = f"""
Dear {first_name},

Thank you for submitting your information to AlmaLead.

We have received your application and our team will review it shortly.
You can expect to hear from us within 2-3 business days.

Best regards,
The AlmaLead Team
        """.strip()

        return await self.send_email(prospect_email, subject, body)

    async def send_attorney_notification(
        self,
        attorney_email: str,
        prospect_first_name: str,
        prospect_last_name: str,
        prospect_email: str,
        lead_id: str
    ) -> bool:
        """
        Send notification email to attorney about new lead.

        Args:
            attorney_email: Attorney's email address
            prospect_first_name: Prospect's first name
            prospect_last_name: Prospect's last name
            prospect_email: Prospect's email address
            lead_id: Lead ID

        Returns:
            True if successful, False otherwise
        """
        subject = f"New Lead Submission: {prospect_first_name} {prospect_last_name}"
        body = f"""
New lead submission received:

Name: {prospect_first_name} {prospect_last_name}
Email: {prospect_email}
Lead ID: {lead_id}

Please review the lead in the dashboard.
        """.strip()

        return await self.send_email(attorney_email, subject, body)


# Global email service instance
email_service = EmailService()
