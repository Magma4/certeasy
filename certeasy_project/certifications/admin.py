from django.contrib import admin
from .models import Certification

# Register your models here.


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'category')
    list_filter = ('title',)
