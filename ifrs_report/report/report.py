#!/usr/bin/python
# -*- encoding: utf-8 -*-

import time

from openerp.osv import osv
from openerp.report import report_sxw


class ifrs_parser(report_sxw.rml_parse):
    _name = 'ifrs.parser'

    def __init__(self, cr, uid, name, context=None):
        super(ifrs_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        # This is a way of capturing objects as depicted in
        # odoo/addons/account/report/account_balance.py
        new_ids = ids
        if data.get('active_ids'):
            new_ids = data['active_ids']
            objects = self.pool.get('ifrs.ifrs').browse(self.cr, self.uid,
                                                        new_ids)
        return super(ifrs_parser, self).set_context(objects, data, new_ids,
                                                    report_type=report_type)


class ifrs_portrait_pdf_report(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="ifrs_report.ifrs_portrait_pdf_report"
    _name = 'report.ifrs_report.ifrs_portrait_pdf_report'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'
    _template = 'ifrs_report.ifrs_template'
    _wrapped_report_class = ifrs_parser


class ifrs_landscape_pdf_report(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="ifrs_report.ifrs_landscape_pdf_report"
    _name = 'report.ifrs_report.ifrs_landscape_pdf_report'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'
    _template = 'ifrs_report.ifrs_template'
    _wrapped_report_class = ifrs_parser

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
