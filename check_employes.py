#!/usr/bin/env python
"""
Script pour vérifier les utilisateurs et employés existants
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digiplus_hr.settings')
django.setup()

from manage_users.models import User, Employe

print("="*70)
print("UTILISATEURS DISPONIBLES")
print("="*70)

users = User.objects.all()
print(f"\nTotal: {users.count()} utilisateurs\n")

for user in users:
    print(f"ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  First Name: {user.first_name}")
    print(f"  Last Name: {user.last_name}")
    print(f"  Role: {user.role}")
    print()

print("="*70)
print("EMPLOYÉS DISPONIBLES")
print("="*70)

employes = Employe.objects.all()
print(f"\nTotal: {employes.count()} employés\n")

for emp in employes:
    user = emp.user
    print(f"ID: {emp.id}")
    print(f"  User ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Name: {user.first_name} {user.last_name}")
    print(f"  Matricule: {emp.matricule}")
    if emp.poste:
        print(f"  Poste: {emp.poste.nom}")
    print()

print("="*70)
print("POUR TESTER, UTILISEZ UN ID EMPLOYÉ VALIDE")
print("="*70)
