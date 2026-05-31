"""
Password reset utilities for handling OTP generation, email sending, and verification
"""
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import PasswordReset


def generate_otp():
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def generate_token():
    """Generate a random token for password reset"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


def send_password_reset_email(user_email, otp, token):
    """
    Send password reset email with OTP
    
    Args:
        user_email: Email address to send OTP to
        otp: 6-digit OTP code
        token: Password reset token
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = 'Password Reset Request - Student Club'
    message = f"""
    Hello,
    
    You have requested to reset your password for your Student Club account.
    
    Your One-Time Password (OTP) is: {otp}
    
    This OTP will expire in 10 minutes. Please do not share this code with anyone.
    
    If you did not request a password reset, please ignore this email.
    
    Best regards,
    Student Club Administration
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">Password Reset Request</h2>
                
                <p style="color: #666; margin-bottom: 20px;">Hello,</p>
                
                <p style="color: #666; margin-bottom: 20px;">You have requested to reset your password for your Student Club account.</p>
                
                <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin: 30px 0; text-align: center;">
                    <p style="color: #666; margin: 0 0 10px 0;">Your One-Time Password (OTP):</p>
                    <p style="color: #2196F3; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 0;">{otp}</p>
                </div>
                
                <p style="color: #666; margin-bottom: 20px;"><strong>Important:</strong> This OTP will expire in 10 minutes. Please do not share this code with anyone.</p>
                
                <p style="color: #666; margin-bottom: 20px;">If you did not request a password reset, please ignore this email and your account will remain secure.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; margin: 0;">Student Club Administration<br>This is an automated message, please do not reply.</p>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject,
            message,
            'noreply@studentclub.com',
            [user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


def send_college_registration_otp_email(college_email, otp, college_name):
    """Send OTP to verify a college registration email address."""
    subject = 'College Registration OTP - Student Club'
    message = f"""
    Hello,

    A college registration was started for {college_name}.

    Your One-Time Password (OTP) is: {otp}

    This OTP will expire in 10 minutes. Please do not share this code with anyone.

    If you did not request this registration, please ignore this email.

    Best regards,
    Student Club Administration
    """

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">College Registration Verification</h2>
                <p style="color: #666; margin-bottom: 20px;">A college registration was started for <strong>{college_name}</strong>.</p>
                <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin: 30px 0; text-align: center;">
                    <p style="color: #666; margin: 0 0 10px 0;">Your One-Time Password (OTP):</p>
                    <p style="color: #2196F3; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 0;">{otp}</p>
                </div>
                <p style="color: #666; margin-bottom: 20px;"><strong>Important:</strong> This OTP will expire in 10 minutes.</p>
                <p style="color: #666; margin-bottom: 20px;">If you did not request this registration, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px; margin: 0;">Student Club Administration<br>This is an automated message, please do not reply.</p>
            </div>
        </body>
    </html>
    """

    try:
        send_mail(
            subject,
            message,
            'noreply@studentclub.com',
            [college_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send college registration OTP: {str(e)}")
        return False


def create_password_reset_request(user):
    """
    Create a password reset request for a user
    
    Args:
        user: Django User object
    
    Returns:
        tuple: (token, otp) on success, (None, None) on failure
    """
    try:
        # Clean up old reset requests
        PasswordReset.objects.filter(
            user=user,
            is_used=False,
            expires_at__lt=timezone.now()
        ).delete()
        
        # Generate token and OTP
        token = generate_token()
        otp = generate_otp()
        
        # Create new password reset record
        expires_at = timezone.now() + timedelta(minutes=10)
        reset_request = PasswordReset.objects.create(
            user=user,
            token=token,
            otp=otp,
            expires_at=expires_at
        )
        
        return token, otp
    except Exception as e:
        print(f"Error creating password reset request: {str(e)}")
        return None, None


def verify_otp_and_get_reset_request(token, otp):
    """
    Verify OTP and return the password reset request
    
    Args:
        token: Reset token
        otp: User-provided OTP
    
    Returns:
        PasswordReset object if OTP is valid, None otherwise
    """
    try:
        reset_request = PasswordReset.objects.get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        if reset_request.otp == otp:
            return reset_request
        return None
    except PasswordReset.DoesNotExist:
        return None


def reset_user_password(reset_request, new_password):
    """
    Reset user password using the reset request
    
    Args:
        reset_request: PasswordReset object
        new_password: New password to set
    
    Returns:
        bool: True if password reset successfully, False otherwise
    """
    try:
        user = reset_request.user
        user.set_password(new_password)
        user.save()
        
        # Mark reset request as used
        reset_request.is_used = True
        reset_request.save()
        
        return True
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        return False
