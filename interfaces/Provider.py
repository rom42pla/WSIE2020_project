import os
from abc import ABC
import requests
import time
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

class Provider(ABC):

    def __init__(self):
        self.browser = None
        self.scrolling_cooldown = 5

    def request(self, url):
        return requests.get(url).content

    def open_browser(self):
        if self.browser:
            self.close_browser()
        options, profile = webdriver.FirefoxOptions(), webdriver.FirefoxProfile()
        # disables images for performances reasons
        profile.set_preference("permissions.default.image", 2)
        # starts the browser
        browser = webdriver.Firefox(options=options, firefox_profile=profile)
        browser.maximize_window()
        browser.implicitly_wait(10)
        self.browser = browser
        return browser

    def close_browser(self):
        if self.browser:
            self.browser.quit()
            self.browser = None

    def get_browser(self):
        if self.browser:
            return self.browser
        else:
            return self.open_browser()

    def open_page(self, url, scroll=False, scroll_cooldown=1, max_iters=10):
        # retrieves the browser
        if not self.browser:
            self.open_browser()
        # opens the page in the browser
        self.browser.get(url)
        if scroll:
            # scrolls until a maximum of iterations are reached
            for _ in range(max_iters):
                # scrolls down
                for _ in range(10):
                    self.get_browser().find_element_by_css_selector("body").send_keys(Keys.PAGE_DOWN)
                # cooldown to let the page load
                time.sleep(scroll_cooldown)
        return self.browser.page_source


