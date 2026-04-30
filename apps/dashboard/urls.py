from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("<str:code>/", views.report, name="report"),
]
