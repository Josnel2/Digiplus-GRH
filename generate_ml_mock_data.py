import os
import sys
import django
import random
from datetime import timedelta, date, datetime

# Setup Django
sys.path.insert(0, 'c:\\Users\\GENIUS ELECTRONICS\\Digiplus-GRH\\digiplus_hr')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digiplus_hr.settings')
django.setup()

from manage_users.models import User, Employe, Poste, Departement, Presence
from django.contrib.auth.hashers import make_password

print("="*70)
print("CRÉATION DE DONNÉES FICTIVES POUR LE MACHINE LEARNING")
print("="*70)

# 1. Créer des départements s'ils n'existent pas
dept_noms = ['IT', 'RH', 'Ventes', 'Marketing', 'Support']
departements = []
for nom in dept_noms:
    dept, _ = Departement.objects.get_or_create(nom=nom)
    departements.append(dept)
print(f"✅ {len(departements)} Départements vérifiés/créés.")

# 2. Créer des postes
poste_titres = ['Développeur', 'Manager', 'Analyste', 'Assistant', 'Consultant']
postes = []
for i, dept in enumerate(departements):
    titre = random.choice(poste_titres)
    poste, _ = Poste.objects.get_or_create(
        titre=titre,
        departement=dept,
        defaults={'salaire_de_base': 50000 + random.randint(-10000, 20000)}
    )
    postes.append(poste)
print(f"✅ {len(postes)} Postes vérifiés/créés.")

# 3. Créer des employés fictifs (environ 20)
print("\nCréation des employés...")
employes = []
for i in range(1, 21):
    email = f"emp{i}_ml@example.com"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': f"Prenom{i}",
            'last_name': f"Nom{i}",
            'password': make_password('pass123'),
            'is_employe': True,
            'is_verified': True
        }
    )
    
    # Ancienneté aléatoire entre 1 et 5 ans
    years_ago = random.randint(1, 5)
    
    employe, created = Employe.objects.get_or_create(
        user=user,
        defaults={
            'matricule': f'ML_EMP{i:03d}',
            'date_embauche': date.today() - timedelta(days=years_ago * 365),
            'statut': 'actif',
            'poste': random.choice(postes)
        }
    )
    employes.append(employe)

print(f"✅ {len(employes)} Employés fictifs générés.")

# 4. Générer l'historique de présences (6 mois)
print("\nGénération de l'historique de présences (6 derniers mois)...")
start_date = date.today() - timedelta(days=180)
end_date = date.today()

total_presences = 0
current_date = start_date

# Profils d'employés (impacte leurs présences)
# Certains employés ont plus tendance à être en retard ou absents
emp_profiles = {}
for emp in employes:
    # 0 = Très ponctuel, 1 = Normal, 2 = Souvent en retard, 3 = Souvent absent
    emp_profiles[emp.id] = random.choices([0, 1, 2, 3], weights=[30, 50, 15, 5])[0]

while current_date <= end_date:
    # Gérer les week-ends (supposant que la boîte est fermée le samedi=5 et dimanche=6)
    if current_date.weekday() >= 5:
        current_date += timedelta(days=1)
        continue

    for emp in employes:
        # Si présence existe déjà, on la skip pour ne pas planter sur la contrainte d'unicité
        if Presence.objects.filter(employe=emp, date=current_date).exists():
            continue
            
        profile = emp_profiles[emp.id]
        
        # Logique de probabilité d'état
        rand_val = random.random()
        statut = 'present' # default
        
        # Heures par défaut
        hr_arrivee = datetime.strptime("08:00", "%H:%M").time()
        hr_depart = datetime.strptime("17:00", "%H:%M").time()
        
        if profile == 0: # Très ponctuel
            if rand_val < 0.01: statut = 'absent'
            elif rand_val < 0.05: statut = 'retard'; hr_arrivee = datetime.strptime("08:15", "%H:%M").time()
            
        elif profile == 1: # Normal
            if rand_val < 0.03: statut = 'absent'
            elif rand_val < 0.10: statut = 'retard'; hr_arrivee = datetime.strptime(f"0{random.randint(8,9)}:{random.randint(10,59)}", "%H:%M").time()
                
        elif profile == 2: # Souvent en retard
            if rand_val < 0.05: statut = 'absent'
            elif rand_val < 0.35: statut = 'retard'; hr_arrivee = datetime.strptime(f"0{random.randint(8,9)}:{random.randint(10,59)}", "%H:%M").time()
                
        elif profile == 3: # Souvent absent
            if rand_val < 0.15: statut = 'absent'
            elif rand_val < 0.30: statut = 'retard'; hr_arrivee = datetime.strptime(f"0{random.randint(8,9)}:{random.randint(10,59)}", "%H:%M").time()


        if statut == 'absent':
            hr_arrivee = None
            hr_depart = None
            duree_travail = 0
            
        elif statut == 'retard':
            # Calcul approximatif de durée
            td = datetime.combine(current_date, hr_depart) - datetime.combine(current_date, hr_arrivee)
            minutes = td.seconds // 60
            duree_travail = minutes - 60 # Retire 1h de pause
            
        else: # present
            # Variation d'arrivée (de 07:45 à 08:00)
            mins = random.randint(45, 59)
            hr_arrivee = datetime.strptime(f"07:{mins}", "%H:%M").time()
            duree_travail = 480 # 8 heures * 60

        try:
            Presence.objects.create(
                employe=emp,
                date=current_date,
                statut=statut,
                heure_arrivee=hr_arrivee,
                heure_depart=hr_depart,
                duree_travail_minutes=duree_travail,
                nb_pauses=1,
                duree_pauses_minutes=60 if hr_arrivee else 0
            )
            total_presences += 1
        except Exception as e:
            pass # Ignore unique constraint duplicates


    current_date += timedelta(days=1)

print(f"✅ {total_presences} enregistrements de Présence créés.")
print("="*70)
print("TERMINE. La base de données contient maintenant suffisamment de données pour l'entraînement ML.")
