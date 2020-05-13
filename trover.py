from bs4 import BeautifulSoup
import requests
import re
from providers.TroverProvider import TroverProvider
from pprint import pprint
import copy
import os

assets_folder = "./assets"
trover_provider = TroverProvider(assets_folder=assets_folder)

while len(trover_provider.get_frontier()) > 0:
    user = trover_provider.pop_first_user_in_frontier()
    if user in (trover_provider.get_visited_users() | set(trover_provider.get_frontier())):
        print(f"User {user} has already been visited (|visited|={len(trover_provider.get_visited_users())})")
        continue
    print(f"Scraping user {user} (|frontier|={len(trover_provider.get_frontier())}, |visited|={len(trover_provider.get_visited_users())})...")
    _ = trover_provider.get_pois(username=user)
    followees = trover_provider.get_followees(username=user)
    trover_provider.add_to_frontier(followees)

