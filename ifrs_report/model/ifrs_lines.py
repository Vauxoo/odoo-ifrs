# -*- coding: utf-8 -*-
# Copyright 2016 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division
import operator as op
from openerp import models, fields, api
LOGICAL_RESULT = [
    ('subtract', 'Left - Right'),
    ('addition', 'Left + Right'),
    ('lf', 'Left'),
    ('rg', 'Right'),
    ('zr', 'Zero (0)'),
]
LOGICAL_OPERATIONS = [
    ('gt', '>'),
    ('ge', '>='),
    ('lt', '<'),
    ('le', '<='),
    ('eq', '='),
    ('ne', '<>'),
]


class IfrsLines(models.Model):

    _name = 'ifrs.lines'
    _order = 'ifrs_id, sequence'

    def _get_sum_total(
            self, cr, uid, brw, operand, number_month=None,
            one_per=False, bag=None, context=None):
        """ Calculates the sum of the line total_ids & operand_ids the current
        ifrs.line
        @param number_month: period to compute
        """
        context = context and dict(context) or {}
        res = 0

        # If the report is two or twelve columns, will choose the field needed
        # to make the sum
        if context.get('whole_fy', False) or one_per:
            field_name = 'ytd'
        else:
            field_name = 'period_%s' % str(number_month)

        # It takes the sum of the total_ids & operand_ids
        for ttt in getattr(brw, operand):
            res += bag[ttt.id].get(field_name, 0.0)
        return res

    def _get_sum_detail(self, cr, uid, ids=None, number_month=None,
                        context=None):
        """ Calculates the amount sum of the line type == 'detail'
        @param number_month: periodo a calcular
        """
        fy_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        context = context and dict(context) or {}
        cx = context.copy()
        res = 0.0

        if not cx.get('fiscalyear'):
            cx['fiscalyear'] = fy_obj.find(cr, uid)

        fy_id = cx['fiscalyear']

        brw = self.browse(cr, uid, ids)

        if brw.acc_val == 'init':
            if cx.get('whole_fy', False):
                cx['periods'] = period_obj.search(cr, uid, [
                    ('fiscalyear_id', '=', fy_id), ('special', '=', True)])
            else:
                period_from = period_obj.search(cr, uid, [
                    ('fiscalyear_id', '=', fy_id), ('special', '=', True)])
                # Case when the period_from is the first non-special period
                # of the fiscalyear
                if period_obj.browse(cr, uid, cx['period_from']).date_start ==\
                        fy_obj.browse(cr, uid, fy_id).date_start:
                    cx['period_to'] = period_from[0]
                else:
                    cx['period_to'] = period_obj.previous(
                        cr, uid, cx['period_from'])
                cx['period_from'] = period_from[0]
        elif brw.acc_val == 'var':
            # it is going to be the one sent by the previous cx
            if cx.get('whole_fy', False):
                cx['periods'] = period_obj.search(cr, uid, [
                    ('fiscalyear_id', '=', fy_id), ('special', '=', False)])
        else:
            # it is going to be from the fiscalyear's beginning
            if cx.get('whole_fy', False):
                cx['periods'] = period_obj.search(cr, uid, [
                    ('fiscalyear_id', '=', fy_id)])
            else:
                period_from = period_obj.search(cr, uid, [
                    ('fiscalyear_id', '=', fy_id), ('special', '=', True)])
                cx['period_from'] = period_from[0]
                cx['periods'] = \
                    period_obj.build_ctx_periods(cr, uid, cx['period_from'],
                                                 cx['period_to'])

        if brw.type == 'detail':
            # Si es de tipo detail
            # If we have to only take into account a set of Journals
            cx['journal_ids'] = [aj_brw.id for aj_brw in brw.journal_ids]
            cx['analytic'] = [an.id for an in brw.analytic_ids]
            cx['ifrs_tax'] = [tx.id for tx in brw.tax_code_ids]
            cx['ifrs_partner'] = [p_brw.id for p_brw in brw.partner_ids]

            # NOTE: This feature is not yet been implemented
            # cx['partner_detail'] = cx.get('partner_detail')

            # Refreshing record with new context
            brw = self.browse(cr, uid, ids, context=cx)

            for aa in brw.cons_ids:
                # Se hace la sumatoria de la columna balance, credito o debito.
                # Dependiendo de lo que se escoja en el wizard
                if brw.value == 'debit':
                    res += aa.debit
                elif brw.value == 'credit':
                    res += aa.credit
                else:
                    res += aa.balance
        return res

    def _get_logical_operation(self, cr, uid, brw, ilf, irg, context=None):
        def result(brw, ifn, ilf, irg):
            if getattr(brw, ifn) == 'subtract':
                res = ilf - irg
            elif getattr(brw, ifn) == 'addition':
                res = ilf + irg
            elif getattr(brw, ifn) == 'lf':
                res = ilf
            elif getattr(brw, ifn) == 'rg':
                res = irg
            elif getattr(brw, ifn) == 'zr':
                res = 0.0
            return res

        context = dict(context or {})
        fnc = getattr(op, brw.logical_operation)

        if fnc(ilf, irg):
            res = result(brw, 'logical_true', ilf, irg)
        else:
            res = result(brw, 'logical_false', ilf, irg)
        return res

    def _get_grand_total(
            self, cr, uid, ids, number_month=None, one_per=False, bag=None,
            context=None):
        """ Calculates the amount sum of the line type == 'total'
        @param number_month: periodo a calcular
        """
        fy_obj = self.pool.get('account.fiscalyear')
        context = context and dict(context) or {}
        cx = context.copy()
        res = 0.0

        if not cx.get('fiscalyear'):
            cx['fiscalyear'] = fy_obj.find(cr, uid)

        brw = self.browse(cr, uid, ids)
        res = self._get_sum_total(
            cr, uid, brw, 'total_ids', number_month, one_per=one_per, bag=bag,
            context=cx)

        if brw.operator in ('subtract', 'condition', 'percent', 'ratio',
                            'product'):
            so = self._get_sum_total(
                cr, uid, brw, 'operand_ids', number_month, one_per=one_per,
                bag=bag, context=cx)
            if brw.operator == 'subtract':
                res -= so
            elif brw.operator == 'condition':
                res = self._get_logical_operation(cr, uid, brw, res, so,
                                                  context=cx)
            elif brw.operator == 'percent':
                res = so != 0 and (100 * res / so) or 0.0
            elif brw.operator == 'ratio':
                res = so != 0 and (res / so) or 0.0
            elif brw.operator == 'product':
                res = res * so
        return res

    def _get_constant(self, cr, uid, ids=None, number_month=None,
                      context=None):
        """ Calculates the amount sum of the line of constant
        @param number_month: periodo a calcular
        """
        cx = context or {}
        brw = self.browse(cr, uid, ids, context=cx)
        if brw.constant_type == 'constant':
            return brw.constant
        fy_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')

        if not cx.get('fiscalyear'):
            cx['fiscalyear'] = fy_obj.find(cr, uid, dt=None, context=cx)

        if not cx.get('period_from', False) and not cx.get('period_to', False):
            if context.get('whole_fy', False):
                cx['period_from'] = period_obj.find_special_period(
                    cr, uid, cx['fiscalyear'])
            cx['period_to'] = period_obj.search(
                cr, uid, [('fiscalyear_id', '=', cx['fiscalyear'])])[-1]

        if brw.constant_type == 'period_days':
            res = period_obj._get_period_days(
                cr, uid, cx['period_from'], cx['period_to'])
        elif brw.constant_type == 'fy_periods':
            res = fy_obj._get_fy_periods(cr, uid, cx['fiscalyear'])
        elif brw.constant_type == 'fy_month':
            res = fy_obj._get_fy_month(cr, uid, cx[
                                       'fiscalyear'], cx['period_to'])
        elif brw.constant_type == 'number_customer':
            res = self._get_number_customer_portfolio(cr, uid, ids, cx[
                'fiscalyear'], cx['period_to'], cx)
        return res

    def exchange(self, cr, uid, ids, from_amount, to_currency_id,
                 from_currency_id, exchange_date, context=None):
        context = context and dict(context) or {}
        if from_currency_id == to_currency_id:
            return from_amount
        curr_obj = self.pool.get('res.currency')
        context['date'] = exchange_date
        return curr_obj.compute(cr, uid, from_currency_id, to_currency_id,
                                from_amount, context=context)

    def _get_amount_value(
            self, cr, uid, ids, ifrs_line=None, period_info=None,
            fiscalyear=None, exchange_date=None, currency_wizard=None,
            number_month=None, target_move=None, pdx=None, undefined=None,
            two=None, one_per=False, bag=None, context=None):
        """ Returns the amount corresponding to the period of fiscal year
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        """

        context = context and dict(context) or {}
        # TODO: Current Company's Currency shall be used: the one on wizard
        from_currency_id = ifrs_line.ifrs_id.company_id.currency_id.id
        to_currency_id = currency_wizard

        if number_month:
            if two:
                context = {
                    'period_from': number_month, 'period_to': number_month}
            else:
                period_id = period_info[number_month][1]
                context = {'period_from': period_id, 'period_to': period_id}
        else:
            context = {'whole_fy': True}

        # NOTE: This feature is not yet been implemented
        # context['partner_detail'] = pdx
        context['fiscalyear'] = fiscalyear
        context['state'] = target_move

        if ifrs_line.type == 'detail':
            res = self._get_sum_detail(
                cr, uid, ifrs_line.id, number_month,
                context=context)
        elif ifrs_line.type == 'total':
            res = self._get_grand_total(
                cr, uid, ifrs_line.id, number_month,
                one_per=one_per, bag=bag, context=context)
        elif ifrs_line.type == 'constant':
            res = self._get_constant(cr, uid, ifrs_line.id, number_month,
                                     context=context)
        else:
            res = 0.0

        if ifrs_line.type == 'detail':
            res = self.exchange(
                cr, uid, ids, res, to_currency_id, from_currency_id,
                exchange_date, context=context)
        return res

    def _get_dict_amount_with_operands(
            self, cr, uid, ids, ifrs_line, period_info=None, fiscalyear=None,
            exchange_date=None, currency_wizard=None, month_number=None,
            target_move=None, pdx=None, undefined=None, two=None,
            one_per=False, bag=None, context=None):
        """ Integrate operand_ids field in the calculation of the amounts for
        each line
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param month_number: period number
        @param target_move: target move to consider
        """

        context = dict(context or {})

        direction = ifrs_line.inv_sign and -1.0 or 1.0

        res = {}
        for number_month in range(1, 13):
            field_name = 'period_%(month)s' % dict(month=number_month)
            bag[ifrs_line.id][field_name] = self._get_amount_value(
                cr, uid, ids, ifrs_line, period_info, fiscalyear,
                exchange_date, currency_wizard, number_month, target_move, pdx,
                undefined, two, one_per=one_per, bag=bag,
                context=context) * direction
            res[number_month] = bag[ifrs_line.id][field_name]

        return res

    def _get_amount_with_operands(
            self, cr, uid, ids, ifrs_l, period_info=None, fiscalyear=None,
            exchange_date=None, currency_wizard=None, number_month=None,
            target_move=None, pdx=None, undefined=None, two=None,
            one_per=False, bag=None, context=None):
        """ Integrate operand_ids field in the calculation of the amounts for
        each line
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        """

        context = context and dict(context) or {}

        if not number_month:
            context = {'whole_fy': True}

        res = self._get_amount_value(
            cr, uid, ids, ifrs_l, period_info, fiscalyear, exchange_date,
            currency_wizard, number_month, target_move, pdx, undefined, two,
            one_per=one_per, bag=bag, context=context)

        res = ifrs_l.inv_sign and (-1.0 * res) or res
        bag[ifrs_l.id]['ytd'] = res

        return res

    def _get_number_customer_portfolio(self, cr, uid, ids, fyr, period,
                                       context=None):
        ifrs_brw = self.browse(cr, uid, ids, context=context)
        company_id = ifrs_brw.ifrs_id.company_id.id
        if context.get('whole_fy', False):
            period_fy = [('period_id.fiscalyear_id', '=', fyr),
                         ('period_id.special', '=', False)]
        else:
            period_fy = [('period_id', '=', period)]
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(cr, uid, [
            ('type', '=', 'out_invoice'),
            ('state', 'in', ('open', 'paid',)),
            ('company_id', '=', company_id)] + period_fy)
        partner_number = \
            set([inv.partner_id.id for inv in
                 invoice_obj.browse(cr, uid, invoice_ids, context=context)])
        return len(list(partner_number))

    def onchange_sequence(self, cr, uid, ids, sequence, context=None):
        context = context and dict(context) or {}
        return {'value': {'priority': sequence}}

    @api.returns('self')
    def _get_default_help_bool(self):
        ctx = dict(self._context)
        return ctx.get('ifrs_help', True)

    @api.returns('self')
    def _get_default_sequence(self):
        ctx = dict(self._context)
        res = 0
        if not ctx.get('ifrs_id'):
            return res + 10
        ifrs_lines_ids = self.search([('ifrs_id', '=', ctx['ifrs_id'])])
        if ifrs_lines_ids:
            res = max(line.sequence for line in ifrs_lines_ids)
        return res + 10

    def onchange_type_without(self, cr, uid, ids, ttype, operator,
                              context=None):
        context = context and dict(context) or {}
        res = {}
        if ttype == 'total' and operator == 'without':
            res = {'value': {'operand_ids': []}}
        return res

    def write(self, cr, uid, ids, vals, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = super(IfrsLines, self).write(cr, uid, ids, vals)
        for ifrs_line in self.pool.get('ifrs.lines').browse(cr, uid, ids):
            if ifrs_line.type == 'total' and ifrs_line.operator == 'without':
                vals['operand_ids'] = [(6, 0, [])]
                super(IfrsLines, self).write(cr, uid, ifrs_line.id, vals)
        return res

    help = fields.Boolean(
        string='Show Help', copy=False, related='ifrs_id.help',
        default=_get_default_help_bool,
        help='Allows you to show the help in the form')
    # Really!!! A repeated field with same functionality! This was done due
    # to the fact that web view everytime that sees sequence tries to allow
    # you to change the values and this feature here is undesirable.
    sequence = fields.Integer(
        string='Sequence', default=_get_default_sequence,
        help=('Indicates the order of the line in the report. The sequence '
              'must be unique and unrepeatable'))
    priority = fields.Integer(
        string='Sequence', default=_get_default_sequence, related='sequence',
        help=('Indicates the order of the line in the report. The sequence '
              'must be unique and unrepeatable'))
    name = fields.Char(
        string='Name', size=128, required=True, translate=True,
        help=('Line name in the report. This name can be translatable, if '
              'there are multiple languages loaded it can be translated'))
    type = fields.Selection(
        [('abstract', 'Abstract'),
         ('detail', 'Detail'),
         ('constant', 'Constant'),
         ('total', 'Total')],
        string='Type', required=True, default='abstract',
        help=('Line type of report:  \n-Abstract(A),\n-Detail(D), '
              '\n-Constant(C),\n-Total(T)'))
    constant = fields.Float(
        string='Constant',
        help=('Fill this field with your own constant that will be used '
              'to compute in your other lines'),
        readonly=False)
    constant_type = fields.Selection(
        [('constant', 'My Own Constant'),
         ('period_days', 'Days of Period'),
         ('fy_periods', "FY's Periods"),
         ('fy_month', "FY's Month"),
         ('number_customer', "Number of customers* in portfolio")],
        string='Constant Type',
        required=False,
        help='Constant Type')
    ifrs_id = fields.Many2one(
        'ifrs.ifrs', string='IFRS',
        required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', related='ifrs_id.company_id',
        store=True)
    amount = fields.Float(
        string='Amount', readonly=True,
        help=('This field will update when you click the compute button in '
              'the IFRS doc form'))
    cons_ids = fields.Many2many(
        'account.account', 'ifrs_account_rel', 'ifrs_lines_id', 'account_id',
        string='Consolidated Accounts')
    journal_ids = fields.Many2many(
        'account.journal', 'ifrs_journal_rel', 'ifrs_lines_id', 'journal_id',
        string='Journals', required=False)
    analytic_ids = fields.Many2many(
        'account.analytic.account', 'ifrs_analytic_rel', 'ifrs_lines_id',
        'analytic_id', string='Consolidated Analytic Accounts')
    partner_ids = fields.Many2many(
        'res.partner', 'ifrs_partner_rel', 'ifrs_lines_id',
        'partner_id', string='Partners')
    tax_code_ids = fields.Many2many(
        'account.tax.code', 'ifrs_tax_rel', 'ifrs_lines_id',
        'tax_code_id', string='Tax Codes')
    parent_id = fields.Many2one(
        'ifrs.lines', string='Parent',
        ondelete='set null',
        domain=("[('ifrs_id','=',parent.id),"
                "('type','=','total'),('id','!=',id)]"))
    operand_ids = fields.Many2many(
        'ifrs.lines', 'ifrs_operand_rel', 'ifrs_parent_id', 'ifrs_child_id',
        string='Second Operand')
    operator = fields.Selection(
        [('subtract', 'Subtraction'),
         ('condition', 'Conditional'),
         ('percent', 'Percentage'),
         ('ratio', 'Ratio'),
         ('product', 'Product'),
         ('without', 'First Operand Only')],
        string='Operator', required=False,
        default='without',
        help='Leaving blank will not take into account Operands')
    logical_operation = fields.Selection(
        LOGICAL_OPERATIONS,
        string='Logical Operations', required=False,
        help=('Select type of Logical Operation to perform with First '
              '(Left) and Second (Right) Operand'))
    logical_true = fields.Selection(
        LOGICAL_RESULT,
        string='Logical True', required=False,
        help=('Value to return in case Comparison is True'))
    logical_false = fields.Selection(
        LOGICAL_RESULT,
        string='Logical False', required=False,
        help=('Value to return in case Comparison is False'))
    comparison = fields.Selection(
        [('subtract', 'Subtraction'),
         ('percent', 'Percentage'),
         ('ratio', 'Ratio'),
         ('without', 'No Comparison')],
        string='Make Comparison', required=False,
        default='without',
        help=('Make a Comparison against the previous period.\nThat is, '
              'period X(n) minus period X(n-1)\nLeaving blank will not '
              'make any effects'))
    acc_val = fields.Selection(
        [('init', 'Initial Values'),
         ('var', 'Variation in Periods'),
         ('fy', ('Ending Values'))],
        string='Accounting Span', required=False,
        default='fy',
        help='Leaving blank means YTD')
    value = fields.Selection(
        [('debit', 'Debit'),
         ('credit', 'Credit'),
         ('balance', 'Balance')],
        string='Accounting Value', required=False,
        default='balance',
        help='Leaving blank means Balance')
    total_ids = fields.Many2many(
        'ifrs.lines', 'ifrs_lines_rel', 'parent_id', 'child_id',
        string='First Operand')
    inv_sign = fields.Boolean(
        string='Change Sign to Amount', default=False, copy=True,
        help='Allows you to show the help in the form')
    invisible = fields.Boolean(
        string='Invisible', default=False, copy=True,
        help='Allows whether the line of the report is printed or not')
    comment = fields.Text(
        string='Comments/Question',
        help='Comments or questions about this ifrs line')

    _sql_constraints = [
        ('sequence_ifrs_id_unique', 'unique(sequence, ifrs_id)',
         'The sequence already have been set in another IFRS line')]

    def _get_level(self, cr, uid, lll, tree, level=1, context=None):
        """ Calcula los niveles de los ifrs.lines, tomando en cuenta que sera
        un mismo arbol para los campos total_ids y operand_ids.
        @param lll: objeto a un ifrs.lines
        @param level: Nivel actual de la recursion
        @param tree: Arbol de dependencias entre lineas construyendose
        """
        context = context and dict(context) or {}
        if not tree.get(level):
            tree[level] = {}
        # The search through level should be backwards from the deepest level
        # to the outmost level
        levels = tree.keys()
        levels.sort()
        levels.reverse()
        xlevel = False
        for nnn in levels:
            xlevel = isinstance(tree[nnn].get(lll.id), (set)) and nnn or xlevel
        if not xlevel:
            tree[level][lll.id] = set()
        elif xlevel < level:
            tree[level][lll.id] = tree[xlevel][lll.id]
            del tree[xlevel][lll.id]
        else:  # xlevel >= level
            return True
        for jjj in set(lll.total_ids + lll.operand_ids):
            tree[level][lll.id].add(jjj.id)
            self._get_level(cr, uid, jjj, tree, level + 1, context=context)
        return True
