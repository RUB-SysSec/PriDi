#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   03.08.2016
#   @author Nicolai Wilkop and Henry Hosseini
#
#   @target_website www.orbitz.com
#

import sys
import logging
import re
import time
import bs4

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
    ENTRY_URI = "http://orbitz.com"
    PAGE_TYPE = "cars"

    def __init__(self):
        pass


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #   Navigates to the results listing.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {dict} search_parameters - Parameters for the search input form.
        #

        navigation_successful = True

        picking_up_location = search_parameters.get("picking_up")
        dropping_off_location = search_parameters.get("dropping_off")
        pick_up_day = int(search_parameters.get("pick_up_day"))
        pick_up_month = int(search_parameters.get("pick_up_month"))
        pick_up_year = int(search_parameters.get("pick_up_year"))
        drop_off_day = int(search_parameters.get("drop_off_day"))
        drop_off_month = int(search_parameters.get("drop_off_month"))
        drop_off_year = int(search_parameters.get("drop_off_year"))
        pick_up_time = search_parameters.get("pick_up_time")
        drop_off_time = search_parameters.get("drop_off_time")

        try:

            car_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#tab-car-tab')))
            car_tab.click()
            logging.debug("[ORBITZ CARS] Car tab clicked.")


            #
            # Set pickup date
            #
            pick_up_day_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "car-pickup-date")))
            #pick_up_day_field.clear()
            pick_up_day_field.click()
            time.sleep(1)
            # pick_up_date_string = "{month:02d}/{day:02d}/{year}".format(
                # day=pick_up_day,
                # month=pick_up_month,
                # year=pick_up_year
            # )
            # pick_up_day_field.send_keys(pick_up_date_string)

            #datepicker for pick up date
            pick_up_date_css_selector, pick_up_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                day=pick_up_day,
                month=pick_up_month,
                year=pick_up_year
            )

            datepicker_status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=pick_up_date_css_selector,
                next_month_css_selector=pick_up_next_month_css_selector
            )

            if not datepicker_status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                pick_up_date_css_selector
                ))

            logging.debug("[ORBITZ CARS] Pickup date selected.")

            time.sleep(2)

            #
            # Set dropoff date
            #

            drop_off_day_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "car-dropoff-date")))
            #drop_off_day_field.clear()
            drop_off_day_field.click()
            time.sleep(1)
            # drop_off_date_string = "{month:02d}/{day:02d}/{year}".format(
                # day=drop_off_day,
                # month=drop_off_month,
                # year=drop_off_year
            # )
            # drop_off_day_field.send_keys(drop_off_date_string)

            #datepicker
            drop_off_date_css_selector, drop_off_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                day=drop_off_day,
                month=drop_off_month,
                year=drop_off_year
            )
            datepicker_status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=drop_off_date_css_selector,
                next_month_css_selector=drop_off_next_month_css_selector
            )

            if not datepicker_status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                drop_off_date_css_selector
                ))
            time.sleep(1)
            logging.debug("[ORBITZ CARS] Dropoff date selected.")

            # #########
            # Fill out picking up and dropping off
            # #########
            picking_up_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "car-pickup")))
            picking_up_field.click()
            #picking_up_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,"id('tab-car-tab')/x:span[1]")))
            #picking_up_field.clear()
            time.sleep(1)
            picking_up_field.send_keys(picking_up_location)
            picking_up_field.send_keys(Keys.TAB)
            time.sleep(1)
            logging.debug("[ORBITZ CARS] Pickup location entered.")


            dropping_off_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "car-dropoff")))
            dropping_off_field.click()
            #dropping_off_field.clear()
            time.sleep(1)
            dropping_off_field.send_keys(dropping_off_location)
            logging.debug("[ORBITZ CARS] Dropoff location entered.")

            try:
                dropping_off_field.send_keys(Keys.ENTER)
                dropping_off_field.send_keys(Keys.ENTER)
                dropping_off_field.send_keys(Keys.ENTER)
            except:
                logging.exception("[ORBITZ CARS] Form submit Hack. Expected Exception")
            finally:
                logging.debug("[ORBITZ CARS] Form submitted.")

            # #########
            # Submit Search form
            # #########
            # search_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search-button")))
            # driver.save_screenshot('screenie_orbitz_submitted.png')
            # search_button.click()
            # logging.debug("[ORBITZ CARS] Submit button clicked.")

            # Wait for results.
            Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector="#search-results .listing-wrapper",
                timeout=60
            )

        except selenium.common.exceptions.TimeoutException:

            logging.exception("TimeoutException in Navigation routine.")
            logging.debug("[ORBITZ CARS] Box or Button not found")
            # driver.save_screenshot('screenie_orbitz_lookup_error.png')
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

            logging.debug("## Navigating finished - Orbitz Cars")


        return navigation_successful


    def scrape_results(self, driver):
        ##
        #   Extract result information and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        logging.debug("## Scraping Data - orbitz cars")
        orbitz_car_results = []
        page_counter = 0
        result_pages_limit = 20

        while True:

            page_counter += 1

            # Get html source and call scraping routine.
            pageSource = driver.page_source
            cars_results_part = self._scraping_routine(page_source=pageSource)
            orbitz_car_results.extend(cars_results_part)

            if len(orbitz_car_results) > 1:
                second_car_model = orbitz_car_results[1]["car_model"]
            else:
                second_car_model = ""

            try:
                # Pagination: Next Page
                next_page_element = driver.find_element_by_css_selector("button.pagination-next")

                # Click on next page link
                next_page_element.click()

                try:
                    # Wait for results.
                    Navigation.wait_for_text_to_be_not_present_in_element(
                        driver=driver,
                        element_css_selector="#search-results .listing-wrapper:nth-of-type(2) .car-model",
                        old_text=second_car_model
                    )

                except selenium.common.exceptions.TimeoutException:
                    # If no results were found.
                    # End loop and return the current results.
                    break

            except selenium.common.exceptions.NoSuchElementException:
                # If no next page link was not found.
                # End loop and return the current results.
                break

            except:
                # log unexpected errors while scraping
                logging.exception("Unexpected error:")

            if page_counter >= result_pages_limit:
                # If the limit is reached.
                # End loop and return the current results.
                break


        return orbitz_car_results


    def _scraping_routine(self, page_source):

        orbitz_car_results = []

        bsObj = bs4.BeautifulSoup(page_source, 'html.parser')

        hotellist_items = bsObj.select("#search-results .listing-wrapper")

        for div in hotellist_items:
            price_daily_text = price_total_text = car_class = company_name = \
            car_model = None

            # Determine the daily price of the current car.
            price_daily_element = div.find_all("div", {"class":"full-price"})
            if len(price_daily_element) > 0:
                price_daily_text = self._encode_and_strip(price_daily_element[0])

            # Determine the total price of the current car.
            price_total_element = div.find_all("div", {"class":"total"})
            if len(price_total_element) > 0:
                # TODO split "total" string from price.
                price_total_text = self._encode_and_strip(price_total_element[0])

            # Determine the class of the car.
            car_class_element = div.select("div.fullName span")
            if len(car_class_element) > 0:
                car_class = self._encode_and_strip(car_class_element[0])

            # Determine the company name of the current car.
            company_name_element = div.select("div.vendor-image-box img")
            if len(company_name_element) > 0:
                # TODO Test whether the alt content is found or not.
                company_name = self._encode_and_strip(company_name_element[0]["alt"])

            # Determine the model of the current car.
            car_model_element = div.select(".car-model")
            if len(car_model_element) > 0:
                car_model = self._encode_and_strip(car_model_element[0])


            # Check if all information of the current car are available.
            if price_daily_text is not None and price_total_text is not None and \
                car_class is not None and company_name is not None and car_model is not None:

                # Normalize the daily and total price for the current car.
                #
                # split price and currency of daily price.
                price_daily, currency_daily = \
                    CurrencyConverter.split_price_and_currency(price_text=price_daily_text)

                currency_code_daily = \
                    CurrencyConverter.get_currency_code_of_sign(currency_sign=currency_daily)

                # get the normalized daily price from the api function
                price_norm_daily = CurrencyConverter.get_normalized_price(
                    price=price_daily,
                    currency_code=currency_code_daily
                )

                # split price and currency of total price.
                price_total, currency_total = \
                    CurrencyConverter.split_price_and_currency(price_text=price_total_text)

                currency_code_total = \
                    CurrencyConverter.get_currency_code_of_sign(currency_sign=currency_total)

                # get the normalized total price from the api function
                price_norm_total = CurrencyConverter.get_normalized_price(
                    price=price_total,
                    currency_code=currency_code_total
                )

                # Store all the received information in the result list.
                orbitz_car_results.append({
                    "company_name": company_name,
                    "car_model": car_model,
                    "car_class" : car_class,
                    "price_daily": price_daily,
                    "price_norm_daily" : price_norm_daily,
                    "price_total": price_total,
                    "price_norm_total" : price_norm_total,
                    "currency" : currency_code_daily,
                    "access_time": time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    },
                )

        return orbitz_car_results

    def _get_datepicker_css_selectors(self, day, month, year):
        ##
        #   Generates the CSS selector of the date and the CSS selector for the
        #   next-month button.
        #
        #   @param {string} day - Day of the date to select.
        #   @param {string} month - Month of the date to select.
        #   @param {string} year - Year of the date to select.
        #
        #   @return {string}, {string}
        #

        date_attributes = "[data-day=\"{day}\"][data-month=\"{month}\"][data-year=\"{year}\"]".format(
            day=int(day),
            month=int(month)-1,
            year=int(year)
        )

        date_css_selector = ".datepicker-cal .datepicker-cal-date{date}".format(date=date_attributes)

        next_month_css_selector = ".datepicker-cal .datepicker-next"

        return date_css_selector, next_month_css_selector


    def _splitter(self, raw_total_price):
        regx = re.compile(r'\d+')
        # regx = re.compile(r'[^0-9][0-9]{2}[^0-9]')
        for item in raw_total_price:
            temp = item.split(" ")
            for part in temp:
                digit = regx.findall(part)
                if len(digit) > 0:
                    return digit[0]


    def _encode_and_strip(self,element):
       element = element.string.encode("utf-8").strip()
       return element


