# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by: Katherine Zaoral <katherine.zaoral@vauxoo.com>
#    Coded by: Yanina Aular <yanina.aular@vauxoo.com>
#    Planified by: Humberto Arocha <hbto@vauxoo.com>
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
##########################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _
import operator as op
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


class ifrs_ifrs(osv.osv):

    _name = 'ifrs.ifrs'
    _rec_name = 'code'

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
        'name': fields.char('Name', 128, required=True, help='Report name'),
        'company_id': fields.many2one('res.company', string='Company',
                                      ondelete='cascade', help='Company name'),
        'currency_id':
            fields.related('company_id', 'currency_id', type='many2one',
                           relation='res.currency', string='Company Currency',
                           help=('Currency at which this report will be \
                                 expressed. If not selected will be used the \
                                 one set in the company')),
        'title':
            fields.char('Title', 128, required=True, translate=True,
                        help='Report title that will be printed'),
        'code': fields.char('Code', 128, required=True, help='Report code'),
        'description': fields.text('Description'),
        'ifrs_lines_ids':
            fields.one2many('ifrs.lines', 'ifrs_id', 'IFRS lines', copy=True),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('ready', 'Ready'),
             ('done', 'Done'),
             ('cancel', 'Cancel')],
            'State', required=True),
        'fiscalyear_id':
            fields.many2one('account.fiscalyear', 'Fiscal Year',
                            help='Fiscal Year'),
        'help':
            fields.boolean('Show Help',
                           help='Allows you to show the help in the form'),
        'ifrs_ids':
            fields.many2many('ifrs.ifrs', 'ifrs_m2m_rel', 'parent_id',
                             'child_id', string='Other Reportes',)
    }

    _defaults = {
        'state': 'draft',
        'help': True,
        'company_id': lambda s, c, u, cx: s.pool.get('res.users').browse(
            c, u, u, context=cx).company_id.id,
        'fiscalyear_id': lambda s, c, u, cx: s.pool['account.fiscalyear'].find(
            c, u, exception=False),
    }

    def _get_level(self, cr, uid, lll, level, tree, context=None):
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
            self._get_level(cr, uid, jjj, level + 1, tree, context=context)
        return True

    def get_ordered_lines(self, cr, uid, ids, context=None):
        """ Return list of browse ifrs_lines per level in order ASC, for can
        calculate in order of priorities.
        """
        context = context and dict(context) or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        ifrs_brw = self.browse(cr, uid, ids[0], context=context)
        tree = {1: {}}
        level = 1
        for lll in ifrs_brw.ifrs_lines_ids:
            self._get_level(cr, uid, lll, level, tree, context=context)
        levels = tree.keys()
        levels.sort()
        levels.reverse()
        ids_x = []  # List of ids per level in order ASC
        for i in levels:
            ids_x += tree[i].keys()
        return ids_x

    def _get_ordered_lines(self, cr, uid, ids, context=None):
        """ Return list of browse ifrs_lines per level in order ASC, for can
        calculate in order of depending.

        Retorna la lista de ifrs.lines del ifrs_id organizados desde el nivel
        mas bajo hasta el mas alto. Lo niveles mas bajos se deben calcular
        primero, por eso se posicionan en primer lugar de la lista.
        """
        ids_x = self.get_ordered_lines(cr, uid, ids, context=context)
        if not ids_x:
            return []

        il_obj = self.pool.get('ifrs.lines')
        # List of browse per level in order ASC
        return il_obj.browse(cr, uid, ids_x, context=context)

    def compute(self, cr, uid, ids, context=None):
        """ Se encarga de calcular los montos para visualizarlos desde
        el formulario del ifrs, hace una llamada al get_report_data, el
        cual se encarga de realizar los calculos.
        """
        context = context and dict(context) or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        fy = self.browse(cr, uid, ids, context=context)[0]
        context.update({'whole_fy': True, 'fiscalyear': fy.fiscalyear_id.id})
        self.get_report_data(cr, uid, ids, is_compute=True, context=context)
        return True

    def _get_periods_name_list(self, cr, uid, ids, fiscalyear_id,
                               context=None):
        """ Devuelve una lista con la info de los periodos fiscales
        (numero mes, id periodo, nombre periodo)
        @param fiscalyear_id: Año fiscal escogido desde el wizard encargada
        de preparar el reporte para imprimir
        """
        context = context and dict(context) or {}

        period_list = []
        period_list.append(('0', None, ' '))

        fiscalyear_bwr = self.pool.get('account.fiscalyear').browse(
            cr, uid, fiscalyear_id, context=context)

        periods_ids = fiscalyear_bwr._get_fy_period_ids()
        periods_ids = periods_ids and isinstance(
            periods_ids[0], (list,)) and periods_ids[0] or periods_ids
        periods = self.pool.get('account.period')

        for ii, period_id in enumerate(periods_ids, start=1):
            period_list.append((str(ii), period_id, periods.browse(
                cr, uid, period_id, context=context).name))
        return period_list

    def _get_period_print_info(self, cr, uid, ids, period_id, report_type,
                               context=None):
        """ Return all the printable information about period
        @param period_id: Dependiendo del report_type, en el caso que sea
        'per', este campo indica el periodo a tomar en cuenta, en caso de que
        el report_type sea 'all', es Falso.
        @param report_type: Su valor se establece desde el wizard que se
        encarga de preparar al reporte para imprimir, el report_type puede ser
        'all' (incluir todo el año fiscal en el reporte) o 'per' (tomar en
        cuenta solo un periodo determinado en el reporte)
        """
        context = context and dict(context) or {}
        if report_type == 'all':
            res = _('ALL PERIODS OF THE FISCALYEAR')
        else:
            period = self.pool.get('account.period').browse(
                cr, uid, period_id, context=context)
            res = str(period.name) + ' [' + str(period.code) + ']'
        return res

    def get_period_print_info(self, cr, uid, ids, period_id, report_type,
                              context=None):
        return self._get_period_print_info(cr, uid, ids, period_id,
                                           report_type, context=context)

    def step_sibling(self, cr, uid, old_id, new_id, context=None):
        '''
        Sometimes total_ids and operand_ids include lines from their own
        ifrs_id report, They are siblings. In this case m2m copy_data just make
        a link from the old report.
        In the new report we have to substitute the cousins that are pretending
        to be siblings with the siblings
        This can be achieved due to the fact that each line has unique sequence
        within each report, using the analogy about relatives then each
        pretending cousin is of same age than that of the actual sibling
        cousins with common parent are siblings among them
        '''
        context = context and dict(context) or {}

        old_brw = self.browse(cr, uid, old_id, context=context)
        new_brw = self.browse(cr, uid, new_id, context=context)
        il_obj = self.pool.get('ifrs.lines')

        sibling_ids = {}
        markt = []
        marko = []
        for lll in old_brw.ifrs_lines_ids:
            for ttt in lll.total_ids:
                if ttt.ifrs_id.id == lll.ifrs_id.id:
                    sibling_ids[ttt.sequence] = ttt.id
                    markt.append(lll.sequence)
            for o in lll.operand_ids:
                if o.ifrs_id.id == lll.ifrs_id.id:
                    sibling_ids[o.sequence] = o.id
                    marko.append(lll.sequence)

        if not sibling_ids:
            return True

        markt = markt and set(markt) or []
        marko = marko and set(marko) or []

        o2n = {}
        for seq in sibling_ids:
            ns_id = il_obj.search(cr, uid, [('sequence', '=', seq),
                                            ('ifrs_id', '=', new_id)],
                                  context=context)
            o2n[sibling_ids[seq]] = ns_id and ns_id[0]

        for nl in new_brw.ifrs_lines_ids:
            if nl.sequence in markt:
                tt = [o2n.get(nt.id, nt.id) for nt in nl.total_ids]
                nl.write({'total_ids': [(6, 0, tt)]})
            if nl.sequence in marko:
                oo = [o2n.get(no.id, no.id) for no in nl.operand_ids]
                nl.write({'operand_ids': [(6, 0, oo)]})

        return True

    def copy_data(self, cr, uid, ids, default=None, context=None):
        res = super(ifrs_ifrs, self).copy_data(cr, uid, ids, default, context)
        if res.get('ifrs_lines_ids', False) and \
                context.get('clear_cons_ids', False):
            for lll in res['ifrs_lines_ids']:
                lll[2]['cons_ids'] = lll[2]['type'] == 'detail' and \
                    lll[2]['cons_ids'] and [] or []
        return res

    def copy(self, cr, uid, ids, default=None, context=None):
        context = context and dict(context) or {}
        default = default or {}
        ru_brw = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        ii_brw = self.pool.get('ifrs.ifrs').browse(
            cr, uid, ids, context=context)
        if ru_brw.company_id.id != ii_brw.company_id.id:
            context['clear_cons_ids'] = True
            default['company_id'] = ru_brw.company_id.id
            default['fiscalyear_id'] = \
                self.pool.get('account.fiscalyear').find(cr, uid,
                                                         exception=False,
                                                         context=context)
        res = super(ifrs_ifrs, self).copy(cr, uid, ids, default, context)
        self.step_sibling(cr, uid, ids, res, context=context)
        return res

    def _get_children_and_consol(self, cr, uid, ids, level, context=None):
        """ Retorna todas las cuentas relacionadas con las cuentas ids
        recursivamente, incluyendolos
        """
        context = context and dict(context) or {}
        aa_obj = self.pool.get('account.account')
        ids2 = []
        for aa_brw in aa_obj.browse(cr, uid, ids, context):
            if not aa_brw.child_id and aa_brw.level < \
                    level and aa_brw.type not in ('consolidation', 'view'):
                ids2.append(aa_brw.id)
            else:
                ids2.append(aa_brw.id)
                ids2 += \
                    self._get_children_and_consol(cr, uid,
                                                  [x.id for x in
                                                   aa_brw.child_id], level,
                                                  context=context)
        return list(set(ids2))

    def get_num_month(self, cr, uid, ids, fiscalyear, period, context=None):
        accountfy_obj = self.pool.get('account.fiscalyear')
        return accountfy_obj._get_fy_month(cr, uid, fiscalyear, period,
                                           special=False, context=context)

    def get_report_data(self, cr, uid, ids, fiscalyear=None,
                        exchange_date=None, currency_wizard=None,
                        target_move=None, period=None, two=None,
                        is_compute=None, context=None):
        """ Metodo que se encarga de retornar un diccionario con los montos
        totales por periodo de cada linea, o la sumatoria de todos montos
        por periodo de cada linea. La información del diccionario se utilizara
        para llenar el reporte, ya sea de dos columnas o de 12 columnas.
        @param fiscalyear: Año fiscal que se reflejara en el reporte
        @param exchange_date:
        @param currency_wizard: Moneda que se reflejara en el reporte
        @param target_move: Asientos contables a tomar en cuenta en los
        calculos
        @param period: Periodo a reflejar en caso de que no se tome en cuenta
        todo el año fiscal
        @param two: Nos dice si el reporte es de 2 o 12 columnas
        """
        context = context and dict(context) or {}

        data = []

        ifrs_line = self.pool.get('ifrs.lines')

        if is_compute is None:
            period_name = self._get_periods_name_list(
                cr, uid, ids, fiscalyear, context=context)

        ordered_lines = self._get_ordered_lines(cr, uid, ids, context=context)

        # Si es llamado desde el metodo compute, solo se actualizaran los
        # montos y no se creara el diccionario
        if is_compute:
            for ifrs_l in ordered_lines:
                ifrs_line._get_amount_with_operands(cr, uid, ids, ifrs_l,
                                                    is_compute=True,
                                                    context=context)
        else:
            if two:
                if period is not None:
                    one_per = True
                for ifrs_l in ordered_lines:
                    amount_value = \
                        ifrs_line._get_amount_with_operands(cr, uid, ids,
                                                            ifrs_l,
                                                            period_name,
                                                            fiscalyear,
                                                            exchange_date,
                                                            currency_wizard,
                                                            period,
                                                            target_move,
                                                            two=two,
                                                            one_per=one_per,
                                                            context=context)

                    line = {'sequence': int(ifrs_l.sequence),
                            'id': ifrs_l.id,
                            'name': ifrs_l.name,
                            'invisible': ifrs_l.invisible,
                            'type': str(ifrs_l.type),
                            'amount': amount_value,
                            'comparison': ifrs_l.comparison,
                            'operator': ifrs_l.operator}

                    # Se toman las lineas del ifrs actual, ya que en los
                    # calculos se incluyen lineas de otros ifrs
                    if ifrs_l.ifrs_id.id == ids[0]:
                        data.append(line)

            else:
                for ifrs_l in ordered_lines:
                    line = {
                        'id': ifrs_l.id,
                        'sequence': int(ifrs_l.sequence),
                        'name': ifrs_l.name,
                        'invisible': ifrs_l.invisible,
                        'type': ifrs_l.type,
                        'period': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
                                   8: 0, 9: 0, 10: 0, 11: 0, 12: 0},
                        'comparison': ifrs_l.comparison,
                        'operator': ifrs_l.operator}
                    for lins in range(1, 13):
                        amount_value = ifrs_line._get_amount_with_operands(
                            cr, uid, ids, ifrs_l, period_name, fiscalyear,
                            exchange_date, currency_wizard, lins, target_move,
                            context=context)
                        line['period'][lins] = amount_value

                    if ifrs_l.ifrs_id.id == ids[0]:
                        # Se toman las lineas del ifrs actual, ya que en los
                        # calculos se incluyen lineas de otros ifrs
                        data.append(line)

        for i in xrange(1, 13):
            cr.execute("update ifrs_lines set period_" + str(i) + "= 0.0;")
        data.sort(key=lambda x: int(x['sequence']))
        return data


