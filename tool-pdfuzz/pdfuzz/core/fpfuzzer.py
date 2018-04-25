#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   This module contains all the methods to manipulate the fingerprint in an
#   WebDriver session.
#
#   @date   07.10.2015
#   @author Nicolai Wilkop
#

import sys
import logging
import ast
import jinja2

from jsmin import jsmin
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import pdfuzz.config.config as cfg


def get_fingerprints(db_manager, timezone_offset):
    ##
    #   Generator function to receive features of a fingerprint. These features
    #   will be prepared to use them as input for the code-injection template.
    #
    #   @param {pdfuzz.core.db_connection.DBManager} db_manager - Instance of
    #   the database management class.
    #
    #   @return {dict}
    #

    pref_navigator = "navigator."
    pref_screen = "screen."
    pref_httpHeader = "httpHeader."

    for raw_fingerprint in db_manager.get_fingerprints():

        # if raw_fingerprint["id"] not in [3]:
        #     continue

        try:

            fingerprint = {
                "id": raw_fingerprint["id"],
                "navigator_obj": {},
                "screen_obj": {

                    "availTop": 0,
                    "width": 1280,
                    "availWidth": 1280,
                    "availHeight": 980,
                    "height": 1024,
                    "colorDepth": 24,
                    "availLeft": 0,
                    "pixelDepth": 24,
                    "top": 0,
                    "left": 0,

                },
                "timezoneoffset": timezone_offset,
                "httpHeader": {},
            }

            for key in raw_fingerprint:

                if raw_fingerprint[key] is None:
                    # If no value exists for the current feature. Skip it, to
                    # use the default value of PhantomJS.
                    continue

                # Check if the current key has the leading navigator prefix.
                if key.startswith(pref_navigator):
                    attribute = key[len(pref_navigator):]

                    if "plugins" in attribute:
                        # Using a set to remove duplicate plugins.
                        js_new_plugin_list = set()
                        plugin_list = ast.literal_eval(raw_fingerprint[key])

                        for plugin_info in plugin_list:
                            # Create JavaScript code that will be used by
                            # the code-injection template to manipulate the
                            # plugin list.
                            js_new_plugin_list.add(
                                "new Plugin('{plugin_name}', '{plugin_description}', '{plugin_filename}', '{plugin_version}')".format(
                                    plugin_name=plugin_info.get("n", ""),
                                    plugin_description=plugin_info.get(
                                        "d", ""),
                                    plugin_filename=plugin_info.get("f", ""),
                                    plugin_version=plugin_info.get("v", ""),
                                )
                            )

                        # Save the list of plugins in the new fingerprint.
                        fingerprint["plugins"] = list(js_new_plugin_list)

                    elif "mimeTypes" in attribute:
                        # Using a set to remove duplicate mimeTypes
                        js_new_mimetypes_list = set()
                        mimetypes_list = ast.literal_eval(raw_fingerprint[key])

                        for mimetype_info in mimetypes_list:
                            # Create JavaScript code that will be used within
                            # the code-injection template to manipulate the
                            # mimeTypes Array.
                            js_new_mimetypes_list.add(
                                "new MimeType('{mimetype_type}', '{mimetype_suffixes}', '{mimetype_description}')".format(
                                    mimetype_type=mimetype_info.get("n", ""),
                                    mimetype_suffixes=mimetype_info.get(
                                        "f", ""),
                                    mimetype_description=mimetype_info.get(
                                        "d", "")
                                )
                            )

                        # Save the list of mimetypes in the new fingerprint.
                        fingerprint["mimetypes"] = list(js_new_mimetypes_list)

                    else:
                        # Use the value of the raw fingerprint by using the key
                        # without the prefix as the key for the fingerprint.
                        # navigator.userAgent -> userAgent
                        fingerprint["navigator_obj"][
                            attribute] = raw_fingerprint[key]

                # Check if the current key has the leading screen prefix.
                elif key.startswith(pref_screen):
                    attribute = key[len(pref_screen):]

                    # Use the value of the raw fingerprint by using the key
                    # without the prefix as the key for the fingerprint.
                    # screen.width -> width
                    fingerprint["screen_obj"][attribute] = raw_fingerprint[key]

                # Check if the current key has the leading httpHeader prefix.
                elif key.startswith(pref_httpHeader):
                    attribute = key[len(pref_httpHeader):]

                    if attribute.startswith("accept"):
                        # fix the underscore of MySQL column names.
                        attribute = attribute.replace("_", "-")

                    # Use the value of the raw fingerprint by using the key
                    # without the prefix as the key for the fingerprint.
                    # httpHeader.accept -> accept
                    fingerprint["httpHeader"][attribute] = raw_fingerprint[key]

                # Fallback if the key can not be handled.
                else:
                    if key != "id" and \
                            key not in cfg.IGNORED_FINGERPRINT_TABLE_COLUMNS:
                        # Log the key which can not be handled.
                        logging.warning(
                            "Key has no valid format: '{key}'".format(key=key))

        except:
            # Catches for example SyntaxError and ValueError.
            exc_type, exc_value = sys.exc_info()[:2]
            logging.warning("Error in Fingerprint with ID ({id}): {error_type} <msg '{error_msg}'>".format(
                error_type=exc_type, error_msg=exc_value, id=raw_fingerprint["id"]))

            logging.info("Fingerprint ({id}) skipped!".format(
                id=raw_fingerprint["id"]))

            # Skip current fingerprint.
            continue

        yield fingerprint


