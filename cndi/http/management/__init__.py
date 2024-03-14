import threading


from cndi.annotations import beans, Component, getBeanObject, ConditionalRendering
from cndi.annotations.threads import ContextThreads
from cndi.env import getContextEnvironment
from cndi.utils import logger

def managementServerSupported(x):
    try:
        from flask import Flask
        from werkzeug.serving import run_simple
        return getContextEnvironment("rcn.management.server.enabled", defaultValue=False, castFunc=bool)
    except ImportError:
        return False

@Component
@ConditionalRendering(callback=managementServerSupported)
class ManagementServer:
    def registerEndpoints(self, flaskApp):
        from flask import jsonify

        @flaskApp.route("/health")
        def health():
            return jsonify(status="OK")

        @flaskApp.route("/management/beans")
        def managementBeans():
            targetResponse = list()
            for bean in beans:
                targetResponse.append({
                    "name": bean['name'],
                    'newInstance': bean['newInstance'],
                    'fullname': bean['fullname'],
                    'index': bean['index']
                })
            return jsonify(beans=targetResponse)

    def run(self):
        from flask import Flask
        from werkzeug.serving import run_simple

        host = getContextEnvironment("rcn.management.server.host", defaultValue="0.0.0.0")
        port = getContextEnvironment("rcn.management.server.port", defaultValue=9000, castFunc=int)

        logger.info(f"Initializing Management Server at {host}:{port}")

        flaskApp = Flask(__name__)
        self.registerEndpoints(flaskApp)
        serverThread = threading.Thread(target=run_simple, kwargs={
            "hostname": host,
            "port": port,
            "application": flaskApp,
            "threaded": False
        })

        contextThread: ContextThreads = getBeanObject('.'.join([ContextThreads.__module__ , ContextThreads.__name__]))
        contextThread.add_thread(serverThread)

        serverThread.start()
