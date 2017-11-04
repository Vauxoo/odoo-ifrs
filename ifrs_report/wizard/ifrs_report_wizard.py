# -*- coding: utf-8 -*-

from openerp import models, fields, api


class IfrsReportWizard(models.TransientModel):
    """ This wizard allows to print report from templates for two or twelve
    columns let that be pdf or xls file. """

    _name = 'ifrs.report.wizard'
    _description = 'IFRS Report Wizard'
    _rec_name = 'ifrs_id'

    @api.multi
    def _default_ifrs(self):
        ctx = self._context
        res = False
        if ctx.get('active_id') and ctx.get('active_model') == 'ifrs.ifrs':
            return ctx.get('active_id')
        return res

    @api.multi
    def _default_fiscalyear(self):
        return self.env['account.fiscalyear'].find()

    @api.multi
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    ifrs_id = fields.Many2one(
        'ifrs.ifrs', string='IFRS Report Template',
        default=_default_ifrs,
        required=True)
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

    @api.multi
    def print_report(self):
        context = dict(
            self._context,
            active_id=self.ifrs_id.id,
            active_ids=[self.ifrs_id.id],
            active_model='ifrs.ifrs',
            )
        datas = {'active_ids': [self.ifrs_id.id]}
        datas['active_model'] = 'ifrs.ifrs'
        datas['active_model'] = 'ifrs.ifrs'
        datas['wizard_id'] = self.id
        datas['report_type'] = str(self.report_type)
        datas['company'] = self.company_id.id
        datas['target_move'] = self.target_move
        datas['exchange_date'] = self.exchange_date
        datas['currency_wizard'] = self.currency_id.id
        datas['currency_wizard_name'] = self.currency_id.name
        datas['fy_name'] = self.fiscalyear_id.name

        if datas['report_type'] == 'all':
            datas['fiscalyear'] = self.fiscalyear_id.id
            datas['period'] = False
        else:
            datas['period'] = self.period.id
            datas['fiscalyear'] = self.fiscalyear_id.id

        if datas['report_type'] == 'all' and \
                str(self.columns) == 'webkitaccount.ifrs_12':
            report_name = 'ifrs_report.ifrs_landscape_pdf_report'
            context['landscape'] = True
            datas['landscape'] = True
        else:
            report_name = 'ifrs_report.ifrs_portrait_pdf_report'
            datas['landscape'] = False

        context['xls_report'] = False
        if self.report_format == 'spreadsheet':
            context['xls_report'] = True

        # This method will do a better job than me at arranging a dictionary to
        # print report
        return self.env['report'].with_context(context).get_action(
            self.ifrs_id, report_name, data=datas)
