"""
URL configuration for certeasy_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    path('login/', login_page, name='login'),
    path('signup/', signup_page, name='signup'),
    path('dashboard/', dashboard_page, name='dashboard'),
    path('mycertifications', mycertifications, name='mycertifications'),
    path('resources', resources, name='resources'),
    path('flashcards', flashcards, name='flashcards'),
    # path('flashcards/create/', create_flashcard, name='create_flashcard'),
    path('quizzes', quizzes, name='quizzes'),
    path('forgot-password/', forgot_password_page, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', reset_confirm_page, name='reset_confirm'),

    # API endpoints
    path('api/auth/', include('dj_rest_auth.urls')),  # login, logout, etc.
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # optional

    path('api/accounts/', include('accounts.urls')),
    path('api/certifications/', include('certifications.urls')),
    path('api/resources/', include('resources.urls')),
    path('api/flashcards/', include('flashcards.urls')),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/discussions/', include('discussions.urls')),

    path('accounts/', include('allauth.urls')),

    path('quizzes/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/start/', start_quiz, name='start_quiz'),
    path('quizzes/attempt/<int:attempt_id>/submit/', submit_quiz, name='submit_quiz'),
    path('certifications/<int:cert_id>/', certification_detail, name='certification_detail'),
    path('quizzes/attempt/<int:attempt_id>/results/', quiz_results, name='quiz_results'),
    path('discussions/', discussions, name='discussions'),
    path('discussions/create/', create_post, name='create_post'),
    path('discussions/post/<int:post_id>/', post_detail, name='post_detail'),
    path('discussions/like/<int:post_id>/', like_post, name='like_post'),
    path('discussions/comment/<int:post_id>/', add_comment, name='add_comment'),
    path('discussions/post/<int:post_id>/delete/', delete_post, name='delete_post'),
    path('discussions/post/<int:post_id>/update/', update_post, name='update_post'),
    path('discussions/comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('discussions/comment/<int:comment_id>/update/', update_comment, name='update_comment'),
    path('create-study-plan/', create_study_plan, name='create_study_plan'),
    path('certification/<int:cert_id>/', certification_view, name='certification_view'),
    path('notification-dropdown/', notification_dropdown_view, name='notification_dropdown'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
