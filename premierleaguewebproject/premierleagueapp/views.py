from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template import Context, Template
import django.utils.html as html
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.core import serializers
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.core.urlresolvers import reverse

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

from geoip import geolite2

from premierleagueapp.models import *
from premierleagueapp.forms import *

from mimetypes import guess_type

from datetime import tzinfo, timedelta, datetime

ZERO = timedelta(0)

class UTC(tzinfo):
  def utcoffset(self, dt):
    return ZERO
  def tzname(self, dt):
    return "UTC"
  def dst(self, dt):
    return ZERO

utc = UTC()

import time
import os
import httplib
import json
import sys

@login_required
def get_fixtures(request, apiteamid):
    try:
        connection = httplib.HTTPConnection('api.football-data.org')
        headers = { 'X-Auth-Token': 'f7462489e0f24a598e4232e269b18946', 'X-Response-Control': 'minified' }
        connection.request('GET', '/v1/teams/'+str(apiteamid)+'/fixtures/', None, headers )
        response = json.loads(connection.getresponse().read().decode())
        fixtures = json.loads(json.dumps(response['fixtures']))

        path = os.path.dirname(os.path.realpath(__file__))
        path += '/static/city.list.update2.json'
        data = {}

        with open(path) as f:
            for line in f:
                data = json.loads(line)
                
        updatedFixtures = []
        for info in fixtures:
            try: 
                hometeam = Team.objects.get(apiteamid=info['homeTeamId'])
                awayteam = Team.objects.get(apiteamid=info['awayTeamId'])
                info['hometeamstadiumloc'] = hometeam.stadiumloc
                city_data = data[hometeam.stadiumloc]
                city_id = str(city_data['id'])
                retval = get_weather(city_id, info['date'])
                fixture_time = info['date']
                fixture_date = datetime.strptime(fixture_time, '%Y-%m-%dT%H:%M:%SZ')
                if (retval != None):
                    currtemp = retval['main']['temp']
                    calvintemp = 273.15
                    celsiustemp = currtemp - calvintemp
                    retval['main']['temp'] = celsiustemp
                    info['weather_info'] = retval
                info['date'] = fixture_date
                info['htid'] = hometeam.id
                info['atid'] = awayteam.id
                updatedFixtures.append(info)
            except Team.DoesNotExist:
                continue
        return updatedFixtures
    except:
        raise Http404("Connection does not exist")

@login_required
def home(request):  
    context = {}
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    g = geolite2.lookup(ip)
    context['ip'] = ip
    context['gloclat'] = g.location[0]
    context['gloclon'] = g.location[1]
    try:
        connection = httplib.HTTPConnection('api.football-data.org')
        headers = { 'X-Auth-Token': 'f7462489e0f24a598e4232e269b18946', 'X-Response-Control': 'minified' }
        connection.request('GET', '/v1/soccerseasons/398/fixtures/', None, headers )
        response = json.loads(connection.getresponse().read().decode())
        fixtures = json.loads(json.dumps(response['fixtures']))
        path = os.path.dirname(os.path.realpath(__file__))
        path += '/static/city.list.update2.json'
        data = {}

        with open(path) as f:
            for line in f:
                data = json.loads(line)
                
        updatedFixtures = []
        for info in fixtures:
            try: 
                hometeam = Team.objects.get(apiteamid=info['homeTeamId'])
                awayteam = Team.objects.get(apiteamid=info['awayTeamId'])
                info['hometeamstadiumloc'] = hometeam.stadiumloc
                city_data = data[hometeam.stadiumloc]
                city_id = str(city_data['id'])
                today = datetime.now()
                fixture_time = info['date']
                end_date = today + timedelta(days=7, hours=0)
                fixture_date = datetime.strptime(fixture_time, '%Y-%m-%dT%H:%M:%SZ')
                if today < fixture_date and fixture_date < end_date:
                    retval = get_weather(city_id, fixture_time)
                    if (retval != None):
                        currtemp = retval['main']['temp']
                        calvintemp = 273.15
                        celsiustemp = currtemp - calvintemp
                        retval['main']['temp'] = celsiustemp
                        info['weather_info'] = retval
                    info['lat'] = str(city_data['coord']['lat'])
                    info['lon'] = str(city_data['coord']['lon'])
                    info['date'] = fixture_date
                    info['htid'] = hometeam.id
                    info['atid'] = awayteam.id
                    updatedFixtures.append(info)
            except Team.DoesNotExist:
                continue
            
        context['fixtures'] = updatedFixtures

        markers = []

        for fixture in updatedFixtures:
            exist = False
            for marker in markers:
                if marker['lat'] == fixture['lat'] and marker['lon'] == fixture['lon']:
                    exist = True
                    new_msg = " & " + str(fixture['homeTeamName'])+" vs. "+str(fixture['awayTeamName'])
                    marker['msg'] += new_msg
                    break
            if exist == False:
                marker = {}
                marker['lat'] = fixture['lat']
                marker['lon'] = fixture['lon']
                marker['msg'] = str(fixture['homeTeamName'])+" vs. "+str(fixture['awayTeamName'])
                markers.append(marker)

        context['markers'] = markers

        return render_to_response('home.html', context, context_instance=RequestContext(request))
    except:
         raise Http404("Connection does not exist")


