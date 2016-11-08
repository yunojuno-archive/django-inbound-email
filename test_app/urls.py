from django.conf.urls import url, include

urlpatterns = [
    url(r'^emails/', include('inbound_email.urls', namespace='inbound'))
]
