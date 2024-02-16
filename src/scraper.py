import requests
from requests import Session
import json

import re
from bs4 import BeautifulSoup

class WikipediaScraper:
    """
    A scraper object for retrieving data about political leaders from an API and their Wikipedia pages.

    This class handles fetching cookies for API authentication, retrieving supported countries and leaders from the API, extracting the first paragraph of a leader's Wikipedia page, and saving this data into a JSON file.

    Parameters
    ----------
    base_url : str, optional
        The base URL of the API (default is "https://country-leaders.onrender.com").

    Attributes
    ----------
    base_url : str
        Base URL for the API.
    country_endpoint : str
        Endpoint for retrieving supported countries.
    leaders_endpoint : str
        Endpoint for retrieving leaders for a specific country.
    cookies_endpoint : str
        Endpoint for retrieving a valid cookie.
    leaders_data : dict
        A dictionary to store retrieved leaders data before saving.
    cookie : dict
        Cookie object used for API calls.
    session : requests.Session
        A requests session for making HTTP requests.

    Methods
    -------
    refresh_cookie()
        Fetches and updates the instance with a new cookie for authentication.
    get_countries()
        Returns a list of countries supported by the API.
    get_leaders(country: str)
        Populates the `leaders_data` attribute with leaders of a specified country.
    get_first_paragraph(wikipedia_url: str)
        Returns the first paragraph from a leader's Wikipedia page.
    to_json_file(filepath: str)
        Saves the `leaders_data` dictionary to a specified JSON file.

    Raises
    ------
    requests.exceptions.RequestException
        If an error occurs while making HTTP requests.
    """

    def __init__(self, base_url = "https://country-leaders.onrender.com"):
        self.base_url = base_url
        self.country_endpoint = "/countries"
        self.leaders_endpoint = "/leaders"
        self.cookies_endpoint = "/cookie"
        self.leaders_data = {}
        self.session = requests.Session()
        self.cookie = self.refresh_cookie()


    def refresh_cookie(self) -> object:
        cookie_url = f"{self.base_url}{self.cookies_endpoint}"
        self.cookie = self.session.get(cookie_url).cookies.get_dict()
        return self.cookie
    

    def get_countries(self) -> list:
        countries_url = self.base_url + self.country_endpoint
        countries_response = self.session.get(countries_url)
        countries = countries_response.json() if countries_response.ok else []
        return countries
    

    def get_leaders(self, country: str) -> None:
        leaders_url = self.base_url + self.leaders_endpoint
            
        if self.cookie is None or self.session is None:
            self.refresh_cookie()

        leaders_response = self.session.get(leaders_url, params={'country': country}, cookies=self.cookie)
        
        if leaders_response.ok:
            self.leaders_data[country] = leaders_response.json()
            for leader in self.leaders_data[country]:
                if 'wikipedia_url' in leader:
                    leader['wikipedia_intro'] = self.get_first_paragraph(leader['wikipedia_url'])
    
        self.to_json_file('leaders_data.json')


    def get_first_paragraph(self, wikipedia_url: str) -> str:

        response = self.session.get(wikipedia_url)

        if not response.ok:
            print("Failed to fetch Wikipedia page for URL:", wikipedia_url)
            return "No suitable paragraph found"

        leader_text = response.text
        soup = BeautifulSoup(leader_text, 'html.parser')

        first_paragraph = None # Create a first_paragraph variable to avoid errors
        for paragraph in soup.find_all('p'):
        # Check if the paragraph contains a <b> tag
            if paragraph.find('b'):
                first_paragraph = paragraph.text
                break

        if first_paragraph: # if first_paragraph is not empty, clean it with Regex

            first_paragraph = re.sub(r'\([^)]*\)', '', first_paragraph) # Remove content in parentheses
            first_paragraph = re.sub(r'\[[^\]]*\]', '', first_paragraph) # Remove content in brackets
            first_paragraph = re.sub(r'\s+', ' ', first_paragraph).strip() # Reduce multiple spaces to one
            first_paragraph = re.sub(r'\s+([,\.:\;!-])', r'\1', first_paragraph) # Remove space before punctuation
            first_paragraph = re.sub(r'\s+([,\.:\;!؟،-])', r'\1', first_paragraph) # Reduce multiple spaces to one in Arabic

        else: # avoid rising of an error
            first_paragraph = "No suitable paragraph found"

        return first_paragraph
    

    def to_json_file(self, filepath: str) -> None:

        with open(filepath, 'w', encoding='utf-8') as outfile:
            # Ensure ASCII characters are not escaped, and the output is nicely formatted
            json.dump(self.leaders_data, outfile, ensure_ascii=False, indent=4)
