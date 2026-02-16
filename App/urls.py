from django.contrib import admin
from django.urls import path
from . import views

app_name = "Bank"

urlpatterns = [
    path('Salary/<uuid:uuid>', views.get_salary, name='Salary'),
]

