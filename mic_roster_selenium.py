# -*- coding: utf-8 -*-
"""
Mic Roster Web Scraper
======================

A module for logging into the Mic Roster website and fetching shift information.

This module is designed to scrape the Mic Roster website to log in and extract shift information,
utilizing the requests and BeautifulSoup libraries. Functions include creating a BeautifulSoup object
from an HTTP response, extracting VIEWSTATE and EVENTVALIDATION values, logging into the website,
processing calendar data, and a main function to coordinate these actions.

Functions
---------
make_soup(response)
    Creates a BeautifulSoup object from an HTTP response.
get_view_event(soup)
    Extracts VIEWSTATE and EVENTVALIDATION values from a BeautifulSoup object.
login(url)
    Logs into the Mic Roster website using provided credentials.
process_response_cal(response)
    Processes and prints calendar data (shifts) from an HTTP response.
main()
    Coordinates the overall process of logging in and scraping shift information.

Author: matthewpicone
Date: 1/12/2023
"""
import time
import requests
from bs4 import BeautifulSoup
import credentials as cr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options  # Import for Chrome options

login_url = 'https://ess.tmc.tambla.net/Microster.SelfService/Default.aspx'
roster_url = 'https://ess.tmc.tambla.net/Microster.SelfService/MyRoster2.aspx'

session = requests.Session()

# Configure Chrome to run in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure Chrome runs headless
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, REQUIRED for Docker and some Linux environments
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
chrome_options.add_argument('--disable-gpu')  # Required for some versions of Chrome to run headless
chrome_options.add_argument('start-maximized')
chrome_options.add_argument('disable-infobars')
chrome_options.add_argument('--disable-extensions')

# Initialize the Chrome driver with options
driver = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)

# The rest of your script remains the same...



def make_soup(response):
    """
    Create a BeautifulSoup object from an HTTP response.

    Given an HTTP response from the requests library, this function creates and
    returns a BeautifulSoup object, which is used for parsing HTML content.

    Parameters
    ----------
    response : Response
        The HTTP response object from the requests' library.

    Returns
    -------
    BeautifulSoup
        A BeautifulSoup object for parsing HTML content.
    """
    try:
        return BeautifulSoup(response.text, 'html.parser')
    except AttributeError:
        return BeautifulSoup(response, 'html.parser')


def get_view_event(soup):
    """
    Extract VIEWSTATE and EVENTVALIDATION values from a BeautifulSoup object.

    This function parses a BeautifulSoup object to find and return the values
    of the `__VIEWSTATE` and `__EVENTVALIDATION` form fields, which are often
    required for POST requests in ASP.NET websites.

    Parameters
    ----------
    soup : BeautifulSoup
        The BeautifulSoup object representing a web page.

    Returns
    -------
    tuple of str
        A tuple containing the VIEWSTATE and EVENTVALIDATION values.
    """
    v = soup.find('input', {'name': '__VIEWSTATE'}).get('value')
    e = soup.find('input', {'name': '__EVENTVALIDATION'}).get('value')
    return v, e


def login(url):
    driver.get(url)
    # Wait for the login elements to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'ctl00$ContentPlaceHolder1$txtPersonnelId'))
    )
    # Fill in login form and submit
    driver.find_element_by_name('ctl00$ContentPlaceHolder1$txtPersonnelId').send_keys(cr.credentials.username)
    driver.find_element_by_name('ctl00$ContentPlaceHolder1$txtPassword').send_keys(cr.credentials.password)
    driver.find_element_by_name('ctl00$ContentPlaceHolder1$btnLogin').click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_calendar_lnkNextMonth"))
    )
    return driver.page_source


def fetch_next_page_html(button_name):
    # Navigate to the next page
    next_page_button = driver.find_element_by_id(button_name)
    next_page_button.click()
    time.sleep(1)
    # Return the HTML of the page
    return driver.page_source

def process_response_cal(response):
    """
    Extract and process calendar data (shifts) from an HTTP response.

    This function processes the response from the shift information page,
    extracting and printing the calendar data including the shifts.

    Parameters
    ----------
    response : Response
        The HTTP response object containing calendar data.

    Returns
    -------
    None
    """
    soup = make_soup(response)
    month_heading = soup.find('span', id='ctl00_ContentPlaceHolder1_calendar_lblCurrentMonth')
    if month_heading:
        month = month_heading.get_text(strip=True)
        print(f"Month Heading: {month}")
    else:
        month = None

    cell_data = {}
    date = 1
    for cell in range(1, 40):
        cell_id = f"ctl00_ContentPlaceHolder1_calendar_DateCell{cell}"
        cell_content = soup.find('td', id=cell_id)
        if cell_content:
            div_content = cell_content.find('div')
            cell_text = div_content.get_text(strip=True) if div_content else ""
            cell_text = cell_text.replace(")", ") ") if ")" in cell_text else cell_text
            cell_data[date] = cell_text
            if cell_text:
                if date < 10:
                    d = f"0{date}"
                else:
                    d = date
                print(f"{d} {month}:  Shift: {cell_text}")
                date += 1


def main():
    """
    Main function for web scraping to fetch shift information.

    This function orchestrates the process of logging into the Mic Roster
    website and scraping shift information. It maintains a session and
    repeatedly fetches and processes shift data until the user decides to exit.

    Parameters
    ----------

    Returns
    -------
    None
    """
    process_response_cal(login(login_url))
    # <a id="ctl00_ContentPlaceHolder1_calendar_lnkPreviousMonth" href="javascript:__doPostBack('ctl00$ContentPlaceHolder1$calendar$lnkPreviousMonth','')">January 2024</a>
    time.sleep(1)
    # input()
    process_response_cal(fetch_next_page_html("ctl00_ContentPlaceHolder1_calendar_lnkNextMonth"))
    time.sleep(2)
    for i in range(24):
        process_response_cal(fetch_next_page_html("ctl00_ContentPlaceHolder1_calendar_lnkPreviousMonth"))
        time.sleep(2)

    driver.quit()




if __name__ == '__main__':
    main()

