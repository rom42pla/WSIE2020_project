import json
from bs4 import BeautifulSoup
import re
import os
from interfaces.Provider import Provider
from .MapsProvider import MapsProvider
from .StorageProvider import StorageProvider


class TroverProvider(Provider):
    def __init__(self, assets_folder):
        super().__init__()
        self.main_url = "https://www.trover.com"
        self.top_users_url = f"{self.main_url}/users"
        self.user_url = f"{self.main_url}/u"
        self.maps = MapsProvider()

        self.storage = StorageProvider(assets_folder)
        self.frontier_filepath = self.storage.main_folder + "/frontier.txt"
        self.locations_filepath = self.storage.main_folder + "/locations.json"
        self.followees_filepath = self.storage.main_folder + "/followees.json"
        self.user_locations_filepath = self.storage.main_folder + "/user_locations.json"

        self.frontier = []
        self.init_frontier()
        self.followees = self.storage.read_or_create_file(self.followees_filepath)
        self.user_locations = self.storage.read_or_create_file(self.user_locations_filepath)
        self.locations = self.storage.read_or_create_file(self.locations_filepath)

    def init_frontier(self):
        if not os.path.isfile(self.frontier_filepath):
            self.frontier = self.storage.read_or_create_file(self.frontier_filepath)
            seeds = self.get_top_users()
            self.storage.save_to_file(filepath=self.frontier_filepath, data=list(seeds))
        self.frontier = self.storage.read_or_create_file(self.frontier_filepath)
        return self.frontier

    def get_frontier(self):
        return self.frontier

    def pop_first_user_in_frontier(self):
        username = self.get_frontier().pop(0)
        return username

    def add_to_frontier(self, users):
        if isinstance(users, str):
            users = [users]
        users = [user for user in users if user not in (self.get_visited_users() | set(self.get_frontier()))]
        self.frontier += users
        self.storage.save_to_file(filepath=self.frontier_filepath, data=self.frontier)

    def get_locations(self):
        return self.locations

    def add_location(self, location_raw: str, location_parsed: {}):
        self.locations[location_raw] = location_parsed
        self.storage.save_to_file(self.locations_filepath, self.locations)

    def get_visited_users(self):
        return set(self.followees.keys())

    def get_user_locations(self):
        return self.user_locations

    def add_user_location(self, username: str, location: {}):
        if username not in self.get_user_locations():
            self.user_locations[username] = [location]
        else:
            self.user_locations[username] += [location]
        self.storage.save_to_file(self.user_locations_filepath, self.get_user_locations())

    def add_followee(self, username: str, followee_username: str):
        if username not in self.get_visited_users():
            self.followees[username] = [followee_username]
        else:
            if followee_username not in self.followees[username]:
                self.followees[username] += [followee_username]
            else:
                return
        self.storage.save_to_file(self.followees_filepath, self.followees)

    def get_user_url(self, username):
        url = f"{self.user_url}/{username}"
        return url

    def get_user_pois_url(self, username):
        url = f"{self.get_user_url(username)}/photos"
        return url

    def get_user_followees_url(self, username):
        url = f"{self.get_user_url(username)}/following"
        return url

    def get_top_users(self):
        top_users = set()
        page = BeautifulSoup(self.request(self.top_users_url), 'html.parser')
        users = page.find_all("div", {"class": "user-block-lg"})
        for user in users:
            top_users.add(
                user.find("a", {"href": re.compile(r"https:\/\/www\.trover\.com\/u\/.*")})["href"].split("/")[-1])
        return top_users

    def get_pois(self, username):
        user_url = self.get_user_pois_url(username)
        page_html = self.open_page(user_url, scroll=True, max_iters=5)
        page = BeautifulSoup(page_html, 'html.parser')
        pois = page.find_all("div", {"class": "colwall-el-discovery"})
        pois_parsed, pois_in_memory = [], 0
        for i_poi, poi in enumerate(pois):
            print(f"\r\t...geocoding point of interest {i_poi + 1} of {len(pois)} ({pois_in_memory} from memory)", end="")
            # scrapes locations from HTML
            place, vicinity = "", ""
            try:
                place = poi.find('div', {'class': 'location-place'}).get_text()
            except AttributeError:
                pass
            try:
                vicinity = poi.find('div', {'class': 'location-vicinity'}).get_text()
            except AttributeError:
                pass
            if not place and not vicinity:
                continue
            location_raw = f"{place} {vicinity}"
            location_raw = self.maps.clean_location_string(location_raw)

            # retrieves geocoded location from storage or a maps provider
            try:
                location = self.get_locations()[location_raw]
                pois_in_memory += 1
            except KeyError:
                location = self.maps.parse_location(location=location_raw)
                if location:
                    self.add_location(location_raw=location_raw, location_parsed=location)
            if location:
                pois_parsed += location
                self.add_user_location(username=username, location=location)
        print()
        return pois_parsed

    def get_followees(self, username: str):
        if username in self.get_visited_users():
            followees_parsed = self.followees[username]
            print(f"\t...retrieved {len(followees_parsed)} followees from local storage")
        else:
            user_url = self.get_user_followees_url(username)
            page_html = self.open_page(user_url, scroll=True, max_iters=5)
            page = BeautifulSoup(page_html, 'html.parser')
            followees = page.find_all("div", {"class": "user-block"})
            followees_parsed = []
            for i_followee, followee in enumerate(followees):
                print(f"\r\t...retrieving followee {i_followee + 1} of {len(followees)}", end="")
                # scrapes usernames from HTML
                try:
                    followee_username = followee.find('a', {'class': 'name'})["href"].split("/")[-1]
                except AttributeError:
                    followee_username = None
                if not followee_username:
                    continue
                else:
                    followees_parsed += [followee_username]
                    self.add_followee(username=username, followee_username=followee_username)
            if len(followees_parsed) > 0:
                print()
        return followees_parsed
