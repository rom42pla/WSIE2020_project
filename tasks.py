from providers.StorageProvider import StorageProvider
from classes.User import User
from classes.Location import Location
from classes.UsersGraph import UsersGraph
from pprint import pprint

folder_assets = "./assets"
file_followees, file_locations, file_user_locations = f"{folder_assets}/followees.json", \
                                                      f"{folder_assets}/locations.json", \
                                                      f"{folder_assets}/user_locations.json"
file_cosine_similarities = f"{folder_assets}/cosine_similarities.csv"
storage = StorageProvider(main_folder=folder_assets)

followees, locations, user_locations = storage.read_or_create_file(filepath=file_followees), \
                                       storage.read_or_create_file(filepath=file_locations), \
                                       storage.read_or_create_file(filepath=file_user_locations)

print(f"There are {len(locations.keys())} unique locations and {len(followees.keys())} unique users, "
      f"of which {'%0.1f' % ((len(user_locations.keys())/len(followees.keys()))*100)}% of them has logged into a location")

users_graph = UsersGraph()
for user_id in followees.keys():
    # eventually creates the new user as a node
    if not users_graph.get_user(user_id):
        user = User(id=user_id)
        # retrieves locations logged by the user
        if user_id in user_locations:
            for location_raw in user_locations[user_id]:
                location = Location(city=location_raw["city"], country=location_raw["country"])
                user.add_location(location)
        users_graph.add_user(user)
    # retrieves followees
    for followee_id in followees[user_id]:
        # eventually creates the new followee as a node
        if not users_graph.get_user(followee_id):
            followee = User(id=followee_id)
            # retrieves locations logged by the user
            if followee_id in user_locations:
                for location_raw in user_locations[followee_id]:
                    location = Location(city=location_raw["city"], country=location_raw["country"])
                    followee.add_location(location)
            users_graph.add_user(followee)

        users_graph.add_edge(user_id_from=user_id, user_id_to=followee_id)

""" cosine similarities """
similarities = users_graph.get_cosine_similarities(filepath=file_cosine_similarities)


a=2

