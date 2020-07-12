import time

import numpy as np
import numba
from numba import jit
import torch
from pprint import pprint

from .User import User
from .Location import Location


class UsersGraph:

    def __init__(self, followees: dict = None, locations: dict = None, user_locations: dict = None):
        self.graph = {}
        self.users_ids_to_ints, self.locations_ids_to_ints = {}, {}
        if followees and locations and user_locations:
            for user_id in followees.keys():
                # eventually creates the new user as a node
                if not self.get_user(user_id):
                    user = User(id=user_id)
                    # retrieves locations logged by the user
                    if user_id in user_locations:
                        for location_raw in user_locations[user_id]:
                            location = Location(city=location_raw["city"], country=location_raw["country"])
                            user.add_location(location)
                    self.add_user(user)
                # retrieves followees
                for followee_id in followees[user_id]:
                    # eventually creates the new followee as a node
                    if not self.get_user(followee_id):
                        followee = User(id=followee_id)
                        # retrieves locations logged by the user
                        if followee_id in user_locations:
                            for location_raw in user_locations[followee_id]:
                                location = Location(city=location_raw["city"], country=location_raw["country"])
                                followee.add_location(location)
                        self.add_user(followee)

                    self.add_edge(user_id_from=user_id, user_id_to=followee_id)

    def add_user(self, user: User):
        self.graph[user.id] = {"infos": user, "followees": set()}
        self.users_ids_to_ints[user.id] = len(self.users_ids_to_ints.keys())
        for location in user.get_locations():
            if str(location) not in self.locations_ids_to_ints:
                self.locations_ids_to_ints[str(location)] = len(self.locations_ids_to_ints.keys())

    def get_users(self):
        return self.graph

    def get_user(self, user_id: str):
        if user_id in self.graph.keys():
            return self.graph[user_id]
        else:
            return None

    def get_followees(self, user_id: str):
        if user_id in self.graph.keys():
            return self.graph[user_id]["followees"]
        else:
            return set()

    def add_edge(self, user_id_from: str, user_id_to: str):
        if self.get_user(user_id_from) and self.get_user(user_id_to):
            self.graph[user_id_from]["followees"].add(user_id_to)

    def remove_edge(self, user_id_from: str, user_id_to: str):
        if self.get_user(user_id_from) and self.get_user(user_id_to) and user_id_to in self.get_followees(user_id_from):
            self.graph[user_id_from]["followees"].remove(user_id_to)

    def get_vector_representations(self):
        """
        Returns a matrix representation of users.
        :return: a matrix representation of users, where each user symbolize the places the user has visited,
        and each column stands for a place. Each cell equals the number of times the user x took a picture of place y
        """
        # initializes the matrix
        representations = np.zeros(shape=(len(self.users_ids_to_ints), len(self.locations_ids_to_ints)),
                                   dtype=np.long)
        # fills the matrix
        for user_id, row_index in self.users_ids_to_ints.items():
            for location in self.get_user(user_id=user_id)["infos"].get_locations():
                representations[row_index][self.locations_ids_to_ints[str(location)]] += 1

        return representations

    def get_cosine_similarities(self, filepath: str, logs: bool = True):
        """
        Computes the cosine similarity between each couple of users and saves them to a file
        :param filepath: where to write down the results
        :param: logs: whether or not to print logs to the console
        """

        # hyper fast GPU cosine similarity formula evaluation
        @jit(nopython=True)
        def cosine_similarity(user_1, user_2, user_1_norm, user_2_norm):
            user_1, user_2 = user_1.astype(np.float64), \
                             user_2.astype(np.float64)
            similarity = np.dot(user_1, user_2) / \
                         (user_1_norm * user_2_norm)
            return similarity

        # empties the file
        with open(filepath, mode="w", encoding="utf-8") as fp:
            fp.write(f"")

        ints_to_users_ids = {v: k for k, v in self.users_ids_to_ints.items()}
        representations = self.get_vector_representations()

        # saving norms for efficiency purposes
        norms = {}
        for user_index in range(0, representations.shape[0]):
            user = representations[user_index]
            norms[user_index] = np.linalg.norm(user)

        # calculating cosine similarity
        execution_time = time.time()
        for user_1_index in range(0, representations.shape[0] - 1):
            similarities = []
            if logs:
                if user_1_index > 0:
                    print(f"\r", end="")
                print(f"Calculating cosine similarity\t"
                      f"{'%0.2f' % ((user_1_index / representations.shape[0]) * 100)}%\t"
                      f"last iteration took {time.time() - execution_time}s",
                      end="")
            execution_time = time.time()
            for user_2_index in range(user_1_index + 1, representations.shape[0]):
                similarity = np.nan
                if norms[user_1_index] != 0 and norms[user_2_index] != 0:
                    similarity = cosine_similarity(user_1=representations[user_1_index],
                                                   user_2=representations[user_2_index],
                                                   user_1_norm=norms[user_1_index],
                                                   user_2_norm=norms[user_2_index])
                similarities += [{"users": (ints_to_users_ids[user_1_index], ints_to_users_ids[user_2_index]),
                                  "value": similarity}]

            # write to file
            similarities_to_write = f""
            for similarity in similarities:
                user_1, user_2 = similarity["users"]
                similarity_value = similarity["value"]
                similarities_to_write += f"{str(user_1).strip()}," \
                                         f"{str(user_2).strip()}," \
                                         f"{str(round(similarity_value, 4)).strip()}\n"
            with open(filepath, mode="a", encoding="utf-8") as fp:
                fp.write(similarities_to_write.strip())
        if logs:
            print()

    def get_connected_components(self):
        """
        Computes all the Strongly Connected Components of this graph using Tarjan's algorithm
        :return: a list of lists, where each one is a scc
        """
        # creates a dummy graph starting from the data
        graph = {user_id: list(self.get_user(user_id)["followees"]) for user_id in self.get_users().keys()}
        # Tarjan's algorithm implementation
        stack, call_stack, lowlinks = [], [], {}
        sccs = []
        for user_id in graph.keys():
            call_stack.append((user_id, 0, len(lowlinks)))
            while call_stack:
                user_id, pi, num = call_stack.pop()
                if pi == 0:
                    if user_id in lowlinks.keys():
                        continue
                    lowlinks[user_id] = num
                    stack.append(user_id)
                if pi > 0:
                    lowlinks[user_id] = min(lowlinks[user_id], lowlinks[graph[user_id][pi - 1]])
                if pi < len(graph[user_id]):
                    call_stack.append((user_id, pi + 1, num))
                    call_stack.append((graph[user_id][pi], 0, len(lowlinks)))
                    continue
                # a new scc is found
                if num == lowlinks[user_id]:
                    scc = []
                    while True:
                        scc.append(stack.pop())
                        lowlinks[scc[-1]] = len(graph)
                        if scc[-1] == user_id: break
                    sccs.append(scc)

        # sorts the result
        sccs = [(len(scc), scc) for scc in sccs]
        sccs.sort(reverse=True)
        # returns the strongly connected components ordered by size of the subgraph
        return [scc for scc_len, scc in sccs]

    def get_most_dense_connected_components(self, filepath: str, top_size: int = 10, logs: bool = True):
        """
        Returns the top k densely connected components of the graph
        :param filepath: where to write out the results
        :param top_size: our k number
        :param logs: whether to print or not logs on the console
        :return: the top k densely connected components of the graph
        """
        sccs = self.get_connected_components()
        sccs = {id: {"users": set(users),
                     "density": None} for id, users in enumerate(sccs)}
        # things to write to the file
        sccs_couples = []
        for scc_id in sccs.keys():
            # samples the subgraph out of that scc
            V, E = [], []
            subgraph = {user_id: [] for user_id in sccs[scc_id]["users"]}
            for user_id in subgraph:
                V += [user_id]
                subgraph[user_id] = [followee_user_id for followee_user_id in self.get_followees(user_id)
                                     if followee_user_id in sccs[scc_id]["users"]]
                E += ([(user_id, followee_user_id) for followee_user_id in subgraph[user_id]])
            # computes the formula
            # for directed simple graphs, the maximum possible edges is twice that of undirected graphs
            # to account for the directedness, so we can discard the 2 at the nominator
            sccs[scc_id]["density"] = np.nan if len(V) <= 1 else (len(E)) / \
                                                                 (len(V) * (len(V) - 1))
            # used later to write to a file
            sccs_couples += [(sccs[scc_id]["density"], sccs[scc_id]["users"])]

        # write to file
        sccs_couples.sort(reverse=True)
        sccs_to_write = f""
        for i, scc_couple in enumerate(sccs_couples):
            if i >= top_size:
                break
            density, users = scc_couple[0], scc_couple[1]
            # adds the density
            sccs_to_write += f"{str(density).strip()},"
            # adds all the users
            for user in users:
                sccs_to_write += f"{str(user).strip()},"
            # removes the last comma
            sccs_to_write = sccs_to_write[:-1]
            sccs_to_write += "\n"
        with open(filepath, mode="w", encoding="utf-8") as fp:
            fp.write(sccs_to_write.strip())

        # eventually prints the results to the console
        if logs:
            print(f"Top {top_size} densely connected components:")
            for scc in sccs_couples[:top_size]:
                print(f"\tDensity: {round(scc[0], 4)}\t\tUsers: {scc[1]}")
        return sccs_couples[:top_size]
