import os
from pathlib import Path


class ResourceFinder:
    def __init__(self):
        if "RCN_HOME" in os.environ:
            self.rcnHome = os.environ['RCN_HOME']
        else:
            self.rcnHome = os.path.join(Path.home().absolute().__str__(), ".rcn")

    def findResource(self, resourcePath):
        currentPath = Path(os.path.abspath(os.path.curdir))
        resourceDirPath = os.path.join(currentPath, "resources")
        resourceExist = os.path.exists(resourceDirPath)

        while not resourceExist  \
                and len(resourceDirPath) >= len(self.rcnHome):
            currentPath = currentPath.parent
            resourceDirPath = os.path.join(currentPath.absolute(), "resources")
            resourceExist = os.path.exists(resourceDirPath) and os.path.isdir(resourceDirPath)

        if resourceExist:
            resourcePath = os.path.join(resourceDirPath, resourcePath)
            if os.path.exists(resourcePath):
                return resourcePath
            raise FileNotFoundError(f"Resource not found at resources/{resourcePath}")
        else:
            raise FileNotFoundError(f"Resource Path not found resources/{resourcePath}")

if __name__ == '__main__':
    resourceFinder = ResourceFinder()
    print(resourceFinder.rcnHome)
    print(resourceFinder.findResource(""))