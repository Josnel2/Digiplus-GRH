# manage_users/management/commands/create_superadmin.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée un super admin si aucun n\'existe'

    def handle(self, *args, **kwargs):
        if User.objects.filter(is_superadmin=True).exists():
            self.stdout.write(self.style.WARNING('Un super admin existe déjà.'))
            return
        
        email = os.environ.get('SUPERADMIN_EMAIL', 'albanpombombe@gmail.com')
        password = os.environ.get('SUPERADMIN_PASSWORD', 'admin12342')
        first_name = os.environ.get('SUPERADMIN_FIRST_NAME', 'Super')
        last_name = os.environ.get('SUPERADMIN_LAST_NAME', 'Admin')
        
        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_superadmin=True,
            is_admin=False,
            is_employe=False,
            is_verified=True,
            is_staff=True,
            is_superuser=True
        )
        user.set_password(password)
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f'Super admin créé: {email}'))