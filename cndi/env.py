from yaml import load, SafeLoader
import os

RCN_ENVS_CONFIG = 'RCN_ENVS_CONFIG'

def addToOsEnviron(key: str, value):
    if not key.startswith("."):
        key = '.' + key
    os.environ[(RCN_ENVS_CONFIG+key).upper()] = str(value)
    print(os.environ[RCN_ENVS_CONFIG+key])

def walkDictKey(parent, parent_label=''):
    responseList = list()
    for key, value in parent.items():
        if isinstance(value, dict):
            responseList.extend(walkDictKey(value, parent_label + '.' + key))
        else:
            parent_label += '.'+ key
            responseList.append([parent_label, value])

    return responseList

def loadEnvFromFile(property_file):
    if(not os.path.exists(property_file)):
        raise FileNotFoundError(f"Environment file does not exists at {property_file}")

    with open(property_file, "r") as stream:
        data = load(stream, SafeLoader)
        envData = walkDictKey(data)
        for key, value in envData:
            addToOsEnviron(key, value)

def getContextEnviroments():
    return dict(
        map(
            lambda items: [items[0][RCN_ENVS_CONFIG.__len__()+1:].lower(), items[1]],
            filter(lambda items: items[0].startswith(RCN_ENVS_CONFIG), os.environ.items())
        )
    )

def getContextEnvironment(key: str):
    envDict = getContextEnviroments()
    key = key.lower()
    if key in envDict:
        return envDict[key]
    return None