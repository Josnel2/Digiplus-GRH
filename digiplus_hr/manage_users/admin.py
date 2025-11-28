from django.contrib import admin
from .models import User, OTP, Poste, Employe, DemandeConge, Notification,DemandeCongeAudit

# Register your models here.
admin.site.register(User)
admin.site.register(OTP)
admin.site.register(Poste)
admin.site.register(Employe)
admin.site.register(DemandeConge)
admin.site.register(Notification)
admin.site.register(DemandeCongeAudit)
