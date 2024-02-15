import requests
from requests import Session
import json

import re
from bs4 import BeautifulSoup


root_url = "https://country-leaders.onrender.com"
countries_url = root_url + "/countries"
leaders_url = root_url + "/leaders"


def get_cookies(session):
    """Fetches and returns new cookies required for authentication using a given session."""
    cookie_url = root_url + "/cookie"
    # Directly return the cookies obtained from the session request
    return session.get(cookie_url).cookies.get_dict()


def get_first_paragraph(wikipedia_url: str, session: requests.Session) -> str:
    """
    Fetches and cleans the first paragraph from a Wikipedia page.

    This function retrieves the Wikipedia page at the given URL, parses the HTML to find the first paragraph that contains bold text (usually the introductory paragraph), and cleans it by removing any content within parentheses or brackets, and adjusting spaces around punctuation.

    Parameters:
    - wikipedia_url (str): The URL of the Wikipedia page to process.

    Returns:
    - str: The cleaned text of the first paragraph. If no suitable paragraph is found, returns a message indicating no paragraph was found.

    Raises:
    - requests.exceptions.RequestException: If an error occurs while making the HTTP request.
    - Exception: For errors during HTML parsing or if BeautifulSoup is unable to parse the document.

    Example:
    >>> url = 'https://en.wikipedia.org/wiki/George_Washington'
    >>> print(get_first_paragraph(url))
    George Washington was an American political leader, military general, statesman, and Founding Father who served as the first president of the United States from 1789 to 1797...

    Note:
    This function depends on the 'requests' and 'BeautifulSoup' libraries for fetching and parsing the webpage, respectively. It assumes the webpage structure is consistent with Wikipedia's layout as of the time of writing. Changes to Wikipedia's layout may require adjustments to the parsing logic.
    """

    response = session.get(wikipedia_url)
    leader_text = response.text
    soup = BeautifulSoup(leader_text, 'html.parser')

    first_paragraph = None # Create a first_paragraph variable to avoid errors
    for paragraph in soup.find_all('p'):
    # Check if the paragraph contains a <b> tag
        if paragraph.find('b'):
            first_paragraph = paragraph.text
            break

    if first_paragraph: # if first_paragraph is not empty, transform text into more readable form

        first_paragraph = re.sub(r'\([^)]*\)', '', first_paragraph) # Remove content in parentheses
        first_paragraph = re.sub(r'\[[^\]]*\]', '', first_paragraph) # Remove content in brackets
        first_paragraph = re.sub(r'\s+', ' ', first_paragraph).strip() # Reduce multiple spaces to one
        first_paragraph = re.sub(r'\s+([,\.:\;!-])', r'\1', first_paragraph) # Remove space before punctuation
        first_paragraph = re.sub(r'\s+([,\.:\;!؟،-])', r'\1', first_paragraph) # Remove not needed space in Arabic

    else: # avoid rising of an error
        first_paragraph = "No suitable paragraph found"

    if not response.ok:
        print("Failed to fetch Wikipedia page for URL:", wikipedia_url)
        return "No suitable paragraph found"

    return first_paragraph


def get_leaders():
    """Retrieves the leaders for each country from an external API and saves them."""
    with requests.Session() as session:
        cookies = get_cookies(session)  # Fetch initial cookies
        session.cookies.update(cookies)  # Update session with fetched cookies

        countries_response = session.get(countries_url)
        countries = countries_response.json() if countries_response.ok else []

        leaders_per_country = {}
        for country in countries:
            leaders_response = session.get(leaders_url, params={'country': country})
            
            # Refresh cookies if expired and retry
            if leaders_response.status_code == 403:
                cookies = get_cookies(session)
                session.cookies.update(cookies)
                leaders_response = session.get(leaders_url, params={'country': country})
            
            if leaders_response.ok:
                leaders_info = leaders_response.json()
                for leader in leaders_info:
                    if 'wikipedia_url' in leader:
                        # Ensure session is passed to get_first_paragraph
                        leader['wikipedia_intro'] = get_first_paragraph(leader['wikipedia_url'], session)
                
                leaders_per_country[country] = leaders_info
        
        # Save the modified leaders data
        save(leaders_per_country)

        return leaders_per_country
    

def save(leaders_per_country: dict):
    """
    Saves the leaders_per_country dictionary to a JSON file with UTF-8 encoding.
    
    Parameters:
    - leaders_per_country (dict): The dictionary containing country leaders' information.
    """
    with open('leaders.json', 'w', encoding='utf-8') as outfile:
        # Ensure ASCII characters are not escaped, and the output is nicely formatted
        json.dump(leaders_per_country, outfile, ensure_ascii=False, indent=4)
