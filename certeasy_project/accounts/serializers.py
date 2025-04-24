from rest_framework import serializers
from .models import User, Subscription

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_subscribed')


class SubscriptionSerializer(serializers.ModelSerializer):
    certification_name = serializers.CharField(source='certification.name', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'certification', 'certification_name', 'plan', 'start_date', 'end_date', 'active']
        read_only_fields = ['start_date', 'end_date', 'active']
