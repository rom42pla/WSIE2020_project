class Location:

    def __init__(self, city: str = None, country: str = None):
        self.city = city
        self.country = country

    def __str__(self):
        location_as_string = f""
        if self.city:
            location_as_string += f"{self.city}, {self.country}"
        else:
            location_as_string += f"-, {self.country}"
        return location_as_string.strip()