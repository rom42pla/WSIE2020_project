from unidecode import unidecode
import re
import geocoder
from pprint import pprint

class MapsProvider():
    def parse_location(self, location: str):
        location_parsed = {}
        location_description = geocoder.osm(location).json
        if not location_description:
            return None
        location_parsed["city"] = unidecode(
            location_description["city"]) if "city" in location_description.keys() else None
        location_parsed["country"] = unidecode(
            location_description["country"]) if "country" in location_description.keys() else None
        return location_parsed

    def clean_location_string(self, location: str):
        location = unidecode(location.strip().lower())
        location = re.sub('[\W]+', " ", location).split()
        location = " ".join(location)
        return location
