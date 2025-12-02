from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def send_otp_email(user):
    """Envoyer un code OTP par email"""
    otp_code = OTP.generate_code()
    OTP.objects.create(user=user, code=otp_code)
    
    subject = 'Votre code de vérification OTP'
    message = f"""
    Bonjour {user.first_name},
    
    Votre code de vérification OTP est : {otp_code}
    
    Ce code expirera dans 5 minutes.
    
    Cordialement,
    L'équipe DigiPlus HR
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
    return otp_code

def send_credentials_email(user, password):
    """Envoyer les identifiants par email lors de la création d'un compte"""
    subject = 'Vos identifiants DigiPlus HR'
    message = f"""
    Bonjour {user.first_name},
    
    Votre compte DigiPlus HR a été créé avec succès.
    
    Voici vos identifiants de connexion :
    Email : {user.email}
    Mot de passe : {password}
    
    Vous pouvez vous connecter à l'adresse : [URL_DU_PORTAL]
    
    Cordialement,
    L'équipe DigiPlus HR
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )