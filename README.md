Jae Joon Lee sample code explanation

<Project spec>
This web application was built for my last project in web application class. The team was
consisted with me and one other student. The purpose of our app was to build a platform where
English Premier League(EPL) fans can figure out all the necessary information about the
league, weather, and post comments on specific games, and chat with other fans. We
researched through internet, and figured that there were no service like ours that gathers all the
games within filtered time period, with weathers fetched from the weather API, and plotted down
on a map. So basically it's like a SNS like experience, but with live EPL status combined in one
service.
(This app is built with django, with javascript and bootstrap. Also we used weather API / football
fixture API, and map api called 'Leaflet'. We had to subscribe for the weather API and football
API, so even compiled, the app will have limited access)

<Sample code snippet that was implemented at my end that would like to explain>
/premierleaguewebproject/premierleagueapp/views.py - home(line 97)
This function is the core of our app. We first send a http request to the football API, and retrieve
all the fixture data from the API, overwrite the current one we have on
/static/city.list.update2.json
And after refreshing the data we got from the football API, we link the weather where the fixture
is held by calling get_weather(line 183) with city and time of the fixture as a parameter. After we
combined all the features of each games, we send it to front-end(html) file to display.
Also, I've also implemented plotting where the map is held in line 156. Where after getting the
latitude and longitude of the city, it returns an object to plot it down on the map API(leaflet).