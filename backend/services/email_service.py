"""
Email service for sending password reset and other notification emails.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from config.settings import EmailSettings


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self, email_settings: EmailSettings):
        """Initialize email service with settings."""
        self.settings = email_settings
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str = None) -> bool:
        """
        Send password reset email to user.
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User's name (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        reset_link = f"{self.settings.base_url}/reset-password/{reset_token}"
        
        # Create email content
        subject = "Password Reset Request - LocalAI"
        
        # HTML email content
        html_content = self._create_reset_email_html(reset_link, user_name or "User")
        
        # Plain text email content (fallback)
        text_content = self._create_reset_email_text(reset_link, user_name or "User")
        
        return self._send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    def _create_reset_email_html(self, reset_link: str, user_name: str) -> str:
        """Create HTML email content for password reset."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Request</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: white; padding: 30px; border: 1px solid #dee2e6; }}
                .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 5px 5px; font-size: 12px; color: #6c757d; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Password Reset Request</h1>
                </div>
                
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>We received a request to reset your password for your LocalAI account. If you made this request, click the button below to reset your password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset My Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace;">{reset_link}</p>
                    
                    <div class="warning">
                        <strong>Important:</strong>
                        <ul>
                            <li>This link will expire in 6 hours for security reasons</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your current password will remain unchanged until you create a new one</li>
                        </ul>
                    </div>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password won't be changed.</p>
                    
                    <p>For security reasons, we cannot tell you who requested this reset, but it was requested from the IP address that sent this request.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent by LocalAI Chat API</p>
                    <p>If you have any questions, please contact your system administrator.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_reset_email_text(self, reset_link: str, user_name: str) -> str:
        """Create plain text email content for password reset."""
        return f"""
Password Reset Request - LocalAI

Hello {user_name},

We received a request to reset your password for your LocalAI account.

If you made this request, click the following link to reset your password:
{reset_link}

IMPORTANT:
- This link will expire in 6 hours for security reasons
- If you didn't request this reset, please ignore this email
- Your current password will remain unchanged until you create a new one

If you didn't request a password reset, you can safely ignore this email. Your password won't be changed.

For security reasons, we cannot tell you who requested this reset, but it was requested from the IP address that sent this request.

---
This email was sent by LocalAI Chat API
If you have any questions, please contact your system administrator.
        """
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Skip sending if SMTP not configured
        if not self.settings.smtp_username or not self.settings.smtp_password:
            print(f"DEBUG: Email would be sent to {to_email}")
            print(f"DEBUG: Subject: {subject}")
            print(f"DEBUG: Reset link in content: {html_content[html_content.find('http'):html_content.find('http')+100]}")
            return True
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.settings.from_name} <{self.settings.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            if self.settings.use_ssl:
                server = smtplib.SMTP_SSL(self.settings.smtp_server, self.settings.smtp_port)
            else:
                server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
                if self.settings.use_tls:
                    server.starttls()
            
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(message)
            server.quit()
            
            print(f"Password reset email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test SMTP connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.settings.smtp_username or not self.settings.smtp_password:
            return False, "SMTP credentials not configured"
        
        try:
            if self.settings.use_ssl:
                server = smtplib.SMTP_SSL(self.settings.smtp_server, self.settings.smtp_port)
            else:
                server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
                if self.settings.use_tls:
                    server.starttls()
            
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.quit()
            
            return True, "SMTP connection successful"
            
        except Exception as e:
            return False, f"SMTP connection failed: {str(e)}"