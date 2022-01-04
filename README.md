# LinkedIn Scraper

## Disclaimer
Scraping data off of LinkedIn is against their User Agreement. This is purely intended for educational purposes.

## Acknowledgements
Thanks to David Craven who I took inspiration from ([link here](https://www.linkedin.com/pulse/how-easy-scraping-data-from-linkedin-profiles-david-craven/))

## What is this? 
This was a tool capable of scraping linkedin profiles in 2018/2019. As of today, this repository can only represent a starting point, but it will most likely not work as expected.

## Dependencies 
It is based on selenium and BeautifulSoup

## How to use
Back in the days, you would first download the Chrome Driver from [here](http://chromedriver.chromium.org/) and extract it to your favourite location.
Create a python3 virtual environment following [this](https://docs.python.org/3/tutorial/venv.html).
Within the virtual environment
```pip install -r requirements.txt```

Edit the `conf.json` config file accordingly specifying the chrome bin path, e.g. by typying 
```which google-chrome``` in a UNIX shell command line, the chrome driver path, the desired queries
and so forth. 

Ultimately to scrape users, you would've run 
```python scrape_users.py --conf conf.json```
or jobs
```python scrape_jobs.py --conf conf.json```
