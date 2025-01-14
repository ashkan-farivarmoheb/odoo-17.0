{
    'name': 'NewRelic Instrumentation',
    'description': 'Wraps requests etc.',
    "version": "17.0.0.0",
    'website': 'https://tisol.com.au/',
    'author': 'Ashkan Farivarmoheb',
    'license': 'AGPL-3',
    'category': 'Tool',
    'depends': [
        'web', 'bus'
    ],
    'external_dependencies': {
        "python": ["newrelic"],
    },
    "installable": True,
    "application": False,
}
