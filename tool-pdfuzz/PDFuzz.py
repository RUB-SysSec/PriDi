#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   PDFuzz is developed to find price discrimination in e-commerce websites,
#   based on browser fingerprinting. It was build as part of the master thesis
#   by the author.
#
#   @date   06.10.2015
#   @author Nicolai Wilkop
#

import os
import logging
import time
import argparse
import pdfuzz.core.fuzzengine as fuzzengine
import pdfuzz.core.db_connection as db_connection
import pdfuzz.config.config as cfg


# global variables
PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
VERSION           = "0.1"
VERSION_INFO      = "PDFuzz v{version}".format(version=VERSION)


def parse_commandline_arguments():
    ##
    #   Parses the commandline arguments.
    #
    #   @return {argparse.results} settings
    #

    parser = argparse.ArgumentParser(
        description="This is PDFuzz. A tool to find price discrimination in e-commerce websites based on the device fingerprint.",
    )

    # Create a default name for the results table.
    default_results_table_name = "pdfuzz_results_{time}".format(
        time=time.strftime("%Y%m%d%H%M", time.gmtime())
    )

    # Handle the parameter to set a name for the result table.
    parser.add_argument(
        "-r",
        "--rename-table",
        action="store",
        dest="result_table_name",
        help="change the table name for the results. A valid string for a MySQL table name is required.",
        default=default_results_table_name
    )

    # Handle the parameter to set a name for the fingerprint table.
    parser.add_argument(
        "-f",
        "--fp-table",
        action="store",
        dest="fingerprint_table_name",
        help="change the table name for the fingerprints. A valid string for a MySQL table name is required.",
        default=cfg.FINGERPRINT_TABLE_NAME
    )

    # Handle the parameter to use the debug mode for the log file.
    parser.add_argument(
        "--debug",
        action="store_const",
        dest="logging_level",
        const=logging.DEBUG,
        default=logging.INFO,
        help="enable debug information."
    )

    # Handle the parameter to set the anti ddos delay.
    parser.add_argument(
        "-a",
        "--anti-ddos-delay",
        dest="anti_ddos_delay",
        type=int,
        default=cfg.ANTI_DDOS_DELAY_SECONDS,
        help="set the anti DDoS delay in seconds (default: {0})".format(cfg.ANTI_DDOS_DELAY_SECONDS)
    )

    # Handle the parameter to set the timeout limit.
    parser.add_argument(
        "-t",
        "--timeout-limit",
        dest="timeout_limit",
        type=int,
        default=cfg.TIMEOUT_LIMIT,
        help="set the limit of page load timeouts before the page is skipped (-1 = off, default: {0})".format(cfg.TIMEOUT_LIMIT)
    )

    # Handle the parameter to set the page load timeout.
    parser.add_argument(
        "-p",
        "--page-load-timeout",
        dest="page_load_timeout",
        type=int,
        default=cfg.PAGE_LOAD_TIMEOUT,
        help="set the page load timeout in seconds (default: {0})".format(cfg.PAGE_LOAD_TIMEOUT)
    )

    # Handle the parameter to set the type of target websites.
    target_website_types = list(cfg.SEARCH_PARAMETERS.keys())
    parser.add_argument(
        "--tt",
        "--target-type",
        action="store",
        dest="target_website_type",
        help="set the type of target websites. Allowed values are {{{target_types}}}".format(
            target_types=", ".join(target_website_types)
        ),
        choices=target_website_types,
        default=cfg.PAGE_TYPES.HOTELS
    )

    # Handle the parameter to show the version of PDFuzz.
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=VERSION_INFO
    )


    settings = parser.parse_args()

    if settings.result_table_name == "fingerprints" or \
        settings.result_table_name == "product" or \
        settings.result_table_name == "search_parameters":

        print("ERROR: The table names 'fingerprints', 'product' and 'search_parameters' are reserved!")
        exit(2)

    return settings


def init_database(new_results_table_name, website_type):
    ##
    #   Initializes the several tables in the MySQL database to store the reqults
    #   of the fuzzing routine. This is done, using the sql file in the db_setup
    #   directory. Every line holds a single command to initialize the database.
    #
    #   @param {string} new_results_table_name - Name of the results table in
    #   the database.
    #   @param {string} website_type - Type of the website. Example: 'hotels'.
    #

    # Init database connection
    db_manager = db_connection.DBManager(
        settings=cfg.MYSQL,
        website_type=website_type,
        mode="init"
    )

    # Determine path to commands file.
    init_commands_filename = \
        "{current_dir}/pdfuzz/config/db_setup/prepare_storage.sql".format(
            current_dir=PACKAGE_DIRECTORY
        )

    # Init the storage tables.
    db_manager.init_storage_tables(commands_filename=init_commands_filename)

    # Rename the results table.
    old_results_table_name = "pdfuzz_results_" + website_type
    db_manager.rename_table(old_name=old_results_table_name, new_name=new_results_table_name)

    # close database connection.
    db_manager.close()


