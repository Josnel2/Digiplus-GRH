from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone

from manage_users.models import User, Employe, CodeQR, Badgeage, Presence


class TestBadgeagePresence(APITestCase):
    def test_badgeage_updates_presence(self):
        user = User.objects.create_user(
            email="emp@example.com",
            password="pass1234",
            first_name="Emp",
            last_name="Test",
            is_employe=True,
            is_verified=True,
        )
        employe = Employe.objects.create(
            user=user,
            matricule="EMP100",
            date_embauche=timezone.now().date(),
        )
        code_qr = CodeQR.objects.create(
            employe=employe,
            code_unique=CodeQR.generate_unique_code(),
            actif=True,
        )

        self.client.force_authenticate(user=user)
        scanner_url = reverse("badgeage-scanner")

        def scan(badge_type):
            payload = {"code_qr": code_qr.code_unique, "type": badge_type}
            return self.client.post(scanner_url, payload, format="json")

        resp = scan("arrivee")
        self.assertEqual(resp.status_code, 201)
        presence = Presence.objects.get(employe=employe, date=timezone.now().date())
        self.assertIsNotNone(presence.heure_arrivee)
        self.assertEqual(presence.statut, "present")

        resp = scan("pause_debut")
        self.assertEqual(resp.status_code, 201)
        presence.refresh_from_db()
        self.assertEqual(presence.nb_pauses, 1)

        resp = scan("pause_fin")
        self.assertEqual(resp.status_code, 201)
        presence.refresh_from_db()
        self.assertGreaterEqual(presence.nb_pauses, 1)
        self.assertGreaterEqual(presence.duree_pauses_minutes, 0)

        resp = scan("depart")
        self.assertEqual(resp.status_code, 201)
        presence.refresh_from_db()
        self.assertIsNotNone(presence.heure_depart)
        self.assertGreaterEqual(presence.duree_travail_minutes, 0)

        badgeages_today = Badgeage.objects.filter(employe=employe, date=timezone.now().date())
        self.assertEqual(badgeages_today.count(), 4)
