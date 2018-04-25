#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   In this module ...
#
#   @date   10.10.2015
#   @author Nicolai Wilkop
#

import atexit
import time
import logging
import multiprocessing
import urllib2
import pprint

import pdfuzz.common.exceptions as PDFuzzExceptions
import pdfuzz.config.config as cfg
import pdfuzz.core.phantomconnection as phanconn
import pdfuzz.core.fpfuzzer as fpfuzzer
import pdfuzz.core.db_connection as db_connection


def start_fuzzing(cl_settings, search_parameters_id):
    ##
    #   The function represents the main-routine of the fuzzer.
    #
    #   @param {argparse.results} cl_settings - Object of parsed parameters
    #   from the commandline.
    #   @param {int} search_parameters_id - Database id of the search
    #   parameters entry.
    #

    # ----- INIT Fuzzing Run -----
    print("[*] Initialization")
    logging.info("Initialization")

    # Get list of navscraper from the config file.
    navscraper_list = cfg.NAVSCRAPERS

    # Init the webdriver manager.
    phwd_manager = phanconn.PhantomWebdriverManager(
        webdriver_details_list=cfg.WEBDRIVERS_SETTINGS
    )

    # Start all webdriver server that are defined in the config file.
    print("[**] Starting WebDriver Server")
    logging.debug("[**] Starting WebDriver Server")

    phwd_manager.start_all_webdriver_instances()

    print("[**] Waiting for WebDriver Server")
    logging.debug("[**] Waiting for WebDriver Server")

    time.sleep(5)

    # Register atexit routine to shutdown all webdriver server.
    print("[**] Register Shutdown Cleanup")
    logging.debug("[**] Register Shutdown Cleanup")

    atexit.register(phwd_manager.shutdown_all_webdriver_server)

    # Get a list of phantom wrappers to communicate with the webdriver servers.
    phantom_wrapper_list = phwd_manager.get_phantom_wrappers()

    # ----- MAIN Routine -----
    print("[*] Start Fuzzing..")
    logging.info("Start Fuzzing..")

    worker_list = []

    # Iterate over all phantom wrapper which represent the different
    # webdriver server.
    for phantom_wrapper_info in phantom_wrapper_list["local"]:

        # Crate/Start a new process for every webdriver server in the list.
        # The name of the process is the country of the geolocation.
        process = multiprocessing.Process(
            name=phantom_wrapper_info["country"] + " (local)",
            target=inner_fuzzing_local,
            args=(phantom_wrapper_info, navscraper_list,
                  search_parameters_id, cl_settings, phwd_manager,)
        )
        worker_list.append(process)
        process.start()

    # Iterate over all phantom wrappers that are using a VM connection and
    # create a process for each VM.
    for index, phantom_wrapper_set in enumerate(phantom_wrapper_list["vm"]):

        start_delay = index * 2
        # Crate/Start a new process for every set of webdriver servers in the
        # list. The name of the process is the country of the geolocation.
        process = multiprocessing.Process(
            name=phantom_wrapper_set[0]["country"] + " (vm_master)",
            target=vm_master,
            args=(phantom_wrapper_set, navscraper_list,
                  search_parameters_id, cl_settings, start_delay,)
        )
        worker_list.append(process)
        process.start()

    # Waiting for all processes.
    for process in worker_list:
        process.join()

    print("[*] Finished")
    logging.info("[*] Finished")


