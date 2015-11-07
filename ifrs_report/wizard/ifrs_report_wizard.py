# -*- coding: utf-8 -*-

import time

from openerp.osv import fields, osv


class IfrsReportWizard(osv.osv_memory):

    """ Wizard que permite al usuario elegir que periodo quiere imprimir del
    año fiscal """

    _name = 'ifrs.report.wizard'
    _description = 'IFRS Report Wizard'
    _rec_name = 'report_type'

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        context = context and dict(context) or {}
        context['company_id'] = company_id
        res = {'value': {}}

        if not company_id:
            return res

        cur_id = self.pool.get('res.company').browse(
            cr, uid, company_id, context=context).currency_id.id
        fy_id = self.pool.get('account.fiscalyear').find(
            cr, uid, context=context)

        res['value'].update({'fiscalyear_id': fy_id})
        res['value'].update({'currency_id': cur_id})
        return res

    _columns = {
        'period': fields.many2one('account.period', 'Force period',
                                  help=('Fiscal period to assign to the\
                                        invoice. Keep empty to use the period\
                                        of the current date.')),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year',
                                         help='Fiscal Year'),
        'company_id': fields.many2one('res.company', string='Company',
                                      ondelete='cascade', required=True,
                                      help='Company name'),
        'currency_id':
            fields.many2one('res.currency', 'Currency',
                            help=('Currency at which this report will be \
                                  expressed. If not selected will be used the \
                                  one set in the company')),
        'exchange_date': fields.date('Exchange Date', help=('Date of change\
                                                            that will be\
                                                            printed in the\
                                                            report, with\
                                                            respect to the\
                                                            currency of the\
                                                            company')),
        'report_type': fields.selection([
            ('all', 'All Fiscalyear'),
            ('per', 'Force Period')],
            string='Type', required=True, help=('Indicates if the report it\
                                                will be printed for the entire\
                                                fiscal year, or for a\
                                                particular period')),
        'columns': fields.selection([
            ('ifrs', 'Two Columns'),
            ('webkitaccount.ifrs_12', 'Twelve Columns'),
            # ('ifrs_12_partner_detail', 'With Partner Detail')
        ],
            string='Number of Columns',
            help='Number of columns that will be printed in the report:'
            " -Two Colums(02),-Twelve Columns(12)"),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                         ], 'Target Moves', help=('Print All\
                                                                  Accounting\
                                                                  Entries or\
                                                                  just Posted\
                                                                  Accounting\
                                                                  Entries')),
        'report_format': fields.selection([
            ('pdf', 'PDF'),
            ('spreadsheet', 'Spreadsheet')], 'Report Format')
    }

    _defaults = {
        'report_type': 'all',
        'target_move': 'posted',
        'company_id': lambda self, cr, uid, c:
        self.pool.get('ifrs.ifrs').browse(cr, uid,
                                          c.get('active_id')).company_id.id,
        'fiscalyear_id': lambda self, cr, uid, c:
        self.pool.get('ifrs.ifrs').browse(cr, uid,
                                          c.get('active_id')).fiscalyear_id.id,
        'exchange_date': fields.date.today,
        'columns': 'ifrs',
        'report_format': 'pdf'
    }

    def default_get(self, cr, uid, ffields, context=None):
        context = context and dict(context) or {}
        res = super(IfrsReportWizard, self).default_get(
            cr, uid, ffields, context=context)
        # res.update({'uid_country':
        # self._get_country_code(cr,uid,context=context)})
        return res

    def print_report(self, cr, uid, ids, context=None):
        context = context and dict(context) or {}
        datas = {'active_ids': context.get('active_ids', [])}
        wizard_ifrs = self.browse(cr, uid, ids, context=context)[0]
        datas['wizard_id'] = wizard_ifrs.id
        datas['report_type'] = str(wizard_ifrs.report_type)
        datas['company'] = wizard_ifrs.company_id.id
        datas['target_move'] = wizard_ifrs.target_move
        datas['exchange_date'] = wizard_ifrs.exchange_date
        datas['currency_wizard'] = wizard_ifrs.currency_id.id
        datas['currency_wizard_name'] = wizard_ifrs.currency_id.name

        if datas['report_type'] == 'all':
            datas['fiscalyear'] = wizard_ifrs.fiscalyear_id.id
            datas['period'] = False
        else:
            datas['period'] = wizard_ifrs.period.id
            datas['fiscalyear'] = wizard_ifrs.fiscalyear_id.id

        if datas['report_type'] == 'all' and \
                str(wizard_ifrs.columns) == 'webkitaccount.ifrs_12':
            report_name = 'ifrs_report.ifrs_landscape_pdf_report'
            context['landscape'] = True
            datas['landscape'] = True
        else:
            report_name = 'ifrs_report.ifrs_portrait_pdf_report'
            datas['landscape'] = False

        context['xls_report'] = False
        if wizard_ifrs.report_format == 'spreadsheet':
            context['xls_report'] = True

        # This method will do a better job than me at arranging a dictionary to
        # print report
        return self.pool['report'].get_action(cr, uid, [], report_name,
                                              data=datas, context=context)
