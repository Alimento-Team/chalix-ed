"""
URL configuration for facial expression recording API.
"""
from django.urls import path
from . import views

app_name = 'facial_expression'

urlpatterns = [
    path('upload/', views.upload_facial_expression_video, name='upload'),
    path('logs/', views.get_facial_expression_logs, name='logs'),
    path('logs/<int:log_id>/', views.get_facial_expression_log_detail, name='log_detail'),
    path('check-recording/', views.check_valid_recording, name='check_recording'),
]
