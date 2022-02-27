from yaml import SafeLoader, load_all
import os

RCN_ENVS_CONFIG = 'RCN_ENVS_CONFIG'
if f"{RCN_ENVS_CONFIG}.active.profile" not in os.environ:
    os.environ[f"{RCN_ENVS_CONFIG}.active.profile"] = "default"


def addToOsEnviron(key: str, value):
    if not key.startswith("."):
        key = '.' + key
    os.environ[(RCN_ENVS_CONFIG+key).upper()] = str(value)

def walkListKey(parent, parent_label=''):
    responseList = list()
    for i,value in enumerate(parent):
        if isinstance(value, dict):
            responseList.extend(walkDictKey(value, parent_label + '.#' + str(i)))
        elif isinstance(value, list):
            responseList.extend(walkListKey(value, parent_label + '.#' + str(i)))
        else:
            responseList.append([parent_label + '.#'+ str(i), value])

    return responseList

def walkDictKey(parent, parent_label=''):
    responseList = list()
    for key, value in parent.items():
        if isinstance(value, dict):
            responseList.extend(walkDictKey(value, parent_label + '.' + key))
        elif isinstance(value, list):
            responseList.extend(walkListKey(value, parent_label + '.' + key))
        else:
            responseList.append([parent_label + '.'+ key, value])

    return responseList

def loadEnvFromFile(property_file):
    if(not os.path.exists(property_file)):
        raise FileNotFoundError(f"Environment file does not exists at {property_file}")

    with open(property_file, "r") as stream:
        data = list(load_all(stream, SafeLoader))
        if len(data) == 1:
            data = data[0]
        else:
            dataDict = dict(map(lambda x: (x['rcn.profile'], x), data))
            data = dataDict[os.environ[f"{RCN_ENVS_CONFIG}.active.profile"]]
        envData = walkDictKey(data)
        for key, value in envData:
            addToOsEnviron(key, value)

def getContextEnvironments():
    return dict(
        map(
            lambda items: [items[0][RCN_ENVS_CONFIG.__len__()+1:].lower(), items[1]],
            filter(lambda items: items[0].startswith(RCN_ENVS_CONFIG), os.environ.items())
        )
    )

def getListTypeContextEnvironments():
    rcn_envs = getContextEnvironments()
    dataDict = dict(filter(lambda key: key[0].__contains__(".#"), rcn_envs.items()))
    return dataDict

def getContextEnvironment(key: str):
    envDict = getContextEnvironments()
    key = key.lower()
    if key in envDict:
        return envDict[key]
    return None