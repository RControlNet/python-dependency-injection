from pathlib import Path

from yaml import SafeLoader, load_all
import os, re
import logging

from cndi import BASE_NAME

logger = logging.getLogger(__name__)


RCN_ENVS_CONFIG = f'{BASE_NAME}_ENVS_CONFIG'
RCN_ACTIVE_PROFILE = f"{RCN_ENVS_CONFIG}.active.profile" # RCN_ENVS_CONFIG.active.profile


if f"{BASE_NAME}_HOME" not in os.environ:
    os.environ[f"{BASE_NAME}_HOME"] = f"{Path.home()}/.rcn/"

configDir = os.environ[f"{BASE_NAME}_HOME"]

if RCN_ACTIVE_PROFILE not in os.environ:
    os.environ[RCN_ACTIVE_PROFILE] = "default"

VARS = dict(map(lambda key: (key,os.environ[key]), filter(lambda key: key.startswith(RCN_ENVS_CONFIG), os.environ)))

def loadEnvsFromRcnHome():
    profile = getConfiguredProfile()
    profileHome = os.path.join(configDir, profile)
    profileEnvFile = os.path.join(profileHome, "env.yml")

    if os.path.exists(profileEnvFile):
        logger.info(f"Profile Environment file found for profile f{profile}")
        loadEnvFromFile(profileEnvFile)

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

def getConfiguredProfile():
    if f"{RCN_ENVS_CONFIG}.active.profile".lower() in VARS:
        return VARS[f"{RCN_ENVS_CONFIG}.active.profile".lower()]
    elif "rcn.active.profile" in os.environ:
        return os.environ["rcn.active.profile"]
    else:
        return "default"

def loadEnvFromFile(property_file):
    if(not os.path.exists(property_file)):
        raise FileNotFoundError(f"Environment file does not exists at {property_file}")

    with open(property_file, "r") as stream:
        data = list(load_all(stream, SafeLoader))
        if len(data) == 1:
            data = data[0]
        else:
            dataDict = dict(map(lambda x: (x['rcn']['profile'], x), data))
            profile = getConfiguredProfile()
            data = dataDict[profile]
            data = normalize(data)
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

def constructDictWithValues(value, keys=[]):
    if len(keys) == 1:
        return {
            keys[0]: value
        }
    else:
        return {
            keys[0]: constructDictWithValues(value, keys[1:])
        }

def constructDict(value, generatedObject, key=''):
    tempDict = generatedObject
    keys = key.split('.')
    for i, key in enumerate(keys):
        if key == "":
            continue

        if key in tempDict:
            tempDict = tempDict[key]
        else:
            tempDict.update(constructDictWithValues(value, keys[i:]))
            break

def normalize(dictObject: dict, key = ''):
    envData = walkDictKey(dictObject)
    envData = sorted(envData, key = lambda data: data[0])

    generatedDict = dict()
    for key, value in envData:
        searchResult = re.findall("\${[a-z0-9A-Z\\_]+}", str(value))
        for result in searchResult:
            groupValue = re.match("\${(?P<envName>[a-z0-9A-Z\\_]+)}", result).group('envName')
            if groupValue.startswith(RCN_ENVS_CONFIG) and groupValue in VARS:
                envValue = VARS[groupValue]
            elif groupValue in os.environ:
                envValue = os.environ[groupValue]
            else:
                raise ValueError(f"Environment Variable not found {groupValue}")
            value = value.replace(result, envValue)

        constructDict(value, generatedDict, key)

    return generatedDict
