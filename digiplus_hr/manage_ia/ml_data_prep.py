from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Iterable

from manage_users.models import DemandeConge, Employe, Presence

if TYPE_CHECKING:
    import pandas as pd


TARGET_STATUSES = {"absent", "retard"}


@dataclass(frozen=True)
class FeatureConfig:
    lookback_days: int = 30


def _safe_days_between(start: date | None, end: date) -> int:
    if not start:
        return 0
    return max((end - start).days, 0)


def _approved_leave_ranges(employe: Employe) -> list[tuple[date, date]]:
    return list(
        DemandeConge.objects.filter(employe=employe, statut="approuve")
        .values_list("date_debut", "date_fin")
    )


def _is_on_approved_leave(target_date: date, leave_ranges: Iterable[tuple[date, date]]) -> int:
    for start, end in leave_ranges:
        if start <= target_date <= end:
            return 1
    return 0


def build_training_dataframe(config: FeatureConfig | None = None):
    import pandas as pd

    config = config or FeatureConfig()
    rows: list[dict] = []

    employes = Employe.objects.select_related("user", "poste", "poste__departement").all()
    for employe in employes:
        presences = list(
            Presence.objects.filter(employe=employe)
            .order_by("date")
            .values("date", "statut")
        )
        if len(presences) <= config.lookback_days:
            continue

        leave_ranges = _approved_leave_ranges(employe)
        birth_date = employe.date_naissance
        hire_date = employe.date_embauche
        department_name = (
            employe.poste.departement.nom
            if employe.poste and employe.poste.departement
            else "inconnu"
        )

        for idx in range(config.lookback_days, len(presences)):
            current = presences[idx]
            current_date = current["date"]
            history = presences[idx - config.lookback_days:idx]

            tardies_30d = sum(1 for item in history if item["statut"] == "retard")
            absences_30d = sum(1 for item in history if item["statut"] == "absent")
            leaves_30d = sum(1 for item in history if item["statut"] == "conge")
            attendance_rate_30d = sum(
                1 for item in history if item["statut"] in {"present", "retard"}
            ) / float(config.lookback_days)

            rows.append(
                {
                    "employe_id": employe.id,
                    "department": department_name,
                    "target_date": current_date,
                    "day_of_week": current_date.weekday(),
                    "month": current_date.month,
                    "age_days": _safe_days_between(birth_date, current_date),
                    "tenure_days": _safe_days_between(hire_date, current_date),
                    "tardies_last_30d": tardies_30d,
                    "absences_last_30d": absences_30d,
                    "leaves_last_30d": leaves_30d,
                    "attendance_rate_last_30d": attendance_rate_30d,
                    "on_approved_leave": _is_on_approved_leave(current_date, leave_ranges),
                    "label_absent_or_late": int(current["statut"] in TARGET_STATUSES),
                }
            )

    return pd.DataFrame(rows)


def build_inference_row(employe: Employe, target_date: date, config: FeatureConfig | None = None) -> dict:
    config = config or FeatureConfig()
    history = list(
        Presence.objects.filter(
            employe=employe,
            date__lt=target_date,
        )
        .order_by("-date")
        .values("date", "statut")
        [: config.lookback_days]
    )
    history.reverse()

    if len(history) < config.lookback_days:
        raise ValueError(
            f"Données insuffisantes pour l'employé {employe.id}: "
            f"{len(history)} jours disponibles sur {config.lookback_days} requis."
        )

    leave_ranges = _approved_leave_ranges(employe)

    return {
        "department": (
            employe.poste.departement.nom
            if employe.poste and employe.poste.departement
            else "inconnu"
        ),
        "day_of_week": target_date.weekday(),
        "month": target_date.month,
        "age_days": _safe_days_between(employe.date_naissance, target_date),
        "tenure_days": _safe_days_between(employe.date_embauche, target_date),
        "tardies_last_30d": sum(1 for item in history if item["statut"] == "retard"),
        "absences_last_30d": sum(1 for item in history if item["statut"] == "absent"),
        "leaves_last_30d": sum(1 for item in history if item["statut"] == "conge"),
        "attendance_rate_last_30d": sum(
            1 for item in history if item["statut"] in {"present", "retard"}
        ) / float(config.lookback_days),
        "on_approved_leave": _is_on_approved_leave(target_date, leave_ranges),
    }
