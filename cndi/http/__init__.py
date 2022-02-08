import os
from pathlib import Path

import requests

if "ELFIE_DOWNLOAD_PATH" not in os.environ:
    path = os.path.join(Path.home(), ".elfie/")
    os.environ["ELFIE_DOWNLOAD_PATH"] = path
    if not os.path.exists(path):
        os.makedirs(path)

def getElfieDownloadPath():
    return os.environ["ELFIE_DOWNLOAD_PATH"]

class CDNFileDownloader(object):
    def __init__(self):
        self.url = "https://github.com/mayank31313/open_cdn/raw/main"
        self.downloadPath = getElfieDownloadPath()

    def downloadFile(self, childPath):
        with requests.get(f"{self.url}/{childPath}", stream=True) as r:
            r.raise_for_status()
            fullPath = os.path.join(self.downloadPath, childPath)
            if not os.path.exists(os.path.dirname(fullPath)):
                os.makedirs(os.path.dirname(fullPath))

            with open(fullPath, "wb") as file:
                for chunk in r.iter_content(chunk_size=8192):
                    file.write(chunk)

            return fullPath