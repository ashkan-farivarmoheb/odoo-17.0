#!/usr/bin/env python3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting Odoo with New Relic...")
logger.debug(f"New Relic License Key: {'*' * 5}{os.getenv('NEW_RELIC_LICENSE_KEY')[-5:] if os.getenv('NEW_RELIC_LICENSE_KEY') else 'Not Set'}")
logger.debug(f"New Relic App Name: {os.getenv('NEW_RELIC_APP_NAME', 'Not Set')}")
logger.debug(f"New Relic Config File: {os.getenv('NEW_RELIC_CONFIG_FILE', 'Not Set')}")

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
except Exception as e:
    logger.error(f"Failed to initialize New Relic: {str(e)}")

import sys
import odoo

if __name__ == '__main__':
    logger.debug("Starting Odoo...")
    sys.exit(odoo.cli.main())
