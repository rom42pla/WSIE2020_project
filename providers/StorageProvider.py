import json
import os
from pprint import pprint


class StorageProvider:

    def __init__(self, main_folder="./assets"):
        self.main_folder = main_folder

    def read_or_create_file(self, filepath: str):
        content = {}
        extension = os.path.splitext(filepath)[1]
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as fp:
                if extension == ".json":
                    json.dump(content, fp)
                else:
                    fp.write("[]")
        else:
            with open(filepath, 'r') as fp:
                if extension == ".json":
                    content = json.load(fp)
                else:
                    content = eval(fp.read())
        return content

    def save_to_file(self, filepath: str, data):
        with open(filepath, 'w') as fp:
            if isinstance(data, dict):
                json.dump(data, fp, indent=4)
            else:
                pprint(data, fp)