class ifrs_lines(osv.osv):

    _name = 'ifrs.lines'
    _order = 'ifrs_id, sequence'

    def _get_sum_total(self, cr, uid, brw, operand, number_month=None,
                       is_compute=None, one_per=False, context=None):
        """ Calculates the sum of the line total_ids & operand_ids the current
        ifrs.line
        @param number_month: period to compute
        @param is_compute: if method will update amount field in view
        """
        context = context and dict(context) or {}
        res = 0

        # If the report is two or twelve columns, will choose the field needed
        # to make the sum
        if is_compute:
            field_name = 'amount'
        else:
            if context.get('whole_fy', False) or one_per:
                field_name = 'ytd'
            else:
                field_name = 'period_%s' % str(number_month)

        # It takes the sum of the total_ids
        for ttt in getattr(brw, operand):
            res += getattr(ttt, field_name)
        return res

    def _get_sum_detail(self, cr, uid, ids=None, number_month=None,
                        is_compute=None, context=None):
        """ Calculates the amount sum of the line type == 'detail'
        @param number_month: periodo a calcular
        @param is_compute: if method will update amount field in view
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
            analytic = [an.id for an in brw.analytic_ids]
            # Tomo los ids de las cuentas analiticas de las lineas
            if analytic:
                # Si habian cuentas analiticas en la linea, se guardan en el
                # context y se usan en algun metodo dentro del modulo de
                # account
                cx['analytic'] = analytic
            cx['partner_detail'] = cx.get('partner_detail')

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

    def _get_grand_total(self, cr, uid, ids=None, number_month=None,
                         is_compute=None, one_per=False, context=None):
        """ Calculates the amount sum of the line type == 'total'
        @param number_month: periodo a calcular
        @param is_compute: if method will update amount field in view
        """
        fy_obj = self.pool.get('account.fiscalyear')
        context = context and dict(context) or {}
        cx = context.copy()
        res = 0.0

        if not cx.get('fiscalyear'):
            cx['fiscalyear'] = fy_obj.find(cr, uid)

        brw = self.browse(cr, uid, ids)
        res = self._get_sum_total(cr, uid, brw, 'total_ids', number_month,
                                  is_compute, one_per=one_per, context=cx)

        if brw.operator in ('subtract', 'condition', 'percent', 'ratio',
                            'product'):
            so = self._get_sum_total(cr, uid, brw, 'operand_ids', number_month,
                                     is_compute, one_per=one_per, context=cx)
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
                      is_compute=None, context=None):
        """ Calculates the amount sum of the line of constant
        @param number_month: periodo a calcular
        @param is_compute: if method will update amount field in view
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
                cx['period_from'] = \
                    period_obj.search(cr, uid,
                                      [('fiscalyear_id', '=',
                                        cx['fiscalyear']),
                                       ('special', '=', True)])
                if not cx['period_from']:
                    raise osv.except_osv(_('Error !'),
                                         _('There are no special period in %s')
                                         % (fy_obj.browse(cr, uid,
                                                          cx['fiscalyear'],
                                                          context=cx).name))
                cx['period_from'] = cx['period_from'][0]
            cx['period_to'] = \
                period_obj.search(
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

    def _get_children_and_total(self, cr, uid, ids, context=None):
        """this function search for all the children and all consolidated
        children (recursively) of the given total ids
        """
        ids3 = []
        ids2 = []
        sql = 'select * from ifrs_lines_rel where parent_id in (' + ','.join(
            [str(idx) for idx in ids]) + ')'
        cr.execute(sql)
        childs = cr.fetchall()
        for rec in childs:
            ids2.append(rec[1])
            self.write(cr, uid, rec[1], {'parent_id': rec[0]})
            rec = self.browse(cr, uid, rec[1], context=context)
            for child in rec.total_ids:
                ids3.append(child.id)
        if ids3:
            ids3 = self._get_children_and_total(cr, uid, ids3, context=context)
        return ids2 + ids3

    def exchange(self, cr, uid, ids, from_amount, to_currency_id,
                 from_currency_id, exchange_date, context=None):
        context = context and dict(context) or {}
        if from_currency_id == to_currency_id:
            return from_amount
        curr_obj = self.pool.get('res.currency')
        context['date'] = exchange_date
        return curr_obj.compute(cr, uid, from_currency_id, to_currency_id,
                                from_amount, context=context)

    def _get_amount_value(self, cr, uid, ids, ifrs_line=None, period_info=None,
                          fiscalyear=None, exchange_date=None,
                          currency_wizard=None, number_month=None,
                          target_move=None, pdx=None, undefined=None, two=None,
                          is_compute=None, one_per=False, context=None):
        """ Returns the amount corresponding to the period of fiscal year
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        @param is_compute: if method will update amount field in view
        """

        context = context and dict(context) or {}
        from_currency_id = ifrs_line.ifrs_id.company_id.currency_id.id
        to_currency_id = currency_wizard

        ifrs_line = self.browse(cr, uid, ifrs_line.id)

        if number_month:
            if two:
                context = {
                    'period_from': number_month, 'period_to': number_month}
            else:
                period_id = period_info[number_month][1]
                context = {'period_from': period_id, 'period_to': period_id}
        else:
            context = {'whole_fy': True}

        context['partner_detail'] = pdx
        context['fiscalyear'] = fiscalyear
        context['state'] = target_move

        if ifrs_line.type == 'detail':
            res = self._get_sum_detail(cr, uid, ifrs_line.id, number_month,
                                       is_compute, context=context)
        elif ifrs_line.type == 'total':
            res = self._get_grand_total(cr, uid, ifrs_line.id, number_month,
                                        is_compute, one_per=one_per,
                                        context=context)
        elif ifrs_line.type == 'constant':
            res = self._get_constant(cr, uid, ifrs_line.id, number_month,
                                     is_compute, context=context)
        else:
            res = 0.0

        if ifrs_line.type == 'detail':
            res = self.exchange(
                cr, uid, ids, res, to_currency_id, from_currency_id,
                exchange_date, context=context)
        return res

    def _get_amount_with_operands(self, cr, uid, ids, ifrs_line,
                                  period_info=None, fiscalyear=None,
                                  exchange_date=None, currency_wizard=None,
                                  number_month=None, target_move=None,
                                  pdx=None, undefined=None, two=None,
                                  one_per=False, is_compute=None,
                                  context=None):
        """
        Integrate operand_ids field in the calculation of the amounts for each
        line
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        @param is_compute: if method will update amount in view
        """

        context = context and dict(context) or {}

        ifrs_line = self.browse(cr, uid, ifrs_line.id)
        if not number_month:
            context = {'whole_fy': True}

        if is_compute:
            field_name = 'amount'
        else:
            if context.get('whole_fy', False) or one_per:
                field_name = 'ytd'
            else:
                field_name = 'period_%s' % str(number_month)

        res = self._get_amount_value(
            cr, uid, ids, ifrs_line, period_info, fiscalyear, exchange_date,
            currency_wizard, number_month, target_move, pdx, undefined, two,
            is_compute, one_per=one_per, context=context)

        res = ifrs_line.inv_sign and (-1.0 * res) or res
        self.write(cr, uid, ifrs_line.id, {field_name: res})

        return res

    def _get_partner_detail(self, cr, uid, ids, ifrs_l, context=None):
        account_obj = self.pool.get('account.account')
        partner_obj = self.pool.get('res.partner')
        res = []
        if ifrs_l.type == 'detail':
            ids2 = [lin.id for lin in ifrs_l.cons_ids]
            ids3 = ids2 and account_obj._get_children_and_consol(
                cr, uid, ids2, context=context) or []
            if ids3:
                cr.execute("""
                    SELECT rp.id
                    FROM account_move_line l
                           JOIN res_partner rp ON rp.id = l.partner_id
                    WHERE l.account_id IN %s
                    GROUP BY rp.id
                    ORDER BY rp.name ASC""", (tuple(ids3), ))
                dat = cr.dictfetchall()
                res = [lins for lins in
                       partner_obj.browse(cr, uid, [li['id'] for li in dat],
                                          context=context)]
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

    def _get_default_sequence(self, cr, uid, context=None):
        ctx = context or {}
        res = 0
        if ctx.get('ifrs_id'):
            ifrs_lines_ids = \
                self.search(cr, uid, [('ifrs_id', '=', ctx['ifrs_id'])])
            if ifrs_lines_ids:
                res = max([line['sequence'] for line in
                           self.read(cr, uid, ifrs_lines_ids, ['sequence'])])
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
        res = super(ifrs_lines, self).write(cr, uid, ids, vals)
        for ifrs_line in self.pool.get('ifrs.lines').browse(cr, uid, ids):
            if ifrs_line.type == 'total' and ifrs_line.operator == 'without':
                vals['operand_ids'] = [(6, 0, [])]
                super(ifrs_lines, self).write(cr, uid, ifrs_line.id, vals)
        return res

    _columns = {
        'help':
            fields.related('ifrs_id', 'help', string='Show Help',
                           type='boolean',
                           help='Allows you to show the help in the form'),
        # Really!!! A repeated field with same functionality! This was done due
        # to the fact that web view everytime that sees sequence tries to allow
        # you to change the values and this feature here is undesirable.
        'priority':
            fields.related('sequence', string='Sequence', type='integer',
                           store=True,
                           help=('Indicates the order of the line in \
                           the report. The sequence must be unique and \
                           unrepeatable')),
        'sequence':
            fields.integer('Sequence', required=True,
                           help=('Indicates the order of the line in the \
                                 report. The sequence must be unique and \
                                 unrepeatable')),
        'name':
            fields.char('Name', 128, required=True, translate=True,
                        help=('Line name in the report. This name can be \
                              translatable, if there are multiple languages \
                              loaded it can be translated')),
        'type':
            fields.selection(
                [('abstract', 'Abstract'),
                 ('detail', 'Detail'),
                 ('constant', 'Constant'),
                 ('total', 'Total')],
                string='Type',
                required=True,
                help='Line type of report:'
                " -Abstract(A),-Detail(D),-Constant(C),-Total(T)"),
        'constant': fields.float(
            string='Constant',
            help=('Fill this field with your own constant that will be used '
                  'to compute in your other lines'),
            readonly=False),
        'constant_type':
            fields.selection(
                [('constant', 'My Own Constant'),
                 ('period_days', 'Days of Period'),
                 ('fy_periods', "FY's Periods"),
                 ('fy_month', "FY's Month"),
                 ('number_customer', "Number of customers* in portfolio")],
                string='Constant Type',
                required=False,
                help='Constant Type'),
        'ifrs_id': fields.many2one('ifrs.ifrs', 'IFRS', required=True),
        'company_id':
            fields.related('ifrs_id', 'company_id', type='many2one',
                           relation='res.company', string='Company',
                           store=True),
        'amount':
            fields.float(string='Amount',
                         help=('This field will update when you click the \
                               compute button in the IFRS doc form'),
                         readonly=True),
        'cons_ids':
            fields.many2many('account.account', 'ifrs_account_rel',
                             'ifrs_lines_id', 'account_id',
                             string='Consolidated Accounts'),
        'journal_ids': fields.many2many(
            'account.journal', 'ifrs_journal_rel',
            'ifrs_lines_id', 'journal_id', 'Journals', required=False),
        'analytic_ids':
            fields.many2many('account.analytic.account', 'ifrs_analytic_rel',
                             'ifrs_lines_id', 'analytic_id', string=(
                                 'Consolidated Analytic Accounts')),
        'parent_id':
            fields.many2one('ifrs.lines', 'Parent', select=True,
                            ondelete='set null', domain=(
                                "[('ifrs_id','=',parent.id),\
                                ('type','=','total'),('id','!=',id)]")),
        'parent_abstract_id':
            fields.many2one('ifrs.lines', 'Parent Abstract', select=True,
                            ondelete='set null',
                            domain=('[("ifrs_id","=",parent.id),\
                                    ("type","=","abstract"),\
                                    ("id","!=",id)]')),
        'operand_ids': fields.many2many('ifrs.lines', 'ifrs_operand_rel',
                                        'ifrs_parent_id', 'ifrs_child_id',
                                        string='Second Operand'),
        'operator': fields.selection(
            [('subtract', 'Subtraction'),
             ('condition', 'Conditional'),
             ('percent', 'Percentage'),
             ('ratio', 'Ratio'),
             ('product', 'Product'),
             ('without', 'First Operand Only')],
            'Operator', required=False,
            help='Leaving blank will not take into account Operands'),
        'logical_operation': fields.selection(
            LOGICAL_OPERATIONS,
            'Logical Operations', required=False,
            help=('Select type of Logical Operation to perform with First '
                  '(Left) and Second (Right) Operand')),
        'logical_true': fields.selection(
            LOGICAL_RESULT,
            'Logical True', required=False,
            help=('Value to return in case Comparison is True')),
        'logical_false': fields.selection(
            LOGICAL_RESULT,
            'Logical False', required=False,
            help=('Value to return in case Comparison is False')),
        'comparison': fields.selection(
            [('subtract', 'Subtraction'),
             ('percent', 'Percentage'),
             ('ratio', 'Ratio'),
             ('without', 'No Comparison')],
            'Make Comparison', required=False,
            help=('Make a Comparison against the previous period.\nThat is, \
                  period X(n) minus period X(n-1)\nLeaving blank will not \
                  make any effects')),
        'acc_val': fields.selection(
            [('init', 'Initial Values'),
             ('var', 'Variation in Periods'),
             ('fy', ('Ending Values'))],
            'Accounting Span', required=False,
            help='Leaving blank means YTD'),
        'value': fields.selection(
            [('debit', 'Debit'),
             ('credit', 'Credit'),
             ('balance', 'Balance')],
            'Accounting Value', required=False,
            help='Leaving blank means Balance'),
        'total_ids': fields.many2many('ifrs.lines', 'ifrs_lines_rel',
                                      'parent_id', 'child_id',
                                      string='First Operand'),
        'inv_sign': fields.boolean('Change Sign to Amount',
                                   help='Allows a change of sign'),
        'invisible':
            fields.boolean('Invisible',
                           help=('Allows whether the line of the report is \
                                 printed or not')),
        'comment': fields.text('Comments/Question',
                               help=('Comments or questions about this ifrs \
                                     line')),
        'ytd': fields.float('YTD', help=('amount control field, functions to \
                                         prevent repeated computes')),
        'period_1': fields.float('Periodo 1'),
        'period_2': fields.float('Periodo 2'),
        'period_3': fields.float('Periodo 3'),
        'period_4': fields.float('Periodo 4'),
        'period_5': fields.float('Periodo 5'),
        'period_6': fields.float('Periodo 6'),
        'period_7': fields.float('Periodo 7'),
        'period_8': fields.float('Periodo 8'),
        'period_9': fields.float('Periodo 9'),
        'period_10': fields.float('Periodo 10'),
        'period_11': fields.float('Periodo 11'),
        'period_12': fields.float('Periodo 12'),
    }

    _defaults = {
        'type': 'abstract',
        'invisible': False,
        'acc_val': 'fy',
        'value': 'balance',
        'help': lambda s, c, u, cx: cx.get('ifrs_help', True),
        'operator': 'without',
        'comparison': 'without',
        'sequence': _get_default_sequence,
        'priority': _get_default_sequence,
    }

    _sql_constraints = [('sequence_ifrs_id_unique', 'unique(sequence,id)',
                         ('The sequence already have been set in another IFRS \
                          line'))]
