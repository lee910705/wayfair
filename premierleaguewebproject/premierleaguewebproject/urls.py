from django.conf.urls import include, url
from django.contrib import admin
from premierleagueapp import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^premierleagueapp/', include('premierleagueapp.urls')),
    url(r'^$', views.home),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                 {'document_root': settings.MEDIA_ROOT}),
]

