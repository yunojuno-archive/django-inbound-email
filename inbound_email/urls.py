try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path

from . import views

urlpatterns = [
    re_path(r'^inbound/$', views.receive_inbound_email, name='receive_inbound_email')
]
