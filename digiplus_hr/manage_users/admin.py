from django.contrib import admin
from .models import User, OTP, Poste, Employe

# Register your models here.
admin.site.register(User)
admin.site.register(OTP)
admin.site.register(Poste)
admin.site.register(Employe)