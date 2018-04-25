#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   ...
#
#   @date   05.11.2015
#   @author Nicolai Wilkop
#


from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC


class text_to_be_not_present_in_element(object):
    """ An expectation for checking if the given text is not present in the
    specified element.
    locator, text
    """
    def __init__(self, locator, text_):
        self.locator = locator
        self.text = text_

    def __call__(self, driver):
        try:
            element_text = EC._find_element(driver, self.locator).text.encode("utf-8")
            return self.text not in element_text
        except StaleElementReferenceException:
            return False