"""
A class to define the methods to scrape LinkedIn user-profile webpages

"""
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from utils import validate_field, scroll_profile_page, is_button_found,\
    validate_user_data, filter_non_printable
from time import sleep
from bs4 import BeautifulSoup as bs


class UserScraper(object):
    def __init__(self, driver):
        self.driver = driver

    def get_name(self, soup):
        """
        Get the name of the user whose profile page is being scraped.

        """
        try:
            name_tag = soup.find_all(class_="pv-top-card-section__name")[0]
            name = name_tag.get_text(strip=True)
            return name
        except IndexError:
            return ""

    def get_job_title(self, soup):
        """
        Get the job title of the user whose profile
        page is being scraped

        """
        try:
            job_title_tag = soup.find_all(
                class_="pv-top-card-section__headline")[0]
            job_title = job_title_tag.get_text(strip=True)
            job_title = filter_non_printable(job_title)
            return job_title
        except IndexError:
            return ""

    def get_location(self, soup):
        """
        Get the location of the user whose profile
        page is being scraped.

        """
        try:
            location_tag = soup.find_all(
                class_="pv-top-card-section__location")[0]
            location = location_tag.get_text(strip=True)
            return location
        except IndexError:
            return ""

    def get_degree(self, soup):
        """
        Get the last degree of the user whose profile page
        is being scraped.

        """
        degree_tags = soup.find_all(
            class_="pv-entity__degree-name")
        if len(degree_tags) != 0:
            degree = degree_tags[0].get_text().split('\n')[2]
            degree = validate_field(degree)
        else:
            degree = ''
        return degree

    def get_skills(self):
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
        delay = 3  # seconds
        body = self.driver.find_element_by_tag_name("body")
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        while not button_found:
            body.send_keys(Keys.PAGE_DOWN)
            sleep(2)
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")
            button_found, showmore_button = is_button_found(
                self.driver, delay)
            if button_found:
                self.driver.execute_script("arguments[0].click();",
                                           showmore_button)
                sleep(2)
                soup = bs(self.driver.page_source, 'html.parser')
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

    def get_languages(self, soup):
        """
        Get the languages in the "Accomplishments" section
        of the user whose profile page is being scraped.
        Look for the accomplishment tags first, and get all the language
        elements from them.
        Return a list of languages.

        """
        languages = []
        accomplishment_tags = soup.find_all(
            class_="pv-accomplishments-block__list-container")
        for a in accomplishment_tags:
            try:
                if a["id"] == "languages-expandable-content":
                    languages = [l.get_text() for l in a.find_all("li")]
            except KeyError:
                pass
        return languages

    def scrape_user(self, query, url):
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
        user_data = {}
        while not success:
            try:
                attempt += 1
                self.driver.get(url)
                sleep(2)
                self.driver.execute_script(
                    "document.body.style.zoom='50%'")
                sleep(3)
                skills = self.get_skills()
                scroll_profile_page(self.driver)
                soup = bs(self.driver.page_source, 'html.parser')
                name = self.get_name(soup)
                job_title = self.get_job_title(soup)
                location = self.get_location(soup)
                degree = self.get_degree(soup)
                languages = self.get_languages(soup)
                user_data = {
                    "URL": url,
                    "name": name,
                    "query": query,
                    "job_title": job_title,
                    "degree": degree,
                    "location": location,
                    "languages": languages,
                    "skills": skills
                }
                success = True
            except TimeoutException:
                print("\nINFO :: TimeoutException raised while " +
                      "getting URL\n" + url)
                print("INFO :: Attempt n." + str(attempt) + " of " +
                      str(MAX_ATTEMPTS) +
                      "\nNext attempt in 60 seconds")
                sleep(60)
            if success:
                break
            if attempt == MAX_ATTEMPTS and not user_data:
                print("INFO :: Max number of attempts reached. " +
                      "Skipping URL" +
                      "\nUser data will be empty.")
        return validate_user_data(user_data)
