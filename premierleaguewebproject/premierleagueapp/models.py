from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Team(models.Model):
	name = models.CharField(max_length=200)
	picture = models.ImageField(upload_to="team", blank=True)
	stadiumname = models.CharField(max_length=200)
	stadiumloc = models.CharField(max_length=200)
	apiteamid = models.IntegerField(blank=True)
	apiteamname = models.CharField(max_length=200)

	def __unicode__(self):
		return self.name

	def __str__(self):
		return self.__unicode__()

class Fixture(models.Model):
	hometeam = models.ForeignKey(Team, related_name="home_team")
	awayteam = models.ForeignKey(Team, related_name="away_team")
	hometeamscore = models.IntegerField(default=0, blank=True)
	awayteamscore = models.IntegerField(default=0, blank=True)
	weather = models.CharField(max_length=200)
	weathericon = models.ImageField(upload_to="weather", blank=True)
	mintemp = models.IntegerField(blank=True)
	maxtemp = models.IntegerField(blank=True)

	def __unicode__(self):
		return self.hometeam + " vs " + self.awayteam

	def __str__(self):
		return self.__unicode__()

class Comment(models.Model):
    text = models.CharField(max_length=200)
    fixture = models.ForeignKey(Fixture)
    username = models.CharField(max_length=200)
    datetime = models.DateTimeField(default=datetime.now, blank=True)
    def __unicode__(self):
        return self.text + self.username
    
    def __str__(self):
        return self.__unicode__()


class Followings(models.Model):
    user = models.ForeignKey(User)
    followings = models.ManyToManyField(Team, related_name="users_teamfollowings")
    
    def __unicode__(self):
    	return self.user

    def __str__(self):
        return self.__unicode__()

class Chat(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    message = models.CharField(max_length=200)

    def __unicode__(self):
        return self.message

class ChatRoom(models.Model):
	team = models.ForeignKey(Team)
	chats = models.ManyToManyField(Chat, related_name="team_chats")

	def __unicode__(self):
		return self.team + " chatroom"