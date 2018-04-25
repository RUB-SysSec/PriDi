#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   In this module ...
#
#   @date   07.10.2015
#   @author Nicolai Wilkop
#

import logging
import time
import subprocess
import pkg_resources
import selenium

import pdfuzz.config.config as cfg


class PhantomWrapper:
    ##
    #   PhantomWrapper is used to build up a connection via PhantomJS remote
    #   WebDriver to visit a website using a  ...
    #

    def __init__(self, remote_webdriver_ip, remote_webdriver_port):
        ##
        #
        #   @param {string} remote_webdriver_ip - IP of the remote webdriver
        #   server, that is created by phantomjs.
        #   @param {int} remote_webdriver_port - Port of the remote webdriver
        #   server, that is created by phantomjs.
        #

        self.RWD_IP = remote_webdriver_ip
        self.RWD_PORT = remote_webdriver_port

        self.page_load_timeout = cfg.PAGE_LOAD_TIMEOUT

    def connect(self, dcap):
        ##
        #   Connect to the defined remote webdriver server with specific
        #   desired capabilities.
        #
        #   @param {selenium.webdriver.common.desired_capabilities} dcap
        #

        self.driver = selenium.webdriver.Remote(
            desired_capabilities=dcap,
            command_executor='http://{0}:{1}'.format(self.RWD_IP, self.RWD_PORT)
        )

        # set page load timeout
        self.driver.set_page_load_timeout(self.page_load_timeout)

    def disconnect(self):
        ##
        #   Disconnect connection to the remote webdriver server.
        #

        self.driver.quit()

    def get_driver(self):
        ##
        #   @return {selenium.webdriver}
        #

        return self.driver

    def load_page(self, uri):
        ##
        #   Loads the given website via selenium remote webdriver connection.
        #   Using the passed JavaScript code, the browser fingerprint is
        #   manipulated.
        #
        #   @param {string} uri - URL of the target website.
        #   @param {string} js_insjct_code - JavaScript code to manipulate the
        #   browser fingerprint.
        #

        try:

            self.driver.get(uri)
            return True

        except selenium.common.exceptions.TimeoutException as e:

            logging.error(e.msg)
            return False


