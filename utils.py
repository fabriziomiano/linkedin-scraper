from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,\
    TimeoutException
from pymongo import MongoClient
from validator_collection import checkers
import json
import os
import errno
import unicodedata


def load_config(path):
    """
    Load configuration file with all the needed parameters

    :param path: str path of the conf file
    :return: dict
    """
    with open(path, 'r') as conf_file:
        conf = json.load(conf_file)
    return conf


def create_nonexistent_dir(path, exc_raise=False):
    """
    Create directory from given path
    Return True if created, False if it exists

    :param path: str dir path
    :param exc_raise: bool raise exception
    :return: str path of the created dir, None otherwise
    """
    try:
        os.makedirs(path)
        print("INFO :: Created directory with path:", str(path))
        return path
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("ERROR :: Could not create directory with path: " +
                  "%s\n", str(path))
            if exc_raise:
                raise
        return None


def validate_field(field):
    """
    Return field if it exists
    otherwise empty string

    :param field: string to validate
    :return: field: input string if not empty, empty string otherwise
    """
    if field:
        pass
    else:
        field = ''
    return field


def validate_user_data(user_data):
    """
    Validate user_data dict by checking that the majority of the keys
    have non-empty values.
    Return an empty dictionary if main keys' values are empty,
    otherwise the original dictionary.

    :param user_data:
    :return: dict
    """
    try:
        if user_data["skills"] == []\
           and user_data["languages"] == []\
           and user_data["name"] == ""\
           and user_data["job_title"] == ""\
           and user_data["degree"] == ""\
           and user_data["location"] == "":
            return {}
        else:
            return user_data
    except KeyError:
        return {}


def init_driver(chrome_path, chromedriver_path):
    """
    Iniitialize Chrome driver
    :param chrome_path: str chrome executable path
    :param chromedriver_path: str chrome driver path
    :return: selenium driver object
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = chrome_path
    chrome_options.add_argument("--normal")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(executable_path=chromedriver_path,
                              chrome_options=chrome_options)
    return driver


def get_job_urls(soup):
    """
    Return a list of job URLs taken from the
    results of a query on LinkedIn.

    :param soup: BeautifulSoup instance
    :return: list of linkedin-job URLs
    """
    base_url = "http://www.linkedin.com"
    job_urls = [base_url + url['href'].split('/?')[0]
                for url in soup.find_all(
                    class_="job-card-search__link-wrapper",
                    href=True)]
    return list(dict.fromkeys(job_urls))


def get_profile_urls(driver, n_pages=1):
    """
    Return a list without repetitions of alphabetically sorted URLs
    taken from the results of a given query on Google search.

    :param driver: selenium chrome driver object
    :param n_pages: int number of google pages to loop over
    :return: list of linkedin-profile URLs
    """
    linkedin_urls = []
    for i in range(n_pages):
        urls = driver.find_elements_by_class_name('iUh30')
        linkedin_urls += [url.text for url in urls
                          if checkers.is_url(url.text)]
        sleep(0.5)
        if i > 1:
            try:
                next_button_url = driver.find_element_by_css_selector(
                    '#pnnext').get_attribute('href')
                driver.get(next_button_url)
            except NoSuchElementException:
                break
    linkedin_urls_no_rep = sorted(
        list(dict.fromkeys([url for url in linkedin_urls])))
    return linkedin_urls_no_rep


def login(driver, user, pwd):
    """
    Type user email and password in the relevant fields and
    perform log in on linkedin.com by using the given credentials.

    :param driver: selenium chrome driver object
    :param user: str username, email
    :param pwd: str password
    :return: None
    """
    username = driver.find_element_by_class_name('login-email')
    username.send_keys(user)
    sleep(0.5)
    password = driver.find_element_by_class_name('login-password')
    password.send_keys(pwd)
    sleep(0.5)
    sign_in_button = driver.find_element_by_xpath('//*[@type="submit"]')
    sign_in_button.click()


def scroll_job_panel(driver):
    """
    Scroll the left panel containing the job offers by sending PAGE_DOWN
    key until the very end has been reached

    :param driver: selenium chrome driver object
    :return: None
    """
    panel = driver.find_element_by_class_name("jobs-search-results")
    last_height = driver.execute_script(
        "return document.getElementsByClassName(" +
        "'jobs-search-results')[0].scrollHeight")
    while True:
        panel.send_keys(Keys.PAGE_DOWN)
        sleep(0.2)
        new_height = driver.execute_script(
            "return document.getElementsByClassName(" +
            "'jobs-search-results')[0].scrollHeight")
        if new_height == last_height:
            break
        else:
            last_height = new_height
    javascript = (
        "var x = document.getElementsByClassName(" +
        "'jobs-search-results')[0]; x.scrollTo(0, x.scrollHeight)"
    )
    driver.execute_script(javascript)


def scroll_profile_page(driver):
    """
    Scroll a profile page by sending the keys PAGE_DOWN
    until the end of the page has been reached.

    :param driver: selenium chrome driver object
    :return:
    """
    body = driver.find_element_by_tag_name("body")
    last_height = driver.execute_script(
        "return document.body.scrollHeight")
    while True:
        body.send_keys(Keys.PAGE_DOWN)
        sleep(3)
        new_height = driver.execute_script(
            "return document.body.scrollHeight")
        if new_height == last_height:
            break
        else:
            last_height = new_height


def is_button_found(driver, delay):
    """
    Try to find the "show more" button in the "skills" section.
    Return a boolean and the button element.

    :param driver: selenium chrome driver object
    :param delay: float delay in seconds
    :return:
    """
    button_found = False
    button_element = None
    try:
        condition_is_met = expected_conditions.presence_of_element_located(
                (By.XPATH, "//button[@class=" +
                 "'pv-profile-section__card-action-bar " +
                 "pv-skills-section__additional-skills " +
                 "artdeco-container-card-action-bar']"))
        button_element = WebDriverWait(driver, delay).until(condition_is_met)
        button_found = True
    except TimeoutException:
        pass
    return button_found, button_element


def print_scraped_data(data):
    """
    Print the user data returned by scrape_url().

    """
    print()
    for key in data:
        print(key + ": " + str(data[key]))


def get_unseen_urls(collection, urls):
    """
    Get a list of URLs that have not already been scraped.
    Loop over all the db entries and create a list with the
    URLs already scraped.
    Get the difference of such list and the list of all the URLs
    for a given query.
    Return a list of URLs which have not already been scraped.

    :param collection: Mongo DB collection
    :param urls: lsit of URLs to check
    :return: list of unseen URLs
    """
    scraped_urls = [entry["URL"] for entry in collection.find()]
    unseen_urls = list(set(urls) - set(scraped_urls))
    return unseen_urls


def connect_mongo(host, user, pwd):
    """
    Conncect Mongo Client

    :param host:
    :param user:
    :param pwd:
    :return: client: Mongo client object
    """
    client = MongoClient("mongodb+srv://" + user + ":" + pwd + host)
    return client


def filter_non_printable(string_to_filter):
    """
    Filter string 's' by removing non-printable chars

    :param string_to_filter:
    :return:
    """
    output_string = ''.join(
        c for c in string_to_filter
        if not unicodedata.category(c) in set('Cf')
    )
    return output_string
