from django.shortcuts import render
from rest_framework import generics, permissions
from .models import User, Subscription
from .serializers import UserSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Auto-expire outdated subscriptions on fetch
def expire_old_subscriptions():
    Subscription.objects.filter(end_date__lt=timezone.now(), active=True).update(active=False)

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class SubscriptionDetailView(generics.RetrieveAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

class SubscriptionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        expire_old_subscriptions()
        queryset = Subscription.objects.filter(user=self.request.user)
        plan = self.request.query_params.get('plan')
        if plan:
            queryset = queryset.filter(plan__iexact=plan)
        return queryset

class SubscriptionCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def user_has_active_subscription(user, certification_id):
    """
    Check if a user has an active subscription to a specific certification
    """
    return Subscription.objects.filter(
        user=user,
        certification_id=certification_id,
        active=True
    ).exists()

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })

@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html', {
        'user': request.user
    })
