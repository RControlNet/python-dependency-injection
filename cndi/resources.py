import os
from pathlib import Path

from cndi import BASE_NAME
from cndi.annotations import Component


@Component
class ResourceFinder:
    def __init__(self):
        if f"{BASE_NAME}_HOME" in os.environ:
            self.rcnHome = os.environ[f'{BASE_NAME}_HOME']
        else:
            self.rcnHome = os.path.join(Path.home().absolute().__str__(), ".rcn")

    def computeResourcePath(self):
        currentPath = Path(os.path.abspath(os.path.curdir))
        return os.path.join(currentPath, "resources")
    def findResource(self, resourcePath):
        currentPath = Path(os.path.abspath(os.path.curdir))
        resourceDirPath = os.path.join(currentPath, "resources")
        resourceExist = os.path.exists(resourceDirPath)

        if f'{BASE_NAME}_RESOURCES_DIR' in os.environ and resourceExist == False:
            resourceDirPath = os.environ[f'{BASE_NAME}_RESOURCES_DIR']
            resourceExist = os.path.exists(os.path.join(resourceDirPath,
                                                        resourcePath))

        if resourceExist:
            resourcePath = os.path.join(resourceDirPath, resourcePath)
            if os.path.exists(resourcePath):
                return Path(resourcePath)
            else:
                raise FileNotFoundError(f"Resource not found at resources/{resourcePath}")
        else:
            raise FileNotFoundError(f"Resource Path not found resources/{resourcePath}")