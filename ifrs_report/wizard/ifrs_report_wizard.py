# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api


class IfrsReportWizard(models.TransientModel):
    """
    This wizard allows to print report from templates for two or twelve columns
    let that be pdf or xls file.
    """

    _name = 'ifrs.report.wizard'
    _description = 'IFRS Report Wizard'
    _rec_name = 'report_type'

    @api.model
    def _default_fiscalyear(self):
        ctx = dict(self._context)
        if not ctx.get('active_ids'):
            return False
        return self.env['ifrs.ifrs'].browse(ctx['active_ids']).fiscalyear_id.id

    @api.model
    def _default_currency(self):
        ctx = dict(self._context)
        if not ctx.get('active_ids'):
            return False
        return self.env['ifrs.ifrs'].browse(ctx['active_ids']).currency_id.id

    period = fields.Many2one(
        'account.period', string='Force period',
        help=('Fiscal period to assign to the invoice. Keep empty to use the '
              'period of the current date.'))
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear', string='Fiscal Year',
        default=_default_fiscalyear,
        help=('Fiscal Year to be used in report'))
    company_id = fields.Many2one(
        'res.company', string='Company',
        ondelete='cascade', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'ifrs.ifrs'),
        help=('Company name'))
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        ondelete='cascade', required=True,
        default=_default_currency,
        help=('Currency at which this report will be expressed. If not '
              'selected will be used the one set in the company'))
    exchange_date = fields.Date(
        string='Exchange Date',
        default=fields.Date.context_today,
        help=('Date of change that will be printed in the report, with '
              'respect to the currency of the company'))
    report_type = fields.Selection(
        [('all', 'All Fiscalyear'),
         ('per', 'Force Period')],
        string='Type', required=True,
        default='all',
        help=('Indicates if the report it will be printed for the entire '
              'fiscal year, or for a particular period'))
    columns = fields.Selection(
        [('ifrs', 'Two Columns'),
         ('webkitaccount.ifrs_12', 'Twelve Columns')],
        string='Number of Columns', required=True,
        default='ifrs',
        help=('Number of columns that will be printed in the report:'
              ' -Two Colums(02),-Twelve Columns(12)'))
    target_move = fields.Selection(
        [('posted', 'All Posted Entries'),
         ('all', 'All Entries')],
        string='Target Moves',
        default='posted',
        help='Print All Accounting Entries or just Posted Accounting Entries')
    report_format = fields.Selection(
        [('pdf', 'PDF'),
         ('spreadsheet', 'Spreadsheet')],
        string='Report Format',
        default='pdf',
        help='Means if the report is to be print in PDF or XLS file')


class IfrsReportWizardInherit(osv.osv_memory):

    _inherit = 'ifrs.report.wizard'

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