def init_logging(log_prefix, log_filename, log_level):
    ##
    #   Configures the logging environment.
    #
    #   @param {string} log_prefix - Prefix for the logging file and it is used
    #   as the directory name for the error and debug logs.
    #   @param {string} log_filename - Name of the log file.
    #   @param {logging.level} log_level - Logging level setting.
    #   

    log_entry_format = "%(asctime)-15s  %(levelname)-9s %(process)d \
                        %(processName)-12s %(module)s : %(message)s"

    logging.basicConfig(
        filename=log_filename,
        level=log_level,
        format=log_entry_format
    )

    # Create directories for debug and error output.
    dir_name = "run_{}".format(log_prefix)
    cfg.DIR_ERROR = os.path.join(cfg.DIR_ERROR, dir_name, "")
    cfg.DIR_DEBUG = os.path.join(cfg.DIR_DEBUG, dir_name, "")

    os.makedirs(cfg.DIR_ERROR)
    os.makedirs(cfg.DIR_DEBUG)


def init_phantomjs():
    ##
    #   Configures the path to the PhantomJS binary file. The path is saved in a
    #   separat file within the config folder of the pdfuzz package.
    #

    #global PACKAGE_DIRECTORY

    # Determine path to PhantomJS executable.
    phantom_bin = os.path.join(PACKAGE_DIRECTORY, 'phantom_exec', 'phantomjs')

    # Store it in the config folder
    open(os.path.join(PACKAGE_DIRECTORY, "pdfuzz", "config", "phantomjs_bin"), "w") \
        .write(phantom_bin)


def init_config_parameters(cl_settings):
    ##
    #   Overwrites the parameters of the config.py with the input commandline
    #   parameters.
    #
    #   @param {arparse.results} cl_settings - Object with the parsed command-
    #   line arguments.

    cfg.ANTI_DDOS_DELAY_SECONDS = cl_settings.anti_ddos_delay
    cfg.TIMEOUT_LIMIT           = cl_settings.timeout_limit
    cfg.PAGE_LOAD_TIMEOUT       = cl_settings.page_load_timeout
    cfg.FINGERPRINT_TABLE_NAME  = cl_settings.fingerprint_table_name


def init(cl_settings):
    ##
    #   Function to initialize configuration parameters and starting the fuzzer.
    #
    #   @param {arparse.results} cl_settings - Object with the parsed command-
    #   line arguments.
    #

    log_prefix = str(time.strftime("%Y%m%d%H%M%S", time.gmtime()))

    log_filename = os.path.join(cfg.DIR_LOG, "{timestamp}_pdfuzz_run.log".format(
        timestamp=log_prefix
    ))

    # Basic Configurations
    init_logging(
        log_prefix=log_prefix,
        log_filename=log_filename,
        log_level=cl_settings.logging_level
    )
    init_phantomjs()
    init_database(
        new_results_table_name=cl_settings.result_table_name,
        website_type=cl_settings.target_website_type
    )
    init_config_parameters(cl_settings)

    logging.info("[*] Configuration Finished.")


def get_search_parameters_id(search_parameters, website_type):
    ##
    #   Determines the database id of the current search parameters.
    #
    #   @param {dict} search_parameters - Input values for the search.
    #   @param {string} website_type - Type of the website. Example: 'hotels'.
    #
    #   @return {int}
    #

    # Init database connection
    db_manager = db_connection.DBManager(
        settings=cfg.MYSQL,
        website_type=website_type,
        mode="init"
    )

    # Try to find the id of the search parameters
    search_parameters_id = \
        db_manager.get_search_parameters_id(search_parameters=search_parameters)

    if search_parameters_id is None:
        # If search parameters can not be found, store them in the database.
        search_parameters_id = db_manager.store_search_parameters(search_parameters)

    # close database connection.
    db_manager.close()

    return search_parameters_id


def main():
    ##
    #   Main function of PDFuzz. Initiates everything.
    #

    # Parse possible command-line arguments.
    cl_settings = parse_commandline_arguments()

    # Initialize the fuzzing environment.
    init(cl_settings=cl_settings)

    # Determine search parameters id in database. If it is not available store
    # the search parameters.
    search_parameters_id = get_search_parameters_id(
        search_parameters=cfg.SEARCH_PARAMETERS.get(cl_settings.target_website_type, None),
        website_type=cl_settings.target_website_type
    )

    # Start Fuzzing.
    fuzzengine.start_fuzzing(cl_settings=cl_settings, search_parameters_id=search_parameters_id)


if __name__ == '__main__':
    main()
