from django.shortcuts import render
from rest_framework import generics, permissions
from .models import User,Subscription
from .serializers import UserSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class SubscriptionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

class SubscriptionCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def user_has_active_subscription(user, certification_id):
    """
    Check if a user has an active subscription to a specific certification.
    """
    return Subscription.objects.filter(
        user=user,
        certification_id=certification_id,
        active=True
    ).exists()
