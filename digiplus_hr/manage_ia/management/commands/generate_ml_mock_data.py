from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from manage_users.models import Departement, Employe, Poste, Presence, User


class Command(BaseCommand):
    help = "Génère des employés et présences factices pour l'entraînement ML."

    def handle(self, *args, **options):
        dept_names = ["IT", "RH", "Ventes", "Marketing", "Support"]
        job_titles = ["Développeur", "Manager", "Analyste", "Assistant", "Consultant"]

        departements = [
            Departement.objects.get_or_create(nom=nom)[0]
            for nom in dept_names
        ]

        postes = []
        for dept in departements:
            poste, _ = Poste.objects.get_or_create(
                titre=random.choice(job_titles),
                departement=dept,
                defaults={"salaire_de_base": 50000 + random.randint(-10000, 20000)},
            )
            postes.append(poste)

        employes = []
        for idx in range(1, 21):
            email = f"emp{idx}_ml@example.com"
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": f"Prenom{idx}",
                    "last_name": f"Nom{idx}",
                    "password": make_password("pass123"),
                    "is_employe": True,
                    "is_verified": True,
                },
            )
            employe, _ = Employe.objects.get_or_create(
                user=user,
                defaults={
                    "matricule": f"ML_EMP{idx:03d}",
                    "date_embauche": date.today() - timedelta(days=random.randint(365, 365 * 5)),
                    "date_naissance": date.today() - timedelta(days=random.randint(22 * 365, 55 * 365)),
                    "statut": "actif",
                    "poste": random.choice(postes),
                },
            )
            employes.append(employe)

        profile_map = {
            employe.id: random.choices([0, 1, 2, 3], weights=[30, 50, 15, 5])[0]
            for employe in employes
        }

        current_date = date.today() - timedelta(days=180)
        created_count = 0
        while current_date <= date.today():
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            for employe in employes:
                if Presence.objects.filter(employe=employe, date=current_date).exists():
                    continue

                profile = profile_map[employe.id]
                rand_val = random.random()
                statut = "present"
                hr_arrivee = datetime.strptime("08:00", "%H:%M").time()
                hr_depart = datetime.strptime("17:00", "%H:%M").time()

                if profile == 0:
                    if rand_val < 0.01:
                        statut = "absent"
                    elif rand_val < 0.05:
                        statut = "retard"
                        hr_arrivee = datetime.strptime("08:15", "%H:%M").time()
                elif profile == 1:
                    if rand_val < 0.03:
                        statut = "absent"
                    elif rand_val < 0.10:
                        statut = "retard"
                        hr_arrivee = datetime.strptime(
                            f"0{random.randint(8, 9)}:{random.randint(10, 59)}", "%H:%M"
                        ).time()
                elif profile == 2:
                    if rand_val < 0.05:
                        statut = "absent"
                    elif rand_val < 0.35:
                        statut = "retard"
                        hr_arrivee = datetime.strptime(
                            f"0{random.randint(8, 9)}:{random.randint(10, 59)}", "%H:%M"
                        ).time()
                else:
                    if rand_val < 0.15:
                        statut = "absent"
                    elif rand_val < 0.30:
                        statut = "retard"
                        hr_arrivee = datetime.strptime(
                            f"0{random.randint(8, 9)}:{random.randint(10, 59)}", "%H:%M"
                        ).time()

                if statut == "absent":
                    hr_arrivee = None
                    hr_depart = None
                    work_minutes = 0
                elif statut == "retard":
                    delta = datetime.combine(current_date, hr_depart) - datetime.combine(current_date, hr_arrivee)
                    work_minutes = max(0, delta.seconds // 60 - 60)
                else:
                    hr_arrivee = datetime.strptime(f"07:{random.randint(45, 59)}", "%H:%M").time()
                    work_minutes = 480

                Presence.objects.create(
                    employe=employe,
                    date=current_date,
                    statut=statut,
                    heure_arrivee=hr_arrivee,
                    heure_depart=hr_depart,
                    duree_travail_minutes=work_minutes,
                    nb_pauses=1,
                    duree_pauses_minutes=60 if hr_arrivee else 0,
                )
                created_count += 1

            current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Données ML prêtes: {len(employes)} employés et {created_count} présences générées."
            )
        )
