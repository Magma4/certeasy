from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from certifications.models import Certification

# Create your models here.
class User(AbstractUser):
    is_subscribed = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, null=True, blank=True)  # <-- add this
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])

    def __str__(self):
        return f"{self.user.email} - {self.certification.title} ({self.plan})"