def create_inject_js(fingerprint):
    ##
    #   By use of the inject_template.js the javascript injection code is
    #   created.
    #   The generated fingerprint is passed to the template.
    #
    #   @param {dict} fingerprint - The fingerprint contains navigator_obj,
    #   screen_obj, timezoneoffset.
    #   @return {string} javascript code to manipulate the fingerprint.
    #

    # Get template to init the template engine via the PackageLoader of jinja2.
    template = jinja2.Environment(
        loader=jinja2.PackageLoader(
            "pdfuzz.config",
            "templates"
        )
    ).get_template("inject_template.js")

    # Reder template with fingerprint information.
    inject_js = template.render(fingerprint)

    # minify js code.
    inject_js_min = jsmin(inject_js)

    # Pass back the injection javascript code.
    return inject_js_min


def create_dcap(fingerprint):
    ##
    #   Create the DesiredCapabilities for the PhantomJS instance.
    #   General settings for the behavior of the browser are made here.
    #
    #   @param {dict} fingerprint - The fingerprint contains navigator_obj,
    #   screen_obj, timezoneoffset.
    #   @return {selenium.webdriver.common.desired_capabilities.DesiredCapabilities}
    #

    # Transform DesiredCapabilities profile to dictionary.
    dcap_profile = DesiredCapabilities.PHANTOMJS
    dcap = dict(dcap_profile)

    # Change userAgent in dcap.
    dcap = changeUserAgent(
        dcap=dcap,
        userAgent=fingerprint["navigator_obj"]["userAgent"]
    )

    # Change the viewportSize
    dcap = changeViewportSize(
        dcap=dcap,
        width=fingerprint["screen_obj"]["width"],
        height=fingerprint["screen_obj"]["height"]
    )

    # Change the custom headers in the dcap.
    dcap = changeHttpHeader(
        dcap=dcap,
        httpHeader=fingerprint["httpHeader"]
    )

    # Set inject JS code.
    code = create_inject_js(fingerprint)
    dcap = set_onInitialized_jsInject_code(
        dcap=dcap,
        jsInject_code=code
    )

    return dcap


def changeUserAgent(dcap, userAgent):
    ##
    #   Extend the dcap structure with the userAgent string so that the
    #   userAgent is set correctly in the http header.
    #
    #   @param {dict} dcap - Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #   @param {string} userAgent - UserAgent value for the PhantomJS instance.
    #
    #   @return {dict} Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #

    dcap["phantomjs.page.settings.userAgent"] = userAgent

    return dcap


def changeHttpHeader(dcap, httpHeader):
    ##
    #   Changing the http header of the PhantomJS instance.
    #
    #   @param {dict} dcap - Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #   @param {dict} httpHeader - Dictionary of http header values. For now
    #   the only needed key ist `accept-language`.
    #
    #   @return {dict} Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #

    # dcap["phantomjs.page.customHeaders.Accept"] = \
    # httpHeader["accept"] # ERROR
    # dcap["phantomjs.page.customHeaders.Accept-Encoding"] = \
    # httpHeader["accept-encoding"] # ERROR
    dcap["phantomjs.page.customHeaders.Accept-Language"] = \
        httpHeader["accept-language"]

    return dcap


def set_onInitialized_jsInject_code(dcap, jsInject_code):
    ##
    #   Add the desired capability to inject javascript code after
    #   initialization of a website.
    #
    #   @param {dict} dcap - Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #   @param {string} jsInject_code - JavaScript code that is to be injected
    #   in the phantom.page object after initialization of the current website.
    #
    #   @return {dict} Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #

    dcap["phantomjs.page.onInitialized.jsInject"] = jsInject_code

    return dcap


def changeViewportSize(dcap, width, height):
    ##
    #   Changes the viewport size in the PhantomJS enviroment. This is done via
    #   the selenium API call set_window_size.
    #
    #   @param {dict} dcap - Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #   @param {int} width - Screen width of the headless browser instance.
    #   @param {int} height - Screen height of the headless browser instance.
    #
    #   @return {dict} Dictionary representation of DesiredCapabilities
    #   object from selenium package.
    #

    dcap["phantomjs.page.viewportSize.width"] = width
    dcap["phantomjs.page.viewportSize.height"] = height

    return dcap
