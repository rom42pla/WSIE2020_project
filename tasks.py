from providers.StorageProvider import StorageProvider
from classes.User import User
from classes.Location import Location
from classes.UsersGraph import UsersGraph
from pprint import pprint

logs = True
top_scc_size = 10

folder_assets = "./assets"
file_followees, file_locations, file_user_locations = f"{folder_assets}/followees.json", \
                                                      f"{folder_assets}/locations.json", \
                                                      f"{folder_assets}/user_locations.json"
file_cosine_similarities, file_sccs = f"{folder_assets}/cosine_similarities.csv", \
                                      f"{folder_assets}/sccs.csv"
storage = StorageProvider(main_folder=folder_assets)

followees, locations, user_locations = storage.read_or_create_file(filepath=file_followees), \
                                       storage.read_or_create_file(filepath=file_locations), \
                                       storage.read_or_create_file(filepath=file_user_locations)

print(f"There are {len(locations.keys())} unique locations and {len(followees.keys())} unique users, "
      f"of which {'%0.1f' % ((len(user_locations.keys()) / len(followees.keys())) * 100)}% of them has logged into a location")

users_graph = UsersGraph(followees=followees, locations=locations, user_locations=user_locations)

""" cosine similarities """
# similarities = users_graph.get_cosine_similarities(filepath=file_cosine_similarities, logs=logs)

""" strongly connected components """
sccs = users_graph.get_most_dense_connected_components(filepath=file_sccs, top_size=top_scc_size, logs=logs)
