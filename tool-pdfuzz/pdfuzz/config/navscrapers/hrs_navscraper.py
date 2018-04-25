#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   29.10.2015
#   @author Nicolai Wilkop
#
#   @target_website hrs.com
#

import sys
import logging
import time
import bs4
import re

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import selenium

import pdfuzz.config.navscrapers.api.currency_converter as CurrencyConverter
import pdfuzz.config.navscrapers.api.navigation as Navigation
import pdfuzz.common.exceptions as PDFuzzExceptions
# import pdfuzz.config.config as cfg


class NavScraper:
    ##
    #
    #
    ENTRY_URI = "http://hrs.com"
    # PAGE_TYPE = cfg.PAGE_TYPES.HOTELS
    PAGE_TYPE = "hotels"

    def __init__(self):
        ##
        #
        #

        # Time in seconds until the results are loaded.
        # This value is used to individualize the waiting for new results.
        self.results_waiting_time = 0


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #   Navigates to the hotel listing.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        self.travel_target           = search_parameters.get("travel_target", "")
        self.number_of_adults        = search_parameters.get("number_of_adults", "0")
        self.number_of_single_rooms  = search_parameters.get("number_of_single_rooms", "0")
        self.number_of_double_rooms  = search_parameters.get("number_of_double_rooms", "0")
        self.check_in_year           = search_parameters.get("check_in_year", "")
        self.check_in_month          = search_parameters.get("check_in_month", "")
        self.check_in_day            = search_parameters.get("check_in_day", "")
        self.check_out_year          = search_parameters.get("check_out_year", "")
        self.check_out_month         = search_parameters.get("check_out_month", "")
        self.check_out_day           = search_parameters.get("check_out_day", "")


        navigation_successful   = True
        self.WEBSITE_MODE       = "default"
        # driver.get_screenshot_as_file("{0}_LOADED_hrs_navscraper.png".format(time.time()))

        try:

            try:
                # Try default mode
                travel_target_element = driver.find_element_by_id("destiny")
                self.WEBSITE_MODE     = "default"

            except selenium.common.exceptions.NoSuchElementException:
                # Touch mode
                # travel_target_element = driver.find_element_by_id("suggestTarget")
                self.WEBSITE_MODE     = "touch"


            if self.WEBSITE_MODE == "default":
                # Use default mode to fill out the search input form.
                navigation_successful = self._use_default_mode(driver=driver)

            elif self.WEBSITE_MODE == "touch":
                # Use touch mode to fill out the search input form.
                navigation_successful = self._use_touch_mode(driver=driver)

            else:
                logging.warning("Unhandled website mode.")
                return False


        except selenium.common.exceptions.TimeoutException:

            # If no results were found.
            logging.debug("## Element not found - HRS")
            logging.warning("Results not found!")

            # Set return value to false.
            navigation_successful = False

        except:
            # Log unexpected errors while navigating.
            exc_type, exc_value = sys.exc_info()[:2]
            print("Unexpected error: {type} <msg '{msg}'>".format(
                type=exc_type, msg=exc_value))
            logging.exception("Unexpected error:")

            navigation_successful = False

        finally:

            logging.debug("## Navigating finished - HRS")

        return navigation_successful


    def _use_default_mode(self, driver):

        logging.debug("Use default mode.")

        # set the needed rooms and the number of adults.
        self._set_rooms_and_adults_number(driver=driver)

        try:
            # Set the check-in and check-out date.
            self._set_travel_dates(driver=driver)

        except PDFuzzExceptions.DateNotFoundException:
            logging.exception("Error while setting the dates.")
            return False

        # Set the travel destination.
        travel_target_element = driver.find_element_by_id("destiny")
        travel_target_element.clear()
        travel_target_element.send_keys(self.travel_target)

        # submit the search input form.
        submit_button_element = driver.find_element_by_name("submitBasicSearch")
        submit_button_element.click()

        logging.debug("Search form sent.")

        # Try to click the target destination concretion.
        self._handle_default_target_concretion(driver=driver)

        # Measure waiting time.
        start_waiting = time.time()

        # Wait for result element.
        Navigation.wait_for_the_presence_of_element(
            driver=driver,
            element_css_selector="#containerAllHotels > .hotelTeaserContainer",
            timeout=120
        )

        # Check the time after results are loaded and calculate the duration.
        end_waiting = time.time()
        self.results_waiting_time = end_waiting - start_waiting

        logging.debug("## Element found - HRS")

        # Some extra time to load the results.
        logging.debug("## Sleep 5 sec")
        time.sleep(5)

        return True

    def _handle_default_target_concretion(self, driver):

        try:
            # Try to find the first link of the concretion listing.
            selector = "#content .box > p > a.link:first-of-type"
            element = Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector=selector,
                timeout=20
            )
            element.click()
            logging.debug("Clicked default target concretion!")

        except:
            logging.exception("Default concretion not found!")


    def _set_rooms_and_adults_number(self, driver):

        # Handle different cases of search-input form.
        # Find out which input form is available.
        try:
            # Look for select.
            person_room_select = Select(driver.find_element_by_id("roomSelector"))
            # Select advanced options to enable the input forms for rooms
            # and adults.
            person_room_select.select_by_value("4") # fixed value: 01.01.2016

        except selenium.common.exceptions.NoSuchElementException:
            pass

        finally:
            # Get input forms for rooms and adults.
            single_room_element   = driver.find_element_by_id("singleRooms")
            double_room_element   = driver.find_element_by_id("doubleRooms")
            number_adults_element = driver.find_element_by_id("adults")

        single_room_element.clear()
        single_room_element.send_keys(self.number_of_single_rooms)
        double_room_element.clear()
        double_room_element.send_keys(self.number_of_double_rooms)
        number_adults_element.clear()
        number_adults_element.send_keys(self.number_of_adults)


    def _set_travel_dates(self, driver):

        travel_start_element = driver.find_element_by_id("start_stayPeriod")
        travel_end_element   = driver.find_element_by_id("end_stayPeriod")

        cin_date_css_selector, cin_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                day=self.check_in_day,
                month=self.check_in_month,
                year=self.check_in_year
            )

        cout_date_css_selector, cout_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                day=self.check_out_day,
                month=self.check_out_month,
                year=self.check_out_year
            )

        travel_start_element.click()
        datepicker_status = Navigation.set_date_in_basic_datepicker(
            driver=driver,
            date_css_selector=cin_date_css_selector,
            next_month_css_selector=cin_next_month_css_selector
        )

        if not datepicker_status:
            raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                cin_date_css_selector
            ))

        logging.debug("[HRS] Checkin date selected.")

        time.sleep(2)

        travel_end_element.click()
        datepicker_status = Navigation.set_date_in_basic_datepicker(
            driver=driver,
            date_css_selector=cout_date_css_selector,
            next_month_css_selector=cout_next_month_css_selector
        )

        if not datepicker_status:
            raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                cout_date_css_selector
            ))

        logging.debug("[HRS] Checkout date selected.")


    def _use_touch_mode(self, driver):

        logging.debug("Use touch mode.")

        self._handle_error_message(driver=driver)

        try:
            # Set check-in and check-out date.
            self._set_travel_dates_in_touch_mode(driver=driver)

        except PDFuzzExceptions.DateNotFoundException:
            logging.exception("Error while setting the dates.")
            return False

        # Set the number of single and double rooms.
        self._set_rooms_number_in_touch_mode(driver=driver)

        # Set the travel target.
        travel_target_element = driver.find_element_by_id("suggestTarget")
        travel_target_element.clear()
        travel_target_element.send_keys(self.travel_target)
        # travel_target_element.send_keys(Keys.ENTER)

        # Submit the search input form.
        travel_target_element.submit()

        # driver.get_screenshot_as_file("{0}_TOUCH_BEFORE_SUBMIT_hrs_navscraper.png".format(time.time()))

        try:
            # If the form is not submitted by the submit of the travel target
            # input element, try to submit the form via the search button.
            # search_button = driver.find_element_by_css_selector("#searchSubmit\\:id")
            search_button = driver.find_element_by_css_selector("input[type=\"submit\"]")
            driver.execute_script('''
                var button = arguments[0];
                button.click();
            ''', search_button)
        except:
            logging.exception("Search button error.")

        # driver.get_screenshot_as_file("{0}_TOUCH_AFTER_SUBMIT_hrs_navscraper.png".format(time.time()))

        self._handle_touch_target_concretion(driver=driver)

        # Measure waiting time.
        start_waiting = time.time()

        # Wait for result element.
        Navigation.wait_for_the_presence_of_element(
            driver=driver,
            element_css_selector="#resultList .listItem",
            timeout=60
        )

        # Check the time after results are loaded and calculate the duration.
        end_waiting = time.time()
        self.results_waiting_time = end_waiting - start_waiting

        logging.debug("## Element found - HRS")

        return True


    def _handle_touch_target_concretion(self, driver):

        try:
            # Try to find the first link of the concretion listing.
            selector = "#content form#j_id_5r > a:first-of-type div"
            element = Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector=selector,
                timeout=20
            )
            driver.execute_script('''
                var button = arguments[0];
                button.click();
            ''', element)
            # element.click()
            logging.debug("Clicked touch target concretion!")

        except:
            logging.exception("Touch concretion not found!")


    def _handle_error_message(self, driver):

        try:

            # Try to click the error away.
            ok_error = driver.find_element_by_css_selector("#feedback .btnGrey > div")
            ok_error.click()

            logging.debug("Error message clicked away.")

        except:
            logging.exception("Error while handling error message.")


    def _manipulate_hidden_date_inputs_touch_mode(self, driver):

        # Determine the hidden input fields
        check_in_element = driver.find_element_by_css_selector("#sfrom")
        check_out_element = driver.find_element_by_css_selector("#sto")

        # Create date strings.
        check_in_date = "{year}-{month:02d}-{day:02d}".format(
            year=int(self.check_in_year),
            month=int(self.check_in_month),
            day=int(self.check_in_day)
        )
        check_out_date = "{year}-{month:02d}-{day:02d}".format(
            year=int(self.check_out_year),
            month=int(self.check_out_month),
            day=int(self.check_out_day)
        )

        # Execute JavaScript code to manipulate the hidden input fields for
        # the checkin and checkout date.
        driver.execute_script('''
            var check_in_elem = arguments[0];
            check_in_elem.value = arguments[1];
            var check_out_elem = arguments[2];
            check_out_elem.value = arguments[3];
        ''', check_in_element, check_in_date, check_out_element, check_out_date)

        logging.debug("Dates manipulated via hidden input fields!")


    def _set_travel_dates_in_touch_mode(self, driver):

        # Open datepicker.
        open_datepicker_element = driver.find_element_by_css_selector("#cal_trigger")
        open_datepicker_element.click()

        time.sleep(3)

        cin_date_css_selector, cin_next_month_css_selector = \
            self._get_touch_datepicker_css_selectors(
                day=self.check_in_day,
                month=self.check_in_month,
                year=self.check_in_year
            )

        cout_date_css_selector, cout_next_month_css_selector = \
            self._get_touch_datepicker_css_selectors(
                day=self.check_out_day,
                month=self.check_out_month,
                year=self.check_out_year
            )

        try:

            # Select check-in date.
            datepicker_status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cin_date_css_selector,
                next_month_css_selector=cin_next_month_css_selector
            )

            if not datepicker_status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cin_date_css_selector
                ))

            logging.debug("[HRS] Checkin date selected.")

            time.sleep(1)

            # Select check-out date.
            datepicker_status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cout_date_css_selector,
                next_month_css_selector=cout_next_month_css_selector
            )

            if not datepicker_status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cout_date_css_selector
                ))

            logging.debug("[HRS] Checkout date selected.")

            # Press ok in the datepicker.
            datepicker_ok_element = driver.find_element_by_id("calOK")
            datepicker_ok_element.click()

            time.sleep(2)

        except PDFuzzExceptions.DateNotFoundException:
            # If the datepicker fails. Try to manipulate the hidden input fields
            # to set the travel dates.
            logging.debug("Datepicker failed. Try hidden field manipulation.")
            self._manipulate_hidden_date_inputs_touch_mode(driver=driver)


    def _set_rooms_number_in_touch_mode(self, driver):

        single_room_minus_element = driver.find_element_by_css_selector("#sr .minus")
        single_room_plus_element  = driver.find_element_by_css_selector("#sr .plus")
        double_room_minus_element = driver.find_element_by_css_selector("#dr .minus")
        double_room_plus_element  = driver.find_element_by_css_selector("#dr .plus")

        # Delete default single rooms.
        single_room_minus_element.click()
        time.sleep(1)

        # Set the number of single rooms via plus button.
        for _ in range(int(self.number_of_single_rooms)):
            single_room_plus_element.click()
            time.sleep(0.6)

        # Set the number of double rooms via plus button.
        for _ in range(int(self.number_of_double_rooms)):
            double_room_plus_element.click()
            time.sleep(0.6)


    def scrape_results(self, driver):
        ##
        #   Extract hotel names and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        if self.WEBSITE_MODE == "default":
            # Use default scraping routine.
            return self._default_scraper(driver=driver)

        elif self.WEBSITE_MODE == "touch":
            # Use scraping routine for touch version of HRS.
            return self._touch_scraper(driver=driver)

        else:
            # Log error and return empty result list.
            logging.warning("Unhandled website mode!")
            return []


    def _default_scraper(self, driver):

        driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")

        # Calculate waiting time. Wait for complete result list.
        waiting_seconds = 5 + self.results_waiting_time
        time.sleep(waiting_seconds)

        logging.debug("Wait {seconds} sec for complete result list.".format(
            seconds=waiting_seconds
        ))

        html_source = driver.page_source

        logging.debug("## Scraping Data")
        return self._scraping_routine(page_source=html_source)


    def _scraping_routine(self, page_source):

        hotel_results = []

        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        hotellist_items = soup.select("div#containerAllHotels > .hotelTeaserContainer")

        for div in hotellist_items:
            hotelname = price = currency_code = price_norm = \
            rating_value = rating_unit = None

            # Extract hotel name.
            a_hotelname = div.select(".hotelname > a:nth-of-type(1)")
            if len(a_hotelname) > 0:
                hotelname = a_hotelname[0].string.encode("utf-8").strip()

            # Extract rating information (stars)
            stars_element = div.select(".hotelname > span:nth-of-type(1)")
            if len(stars_element) > 0:
                stars_element_classes = stars_element[0].get("class")
                stars_class = stars_element_classes[0]
                rating_value = float(stars_class[5:])
                rating_unit = "stars"
            else:
                rating_value = 0.0
                rating_unit = None

            # Extract price of hotel.
            for strong_price in div.select(".priceContainer > .standardPrice > strong"):
                contents = strong_price.contents

                big_money = contents[0].encode("utf-8").replace("\xc2\xa0", "").replace(".", "").strip()
                small_money = strong_price.find_all("sup")[0].string.encode("utf-8").strip()
                if len(small_money) < 2:
                    small_money = "00"

                # Remove all non-numeric values from big_money
                big_money = re.sub("[^0-9]", "", big_money)

                price = float("{0}.{1}".format(big_money, small_money))

                span_currency = strong_price.find_all("span")
                if len(span_currency) > 0:
                    currency = span_currency[0].string.encode("utf-8").strip()
                else:
                    currency = contents[2].encode("utf-8").strip()

                currency_code = CurrencyConverter.get_currency_code_of_sign(currency)

                # get the normalized price from the api function
                price_norm = CurrencyConverter.get_normalized_price(
                    price=price,
                    currency_code=currency_code
                )


            if hotelname != None and price != None:

                # this information is not available on the website.
                # it seems to be always the price per night
                number_of_nights = 1

                hotel_results.append({
                    "name" : hotelname,
                    "price" : price,
                    "currency" : currency_code,
                    "price_norm" : price_norm,
                    "number_of_nights" : number_of_nights,
                    "rating_value" : rating_value,
                    "rating_unit" : rating_unit,
                    "access_time" : time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                })

        return hotel_results


    def _touch_scraper(self, driver):

        hotel_results   = []
        page_counter    = 0
        page_limit      = 20

        # driver.get_screenshot_as_file("{0}_TOUCH_RESULTS_hrs_navscraper.png".format(time.time()))

        waiting_seconds = float(2.0 + self.results_waiting_time)
        while True:

            page_counter += 1

            # Scroll down in the page element.
            driver.execute_script('''
                var page_element = document.getElementById("page");
                page_element.scrollTop = page_element.scrollHeight;
            ''')


            time.sleep(waiting_seconds)
            logging.debug("Waited {seconds} sec for more results.".format(
                seconds=waiting_seconds
            ))

            html_source = driver.page_source
            hotel_results_tmp = self._touch_scraping_routine(page_source=html_source)

            if len(hotel_results_tmp) > len(hotel_results):
                # Make a full copy of the new list and save it as the result list.
                hotel_results = list(hotel_results_tmp)

                if page_counter >= page_limit:
                    break

            else:
                break

        return hotel_results


    def _touch_scraping_routine(self, page_source):

        hotel_results = []

        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        hotellist_items = soup.select("#resultList .listItem")

        for div in hotellist_items:
            hotelname = price = currency_code = price_norm = None

            # Extract hotel name.
            div_name = div.select(".hotelData > .labeled")
            if len(div_name) > 0:
                hotelname = div_name[0].string.encode("utf-8").strip()

            # Extract rating information (stars)
            stars_element = div.select(".hotelData .smaller .stars")
            if len(stars_element) > 0:
                stars_element_classes = stars_element[0].get("class")
                # Search the sX class which indicates the number of stars.
                for star_class in stars_element_classes:
                    if star_class[-1].isdigit():
                        rating_value = float(star_class[1:])
                rating_unit = "stars"

            else:
                rating_value = 0.0
                rating_unit = None

            # Extract hotel price.
            span_price = div.select(".hotelData > .priceInfo span.price")
            if len(span_price) > 0:
                price_text = span_price[0].string.encode("utf-8").strip()

                # Extract the price and currency from the price string.
                price, currency = \
                    CurrencyConverter.split_price_and_currency(price_text=price_text)

                # Get the currency code for the extracted currency.
                currency_code = \
                    CurrencyConverter.get_currency_code_of_sign(currency_sign=currency)

                # get the normalized price from the api function
                price_norm = CurrencyConverter.get_normalized_price(
                    price=price,
                    currency_code=currency_code
                )


            if hotelname != None and price != None and price_norm != None:

                # this information is not available on the website.
                # it seems to be always the price per night
                number_of_nights = 1

                hotel_results.append({
                    "name" : hotelname,
                    "price" : price,
                    "currency" : currency_code,
                    "price_norm" : price_norm,
                    "number_of_nights" : number_of_nights,
                    "rating_value" : rating_value,
                    "rating_unit" : rating_unit,
                    "access_time" : time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                })

        return hotel_results


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

        href_val = "javascript:sendDate({year},{month},{day}, ankerEl)".format(
            year=int(year),
            month=int(month)-1,
            day=int(day)
        )

        date_css_selector = "#calTab #calBody td a[href='{href_val}']".format(href_val=href_val)

        next_month_css_selector = "#calTab #calHead #nextM a"

        return date_css_selector, next_month_css_selector


    def _get_touch_datepicker_css_selectors(self, day, month, year):
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

        date_id = "d_{month}_{year}-{month:02d}-{day:02d}".format(
            day=int(day),
            month=int(month),
            year=int(year)
        )

        date_css_selector = ".calWeeks #{date_id}".format(date_id=date_id)

        next_month_css_selector = None

        return date_css_selector, next_month_css_selector

