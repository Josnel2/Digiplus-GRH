from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

from .models import OTP

def send_otp_email(user, purpose='login'):
    """
    Envoyer un code OTP par email
    purpose: 'login' ou 'password_reset'
    """
    otp_code = OTP.generate_code()
    OTP.objects.create(user=user, code=otp_code)

    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    
    if purpose == 'password_reset':
        subject = 'Réinitialisation de votre mot de passe - Digiplus RH'
        text_template = 'emails/otp_password_reset.txt'
        html_template = 'emails/otp_password_reset.html'
    else:
        subject = 'Votre code de vérification OTP'
        text_template = 'emails/otp_login.txt'
        html_template = 'emails/otp_login.html'

    context = {
        'first_name': user.first_name,
        'otp_code': otp_code,
        'expiry_minutes': expiry_minutes,
    }

    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=[user.email])
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=False)
    
    return otp_code

def send_credentials_email(user, password):
    """Envoyer les identifiants par email lors de la création d'un compte"""
    subject = 'Vos identifiants DigiPlus HR'

    portal_url = getattr(settings, 'PORTAL_URL', '[URL_DU_PORTAL]')
    context = {
        'first_name': user.first_name,
        'email': user.email,
        'password': password,
        'portal_url': portal_url,
    }

    text_body = render_to_string('emails/credentials.txt', context)
    html_body = render_to_string('emails/credentials.html', context)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=[user.email])
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=False)