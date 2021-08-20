from yaml import load, Loader
import os

DEFAULT_PROPERTIES_PATH = "./resources/application.yml"

class Properties:
    def __init__(self, property_file):
        if(not os.path.exists(property_file)):
            raise FileNotFoundError(f"Environment file does not exists at {property_file}")

        with open(property_file, "r") as stream:
            self.data = load(stream, Loader)

    def getProperty(self, key):
        return self.data[key]

    @staticmethod
    def getResourceProperties():
        if not os.path.exists(DEFAULT_PROPERTIES_PATH):
            return None

        return Properties(DEFAULT_PROPERTIES_PATH)