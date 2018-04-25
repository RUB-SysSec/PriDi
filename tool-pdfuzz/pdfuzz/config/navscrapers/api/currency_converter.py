#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   This module offers methods to do currency conversions.
#
#   @date   30.11.2015
#   @author Nicolai Wilkop
#


import re
import urllib2
import csv
import requests

EXCHANGE_RATES = {}
REGEX_PRICE = re.compile("([0-9]+[.])*[0-9]+")



def get_exchange_rate_yahoo(src_currency_code, dest_currency_code="EUR"):
    ##
    #   This function returns the exchange rate for the passed currencies.
    #   Source for this rate is the website: https://finance.yahoo.com
    #
    #   @param {string} src_currency_code - Code (i.e. USD) for the source currency.
    #   @param {string} dest_currency_code - Code (i.e. EUR) for the source currency.
    #
    #   @return {float} exchange_rate
    #

    url = "http://download.finance.yahoo.com/d/quotes.csv?s={src_currency_code}{dest_currency_code}=X&f=l1".format(
        src_currency_code=src_currency_code, dest_currency_code=dest_currency_code)

    response = urllib2.urlopen(url)
    csv_reader = csv.reader(response)
    exchange_rate = next(csv_reader)[0]

    # API returns N/A if the requested exchange rate can not be found.
    if exchange_rate == "N/A":
        exchange_rate = None
    # API returns 0 if the exchange rate is smaller than 4 digits behind the comma.
    elif float(exchange_rate) == 0:
        exchange_rate = None
    else:
        exchange_rate = float(exchange_rate)
    
    return exchange_rate


def get_exchange_rate_appspot(src_currency_code, dest_currency_code="EUR"):
    ##
    #   This function returns the exchange rate for the passed currencies.
    #   Source for this rate is the website: https://currency-api.appspot.com
    #
    #   @param {string} src_currency_code - Code (i.e. USD) for the source currency.
    #   @param {string} dest_currency_code - Code (i.e. EUR) for the source currency.
    #
    #   @return {float} exchange_rate
    #

    url = "https://currency-api.appspot.com/api/{src_currency_code}/{dest_currency_code}.json".format(
        src_currency_code=src_currency_code, dest_currency_code=dest_currency_code)

    try:
        response = requests.get(url)
        exchange_rate = response.json()["rate"]

    except:
        exchange_rate = None

    if not exchange_rate:
        # If exchange rate can not be found. API returns false.
        exchange_rate = None

    return exchange_rate


def get_exchange_rate(src_currency_code, dest_currency_code="EUR"):
    ##
    #   This function returns the exchange rate for the passed currencies.
    #   This function is based on multiple exchange rate APIs.
    #
    #   @param {string} src_currency_code - Code (i.e. USD) for the source currency.
    #   @param {string} dest_currency_code - Code (i.e. EUR) for the source currency.
    #
    #   @return {float} exchange_rate
    #

    # Get exchange rate from appspot currency API
    exchange_rate = get_exchange_rate_appspot(src_currency_code, dest_currency_code)

    if exchange_rate is None:
        # Get exchange rate from Yahoo finance API
        exchange_rate = get_exchange_rate_yahoo(src_currency_code, dest_currency_code)

    return exchange_rate


def get_currency_code_of_sign(currency_sign="€"):
    ##
    #   Determine the corresponding currency code for the input sign of the currency.
    #
    #   @param {string} currency_sign - The sign or code which represents the currency
    #   of the products price.
    #
    #   @return {string} The corresponding currency code for the input sign.
    #

    if currency_sign is None:
        return None

    if "€" in currency_sign:
        currency_code = "EUR"
    elif "R$" in currency_sign:
        currency_code = "BRL"
    elif "S$" in currency_sign:
        currency_code = "SGD"
    elif "AR$" in currency_sign:
        currency_code = "ARS"
    elif "CL$" in currency_sign:
        currency_code = "CLP"
    elif "HK$" in currency_sign:
        currency_code = "HKD"
    elif "$CAD" in currency_sign:
        currency_code = "CAD"
    elif "$" in currency_sign or "US$" in currency_sign:
        currency_code = "USD"
    elif "£" in currency_sign:
        currency_code = "GBP"
    elif "¥" in currency_sign or "￥" in currency_sign:
        currency_code = "JPY"
    elif "Rs." in currency_sign or "Rs" in currency_sign:
        currency_code = "INR"
    elif "Rp" in currency_sign:
        currency_code = "IDR"
    elif "lei" in currency_sign:
        currency_code = "RON"
    elif "₪" in currency_sign:
        currency_code = "ILS"
    elif "Kč" in currency_sign:
        currency_code = "CZK"
    elif "zł" in currency_sign:
        currency_code = "PLN"
    elif "₫" in currency_sign:
        currency_code = "VND"
    elif "₴" in currency_sign:
        currency_code = "UAH"
    elif "₩" in currency_sign or "￦" in currency_sign:
        currency_code = "KRW"
    elif "руб" in currency_sign or "₽" in currency_sign:
        currency_code = "RUB"
    else:
        currency_code = currency_sign

    return currency_code


def get_normalized_price(price, currency_code):
    ##
    #   Calculate the price in euro. For this purpose the exchange rate is requested.
    #
    #   @param {float} price - Price of the product.
    #   @param {string} currency_code - Currency code of the price.
    #
    #   @return {float}
    #

    if price is None or currency_code is None:
        return None

    if currency_code != "EUR":
        # If currency is not euro, it needs to be normalized.
        if not currency_code in EXCHANGE_RATES:
            # Determine exchange rate for current currency to euro.
            # Save the rate in the EXCHANGE_RATES dictionary to
            # improve the performance.
            EXCHANGE_RATES[currency_code] = \
                get_exchange_rate(src_currency_code=currency_code)

        # Check if exchange rate is None
        if EXCHANGE_RATES[currency_code] is None:
            price_norm = None

        else:
            # Calculate the euro value.
            price_norm = round(price * EXCHANGE_RATES[currency_code], 2)

    else:
        # If currency is euro then use the price as the normalized one.
        price_norm = price

    return price_norm


def split_price_and_currency(price_text):
    ##
    #   Split the price from the currency and passes both of them back.
    #
    #   @param {string} price_text - The string which holds the price and the currency.
    #
    #   @return {string} price, {sting} currency
    #

    if price_text is None:
        return None, None

    price_text = price_text.replace(" ", "") \
                           .replace("\xc2\xa0", "") \
                           .replace(",", ".") \
                           .strip()

    parts = price_text.split(".")
    if len(filter(lambda x: x in "1234567890", parts[-1])) > 2 or len(parts) == 1:
        price_text = price_text.replace(".", "")
    else:
        price_text = "{0}.{1}".format("".join(parts[:-1]), parts[-1])

    match = REGEX_PRICE.search(price_text)
    price = match.group(0).strip()
    currency = price_text.replace(price, "").strip()

    return float(price), currency
