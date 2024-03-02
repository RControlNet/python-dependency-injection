import os
from pathlib import Path
import yaml
from yaml import SafeLoader

class BaseConfigGenerator:
    def __init__(self, sourceDir, destinationFile):
        self.sourceDir = sourceDir
        self.destinationFile = destinationFile
    def readDocs(self, exts=['.yaml', '.yml']):
        files = filter(lambda x: os.path.isfile(x) and os.path.splitext(x)[1] in exts,
                       map(
                           lambda x: os.path.join(self.sourceDir, x), os.listdir(self.sourceDir)
                           )
                       )

        docs = []
        for file in files:
            with open(file, 'r') as stream:
                docs.append(yaml.load(stream, Loader=SafeLoader))

        return docs

class NLUConfigGenerator(BaseConfigGenerator):
    def __init__(self, sourceDir: str, destinationFile: str, version='3.1'):
        BaseConfigGenerator.__init__(self, sourceDir, destinationFile)
        self.version = version

    def transform(self):
        docs = self.readDocs()
        outputData = {}
        for doc in docs:
            intent = doc['intent']
            examples = list(doc['examples'].split("\n")) if isinstance(doc['examples'], str) else doc['examples']
            if intent in outputData:
                outputData[intent].extend(examples)
            else:
                outputData[intent] = examples
        return outputData

    def writeToFile(self, outputData={}):
        nlu = []
        for intent, examples in outputData.items():
            example = str.join("", map(lambda x: f"- {x} \n", examples))
            nlu.append({
                "intent": intent,
                "examples": example
            })

        nluData = {
            "version": self.version,
            "nlu": nlu
        }

        with open(self.destinationFile, "w") as  stream:
            yaml.dump(nluData, stream)

        return Path(self.destinationFile)


if __name__ == '__main__':
    nlu = NLUConfigGenerator("./", "output.yml")
    output = nlu.transform()
    print(nlu.writeToFile(output))


