import json
import requests
from requests import Session

from bs4 import BeautifulSoup
import re

from src.scraper import WikipediaScraper

scraper = WikipediaScraper()

countries = scraper.get_countries()

try:
    for country in countries:
        scraper.get_leaders(country)
    print('The data were obtained successfully.')

except:
    print("Something went wrong. Please, try again later.")
