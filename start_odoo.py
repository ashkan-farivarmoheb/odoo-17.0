#!/usr/bin/env python3
import gevent.monkey
gevent.monkey.patch_all()

import newrelic.agent
newrelic.agent.initialize('/etc/newrelic/newrelic.ini')

import sys
import odoo

if __name__ == '__main__':
    sys.exit(odoo.cli.main())