class PhantomWebdriverManager:
    ##
    #   PhantomWebdriverManager is used to start and manage phantomjs webdriver
    #   server instances. It represents a container for all the started servers
    #   and returns the connection details.
    #

    def __init__(self, webdriver_details_list):
        ##
        #
        #   @param {list} webdriver_details_list - ...
        #

        self.webdriver_instances = []
        self.phantom_wrapper_list = {
            'vm': [],
            'local': [],
        }
        self.webdriver_details_list = webdriver_details_list

        # Get path to PhantomJS binary from "phantomjs_bin" file of "pdfuzz.config" package.
        self.phantomjs_bin = pkg_resources.resource_string("pdfuzz.config", "phantomjs_bin")

    def start_all_webdriver_instances(self):
        ##
        #   Iterates over the list of webdriver instances that are to be created.
        #   For every entry in this list on of the following cli commands are
        #   executed:
        #
        #   The default command:
        #   phantomjs --webdriver=<port>
        #
        #   If a proxy server is configured:
        #   phantomjs --webdriver=<port> --proxy=<uri>:<port>
        #

        for wd in self.webdriver_details_list:

            if wd.is_proxy_configured():
                # If the proxy IP and port is configured.
                self.start_webdriver(

                    ip=wd.wd_ip,
                    port=wd.wd_port,
                    num_wd_instances=wd.num_wd_instances,
                    country=wd.country,
                    proxy_ip=wd.proxy_ip,
                    proxy_port=wd.proxy_port,
                    timezone_offset=wd.timezone_offset

                )

            else:
                # If no proxy is configured.
                self.start_webdriver(

                    ip=wd.wd_ip,
                    port=wd.wd_port,
                    num_wd_instances=wd.num_wd_instances,
                    country=wd.country,
                    timezone_offset=wd.timezone_offset

                )

    def start_webdriver(self, ip, port, num_wd_instances, proxy_ip=None, proxy_port=None, country="Germany", timezone_offset=-60):
        ##
        #   This function will start a new webdriver server via the phantomjs
        #   command. A proxy server can be set for the webdriver server. The
        #   process will be stored in a list for later usage.
        #
        #   @param {string} ip - IP of the webdriver server.
        #   @param {int} port - Port of the webdriver server.
        #   @param {int} num_wd_instances - Number of running WebDriver instances
        #   on the given IP address.
        #   @param {string} proxy_ip - (optional) IP address of the proxy server.
        #   An URL is also a valid value.
        #   @param {int} proxy_port - (optional) Port of the proxy server.
        #   @param {string} country - (optional) ...
        #   @param {string} timezone_offset - (optional) The timezone offset for
        #   the proxy location.
        #

        p = None

        if ip in ["localhost", "127.0.0.1"]:

            if proxy_ip is None or proxy_port is None:
                # If no proxy information are set.
                p = subprocess.Popen([self.phantomjs_bin, "--webdriver={0}".format(port)])

            else:
                # If a proxy server is defined.
                p = subprocess.Popen([self.phantomjs_bin, "--webdriver={0}".format(port), "--proxy={0}:{1}".format(proxy_ip, proxy_port)])

            self.webdriver_instances.append(p)

            # Create a new phantom wrapper for ip and port.
            phw = self.create_phantom_wrapper(ip=ip, port=port)

            self.phantom_wrapper_list["local"].append({
                "index": len(self.phantom_wrapper_list["local"]),
                "country": country,
                "timezone_offset": timezone_offset,
                "phantomwrapper": phw,
                "ip": ip,
                "port": port,
                "proxy_ip": proxy_ip,
                "proxy_port": proxy_port,
            })

        else:
            # If the PhantomJS instance is on an external server.
            self.phantom_wrapper_list["vm"].append([])
            vm_index = len(self.phantom_wrapper_list["vm"]) - 1

            # Create an phantom_wrapper for each instance of PhantomJS on this server.
            for i in range(num_wd_instances):

                # Create a new phantom wrapper for ip and port.
                phw = self.create_phantom_wrapper(ip=ip, port=port + i)

                self.phantom_wrapper_list["vm"][vm_index].append({
                    "index": i,
                    "country": country,
                    "timezone_offset": timezone_offset,
                    "phantomwrapper": phw,
                    "ip": ip,
                    "port": port + i,
                    "proxy_ip": proxy_ip,
                    "proxy_port": proxy_port,
                })

    def restart_webdriver(self, phantom_wrapper_info):
        ##
        #
        #
        #   @param {dict} phantom_wrapper_info - Dictionary with all information
        #   about the crashed webdriver server.
        #

        if phantom_wrapper_info["ip"] in ["localhost", "127.0.0.1"]:

            if phantom_wrapper_info.get["proxy_ip"] is None or phantom_wrapper_info["proxy_port"] is None:
                # If no proxy information are set.
                p = subprocess.Popen([
                    self.phantomjs_bin,
                    "--webdriver={0}".format(
                        phantom_wrapper_info["port"]
                    )
                ])

            else:
                # If a proxy server is defined.
                p = subprocess.Popen([
                    self.phantomjs_bin,
                    "--webdriver={0}".format(
                        phantom_wrapper_info["port"]
                    ),
                    "--proxy={0}:{1}".format(
                        phantom_wrapper_info["proxy_ip"],
                        phantom_wrapper_info["proxy_port"]
                    )
                ])

            self.webdriver_instances.append(p)

            phw = self.create_phantom_wrapper(port=phantom_wrapper_info["port"])

            # Replace the old phantomwrapper object.
            phantom_wrapper_info["phantomwrapper"] = phw

            # Replace the old list entry.
            self.phantom_wrapper_list["local"][phantom_wrapper_info["index"]] = phantom_wrapper_info

            # Delay to let the webdriver start.
            time.sleep(5)

            return phw

    def create_phantom_wrapper(self, port, ip):
        ##
        #   ...
        #
        #   @param {int} port - Port of the webdriver server the wrapper shall
        #   connect to.
        #   @param {string} ip - (optional) IP of the webdriver server the
        #   wrapper shall connect to.
        #
        #   @return pdfuzz.core.phantomconnection.PhantomWrapper
        #

        ph = PhantomWrapper(remote_webdriver_ip=ip, remote_webdriver_port=port)

        return ph

    def shutdown_all_webdriver_server(self):
        ##
        #   Exits all the webdriver servers. It makes sens to call this function
        #   when the fuzzer is done.
        #
        #   import atexit
        #
        #   atexit.register()
        #

        print("[**] Shutdown all WebDriver Server")
        logging.info("Shutdown all WebDriver Server")

        for p in self.webdriver_instances:
            if p is not None:
                # Kill process.
                p.kill()

    def get_phantom_wrappers(self):
        ##
        #   Returns the list of PhantomWrapper objects.
        #
        #   @return {list(dict("country" : "",
        #   "phantomwrapper" : pdfuzz.core.phantomconnection.PhantomWrapper))}
        #

        return self.phantom_wrapper_list