@login_required
def teams(request):
    context = {}
    return render_to_response('teams.html', context, context_instance=RequestContext(request))

def get_weather(location_id, fixture_time):
    today = datetime.now()
    end_date = today + timedelta(days=4, hours=18)
    fixture_date = datetime.strptime(fixture_time, '%Y-%m-%dT%H:%M:%SZ')

    if today <= fixture_date and fixture_date <= end_date:
        conn = httplib.HTTPConnection('api.openweathermap.org')
        hdrs = {'X-Auth-Token' : 'c7d210629123891fefbab2b38afac30d'}
        conn.request('GET', '/data/2.5/forecast/city?id='+location_id+'&APPID=c7d210629123891fefbab2b38afac30d', None, hdrs)
        try: 
            response = json.loads(conn.getresponse().read().decode())
            w_list = json.loads(json.dumps(response['list']))
            for w_info in w_list:
                w_datestr = w_info['dt_txt']
                w_datetime = datetime.strptime(w_datestr, '%Y-%m-%d %H:00:00')
                if fixture_date - w_datetime > timedelta(hours=0) and fixture_date - w_datetime < timedelta(hours=3):
                    return w_info
        except ValueError:
            return None
    else:
        return None


@transaction.atomic
def register(request):
    context = {}

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = RegistrationForm()
        return render(request, 'register.html', context)

    # Creates a bound form from the request POST parameters and makes the 
    # form available in the request context dictionary.
    form = RegistrationForm(request.POST, request.FILES)
    # form.save()
    context['form'] = form

    # Validates the form.
    if not form.is_valid():
        return render(request, 'register.html', context)

    # If we get here the form data was valid.  Register and login the user.
    new_user = User.objects.create_user(username=form.cleaned_data['username'], 
                                        password=form.cleaned_data['password1'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'],
                                        email=form.cleaned_data['email'])
    new_user.save()

    new_followings = Followings(user=new_user)
    new_followings.save()

    # Logs in the new user and redirects to his/her todo list
    new_user = authenticate(username=form.cleaned_data['username'], \
                            password=form.cleaned_data['password1'])

    # Generate a one-time use token and an email message body
    token = default_token_generator.make_token(new_user)

    email_body = """
Welcome to Premier League Share Your Soccer Moments.  Please click the link below to
verify your email address and complete the registration of your account:

  http://%s%s
""" % (request.get_host(), 
       reverse('confirm', args=(new_user.username, token)))

    send_mail(subject="Verify your email address",
              message= email_body,
              from_email="klee2011@gmail.com",
              recipient_list=[new_user.email])

    context['email'] = form.cleaned_data['email']
    return render(request, 'needs-confirmation.html', context)
    
@transaction.atomic
def confirm_registration(request, username, token):
    user = get_object_or_404(User, username=username)

    # Send 404 error if token is invalid
    if not default_token_generator.check_token(user, token):
        raise Http404

    # Otherwise token was valid, activate the user.
    user.is_active = True
    user.save()
    return render(request, 'confirmed.html', {})

@login_required
def view_teampage(request, teamid):
    reload(sys)
    sys.setdefaultencoding("utf-8")
    context = {}
    team = get_object_or_404(Team, id=teamid)
    followings = get_object_or_404(Followings, user=request.user)
    existing = followings.followings.all().values()
    try:
        existing.get(name=team.name)
        context['alreadyfollowed'] = ['y']
    except ObjectDoesNotExist:
        context['alreadyfollowed'] = ['n']
    context['team'] = team
    fixtures = get_fixtures(request, team.apiteamid)
    context['fixtures'] = fixtures
    return render_to_response('teampage.html', context, context_instance=RequestContext(request))

def get_picture(request, ateamid):
    team = get_object_or_404(Team, apiteamid=ateamid)
    picture_type = guess_type(team.picture.name)
    return HttpResponse(team.picture, content_type = picture_type)

def get_teamcity(request, ateamid):
    team = get_object_or_404(Team, apiteamid=ateamid)
    return HttpResponse(team.stadiumloc, content_type = "text/plain")

@login_required
def view_teamchat(request, teamid):
    team = get_object_or_404(Team, id=teamid)
    try:
        followings = Followings.objects.get(user=request.user)
        existing = followings.followings.all().values()
        try:
            existing.get(name=team.name)

            try:
                chatroom = ChatRoom.objects.get(team=team)
                allchats = chatroom.chats.all()
                fchats = []
                for c in allchats:
                     creationdatetime = c.created
                     today = datetime.now(utc)
                     if creationdatetime >= today - timedelta(hours=5) and creationdatetime <= today:
                         fchats.append(c)
                     else:
                         chatroom.chats.remove(c)
                         chatroom.save()
                         chat = get_object_or_404(Chat, id=c.id)
                         chat.delete()
                return render(request, "chatroom.html", {'chat': fchats, 'teamid': teamid, 'teamname': team.name})
            except ChatRoom.DoesNotExist:
                new_chatroom = ChatRoom(team=team)
                new_chatroom.save()
                c = []
                return render(request, "chatroom.html", {'chat': c, 'teamid': teamid, 'teamname' : team.name })
        except ObjectDoesNotExist:
            return HttpResponseRedirect('http://52.36.111.215/premierleagueapp/teampage/'+str(teamid))
    except Followings.DoesNotExist:
        return HttpResponseRedirect('http://52.36.111.215/premierleagueapp/teampage/'+str(teamid))

@login_required
@transaction.atomic
def add_chat(request):
    if request.method == "POST":
        msg = request.POST.get('chat-msg', None)
        teamid = request.POST.get('team-id', -1)
        team = get_object_or_404(Team, id=teamid)
        c = Chat(user=request.user, message=msg)
        if msg != '':
            c.save()
            chatroom = get_object_or_404(ChatRoom, team=team)
            chatroom.chats.add(c)
        return HttpResponseRedirect('http://52.36.111.215/premierleagueapp/teamchat/'+str(teamid))
    else:
        return HttpResponse('Request must be POST.')

@login_required
def view_messages(request, teamid):
    context = {}
    team = get_object_or_404(Team, id=teamid)
    chatroom = get_object_or_404(ChatRoom, team=team)
    allchats = chatroom.chats.all()
    fchats = []
    for c in allchats:
        creationdatetime = c.created
        today = datetime.now(utc)
        if creationdatetime >= today - timedelta(hours=5) and creationdatetime <= today:
            fchats.append(c)
        else:
            chatroom.chats.remove(c)
            chatroom.save()
            chat = get_object_or_404(Chat, id=c.id)
            chat.delete()
    return render(request, "messages.html", {'chat': fchats})

@login_required
@transaction.atomic
def unfollow(request, teamid):
    reload(sys)
    sys.setdefaultencoding("utf-8")
    errors = []
    context = {}
    team = get_object_or_404(Team, id=teamid)
    followings = get_object_or_404(Followings, user=request.user)
    existing = followings.followings.all().values()
    try:
        existing.get(name=team.name)
        followings.followings.remove(team)
        followings.save()
        context['alreadyfollowed'] = ['n']
    except ObjectDoesNotExist:
        context['alreadyfollowed'] = ['n']
    context['team'] = team
    fixtures = get_fixtures(request, team.apiteamid)
    context['fixtures'] = fixtures
    return render_to_response('teampage.html', context, context_instance=RequestContext(request))

@login_required
@transaction.atomic
def follow(request, teamid):
    reload(sys)
    sys.setdefaultencoding("utf-8")
    errors = []
    context = {}
    team = get_object_or_404(Team, id=teamid)
    followings = get_object_or_404(Followings, user=request.user)
    existing = followings.followings.all().values()
    try:
        existing.get(name=team.name)
        context['alreadyfollowed'] = ['y']
    except ObjectDoesNotExist:
        followings.followings.add(team)
        followings.save()
        context['alreadyfollowed'] = ['y']
    context['team'] = team
    fixtures = get_fixtures(request, team.apiteamid)
    context['fixtures'] = fixtures
    return render_to_response('teampage.html', context, context_instance=RequestContext(request))

@login_required
def favorite_matches(request):
    reload(sys)
    sys.setdefaultencoding("utf-8")
    errors = []
    context = {}
    followings = get_object_or_404(Followings, user=request.user)
    context['fixtures'] = []
    existing = followings.followings.all().values()
    try:
        fixtures = []
        for teaminfo in existing:
            connection = httplib.HTTPConnection('api.football-data.org')
            headers = { 'X-Auth-Token': 'f7462489e0f24a598e4232e269b18946', 'X-Response-Control': 'minified' }
            connection.request('GET', '/v1/teams/'+str(teaminfo['apiteamid'])+'/fixtures/', None, headers )
            response = json.loads(connection.getresponse().read().decode())
            fixtures.append(json.loads(json.dumps(response['fixtures'])))
        flattened = []
        for sublist in fixtures:
            for val in sublist:
                flattened.append(val)
        fixtures = flattened

        path = os.path.dirname(os.path.realpath(__file__))
        path += '/static/city.list.update2.json'
        data = {}

        with open(path) as f:
            for line in f:
                data = json.loads(line)
                
        updatedFixtures = []
        for info in fixtures:
            try: 
                hometeam = Team.objects.get(apiteamid=info['homeTeamId'])
                awayteam = Team.objects.get(apiteamid=info['awayTeamId'])
                info['hometeamstadiumloc'] = hometeam.stadiumloc
                fixture_time = info['date']
                fixture_date = datetime.strptime(fixture_time, '%Y-%m-%dT%H:%M:%SZ')
                city_data = data[hometeam.stadiumloc]
                city_id = str(city_data['id'])
                retval = get_weather(city_id, info['date'])
                if (retval != None):
                    currtemp = retval['main']['temp']
                    calvintemp = 273.15
                    celsiustemp = currtemp - calvintemp
                    retval['main']['temp'] = celsiustemp
                    info['weather_info'] = retval
                info['date'] = fixture_date
                info['htid'] = hometeam.id
                info['atid'] = awayteam.id
                updatedFixtures.append(info)
            except Team.DoesNotExist:
                continue
            
        context['fixtures'] = updatedFixtures
        return render_to_response('favoritematches.html', context, context_instance=RequestContext(request))
    except:
        raise Http404("Connection does not exist")

def handler400(request):
    render(request,'400.html', {})

def handler403(request):
    render(request,'403.html' , {})

def handler404(request):
    render(request,'404.html', { 'status' : "Connection does not exist" })

def handler500(request):
    render(request,'500.html', {})
