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
    
    @classmethod
    def config_key(cls, datasource, context):
        LOG.info("config_key is working")
        return (
            context.device().id,
            datasource.getCycleTime(context),
            'Current conditions',
        )
    
    @classmethod
    def params(cls, datasource, context):
        LOG.info("params is working")
        return {
            'WeatherAPIKey': context.zWeatherAPIKey,
            'WeatherAPIHost': context.zWeatherAPIHost,
            'city_id': context.id,
            'country': context.country,
        }
    
    @inlineCallbacks
    def collect(self, config):
        LOG.info("collect is working")
        headers = {
            'x-rapidapi-host': [config.datasources[0].params['WeatherAPIHost']],
            'x-rapidapi-key': [config.datasources[0].params['WeatherAPIKey']]
        }
        result = []
        for datasource in config.datasources:
            try:
                client = Agent(reactor)
                response = yield client.request('GET',
                                                'https://weatherapi-com.p.rapidapi.com/current.json?q={query}'
                                                .format(query=datasource.params['city_id']), Headers(headers))
                response = yield readBody(response)
                result.append(json.loads(response))
                # LOG.info(response)
            except Exception:
                LOG.exception(
                    "%s: failed to get conditions data for %s",
                    config.id,
                    datasource.params.get('id'))
                continue
        returnValue(result)
        
        
    def onResult(self, result, config):
        LOG.info("onResult is working")
        if result is not None:
            return result
        else:
            return None
            

    def onSuccess(self, result, config):
        LOG.info("onSuccess is working")
        data = self.new_data()
        for locationResult, datasource in zip(result, config.datasources):
            current_observation = locationResult.get('current')
            LOG.info(current_observation)
            for datapoint_id in (x.id for x in datasource.points):
                if datapoint_id not in current_observation:
                    continue
        
                try:
                    value = current_observation.get(datapoint_id)
                    if isinstance(value, basestring):
                        value = value.strip(' %')
                    value = float(value)
                except (TypeError, ValueError):
                    # Sometimes values are NA or not available.
                    continue
                LOG.info(datasource.datasource)
                dpname = '_'.join((datasource.datasource, datapoint_id))
                data['values'][datasource.component][dpname] = (value, 'N')
        
        result = data
        LOG.info(result)
        return result

    def onError(self, result, config):
        """Called only on error. After onResult, before onComplete."""
        LOG.info("onError working")
        LOG.exception("In onError - result is {} and config is {}.".format(result, config.id))
        return result

    def onComplete(self, result, config):
        """Called last for success and error."""
        LOG.info("onComplete working")
        return result

    def cleanup(self, config):
        """Called when collector exits, or task is deleted or recreated."""
        LOG.info("cleanup working")
        return
