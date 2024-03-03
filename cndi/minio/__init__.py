from cndi.annotations import Bean, ConditionalRendering
from cndi.env import getContextEnvironment

try:

    from minio import Minio

    @Bean()
    @ConditionalRendering(callback=lambda x: getContextEnvironment('rcn.minio.enabled', defaultValue=False, castFunc=bool))
    def getMinio() -> Minio:
        clientId = getContextEnvironment("rcn.minio.clientId")
        clientSecret = getContextEnvironment("rcn.minio.clientSecret")
        endpoint = getContextEnvironment("rcn.minio.endpoint")

        return Minio(endpoint,
                     access_key=clientId, secret_key=clientSecret)

except ImportError:
    pass