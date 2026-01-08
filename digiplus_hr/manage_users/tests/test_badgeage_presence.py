import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from manage_users.models import User, Employe, CodeQR, Badgeage, Presence


@pytest.mark.django_db
def test_badgeage_updates_presence():
    client = APIClient()

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

    client.force_authenticate(user=user)
    scanner_url = reverse("badgeage-scanner")

    def scan(badge_type):
        payload = {"code_qr": code_qr.code_unique, "type": badge_type}
        return client.post(scanner_url, payload, format="json")

    # Arrivee
    resp = scan("arrivee")
    assert resp.status_code == 201
    presence = Presence.objects.get(employe=employe, date=timezone.now().date())
    assert presence.heure_arrivee is not None
    assert presence.statut == "present"

    # Debut de pause
    resp = scan("pause_debut")
    assert resp.status_code == 201
    presence.refresh_from_db()
    assert presence.nb_pauses == 1

    # Fin de pause
    resp = scan("pause_fin")
    assert resp.status_code == 201
    presence.refresh_from_db()
    assert presence.nb_pauses >= 1
    assert presence.duree_pauses_minutes >= 0

    # Depart
    resp = scan("depart")
    assert resp.status_code == 201
    presence.refresh_from_db()
    assert presence.heure_depart is not None
    assert presence.duree_travail_minutes >= 0

    # Badgeages du jour
    badgeages_today = Badgeage.objects.filter(employe=employe, date=timezone.now().date())
    assert badgeages_today.count() == 4
