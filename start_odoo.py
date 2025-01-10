#!/usr/bin/env python3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting Odoo with New Relic...")
logger.debug(f"New Relic License Key: {'*' * 5}{os.getenv('NEW_RELIC_LICENSE_KEY')[-5:] if os.getenv('NEW_RELIC_LICENSE_KEY') else 'Not Set'}")
logger.debug(f"New Relic App Name: {os.getenv('NEW_RELIC_APP_NAME', 'Not Set')}")

# Initialize gevent
logger.debug("Initializing gevent monkey patching...")
import gevent.monkey
gevent.monkey.patch_all()
logger.debug("Gevent monkey patching complete")

# Initialize New Relic
logger.debug("Initializing New Relic...")
import newrelic.agent
try:
    newrelic.agent.initialize('/etc/newrelic/newrelic.ini')
    logger.debug("New Relic initialization complete")

    # Add manual instrumentation
    @newrelic.agent.background_task()
    def background_task():
        logger.debug("Running background task...")
        return True

    # Run a test background task
    background_task()
    
    # Instrument HTTP endpoints
    def instrument_odoo():
        logger.debug("Instrumenting Odoo web controllers...")
        import odoo.http
        
        original_dispatch = odoo.http.Root.dispatch

        @newrelic.agent.function_trace()
        def instrumented_dispatch(self, environ, start_response):
            transaction = newrelic.agent.current_transaction()
            if transaction:
                logger.debug(f"Processing request in transaction: {transaction.name}")
            return original_dispatch(self, environ, start_response)

        odoo.http.Root.dispatch = instrumented_dispatch
        logger.debug("Odoo web controllers instrumented")

    instrument_odoo()

except Exception as e:
    logger.error(f"Failed to initialize New Relic: {str(e)}", exc_info=True)

import sys
import odoo

if __name__ == '__main__':
    logger.debug("Starting Odoo...")
    # Create application
    application = newrelic.agent.WSGIApplicationWrapper(odoo.service.wsgi_server.application)
    odoo.service.wsgi_server.application = application
    logger.debug("WSGI application wrapped with New Relic")
    
    sys.exit(odoo.cli.main())
