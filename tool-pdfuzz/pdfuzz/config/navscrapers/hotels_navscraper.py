#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   02.11.2015
#   @author Nicolai Wilkop
#
#   @target_website hotels.com
#

import sys
import logging
import re
import time
import bs4

from selenium.webdriver.support.ui import Select
import selenium

import pdfuzz.config.navscrapers.api.currency_converter as CurrencyConverter
import pdfuzz.config.navscrapers.api.navigation as Navigation
# import pdfuzz.config.config as cfg


class NavScraper:
    ##
    #
    #
    ENTRY_URI = "http://hotels.com"
    # PAGE_TYPE = cfg.PAGE_TYPES.HOTELS
    PAGE_TYPE = "hotels"

    def __init__(self):
        ##
        #
        #   @param {webdriver} driver - Selenium webdriver object which is
        #   connected to the PhantomJS WebDriver server.
        #
        pass


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #   Navigates to the hotel listing.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        navigation_successful = True
        # driver.get_screenshot_as_file("{0}_LOADED_hotels_navscraper.png".format(time.time()))

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


        # check if there is an overlay visible and handle it propperly.
        self._close_download_app_overlay(driver=driver)
        self._close_general_overlay(driver=driver)

        try:

            # Set the dates for check-in and check-out
            self._set_travel_dates(driver=driver)

            # driver.get_screenshot_as_file("{0}_CHECK_OUT_DATE_SELECTED_hotels_navscraper.png".format(time.time()))

            # Select rooms and number of persons.
            self._set_rooms_and_adults_number(driver=driver)

            # Set the travel destination.
            travel_target_element = driver.find_element_by_id("qf-0q-destination")
            travel_target_element.clear()
            travel_target_element.send_keys(self.travel_target)

            # driver.get_screenshot_as_file("{0}_FILLED_FORM_hotels_navscraper.png".format(time.time()))

            # Submit the search input form.
            travel_target_element.submit()

            # Wait for results.
            Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector="div#listings > ol.listings > li.hotel",
                timeout=60
            )

            # driver.get_screenshot_as_file("{0}_RESULTS_hotels_navscraper.png".format(time.time()))

        except selenium.common.exceptions.TimeoutException:

            # If no results were found.
            # driver.get_screenshot_as_file("hotels_ERROR_navscraper.png")
            logging.warning("Results not found! - hotels")
            # logging.debug(driver.page_source)

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

            logging.debug("## Navigating finished - hotels")

        return navigation_successful


    def _close_general_overlay(self, driver):

        try:
            logging.debug("## Find overlay")
            # Check for overlay
            element = Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector="button.widget-overlay-close",
                timeout=5
            )
            # element = driver.find_element_by_css_selector("button.widget-overlay-close")

            # Close overlay
            element.click()
            logging.debug("## Overlay closed")
            time.sleep(2)
            # driver.get_screenshot_as_file("hotels_OVERLAY_CLOSED_navscraper.png".format(time.time()))

        # except selenium.common.exceptions.NoSuchElementException:
        except selenium.common.exceptions.TimeoutException:
            logging.debug("## No overlay")


    def _close_download_app_overlay(self, driver):

        try:
            logging.debug("## Find Download App Overlay")
            # Check for overlay
            element = Navigation.wait_for_the_presence_of_element(
                driver=driver,
                element_css_selector="#download-app-overlay button.cancel-button",
                timeout=5
            )
            # element = driver.find_element_by_css_selector("button.widget-overlay-close")

            # Close overlay
            element.click()
            logging.debug("## Download App Overlay Closed")
            time.sleep(2)
            # driver.get_screenshot_as_file("hotels_OVERLAY_CLOSED_navscraper.png".format(time.time()))

        # except selenium.common.exceptions.NoSuchElementException:
        except selenium.common.exceptions.TimeoutException:
            logging.debug("## No Download App Overlay")


    def _set_travel_dates(self, driver):

        travel_start_element = driver.find_element_by_id("qf-0q-localised-check-in")
        travel_end_element   = driver.find_element_by_id("qf-0q-localised-check-out")

        # Little delay for the input form.
        time.sleep(2)

        cin_date_css_selector, cin_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                datepicker_class="div.widget-daterange-start",
                day=self.check_in_day,
                month=self.check_in_month,
                year=self.check_in_year
            )

        cout_date_css_selector, cout_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                datepicker_class="div.widget-daterange-end",
                day=self.check_out_day,
                month=self.check_out_month,
                year=self.check_out_year
            )

        # fill out the form.
        travel_start_element.click()
        # driver.get_screenshot_as_file("{0}_CHECK_IN_CLICKED_hotels_navscraper.png".format(time.time()))

        # Try to use the datepicker to select the check-in date.
        datepicker_status = Navigation.set_date_in_basic_datepicker(
            driver=driver,
            date_css_selector=cin_date_css_selector,
            next_month_css_selector=cin_next_month_css_selector
        )

        if not datepicker_status:
            # if no datepicker was found, try to input the date.
            travel_start_element.send_keys("{year}-{month}-{day}".format(
                year=self.check_in_year,
                month=self.check_in_month,
                day=self.check_in_day
            ))

        # Little delay for the input form.
        time.sleep(2)

        # driver.get_screenshot_as_file("{0}_CHECK_IN_DATE_SELECTED_hotels_navscraper.png".format(time.time()))

        travel_end_element.click()
        # driver.get_screenshot_as_file("{0}_CHECK_OUT_CLICKED_hotels_navscraper.png".format(time.time()))

        datepicker_status = Navigation.set_date_in_basic_datepicker(
            driver=driver,
            date_css_selector=cout_date_css_selector,
            next_month_css_selector=cout_next_month_css_selector
        )

        if not datepicker_status:
            # if no datepicker was found, try to input the date.
            travel_end_element.send_keys("{year}-{month}-{day}".format(
                year=self.check_out_year,
                month=self.check_out_month,
                day=self.check_out_day
            ))

        # Little delay for the input form.
        time.sleep(2)


    def _set_rooms_and_adults_number(self, driver):

        # Select rooms and number of persons.
        # Select more options to setup the rooms separatly.
        # logging.debug("driver.find_element_by_id(\"qf-0q-compact-occupancy\")")
        room_select = Select(driver.find_element_by_id("qf-0q-compact-occupancy"))
        room_select.select_by_index(2)

        # Calculate the total number of rooms
        number_of_rooms = int(self.number_of_double_rooms) + int(self.number_of_single_rooms)
        # Determine the select box to choose the number of rooms
        number_of_rooms_select = Select(driver.find_element_by_id("qf-0q-rooms"))
        # Set the number of rooms
        number_of_rooms_select.select_by_index(number_of_rooms - 1)

        room_index = [0]
        # Setup all single rooms.
        self._set_rooms_with_size(
            driver=driver,
            room_index=room_index,
            number_of_rooms=int(self.number_of_single_rooms),
            number_of_adults_per_room=1
        )

        # Setup all double rooms.
        self._set_rooms_with_size(
            driver=driver,
            room_index=room_index,
            number_of_rooms=int(self.number_of_double_rooms),
            number_of_adults_per_room=2
        )


    def scrape_results(self, driver):
        ##
        #   Extract hotel names and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        # print("## Taking Screenshot")
        # driver.get_screenshot_as_file("{0}_hotels_navscraper.png".format(time.time()))
        
        try:
            # Check if the pagination bar is available.
            driver.find_element_by_css_selector("footer > div.pagination a")
            logging.debug("[*] Pagination Scraper - hotels")
            scraping_function = self._scrape_results_pagination

        except:
            # If there is no pagination bar, scrape by scrolling.
            logging.debug("[*] Scrolling Scraper - hotels")
            scraping_function = self._scrape_results_scrolling

        logging.debug("## Scraping Data - hotels")
        return scraping_function(driver=driver)


    def _scrape_results_scrolling(self, driver):

        hotel_results = []
        page_counter = 0
        result_pages_limit = 20

        last_page_length = 0

        while True:

            page_counter += 1

            html_source = driver.page_source
            hotel_results_part = self._scraping_routine(page_source=html_source)

            # Take full page as final result, because if new results are loaded
            # by scrolling down, the site is extended by scrolling down.
            hotel_results = list(hotel_results_part)

            try:
                # Scroll down.
                logging.debug("[DEBUG] Scroll down")
                driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
                time.sleep(5)

            except:
                # log unexpected errors while scraping
                logging.exception("Unexpected error:")


            if page_counter >= result_pages_limit or len(hotel_results) <= last_page_length:
                # If the limit is reached.
                # End loop and return the current results.
                break

            else:
                # update the length of the last page.
                last_page_length = len(hotel_results)

        return hotel_results


    def _scrape_results_pagination(self, driver):

        hotel_results = []
        extend_results_by_pagination = True
        page_counter = 0
        result_pages_limit = 20

        while True:

            page_counter += 1

            html_source = driver.page_source
            hotel_results_part = self._scraping_routine(page_source=html_source)

            if extend_results_by_pagination:
                # extend results if pagination is available, because new results
                # are loaded site by site.
                hotel_results.extend(hotel_results_part)

            else:
                # Take full page as final result, because if new results are loaded
                # by scrolling down, the site is extended by scrolling down.
                hotel_results = hotel_results_part


            try:

                # Futher results are loaded in two different ways.
                # First: By pagination link.
                # Second: By scrolling down.
                # One of this cases will appear and we need to determine which
                # of them is available.
                try:
                    if not extend_results_by_pagination:
                        # Speed up.
                        raise selenium.common.exceptions.ElementNotVisibleException()

                    # First case:
                    # Pagination: Next Page
                    logging.debug("[DEBUG] Pagination")
                    next_page_element = driver.find_element_by_css_selector("footer > div.pagination a")

                    # Click on next page link
                    next_page_element.click()

                    # Extend results if this pagination variant is present.
                    extend_results_by_pagination = True

                except selenium.common.exceptions.ElementNotVisibleException:

                    # Second case:
                    # If pagination is not visible.
                    # Scroll down.
                    logging.debug("[DEBUG] Scroll down")
                    driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")

                    # Replace results if the results page is extending content.
                    extend_results_by_pagination = False


                try:
                    # Wait for results.
                    logging.debug("[DEBUG] Wait for new results")

                    if extend_results_by_pagination:
                        logging.debug("[DEBUG] First hotel name: {}".format(hotel_results_part[0]["name"]))
                        Navigation.wait_for_text_to_be_not_present_in_element(
                            driver=driver,
                            element_css_selector="div#listings > ol.listings > li.hotel:first-of-type h3.p-name a",
                            old_text=hotel_results_part[0]["name"]
                        )

                    else:
                        logging.debug("[DEBUG] Last hotel name: {}".format(hotel_results_part[-1]["name"]))
                        Navigation.wait_for_text_to_be_not_present_in_element(
                            driver=driver,
                            element_css_selector="div#listings > ol.listings > li.hotel:nth-last-of-type(2) h3.p-name a",
                            old_text=hotel_results_part[-1]["name"]
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
                # exc_type, exc_value = sys.exc_info()[:2]
                # print("Unexpected error: {}".format(sys.exc_info()[0]))
                logging.exception("Unexpected error:")

            if page_counter >= result_pages_limit:
                # If the limit is reached.
                # End loop and return the current results.
                break

        return hotel_results


    def _scraping_routine(self, page_source):
        ##
        #   ...
        #
        #   @param {string} page_source - ...
        #
        #   @return {list}
        #

        regex_price_per_nights = re.compile("[0-9]+")

        hotel_results = []
        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        # Extract info about the search values. For debug.
        div_search_info = soup.select(".dates-occupancy")

        search_dates = div_search_info[0].select(".search-dates")[0].string.encode("utf-8").strip()
        search_nights = div_search_info[0].select(".search-nights")[0].string.encode("utf-8").strip()
        search_rooms = div_search_info[0].select(".search-rooms")[0].string.encode("utf-8").strip()

        search_info = "{dates}, {nights}, {rooms}".format(
            dates=search_dates, nights=search_nights, rooms=search_rooms)


        # Start with the extraction of hotel information.
        hotellist_items = soup.select("div#listings > ol.listings > li.hotel")

        for div in hotellist_items:
            hotelname = price = price_text = number_of_nights = \
            number_of_nights_text = currency_code = price_norm = \
            rating_value = rating_unit = location = None

            # Extract the hotel name.
            a_name = div.select("h3.p-name a")
            if len(a_name) > 0:
                hotelname = a_name[0].string.encode("utf-8").strip()

            # Extract location.
            address_element = div.select(".contact .p-adr")
            if len(address_element) > 0:
                location = "".join(list(address_element[0].strings)[:-1]).encode('utf-8').strip()

            # Extract the stars rating.
            span_star_rating = div.select("span.star-rating.widget-star-rating-overlay")
            if len(span_star_rating) > 0:
                rating_value = float(span_star_rating[0].get("data-star-rating"))
                rating_unit = "stars"
            else:
                rating_value = 0.0

            # try to extract the normal price.
            b_price = div.select(".price b")
            if len(b_price) > 0:
                price_text = b_price[0].string.encode("utf-8").strip()

            else:
                # if price was reduced (red colored price)
                ins_price = div.select(".price span.old-price-cont ins")
                if len(ins_price) > 0:
                    price_text = ins_price[0].string.encode("utf-8").strip()

            # determine the number of nights the extracted price stands for.
            span_price_info = div.select(".price-breakdown > .price-info")
            if len(span_price_info) > 0:
                number_of_nights_text = span_price_info[0].string.encode("utf-8").strip()
                match = regex_price_per_nights.search(number_of_nights_text)
                if match != None:
                    number_of_nights = int(number_of_nights_text[match.start():match.end()])
                else:
                    # Fallback, because if the price is per night, there is not
                    # always a 1 in the string.
                    number_of_nights = 1


            # save hotel in results, if all information were extracted.
            if hotelname != None and price_text != None and number_of_nights != None:

                # split price and currency.
                price, currency = \
                    CurrencyConverter.split_price_and_currency(price_text=price_text)

                currency_code = \
                    CurrencyConverter.get_currency_code_of_sign(currency_sign=currency)

                # get the normalized price from the api function
                price_norm = CurrencyConverter.get_normalized_price(
                    price=price,
                    currency_code=currency_code
                )

                if price_norm is not None:
                    # calc price for one night
                    price_norm = round(price_norm / number_of_nights, 2)

                hotel_results.append({
                    "name" : hotelname,
                    "location" : location,
                    "price" : price,
                    "currency" : currency_code,
                    "price_norm" : price_norm,
                    "number_of_nights" : number_of_nights,
                    "rating_value" : rating_value,
                    "rating_unit" : rating_unit,
                    "access_time" : time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    "debug" : {
                        "price_text" : price_text,
                        "number_of_nights_text" : number_of_nights_text,
                        "search_info" : search_info,
                    },
                })

        return hotel_results


    def _set_rooms_with_size(self, driver, room_index, number_of_rooms, number_of_adults_per_room):
        ##
        #   Sets up the all rooms with a specific capacity of adults.
        #
        #   @param {selenium.webdriver} driver - Webdriver instance.
        #   @param {list} room_index - List with one item which is the current room
        #   index to determine the select tag for the number of adults.
        #   @param {int} number_of_rooms - Number of rooms for this size.
        #   @param {int} number_of_adults_per_room - Number of adults for this rooms.
        #

        for _ in range(number_of_rooms):

            # Determine the id for the select tag for the current room.
            adults_select_id = "qf-0q-room-{room_index}-adults".format(
                room_index=room_index[0]
            )

            adult_select = Select(driver.find_element_by_id(adults_select_id))
            adult_select.select_by_index(number_of_adults_per_room - 1)

            # increment room index
            room_index[0] += 1


    def _get_datepicker_css_selectors(self, datepicker_class, day, month, year):
        ##
        #   Generates the CSS selector of the date and the CSS selector for the
        #   next-month button.
        #
        #   @param {string} datepicker_class - CSS class selector for the datepicker.
        #   @param {string} day - Day of the date to select.
        #   @param {string} month - Month of the date to select.
        #   @param {string} year - Year of the date to select.
        #
        #   @return {string}, {string}
        #

        date_to_select = "{0}-{1}-{2}".format(year, int(month)-1, day)

        date_css_selector = "{datepicker_class} td[data-date=\"{date}\"] a".format(
            datepicker_class=datepicker_class,
            date=date_to_select
        )

        next_month_css_selector = "{datepicker_class} .widget-datepicker-next".format(
            datepicker_class=datepicker_class
        )

        return date_css_selector, next_month_css_selector
