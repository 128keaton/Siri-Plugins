#!/usr/bin/python
# -*- coding: utf-8 -*-
#version 0.5.1 alpha
#todo: add RequestOrigin handler, Weather snippet, fix UTF-8 encoding..
import json
import sys
import urllib, urllib2
import re
from xml.dom import minidom
from urllib import quote

from plugin import *

from siriObjects.baseObjects import AceObject, ClientBoundCommand
from siriObjects.uiObjects import AddViews, AssistantUtteranceView
from siriObjects.systemObjects import DomainObject


class SiriWeatherItemSnippet(AceObject):
    def __init__(self, userCurrentLocation=True, items=None):
        super(SiriWeatherItemSnippet, self).__init__("WeatherItemSnippet", "com.apple.ace.weather")
       
        self.items = items
    
    def to_plist(self):
        self.add_property('userCurrentLocation')
        self.add_property('items')
        return super(SiriWeatherItemSnippet, self).to_plist()



class SiriLocation(AceObject):
    def __init__(self, label="Apple", street="1 Infinite Loop", city="Cupertino", stateCode="CA", countryCode="US", postalCode="95014", latitude=37.3317031860352, longitude=-122.030089795589):
        super(SiriLocation, self).__init__("Location", "com.apple.ace.system")
        self.label = label
        self.street = street
        self.city = city
        self.stateCode = stateCode
        self.countryCode = countryCode
        self.postalCode = postalCode
        self.latitude = latitude
        self.longitude = longitude
    
    def to_plist(self):
        self.add_property('label')
        self.add_property('street')
        self.add_property('city')
        self.add_property('stateCode')
        self.add_property('countryCode')
        self.add_property('postalCode')
        self.add_property('latitude')
        self.add_property('longitude')
        return super(SiriLocation, self).to_plist()

class SiriWeatherItem(AceObject):
    def __init__(self, label="Apple Headquarters", location=SiriLocation(), detailType="BUSINESS_ITEM"):
        super(SiriWeatherItem, self).__init__("weatherItem", "com.apple.ace.weather")
        self.userCurrentLocation = userCurrentLocation
        self.label = label
        self.detailType = detailType
        self.location = location
    
    def to_plist(self):
        self.add_property('label')
        self.add_property('detailType')
        self.add_property('location')
        return super(SiriweatherItem, self).to_plist()
class WeatherSnippet(AceObject):
    def __init__(self, clocks=None):
        super(WeatherSnippet, self).__init__("Snippet", "com.apple.ace.weather")
        self.weather = weather if weather != None else []

    def to_plist(self):
        self.add_property('weather')
        return super(WeatherSnippet, self).to_plist()

class WeatherObject(DomainObject):
    def __init__(self):
        super(ClockObject, self).__init__("com.apple.ace.weather")
        self.unlocalizedCountryName = None
        self.unlocalizedCityName = None
    
        self.countryName = None
        self.countryCode = None
        self.cityName = None
        self.alCityId = None
    
    def to_plist(self):
        self.add_property('unlocalizedCountryName')
        self.add_property('unlocalizedCityName')
      
        self.add_property('countryName')
        self.add_property('countryCode')
        self.add_property('cityName')
        self.add_property('alCityId')
        return super(WeatherObject, self).to_plist()

####### geonames.org API username ######
geonames_user="test2"

