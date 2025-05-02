# certeasy_project/accounts/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import UserProfileView, SubscriptionListView, SubscriptionCreateView, profile_view, settings_view

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('subscribe/', SubscriptionCreateView.as_view(), name='subscription-create'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
]
