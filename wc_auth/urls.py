# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="backend-admin-login"),
    path('role/', views.RoleListView.as_view(), name="backend-admin-role-list"),
    path('info/', views.InfoView.as_view(), name="backend-admin-info"),
    path('quiz/', views.QuizView.as_view(), name="backend-admin-quiz"),
]
