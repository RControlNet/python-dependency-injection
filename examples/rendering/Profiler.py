import os

from cndi.annotations import Component, Profile
from cndi.env import RCN_ACTIVE_PROFILE
from cndi.initializers import AppInitializer

os.environ[RCN_ACTIVE_PROFILE] = "local"

@Component
@Profile()
class LoadDefaultProfile:
    def __init__(self):
        print("Default Profile Component Loaded")

@Component
@Profile(profiles=['dev'])
class LoadDevProfile:
    def __init__(self):
        print("Dev Profile Component Loaded")

if __name__ == '__main__':
    app = AppInitializer()
    app.run()