def inner_fuzzing_local(phantom_wrapper_info, navscraper_list, search_parameters_id, cl_settings, phwd_manager):
    ##
    #   Main fuzzing routine that can be started in multiple threads/processes.
    #   It iterates over the several variables (NavScrapers, Fingerprints),
    #   gets the data from the websites and stores it in the database.
    #
    #   @param {} phantom_wrapper_info - ...
    #   @param {list} navscraper_list - List that holds the instances of the
    #   various NavScrapers.
    #   @param {int} search_parameters_id - Database id of the search
    #   parameters entry.
    #   @param {argparse.results} cl_settings - Object of parsed parameters
    #   from the commandline.
    #   @param {PhantomWebdriverManager} phwd_manager - ...
    #

    # Store the type of the target websites in a local variable.
    target_website_type = cl_settings.target_website_type

    # Prepare the proxy address string.
    if phantom_wrapper_info["proxy_ip"] is not None and \
            phantom_wrapper_info["proxy_port"] is not None:
        proxy_address = "{ip}:{port}".format(
            ip=phantom_wrapper_info["proxy_ip"],
            port=phantom_wrapper_info["proxy_port"]
        )
    else:
        proxy_address = None

    try:
        # Get phantomwrapper object
        phw = phantom_wrapper_info["phantomwrapper"]

        # Init database connection
        db_manager = db_connection.DBManager(
            settings=cfg.MYSQL,
            website_type=target_website_type,
            result_table_name=cl_settings.result_table_name
        )

        # Iterate over navscrapers.
        # Means that this iterated also over the target websites.
        for navscraper_class in navscraper_list:

            # Skip every NavScraper that does not have the actual page type.
            if navscraper_class.PAGE_TYPE != target_website_type:
                continue

            # Get a new instance of the current NavScraper.
            navscraper = navscraper_class()

            logging.info("Testing: {0}".format(navscraper.ENTRY_URI))

            # Get the initial timeout limit from the config file.
            timeout_limit = cfg.TIMEOUT_LIMIT

            # Determine the input parameters for the navigation of the
            # NavScraper.
            navigation_search_parameters = \
                cfg.SEARCH_PARAMETERS.get(target_website_type, {})

            # Iterate over all fingerprints that are to be tested.
            for fingerprint in fpfuzzer.get_fingerprints(
                    db_manager=db_manager,
                    timezone_offset=phantom_wrapper_info["timezone_offset"]):

                scan_successful = False
                timeout_occurred = False
                retry_count = 0
                while not scan_successful:

                    try:
                        # Run the navigation and scraping routine of the
                        # current NavScraper with the actual fingerprint.
                        results = gather_information_with_fingerprint(
                            navscraper=navscraper,
                            fingerprint=fingerprint,
                            phw=phw,
                            navigation_search_parameters=navigation_search_parameters
                        )

                        # Save results in database.
                        store_results(
                            db_manager=db_manager,
                            results=results,
                            worker_info={
                                "name": multiprocessing.current_process().name,
                                "timezone_offset": phantom_wrapper_info["timezone_offset"],
                                "proxy_address": proxy_address,
                            },
                            fp_id=fingerprint["id"],
                            target_website=navscraper.ENTRY_URI,
                            search_parameters_id=search_parameters_id
                        )

                        # Mark scan with current FP as successful.
                        scan_successful = True

                        # Reset timeout limit.
                        timeout_limit = cfg.TIMEOUT_LIMIT

                    except PDFuzzExceptions.NavScraperException as e:

                        if isinstance(e, PDFuzzExceptions.NetworkErrorException):
                            logging.warning("Restarting WebDriver after crash.")
                            # Restart the PhantomJS WebDriver and go on.
                            phw = phwd_manager.restart_webdriver(phantom_wrapper_info)

                        elif retry_count == cfg.FP_RETRY:
                            log_scan_not_completed_error(
                                driver=phw.get_driver(),
                                exception=e
                            )
                            break

                        # Increment the retry counter.
                        retry_count += 1
                        print("# {retry_count}. retry for {website} with FP {fp_id}".format(
                            retry_count=retry_count,
                            website=navscraper.ENTRY_URI,
                            fp_id=fingerprint["id"]
                        ))
                        logging.info("{retry_count}. retry for {website} with FP {fp_id}".format(
                            retry_count=retry_count,
                            website=navscraper.ENTRY_URI,
                            fp_id=fingerprint["id"]
                        ))

                    except PDFuzzExceptions.PageLoadTimeoutException as e:

                        if retry_count == cfg.FP_RETRY:
                            break

                        # Increment the retry counter.
                        retry_count += 1

                        if timeout_limit > 0 and not timeout_occurred:
                            timeout_limit -= 1
                            timeout_occurred = True
                            logging.info("{timeout_limit} timouts remaining for {website}".format(
                                timeout_limit=timeout_limit,
                                website=navscraper.ENTRY_URI
                            ))

                    finally:
                        # Disconnect from PhantomJS WebDriver server.
                        phw.disconnect()

                if timeout_limit == 0:
                    # If the timeout limit reached zero, move on to the
                    # next website.
                    logging.info("Skip fuzzing of {website} after {max_timeouts} timeouts.".format(
                        website=navscraper.ENTRY_URI,
                        max_timeouts=cfg.TIMEOUT_LIMIT
                    ))
                    break

                # Anti DDoS delay
                logging.debug("Waiting for {sec} seconds before using the next fingerprint.".format(
                    sec=cfg.ANTI_DDOS_DELAY_SECONDS))
                time.sleep(cfg.ANTI_DDOS_DELAY_SECONDS)

        # If the worker is finished, write it to the log and console.
        logging.debug("Shutdown worker {}".format(
            multiprocessing.current_process().name))
        print("Shutdown worker {}".format(
            multiprocessing.current_process().name))

    except:

        logging.exception("Processname: {name}".format(
            name=multiprocessing.current_process().name))

        logging.debug("Worker {} crashed".format(
            multiprocessing.current_process().name))
        print("Worker {} crashed".format(
            multiprocessing.current_process().name))

    finally:

        # close database connection.
        db_manager.close()
        return


