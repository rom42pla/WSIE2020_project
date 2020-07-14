# -*- coding: utf-8 -*-
"""FourSquare scraper.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1o7q_0QGdTJx95mlyVVmCcSA3cBRvtwv9
"""

import requests, json, bs4, re, copy, time, traceback, os
from pprint import pprint

seeds = ["201739388"]
frontier, visited = list(copy.deepcopy(seeds)), set()
assets_folder = "./assets"
pois_filepath, users_filepath, frontier_filepath = f"{assets_folder}/4square_pois_file.json", f"{assets_folder}/4square_users.json", f"{assets_folder}/4square_frontier.json"
pois, users = {}, {}

if os.path.isfile(pois_filepath) and os.path.isfile(users_filepath) and os.path.isfile(frontier_filepath):
    with open(pois_filepath, mode="r", encoding="utf-8") as pois_file:
        pois = json.load(pois_file)
    with open(users_filepath, mode="r", encoding="utf-8") as users_file:
        users = json.load(users_file)
        visited = set(users.keys())
    with open(frontier_filepath, mode="r", encoding="utf-8") as frontier_file:
        frontier = json.load(frontier_file)


starting_time = time.time()
while len(frontier) > 0:
    user_id = frontier.pop()
    if user_id in visited: 
        continue
    visited.add(user_id)
    user = {
        "infos": {},
        "pois": [],
        "followers": [],
        "followings": [] 
    }

    try:
        r = requests.get(f"https://api.foursquare.com/v2/users/{user_id}?locale=it&explicit-lang=true&v=20200712&id=380537407&limit=197&afterMarker=&m=foursquare&wsid=DSEKLW5VDCBYM3VMVVFTTPUPLHYEEQ&oauth_token=QEJ4AQPTMMNB413HGNZ5YDMJSHTOHZHMLZCAQCCLXIX41OMP")
        user_infos = json.loads(r.text)["response"]["user"]
        formatted_user_infos = {
            "first_name": user_infos["firstName"] if "firstName" in user_infos.keys() else None,
            "last_name": user_infos["lastName"] if "lastName" in user_infos.keys() else None,
            "gender": user_infos["gender"] if "gender" in user_infos.keys() else None,
            "home_city": user_infos["homeCity"] if "homeCity" in user_infos.keys() else None
        }
        user["infos"] = formatted_user_infos

        r = requests.get(f"https://api.foursquare.com/v2/users/{user_id}/tips?locale=it&explicit-lang=true&v=20200712&id=380537407&limit=197&afterMarker=&m=foursquare&wsid=DSEKLW5VDCBYM3VMVVFTTPUPLHYEEQ&oauth_token=QEJ4AQPTMMNB413HGNZ5YDMJSHTOHZHMLZCAQCCLXIX41OMP")
        tips = json.loads(r.text)["response"]["tips"]["items"]
        for tip in tips:
            tip_id = tip["venue"]["id"]
            formatted_tip = {
                "name": tip["venue"]["name"],
                "categories": [category["name"] for category in tip["venue"]["categories"]],
                "stats": {
                    "rating": tip["venue"]["rating"] if "rating" in tip["venue"].keys() else None,
                    "popularity": tip["venue"]["popularityByGeo"] if "popularityByGeo" in tip["venue"].keys() else None,
                    "checkins_count": tip["venue"]["stats"]["checkinsCount"] if "checkinsCount" in tip["venue"]["stats"].keys() else None,
                },
                "address": {
                    "address": tip["venue"]["location"]["address"] if "address" in tip["venue"]["location"].keys() else None,
                    "zip": tip["venue"]["location"]["postalCode"] if "postalCode" in tip["venue"]["location"].keys() else None,
                    "city": tip["venue"]["location"]["city"] if "city" in tip["venue"]["location"].keys() else None,
                    "country": tip["venue"]["location"]["country"] if "country" in tip["venue"]["location"].keys() else None,
                    "latitude": tip["venue"]["location"]["lat"] if "lat" in tip["venue"]["location"].keys() else None,
                    "longitude": tip["venue"]["location"]["lng"] if "lng" in tip["venue"]["location"].keys() else None
                }
            }
            pois[tip_id] = formatted_tip 
            user["pois"] += [tip_id]
        

        r = requests.get(f"https://api.foursquare.com/v2/users/{user_id}/followers?locale=it&explicit-lang=true&v=20200712&id=380537407&limit=197&afterMarker=&m=foursquare&wsid=DSEKLW5VDCBYM3VMVVFTTPUPLHYEEQ&oauth_token=QEJ4AQPTMMNB413HGNZ5YDMJSHTOHZHMLZCAQCCLXIX41OMP")
        followers = json.loads(r.text)["response"]["followers"]["items"]
        for follower_user in followers:
            follower_user_id = follower_user["user"]["id"]
            if follower_user_id not in frontier and follower_user_id not in visited:
                frontier += [follower_user_id]
            user["followers"] += [follower_user_id]


        r = requests.get(f"https://api.foursquare.com/v2/users/{user_id}/following?locale=it&explicit-lang=true&v=20200712&id=380537407&limit=197&afterMarker=&m=foursquare&wsid=DSEKLW5VDCBYM3VMVVFTTPUPLHYEEQ&oauth_token=QEJ4AQPTMMNB413HGNZ5YDMJSHTOHZHMLZCAQCCLXIX41OMP")
        following = json.loads(r.text)["response"]["following"]["items"]
        for following_user in following:
            following_user_id = following_user["user"]["id"]
            if following_user_id not in frontier and following_user_id not in visited:
                frontier += [following_user_id]
            user["followings"] += [following_user_id]

        users[user_id] = user

        minutes_passed = (time.time() - starting_time)/60
        print(f"{user_id} has {len(followers)} followers and {len(following)} following and {len(tips)} tips")
        print(f"|frontier| = {len(frontier)}, |visited| = {len(visited)}")
        print(f"Time elapsed = {round(minutes_passed, 1)} minutes")
        time.sleep(0.1)

        # saves results to a file, once in a while
        if len(visited) % 20 == 0:
            with open(pois_filepath, mode="w", encoding="utf-8") as pois_file:
                json.dump(pois, pois_file, indent=4, ensure_ascii=False)
            with open(users_filepath, mode="w", encoding="utf-8") as users_file:
                json.dump(users, users_file, indent=4, ensure_ascii=False)
            with open(frontier_filepath, mode="w", encoding="utf-8") as frontier_file:
                json.dump(frontier, frontier_file, indent=4, ensure_ascii=False)
        
    except:
        print(f"There was an error parsing user {user_id}")
        print(traceback.format_exc())
