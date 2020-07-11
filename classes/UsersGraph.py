import time

import numpy as np
import numba
from numba import jit
import torch

from .User import User


class UsersGraph:

    def __init__(self, ):
        self.graph = {}
        self.users_ids_to_ints, self.locations_ids_to_ints = {}, {}

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
        representations = np.zeros(shape=(len(self.users_ids_to_ints), len(self.locations_ids_to_ints)),
                                   dtype=np.long)
        for user_id, row_index in self.users_ids_to_ints.items():
            for location in self.get_user(user_id=user_id)["infos"].get_locations():
                representations[row_index][self.locations_ids_to_ints[str(location)]] += 1

        return representations

    def get_cosine_similarities(self, filepath: str):
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
        print()
