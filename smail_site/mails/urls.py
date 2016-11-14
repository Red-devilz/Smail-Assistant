from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^(?P<category_id>[0-9]+)/$', views.classify, name='classify'),
    url(r'^login$', views.login, name="login"),
    url(r'^logout$', views.logout, name="logout"),
    url(r'^oauth2callback$', views.oauth2callback, name="oauth2callback"),
    url(r'^msg/(?P<msg_id>[a-z0-9]+)/$', views.display, name='display'),
    url(r'^addcal$', views.addCal, name="addcal"),
]
