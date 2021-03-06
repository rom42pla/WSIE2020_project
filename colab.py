# -*- coding: utf-8 -*-
"""WSIE2020_project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AwOp6H_Yfgh5FyUr0zaJk8kdC2SDOu-d

# Initial setup

## Generic imports
"""

# utility
import re
import time
from pprint import pprint
import json
from tqdm import tqdm
!pip install unidecode
from unidecode import unidecode
import os
import sys
sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')

"""## Storage"""

def read_or_create_file(filepath):
  content = {}
  if not os.path.isfile(filepath):
    with open(filepath, 'w') as fp:
      json.dump(content, fp)
  else:
    with open(filepath, 'r') as fp:
      content = json.load(fp)
  return content

def save_to_file(filepath, data):
  with open(filepath, 'w') as fp:
    json.dump(data, fp, indent=4)

from google.colab import drive
drive.mount("/content/drive")
main_folder = "/content/drive/My Drive/Colab Notebooks/WSIE2020_project/"

locations_filepath, locations = main_folder + "locations.json", {}
followings_filepath, followings = main_folder + "followings.json", {}
user_locations_filepath, user_locations = main_folder + "user_locations.json", {}

followings = read_or_create_file(followings_filepath)
user_locations = read_or_create_file(user_locations_filepath)
locations = read_or_create_file(locations_filepath)

"""## Scraping"""

!pip install selenium
!apt-get update
!apt install chromium-chromedriver
#!cp /usr/lib/chromium-browser/chromedriver /usr/bin
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver', options=options)
driver.implicitly_wait(10)

instagram_url = "https://www.instagram.com"

"""## Maps"""

def parse_location(location):
  location = clean_location_string(location)
  location_parsed = {}
  if location in locations.keys():
    location_parsed = locations[location]
  else:
    location_description = geocoder.tomtom(location, key=maps_key).json
    if not location_description:
      return None
    location_parsed["city"] = unidecode(location_description["city"]) if "city" in location_description.keys() else None
    location_parsed["country"] = unidecode(location_description["country"]) if "country" in location_description.keys() else None
    add_city_alias(location, location_parsed)
  return location_parsed

def clean_location_string(raw_location):
  location = unidecode(raw_location.strip().lower())
  location = re.sub('[\W]+', " ", location).split()
  location = " ".join(location)
  return location

def add_city_alias(alias, data):
  locations[alias] = data
  save_to_file(locations_filepath, locations)

def add_user_location(username, data):
  if username not in user_locations:
    user_locations[username] = [data]
  else:
    user_locations[username] += [data]
  save_to_file(user_locations_filepath, user_locations)

!pip install geocoder
import geocoder

maps_key = "TG6c7Awx0fCAPqpnYxZytGKNXNABEzaQ"

"""## Instagram provider"""

instagram_username, instagram_password = "kapela__________________", "password1234"

def add_following(username, followee):
    if username not in followings:
        followings[username] = [followee]
    else:
        followings[username] += [followee]
    save_to_file(followings_filepath, followings)


def login(driver, username, password):
    url = f"{instagram_url}"
    driver.get(url)
    time.sleep(3)
    for item in driver.find_elements_by_tag_name("input"):
        if item.get_attribute("name") == "username":
            item.send_keys(username)
        if item.get_attribute("name") == "password":
            item.send_keys(password)
    for item in driver.find_elements_by_tag_name("button"):
        if item.get_attribute("type") == "submit":
            item.click()
            print("Logged in!")
    time.sleep(3)

def get_posts_from_page(driver, url, max_scrolls=0):
    assert max_scrolls >= 0
    driver.get(url)
    posts = set()
    scrolls, cooldown = 0, 2
    prev_following = -1
    last_height = driver.execute_script("return document.body.scrollHeight")
    while scrolls <= max_scrolls:
        scrolls += 1
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(cooldown)
        soup = BeautifulSoup(driver.page_source)
        for element in soup.find_all("a", {"href" : re.compile('/p/[^/]*/')}):
            posts.add(f"{instagram_url}{element.get('href', default=None)}")
        if len(posts) != 0 and prev_following == len(posts):
            break
        prev_following = len(posts)
    return posts

def get_info_from_post(driver, url):
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source)
    infos = {}
    # username
    print(url)
    infos["username"] = None
    for element in soup.find_all("a", {"href" : re.compile('/.*/')}):
        if f"/{element.get_text()}/" == element.get("href", default=None):
            infos["username"] = element.get_text()
            break
    # location
    location = soup.find("a", {"href" : re.compile('/explore/locations/\d*/.*')})
    infos["location"] = parse_location(location.get_text()) if location else None
    if infos["location"]:
        add_user_location(infos["username"], infos["location"])
    print(infos)
    return infos

def has_private_profile(driver, username):
    url = f"{instagram_url}/{username}"
    following = set()
    driver.get(url)
    following_link = driver.find_elements_by_css_selector(f"a[href='/{username}/following/']")
    try:
        following_link[0].click()
        return False
    except:
        return True


def get_following_users(driver, username, max_scrolls=10):
    assert max_scrolls >= 0
    if has_private_profile(driver, username):
        print(f"\n{username} has a private profile")
        return set()
    url = f"{instagram_url}/{username}"
    following = set()
    driver.get(url)

    scrolls, cooldown = 0, 1
    prev_following = -1
    while scrolls <= max_scrolls:
        scrolls += 1
        following_window = driver.find_element_by_css_selector("div[role='dialog']")
        user_area = following_window.find_elements_by_css_selector("li")
        if len(user_area) == 0:
            prev_following = len(user_area)
            time.sleep(cooldown)
            continue
        if len(user_area) != 0 and prev_following == len(user_area):
            break
        prev_following = len(user_area)
        user_area[-1].click()
        ActionChains(driver).move_to_element(user_area[-1]).key_down(Keys.PAGE_DOWN).perform()
        following = following | {user.text.split("\n")[0] for user in user_area}
        following = {followee for followee in following if followee}
        for followee in following:
            add_following(username, followee)
        time.sleep(cooldown)
    return following

"""# Dataset building

## Login to Instagram
"""

login(driver=driver, username=instagram_username, password=instagram_password)

"""## Retrieving initial seeds"""

initial_users = set()
posts = get_posts_from_page(driver=driver, url=f"{instagram_url}/explore/tags/igers/", max_scrolls=1)
for i, post in enumerate(posts):
    infos = get_info_from_post(driver=driver, url=post)
    initial_users.add(infos["username"])
    print(f"\rRetrieved {i+1} posts out of {len(posts)}...", end="")
print(initial_users)

"""## Main loop"""

frontier_users = list(initial_users)
while len(frontier_users) > 0:
    user = frontier_users.pop(0)
    print(user)
    if has_private_profile(driver, user):
        continue
    posts = get_posts_from_page(driver=driver, url=f"{instagram_url}/{user}", max_scrolls=100)
    for i, post in enumerate(posts):
        print(f"\rScraping post {i+1} of {len(posts)} from {user}...", end="")
        infos = get_info_from_post(driver=driver, url=post)
    following_users = get_following_users(driver=driver, username=user)
    print(f"\n{user} follows: {following_users}")
    if len(following_users) > 0:
        frontier_users += list(following_users)