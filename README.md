# An Empirical Study on Online Price Differentiation

This repo contains the tool PDFuzz used for the CODASPY 2018 paper [An Empirical Study on Online Price Differentiation](https://www.syssec.rub.de/media/emma/veroeffentlichungen/2018/04/24/codaspy18_pridi.pdf) and some files to setup the environment.

## BibTex:
```
@inproceedings{hupperich2018pridi,
    author = {Hupperich, Thomas and Tatang, Dennis and Wilkop, Nicolai and Holz, Thorsten},
    title = {{An Empirical Study on Online Price Differentiation}},
    year = {2018},
    booktitle = {Proceedings of the Eighth ACM Conference on Data and Application Security and Privacy},
    series = {CODASPY '18}
}
```

## Requirements

**Tested Python Version:** v2.75

**Python Packages:**

 * selenium
 * jsmin
 * jinja2
 * beautifulsoup4 (for NavScraper)

**PhantomJS:**

To use PDFuzz you will need the PhantomJS version 2.0 with an extended [GhostDriver](https://github.com/nico101/ghostdriver) version. Copy the full src folder of this GhostDriver fork in the ghostdriver folder of the PhantomJS project and replace the existing files. Make sure that you do not delete the ghostdriver.qrc file from the PhantomJS project.

After you have done this, follow the [build instructions](http://phantomjs.org/build.html) from the PhantomJS website.

At least, copy the resulting phantomjs binary in the folder *phantom_exec*.


## How to Use

 * `python PDFuzz.py --help`

### Configuration

 * Before you can start, you need to create a `fingerprints` table (see setup/create_fingerprints_table.sql)
 * Next you need to go to the `pdfuzz/config/config.py` to configure your Webdriver instances.
 * Before you start scanning, type `python PDFuzz.py --help` to see more parameters.


## How to Extend

To extend PDFuzz by a new category of target websites the following steps are necessary:

 * Define a new key in pdfuzz/config/config.py for SEARCH_PARAMETERS.
 * Define a dictionary of input parameters for the NavScrapers.
 * Register the new key in the WebsiteTypes class in the file pdfuzz/config/config_data_structures.py.
 * Create the necessary database tables(required tables: `search_parameters_<key>` and `pdfuzz_results_<key>`) for your purpose by appending the queries to the file prepare_storage.sql which is located in pdfuzz/config/db_setup/.
 * Go to pdfuzz/core/db_connection.py and insert the necessary code to handle your new type of website in the functions 'get_search_parameters_id', 'store_search_parameters' and 'write_results'.
 * Now you can write NavScrapers for the target websites under your conditions.