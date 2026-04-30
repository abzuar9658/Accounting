from django.urls import path

from . import views

app_name = "earnings"

urlpatterns = [
    path("", views.earning_list, name="list"),
    path("create/", views.earning_create, name="create"),
    path("<int:pk>/", views.earning_detail, name="detail"),
    path("<int:pk>/edit/", views.earning_edit, name="edit"),
    path("<int:pk>/update/", views.earning_update, name="update"),
    path("<int:pk>/delete/", views.earning_delete, name="delete"),
]
