#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   07.10.2015
#   @author Nicolai Wilkop
#
#   @target_website localhost_fingerprinting
#

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium

import time
import logging


class NavScraper:
    ##
    #   
    #
    # ENTRY_URI = "file:///D:/Uni/Masterarbeit/Price-Discrimination/Fingerprinting/FPClass/get_fingerprint.html"
    ENTRY_URI = "http://nicolaiwilkop.de/Old_stuff/html_experiments/get_fingerprint.html"
    PAGE_TYPE = "debug"

    def __init__(self):
        ##
        #
        #   @param {webdriver} driver - Selenium webdriver object which is 
        #   connected to the PhantomJS WebDriver server.
        #      
        pass  


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        navigation_successful = False

        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "results"))
            )

        except selenium.common.exceptions.TimeoutException, e:

            # If no results were found.
            logging.warning("Results not found!")
            logging.error(driver.page_source)

            # Set return value to false.
            navigation_successful = False

        finally:

            print("## Navigating finished - localhost")

            driver.get_screenshot_as_file("{0}_localhost_navscraper.png".format(time.time()))

        return navigation_successful


    def scrape_results(self, driver):
        ##
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #
        # html_source = driver.page_source
        pass
