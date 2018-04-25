#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   07.10.2015
#   @author Nicolai Wilkop and Henry Hosseini
#
#   @target_website www.avis.com
#


import sys
import logging
import re
import time
from datetime import datetime
import bs4

from pprint import pprint

from selenium.webdriver.support.ui import Select
import selenium

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import pdfuzz.config.navscrapers.api.currency_converter as CurrencyConverter
import pdfuzz.config.navscrapers.api.navigation as Navigation
import pdfuzz.common.exceptions as PDFuzzExceptions


class NavScraper:
    ##
    #
    #
    ENTRY_URI = "http://www.avis.com/"
    PAGE_TYPE = "cars"

    def __init__(self):
        ##
        #
        #   @param {webdriver} driver - Selenium webdriver object which is
        #   connected to the PhantomJS WebDriver server.
        #
        self.WEBSITE_MODE = "mobile"


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        navigation_successful = True

        self.picking_up_location = search_parameters.get("picking_up")
        self.dropping_off_location = search_parameters.get("dropping_off")
        self.pick_up_day = int(search_parameters.get("pick_up_day"))
        self.pick_up_month = int(search_parameters.get("pick_up_month"))
        self.pick_up_year = int(search_parameters.get("pick_up_year"))
        self.drop_off_day = int(search_parameters.get("drop_off_day"))
        self.drop_off_month = int(search_parameters.get("drop_off_month"))
        self.drop_off_year = int(search_parameters.get("drop_off_year"))
        self.pick_up_time = search_parameters.get("pick_up_time")
        self.drop_off_time = search_parameters.get("drop_off_time")

        try:

            try:
                # Try mobile mode
                reserve_now_button = driver.find_element_by_id("home-reserve-now")
                reserve_now_button.click()
                self.WEBSITE_MODE = "mobile"

            except selenium.common.exceptions.NoSuchElementException:
                # Default mode
                self.WEBSITE_MODE = "default"

            # Determine the Website mode and start the navigation handling.
            if self.WEBSITE_MODE == "mobile":
                self._handle_mobile_navigition(
                    driver=driver
                )

                # Waiting for results.
                Navigation.wait_for_the_presence_of_element(
                    driver=driver,
                    element_css_selector=".car-selector > section",
                    timeout=60
                )

            elif self.WEBSITE_MODE == "default":
                self._handle_default_navigation(
                    driver=driver
                )

                # Waiting for results.
                Navigation.wait_for_the_presence_of_element(
                    driver=driver,
                    element_css_selector="#vehPresentation .listOfVehicles .carView",
                    timeout=60
                )

        except selenium.common.exceptions.TimeoutException, e:

            # If no results were found.
            logging.warning("Results not found!")
            # logging.error(driver.page_source)

            # Set return value to false.
            navigation_successful = False

        except:
            # Log unexpected errors while navigating.
            exc_type, exc_value = sys.exc_info()[:2]
            print("Unexpected error: {type} <msg '{msg}'>".format(
                type=exc_type, msg=exc_value))
            logging.exception("Unexpected error:")

            # Set the return value to False.
            navigation_successful = False

        finally:

            print("## Navigating finished - Avis Cars")

            # driver.get_screenshot_as_file("{0}_avis_cars_navscraper.png".format(time.time()))

        return navigation_successful



    def _handle_default_navigation(self, driver):

        pickup_location_field = driver.find_element_by_css_selector("#location")
        pickup_location_field.click()
        time.sleep(1)
        pickup_location_field.send_keys(self.picking_up_location)
        logging.debug("[AVIS CARS] Pickup location entered")
        time.sleep(1)

        pickup_date_field = driver.find_element_by_css_selector("#from")
        pickup_date_field.click()
        time.sleep(1)
        pick_up_date_string = "{month:02d}/{day:02d}/{year}".format(
            day=self.pick_up_day,
            month=self.pick_up_month,
            year=self.pick_up_year
        )
        pickup_date_field.send_keys(pick_up_date_string)
        pickup_date_field.send_keys(Keys.RETURN)
        logging.debug("[AVIS CARS] Pickup date entered")
        time.sleep(3)


        drop_off_date_field = driver.find_element_by_css_selector("#to")
        drop_off_date_field.click()
        drop_off_date_string = "{month:02d}/{day:02d}/{year}".format(
            day=self.drop_off_day,
            month=self.drop_off_month,
            year=self.drop_off_year
        )
        drop_off_date_field.send_keys(drop_off_date_string)
        drop_off_date_field.send_keys(Keys.RETURN)
        logging.debug("[AVIS CARS] Dropoff date entered")
        time.sleep(3)

        # Convert pick up time to 12h format.
        d = datetime.strptime(self.pick_up_time, "%H:%M")
        pickup_time = d.strftime("%I:%M %p")

        # Set pick up time.
        pickup_time_select = Select(driver.find_element_by_name("resForm.pickUpTime"))
        pickup_time_select.select_by_value(pickup_time)

        # Convert drop off time to 12h format.
        d = datetime.strptime(self.drop_off_time, "%H:%M")
        dropoff_time = d.strftime("%I:%M %p")

        # Set drop off time.
        dropoff_time_select = Select(driver.find_element_by_name("resForm.dropOffTime"))
        dropoff_time_select.select_by_value(dropoff_time)

        # Click the search button.
        search_button = driver.find_element_by_css_selector("#selectMyCarId")
        search_button.click()


    def _handle_mobile_navigition(self, driver):

        picking_up_element = driver.find_element_by_css_selector("#pick-up-location")
        picking_up_element.click()
        picking_up_element.send_keys(self.picking_up_location)

        # Determine formatted date to inject into the input fields.
        pick_up_date = get_formatted_date(
            year=self.pick_up_year,
            month=self.pick_up_month,
            day=self.pick_up_day
        )

        drop_off_date = get_formatted_date(
            year=self.drop_off_year,
            month=self.drop_off_month,
            day=self.drop_off_day
        )

        pick_up_date_element = driver.find_element_by_id("pick-up-date-input")
        drop_off_date_element = driver.find_element_by_id("return-date-input")

        driver.execute_script('''
            var pick_up_elem = arguments[0];
            pick_up_elem.value = arguments[1];
            var drop_off_elem = arguments[2];
            drop_off_elem.value = arguments[3];
        ''', pick_up_date_element, pick_up_date, drop_off_date_element, drop_off_date)

        # Convert pick up time to 12h format.
        d = datetime.strptime(self.pick_up_time, "%H:%M")
        pickup_time = d.strftime("%I:%M %p")

        # Set pick up time.
        pickup_time_select = Select(driver.find_element_by_id("pick-up-time"))
        pickup_time_select.select_by_value(pickup_time)

        # Convert drop off time to 12h format.
        d = datetime.strptime(self.drop_off_time, "%H:%M")
        dropoff_time = d.strftime("%I:%M %p")

        # Set drop off time.
        dropoff_time_select = Select(driver.find_element_by_id("return-time"))
        dropoff_time_select.select_by_value(dropoff_time)

        search_button = driver.find_element_by_id("find-a-car")
        search_button.click()

        # ###############################
        # Open summary for debug only.
        # summary_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "header.banner.title-bar.drawer-toggle > h4")))
        # summary_element.click()
        # driver.get_screenshot_as_file("{0}_avis_cars_SUMMARY_navscraper.png".format(time.time()))
        # #############################


    def scrape_results(self, driver):
        ##
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #
        # html_source = driver.page_source

        logging.debug("## Scraping Data - Avis cars")

        car_results = []

        if self.WEBSITE_MODE == "mobile":

            car_results = self._scrape_mobile_results(
                driver=driver
            )

        elif self.WEBSITE_MODE == "default":

            car_results = self._scrape_default_results(
                driver=driver
            )

        return car_results


    def _scrape_mobile_results(self, driver):

        time.sleep(2)
        # driver.get_screenshot_as_file("{0}_avis_cars_SECTIONS_CLOSED_navscraper.png".format(time.time()))
        # Open all car sections.
        car_section_elements = driver.find_elements_by_css_selector(".car-selector > section > h3 > span:nth-of-type(1)")
        for car_section_element in car_section_elements:
            car_section_element.click()

        # driver.get_screenshot_as_file("{0}_avis_cars_SECTIONS_OPEN_navscraper.png".format(time.time()))

        # Get html source and start scraping routine.
        html_source = driver.page_source
        car_results = self._mobile_scraping_routine(page_source=html_source)

        return car_results


    def _mobile_scraping_routine(self, page_source):

        car_results = []

        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        car_sections = soup.select(".car-selector > section")

        for car_section in car_sections:
            # Determine the car items of the current section.
            car_items = car_section.select(".cars-list .car")

            for car_item in car_items:
                price_total_text = car_class = car_model = currency_total = \
                transmission = None

                # Determine the class of the car.
                car_class_element = car_item.select(".status-label")
                if len(car_class_element) > 0:
                    car_class = car_class_element[0].string.encode("utf-8").strip()

                # Determine the model of the car.
                car_model_element = car_item.select(".car-class-desc")
                if len(car_model_element) > 0:
                    car_model = car_model_element[0].string.encode("utf-8").strip()

                # Determine transmission.
                car_transmission_element = car_item.select(".transmission i")
                if len(car_transmission_element) > 0:
                    trans_class = car_transmission_element[0].get("class")
                    if "icon-automatic" in trans_class:
                        transmission = "automatic"
                    elif "icon-manual" in trans_class:
                        transmission = "manual"

                # Determine the price of the car.
                price_total_element = car_item.select("span.price")
                if len(price_total_element) > 0:
                    price_total_text = price_total_element[0].string.encode("utf-8").strip()

                # Determine the currency of the price.
                currency_total_element = car_item.select("span.currency")
                if len(currency_total_element) > 0:
                    currency_total = currency_total_element[0].string.encode("utf-8").strip()


                # Check if all information of the current car are available.
                if price_total_text is not None and car_class is not None and \
                    currency_total is not None and car_model is not None:
                    # Normalize the daily and total price for the current car.
                    price_total = float(price_total_text.replace(",", ".").replace("\xc2\xa0", "").strip())

                    currency_code_total = \
                        CurrencyConverter.get_currency_code_of_sign(currency_sign=currency_total)

                    # get the normalized total price from the api function
                    price_norm_total = CurrencyConverter.get_normalized_price(
                        price=price_total,
                        currency_code=currency_code_total
                    )

                    # Store all the received information in the result list.
                    car_results.append({
                        "car_model": car_model,
                        "transmission": transmission,
                        "car_class" : car_class,
                        "price_total": price_total,
                        "price_norm_total" : price_norm_total,
                        "currency" : currency_code_total,
                        "access_time": time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                        },
                    )

        return car_results


    def _scrape_default_results(self, driver):

        html_source = driver.page_source
        car_results = self._default_scraping_routine(page_source=html_source)
        return car_results


    def _default_scraping_routine(self, page_source):

        car_results = []

        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        car_items = soup.select("#vehPresentation .listOfVehicles .carView")

        for car_item in car_items:
            price_total_text = car_class = car_model = currency_total = \
            transmission = None

            # Determine the class of the car.
            car_class_element = car_item.select(".brandName h2")
            if len(car_class_element) > 0:
                car_class = car_class_element[0].string.encode("utf-8").strip()

            # Determine the model of the car.
            car_model_element = car_item.select(".brandName .moreDet")
            if len(car_model_element) > 0:
                car_model = list(car_model_element[0].strings)[1].replace("\t", "").replace("\n", " ").strip()
                # car_model += " - " + list(car_model_element[0].strings)[2].replace("\t", "").replace("\n", " ").strip()

            # Determine transmission.
            car_transmission_element = car_item.select(".featureList li:nth-of-type(2) p:nth-of-type(1)")
            if len(car_transmission_element) > 0:
                transmission = car_transmission_element[0].string.encode("utf-8").strip().lower()

            # Determine the price of the car.
            price_total_element = car_item.select(".colHalf_payLater .pricePD .price")
            if len(price_total_element) > 0:
                price_total_text = price_total_element[0].string.encode("utf-8").strip()

            # Determine the currency of the price.
            currency_total_element = car_item.select(".colHalf_payLater .pricePD span.setTop")
            if len(currency_total_element) > 0:
                currency_total = currency_total_element[0].string.encode("utf-8").strip()


            # Check if all information of the current car are available.
            if price_total_text is not None and car_class is not None and \
                currency_total is not None and car_model is not None:
                # Normalize the daily and total price for the current car.
                #

                price_total = float(price_total_text.replace(",", ".").replace("\xc2\xa0", "").strip())

                currency_code_total = \
                    CurrencyConverter.get_currency_code_of_sign(currency_sign=currency_total)

                # get the normalized total price from the api function
                price_norm_total = CurrencyConverter.get_normalized_price(
                    price=price_total,
                    currency_code=currency_code_total
                )

                # Store all the received information in the result list.
                car_results.append({
                    "car_model": car_model,
                    "car_class" : car_class,
                    "transmission" : transmission,
                    "price_total": price_total,
                    "price_norm_total" : price_norm_total,
                    "currency" : currency_code_total,
                    "access_time": time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    },
                )

        return car_results


def get_formatted_date(year, month, day):
    return time.strftime("%a %b %d, %Y", (int(year), int(month), int(day), 0,0,0,0,0,0))
