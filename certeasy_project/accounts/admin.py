from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'certification', 'plan', 'active', 'start_date', 'end_date')
    list_filter = ('plan', 'active')
