#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   This module offers methods to simplify the navigation process.
#
#   @date   13.01.2016
#   @author Nicolai Wilkop
#


import time
import logging

import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pdfuzz.selenium_extension import expected_conditions as MyEC


def set_date_in_basic_datepicker(driver, date_css_selector, next_month_css_selector, delay_before_date_click=2.5):
    ##
    #   Set up the date for checkin or checkout and passes back the state
    #   of success of failure.
    #
    #   @param {selenium.webdriver} driver - Webdriver instance.
    #   @param {string} date_css_selector - CSS selector for the date within
    #   the datepicker.
    #   @param {string} next_month_css_selector - CSS selector to go to the
    #   next month, if the date is not visible in the current view of the
    #   datepicker.
    #   @param {float} delay_before_date_click - Delay in seconds to wait before
    #   trying to select the date. Default: 2.5sec
    #
    #   @return {bool} status
    #

    status = False

    while True:
        # Delay for datepicker to appear.
        time.sleep(delay_before_date_click)
        try:
            date_element = driver.find_element_by_css_selector(date_css_selector)
            date_element.click()

            status = True
            break

        except (selenium.common.exceptions.NoSuchElementException, \
            selenium.common.exceptions.ElementNotVisibleException):

            try:

                if next_month_css_selector is None:
                    raise

                next_month_element = driver.find_element_by_css_selector(next_month_css_selector)
                next_month_element.click()
                continue

            except:

                print("[DEBUG] Date not found.")
                logging.exception("Date not found in datepicker: '{0}'".format(date_css_selector))

                status = False
                break

    return status


def wait_for_text_to_be_not_present_in_element(driver, element_css_selector, old_text, timeout=30):
    ##
    #   Wait for a new text in an element which is spcified by a CSS selector.
    #
    #   @param {selenium.webdriver} driver - Webdriver instance.
    #   @param {string} element_css_selector - CSS selector for the element
    #   of interest.
    #   @param {string} old_text - Text that should not be present anymore.
    #   @param {int} timeout - Timeout for the waiting process.
    #
    #   @return {element}
    #
    #   @raise selenium.common.exceptions.TimeoutException
    #

    element = WebDriverWait(driver, timeout).until(
        MyEC.text_to_be_not_present_in_element((By.CSS_SELECTOR, element_css_selector), old_text)
    )

    return element


def wait_for_the_presence_of_element(driver, element_css_selector, timeout=30):
    ##
    #   Wait for the presence of an element which is specified by a CSS selector.
    #
    #   @param {selenium.webdriver} driver - Webdriver instance.
    #   @param {string} element_css_selector - CSS selector for the element
    #   of interest.
    #   @param {int} timeout - Timeout for the waiting process.
    #
    #   @return {element}
    #
    #   @raise selenium.common.exceptions.TimeoutException
    #

    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, element_css_selector))
    )

    return element
