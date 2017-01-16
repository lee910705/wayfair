from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from premierleagueapp import views as pla_views
import django.contrib.auth.views

urlpatterns = [
    url(r'^$', pla_views.home, name='home'),
    url(r'^register/$', pla_views.register, name='register'),
    url(r'^login$', django.contrib.auth.views.login,
        {'template_name':'login.html'}, name='login'),
    url(r'^teams$', pla_views.teams, name='teams'),
    url(r'^logout$', django.contrib.auth.views.logout_then_login, name='logout'),
    url(r'^confirm-registration/(?P<username>[a-zA-Z0-9_@\+\-]+)/(?P<token>[a-z0-9\-]+)$',
        pla_views.confirm_registration, name='confirm'),
    url(r'^teampage/(?P<teamid>\d+)$', pla_views.view_teampage, name='view_teampage'),
    url(r'^teamchat/(?P<teamid>\d+)$', pla_views.view_teamchat, name='view_teamchat'),
    url(r'^getpicture/(?P<ateamid>\d+)$', pla_views.get_picture, name='get_picture'),
    url(r'^getteamcity/(?P<ateamid>\d+)$', pla_views.get_teamcity, name='get_teamcity'),
    url(r'^getweather/(?P<city_name>\d+)$', pla_views.get_weather, name='get_weather'),
    url(r'^addchat/', pla_views.add_chat, name='add_chat'),
    url(r'^messages/(?P<teamid>\d+)$', pla_views.view_messages, name='view_messages'),
    url(r'^follow/(?P<teamid>\d+)$', pla_views.follow, name='followteam'),
    url(r'^unfollow/(?P<teamid>\d+)$', pla_views.unfollow, name='unfollowteam'),
    url(r'^favoritematches/$', pla_views.favorite_matches, name='favorite_matches'),
] 


handler400 = 'pla_views.handler400'
handler403 = 'pla_views.handler403'
handler404 = 'pla_views.handler404'
handler500 = 'pla_views.handler500'

