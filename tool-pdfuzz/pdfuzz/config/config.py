#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   Main config file for PDFuzz.
#
#   @date   10.10.2015
#   @author Nicolai Wilkop
#

import pdfuzz.config.config_data_structures as cfg_data

import pdfuzz.config.navscrapers.localhost_navscraper as localhost_navscraper
import pdfuzz.config.navscrapers.panopticlick_navscraper as panopticlick_navscraper
import pdfuzz.config.navscrapers.hrs_navscraper as hrs_navscraper
import pdfuzz.config.navscrapers.booking_navscraper as booking_navscraper
import pdfuzz.config.navscrapers.hotels_navscraper as hotels_navscraper
import pdfuzz.config.navscrapers.orbitz_navscraper as orbitz_navscraper
import pdfuzz.config.navscrapers.orbitz_cars_navscraper as orbitz_cars_navscraper
import pdfuzz.config.navscrapers.avis_cars_navscraper as avis_cars_navscraper

# Add NavScraper classes for the sites that are to be tested.
NAVSCRAPERS = [

    # panopticlick_navscraper.NavScraper,
    # booking_navscraper.NavScraper,
    hotels_navscraper.NavScraper,
    hrs_navscraper.NavScraper,
    orbitz_navscraper.NavScraper,
    # avis_cars_navscraper.NavScraper,
    # orbitz_cars_navscraper.NavScraper,
    # localhost_navscraper.NavScraper,

]


# List of WebDriver Server
WEBDRIVERS_SETTINGS = [

    # ############################################### #
    # WebDriver Instances running on external server. #
    # ############################################### #

    cfg_data.WebDriverSettings(
        wd_ip='192.168.122.50',
        wd_port=8080,
        country="Germany",
        country_code="DE",
        num_wd_instances=6
    ),
    cfg_data.WebDriverSettings(
        wd_ip='192.168.122.51',
        wd_port=8080,
        country="France",
        country_code="FR",
        num_wd_instances=6
    ),
    cfg_data.WebDriverSettings(
        wd_ip='192.168.122.52',
        wd_port=8080,
        country="Romania",
        country_code="RO",
        num_wd_instances=6
    ),
    # cfg_data.WebDriverSettings(
    #     wd_ip='192.168.122.117',
    #     wd_port=8080,
    #     country="Russia",
    #     country_code="RU",
    #     num_wd_instances=6
    # ),
    cfg_data.WebDriverSettings(
        wd_ip='192.168.122.67',
        wd_port=8080,
        proxy_ip="104.236.88.28",
        proxy_port=8080,
        country="USA",
        country_code="US",
        num_wd_instances=6
    ),

    # ######################################### #
    # WebDriver Instances running on localhost. #
    # ######################################### #

    # cfg_data.WebDriverSettings(
    #     wd_port=4000,
    #     country="Germany",
    #     country_code="DE"
    # ),
    # cfg_data.WebDriverSettings(
    #     wd_port=4001,
    #     country="USA",
    #     country_code="US",
    #     proxy_ip="108.59.10.129",
    #     proxy_port=55555
    # ),
    # cfg_data.WebDriverSettings(
    #     wd_port=4002,
    #     country="Russia",
    #     country_code="RU",
    #     proxy_ip="82.116.42.154",
    #     proxy_port=3128
    # ),
    # cfg_data.WebDriverSettings(
    #     wd_port=4003,
    #     country="India",
    #     country_code="IN",
    #     proxy_ip="103.14.196.86",
    #     proxy_port=8080
    # ),
    # cfg_data.WebDriverSettings(
    #     wd_port=4004,
    #     country="France",
    #     country_code="FR",
    #     proxy_ip="151.80.64.100",
    #     proxy_port=8080
    # ),

]


# Number of VM PhantomJS instances
NUM_VM_PHANTOMJS_INSTANCES = 6


# Time in seconds to wait for page-load is finished.
PAGE_LOAD_TIMEOUT = 20


# Seconds to wait, so that the server will not be ddosed.
ANTI_DDOS_DELAY_SECONDS = 20


# Timeout counter: Number of maximal timeouts per website. If the number of
# timeouts is reached the website will be skipped. -1 to turn it off.
TIMEOUT_LIMIT = -1


# Number of times a fingerprint is scanned again if the scan do not complete.
FP_RETRY = 2


# Configuration parameter for the database connection.
MYSQL = {

    "host": "localhost",
    "port": 3306,
    "user": "pridi-master",
    "pass": "pridi-master",
    "db": "pdfuzz",

}


# Dictionary to save the search parameters for the different types of websites.
# The keys need to be added to the WebsiteTypes class in
# config_data_structures.py which is located in the same folder as config.py.
SEARCH_PARAMETERS = {

    # Search parameters for NavScrapers of type "hotels"
    "hotels": {

        "travel_target": "Berlin Deutschland",
        # "travel_target": "London United Kingdom",
        # "travel_target": "Tokyo, Tokyo Japan",
        # "travel_target": "Los Angeles, California, USA",

        # "check_in_day": "14",
        # "check_in_month": "10",
        "check_in_day": "17",
        "check_in_month": "2",

        # "check_in_year": "2016",
        "check_in_year": "2017",

        # "check_out_day": "15",
        # "check_out_month": "10",
        "check_out_day": "18",
        "check_out_month": "2",

        # "check_out_year": "2016",
        "check_out_year": "2017",
        "number_of_adults": "1",
        "number_of_single_rooms": "1",
        "number_of_double_rooms": "0",

    },

    "cars": {

        "picking_up": "TXL",
        "dropping_off": "TXL",
        "pick_up_day": "17",
        "pick_up_month": "2",
        "pick_up_year": "2017",
        "drop_off_day": "18",
        "drop_off_month": "2",
        "drop_off_year": "2017",
        "pick_up_time": "10:30",
        "drop_off_time": "10:30",

    },

}


# Definition of directories.
DIR_LOG = "logs/"
DIR_ERROR = "errors/"
DIR_DEBUG = "debug/"


# Making the WebsiteTypes class available.
PAGE_TYPES = cfg_data.WebsiteTypes


# Name of the fingerprint table. This variable is modified via the commandline
# interface.
FINGERPRINT_TABLE_NAME = "fingerprints"


# List of columns that should be ignored while interacting with the fingerprint
# table. This feature is only used to reduce the number of logged warnings. All
# columns that do not represent a fingerprint feature should be listed here.
IGNORED_FINGERPRINT_TABLE_COLUMNS = [
    "pairing",
    "factor_1",
    "factor_2",
    "factor_3",
]
