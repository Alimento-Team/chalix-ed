"""
URL configuration for Teacher Dashboard.
"""

from django.urls import path
from . import views

app_name = 'teacher_dashboard'

urlpatterns = [
    path('', views.teacher_dashboard_view, name='teacher_dashboard'),
]
