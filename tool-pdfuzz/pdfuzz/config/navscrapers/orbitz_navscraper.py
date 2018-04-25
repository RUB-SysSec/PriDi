#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#
#   @date   15.12.2015
#   @author Nicolai Wilkop
#
#   @target_website orbitz.com
#

import sys
import logging
import re
import time
import bs4

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
    ENTRY_URI = "http://orbitz.com"
    # PAGE_TYPE = cfg.PAGE_TYPES.HOTELS
    PAGE_TYPE = "hotels"

    def __init__(self):
        ##
        #
        #

        self.WEBSITE_MODE = "default"


    def navigate_to_results(self, driver, search_parameters={}):
        ##
        #   Navigates to the hotel listing.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {dict} search_parameters - Parameters for the search input form.
        #

        travel_target           = search_parameters.get("travel_target", "")
        # number_of_adults        = search_parameters.get("number_of_adults", "0")
        number_of_single_rooms  = search_parameters.get("number_of_single_rooms", "0")
        number_of_double_rooms  = search_parameters.get("number_of_double_rooms", "0")
        check_in_year           = search_parameters.get("check_in_year", "")
        check_in_month          = search_parameters.get("check_in_month", "")
        check_in_day            = search_parameters.get("check_in_day", "")
        check_out_year          = search_parameters.get("check_out_year", "")
        check_out_month         = search_parameters.get("check_out_month", "")
        check_out_day           = search_parameters.get("check_out_day", "")

        navigation_successful = True

        # driver.get_screenshot_as_file("errors/{0}_LOADED_orbitz_navscraper.png".format(time.time()))

        try:

            # Switch to the hotel tab.
            self._select_hotels_tab(driver=driver)

            logging.debug("Switched to hotels tab.")


            # Configure the number of rooms that are needed with the specific
            # amount of adults.
            self._set_rooms_and_adults_number_new_version(
                driver=driver,
                number_of_single_rooms=number_of_single_rooms,
                number_of_double_rooms=number_of_double_rooms
            )

            logging.debug("Filled persons and rooms.")

            # Set the check-in and check-out date for the travel.
            self._set_travel_dates(
                driver=driver,
                check_in_dates={
                    "day" : check_in_day,
                    "month" : check_in_month,
                    "year" : check_in_year,
                },
                check_out_dates={
                    "day" : check_out_day,
                    "month" : check_out_month,
                    "year" : check_out_year,
                }
            )

            logging.debug("Set travel dates.")

            # Timeout for waiting that the input field is editable.
            time.sleep(1)
            travel_target_element = driver.find_element_by_id("hotel-destination")
            travel_target_element.clear()
            travel_target_element.click()
            travel_target_element.send_keys(travel_target)

            logging.debug("Set travel destination.")

            # driver.get_screenshot_as_file("{0}_BEFORE_SUBMIT_orbitz_navscraper.png".format(time.time()))
            submit_button = driver.find_element_by_id("search-button")
            # submit_button.click()
            submit_button.send_keys(Keys.ENTER)

            logging.debug("Search form sent. WEBSITE_MODE: '{}'".format(self.WEBSITE_MODE))

            # Wait for result element.
            if self.WEBSITE_MODE == "alternative":

                logging.debug("Waiting for 'alternative' results.")
                Navigation.wait_for_the_presence_of_element(
                    driver=driver,
                    element_css_selector=".hotelSlimResultsModuleMod > div > div.hotel-result",
                    timeout=120
                )

            elif self.WEBSITE_MODE == "default":

                logging.debug("Waiting for 'default' results.")
                Navigation.wait_for_the_presence_of_element(
                    driver=driver,
                    element_css_selector="#resultsContainer .hotel.listing",
                    timeout=120
                )


            # driver.get_screenshot_as_file("{0}_RESULTS_orbitz_navscraper.png".format(time.time()))

            logging.debug("## Results found - orbitz")

        except selenium.common.exceptions.TimeoutException:

            # If no results were found.
            logging.warning("Results not found! - orbitz")
            logging.exception("Results not found!")
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

            # driver.get_screenshot_as_file("orbitz_FINALLY_navscraper.png")
            logging.debug("## Navigating finished - orbitz")

        return navigation_successful


    def _select_hotels_tab(self, driver):

        hotel_tab_element = driver.find_element_by_id("tab-hotel-tab")
        hotel_tab_element.click()


    def _set_rooms_and_adults_number_new_version(self, driver, number_of_single_rooms, number_of_double_rooms):

        total_room_number = int(number_of_double_rooms) + int(number_of_single_rooms)

        # Try to find the select tag to modify the number of adults.
        room_number_select = Select(driver.find_element_by_id("hotel-rooms"))
        room_number_select.select_by_value(str(total_room_number))

        room_counter = 1

        for _ in range(int(number_of_double_rooms)):
            adults_select = Select(driver.find_element_by_id("hotel-{room_num}-adults".format(room_num=room_counter)))
            adults_select.select_by_value("2")
            room_counter += 1

        for _ in range(int(number_of_single_rooms)):
            adults_select = Select(driver.find_element_by_id("hotel-{room_num}-adults".format(room_num=room_counter)))
            adults_select.select_by_value("1")
            room_counter += 1


    def _set_rooms_and_adults_number(self, driver, number_of_single_rooms, number_of_double_rooms):

        # Get the selects for adults.
        try:

            # Try to find the select tag to modify the number of adults.
            Select(driver.find_element_by_name("hotel.rooms[0].adlts"))

            # Get add_room link
            add_room_link = driver.find_element_by_css_selector("a.addRoom")

            room_counter = [0]

            # Setup single rooms within overlay.
            self._set_rooms(
                driver=driver,
                room_counter=room_counter,
                number_of_rooms=number_of_single_rooms,
                room_size=1,
                add_room_link=add_room_link,
                set_room_function=self._set_room_in_start_page
            )

            # Setup double rooms within overlay.
            self._set_rooms(
                driver=driver,
                room_counter=room_counter,
                number_of_rooms=number_of_double_rooms,
                room_size=2,
                add_room_link=add_room_link,
                set_room_function=self._set_room_in_start_page
            )

            self.WEBSITE_MODE = "default"

            # driver.get_screenshot_as_file("{0}_ROOMS_SETUP_START_PAGE_orbitz_navscraper.png".format(time.time()))


        except selenium.common.exceptions.UnexpectedTagNameException:

            # If no select tag can be found, activate the overlay to choose
            # the number of adults and the rooms.
            input_text_element = driver.find_element_by_css_selector("a.input-text")
            input_text_element.click()

            # driver.get_screenshot_as_file("{0}_INPUT_TEXT_CLICKED_orbitz_navscraper.png".format(time.time()))

            # Get add_room link
            add_room_link = driver.find_element_by_css_selector("a.add-room-card")

            room_counter = [0]

            # Setup single rooms within overlay.
            self._set_rooms(
                driver=driver,
                room_counter=room_counter,
                number_of_rooms=number_of_single_rooms,
                room_size=1,
                add_room_link=add_room_link,
                set_room_function=self._set_room_in_overlay
            )

            # Setup double rooms within overlay.
            self._set_rooms(
                driver=driver,
                room_counter=room_counter,
                number_of_rooms=number_of_double_rooms,
                room_size=2,
                add_room_link=add_room_link,
                set_room_function=self._set_room_in_overlay
            )

            # driver.get_screenshot_as_file("{0}_ROOMS_SETUP_OVERLAY_orbitz_navscraper.png".format(time.time()))

            # get apply link
            apply_link = driver.find_element_by_id("overlay-submit")
            apply_link.click()

            self.WEBSITE_MODE = "default"


    def _set_travel_dates(self, driver, check_in_dates, check_out_dates):

        travel_checkin_element  = driver.find_element_by_id("hotel-checkin")
        travel_checkout_element = driver.find_element_by_id("hotel-checkout")

        # Old Stuff. Datepicker is now automated.
        # #######################################
        # time.sleep(1)
        # # driver.get_screenshot_as_file("{0}_BEFORE_CHECKIN_orbitz_navscraper.png".format(time.time()))
        # # Set check-in date.
        # travel_checkin_element.clear()
        # travel_checkin_element.send_keys("{month:02d}/{day:02d}/{year}".format(
        #     month=int(check_in_dates["month"]),
        #     day=int(check_in_dates["day"]),
        #     year=check_in_dates["year"]
        # ))
        # # driver.get_screenshot_as_file("{0}_AFTER_CHECKIN_orbitz_navscraper.png".format(time.time()))

        # time.sleep(1)
        # # Set check-out date.
        # travel_checkout_element.clear()
        # travel_checkout_element.send_keys("{month:02d}/{day:02d}/{year}".format(
        #     month=int(check_out_dates["month"]),
        #     day=int(check_out_dates["day"]),
        #     year=check_out_dates["year"]
        # ))
        #
        # ########################################

        cin_date_css_selector, cin_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                day=int(check_in_dates["day"]),
                month=int(check_in_dates["month"]),
                year=check_in_dates["year"]
            )

        cout_date_css_selector, cout_next_month_css_selector = \
            self._get_datepicker_css_selectors(
                day=int(check_out_dates["day"]),
                month=int(check_out_dates["month"]),
                year=check_out_dates["year"]
            )

        # Select check-in date.
        travel_checkin_element.click()

        # Try to click the prev button (For Bugfixing)
        try:
            time.sleep(1)
            datepicker_prev = driver.find_element_by_css_selector(".datepicker-prev")
            datepicker_prev.click()
            time.sleep(1)
        except selenium.common.exceptions.ElementNotVisibleException, e:
            logging.debug("datepicker prev button not found - MOVE ON")


        datepicker_status = Navigation.set_date_in_basic_datepicker(
            driver=driver,
            date_css_selector=cin_date_css_selector,
            next_month_css_selector=cin_next_month_css_selector
        )

        if not datepicker_status:
            raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                cin_date_css_selector
            ))

        logging.debug("[Orbitz] Checkin date selected.")


        # Select check-out date.
        travel_checkout_element.click()
        time.sleep(1)

        datepicker_status = Navigation.set_date_in_basic_datepicker(
            driver=driver,
            date_css_selector=cout_date_css_selector,
            next_month_css_selector=cout_next_month_css_selector
        )

        if not datepicker_status:
            raise PDFuzzExceptions.DateNotFoundException("Unable to find the given date: '{}'".format(
                cout_date_css_selector
            ))


    # def _set_travel_dates_new_version(self, driver, check_in_dates, check_out_dates):

    #     check_in_element = find_element_by_id()
    #     check_in_element.click()

    #     Navigation.set_date_in_basic_datepicker(
    #         driver=driver,
    #         date_css_selector,
    #         next_month_css_selector
    #     )

    #     check_out_element = find_element_by_id()
    #     check_out_element.click()

    #     Navigation.set_date_in_basic_datepicker(
    #         driver=driver,
    #         date_css_selector,
    #         next_month_css_selector
    #     )


    def scrape_results(self, driver):
        ##
        #   Extract hotel names and prices from the website.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #

        if self.WEBSITE_MODE == "default":
            return self._default_scraper(driver=driver)

        elif self.WEBSITE_MODE == "alternative":
            return self._alternative_scraper(driver=driver)


    def _alternative_scraper(self, driver):

        # print("## Taking Screenshot")
        # driver.get_screenshot_as_file("{0}_orbitz_navscraper.png".format(time.time()))

        logging.debug("## Scraping Data - orbitz")
        hotel_results = []
        prev_result_length = 0
        extend_results_by_scroll_down = scrolled_down = False
        page_counter = 0
        result_pages_limit = 20

        while True:

            page_counter += 1
            # print("[DEBUG] Scraping page {0}".format(page_counter))
            # driver.get_screenshot_as_file("orbitz_RESULTS_PAGE_{0}_navscraper.png".format(page_counter))

            html_source = driver.page_source
            hotel_results_part = self._alternative_scraping_routine(page_source=html_source)
            hotel_results.extend(hotel_results_part)

            first_hotel_name = hotel_results_part[0]["name"]

            if scrolled_down and prev_result_length < len(hotel_results_part):
                logging.debug("[SCROLL] More results due to scrolling.")
                extend_results_by_scroll_down = True
                hotel_results = hotel_results_part

            prev_result_length = len(hotel_results_part)

            try:
                # Pagination: Next Page
                next_page_element = driver.find_element_by_css_selector("div.hotel-pagination > a.next")

                # Click on next page link
                next_page_element.click()

                try:
                    # Wait for results.
                    Navigation.wait_for_text_to_be_not_present_in_element(
                        driver=driver,
                        element_css_selector=".hotelSlimResultsModuleMod div.hotel-result:first-of-type h2.hotel-result-title > a",
                        old_text=first_hotel_name
                    )

                except selenium.common.exceptions.TimeoutException:
                    # If no results were found.
                    # End loop and return the current results.
                    break

            except selenium.common.exceptions.NoSuchElementException:
                # If no next page link was not found.

                if page_counter == 1 or (extend_results_by_scroll_down and page_counter < result_pages_limit):

                    logging.debug("[SCROLL] Scroll down for more results.")
                    driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
                    time.sleep(2.5)
                    scrolled_down = True

                    continue

                # End loop and return the current results.
                break

            except:
                # log unexpected errors while scraping
                #exc_type, exc_value = sys.exc_info()[:2]
                # print("Unexpected error: {}".format(sys.exc_info()[0]))
                logging.exception("Unexpected error:")

            if page_counter >= result_pages_limit:
                # If the limit is reached.
                # End loop and return the current results.
                break

        return hotel_results


    def _alternative_scraping_routine(self, page_source):
        ##
        #   ...
        #
        #   @param {string} page_source - ...
        #
        #   @return {list}
        #

        regex_price = re.compile("([0-9]+[ .])*[0-9]+")

        hotel_results = []
        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        # search_info_span = soup.select("#breadcrumb div:nth-of-type(5) span")
        # search_target_adults = search_info_span[0].contents[1].string.encode("utf-8").strip()
        # search_nights = search_info_span[0].contents[2].string.encode("utf-8").strip()
        # search_dates = search_info_span[0].contents[3].string.encode("utf-8").strip()

        # search_info = "{} {} {}".format(search_target_adults, search_nights, search_dates)

        hotellist_items = soup.select(".hotelSlimResultsModuleMod > div > div.hotel-result")

        for div in hotellist_items:
            hotelname = price_text = number_of_nights_text = None

            a_name = div.select("h2.hotel-result-title > a")
            if len(a_name) > 0:
                hotelname = a_name[0].string.encode("utf-8").strip()

            b_price = div.select(".primary-price strong")
            if len(b_price) > 0:
                price_text = b_price[0].string.encode("utf-8").strip()


            # per night info
            div_nights = div.select(".rate-choice-msg")
            if len(div_nights) > 0:
                number_of_nights_text = div_nights[0].string.encode("utf-8").strip()

            if hotelname != None:

                number_of_nights = 1

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

                hotel_results.append({
                    "name" : hotelname,
                    "price" : price,
                    "currency" : currency_code,
                    "price_norm" : price_norm,
                    "number_of_nights" : number_of_nights,
                    "access_time" : time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()),
                    "debug" : {
                        "price_text" : price_text,
                        "number_of_nights_text" : number_of_nights_text,
                    },

                })

        return hotel_results


    def _default_scraper(self, driver):

        # print("## Taking Screenshot")
        # driver.get_screenshot_as_file("{0}_orbitz_navscraper.png".format(time.time()))

        logging.debug("## Scraping Data - orbitz")
        hotel_results = []
        page_counter = 0
        result_pages_limit = 20

        while True:

            page_counter += 1
            # print("[DEBUG] Scraping page {0}".format(page_counter))
            # driver.get_screenshot_as_file("{0}_orbitz_RESULTS_PAGE_{1}_navscraper.png".format(time.time(), page_counter))

            html_source = driver.page_source
            hotel_results_part = self._default_scraping_routine(page_source=html_source)
            hotel_results.extend(hotel_results_part)

            if len(hotel_results_part) > 1:
                second_hotel_name = hotel_results_part[1]["name"]
            else:
                second_hotel_name = ""

            try:
                # Pagination: Next Page
                next_page_element = driver.find_element_by_css_selector("button.pagination-next")

                # Click on next page link
                next_page_element.click()

                try:
                    # Wait for results.
                    Navigation.wait_for_text_to_be_not_present_in_element(
                        driver=driver,
                        element_css_selector="#resultsContainer .hotel.listing:nth-of-type(2) .hotelTitle > .hotelName",
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
                #exc_type, exc_value = sys.exc_info()[:2]
                # print("Unexpected error: {}".format(sys.exc_info()[0]))
                logging.exception("Unexpected error:")

            if page_counter >= result_pages_limit:
                # If the limit is reached.
                # End loop and return the current results.
                break

        # driver.get_screenshot_as_file("{0}_orbitz_SCRAPER_END_{1}_navscraper.png".format(time.time(), page_counter))

        return hotel_results


    def _default_scraping_routine(self, page_source):
        ##
        #   ...
        #
        #   @param {string} page_source - ...
        #
        #   @return {list}
        #

        hotel_results = []
        soup = bs4.BeautifulSoup(page_source, 'html.parser')

        # search_info_span = soup.select("#breadcrumb div:nth-of-type(5) span")
        # search_target_adults = search_info_span[0].contents[1].string.encode("utf-8").strip()
        # search_nights = search_info_span[0].contents[2].string.encode("utf-8").strip()
        # search_dates = search_info_span[0].contents[3].string.encode("utf-8").strip()

        # search_info = "{} {} {}".format(search_target_adults, search_nights, search_dates)

        hotellist_items = soup.select("#resultsContainer .hotel.listing")

        for div in hotellist_items:
            hotelname = price_text = number_of_nights_text = rating_value = \
            rating_unit = location = None

            # Extract the name of the hotel.
            strong_name = div.select(".hotelTitle > .hotelName")
            if len(strong_name) > 0:
                hotelname = strong_name[0].string.encode("utf-8").strip()

            location_tag = div.select(".hotel-info .neighborhood")
            if len(location_tag) > 0:
                location = list(location_tag[0].strings)[0].encode("utf-8").strip()

            # Extract the number of stars.
            span_stars = div.select("li.starRating strong.star-rating > span:nth-of-type(2)")
            if len(span_stars) > 0:
                star_classes = span_stars[0].get("class")
                for star_class in star_classes:
                    if "icon-stars" in star_class:
                        rating_value = float(star_class[-3:].replace("-", "."))
                        rating_unit  = "stars"
                        break
            else:
                rating_unit  = None
                rating_value = 0.0

            # Extract the price of the hotel.
            price_tag = div.select(".hotel-price .actualPrice")
            if len(price_tag) > 0:
                price_text = list(price_tag[0].strings)[-1].encode("utf-8").strip()

            # Extract the number of nights, the price stands for.
            li_nights = div.select("li.avgPerNight.priceType")
            if len(li_nights) > 0:
                number_of_nights_text = list(li_nights[0].strings)[-1].encode("utf-8").strip()

            if hotelname is not None:

                number_of_nights = 1

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
                    },

                })

        return hotel_results


    def _set_room_in_overlay(self, driver, room_index, number_of_adults):
        ##
        #   Fill out the form for a defined room. The number of adults is set
        #   in the input field using the arrow_up key.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {int} room_index - Defines the current room.
        #   @param {int} number_of_adults - Defines number of adults for this room.
        #

        # get input element
        number_adults_element = \
            driver.find_element_by_name("adult{room_index}".format(room_index=room_index))
        number_adults_element.clear()

        # driver.get_screenshot_as_file("{0}_ADULTS_CLEARED_orbitz_navscraper.png".format(time.time()))

        # Determine the number of incrementations to reach the correct number of adults.
        click_counter = int(number_of_adults) - 1
        while click_counter > 0:
            # Increment the number of adults, by using the arrow_up key.
            number_adults_element.send_keys(Keys.ARROW_UP)
            click_counter -= 1

        # driver.get_screenshot_as_file("{0}_ADULTS_FILLED_orbitz_navscraper.png".format(time.time()))


    def _set_room_in_start_page(self, driver, room_index, number_of_adults):
        ##
        #   Fill out the form for a defined room. The number of adults is set
        #   in the combobox.
        #
        #   @param {selenium.webdriver} driver - Instance of a webdriver.
        #   @param {int} room_index - Defines the current room.
        #   @param {int} number_of_adults - Defines number of adults for this room.
        #

        # get input element
        number_adults_select = Select(driver.find_element_by_name("hotel.rooms[{room_index}].adlts".format(room_index=room_index)))
        number_adults_select.select_by_value(str(number_of_adults))


    def _set_rooms(self, driver, room_counter, number_of_rooms, room_size, add_room_link, set_room_function):

        # Setup rooms.
        if int(number_of_rooms) > 0:
            rooms_remaining_counter = int(number_of_rooms)

            while rooms_remaining_counter > 0:

                if room_counter[0] > 0:
                    # Add a new room if more than one room is needed.
                    add_room_link.click()
                    time.sleep(1.5)

                # Setup a single room.
                set_room_function(
                    driver=driver,
                    room_index=room_counter[0],
                    number_of_adults=room_size
                )

                rooms_remaining_counter -= 1
                room_counter[0] += 1


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