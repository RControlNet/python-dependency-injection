from flask import jsonify, request

from cndi.annotations import Autowired
from cndi.env import addToOsEnviron
from cndi.flask.flask_app import FlaskApplication
from cndi.initializers import AppInitializer

@Autowired()
def addEndpoints(flaskApp: FlaskApplication):
    @flaskApp.app.route("/", methods=["POST"])
    def serve():
        return jsonify(request.json)

if __name__ == '__main__':
    addToOsEnviron("app.flask.enabled", "true")                     # Enable Flask App
    addToOsEnviron("rcn.management.server.enabled", "true")         # Enable Management and Health Endpoint
    addToOsEnviron("management.context.thread.enable", "true")      # Enable Context Thread


    app = AppInitializer()
    app.componentScan("cndi.flask")
    app.run()