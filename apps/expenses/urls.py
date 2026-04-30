from django.urls import path

from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_list, name="list"),
    path("new/", views.expense_create, name="create"),
    path("<int:pk>/edit/", views.expense_edit, name="edit"),
    path("<int:pk>/update/", views.expense_update, name="update"),
    path("<int:pk>/delete/", views.expense_delete, name="delete"),
]
