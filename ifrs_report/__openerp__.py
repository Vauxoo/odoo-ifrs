# -*- coding: utf-8 -*-

{
    "name": "IFRS",
    "version": "8.0.0.0.7",
    "author": "Vauxoo",
    "category": "Accounting & Finance",
    "website": "http://www.vauxoo.com",
    "license": "",
    "depends": [
        "base",
        "account",
        "account_group_auditory",
        "report",
        "controller_report_xls",
    ],
    "demo": [
        'demo/demo.xml',
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "view/wizard.xml",
        "view/ifrs_view.xml",
        "report/layouts.xml",
        "report/template.xml",
        "data/report_paperformat.xml",
        "view/report.xml",
        "data/data_ifrs.xml",
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    'images': [
        'static/description/Banner.png',
    ],
    'price': 143.00,
    'currency': 'EUR',
    "installable": True,
    "auto_install": False,
    "application": True,
}
