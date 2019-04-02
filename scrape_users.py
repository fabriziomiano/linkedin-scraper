"""
Scrape linkedin URLs by using selenium, to simulate the navigation
(click, scroll) and BeautifulSoup to parse the HTML code of the page
Perform a number of queries and log a number of files
for each scraped user.
Write dataset to mongoDB with the scraped data

"""
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException
from utils import init_driver, get_profile_urls, login,\
    print_scraped_data, save_json, create_nonexistent_dir, load_config,\
    get_unseen_urls, init_mongo
from time import sleep, time
from classes.UserScraper import UserScraper
import argparse
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
                    help='Specify the path of the configuration file')
args = parser.parse_args()
conf = load_config(args.conf)
parameters = conf["parameters"]
credentials = conf["credentials"]
CHROME_PATH = parameters["CHROME_PATH"]
CHROMEDRIVER_PATH = parameters["CHROMEDRIVER_PATH"]
LOG_DIRECTORY = parameters["LOG_DIRECTORY"] + 'profiles/'
QUERIES = parameters["USER_QUERIES"]
N_PAGES = parameters["N_PAGES"]
LINUSERNAME = credentials["LINUSERNAME"]
LINPWD = credentials["LINPWD"]
MONGOUSER = credentials["MONGOUSER"]
MONGOPWD = credentials["MONGOPWD"]
HOST = parameters["HOST"]
client = init_mongo(HOST, MONGOUSER, MONGOPWD)
db = client["linkedin"]
users = db["users"]
driver = init_driver(CHROME_PATH, CHROMEDRIVER_PATH)
driver.get("https://www.linkedin.com")
login(driver, LINUSERNAME, LINPWD)
create_nonexistent_dir(LOG_DIRECTORY)
us = UserScraper(driver)
for query in QUERIES:
    driver.get("https://www.google.com")
    sleep(2)
    search_query = driver.find_element_by_name('q')
    try:
        search_query.send_keys(query)
    except ElementNotInteractableException:
        print("ERROR :: Cannot send query. Google might be blocking")
        sys.exit(1)
    sleep(0.5)
    search_query.send_keys(Keys.RETURN)
    profile_urls = get_profile_urls(driver, N_PAGES)
    if len(profile_urls) == 0:
        print("WARNING :: " +
              "Could not get any URLs for the query\n" + query)
        print("Please double-check that Google is not " +
              "blocking the query")
        continue
    unseen_urls = get_unseen_urls(users, profile_urls)
    if len(unseen_urls) != 0:
        print("INFO :: Resuming from URL", unseen_urls[0])
    else:
        print("INFO :: All URLs from " + str(N_PAGES) +
              " Google-search page(s) for the query " + query +
              " have already been scraped. " +
              "Moving onto the next query if any.")
        continue
    for url in unseen_urls:
        user_data = us.scrape_user(query, url)
        if user_data and\
           not db["users"].count_documents(user_data, limit=1):
            print_scraped_data(user_data)
            user_file = LOG_DIRECTORY + str(time())
            save_json(user_file, user_data)
            users.insert_one(user_data)
driver.quit()
