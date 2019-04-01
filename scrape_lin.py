"""
Scrape linkedin URLs by using selenium, to simulate the navigation
(click, scroll) and BeautifulSoup to parse the HTML code of the page
Perform a number of queries and log a number of files
for each scraped user.
Write dataset to disk with the scraped data from all the users

"""
from selenium.webdriver.common.keys import Keys
from utils import init_driver, get_urls, login, scrape_url,\
    print_user_data, save_json, create_nonexistent_dir, load_config,\
    get_unseen_urls, init_mongo
from time import sleep, time
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
LOG_DIRECTORY = parameters["LOG_DIRECTORY"]
QUERIES = parameters["QUERIES"]
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
for query in QUERIES:
    driver.get("https://www.google.com")
    sleep(2)
    search_query = driver.find_element_by_name('q')
    search_query.send_keys(query)
    sleep(0.5)
    search_query.send_keys(Keys.RETURN)
    linkedin_urls = get_urls(driver, N_PAGES)
    unseen_urls = get_unseen_urls(users,
                                  linkedin_urls)
    if len(linkedin_urls) != len(unseen_urls) and len(unseen_urls) != 0:
        print("INFO :: Resuming from URL", unseen_urls[0])
    if len(unseen_urls) == 0:
        print("INFO :: All URLs from " + N_PAGES + " Google-search "
              "page(s) for the query " + query + " have already been "
              "scraped. Moving onto the next query if any.")
        continue
    for linkedin_url in unseen_urls:
        user_data = scrape_url(query, linkedin_url, driver)
        print_user_data(user_data)
        user_file = LOG_DIRECTORY + str(time())
        save_json(user_file, user_data)
        if user_data and\
           not db["users"].count_documents(user_data, limit=1):
            users.insert_one(user_data)
driver.quit()