def get_chunks(the_list, num_of_sub_lists):

    chunks = [[] for x in range(num_of_sub_lists)]

    for index, item in enumerate(the_list):
        chunks[index % num_of_sub_lists].append(item)

    return chunks


def vm_master(phantom_wrapper_set, navscraper_list, search_parameters_id, cl_settings, start_delay):
    ##
    #   The master starts a subprocess for each WebDriver instance that is
    #   running on the VM.
    #
    #   @param {} phantom_wrapper_set - ...
    #   @param {list} navscraper_list - List that holds the instances of the
    #   various NavScrapers.
    #   @param {int} search_parameters_id - Database id of the search parameters
    #   entry.
    #   @param {argparse.results} cl_settings - Object of parsed parameters from
    #   the commandline.
    #   @param {int} start_delay - Number of seconds to wait befor starting the
    #   worker sub-processes.
    #

    # Wait before starting to work.
    time.sleep(start_delay)

    logging.debug("VM master: {} (started)".format(
        multiprocessing.current_process().name))
    print("VM master: {} (started)".format(
        multiprocessing.current_process().name))

    vm_worker_list = []

    # Init database connection
    db_manager = db_connection.DBManager(
        settings=cfg.MYSQL,
        mode="fuzzing_read",
        website_type=cl_settings.target_website_type,
        result_table_name=cl_settings.result_table_name
    )

    # Get all fingerprints from the database.
    total_fingerprints = list(fpfuzzer.get_fingerprints(
        db_manager=db_manager,
        timezone_offset=phantom_wrapper_set[0]["timezone_offset"]
    ))

    # Close database connection.
    db_manager.close()

    # Determine list of fingerprints for each worker.
    list_of_fingerprint_lists = get_chunks(
        the_list=total_fingerprints,
        num_of_sub_lists=len(phantom_wrapper_set)
    )

    for phantom_wrapper_index, phantom_wrapper_info in enumerate(phantom_wrapper_set):

        time.sleep(start_delay + phantom_wrapper_index)

        fingerprint_sublist = list_of_fingerprint_lists[phantom_wrapper_index]

        # Crate/Start a new process for every set of webdriver servers in the
        # list. The name of the process is the country of the geolocation.
        process = multiprocessing.Process(
            name="{} (vm_worker {})".format(
                phantom_wrapper_info["country"], phantom_wrapper_index),
            target=inner_fuzzing_vm,
            args=(phantom_wrapper_info, navscraper_list,
                  search_parameters_id, cl_settings, fingerprint_sublist,)
        )
        vm_worker_list.append(process)
        process.start()

    # Waiting for all processes.
    for process in vm_worker_list:
        process.join()

    logging.debug("Shutdown VM master: {} (finished)".format(
        multiprocessing.current_process().name))
    print("Shutdown VM master: {} (finished)".format(
        multiprocessing.current_process().name))


