"""
Scrape linkedin jobs by using selenium, to simulate the navigation
(click, scroll) and BeautifulSoup to parse the HTML code of the page
Perform a number of queries and log a number of files
for each scraped job offer.
Write dataset to mongoDB with the scraped data

"""
from selenium.common.exceptions import TimeoutException
from utils import init_driver, get_job_urls, login, print_scraped_data,\
    load_config, get_unseen_urls, scroll_job_panel, connect_mongo
from time import sleep
from bs4 import BeautifulSoup
from classes.JobScraper import JobScraper
import argparse


parser = argparse.ArgumentParser(
    description=("Scrape linkedin job offers based on the " +
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
QUERIES = parameters["JOB_QUERIES"]
LINUSERNAME = credentials["LINUSERNAME"]
LINPWD = credentials["LINPWD"]
MONGOUSER = credentials["MONGOUSER"]
MONGOPWD = credentials["MONGOPWD"]
HOST = parameters["HOST"]
client = connect_mongo(HOST, MONGOUSER, MONGOPWD)
db = client["linkedin"]
jobs = db["jobs"]
driver = init_driver(CHROME_PATH, CHROMEDRIVER_PATH)
driver.get("https://www.linkedin.com")
login(driver, LINUSERNAME, LINPWD)
JOB_SEARCH_URL = "https://www.linkedin.com/jobs/search/?keywords="
for query in QUERIES:
    driver.get(JOB_SEARCH_URL + query)
    sleep(0.5)
    scroll_job_panel(driver)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    n_results_element = soup.find(class_="t-12 t-black--light t-normal")
    n_results_string = n_results_element.get_text()
    n_results = int(n_results_string.split()[0].replace(',', ''))
    job_urls = get_job_urls(soup)
    start = 25
    url = JOB_SEARCH_URL + query + "&start=" + str(start)
    while start < n_results:
        try:
            driver.get(url)
            scroll_job_panel(driver)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_urls.extend(get_job_urls(soup))
            start += 25
        except TimeoutException:
            print(
                "\nINFO :: TimeoutException raised while getting " +
                "URL\n" + url
            )
    if len(job_urls) == 0:
        print()
        print("WARNING :: Could not get any URLs for the query\n" +
              query)
        print("Please double-check that LinkedIn is not " +
              "blocking the query")
        continue
    unseen_urls = get_unseen_urls(jobs, job_urls)
    if len(unseen_urls) != 0:
        print("INFO :: Resuming from URL", unseen_urls[0])
    else:
        print("INFO :: All job URLs for the query " + query +
              " have already been scraped. " +
              "Moving onto the next query if any.")
        continue
    for url in unseen_urls:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        js = JobScraper(soup, url, query)
        job_data = js.get_job_data()
        if job_data and\
           not db["jobs"].count_documents(job_data, limit=1):
            print_scraped_data(job_data)
            jobs.insert_one(job_data)
driver.quit()
