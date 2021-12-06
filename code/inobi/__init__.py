
import builtins, pdb
builtins._breakpoint = pdb.set_trace

import eventlet
eventlet.monkey_patch()

import os

import typing as T

from flask import Flask
from flask_socketio import SocketIO
from . import config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.contrib.fixers import ProxyFix


def make_app():
    app = Flask(config.APP_NAME, static_folder=config.STATIC_DIRECTORY, template_folder=config.TEMPLATES_DIRECTORY)
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSON_AS_ASCII'] = False
    app.config['SECRET_KEY'] = config.FLASK_SECRET

    ###################
    ### Auth MODULE ###
    ###################

    # from inobi.auth import Auth, config as auth_config, bp as auth_bp
    # app.app_auth = Auth(api_key=auth_config.API_KEY, redis_url=config.REDIS_URL)
    # app.register_blueprint(auth_bp, url_prefix=auth_config.PREFIX)


    #######
    # SENTRY
    if config.SENTRY_DSN:

        import raven
        from raven.contrib.flask import Sentry
        from raven.exceptions import InvalidGitRepository

        try:
            app.config['SENTRY_RELEASE'] = raven.fetch_git_sha(config.BASE_DIR)
        except InvalidGitRepository as e:
            import warnings
            warnings.warn(str(e), UserWarning)
        app.config['SENTRY_DSN'] = config.SENTRY_DSN
        sentry = Sentry(app)
        app.sentry = sentry
    else:
        app.sentry = None

    ######

    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = config.SQL_ECHO

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    # config is deprecated since flask-sqlalchemy 2.4, should switch to engine_options
    app.config['SQLALCHEMY_POOL_SIZE'] = app.config['SQLALCHEMY_ENGINE_OPTIONS']['pool_size'] = 20

    db.init_app(app)
    migrate.init_app(app)

    app.wsgi_app = ProxyFix(app.wsgi_app)

    socketio.init_app(app)

    ########################
    ### TRANSPORT MODULE ###
    ########################

    from .transport import transport_bp as transport_blueprint
    from .transport.organization import bp as transport_organization_blueprint

    app.register_blueprint(transport_blueprint, url_prefix='/transport')
    app.register_blueprint(transport_organization_blueprint, url_prefix='/transport/organization')

    ####################
    ### DEBUG MODULE ###
    ####################

    from .debug import bp as debug_blueprint, config as debug_config
    from .debug.websocket import DebugNamespace

    socketio.on_namespace(DebugNamespace(debug_config.WS_NAMESPACE))
    app.register_blueprint(debug_blueprint, url_prefix=debug_config.PREFIX)

    ###################
    ## CITIES MODULE ##
    ###################

    from .city import bp as cities_blueprint, config as cities_config
    app.register_blueprint(cities_blueprint)

    ###################
    ### BOX MODULE ####
    ###################

    from .transport.box import bp as box_bp, config as box_config
    app.register_blueprint(box_bp, url_prefix=box_config.PREFIX)

    ############################
    ### ADVERTISEMENT MODULE ###
    ############################

    from .advertisement import bp as advertisement_bp, config as advertisement_config
    app.register_blueprint(advertisement_bp, url_prefix=advertisement_config.PREFIX)

    ######################
    ### REPORTS MODULE ###
    ######################

    from .reports import bp as report_bp, config as report_config
    app.register_blueprint(report_bp, url_prefix=report_config.PREFIX)

    ######################
    ### NETWORK MODULE ###
    ######################

    from .network import bp as network_bp, config as network_config
    app.register_blueprint(network_bp, url_prefix=network_config.PREFIX)

    from .mobile_app import bp as mobile_app_bp, config as mobile_app_config
    app.register_blueprint(mobile_app_bp, url_prefix=mobile_app_config.PREFIX)

    from .project import bp as test_project_bp
    app.register_blueprint(test_project_bp, url_prefix='/project')

    from .exceptions import register_error_handlers
    register_error_handlers(app)

    from .error_codes_info import register_error_code_info
    register_error_code_info(app)

    return app


prerun_hooks = []


def add_prerun_hook(prep: T.Callable[[], None]):
    prerun_hooks.append(prep)


def run_prerun_hooks(app=None, migrations: bool = True):
    if app is None:
        app = make_app()
    with app.app_context():
        def filter_func(f):
            is_migration = getattr(f, 'is_migration', False)
            if migrations:
                return is_migration
            else:
                return not is_migration
        hooks_to_run = filter(filter_func, prerun_hooks)
        for f in hooks_to_run:
            f()


db = SQLAlchemy()
migrate = Migrate(db=db)
socketio = SocketIO()


def run(host='0.0.0.0', port=5000, debug=False, **kwargs):
    app = make_app()
    if kwargs.pop('hooks', False):
        run_prerun_hooks(app=app, migrations=kwargs.pop('run_migrations', False))
    socketio.run(app, host=host, port=port, debug=debug, max_size=1024*10, **kwargs)
