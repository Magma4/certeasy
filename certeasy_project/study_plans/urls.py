from django.urls import path
from . import views

app_name = 'study_plans'

urlpatterns = [
    path('', views.study_plan_list, name='list'),
    path('create/', views.create_study_plan, name='create'),
    path('<int:plan_id>/update/', views.update_study_plan, name='update'),
    path('<int:plan_id>/delete/', views.delete_study_plan, name='delete'),
    path('get-activity-content/', views.get_activity_content, name='get_activity_content'),
]
