from yaml import SafeLoader, load_all
import os
import logging

logger = logging.getLogger(__name__)


RCN_ENVS_CONFIG = 'RCN_ENVS_CONFIG'
if f"{RCN_ENVS_CONFIG}.active.profile" not in os.environ:
    os.environ[f"{RCN_ENVS_CONFIG}.active.profile"] = "default"

VARS = dict(map(lambda key: (key,os.environ[key]), filter(lambda key: key.startswith(RCN_ENVS_CONFIG), os.environ)))


def addToOsEnviron(key: str, value):
    if not key.startswith("."):
        key = '.' + key
    if (RCN_ENVS_CONFIG+key) not in VARS:
        VARS[(RCN_ENVS_CONFIG+key)] = str(value)
    else:
        logger.warning(f"An env variable already exists with key={(RCN_ENVS_CONFIG+key)}")

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

def loadEnvFromFiles(*files):
    for file in files:
        if not os.path.exists(file):
            logger.info(f"Env file does not exist: {file}")
            continue

        loadEnvFromFile(file)
def loadEnvFromFile(property_file):
    if(not os.path.exists(property_file)):
        raise FileNotFoundError(f"Environment file does not exists at {property_file}")

    with open(property_file, "r") as stream:
        data = list(load_all(stream, SafeLoader))
        if len(data) == 1:
            data = data[0]
        else:
            dataDict = dict(map(lambda x: (x['rcn.profile'], x), data))
            data = dataDict[VARS[f"{RCN_ENVS_CONFIG}.active.profile"]]
        envData = walkDictKey(data)
        for key, value in envData:
            addToOsEnviron(key, value)

def getContextEnvironments():
    return dict(
        map(
            lambda items: [items[0][RCN_ENVS_CONFIG.__len__()+1:].lower(), items[1]],
            filter(lambda items: items[0].startswith(RCN_ENVS_CONFIG), VARS.items())
        )
    )

def getListTypeContextEnvironments():
    rcn_envs = getContextEnvironments()
    dataDict = dict(filter(lambda key: key[0].__contains__(".#"), rcn_envs.items()))
    return dataDict

def getContextEnvironment(key: str, defaultValue = None, castFunc = None, required=False):
    envDict = getContextEnvironments()
    key = key.lower()
    if key in envDict:
        if castFunc is not None:
            return castFunc(envDict[key])
        return envDict[key]
    if required:
        raise KeyError(f"Environment Variable with Key: {key} not found")
    return defaultValue