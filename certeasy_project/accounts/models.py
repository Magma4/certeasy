from django.db import models
from django.utils import timezone
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

class UserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logins')
    login_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'login_date')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gamified_profile')
    study_streak = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)

    def update_streak(self):
        today = timezone.now().date()
        if self.last_study_date == today:
            return # already studied today
        elif self.last_study_date == today - timezone.timedelta(days=1):
            self.study_streak += 1
        else:
            self.study_streak = 1
        self.last_study_date = today
        self.save()