def inner_fuzzing_vm(phantom_wrapper_info, navscraper_list, search_parameters_id, cl_settings, fingerprint_list):
    ##
    #   Main fuzzing routine that can be started in multiple threads/processes.
    #   It iterates over the several variables (NavScrapers, Fingerprints),
    #   gets the data from the websites and stores it in the database.
    #
    #   @param {} phantom_wrapper_info - ...
    #   @param {list} navscraper_list - List that holds the instances of the
    #   various NavScrapers.
    #   @param {int} search_parameters_id - Database id of the search
    #   parameters entry.
    #   @param {argparse.results} cl_settings - Object of parsed parameters
    #   from the commandline.
    #   @param {list} fingerprint_list - List of fingerprints to scan.
    #

    # Store the type of the target websites in a local variable.
    target_website_type = cl_settings.target_website_type

    # Prepare the proxy address string.
    if phantom_wrapper_info["proxy_ip"] is not None and \
            phantom_wrapper_info["proxy_port"] is not None:

        proxy_address = "{ip}:{port}".format(
            ip=phantom_wrapper_info["proxy_ip"],
            port=phantom_wrapper_info["proxy_port"]
        )
    else:
        proxy_address = None

    try:

        # Get phantomwrapper object
        phw = phantom_wrapper_info["phantomwrapper"]

        # Init database connection
        db_manager = db_connection.DBManager(
            settings=cfg.MYSQL,
            mode="fuzzing_write",
            website_type=target_website_type,
            result_table_name=cl_settings.result_table_name
        )

        # Iterate over navscrapers.
        # Means that this iterated also over the target websites.
        for navscraper_class in navscraper_list:

            # Skip every NavScraper that does not have the actual page type.
            if navscraper_class.PAGE_TYPE != target_website_type:
                continue

            # Get a new instance of the current NavScraper.
            navscraper = navscraper_class()

            logging.info("Testing: {0}".format(navscraper.ENTRY_URI))

            # Get the initial timeout limit from the config file.
            timeout_limit = cfg.TIMEOUT_LIMIT

            # Determine the input parameters for the navigation of the
            # NavScraper
            navigation_search_parameters = \
                cfg.SEARCH_PARAMETERS.get(target_website_type, {})

            # Iterate over all fingerprints that are to be tested.
            for fingerprint in fingerprint_list:

                scan_successful = False
                timeout_occurred = False
                retry_count = 0
                while not scan_successful:

                    try:
                        # Run the navigation and scraping routine of the
                        # current NavScraper with the actual fingerprint.
                        results = gather_information_with_fingerprint(
                            navscraper=navscraper,
                            fingerprint=fingerprint,
                            phw=phw,
                            navigation_search_parameters=navigation_search_parameters
                        )

                        # Save results in database.
                        store_results(
                            db_manager=db_manager,
                            results=results,
                            worker_info={
                                "name": multiprocessing.current_process().name.split(" ")[0],
                                "timezone_offset": phantom_wrapper_info["timezone_offset"],
                                "proxy_address": proxy_address,
                            },
                            fp_id=fingerprint["id"],
                            target_website=navscraper.ENTRY_URI,
                            search_parameters_id=search_parameters_id
                        )

                        # Mark scan with current FP as successful.
                        scan_successful = True

                        # Reset timeout limit.
                        timeout_limit = cfg.TIMEOUT_LIMIT

                    except PDFuzzExceptions.NavScraperException as e:

                        if retry_count == cfg.FP_RETRY:
                            log_scan_not_completed_error(
                                driver=phw.get_driver(),
                                exception=e
                            )
                            break

                        # Increment the retry counter.
                        retry_count += 1
                        print("# {retry_count}. retry for {website} with FP {fp_id}".format(
                            retry_count=retry_count,
                            website=navscraper.ENTRY_URI,
                            fp_id=fingerprint["id"]
                        ))
                        logging.info("{retry_count}. retry for {website} with FP {fp_id}".format(
                            retry_count=retry_count,
                            website=navscraper.ENTRY_URI,
                            fp_id=fingerprint["id"]
                        ))

                    except PDFuzzExceptions.PageLoadTimeoutException as e:

                        if retry_count == cfg.FP_RETRY:
                            break

                        # Increment the retry counter.
                        retry_count += 1

                        if timeout_limit > 0 and not timeout_occurred:
                            timeout_limit -= 1
                            timeout_occurred = True
                            logging.info("{timeout_limit} timouts remaining for {website}".format(
                                timeout_limit=timeout_limit,
                                website=navscraper.ENTRY_URI
                            ))

                    finally:
                        # Disconnect from PhantomJS WebDriver server.
                        phw.disconnect()

                if timeout_limit == 0:
                    # If the timeout limit reached zero, move on to the
                    # next website.
                    logging.info("Skip fuzzing of {website} after {max_timeouts} timeouts.".format(
                        website=navscraper.ENTRY_URI,
                        max_timeouts=cfg.TIMEOUT_LIMIT
                    ))
                    break

                # Anti DDoS delay
                logging.debug("Waiting for {sec} seconds before using the next fingerprint.".format(
                    sec=cfg.ANTI_DDOS_DELAY_SECONDS))
                time.sleep(cfg.ANTI_DDOS_DELAY_SECONDS)

        # If the worker is finished, write it to the log and console.
        logging.debug("Shutdown worker {}".format(
            multiprocessing.current_process().name))
        print("Shutdown worker {}".format(
            multiprocessing.current_process().name))

    except:

        logging.exception("Processname: {name}".format(
            name=multiprocessing.current_process().name))

        logging.debug("Worker {} crashed".format(
            multiprocessing.current_process().name))
        print("Worker {} crashed".format(
            multiprocessing.current_process().name))

    finally:

        # close database connection.
        db_manager.close()
        return


