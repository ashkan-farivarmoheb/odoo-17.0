import os
from .strtobool import strtobool
import logging
_logger = logging.getLogger(__name__)

def is_true(strval):
    _logger.debug("newrelic is true? %s",bool(strtobool(strval or "0".lower())))
    return bool(strtobool(strval or "0".lower()))

try:
    import odoo
    from odoo.tools import config
    import newrelic.agent

    config_option = config.options

    if is_true(config_option.get("new_relic_enabled")):
        try:
            # Initialize New Relic first
            try:
                newrelic.agent.initialize(config_option.get("new_relic_config_file"), config_option.get("new_relic_environment"))
            except KeyError:
                try:
                    newrelic.agent.initialize(config_option.get("new_relic_config_file"))
                except KeyError:
                    _logger.info('NewRelic setting up from env variables')
                    newrelic.agent.initialize()

            # Ensure we're loaded as a server-wide module
            if hasattr(odoo, 'conf') and hasattr(odoo.conf, 'server_wide_modules'):
                if 'newrelic' not in odoo.conf.server_wide_modules:
                    odoo.conf.server_wide_modules.append('newrelic')

            def wrap_wsgi():
                """Wrap WSGI application after server is fully initialized"""
                import odoo.service.wsgi_server
                if not hasattr(odoo.service.wsgi_server, '_nr_instrumented'):
                    odoo.service.wsgi_server._nr_instrumented = True
                    odoo.http.root = newrelic.agent.WSGIApplicationWrapper(
                    odoo.http.root
                    )
                    _logger.info('NewRelic WSGI application wrapped successfully')

                    # Instrument WebSocket handler
                    try:
                        _logger.info('Attaching to websocket handler')
                        try:
                            from odoo.addons.bus.controllers import websocket
                        except ImportError as e:
                            _logger.error(f"Import error: {e}")
                        else:
                            newrelic.agent.wrap_function_trace(
                                odoo.addons.bus.controllers.websocket.WebsocketController,
                                'websocket'
                            )
                            newrelic.agent.wrap_function_trace(
                                odoo.addons.bus.controllers.websocket.WebsocketController,
                                'peek_notifications'
                            )
                            _logger.info('Finished attaching to websocket handler')
                    except Exception as e:
                        _logger.warning('Failed to instrument websocket handler: %s', e)

            # Error handling
            def status_code(exc, value, tb):
                from werkzeug.exceptions import HTTPException
                if isinstance(value, HTTPException):
                    return value.code

            def _nr_wrapper_handle_exception_(wrapped):
                def _handle_exception(*args, **kwargs):
                    transaction = newrelic.agent.current_transaction()
                    if transaction is None:
                        return wrapped(*args, **kwargs)
                    transaction.notice_error(status_code=status_code)
                    name = newrelic.agent.callable_name(args[1])
                    with newrelic.agent.FunctionTrace(transaction, name):
                        return wrapped(*args, **kwargs)
                return _handle_exception

            # Initialize at module load
            wrap_wsgi()

            # Patch error handling
            import odoo.http
            if hasattr(odoo.http, 'WebRequest'):
                original_handle_exception = odoo.http.WebRequest._handle_exception
                odoo.http.WebRequest._handle_exception = _nr_wrapper_handle_exception_(original_handle_exception)
                _logger.info('NewRelic error handling patched successfully')

        except Exception as e:
            _logger.error('Failed to initialize New Relic: %s', e, exc_info=True)

except ImportError:
    _logger.warning('newrelic python module not installed or other missing module')
