#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   07.10.2015
#   @author Nicolai Wilkop
#
#   @target_website www.template.tmp
#

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class NavScraper:
    ##
    #   
    #
    ENTRY_URI = "http://www.template.tmp"
    PAGE_TYPE = "debug"

    def __init__(self):
        pass        


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #   Navigates to the results listing.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {dict} search_parameters - Parameters for the search input form.
        #
        pass


    def scrape_results(self, driver):
        ##
        #   Extract result information and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #
        pass


