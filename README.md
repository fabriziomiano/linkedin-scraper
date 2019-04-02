# LIn Scraper

## Acknowledgements
Thanks to David Craven who I took inspiration from ([link here](https://www.linkedin.com/pulse/how-easy-scraping-data-from-linkedin-profiles-david-craven/))

## What is this? 
This is a tool capable of scraping linkedin profiles

## Dependencies 
It is based on selenium and BeautifulSoup

## How to use
First, download the Chrome Driver from [here](http://chromedriver.chromium.org/) and extract it to your favourite location.
Create a python3 virtual environment following [this](https://docs.python.org/3/tutorial/venv.html).
Within the virtual environment
```pip install -r requirements.txt```

Edit the `conf.json` config file accordingly specifying the chrome bin path, e.g. by typying 
```which google-chrome``` in a UNIX shell command line, the chrome driver path, the desired queries
and so forth. 

Finally, to scrape users run 
```python scrape_users.py --conf conf.json```
or jobs
```python scrape_jobs.py --conf conf.json```
