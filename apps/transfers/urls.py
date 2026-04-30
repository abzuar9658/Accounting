from django.urls import path

from . import views

app_name = "transfers"

urlpatterns = [
    path("", views.transfer_list, name="list"),
    path("<int:pk>/", views.transfer_detail, name="detail"),
    path("<int:pk>/pay/", views.payment_create, name="payment_create"),
    path("settle/<str:code>/", views.settle_month_view, name="settle_month"),
]
