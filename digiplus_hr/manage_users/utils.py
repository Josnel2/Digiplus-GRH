from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def send_otp_email(user, purpose='login'):
    """
    Envoyer un code OTP par email
    purpose: 'login' ou 'password_reset'
    """
    # otp_code = OTP.generate_code()
    otp_code = '123456'  # Pour les tests, à retirer en production

    OTP.objects.create(user=user, code=otp_code)
    
    if purpose == 'password_reset':
        subject = 'Réinitialisation de votre mot de passe - Digiplus RH'
        message = f"""
Bonjour {user.first_name},

Vous avez demandé la réinitialisation de votre mot de passe pour le Portail RH Digiplus.

Votre code de vérification est : {otp_code}

Ce code expire dans 5 minutes.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email et votre mot de passe restera inchangé.

Cordialement,
L'équipe Digiplus RH
        """
    else:
        subject = 'Votre code de vérification OTP'
        message = f"""
Bonjour {user.first_name},

Votre code de vérification OTP est : {otp_code}

Ce code expirera dans 5 minutes.

Cordialement,
L'équipe DigiPlus HR
        """
    
    # send_mail(
    #     subject,
    #     message,
    #     settings.DEFAULT_FROM_EMAIL,
    #     [user.email],
    #     fail_silently=False,
    # )
    
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