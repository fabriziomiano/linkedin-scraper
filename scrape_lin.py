"""
Scrape linkedin URLs by using selenium, to simulate the navigation
(click, scroll) and BeautifulSoup to parse the HTML code of the page
Perform a number of queries and log a number of files 
for each scraped user.
Write dataset to disk with the scraped data from all the users

"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from utils import init_driver, get_urls, login, scrape_url,\
    print_user_data, save_json, create_nonexistent_dir, load_config,\
    get_unseen_urls, make_dataset
from time import sleep, time
import argparse
import json
import sys


args = sys.argv
parser = argparse.ArgumentParser(
    description=("Scrape linkedin profiles based on the " +
                 "queries specified in the conf file")
)
parser.add_argument('-c', '--conf',
                    type=str,
                    metavar='',
                    required=True,
                    help='Specify the path of the configuration file'
)
args = parser.parse_args()
conf = load_config(args.conf)
parameters = conf["parameters"]
credentials = conf["credentials"]
CHROME_PATH = parameters["CHROME_PATH"]
CHROMEDRIVER_PATH = parameters["CHROMEDRIVER_PATH"]
LOG_DIRECTORY = parameters["LOG_DIRECTORY"]
QUERIES = parameters["QUERIES"]
N_PAGES = parameters["N_PAGES"]
OUT_FILE_NAME = parameters["OUT_FILE_NAME"]
USERNAME = credentials["USERNAME"]
PASSWORD = credentials["PASSWORD"]
driver = init_driver(CHROME_PATH, CHROMEDRIVER_PATH)
driver.get("https://www.linkedin.com")
login(driver, USERNAME, PASSWORD)
create_nonexistent_dir(LOG_DIRECTORY)
for query in QUERIES:
    driver.get("https://www.google.com")
    sleep(2)
    search_query = driver.find_element_by_name('q')
    search_query.send_keys(query)
    sleep(0.5)
    search_query.send_keys(Keys.RETURN)
    linkedin_urls = get_urls(driver, N_PAGES)
    unseen_urls = get_unseen_urls(LOG_DIRECTORY,
                                  linkedin_urls)
    if len(linkedin_urls) != len(unseen_urls):
        print("INFO :: Resuming from URL", unseen_urls[0])
    for linkedin_url in unseen_urls:
        user_data = scrape_url(query, linkedin_url, driver)
        print_user_data(user_data)
        user_file = str(time())
        save_json(LOG_DIRECTORY + user_file, user_data)
driver.quit()
make_dataset(LOG_DIRECTORY, OUT_FILE_NAME)
