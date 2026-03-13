from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os

class CompanyDocument(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre du Document")
    file = models.FileField(upload_to="documents_ia/", verbose_name="Fichier PDF")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_indexed = models.BooleanField(default=False, verbose_name="Indexé par l'IA")

    def __str__(self):
        return self.title

# On va importer rag_utils à l'intérieur des signaux pour éviter les imports circulaires
@receiver(post_save, sender=CompanyDocument)
def index_document_on_save(sender, instance, created, **kwargs):
    if created and not instance.is_indexed:
        # Dans un environnement de prod, on ferait ça avec Celery pour ne pas bloquer l'interface
        # Ici on le fait de manière synchrone pour la démo
        try:
            from .rag_utils import add_document_to_index
            add_document_to_index(instance)
            CompanyDocument.objects.filter(id=instance.id).update(is_indexed=True)
        except Exception as e:
            print(f"Erreur lors de l'indexation du document {instance.title}: {str(e)}")

@receiver(post_delete, sender=CompanyDocument)
def delete_document_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)
    # L'idéal serait aussi de retirer le document de l'index FAISS, mais FAISS
    # ne permet pas facilement la suppression d'un vecteur spécifique.
    # On devrait reconstruire l'index complètement s'il y a trop de suppressions.
