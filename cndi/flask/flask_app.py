import logging
import threading


from cndi.annotations import Component, ConditionalRendering, getBeanObject
from cndi.annotations.threads import ContextThreads, isContextThreadEnable
from cndi.consts import RCN_FLASK_APP_ENABLED, RCN_FLASK_APP_NAME, RCN_FLASK_APP_PORT, RCN_FLASK_APP_LISTEN, \
    RCN_FLASK_APP_CONTEXT_URL, RCN_FLASK_APP_CONFIGS_LIST, RCN_FLASK_APP_BACKEND_SERVER
from cndi.env import getContextEnvironment, getContextEnvironments

logger = logging.getLogger(__name__)

def __check_flask_enabled__(x):
    """
    Checks whether Flask is enabled.

    This function checks the environment for a variable named 'app.flask.enabled'. If the variable is set to 'True', the function returns True. If the variable is not set or is set to any other value, the function returns False.

    Returns:
        True if Flask is enabled, False otherwise.
    """
    try:
        from flask import Flask
        return getContextEnvironment(RCN_FLASK_APP_ENABLED, castFunc=bool, defaultValue=False) \
            and isContextThreadEnable(f"{FlaskApplication.__module__}.{FlaskApplication.__qualname__}")
    except ImportError:
        return False

@Component
@ConditionalRendering(callback=__check_flask_enabled__)
class FlaskApplication:
    """
    This class represents a Flask application.

    It is marked as a component and is conditionally rendered based on whether Flask is enabled.

    Attributes:
        appName: The name of the Flask application.
        port: The port on which the Flask application runs.
        host: The host on which the Flask application runs.
        configs: A dictionary of configuration settings for the Flask application.
        app: The Flask application instance.

    Methods:
        postConstruct: A method that is called after the Flask application is constructed.
        run: Starts the Flask application.
    """
    def __init__(self):
        """
        Initializes a new instance of the Flask application.

        The application's name, port, host, debug mode, and configuration settings are retrieved from the environment.
        """
        from flask import Flask, Blueprint
        self.appName = getContextEnvironment(RCN_FLASK_APP_NAME, defaultValue="app")
        self.port = getContextEnvironment(RCN_FLASK_APP_PORT, defaultValue=8080, castFunc=int)
        self.host = getContextEnvironment(RCN_FLASK_APP_LISTEN, defaultValue="0.0.0.0")
        self.contextUrl = getContextEnvironment(RCN_FLASK_APP_CONTEXT_URL, defaultValue="/")
        contextEnvs = getContextEnvironments()
        self.configs = dict(map(lambda items: (items[0][f'{RCN_FLASK_APP_CONFIGS_LIST}.'.__len__():], items[1]),
                                filter(lambda items: items[0].startswith(RCN_FLASK_APP_CONFIGS_LIST), contextEnvs.items())))

        self.__app = Flask(self.appName)
        self.app = Blueprint(self.appName, __name__)
        

    def postConstruct(self):
        """
        A method that is called after the Flask application is constructed.

        This method currently does nothing, but can be overridden in subclasses to perform setup tasks.
        """
        pass

    def run(self):
        """
        Starts the Flask application.

        This method starts the Flask application on the specified host and port.
        """

        self.__app.register_blueprint(self.app, url_prefix=self.contextUrl)

        backend = getContextEnvironment(RCN_FLASK_APP_BACKEND_SERVER, defaultValue="werkzeug")
        logger.info(f"Starting Flask Server at {self.host}:{self.port} at Context URL: {self.contextUrl} on Backend {backend}")

        if backend == "werkzeug":
            from werkzeug import run_simple
            serverThread = threading.Thread(name=f"thread-{self.appName}", target=run_simple, kwargs={
                "hostname": self.host,
                "port": self.port,
                "application": self.__app,
                **self.configs
            })
        elif backend == "waitress":
            from waitress import serve
            serverThread = threading.Thread(name=f"thread-{self.appName}", target=serve, kwargs={
                "host": self.host,
                "port": self.port,
                "app": self.__app,
                **self.configs
            })

        contextThread: ContextThreads = getBeanObject('.'.join([ContextThreads.__module__ , ContextThreads.__name__]))
        contextThread.add_thread(serverThread)

        serverThread.start()