class weather(Plugin):
    
    localizations = {"currentWeather": 
                        {"search":{"de-DE": "Es wird gesucht ...", "en-US": "Looking up ..."}, 
                         "currentWeather": {"de-DE": "Es ist @{fn#currentWeather}", "en-US": "It is @{fn#currentWeather}"}}, 
                     "currentWeatherIn": 
                        {"search":{"de-DE": "Es wird gesucht ...", "en-US": "Looking up ..."}, 
                         "currentWeatherIn": 
                                {
                                "tts": {"de-DE": u"Das Wetter in {0},{1} ist @{{fn#currentWeatherIn#{2}}}:", "en-US": "The weather in {0},{1} is @{{fn#currentWeatherIn#{2}}}:"},
                                "text": {"de-DE": u"Das Wetter in {0}, {1} ist @{{fn#currentWeatherIn#{2}}}:", "en-US": "The weather in {0}, {1} is @{{fn#currentWeatherIn#{2}}}:"}
                                }
                        },
                    "failure": {
                                "de-DE": "Ich kann dir das Wetter gerade nicht sagen!", "en-US": "I cannot show you the weather right now"
                                }
                    }

    @register("de-DE", "(Wie ist das Wetter.*)|(.*Wetter.*)")     
    @register("en-US", "(How is the weather.*)|(.*weather.*)")
    def currentWheather(self, speech, language):
        #check for location coords later as soon as they are implented, for now just reject request
            
            if language == 'de-DE':
                self.say(u"Bitte gebe ein Land oder eine Stadt bei deiner Anfrage an!")
            else:            
                self.ask(u"Please provide a country or city with your request!")
            self.complete_request()
        
    @register("de-DE", "(Wie ist das Wetter.*in [a-z]+)|(Wetter.*in [a-z]+)")
    @register("en-US", "(How is the weather.*in [a-z]+)|(.*weather.*in [a-z]+)")
    def currentWeatherIn(self, speech, language):
        weathersnippet = SiriWeatherItemSnippet(items=[SiriWeatherItem()])
        view = AddViews(self.refId, dialogPhase="Reflection")
        view.views = [AssistantUtteranceView(text=weather.localizations['currentWeatherIn']['search'][language], speakableText=weather.localizations['currentWeatherIn']['search'][language], dialogIdentifier="Weather#getWeather"),weathersnippet]
        self.sendRequestWithoutAnswer(view)
        error = False
        countryOrCity = re.match(".*in (\D[\\xf6\\xfc\\xe4a-z, ]+)$", speech, re.IGNORECASE)
      

        
        if countryOrCity != None:
            #self.say(countryOrCity.decode("latin-1").encode("utf-8"))
            countryOrCity = countryOrCity.group(1).strip()
            # lets see what we got, a country or a city... 
            # lets use google geocoding API for that
            url = "http://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=false&language={1}".format(urllib.quote_plus(countryOrCity.encode("utf-8")), language)
            # lets wait max 3 seconds
            
            jsonString = None
            try:
                jsonString = urllib2.urlopen(url, timeout=3).read()
            except:
                pass
            if jsonString != None:
                response = json.loads(jsonString)
                # lets see what we have...
                if response['status'] == 'OK':
                    components = response['results'][0]['address_components']
                    types = components[0]['types'] # <- this should be the city or country
                    if "country" in types:
                        # OK we have a country as input, that sucks, we need the capital, lets try again and ask for capital also
                        components = filter(lambda x: True if "country" in x['types'] else False, components)
                        url = "http://maps.googleapis.com/maps/api/geocode/json?address=capital%20{0}&sensor=false&language={1}".format(urllib.quote_plus(components[0]['long_name']), language)
                            # lets wait max 3 seconds
                        jsonString = None
                        try:
                            jsonString = urllib2.urlopen(url, timeout=3).read()
                        except:
                            pass
                        if jsonString != None:
                            response = json.loads(jsonString)
                            if response['status'] == 'OK':
                                components = response['results'][0]['address_components']
                # response could have changed, lets check again, but it should be a city by now 
                if response['status'] == 'OK':
                    # get latitude and longitude
                    if language == 'de-DE':
                        s=get_weather_from_google(components[0]['long_name'].encode("utf-8"),'de')
                        self.say(u'Hier kommt das Wetter fuer {0}'.format(s['forecast_information']['city']))
                        to_speak=u'Temperatur: {0} grad Celsius, {1}, {2}, Es ist: {3}'.format(s['current_conditions']['temp_c'],s['current_conditions']['humidity'],s['current_conditions']['wind_condition'],s['current_conditions']['condition'])
                        to_read=' '
                        self.say(to_speak, to_read)
                    else:
                        s=get_weather_from_google(components[0]['long_name'],'en')
                        self.say(u'Here is the weather for: {0}'.format(s['forecast_information']['city']))
                        to_speak='The temperature is : {0} degrees Fahrenheit , {1}, {2}, It is: {3}'.format(s['current_conditions']['temp_f'],s['current_conditions']['humidity'],s['current_conditions']['wind_condition'],s['current_conditions']['condition'])
                        to_read=(to_speak)

                        self.say(to_speak, to_read)    


                else:
                    error = True
            else:
                error = True
        else:
            error = True
        if error:
            view = AddViews(self.refId, dialogPhase="Completion")
            view.views = [AssistantUtteranceView(text=weather.localizations['failure'][language], speakableText=weather.localizations['failure'][language], dialogIdentifier="Clock#cannotShowClocks")]
            self.sendRequestWithoutAnswer(view)
        self.complete_request()
    

def get_weather_from_google(location_id, hl = 'de'):
    GOOGLE_WEATHER_URL   = 'http://www.google.com/ig/api?weather=%s&hl=%s'
    location_id, hl = list(map(quote, (location_id, hl)))
    url = GOOGLE_WEATHER_URL % (location_id.decode("latin-1").encode("utf-8"), hl)
    f = urllib.urlopen(url)
    content = f.read()
    dom = minidom.parseString(content.decode('latin-1').encode('utf-8'))    
    weather_data = {}
    weather_dom = dom.getElementsByTagName('weather')[0]
    
    data_structure = { 
        'forecast_information': ('city', 'postal_code', 'latitude_e6', 'longitude_e6', 'forecast_date', 'current_date_time', 'unit_system'),
        'current_conditions': ('condition','temp_f', 'temp_c', 'humidity', 'wind_condition', 'icon')
    }           
    for (tag, list_of_tags2) in data_structure.items():
        tmp_conditions = {}
        for tag2 in list_of_tags2:
            try: 
                tmp_conditions[tag2] =  weather_dom.getElementsByTagName(tag)[0].getElementsByTagName(tag2)[0].getAttribute('data')
            except IndexError:
                pass
        weather_data[tag] = tmp_conditions

    forecast_conditions = ('day_of_week', 'low', 'high', 'icon', 'condition')
    forecasts = []
    
    for forecast in dom.getElementsByTagName('forecast_conditions'):
        tmp_forecast = {}
        for tag in forecast_conditions:
            tmp_forecast[tag] = forecast.getElementsByTagName(tag)[0].getAttribute('data')
        forecasts.append(tmp_forecast)

    weather_data['forecasts'] = forecasts
    dom.unlink()

    return weather_data