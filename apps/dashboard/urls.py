from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("income/", views.entity_income, name="entity_income"),
    path("<str:code>/", views.report, name="report"),
]