def error_log(driver, target_website, country, fingerprint_id, error_msg="NO_RESULTS"):

    # take a screenshot
    driver.get_screenshot_as_file("{dir_error}{timestamp}_{website_name}_{country}_fp{fp_id}_{error_description}_webpage.png".format(
        dir_error=cfg.DIR_ERROR,
        timestamp=time.time(),
        website_name=target_website.replace("http://", "").replace(".", ""),
        country=country,
        fp_id=fingerprint_id,
        error_description=error_msg))

    # dump page source code
    logging.error("{error_description} on {website} for ({country}, FP_ID({fp_id}))".format(
        website=target_website,
        country=country,
        fp_id=fingerprint_id,
        error_description=error_msg))
    logging.error(driver.page_source)


def connect_to_phantomjs(phw, fingerprint):

    # Get desired_capabilities version of fingerprint.
    dcap = fpfuzzer.create_dcap(fingerprint=fingerprint)

    # Connect to WebDriver with specific dcap profile.
    phw.connect(dcap=dcap)


def load_website(phw, uri, fp_id):

    # Load the target homepage and inject the fingerprint.
    print("# Load page '{url}' with FP {fp_id} from {country}".format(
        url=uri,
        fp_id=fp_id,
        country=multiprocessing.current_process().name
    ))
    logging.info("# Load page '{url}' with FP {fp_id}".format(
        url=uri,
        fp_id=fp_id
    ))

    loading_status = phw.load_page(uri=uri)

    # DEBUG: Log cookies.
    logging.debug(
        "Cookies:\n" + pprint.pformat(phw.get_driver().get_cookies()))

    return loading_status


def navscraper_navigation(navscraper, phw, search_parameters, fingerprint):
    # Use the navscraper for the target website to navigate
    # to the results.
    print("# NavScraper Navigation - {url} with FP {fp_id} from {country}".format(
        url=navscraper.ENTRY_URI,
        fp_id=fingerprint["id"],
        country=multiprocessing.current_process().name
    ))
    logging.info(
        "# NavScraper Navigation - {}".format(navscraper.ENTRY_URI))

    nav_status = False

    try:
        # Calling the navigation routine of the NavScraper to receive the page
        # with the results.
        nav_status = navscraper.navigate_to_results(
            driver=phw.get_driver(),
            search_parameters=search_parameters
        )

    except:
        # Handle unexpected errors in the navigation routine.
        logging.exception("Unexpected error in navigation routine of {website} (FP_id: {fp_id}):".format(
            website=navscraper.ENTRY_URI, fp_id=fingerprint["id"]))

        nav_status = False

    finally:

        return nav_status


