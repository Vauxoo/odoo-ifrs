# -*- coding: utf-8 -*-

{
    "name": "IFRS",
    "version": "0.6",
    "author": "Vauxoo",
    "category": "Accounting & Finance",
    "website": "http://www.vauxoo.com",
    "license": "",
    "depends": [
        "base",
        "account",
        "account_group_auditory",
        "account_periods_initial",
        "report",
        "controller_report_xls",
    ],
    "demo": [
        'demo/account.account.csv',
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "view/ifrs_view.xml",
        "view/wizard.xml",
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
    "installable": True,
    "auto_install": False,
    "application": True,
}
