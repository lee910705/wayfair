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

from background_task import background

@background(schedule=20)
def send_emails():
    context = {}
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
                retval = get_weather(city_id, info['date'])
                if (retval != None):
                    for u in allusers:
                        try:
                            followings = Followings.objects.get(user=u)
                            existing = followings.followings.all().values()
                            try:
                                existing.get(name=hometeam.name)
                                print(hometeam.name)
                                send_match_email(u, hometeam, info['date'])
                            except ObjectDoesNotExist:
                                continue
                        except Followings.DoesNotExist:
                            continue
            except Team.DoesNotExist:
                continue
    except httplib.HTTPException:
        raise Http404("Connection does not exist")

def send_match_email(user, team, fixture_date_str):
    email_body = """
This is from Premier League Share Your Soccer Moments.
This is a reminder of %s's upcoming match that will take place in %s
""" % (team.name, fixture_date_str)

    send_mail(subject="Upcoming Match Reminder",
              message= email_body,
              from_email="klee2011@gmail.com",
              recipient_list=[user.email])
    return None

