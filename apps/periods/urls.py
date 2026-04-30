from django.urls import path

from . import views

app_name = "periods"

urlpatterns = [
    path("", views.month_list, name="month_list"),
    path("<str:code>/", views.month_detail, name="month_detail"),
    path("<str:code>/split/", views.split_edit, name="split_edit"),
    path("<str:code>/transition/<str:target>/", views.month_transition, name="month_transition"),
    path("<str:code>/delete/", views.month_delete, name="month_delete"),
]
