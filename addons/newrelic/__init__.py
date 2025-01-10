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

            def wrap_wsgi():
                """Wrap WSGI application after server is fully initialized"""
                import odoo.service.wsgi_server
                if not hasattr(odoo.service.wsgi_server, '_nr_instrumented'):
                    odoo.service.wsgi_server._nr_instrumented = True
                    odoo.service.wsgi_server.application = newrelic.agent.WSGIApplicationWrapper(
                        odoo.service.wsgi_server.application
                    )
                    _logger.info('NewRelic WSGI application wrapped successfully')

                    # Instrument bus controller
                    try:
                        _logger.info('Attaching to bus controller')
                        import odoo.addons.bus.controllers.main
                        newrelic.agent.wrap_background_task(
                            odoo.addons.bus.controllers.main, 
                            'BusController._poll'
                        )
                        _logger.info('Finished attaching to bus controller')
                    except Exception as e:
                        _logger.warning('Failed to instrument bus controller: %s', e)

            # Register post-init hook
            if hasattr(odoo, 'conf'):
                odoo.conf.server_wide_modules.append('newrelic')
            
            # Hook into Odoo's post-init
            from odoo.modules.loading import post_init_hook_registry
            post_init_hook_registry.append(wrap_wsgi)

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

            # Patch error handling after http module is loaded
            def patch_error_handling():
                import odoo.http
                if hasattr(odoo.http, 'WebRequest'):
                    odoo.http.WebRequest._handle_exception = _nr_wrapper_handle_exception_(
                        odoo.http.WebRequest._handle_exception
                    )

            post_init_hook_registry.append(patch_error_handling)

        except Exception as e:
            _logger.error('Failed to initialize New Relic: %s', e, exc_info=True)

except ImportError:
    _logger.warning('newrelic python module not installed or other missing module')