def navscraper_scraping(navscraper, phw, fingerprint):

    # Call the scraping routine, if the navigation to the results was
    # successful.
    print("# Scraping - {url} with FP {fp_id} from {country}".format(
        url=navscraper.ENTRY_URI,
        fp_id=fingerprint["id"],
        country=multiprocessing.current_process().name
    ))
    logging.info("# Scraping")

    try:
        # Calling the scraping routine of the NavScraper to receive the results
        # for the website.
        results = navscraper.scrape_results(
            driver=phw.get_driver())

        # Error log if no results were found.
        if len(results) == 0:
            raise PDFuzzExceptions.NoResultsException(
                message="No Results found",
                target_website=navscraper.ENTRY_URI,
                country=multiprocessing.current_process().name,
                fp_id=fingerprint["id"]
            )

        else:

            if len(results) < 101:
                # Log if result set is smaller than 100.
                raise PDFuzzExceptions.SmallResultsException(
                    message="Small Set of Results",
                    target_website=navscraper.ENTRY_URI,
                    country=multiprocessing.current_process().name,
                    fp_id=fingerprint["id"]
                )

    except (PDFuzzExceptions.SmallResultsException, PDFuzzExceptions.NoResultsException) as e:
        raise e

    except:
        # Handle unexpected errors in the scraping routine.
        logging.exception("Unexpected error in scraping routine of {website} (FP_id: {fp_id}):".format(
            website=navscraper.ENTRY_URI, fp_id=fingerprint["id"]))

        raise PDFuzzExceptions.ScrapingErrorException(
            message="Scraping error",
            target_website=navscraper.ENTRY_URI,
            country=multiprocessing.current_process().name,
            fp_id=fingerprint["id"]
        )

    return results


def store_results(db_manager, results, worker_info, fp_id, target_website, search_parameters_id):

    # Save results in database.
    print("# Saving data - {url} with FP {fp_id} from {country}".format(
        url=target_website,
        fp_id=fp_id,
        country=multiprocessing.current_process().name
    ))
    logging.info("# Saving data")

    db_manager.write_results(
        worker_info=worker_info,
        fingerprint_id=fp_id,
        target_website=target_website,
        search_parameters_id=search_parameters_id,
        results=results
    )


def gather_information_with_fingerprint(navscraper, fingerprint, phw, navigation_search_parameters):

    try:
        # Create injection code and connect to PhantomJS using the
        # injection code to manipulate the fingerprint.
        connect_to_phantomjs(
            phw=phw,
            fingerprint=fingerprint
        )

        # Load the current target website.
        loading_status = load_website(
            phw=phw,
            uri=navscraper.ENTRY_URI,
            fp_id=fingerprint["id"]
        )

        if not loading_status:
            # If the page cannot be loaded in the defined time.
            # Decrement the timeout limit if it is greater than
            # zero.
            raise PDFuzzExceptions.PageLoadTimeoutException(
                "Page-loading timeout reached"
            )

        else:
            # Use the NavScraper to navigate to the result page.
            nav_status = navscraper_navigation(
                navscraper=navscraper,
                phw=phw,
                search_parameters=navigation_search_parameters,
                fingerprint=fingerprint
            )

            if not nav_status:
                raise PDFuzzExceptions.NavigationFailedException(
                    message="No Results found",
                    target_website=navscraper.ENTRY_URI,
                    country=multiprocessing.current_process().name,
                    fp_id=fingerprint["id"]
                )

            else:
                # Use NavScraper to read out the information from
                # the result page.
                results = navscraper_scraping(
                    navscraper=navscraper,
                    phw=phw,
                    fingerprint=fingerprint
                )

                if results is None:
                    raise PDFuzzExceptions.NoResultsException(
                        message="No Results found",
                        target_website=navscraper.ENTRY_URI,
                        country=multiprocessing.current_process().name,
                        fp_id=fingerprint["id"]
                    )

                return results

    except urllib2.URLError as e:

        logging.warning("Restarting WebDriver after crash.")
        raise PDFuzzExceptions.NetworkErrorException(
            message=str(e),
            target_website=navscraper.ENTRY_URI,
            country=multiprocessing.current_process().name,
            fp_id=fingerprint["id"]
        )


def log_scan_not_completed_error(driver, exception):

    error_log(
        driver=driver,
        target_website=exception.target_website,
        country=exception.country,
        fingerprint_id=exception.fp_id,
        error_msg=exception.error_msg
    )
