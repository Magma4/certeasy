from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserLogin
from django.utils import timezone
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(user_logged_in)
def record_daily_login(sender, user, request, **kwargs):
    today = timezone.now().date()
    UserLogin.objects.get_or_create(user=user, login_date=today)

@receiver(post_save, sender=User)
def create_user_login(sender, instance, created, **kwargs):
    if created:
        UserLogin.objects.create(user=instance)
