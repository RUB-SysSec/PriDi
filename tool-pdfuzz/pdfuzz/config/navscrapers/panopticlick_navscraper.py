#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   18.10.2015
#   @author Nicolai Wilkop
#
#   @target_website panopticlick.eff.org
#

import time
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium

import pdfuzz.config.navscrapers.api.navigation as Navigation
# from pprint import pprint


class NavScraper:
    ##
    #
    #
    ENTRY_URI = "https://panopticlick.eff.org"
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
        # driver.get_screenshot_as_file("{0}_LOADED_panopticlick_navscraper.png".format(time.time()))

        start_tracking = driver.find_element_by_id("trackerlink")
        start_tracking.click()

        try:
            # WebDriverWait(driver, 60).until(
            #     EC.presence_of_element_located((By.ID, "results"))
            # )

            Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector="#fingerprintTable #results",
                timeout=60
            )

            Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector="#buttons",
                timeout=60
            )

            more_results = driver.find_element_by_id("showFingerprintLink2")
            more_results.click()

            time.sleep(2)

            print("## Element found - panopticlick")

            return False

        except selenium.common.exceptions.TimeoutException:

            # If no results were found.
            print("## Element not found - panopticlick")

            # Set return value to false.
            navigation_successful = False

        finally:

            print("## Navigating finished - panopticlick")
            driver.get_screenshot_as_file("{0}_panopticlick_navscraper.png".format(time.time()))
            logging.debug(driver.page_source)

        return navigation_successful


    def scrape_results(self, driver):
        ##
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #
        
        html_source = driver.page_source

