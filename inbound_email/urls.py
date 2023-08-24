from django.urls import path

from . import views

urlpatterns = [
    path('inbound/', views.receive_inbound_email, name='receive_inbound_email')
]
