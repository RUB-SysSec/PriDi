#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   This module contains all functions to communicate with the underlying
#   database.
#
#   @date   03.11.2015
#   @author Nicolai Wilkop
#

import time
import logging

from contextlib import closing
import MySQLdb
import MySQLdb.cursors

import pdfuzz.config.config as cfg


class DBManager:
    ##
    #   DBManager class contains the various functions to communicate with the
    #   database.
    #

    def __init__(self, settings, website_type, mode="fuzzing", result_table_name="pdfuzz_results"):
        ##
        #   Constructor for the DBManager.
        #
        #   @param {dict} settings - Dictionary with the connection settings.
        #   @param {string} website_type - Type of the website. Example: 'hotels'.
        #   @param {string} mode - String to setup the mode of the instance.
        #   The possible settings are 'init' and 'fuzzing'.
        #   @param {string} result_table_name - The name of the table which
        #   holds the results.
        #

        self.connection_mode = mode
        self.result_table_name = result_table_name
        self.website_type = website_type
        self.fingerprint_table_name = cfg.FINGERPRINT_TABLE_NAME
        self.connection_settings = settings

        if self.connection_mode == "fuzzing":

            # init database connection
            self.connect_read()
            self.connect_write()

        elif self.connection_mode == "init":

            # init database connection
            self.db = MySQLdb.connect(
                host=settings["host"],
                port=settings["port"],
                user=settings["user"],
                passwd=settings["pass"],
                db=settings["db"],
                cursorclass=MySQLdb.cursors.DictCursor,
                charset="utf8"
            )

        elif self.connection_mode == "fuzzing_read":

            # init database connection
            self.connect_read()

        elif self.connection_mode == "fuzzing_write":

            # init database connection
            self.connect_write()


    def connect_read(self):

        # init database connection
        self.db_read = MySQLdb.connect(
            host=self.connection_settings["host"],
            port=self.connection_settings["port"],
            user=self.connection_settings["user"],
            passwd=self.connection_settings["pass"],
            db=self.connection_settings["db"],
            cursorclass=MySQLdb.cursors.DictCursor,
            charset="utf8"
        )

        # prepare a cursor object
        self.cursor_read = self.db_read.cursor()


    def connect_write(self):

        # init database connection
        self.db_write = MySQLdb.connect(
            host=self.connection_settings["host"],
            port=self.connection_settings["port"],
            user=self.connection_settings["user"],
            passwd=self.connection_settings["pass"],
            db=self.connection_settings["db"],
            cursorclass=MySQLdb.cursors.DictCursor,
            charset="utf8"
        )

        # prepare a cursor object
        self.cursor_write = self.db_write.cursor()


    def close(self):
        ##
        #   Closes the connection to the database.
        #

        if self.connection_mode == "fuzzing":

            self.cursor_read.close()
            self.db_read.close()

            self.cursor_write.close()
            self.db_write.close()

        elif self.connection_mode == "init":

            self.db.close()

        elif self.connection_mode == "fuzzing_read":

            self.cursor_read.close()
            self.db_read.close()

        elif self.connection_mode == "fuzzing_write":

            self.cursor_write.close()
            self.db_write.close()


    def init_storage_tables(self, commands_filename):
        ##
        #   Initializes the database tables based on the file with the commands.
        #
        #   @param {string} commands_filename - Path to the file with the commands
        #   for the initialization of the database.
        #

        if self.connection_mode == "init":

            with open(commands_filename, "r") as commands_file:

                with closing(self.db.cursor()) as cursor:

                    for line in commands_file:

                        # remove line-break from sql query.
                        sql_query = line.strip()
                        # execute the query and commit changes.
                        cursor.execute(sql_query)
                        self.db.commit()

            logging.info("[*] Storage initialized!")


    def get_search_parameters_id(self, search_parameters):
        ##
        #   Searches for an entry in the search_parameters table and returns
        #   the id of the entry with the search parameters in it. If no entry
        #   can be found "None" will be returned.
        #
        #   @param {dict} search_parameters - Input values for the search.
        #
        #   @return {int or None} returns None if search parameters can not
        #   be found.
        #

        if self.connection_mode == "init":

            with closing(self.db.cursor()) as cursor:

                if self.website_type == cfg.PAGE_TYPES.HOTELS:
                    # Handle the type of hotel-comparison websites.
                    check_in_date = get_formatted_date(
                        day=search_parameters["check_in_day"],
                        month=search_parameters["check_in_month"],
                        year=search_parameters["check_in_year"]
                    )

                    check_out_date = get_formatted_date(
                        day=search_parameters["check_out_day"],
                        month=search_parameters["check_out_month"],
                        year=search_parameters["check_out_year"]
                    )

                    query = "SELECT id FROM search_parameters WHERE check_in=%s AND check_out=%s AND travel_target=%s AND number_of_adults=%s AND number_of_single_rooms=%s AND number_of_double_rooms=%s"

                    cursor.execute(query, (
                        check_in_date,
                        check_out_date,
                        search_parameters["travel_target"],
                        int(search_parameters["number_of_adults"]),
                        int(search_parameters["number_of_single_rooms"]),
                        int(search_parameters["number_of_double_rooms"])
                    ))

                    results = cursor.fetchall()

                    if len(results) > 0:
                        return results[0]["id"]
                    else:
                        return None

                elif self.website_type == cfg.PAGE_TYPES.CARS:

                    # Lookup for current search parameters.
                    pick_up_date = get_formatted_date(
                        day=search_parameters["pick_up_day"],
                        month=search_parameters["pick_up_month"],
                        year=search_parameters["pick_up_year"]
                    )

                    drop_off_date = get_formatted_date(
                        day=search_parameters["drop_off_day"],
                        month=search_parameters["drop_off_month"],
                        year=search_parameters["drop_off_year"]
                    )

                    # Create query to lookup the current search parameters in
                    # the search parameters table of the cars category.
                    query = "SELECT id FROM search_parameters_cars WHERE picking_up=%s AND dropping_off=%s AND pick_up_date=%s AND pick_up_time=%s AND drop_off_date=%s AND drop_off_time=%s"

                    cursor.execute(query, (
                        search_parameters["picking_up"],
                        search_parameters["dropping_off"],
                        pick_up_date,
                        search_parameters["pick_up_time"],
                        drop_off_date,
                        search_parameters["drop_off_time"],
                    ))

                    results = cursor.fetchall()

                    if len(results) > 0:
                        return results[0]["id"]
                    else:
                        return None

                else:
                    # In case of an unknown website type.
                    return None


    def store_search_parameters(self, search_parameters):
        ##
        #   Stores the given search parameters in the table.
        #
        #   @param {dict} search_parameters - Input values for the search.
        #
        #   @return {int} search_parameters_id
        #

        if self.connection_mode == "init":

            with closing(self.db.cursor()) as cursor:

                if self.website_type == cfg.PAGE_TYPES.HOTELS:
                    # Handle the type of hotel-comparison websites.

                    check_in_date = get_formatted_date(
                        day=search_parameters["check_in_day"],
                        month=search_parameters["check_in_month"],
                        year=search_parameters["check_in_year"]
                    )

                    check_out_date = get_formatted_date(
                        day=search_parameters["check_out_day"],
                        month=search_parameters["check_out_month"],
                        year=search_parameters["check_out_year"]
                    )

                    query = "INSERT INTO search_parameters (check_in, check_out, travel_target, number_of_adults, number_of_single_rooms, number_of_double_rooms) VALUES (%s,%s,%s,%s,%s,%s)"

                    cursor.execute(query, (
                        check_in_date,
                        check_out_date,
                        search_parameters["travel_target"],
                        int(search_parameters["number_of_adults"]),
                        int(search_parameters["number_of_single_rooms"]),
                        int(search_parameters["number_of_double_rooms"])
                    ))

                    self.db.commit()

                    return cursor.lastrowid

                elif self.website_type == cfg.PAGE_TYPES.CARS:
                    # Store current search parameters for key CARS.

                    pick_up_date = get_formatted_date(
                        day=search_parameters["pick_up_day"],
                        month=search_parameters["pick_up_month"],
                        year=search_parameters["pick_up_year"]
                    )

                    drop_off_date = get_formatted_date(
                        day=search_parameters["drop_off_day"],
                        month=search_parameters["drop_off_month"],
                        year=search_parameters["drop_off_year"]
                    )

                    query = "INSERT INTO search_parameters_cars (picking_up, dropping_off, pick_up_date, pick_up_time, drop_off_date, drop_off_time) VALUES (%s,%s,%s,%s,%s,%s)"

                    cursor.execute(query, (
                        search_parameters["picking_up"],
                        search_parameters["dropping_off"],
                        pick_up_date,
                        search_parameters["pick_up_time"],
                        drop_off_date,
                        search_parameters["drop_off_time"],
                    ))

                    self.db.commit()

                    # Return ID of new entry.
                    return cursor.lastrowid

                else:
                    # In case of an unknown website type.
                    return None


    def rename_table(self, old_name, new_name):
        ##
        #   Renames a table in the database.
        #
        #   @param {string} old_name - Old name of the table to rename.
        #   @param {string} new_name - The new name of the table.
        #

        if self.connection_mode == "init":

            with closing(self.db.cursor()) as cursor:

                # Delete table with new name if exists
                sql_query = "DROP TABLE IF EXISTS `{table_name}`".format(
                        table_name=new_name
                    )
                # execute the query and commit changes.
                cursor.execute(sql_query)
                self.db.commit()

                # create sql query to rename the table.
                sql_query = "RENAME TABLE  `{old_table_name}` TO  `{new_table_name}`".format(
                        old_table_name=old_name,
                        new_table_name=new_name
                    )
                # execute the query and commit changes.
                cursor.execute(sql_query)
                self.db.commit()



    def _result_iter(self, cursor, arraysize=100):
        ##
        #   An iterator that uses fetchmany to keep memory usage down.
        #
        while True:
            results = cursor.fetchmany(arraysize)
            if not results:
                break
            for result in results:
                yield result


    def get_fingerprints(self):
        ##
        #   Queries the database, to receive all fingerprints. The fingerprints
        #   are passed back with a generator to hold the memory usage low.
        #

        try:
            sql_get_fingerprints = "SELECT * FROM `{table_name}`".format(
                table_name=self.fingerprint_table_name
            )
            self.cursor_read.execute(sql_get_fingerprints)

        except MySQLdb.OperationalError, e:
            if e[0] not in (2006, 2013):
                raise

            # reconnect to database.
            self.connect_read()
            self.cursor_read.execute(sql_get_fingerprints)


        return self._result_iter(self.cursor_read)


    def write_results(self, worker_info, fingerprint_id, target_website, search_parameters_id, results):
        ##
        #   Save the results of the fuzzing run in the database. For debug purpose
        #   the results are also stored in a file.
        #
        #   @param {dict} worker_info - Information about the current worker.
        #   @param {int} fingerprint_id - Database id of the used fingerprint.
        #   @param {string} target_website - URL of the target website.
        #   @param {dict} search_parameters - Holds the search parameters that
        #   lead to the actual results.
        #   @param {list} results - List of all the results that have been
        #   extracted from the website.
        #

        if self.website_type == cfg.PAGE_TYPES.HOTELS:
            # Handle the type of hotel-comparison websites.
            sql_insert_query = '''INSERT INTO {table_name} (provider_name, product_name, location, room_type, price,
                currency, price_euro, nights, rating_value, rating_unit, fp_id, fp_table_name,
                search_param_id, request_country, request_timezone_offset, proxy_address,
                access_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''.format(
                    table_name=self.result_table_name
                )

            for product in results:

                # Insert data for the current product.
                self.cursor_write.execute(sql_insert_query, (
                    target_website,
                    product.get("name", "?"),
                    product.get("location", None),
                    product.get("room_type", None),
                    product.get("price", None),
                    product.get("currency", None),
                    product.get("price_norm", None),
                    product.get("number_of_nights", None),
                    product.get("rating_value", None),
                    product.get("rating_unit", None),
                    fingerprint_id,
                    self.fingerprint_table_name,
                    search_parameters_id,
                    worker_info.get("name", "unknown"),
                    worker_info.get("timezone_offset", None),
                    worker_info.get("proxy_address", None),
                    product.get("access_time", "?")
                ))


            self.db_write.commit()

        elif self.website_type == cfg.PAGE_TYPES.CARS:
            # Write results of the cars NavScraper.
            sql_insert_query = '''INSERT INTO {table_name} (provider_name, company_name, car_class,
                car_model, transmission, price_daily, price_norm_daily, price_total, price_norm_total, currency,
                fp_id, fp_table_name, search_param_id, request_country, request_timezone_offset,
                proxy_address, access_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''.format(
                    table_name=self.result_table_name
                )

            for product in results:
                self.cursor_write.execute(sql_insert_query, (
                    target_website,
                    product.get("company_name", None),
                    product.get("car_class", None),
                    product.get("car_model", None),
                    product.get("transmission", None),
                    product.get("price_daily", None),
                    product.get("price_norm_daily", None),
                    product.get("price_total", None),
                    product.get("price_norm_total", None),
                    product.get("currency", None),
                    fingerprint_id,
                    self.fingerprint_table_name,
                    search_parameters_id,
                    worker_info.get("name", "unknown"),
                    worker_info.get("timezone_offset", None),
                    worker_info.get("proxy_address", None),
                    product.get("access_time", "?")
                ))
            self.db_write.commit()


        # DEBUG Outupt
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            # Outputs that are only visible in verbose mode

            if self.website_type == cfg.PAGE_TYPES.HOTELS:
                # Handle the type of hotel-comparison websites.
                # Create a filename with all the important infos.
                filename = "{dir_debug}{timestamp}_{worker_name}_{website_name}_fp{fp_id}_data".format(
                    dir_debug=cfg.DIR_DEBUG,
                    timestamp=time.time(),
                    worker_name=worker_info["name"],
                    website_name=target_website.replace("http://", "").replace(".", ""),
                    fp_id=fingerprint_id
                )
                # Write the data with extra debug information into the file.
                with open(filename, "w") as debug_out_file:
                    for product in results:



                        debug_out_file.write("{product} : {price} {currency} - {rating_value} {rating_unit}\n".format(
                            product=product["name"],
                            price=product["price"],
                            currency=product["currency"],
                            rating_value=product.get("rating_value", None),
                            rating_unit=product.get("rating_unit", None)
                        ))

                        debug_data = product.get("debug", None)
                        if debug_data != None:

                            dbg_price       = debug_data.get("price_text", "[EMPTY]")
                            dbg_nights      = debug_data.get("number_of_nights_text", "[EMPTY]")
                            dbg_search_info = debug_data.get("search_info", "[EMPTY]")

                            # Convert NoneType to string.
                            if dbg_price is None:
                                dbg_price = "None"
                            if dbg_nights is None:
                                dbg_nights = "None"

                            debug_out_file.write("{price}\n{price_hex}\n{nights}\n{nights_hex}\n{search_info}\n".format(
                                price=dbg_price,
                                price_hex=dbg_price.encode("hex"),
                                nights=dbg_nights,
                                nights_hex=dbg_nights.encode("hex"),
                                search_info=dbg_search_info
                            ))


def get_formatted_date(year, month, day):

    return "{day}.{month}.{year}".format(
        day=day,
        month=month,
        year=year
    )