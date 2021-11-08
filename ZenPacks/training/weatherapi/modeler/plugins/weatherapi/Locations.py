"""Models locations using the rapidapi Weather API."""

# stdlib Imports
import json
import urllib


# Twisted Imports
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList
from twisted.web.client import getPage, Agent, readBody
from twisted.web.http_headers import Headers

# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin


class Locations(PythonPlugin):
    """Weather API Locations modeler plugin."""
    
    relname = 'weatherAPILocations'
    modname = 'ZenPacks.training.weatherapi.WeatherAPILocations'
    
    requiredProperties = (
        'zWeatherAPICities',
        'zWeatherAPIKey',
        'zWeatherAPIHost',
    )
    
    deviceProperties = PythonPlugin.deviceProperties + requiredProperties
    
    @inlineCallbacks
    def collect(self, device, log):
        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)
        
        WeatherAPICities = getattr(device, 'zWeatherAPICities', None)
        if not WeatherAPICities:
            log.error(
                "%s: %s not set.",
                device.id,
                'zWeatherAPICities')
            returnValue(None)
        responses = []
        
        WeatherAPIKey = getattr(device, 'zWeatherAPIKey', None)
        WeatherAPIHost = getattr(device, 'zWeatherAPIHost', None)
        
        headers = {
            'x-rapidapi-host': [WeatherAPIHost],
            'x-rapidapi-key': [WeatherAPIKey]
        }
        
        for WeatherAPICity in WeatherAPICities:
            if WeatherAPICity:
                try:
                    client = Agent(reactor)
                    response = yield client.request('GET',
                                                    'https://weatherapi-com.p.rapidapi.com/current.json?q={query}'
                                                    .format(query=WeatherAPICity), Headers(headers))
                    response = yield readBody(response)
                    responses.append(json.loads(response))
                except Exception, e:
                    log.error(
                        "%s: %s", device.id, e)
                    returnValue(None)
        
        returnValue(responses)
    
    def process(self, device, results, log):
        """Process results. Return iterable of datamaps or None."""
        rm = self.relMap()

        for locationResult in results:
            id = self.prepId(locationResult['location']['name'])
            rm.append(self.objectMap({
                'id': id,
                'City': locationResult['location']['name'],
                'Longitude': locationResult['location']['lon'],
                'Latitude': locationResult['location']['lat'],
                'Country': locationResult['location']['country'],
            }))
        return rm
