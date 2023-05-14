import os
from pathlib import Path
from cndi import BASE_NAME


class ResourceFinder:
    def __init__(self):
        if f"{BASE_NAME}_HOME" in os.environ:
            self.rcnHome = os.environ[f'{BASE_NAME}_HOME']
        else:
            self.rcnHome = os.path.join(Path.home().absolute().__str__(), ".rcn")

    def findResource(self, resourcePath):
        currentPath = Path(os.path.abspath(os.path.curdir))
        resourceDirPath = os.path.join(currentPath, "resources")
        resourceExist = os.path.exists(resourceDirPath)

        while not resourceExist \
                and len(resourceDirPath) >= len(self.rcnHome):
            currentPath = currentPath.parent
            resourceDirPath = os.path.join(currentPath.absolute(), "resources")
            resourceExist = os.path.exists(resourceDirPath) and os.path.isdir(resourceDirPath)

        if f'{BASE_NAME}_RESOURCES_DIR' in os.environ and resourceExist == False:
            resourceDirPath = os.environ[f'{BASE_NAME}_RESOURCES_DIR']
            resourceExist = os.path.exists(os.path.join(resourceDirPath,
                                                        resourcePath))

        if resourceExist:
            resourcePath = os.path.join(resourceDirPath, resourcePath)
            if os.path.exists(resourcePath):
                return resourcePath
            raise FileNotFoundError(f"Resource not found at resources/{resourcePath}")
        else:
            raise FileNotFoundError(f"Resource Path not found resources/{resourcePath}")