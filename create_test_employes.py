#!/usr/bin/env python
"""
Script pour créer des employés de test
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, 'c:\\Users\\GENIUS ELECTRONICS\\Digiplus-GRH\\digiplus_hr')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digiplus_hr.settings')
django.setup()

from manage_users.models import User, Employe, Poste, Departement
from django.contrib.auth.hashers import make_password

print("="*70)
print("CRÉATION D'EMPLOYÉS DE TEST")
print("="*70)

# Créer des utilisateurs supplémentaires
users_data = [
    {"email": "chef.it@example.com", "first_name": "Jean", "last_name": "Dupont", "password": "pass123"},
    {"email": "chef.hr@example.com", "first_name": "Marie", "last_name": "Martin", "password": "pass123"},
    {"email": "chef.ventes@example.com", "first_name": "Pierre", "last_name": "Bernard", "password": "pass123"},
]

created_users = []
for user_data in users_data:
    user, created = User.objects.get_or_create(
        email=user_data['email'],
        defaults={
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'password': make_password(user_data['password']),
            'is_admin': True,
            'is_employe': True,
            'is_verified': True
        }
    )
    created_users.append(user)
    status = "✅ Créé" if created else "⚠️  Existe déjà"
    print(f"{status}: {user.email} (ID: {user.id})")

# Créer des employés correspondants
print("\n" + "="*70)
print("CRÉATION D'EMPLOYÉS")
print("="*70)

for i, user in enumerate(created_users, start=2):
    employe, created = Employe.objects.get_or_create(
        user=user,
        defaults={
            'matricule': f'EMP{100+i:03d}',
            'date_embauche': '2020-01-01',
            'statut': 'actif'
        }
    )
    status = "✅ Créé" if created else "⚠️  Existe déjà"
    print(f"{status}: {user.email} (Employe ID: {employe.id}, Matricule: {employe.matricule})")

print("\n" + "="*70)
print("LISTE FINALE DES EMPLOYÉS")
print("="*70)

employes = Employe.objects.all().select_related('user')
for emp in employes:
    print(f"Employe ID: {emp.id} | User ID: {emp.user.id} | {emp.user.email} | {emp.user.first_name} {emp.user.last_name}")

print("\n✅ Prêt! Utilisez les IDs d'employé ci-dessus pour le champ 'chef_departement'")
