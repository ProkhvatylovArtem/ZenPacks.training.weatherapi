"""Monitors current conditions using the rapidapi Weather API"""

# Logging
import logging

LOG = logging.getLogger('zen.WeatherAPI')

# stdlib Imports
import json
import time
from datetime import datetime
from dateutil import parser

# Twisted Imports
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage, Agent, readBody
from twisted.web.http_headers import Headers

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
)


class Conditions(PythonDataSourcePlugin):
    """WeatherAPI conditions data source plugin."""
    
    proxy_attrinutes = "zWeatherAPICities, zWeatherAPIHost, zWeatherAPIKey,"
    
    @classmethod
    def config_key(cls, datasource, context):
        LOG.info("config_key is working")
        return (
            context.device().id,
            datasource.getCycleTime(context),
            context.id,
            'Current conditions',
        )
    
    @classmethod
    def params(cls, datasource, context):
        LOG.info("params is working")
        return {
            'city_id': context.id,
            'counrty': context.country,
        }
    
    @inlineCallbacks
    def collect(self, config):
        LOG.info("collect is working")
        data = self.new_data()
        
        headers = {
            'x-rapidapi-host': [config.datasources.zWeatherAPIHost],
            'x-rapidapi-key': [config.datasources.zWeatyerAPIKey]
        }
        LOG.info(headers)
        
        for datasource in config.datasources:
            try:
                client = Agent(reactor)
                response = yield client.request('GET',
                                                'https://weatherapi-com.p.rapidapi.com/current.json?q={query}'
                                                .format(query=config.datasources.zWeatherAPICities), Headers(headers))
                response = yield readBody(response)
            except Exception:
                LOG.exception(
                    "%s: failed to get conditions data for %s",
                    config.id,
                    datasource.params.get('id'))
                continue
            
            current_observation = response.get('current')
            LOG.info(current_observation)
            for datapoint_id in (x.id for x in datasource.points):
                if datapoint_id not in current_observation:
                    continue
                
                try:
                    value = current_observation[datapoint_id]['temp_c']
                    if isinstance(value, basestring):
                        value = value.strip(' %')
                    value = float(value)
                except (TypeError, ValueError):
                    # Sometimes values are NA or not available.
                    continue
                
                dpname = '_'.join((datasource.datasource, datapoint_id))
                data['values'][datasource.component][dpname] = (value, 'N')
        LOG.info(data)
        returnValue(data)
