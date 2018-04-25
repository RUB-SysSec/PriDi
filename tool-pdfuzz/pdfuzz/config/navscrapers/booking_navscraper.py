#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   02.11.2015
#   @author Nicolai Wilkop
#
#   @target_website booking.com
#

import sys
import logging
import re
import time
import datetime
import bs4
# import json

from selenium.webdriver.support.ui import Select
import selenium

import pdfuzz.config.navscrapers.api.currency_converter as CurrencyConverter
import pdfuzz.config.navscrapers.api.navigation as Navigation
import pdfuzz.common.exceptions as PDFuzzExceptions
# import pdfuzz.config.config as cfg


class NavScraper:
    ##
    #
    #
    ENTRY_URI = "http://booking.com"
    # PAGE_TYPE = cfg.PAGE_TYPES.HOTELS
    PAGE_TYPE = "hotels"

    def __init__(self):
        ##
        #
        #   @param {webdriver} driver - Selenium webdriver object which is
        #   connected to the PhantomJS WebDriver server.
        #

        self.SCRAPING_MODE = 0

    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #   Navigates to the hotel listing.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        self.travel_target = search_parameters.get("travel_target", "")
        self.number_of_adults = search_parameters.get("number_of_adults", "0")
        self.number_of_single_rooms = search_parameters.get("number_of_single_rooms", "0")
        self.number_of_double_rooms = search_parameters.get("number_of_double_rooms", "0")
        self.check_in_year = search_parameters.get("check_in_year", "")
        self.check_in_month = search_parameters.get("check_in_month", "")
        self.check_in_day = search_parameters.get("check_in_day", "")
        self.check_out_year = search_parameters.get("check_out_year", "")
        self.check_out_month = search_parameters.get("check_out_month", "")
        self.check_out_day = search_parameters.get("check_out_day", "")

        navigation_successful = True
        navigation_mode = -1
        # driver.get_screenshot_as_file("{0}_LOADED_booking_navscraper.png".format(time.time()))

        try:

            # Start navigation.
            try:

                try:
                    # Try to use the mobile navigation.
                    travel_target_element = self._mobile_navigation(
                        driver=driver
                    )
                    navigation_mode = 1

                except PDFuzzExceptions.DateNotFoundException:
                    # If the date can not be set, stop navigation.
                    return False

            except selenium.common.exceptions.NoSuchElementException:

                try:
                    # If the elements for the mobile navigation can not be
                    # found. Try the default navigation.
                    travel_target_element = self._default_navigation(
                        driver=driver
                    )
                    navigation_mode = 0

                except selenium.common.exceptions.WebDriverException:
                    # If an unexpected WebDriverException occurs, stop
                    # navigation.
                    return False

                except PDFuzzExceptions.DateNotFoundException:
                    # If the date can not be set, stop navigation.
                    return False

            # fill out the destination form.
            travel_target_element.clear()
            travel_target_element.send_keys(self.travel_target)

            # Set up the number of rooms and adults.
            self._set_rooms_and_adults_number(driver=driver)

            try:
                # Click radio button to select "hotels only".
                hotels_only_element = driver.find_element_by_css_selector(
                    "[name='nflt'][data-sb-acc-types='2']"
                )
                hotels_only_element.click()
            except:
                logging.warning('Hotels only mode is not available!')

            # driver.get_screenshot_as_file("{0}_BEFORE_SUBMIT_booking_navscraper.png".format(time.time()))

            # Submit the search form.
            travel_target_element.submit()

            # Handle the concretion dialog after submitting the search form.
            element, successful_option = self._handle_target_input_concretion(
                driver=driver
            )

            # Click or try to find results.
            # If one of the two cases match, the found element will be
            # clicked. In the case, that no element is found, the correction
            # view may not appeared and we try to find the results.
            if element:
                logging.debug("## Town selection found - booking")
                element.click()
            else:
                logging.debug("## Town selection NOT found - booking")
                # Try to find results for the current navigation mode.
                successful_option = navigation_mode

            # Wait for result element.
            if successful_option in [0]:
                # Wait for results on normal website.
                try:
                    element = Navigation.wait_for_the_presence_of_element(
                        driver=driver,
                        element_css_selector="div#hotellist_inner > div.sr_item",
                        timeout=60
                    )

                    # Choose default scraping routine.
                    self.SCRAPING_MODE = 0

                except selenium.common.exceptions.TimeoutException:
                    logging.exception("First normal Results not found")
                    logging.info("Try alternative Normal Results")

                    element = Navigation.wait_for_the_presence_of_element(
                        driver=driver,
                        element_css_selector="div#search_results_table > div.hotel-newlist",
                        timeout=60
                    )

                    # Choose default scraping routine.
                    self.SCRAPING_MODE = 2

            elif successful_option in [1]:
                # Wait for results on mobile website.
                element = Navigation.wait_for_the_presence_of_element(
                    driver=driver,
                    element_css_selector="div#srList ol#sr li.sr_simple_card",
                    timeout=60
                )

                # Choose mobile scraping routine.
                self.SCRAPING_MODE = 1

            else:
                logging.warning("Unhandled OPTION")
                return False

            # Wait for first price to be loaded.
            # element = self._wait_for_text_not_in_element(
            #     driver=driver,
            #     css_selector="div#hotellist_inner > div.sr_item:first-of-type td.roomPrice strong.price > b",
            #     old_text=""
            # )

            logging.debug("## Results found - booking")

            # Some extra time to load the results.
            # print("## Sleep 5 sec")
            time.sleep(2.5)

        except selenium.common.exceptions.TimeoutException:

            # If no results were found.
            logging.warning("Results not found! - booking")
            logging.exception("Timeout in navigation routine - booking")
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

            # driver.get_screenshot_as_file("booking_FINALLY_navscraper.png")
            logging.debug("## Navigating finished - booking")

        return navigation_successful

    def _default_navigation(self, driver):

        # Handle different cases for travel target input form
        # The input form does not always have an ID
        # print("[DEBUG] Try Desktop navigation")
        logging.debug("Try Desktop navigation")
        try:
            travel_target_element = driver.find_element_by_id("destination")
        except selenium.common.exceptions.NoSuchElementException:
            travel_target_element = \
                driver.find_element_by_css_selector(".c-autocomplete.sb-destination > input.c-autocomplete__input.sb-destination__input")

        try:
            logging.debug("Try to set the check-in and check-out dates via ComboBoxes.")
            # Try to set the check-in and check-out dates via ComboBoxes in the search form.
            # and set the dates in the ComboBoxes
            travel_start_md_select = Select(driver.find_element_by_name("checkin_monthday"))
            travel_start_md_select.select_by_value(self.check_in_day)

            travel_start_y_m_select = Select(driver.find_element_by_name("checkin_year_month"))
            travel_start_y_m_select.select_by_value("{0}-{1}".format(
                self.check_in_year, self.check_in_month
            ))

            travel_end_md_select = Select(driver.find_element_by_name("checkout_monthday"))
            travel_end_md_select.select_by_value(self.check_out_day)

            travel_end_y_m_select = Select(driver.find_element_by_name("checkout_year_month"))
            travel_end_y_m_select.select_by_value("{0}-{1}".format(
                self.check_out_year, self.check_out_month
            ))

        except selenium.common.exceptions.ElementNotVisibleException:

            # This exception is thrown if the Tablet version of the website is
            # shown. The Select boxes are available but hidden, so we have to
            # set the values directly via JS because we can not automate the
            # used datepicker.
            logging.exception("Error while trying to use selects to fill out the travel dates. Fill out selects by JS injection.")

            travel_start_md_select = driver.find_element_by_name("checkin_monthday")
            travel_start_y_m_select = driver.find_element_by_name("checkin_year_month")

            driver.execute_script(
                '''
                var checkin_monthday = arguments[0],
                    checkin_month_year = arguments[1];

                checkin_monthday.value = arguments[2];
                checkin_month_year.value = arguments[3];
                ''',
                travel_start_md_select,
                travel_start_y_m_select,
                self.check_in_day,
                "{0}-{1}".format(
                    self.check_in_year, self.check_in_month
                )
            )

            travel_end_md_select = driver.find_element_by_name("checkout_monthday")
            travel_end_y_m_select = driver.find_element_by_name("checkout_year_month")

            driver.execute_script(
                '''
                var checkout_monthday = arguments[0],
                    checkout_month_year = arguments[1];

                checkout_monthday.value = arguments[2];
                checkout_month_year.value = arguments[3];
                ''',
                travel_end_md_select,
                travel_end_y_m_select,
                self.check_out_day,
                "{0}-{1}".format(
                    self.check_out_year,
                    self.check_out_month
                )
            )

            logging.debug("Fill out hidden Selects via JS injection.")

        except selenium.common.exceptions.UnexpectedTagNameException:

            logging.exception("Error while trying to use selects to fill out the travel dates. Fill out inputs by JS injection.")

            travel_start_md_select = driver.find_element_by_name("checkin_monthday")
            travel_start_m_select = driver.find_element_by_name("checkin_month")
            travel_start_y_select = driver.find_element_by_name("checkin_year")

            driver.execute_script(
                '''
                var checkin_monthday = arguments[0],
                    checkin_month = arguments[1],
                    checkin_year = arguments[2];

                checkin_monthday.value = arguments[3];
                checkin_month.value = arguments[4];
                checkin_year.value = arguments[5];
                ''',
                travel_start_md_select, travel_start_m_select, travel_start_y_select,
                self.check_in_day, self.check_in_month, self.check_in_year)

            travel_end_md_select = driver.find_element_by_name("checkout_monthday")
            travel_end_m_select = driver.find_element_by_name("checkout_month")
            travel_end_y_select = driver.find_element_by_name("checkout_year")

            driver.execute_script(
                '''
                var checkout_monthday = arguments[0],
                    checkout_month = arguments[1],
                    checkout_year = arguments[2];

                checkout_monthday.value = arguments[3];
                checkout_month.value = arguments[4];
                checkout_year.value = arguments[5];

                ''',
                travel_end_md_select, travel_end_m_select, travel_end_y_select,
                self.check_out_day, self.check_out_month, self.check_out_year)

            logging.debug("Hidden Inputs selected and value manipulated!")

        except selenium.common.exceptions.WebDriverException:

            # Unexpected WebDriverException.
            logging.exception("Error while using the ComboBoxes to set the dates.")

            # Automate datepicker of second mobile version.
            check_in_day = '<input type="hidden" value="{0}" name="checkin_monthday">'.format(
                self.check_in_day
            )

            check_in_monthyear = '<input type="hidden" value="{0}-{1}" name="checkin_year_month">'.format(
                self.check_in_year, self.check_in_month
            )

            check_out_day = '<input type="hidden" value="{0}" name="checkout_monthday">'.format(
                self.check_out_day
            )
            check_out_monthyear = '<input type="hidden" value="{0}-{1}" name="checkout_year_month">'.format(
                self.check_out_year, self.check_out_month
            )

            driver.execute_script('''
                var target = $('.sb-date-picker[data-calendar2-type="checkin"] div[data-render=""]'),
                    html_code = target.html(),
                    day_code = arguments[0],
                    monthyear_code = arguments[1],
                    manipulated_html = day_code + monthyear_code + html_code;

                target.html(manipulated_html);
            ''', check_in_day, check_in_monthyear)

            driver.execute_script('''
                var target = $('.sb-date-picker[data-calendar2-type="checkout"] div[data-render=""]'),
                    html_code = target.html(),
                    day_code = arguments[0],
                    monthyear_code = arguments[1],
                    manipulated_html = day_code + monthyear_code + html_code;

                target.html(manipulated_html);
            ''', check_out_day, check_out_monthyear)

            time.sleep(2)

            logging.debug("Datepicker via injection of hidden input fields automated!")

        except:

            logging.exception("Error which leads to the datepicker alternative.")
            # If the ComboBoxes are not available.
            # Try to use the datepicker that is possible visible instead.
            logging.debug("Try to set the check-in and check-out dates via the alternative datepicker.")
            # Create the CSS selectors for the check-in date.
            cin_date_css_selector, cin_next_month_css_selector = \
                self._get_default_datepicker_css_selectors(
                    datepicker_class=".sb-calendar__calendars",
                    day=self.check_in_day,
                    month=self.check_in_month,
                    year=self.check_in_year
                )

            # Create the CSS selectors for the check-out date.
            cout_date_css_selector, cout_next_month_css_selector = \
                self._get_default_datepicker_css_selectors(
                    datepicker_class=".sb-calendar__calendars",
                    day=self.check_out_day,
                    month=self.check_out_month,
                    year=self.check_out_year
                )

            # set the dates via datepicker.
            check_in_div = \
                driver.find_element_by_css_selector(".-outside .-check-in")
            check_out_div = \
                driver.find_element_by_css_selector(".-outside .-check-out")

            # open checkin datepicker
            check_in_div.click()

            status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cin_date_css_selector,
                next_month_css_selector=cin_next_month_css_selector,
                delay_before_date_click=2.5
            )

            if not status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cin_date_css_selector
                ))

            time.sleep(2.5)

            # open checkout datepicker
            check_out_div.click()

            status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cout_date_css_selector,
                next_month_css_selector=cout_next_month_css_selector,
                delay_before_date_click=2.5
            )

            if not status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cout_date_css_selector
                ))

        return travel_target_element

    def _mobile_navigation(self, driver):

        # print("[DEBUG] Try Mobile navigation")
        logging.debug("Try Mobile navigation")
        travel_target_element = driver.find_element_by_id("input_destination")

        try:

            # Create the CSS selectors for the check-in date.
            cin_date_css_selector, cin_next_month_css_selector = \
                self._get_mobile_datepicker_css_selectors(
                    datepicker_class=".pikaday-checkin",
                    day=self.check_in_day,
                    month=self.check_in_month,
                    year=self.check_in_year
                )

            # Create the CSS selectors for the check-out date.
            cout_date_css_selector, cout_next_month_css_selector = \
                self._get_mobile_datepicker_css_selectors(
                    datepicker_class=".pikaday-checkout",
                    day=self.check_out_day,
                    month=self.check_out_month,
                    year=self.check_out_year
                )

            # set the dates via datepicker.
            check_in_div = driver.find_element_by_id("ci_date_field")
            check_out_div = driver.find_element_by_id("co_date_field")

            # open checkin datepicker
            check_in_div.click()

            status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cin_date_css_selector,
                next_month_css_selector=cin_next_month_css_selector,
                delay_before_date_click=2.5
            )

            if not status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cin_date_css_selector
                ))

            time.sleep(2.5)

            # open checkout datepicker
            check_out_div.click()

            status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cout_date_css_selector,
                next_month_css_selector=cout_next_month_css_selector,
                delay_before_date_click=2.5
            )

            if not status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cout_date_css_selector
                ))

        except:

            # If the first attempt of automating the datepicker fails, try the
            # second alternative.
            logging.exception("Try second version of the datepicker.")

            # Create the CSS selectors for the check-in date.
            cin_date_css_selector, cin_next_month_css_selector = \
                self._get_mobile_datepicker_css_selectors(
                    datepicker_class=".checkin-active",
                    day=self.check_in_day,
                    month=self.check_in_month,
                    year=self.check_in_year
                )

            # Create the CSS selectors for the check-out date.
            cout_date_css_selector, cout_next_month_css_selector = \
                self._get_mobile_datepicker_css_selectors(
                    datepicker_class=".checkout-active",
                    day=self.check_out_day,
                    month=self.check_out_month,
                    year=self.check_out_year
                )

            # set the dates via datepicker.
            check_in_div = driver.find_element_by_id("ci_date_field")
            check_out_div = driver.find_element_by_id("co_date_field")

            # open checkin datepicker
            check_in_div.click()

            status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cin_date_css_selector,
                next_month_css_selector=cin_next_month_css_selector,
                delay_before_date_click=2.5
            )

            if not status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cin_date_css_selector
                ))

            time.sleep(2.5)

            # open checkout datepicker
            check_out_div.click()

            status = Navigation.set_date_in_basic_datepicker(
                driver=driver,
                date_css_selector=cout_date_css_selector,
                next_month_css_selector=cout_next_month_css_selector,
                delay_before_date_click=2.5
            )

            if not status:
                raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                    cout_date_css_selector
                ))

        return travel_target_element

    def _set_rooms_and_adults_number(self, driver):
        # print("[DEBUG] Set room and adults")
        # Handle the different cases of input form for rooms, adults and
        # children.
        try:

            try:
                # Look for room select.
                room_select = Select(driver.find_element_by_css_selector(".b-form__group > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > label:nth-child(1) > select:nth-child(2)"))

            except selenium.common.exceptions.NoSuchElementException:
                # Look for alternative room select.
                room_select = Select(driver.find_element_by_css_selector(".js-sb_predefined_group_options_select"))

            # Select advanced options to enable the selects for rooms,
            # adults and children.
            room_select.select_by_value("3")

        except selenium.common.exceptions.NoSuchElementException:
            pass

        # Fill out the selects for room number and count of persons (adult, children)
        try:
            # Try to get the select for the number of rooms.
            # The mobile version does not have this select and the attempt to
            # access it will cause an error.
            number_rooms_select = Select(driver.find_element_by_name("no_rooms"))
            number_rooms_select.select_by_value(self.number_of_single_rooms)
        except selenium.common.exceptions.UnexpectedTagNameException:
            # Ignore the error and go on because on mobile devices it is not
            # necessary to fill out the number of rooms.
            pass

        # Determine select fields.
        number_adults_select = \
            Select(driver.find_element_by_name("group_adults"))
        # number_children_select = \
        #     Select(driver.find_element_by_name("group_children"))

        # Enter the number of adults.
        number_adults_select.select_by_value(self.number_of_adults)

    def _handle_target_input_concretion(self, driver):

        # Wait for target concretion.
        # At this point two cases need to be handled. Sometimes a different
        # page is passed back by the server. If the first (Normal) does not
        # match, the second (Fallback) will be used. Third case is Mobile.
        correction_selectors = [
            # ("[OPTION] Normal", "div#cityWrapper > div"),
            # ("[OPTION] Normal", ".cityWrapper .disname:first-of-type a.destination_name"),
            ("[OPTION] Normal", "div.disam-single-result:first-of-type .dismeta a > span", 0),
            ("[OPTION] Mobile", "ol#disamb > li:first-of-type > a", 1),
        ]

        element = None
        successful_option = -1

        for debug_text, selector, status_code in correction_selectors:

            try:

                logging.debug(debug_text)
                element = Navigation.wait_for_the_presence_of_element(
                    driver=driver,
                    element_css_selector=selector,
                    timeout=20
                )

                successful_option = status_code

                # driver.get_screenshot_as_file("{0}_booking_CORRECTION_navscraper.png".format(time.time()))
                break

            except selenium.common.exceptions.TimeoutException:
                continue

        return element, successful_option


    def scrape_results(self, driver):
        ##
        #   Extract hotel names and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        # print("## Taking Screenshot")
        # driver.get_screenshot_as_file("{0}_booking_navscraper.png".format(time.time()))

        logging.debug("## Scraping Data - booking")
        hotel_results = []
        result_pages_limit = 20

        if self.SCRAPING_MODE == 0:

            logging.info("Using default scraper.")
            hotel_results = self._default_scraper(
                driver=driver,
                result_pages_limit=result_pages_limit
            )

            if len(hotel_results) == 0:
                logging.debug("Default scraper did not work, try alternative default scraper.")
                self.SCRAPING_MODE = 2


        if self.SCRAPING_MODE == 1:

            logging.info("Using mobile scraper.")
            hotel_results = self._mobile_scraper(
                driver=driver,
                result_pages_limit=result_pages_limit
            )

        if self.SCRAPING_MODE == 2:

            logging.info("Using alternative default scraper.")
            hotel_results = self._alternative_default_scraper(
                driver=driver,
                result_pages_limit=result_pages_limit
            )

        return hotel_results


    def _default_scraper(self, driver, result_pages_limit):
        ##
        #   Extract hotel names and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {int} result_pages_limit - Limit for next pages.
        #

        hotel_results = []
        page_counter = 0

        while True:

            driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            time.sleep(2)

            page_counter += 1
            logging.debug("Scraping page {0}".format(page_counter))
            print("[DEBUG] Scraping page {0}".format(page_counter))
            # driver.get_screenshot_as_file("booking_RESULTS_PAGE_{0}_navscraper.png".format(page_counter))

            html_source = driver.page_source
            with open("booking_dump_page_{}.html".format(page_counter), "w") as f:
                f.write(html_source.encode("utf-8"))

            hotel_results_part = self._default_scraping_routine(page_source=html_source)
            hotel_results.extend(hotel_results_part)

            if len(hotel_results_part) > 1:
                second_hotel_name = hotel_results_part[1]["name"]
            else:
                second_hotel_name = ""

            print("[DEBUG] Number of Results: {0}".format(len(hotel_results_part)))
            print("[DEBUG] Second hotel name: {0}".format(second_hotel_name))

            try:
                # Pagination: Next Page
                next_page_element = driver.find_element_by_css_selector("div.results-paging > a.paging-next")

                # Click on next page link
                next_page_element.click()
                logging.debug("Page_Next Button clicked.")

                try:
                    logging.debug("Start Waiting for next result page.")
                    # Wait for results.
                    Navigation.wait_for_text_to_be_not_present_in_element(
                        driver=driver,
                        element_css_selector="div#hotellist_inner > div.sr_item:nth-of-type(2) a.hotel_name_link > .sr-hotel__name",
                        old_text=second_hotel_name,
                        timeout=480
                    )
                    logging.debug("Next result page loaded.")

                except selenium.common.exceptions.TimeoutException:
                    # If no results were found.
                    # End loop and return the current results.
                    logging.exception("No updated results! Last hotel name from second position: '{}'".format(second_hotel_name))
                    break

            except selenium.common.exceptions.NoSuchElementException:
                # If no next page link was not found.
                # End loop and return the current results.
                logging.exception("No Next Link found!")
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

    def _default_scraping_routine(self, page_source):
        ##
        #   ...
        #
        #   @param {string} page_source - ...
        #
        #   @return {list}
        #

        # regex_price = re.compile("([0-9]+[ .])*[0-9]+")

        hotel_results = []
        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        # Get search information for debug output.
        search_info = number_of_nights = None
        breadcrumb_divs = soup.select("#breadcrumb > div")
        if len(breadcrumb_divs) > 0:
            # take the last div in the breadcrumb and find the span tag.
            search_info_span = breadcrumb_divs[-1].select("span")
            if len(search_info_span) > 0:
                search_target_adults = search_info_span[0].contents[1].string.encode("utf-8").strip()
                search_nights = search_info_span[0].contents[2].string.encode("utf-8").strip()
                search_dates = search_info_span[0].contents[3].string.encode("utf-8").strip()

                search_info = "{} {} {}".format(
                    search_target_adults,
                    search_nights,
                    search_dates
                )

                # Determine the number of nights.
                number_of_nights = \
                    int(re.search("[0-9]+", search_nights).group())

            else:
                # Fallback: Calculate nights by the use of the dates
                search_info = "[EMPTY]"
                cin = datetime.date(
                    int(self.check_in_year),
                    int(self.check_in_month),
                    int(self.check_in_day)
                )
                cout = datetime.date(
                    int(self.check_out_year),
                    int(self.check_out_month),
                    int(self.check_out_day)
                )
                delta = cout - cin
                number_of_nights = delta.days

        hotellist_items = soup.select("#hotellist_inner > div.sr_item")

        for div in hotellist_items:
            hotelname = number_of_nights_text = price = price_text = \
                currency_code = rating_value = rating_unit = price_norm = None

            # determine name of hotel
            a_name = div.select("a.hotel_name_link > .sr-hotel__name")
            if len(a_name) > 0:
                hotelname = list(a_name[0].strings)[-1].encode("utf-8").strip()

            # Extract rating information (stars, circles)
            rating_element = div.select(".star_track")
            if len(rating_element) > 0:
                rating_element = rating_element[0]
                rating_element_classes = rating_element.get("class")

                # Determine if the rating unit is stars or circles.
                if "ratings_circles_any" in rating_element_classes:
                    rating_unit = "circles"
                    class_prefix = "ratings_circles_"
                else:
                    rating_unit = "stars"
                    class_prefix = "ratings_stars_"

                # Iterate over classes and extract the number of stars/circles
                # out of the class.
                for re_class in rating_element_classes:
                    if re_class.startswith(class_prefix) and \
                            re_class[-1].isdigit():
                        rating_value = float(re_class[len(class_prefix):])
                        break

            else:
                # Rating of zero stars/circles.
                rating_value = 0.0
                rating_unit = None

            # extract price.
            b_price = div.select("td.roomPrice strong.price > b")
            if len(b_price) > 0:
                price_text = b_price[0].string.encode("utf-8").strip()

                # split price and currency.
                price, currency = \
                    CurrencyConverter.split_price_and_currency(
                        price_text=price_text
                    )

                currency_code = \
                    CurrencyConverter.get_currency_code_of_sign(
                        currency_sign=currency
                    )

                # get the normalized price from the api function
                price_norm = CurrencyConverter.get_normalized_price(
                    price=price,
                    currency_code=currency_code
                )

                # DEBUG
                if price_norm is not None and price_norm < 4:
                    logging.debug("[LOW_PRICE_BUG] Strange low price:\n{text}\n{bytes}".format(
                        text=price_text, bytes=price_text.encode("hex")))

            # determine the number of nights the extracted price stands for.
            span_price_for_x_nights = div.select(".price_for_x_nights_format")
            if len(span_price_for_x_nights) > 0:
                number_of_nights_text = \
                    span_price_for_x_nights[0].string.encode("utf-8").strip()
            else:
                number_of_nights_text = "[EMPTY]"

            print("Name: {} ; Price: {} ; Nights: {}".format(
                hotelname, price, number_of_nights
            ))

            if hotelname is not None and price is not None and \
                    number_of_nights is not None:

                if price_norm is not None:
                    # calc price for one night
                    price_norm = round(price_norm / number_of_nights, 2)

                hotel_results.append({
                    "name": hotelname,
                    "price": price,
                    "currency": currency_code,
                    "price_norm": price_norm,
                    "number_of_nights": number_of_nights,
                    "rating_value": rating_value,
                    "rating_unit": rating_unit,
                    "access_time": time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    "debug": {
                        "price_text": price_text,
                        "number_of_nights_text": number_of_nights_text,
                        "search_info": search_info,
                    },
                })

        return hotel_results

    def _alternative_default_scraper(self, driver, result_pages_limit):
        ##
        #   Extract hotel names and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {int} result_pages_limit - Limit for next pages.
        #

        hotel_results = []
        page_counter = 0

        while True:

            page_counter += 1
            # print("[DEBUG] Scraping page {0}".format(page_counter))
            # driver.get_screenshot_as_file("booking_RESULTS_PAGE_{0}_navscraper.png".format(page_counter))

            html_source = driver.page_source
            hotel_results_part = self._alternative_default_scraping_routine(page_source=html_source)
            hotel_results.extend(hotel_results_part)

            if len(hotel_results_part) > 1:
                second_hotel_name = hotel_results_part[1]["name"]
            else:
                second_hotel_name = ""

            try:
                # Pagination: Next Page
                next_page_element = driver.find_element_by_css_selector("div.results-paging > a.paging-next")

                # Click on next page link
                next_page_element.click()

                try:
                    # Wait for results.
                    Navigation.wait_for_text_to_be_not_present_in_element(
                        driver=driver,
                        element_css_selector="#search_results_table > .hotel-newlist:nth-of-type(2) .title_fix > a.hotel_name_link",
                        old_text=second_hotel_name
                    )

                except selenium.common.exceptions.TimeoutException:
                    # If no results were found.
                    # End loop and return the current results.
                    logging.exception("No updated results! Last hotel name from second position: '{}'".format(second_hotel_name))
                    break

            except selenium.common.exceptions.NoSuchElementException:
                # If no next page link was not found.
                # End loop and return the current results.
                logging.exception("No Next Link found!")
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

    def _alternative_default_scraping_routine(self, page_source):
        ##
        #   ...
        #
        #   @param {string} page_source - ...
        #
        #   @return {list}
        #

        logging.debug("[ALT-SCRAPER] Access Scraping routine.")
        # regex_price = re.compile("([0-9]+[ .])*[0-9]+")

        hotel_results = []
        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        # Get search information for debug output.
        search_info = number_of_nights = None
        breadcrumb_divs = soup.select("#breadcrumb > div")
        if len(breadcrumb_divs) > 0:
            # take the last div in the breadcrumb and find the span tag.
            search_info_span = breadcrumb_divs[-1].select("span")
            if len(search_info_span) > 0:
                search_target_adults = search_info_span[0].contents[1].string.encode("utf-8").strip()
                search_nights = search_info_span[0].contents[2].string.encode("utf-8").strip()
                search_dates = search_info_span[0].contents[3].string.encode("utf-8").strip()

                search_info = "{} {} {}".format(search_target_adults, search_nights, search_dates)

                # Determine the number of nights.
                number_of_nights = int(re.search("[0-9]+", search_nights).group())

            else:
                # Fallback: Calculate nights by the use of the dates
                search_info = "[EMPTY]"
                cin = datetime.date(int(self.check_in_year), int(self.check_in_month), int(self.check_in_day))
                cout = datetime.date(int(self.check_out_year), int(self.check_out_month), int(self.check_out_day))
                delta = cout - cin
                number_of_nights = delta.days

        logging.debug("[ALT-SCRAPER] Getting hotel list.")
        hotellist_items = soup.select("#search_results_table > .hotel-newlist")
        logging.debug("[ALT-SCRAPER] Iterate over hotel list.")
        for div in hotellist_items:
            hotelname = number_of_nights_text = price = price_text = currency_code = \
            rating_value = rating_unit = price_norm = location = None

            # determine name of hotel
            a_name = div.select(".title_fix > a.hotel_name_link")
            if len(a_name) > 0:
                hotelname = list(a_name[0].strings)[-1].encode("utf-8").strip()

            # Extract location.
            location_element = div.select(".address a")
            if len(location_element) > 0:
                location = location_element[0].get("data-coords")

            # Extract rating information (stars, circles)
            rating_element = div.select(".nowrap > span:nth-of-type(1)")
            if len(rating_element) > 0:
                rating_element = rating_element[0]
                rating_element_classes = rating_element.get("class")

                # Determine if the rating unit is stars or circles.
                if "retina_estimated" in rating_element_classes:
                    rating_unit = "circles"
                    class_prefix = "retina_stars_"
                else:
                    rating_unit = "stars"
                    class_prefix = "retina_stars_"

                # Iterate over classes and extract the number of stars/circles out of
                # the class.
                for re_class in rating_element_classes:
                    if re_class.startswith(class_prefix) and re_class[-1].isdigit():
                        rating_value = float(re_class[len(class_prefix):])
                        break

            else:
                # Rating of zero stars/circles.
                rating_value = 0.0
                rating_unit = None

            # extract price.
            b_price = div.select("td.roomPrice .price.big-price")
            if len(b_price) > 0:
                price_text = b_price[0].string.encode("utf-8").strip()

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

                # DEBUG
                if price_norm is not None and price_norm < 4:
                    logging.debug("[LOW_PRICE_BUG] Strange low price:\n{text}\n{bytes}".format(
                        text=price_text, bytes=price_text.encode("hex")))

            # determine the number of nights the extracted price stands for.
            span_price_for_x_nights = div.select(".price_for_x_nights_format")
            if len(span_price_for_x_nights) > 0:
                number_of_nights_text = span_price_for_x_nights[0].string.encode("utf-8").strip()
            else:
                number_of_nights_text = "[EMPTY]"

            logging.debug("Hotelname: {} ; Price: {} ; number_of_nights: {} ; Rating: {} {}".format(
                hotelname,
                price,
                number_of_nights,
                rating_value,
                rating_unit
            ))
            if hotelname is not None and price is not None and \
                    number_of_nights is not None:

                if price_norm is not None:
                    # calc price for one night
                    price_norm = round(price_norm / number_of_nights, 2)

                hotel_results.append({
                    "name": hotelname,
                    "location": location,
                    "price": price,
                    "currency": currency_code,
                    "price_norm": price_norm,
                    "number_of_nights": number_of_nights,
                    "rating_value": rating_value,
                    "rating_unit": rating_unit,
                    "access_time": time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    "debug": {
                        "price_text": price_text,
                        "number_of_nights_text": number_of_nights_text,
                        "search_info": search_info,
                    },
                })

        return hotel_results


    def _mobile_scraper(self, driver, result_pages_limit):
        ##
        #   Extract hotel names and prices from the mobile version of the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {int} result_pages_limit - Limit for next pages.
        #

        hotel_results = []
        page_counter = 0

        while True:

            page_counter += 1
            # print("[DEBUG] Scraping page {0}".format(page_counter))
            # driver.get_screenshot_as_file("booking_RESULTS_PAGE_{0}_navscraper.png".format(page_counter))

            html_source = driver.page_source
            hotel_results_part = self._mobile_scraping_routine(page_source=html_source)
            hotel_results.extend(hotel_results_part)

            if len(hotel_results_part) > 1:
                second_hotel_name = hotel_results_part[1]["name"]
            else:
                second_hotel_name = ""

            try:
                # Pagination: Next Page
                pagination_next_selectors = [
                    "li.pagination_next > a#sr_link_next > span",
                    ".sr-pagination a.sr-pagination--item__next",
                ]
                for page_next_index, page_next_selector in enumerate(pagination_next_selectors):
                    # Try the various pagination next CSS selectors.
                    try:
                        next_page_element = driver.find_element_by_css_selector(page_next_selector)
                        # Click on next page link
                        next_page_element.click()
                        break

                    except selenium.common.exceptions.NoSuchElementException:

                        if page_next_index == (len(pagination_next_selectors) - 1):
                            # If no page next selector was successful, raise
                            # the exception to end the scraping procedure.
                            raise

                try:
                    # Wait for results.
                    Navigation.wait_for_text_to_be_not_present_in_element(
                        driver=driver,
                        element_css_selector="div#srList ol#sr li.sr_simple_card:nth-of-type(2) h3.sr_simple_card_hotel_name",
                        old_text=second_hotel_name
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


    def _mobile_scraping_routine(self, page_source):
        ##
        #   ...
        #
        #   @param {string} page_source - ...
        #
        #   @return {list}
        #

        hotel_results = []
        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        # Get search information for debug output.
        search_info = number_of_nights = None
        # breadcrumb_divs = soup.select("#breadcrumb > div")
        # if len(breadcrumb_divs) > 0:
        #     # take the last div in the breadcrumb and find the span tag.
        #     search_info_span = breadcrumb_divs[-1].select("span")
        #     if len(search_info_span) > 0:
        #         search_target_adults = search_info_span[0].contents[1].string.encode("utf-8").strip()
        #         search_nights        = search_info_span[0].contents[2].string.encode("utf-8").strip()
        #         search_dates         = search_info_span[0].contents[3].string.encode("utf-8").strip()

        #         search_info = "{} {} {}".format(search_target_adults, search_nights, search_dates)

        #         # Determine the number of nights.
        #         number_of_nights = int(re.search("[0-9]+", search_nights).group())

        #     else:
        # Fallback: Calculate nights by the use of the dates
        search_info = "[EMPTY]"
        cin  = datetime.date(int(self.check_in_year), int(self.check_in_month), int(self.check_in_day))
        cout = datetime.date(int(self.check_out_year), int(self.check_out_month), int(self.check_out_day))
        delta = cout - cin
        number_of_nights = delta.days


        hotellist_items = soup.select("div#srList ol#sr li.sr_simple_card")

        for li_sr in hotellist_items:
            hotelname = number_of_nights_text = price = price_text = currency_code = \
            rating_value = rating_unit = price_norm = None

            # determine name of hotel
            h3_name = li_sr.find_all("h3", {"class": "sr_simple_card_hotel_name"})
            if len(h3_name) > 0:
                hotelname = h3_name[0].string.encode("utf-8").strip()

            # Extract rating information. (stars, circles)
            # Check if the rating unit is stars.
            stars_list = li_sr.select(".m-badge > i.bicon-acstar")
            if len(stars_list) > 0:
                rating_value = len(stars_list)
                rating_unit = "stars"
            else:
                # Check if the rating unit is circles.
                circles_list = li_sr.select(".m-badge > i.bicon-circle")
                if len(circles_list) > 0:
                    rating_value = len(circles_list)
                    rating_unit = "circles"
                else:
                    rating_value = 0.0
                    rating_unit = None

            # Extract price of the hotel.
            price_element = li_sr.select("div.sr-card__item--strong.sr-card__item--large")
            if len(price_element) > 0:
                price_text = list(price_element[0].strings)[0].encode("utf-8").strip()
            else:
                # Try alternative price representation.
                price_element = li_sr.find_all("span", {"class": "sr_simple_card_price_cheapest_price"})
                if len(price_element) > 0:
                    price_text = list(price_element[0].strings)[0].encode("utf-8").strip()

            if price_text is not None:

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

                # DEBUG
                if price_norm is not None and price_norm < 4:
                    logging.debug("[LOW_PRICE_BUG] Strange low price:\n{text}\n{bytes}".format(
                        text=price_text, bytes=price_text.encode("hex")))

            # determine the number of nights the extracted price stands for.
            # span_price_for_x_nights = li_sr.select(".price_for_x_nights_format")
            # if len(span_price_for_x_nights) > 0:
            #     number_of_nights_text = span_price_for_x_nights[0].string.encode("utf-8").strip()
            # else:
            number_of_nights_text = "[EMPTY]"

            if hotelname is not None and price is not None and \
                    number_of_nights is not None:

                if price_norm is not None:
                    # calc price for one night
                    price_norm = round(price_norm / number_of_nights, 2)

                hotel_results.append({
                    "name": hotelname,
                    "price": price,
                    "currency": currency_code,
                    "price_norm": price_norm,
                    "number_of_nights": number_of_nights,
                    "rating_value": rating_value,
                    "rating_unit": rating_unit,
                    "access_time": time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    "debug": {
                        "price_text": price_text,
                        "number_of_nights_text": number_of_nights_text,
                        "search_info": search_info,
                    },
                })

        return hotel_results


    def _get_mobile_datepicker_css_selectors(self, datepicker_class, day, month, year):
        ##
        #
        #
        #   @param {string} datepicker_css_selector - CSS selector for the datepicker.
        #   @param {int} day - Day of the date.
        #   @param {int} month - Month of the date.
        #   @param {int} year - Year of the date.
        #
        #   @return {string}, {string}
        #

        day     = int(day)
        month   = int(month) - 1
        year    = int(year)

        date_css_selector = \
            "{datepicker_class} td button[data-pika-day=\"{day}\"][data-pika-month=\"{month}\"][data-pika-year=\"{year}\"]".format(
                datepicker_class=datepicker_class,
                day=day,
                month=month,
                year=year
            )

        next_month_css_selector = \
            "{datepicker_class} button.pika-next".format(datepicker_class=datepicker_class)


        return date_css_selector, next_month_css_selector


    def _get_default_datepicker_css_selectors(self, datepicker_class, day, month, year):
        ##
        #
        #
        #   @param {string} datepicker_css_selector - CSS selector for the datepicker.
        #   @param {int} day - Day of the date.
        #   @param {int} month - Month of the date.
        #   @param {int} year - Year of the date.
        #
        #   @return {string}, {string}
        #

        day     = int(day)
        month   = int(month) - 1
        year    = int(year)

        date_css_selector = \
            "{datepicker_class} span[data-day=\"{day}\"][data-month=\"{month}\"][data-year=\"{year}\"]".format(
                datepicker_class=datepicker_class,
                day=day,
                month=month,
                year=year
            )

        next_month_css_selector = None

        return date_css_selector, next_month_css_selector
