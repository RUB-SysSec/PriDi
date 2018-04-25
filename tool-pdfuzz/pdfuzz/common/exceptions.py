#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   This module contains all the custom Exceptions that can occure in the
#   code of PDFuzz.
#
#   @date   13.01.2016
#   @author Nicolai Wilkop
#


class DateNotFoundException(Exception):
    pass


class ScanWithFingerprintNotCompleteException(Exception):
    pass


class NavScraperException(Exception):

    def __init__(self, message, target_website, country, fp_id, error_msg):

        # Call the base class constructor with the parameters it needs
        super(NavScraperException, self).__init__(message)

        # Store error data.
        self.target_website = target_website
        self.country = country
        self.fp_id = fp_id
        self.error_msg = error_msg


class NavigationFailedException(NavScraperException):

    def __init__(self, message, target_website, country, fp_id):

        # Store error message.
        error_msg = "NAV_ERROR"

        # Call the base class constructor with the parameters it needs
        super(NavigationFailedException, self) \
            .__init__(message, target_website, country, fp_id, error_msg)


class ScrapingErrorException(NavScraperException):

    def __init__(self, message, target_website, country, fp_id):

        # Store error message.
        error_msg = "SCRAPING_ERROR"

        # Call the base class constructor with the parameters it needs
        super(ScrapingErrorException, self) \
            .__init__(message, target_website, country, fp_id, error_msg)


class SmallResultsException(NavScraperException):

    def __init__(self, message, target_website, country, fp_id):

        # Store error message.
        error_msg = "SMALL_RESULTS"

        # Call the base class constructor with the parameters it needs
        super(SmallResultsException, self) \
            .__init__(message, target_website, country, fp_id, error_msg)


class NoResultsException(NavScraperException):

    def __init__(self, message, target_website, country, fp_id):

        # Store error message.
        error_msg = "NO_RESULTS"

        # Call the base class constructor with the parameters it needs
        super(NoResultsException, self) \
            .__init__(message, target_website, country, fp_id, error_msg)


class NetworkErrorException(NavScraperException):

    def __init__(self, message, target_website, country, fp_id):

        # Store error message.
        error_msg = "NETWORK_ERROR"

        # Call the base class constructor with the parameters it needs
        super(NoResultsException, self) \
            .__init__(message, target_website, country, fp_id, error_msg)


class PageLoadTimeoutException(Exception):
    pass
