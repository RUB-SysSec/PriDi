#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   This file holds data structures for the config file.
#
#   @date   19.10.2015
#   @author Nicolai Wilkop
#

import datetime
import pytz


def _get_timezone_offset_by_timezone(timezone):
    ##
    #   Determine the timezone offset in JavaScript format for the given timzone.
    #
    #   @param {string} timezone - Timezone string.
    #
    #   @return {int} timezone offset in JavaScript format.
    #

    offset = datetime.datetime.now(pytz.timezone(timezone)).strftime("%z")

    # Convert to JavaScript getTimezoneOffset format
    hours = offset[:3]
    minutes = int(offset[3:]) / 6
    js_timezone_offset = "{hours}.{decimal_minutes}".format(
        hours=hours,
        decimal_minutes=minutes
    )

    js_timezone_offset = int(float(js_timezone_offset) * -60)

    return js_timezone_offset


def get_timezone_offset(country_code):
    ##
    #   Determine the  timezone offset for the given country code.
    #
    #   @param {string} country_code - 2 digits ISO country code.
    #
    #   @return {int} timezone offset in JavaScript format.
    #

    timezones = pytz.country_timezones[country_code]
    middle_timezone = timezones[int(len(timezones) / 2)]

    js_timezone_offset = _get_timezone_offset_by_timezone(timezone=middle_timezone)

    return js_timezone_offset


class WebDriverSettings:
    ##
    #
    #

    def __init__(self, wd_port, country, country_code, num_wd_instances=1, wd_ip='localhost', proxy_ip=None, proxy_port=None):
        ##
        #
        #   @param {int} wd_port - Port for the local webdriver server.
        #   @param {string} country - Country of the IP address of the webdriver
        #   server. If a proxy is configured, the country of the proxy have to
        #   be passed here.
        #   @param {int} num_wd_instances - (optional) Number of running WebDriver
        #   instances on the given IP address.
        #   @param {string} wd_ip - (optional) IP of the WebDriver Server.
        #   @param {string} proxy_ip - (optional) IP or URI of the proxy server.
        #   @param {int} porxy_port - (optional) Port of the proxy server.
        #

        if proxy_ip is not None:
            proxy_ip = proxy_ip.strip()

        self.wd_ip              = wd_ip
        self.wd_port            = wd_port
        self.country            = country.strip()
        self.country_code       = country_code.strip()
        self.timezone_offset    = get_timezone_offset(country_code=country_code)
        self.proxy_ip           = proxy_ip
        self.proxy_port         = proxy_port
        self.num_wd_instances   = num_wd_instances

    def is_proxy_configured(self):

        if self.proxy_ip is None and self.proxy_port is None:
            return False
        else:
            return True


# Rebuild of an Enum for website types.
class WebsiteTypes:
    HOTELS = "hotels"
    CARS = "cars"
