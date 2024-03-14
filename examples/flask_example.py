from cndi.env import addToOsEnviron
from cndi.initializers import AppInitializer

if __name__ == '__main__':
    addToOsEnviron("app.flask.enabled", "true")                     # Enable Flask App
    addToOsEnviron("rcn.management.server.enabled", "true")         # Enable Management and Health Endpoint
    addToOsEnviron("management.context.thread.enable", "true")      # Enable Context Thread


    app = AppInitializer()
    app.componentScan("cndi.flask")
    app.run()