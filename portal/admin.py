from django.contrib import admin
from .models import Word, Type, Offer, Locality, Demand, RestrictedWord, UploadFile, AdminText

# Register your models here.

admin.site.register(Word)
admin.site.register(Type)
admin.site.register(Offer)
admin.site.register(Locality)
admin.site.register(Demand)
admin.site.register(RestrictedWord)
admin.site.register(UploadFile)
admin.site.register(AdminText)
