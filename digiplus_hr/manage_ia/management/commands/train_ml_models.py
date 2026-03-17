from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from manage_ia.ml_train import train_absence_model


class Command(BaseCommand):
    help = "Entraîne le modèle ML de prédiction absence/retard."

    def handle(self, *args, **options):
        try:
            metrics = train_absence_model()
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Modèle entraîné avec succès."))
        self.stdout.write(f"Artifact: {metrics['model_path']}")
        self.stdout.write(f"Lignes d'entraînement: {metrics['training_rows']}")
        self.stdout.write(f"ROC AUC: {metrics['roc_auc']:.4f}")
