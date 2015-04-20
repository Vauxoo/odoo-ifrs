#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# #############Credits######################################################
#    Coded by: Humberto Arocha <hbto@vauxoo.com>
#    Planified by: Rafael Silva <rsilvam@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
#############################################################################
#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or (at your
#    option) any later version.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#    or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
#    License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
{
    "name": "IFRS",
    "version": "0.6",
    "author": "Vauxoo",
    "category": "Accounting & Finance",
    "description": "",
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
    "active": False,
    "application": True,
}
