from django.urls import path
from .views import UserProfileView,SubscriptionListView, SubscriptionCreateView

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('subscribe/', SubscriptionCreateView.as_view(), name='subscription-create'),
]
