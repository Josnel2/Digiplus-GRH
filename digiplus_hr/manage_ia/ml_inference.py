from __future__ import annotations

from datetime import timedelta

import joblib
from django.utils import timezone

from manage_users.models import Employe

from .ml_data_prep import build_inference_row
from .ml_train import MODEL_PATH


class AbsenceInferenceService:
    def __init__(self) -> None:
        self._artifact = None

    def _load_artifact(self) -> dict:
        if self._artifact is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    "Modèle introuvable. Lancez d'abord `python manage.py train_ml_models`."
                )
            self._artifact = joblib.load(MODEL_PATH)
        return self._artifact

    def predict_for_employee(self, employe: Employe, target_date=None) -> dict:
        artifact = self._load_artifact()
        target_date = target_date or (timezone.localdate() + timedelta(days=1))
        features = build_inference_row(employe, target_date=target_date)
        import pandas as pd

        frame = pd.DataFrame([features], columns=artifact["feature_columns"])
        probability = float(artifact["model"].predict_proba(frame)[0][1])
        label = "high" if probability >= 0.7 else "medium" if probability >= 0.4 else "low"

        return {
            "employe_id": employe.id,
            "target_date": target_date.isoformat(),
            "risk_probability": probability,
            "risk_percent": round(probability * 100, 2),
            "risk_level": label,
            "features": features,
        }

    def predict_for_department(self, departement_id: int) -> dict:
        employes = Employe.objects.select_related("user", "poste", "poste__departement").filter(
            poste__departement_id=departement_id
        )
        predictions = []
        skipped = []

        for employe in employes:
            try:
                predictions.append(self.predict_for_employee(employe))
            except ValueError as exc:
                skipped.append({"employe_id": employe.id, "reason": str(exc)})

        average_risk = (
            round(sum(item["risk_probability"] for item in predictions) / len(predictions) * 100, 2)
            if predictions
            else 0.0
        )

        return {
            "departement_id": departement_id,
            "predictions_count": len(predictions),
            "average_risk_percent": average_risk,
            "high_risk_count": sum(1 for item in predictions if item["risk_level"] == "high"),
            "predictions": predictions,
            "skipped": skipped,
        }


absence_inference_service = AbsenceInferenceService()
