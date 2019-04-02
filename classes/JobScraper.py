"""
A class to define the methods to scrape LinkedIn job web pages

"""
class JobScraper(object):
    def __init__(self, soup, url, query):
        """
        Initialize the class

        """
        self.soup = soup
        self.url = url
        self.query = query


    def get_job_skills(self):
        """
        Get the skills required by the job offer being scraped.
        Return a list of skills.

        """
        requested_skills = [rq.get_text() for rq in self.soup.find_all(
            class_="jobs-ppc-criteria__value")]
        return requested_skills



    def get_job_title(self):
        """
        Get the job title of the job page is being scraped.
        Return a string containing the job title

        """
        try:
            job_title = self.soup.find_all(
                class_="jobs-top-card__job-title")[0].get_text()
        except IndexError:
            job_title = ""
        return job_title


    def get_job_location(self):
        """
        Get the location of the job offer being scraped.
        Return a string containing the location.

        """
        def validate_location(loc):
            """
            Validate the location by checking that the string extracted
            by the preferred "jobs-top-card__exact-location" HTML class
            is not empty, otherwise get the location string from the 
            "jobs-top-card__bullet" HTML class

            """
            if loc:
                return loc
            else:
                try:
                    loc = [l.get_text().strip()
                           for l in self.soup.find_all(
                               class_="jobs-top-card__bullet")][0]
                except IndexError:
                    loc = ""
            return loc
        try:
            location = [l.get_text().strip() 
                        for l in self.soup.find_all(
                            class_="jobs-top-card__exact-location")][0]
        except IndexError:
            location = ""
        return validate_location(location)


    def get_job_data(self):
        """
        Get the job data by using the get* methods of the class. 
        Return a dictionary

        """
        skills = self.get_job_skills()
        if len(skills) == 0:
            return {}
        else:
            job_data = {
                "URL": self.url,
                "query": self.query,
                "job_title": self.get_job_title(),
                "location": self.get_job_location(),
                "skills": skills
            }
            return job_data
