from .Location import Location

class User:

    def __init__(self, id: str, locations_logs: list = None):
        self.id = id
        self.locations_logs = []
        if locations_logs:
            self.locations_logs = locations_logs

    def __str__(self):
        user_as_string = f"User\n\t{self.id}\n"
        user_as_string += f"Locations\n"
        for location in self.locations_logs:
            user_as_string += f"\t{location}\n"
        return user_as_string.strip()

    def add_location(self, location: Location):
        self.locations_logs += [location]

    def get_locations(self):
        return self.locations_logs