from parsel import Selector
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,\
    TimeoutException
from bs4 import BeautifulSoup as bs
import uuid
import json
import os
import errno


def load_config(path):
    """
    Load configuration file with all the needed parameters

    """
    with open(path, 'r') as conf_file:
        conf = json.load(conf_file)
    return conf


def create_nonexistent_dir(path, exc_raise=False):
    """
    Create directory from given path
    Return True if created, False if it exists

    """
    try:
        os.makedirs(path)
        print("INFO :: Created directory with path:", str(path))
        return path
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("ERROR :: Could not create directory with path: " +
                  "%s\n", path)
            if exc_raise:
                raise
        return None


def validate_field(field):
    """
    return field if it exists
    otherwise empty string

    """
    if field:
        pass
    else:
        field = ''
    return field


def init_driver(CHROME_PATH, CHROMEDRIVER_PATH):
    """
    Initialize Chrome driver

    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = CHROME_PATH
    chrome_options.add_argument("--normal")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                              chrome_options=chrome_options)
    return driver


def get_urls(driver, n_pages=1):
    """
    Return a list without repetitions of alphabetically sorted URLs
    taken from the results of a given query on Google search.

    """
    linkedin_urls = []
    for i in range(n_pages):
        urls = driver.find_elements_by_class_name('iUh30')
        linkedin_urls += [url.text for url in urls]
        sleep(0.5)
        try:
            nextpage_button_url = driver.find_element_by_css_selector(
                '#pnnext').get_attribute('href')
            driver.get(nextpage_button_url)
        except NoSuchElementException:
            break
    linkedin_urls_no_rep = sorted(
        list(dict.fromkeys([url for url in linkedin_urls])))
    return linkedin_urls_no_rep


def login(driver, user, pwd):
    """
    Type user email and password in the relevant fields and
    perform log in on linkedin.com by using the given credentials.

    """
    username = driver.find_element_by_class_name('login-email')
    username.send_keys(user)
    sleep(0.5)
    password = driver.find_element_by_class_name('login-password')
    password.send_keys(pwd)
    sleep(0.5)
    sign_in_button = driver.find_element_by_xpath('//*[@type="submit"]')
    sign_in_button.click()


def get_job_title(selector):
    """
    Get the job title of the user whose profile page is being scraped

    """
    job_title = selector.xpath(
        '//*[starts-with(@class, "pv-top-card-section__headline"' +
        ')]/text()').extract_first()
    if job_title:
        job_title = job_title.strip()
    job_title = validate_field(job_title)
    return job_title


def get_location(selector):
    """
    Get the location of the user whose profile page is being scraped.

    """
    location = selector.xpath(
        '//*[starts-with(@class, ' +
        '"pv-top-card-section__location")]/text()').extract_first()
    if location:
        location = location.strip()
    location = validate_field(location)
    return location


def get_degree(soup):
    """
    Get the last degree of the user whose profile page
    is being scraped.

    """
    degree_tags = soup.find_all(class_="pv-entity__degree-name")
    if len(degree_tags) != 0:
        degree = degree_tags[0].get_text().split('\n')[2]
        degree = validate_field(degree)
    else:
        degree = ''
    return degree


def scroll_to_end(driver):
    """
    Scroll until the end of a web page by sending the keys PAGE_DOWN
    until the end of the page has been reached.

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

    """
    button_found = False
    button_element = None
    try:
        button_element = WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((
                By.XPATH, "//button[@class=" +
                "'pv-profile-section__card-action-bar " +
                "pv-skills-section__additional-skills " +
                "artdeco-container-card-action-bar']")))
        button_found = True
    except TimeoutException:
        pass
    return button_found, button_element


def get_skills(driver):
    """
    Get the skills of the user whose profile page is being scraped.
    Scroll down the page by sending the PAGE_DOWN button
    until either the "show more" button in the skills section
    has been found, or the end of the page has been reached
    Return a list of skills.

    """
    skills = []
    button_found = False
    endofpage_reached = False
    attempt = 0
    MAX_ATTEMPTS = 3
    delay = 3 # seconds
    body = driver.find_element_by_tag_name("body")
    last_height = driver.execute_script(
        "return document.body.scrollHeight")
    while not button_found:
        body.send_keys(Keys.PAGE_DOWN)
        sleep(2)
        new_height = driver.execute_script(
            "return document.body.scrollHeight")
        button_found, showmore_button = is_button_found(driver, delay)
        if button_found:
            driver.execute_script("arguments[0].click();",
                                  showmore_button)
            sleep(2)
            soup = bs(driver.page_source, 'html.parser')
            skills_tags = soup.find_all(
                class_="pv-skill-category-entity__name-text")
            skills = [item.get_text(strip=True)
                      for item in skills_tags]
            skills = [validate_field(skill) for skill in skills]
        if new_height == last_height:
            attempt += 1
            if attempt == MAX_ATTEMPTS:
                endofpage_reached = True
        else:
            last_height = new_height
        if button_found or endofpage_reached:
            break
    return skills


def get_languages(soup):
    """
    Get the languages in the "Accomplishments" section
    of the user whose profile page is being scraped.
    Look for the accomplishment tags first, and get all the language
    elements from them.
    Return a list of languages.

    """
    try:
        accomplishment_tags = soup.find_all(
            class_='pv-accomplishments-block__list-container')
        languages = [[lang_tag.get_text()
                      for lang_tag in a.find_all('li')]
                     for a in accomplishment_tags
                     if a['id'] == "languages-expandable-content"][0]
        languages = [validate_field(language) for language in languages]
    except IndexError:
        languages = []
    return languages


def get_name(selector):
    """
    Get the name of the user whose profile page is being scraped.

    """
    name = selector.xpath(
        '//*[starts-with(@class' +
        ', "pv-top-card-section__name")]/text()').extract_first()
    if name:
        name = name.strip()
    name = validate_field(name)
    return name


def scrape_url(query, url, driver):
    """
    Get the user data for a given query and linkedin URL.
    Call get_name() and get_job_title() to get name and
    job title, respectively. Scroll down the given URL
    to make the skill-section HTML code appear;
    call get_skills() and get_degree() to extract the user skills
    and their degree, respectively. Scroll down the page until its
    end to extract the user languages by calling
    get_languages().
    Finally, return a dictionary with the extracted data.

    """
    attempt = 0
    MAX_ATTEMPTS = 3
    success = False
    while not success:
        try:
            attempt += 1
            driver.get(url)
            sleep(2)
            sel = Selector(text=driver.page_source)
            name = get_name(sel)
            job_title = get_job_title(sel)
            location = get_location(sel)
            driver.execute_script("document.body.style.zoom='50%'")
            sleep(3)
            skills = get_skills(driver)
            soup = bs(driver.page_source, 'html.parser')
            degree = get_degree(soup)
            scroll_to_end(driver)
            languages = get_languages(soup)
            user_data = {
                "URL": url,
                "name": name,
                "query": query.split('AND ')[-1].replace('\"', ''),
                "job_title": job_title,
                "degree": degree,
                "location": location,
                "languages": languages,
                "skills": skills
            }
            success = True
        except TimeoutException as e:
            print("\nINFO :: TimeoutException raised while " +
                  "getting URL\n" + url)
            print("INFO :: Attempt n." + str(attempt) + " of " +
                str(MAX_ATTEMPTS) + "\nNext attempt in 60 seconds")
            sleep(60)
        if success:
            break
        if attempt == MAX_ATTEMPTS:
            print("INFO :: Max number of attempts reached. Skipping URL"
                  "User data will be empty.")
            user_data = {}
    return user_data


def print_user_data(user_data):
    """
    Print the user data returned by scrape_url().

    """
    print()
    for key in user_data:
        print(key + ": " + str(user_data[key]))


def save_json(file_path, dictionary):
    """
    Save a json file at a given path.

    """
    with open(file_path, 'w') as f:
        json.dump(dictionary, f, ensure_ascii=False,
                  indent=2, separators=(',', ': '))


def get_unseen_urls(logdir, urls):
    """
    Get a list of URLs that have not already been scraped.
    Loop over all the log files and create a list with all the
    URLs already scraped.
    Get the difference of such list and the list of all the URLs
    for a given query.
    Return a list of URLs which have not already been scraped.

    """
    unseen_urls = []
    for logfile in os.listdir(logdir):
        with open(logdir + logfile, 'r') as logfile:
            data = json.load(logfile)
            if data["URL"] not in urls:
                unseen_urls.append(data["URL"])
    return unseen_urls


def make_dataset(logdir, outfile):
    """
    Write all the scraped data to disk by looping over all the single
    user files saved within the LOGDIR.

    """
    data = []
    print("INFO :: Creating dataset")
    for logfile in os.listdir(logdir):
        with open(logdir + logfile, 'r') as logfile:
            user_data = json.load(logfile)
        data.append(user_data)
    save_json(outfile, data)
    print("INFO :: Dataset saved at " + outfile)
