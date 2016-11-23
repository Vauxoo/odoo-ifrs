# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class IfrsIfrs(models.Model):

    _name = 'ifrs.ifrs'
    _rec_name = 'code'

    @api.multi
    def _default_fiscalyear(self):
        af_obj = self.env['account.fiscalyear']
        return af_obj.find(exception=False)

    @api.onchange('company_id')
    def onchange_company_id(self):
        af_obj = self.env['account.fiscalyear']
        self.fiscalyear_id = af_obj.find(exception=False)
        self.currency_id = self.company_id.currency_id.id

    name = fields.Char(
        string='Name', size=128, required=True, help='Report name')
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=False,
        required=False, readonly=True, states={},
        default=lambda self: self.env['res.company']._company_default_get(
            'ifrs.ifrs'), help='Company name')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        required=False, readonly=True, states={},
        related='company_id.currency_id',
        help=('Currency at which this report will be expressed. If not '
              'selected will be used the one set in the company'))
    title = fields.Char(
        string='Title', size=128, required=True, translate=True,
        help='Report title that will be printed')
    code = fields.Char(
        string='Code', size=128, required=True,
        help='Report code')
    description = fields.Text(string='Description')
    ifrs_lines_ids = fields.One2many(
        'ifrs.lines', 'ifrs_id', string='IFRS lines',
        readonly=False, states={'draft': [('readonly', False)]}, copy=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('ready', 'Ready'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        string='State', required=True, default='draft')
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear', string='Fiscal Year',
        default=_default_fiscalyear,
        help=('Fiscal Year to be used in report'))
    help = fields.Boolean(
        string='Show Help', default=True, copy=False,
        help='Allows you to show the help in the form')
    ifrs_ids = fields.Many2many(
        'ifrs.ifrs', 'ifrs_m2m_rel', 'parent_id', 'child_id',
        string='Other Reportes')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = u"[%s] %s" % (record.code, record.name)
            res.append((record.id, name))
        return res

    @api.multi
    def _get_ordered_lines(self):
        """ Return list of browse ifrs_lines per level in order ASC, for can
        calculate in order of priorities.

        Retorna la lista de ifrs.lines del ifrs_id organizados desde el nivel
        mas bajo hasta el mas alto. Lo niveles mas bajos se deben calcular
        primero, por eso se posicionan en primer lugar de la lista.
        """
        self.ensure_one()
        context = dict(self._context or {})
        il_obj = self.pool.get('ifrs.lines')
        tree = {1: {}}
        for lll in self.ifrs_lines_ids:
            il_obj._get_level(
                self._cr, self._uid, lll, tree, 1, context=context)
        levels = tree.keys()
        levels.sort()
        levels.reverse()
        ids_x = []  # List of ids per level in order ASC
        for i in levels:
            ids_x += tree[i].keys()
        return ids_x

    @api.multi
    def compute(self):
        """ Se encarga de calcular los montos para visualizarlos desde
        el formulario del ifrs, hace una llamada al get_report_data, el
        cual se encarga de realizar los calculos.
        """
        context = dict(self._context or {})
        fy = self.env['account.fiscalyear'].find(exception=False)
        context.update({'whole_fy': True, 'fiscalyear': fy})
        for record in self.with_context(context).get_report_data(
                None, target_move='posted', two=True):
            if record['type'] == 'abstract':
                continue
            self.env['ifrs.lines'].browse(record['id']).write(
                {'amount': record['amount']})
        return True

    @api.multi
    def _get_periods_name_list(self, fiscalyear_id):
        """ Devuelve una lista con la info de los periodos fiscales
        (numero mes, id periodo, nombre periodo)
        @param fiscalyear_id: Año fiscal escogido desde el wizard encargada
        de preparar el reporte para imprimir
        """
        context = dict(self._context or {})
        af_obj = self.env['account.fiscalyear']
        periods = self.env['account.period']

        period_list = [('0', None, ' ')]

        fiscalyear_bwr = af_obj.browse(fiscalyear_id).with_context(context)
        periods_ids = fiscalyear_bwr._get_fy_period_ids()

        for ii, period_id in enumerate(periods_ids, start=1):
            period_list.append(
                (str(ii), period_id,
                 periods.browse(period_id).name))
        return period_list

    @api.multi
    def get_period_print_info(self, period_id, report_type):
        """ Return all the printable information about period
        @param period_id: Dependiendo del report_type, en el caso que sea
        'per', este campo indica el periodo a tomar en cuenta, en caso de que
        el report_type sea 'all', es Falso.
        @param report_type: Su valor se establece desde el wizard que se
        encarga de preparar al reporte para imprimir, el report_type puede ser
        'all' (incluir todo el año fiscal en el reporte) o 'per' (tomar en
        cuenta solo un periodo determinado en el reporte)
        """
        if report_type == 'all':
            res = _('ALL PERIODS OF THE FISCALYEAR')
        else:
            period = self.env['account.period'].browse(period_id)
            res = '%(name)s [%(code)s]' % dict(
                name=period.name, code=period.code)
        return res

    def step_sibling(self, cr, uid, old_id, new_id, context=None):
        """ Sometimes total_ids and operand_ids include lines from their own
        ifrs_id report, They are siblings. In this case m2m copy_data just make
        a link from the old report. In the new report we have to substitute the
        cousins that are pretending to be siblings with the siblings This can
        be achieved due to the fact that each line has unique sequence within
        each report, using the analogy about relatives then each pretending
        cousin is of same age than that of the actual sibling cousins with
        common parent are siblings among them """
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
        res = super(IfrsIfrs, self).copy_data(cr, uid, ids, default, context)
        if res.get('ifrs_lines_ids', False) and \
                context.get('clear_cons_ids', False):
            for lll in res['ifrs_lines_ids']:
                lll[2]['cons_ids'] = lll[2]['type'] == 'detail' and \
                    lll[2]['cons_ids'] and [] or []
        return res

    # pylint: disable=W8102
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
        res = super(IfrsIfrs, self).copy(cr, uid, ids, default, context)
        self.step_sibling(cr, uid, ids, res, context=context)
        return res

    @api.multi
    def get_report_data(
            self, wizard_id, fiscalyear=None, exchange_date=None,
            currency_wizard=None, target_move=None, period=None, two=None):
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
        self.ensure_one()
        ctx = dict(self._context or {})
        data = []
        ifrs_line = self.env['ifrs.lines']
        period_name = self.with_context(ctx)._get_periods_name_list(fiscalyear)

        ordered_lines = self.with_context(ctx)._get_ordered_lines()
        bag = {}.fromkeys(ordered_lines, None)

        # TODO: THIS Conditional shall reduced
        one_per = period is not None

        for il_id in ordered_lines:
            ifrs_l = ifrs_line.browse(il_id)
            bag[ifrs_l.id] = {}

            line = {
                'sequence': int(ifrs_l.sequence),
                'id': ifrs_l.id,
                'name': ifrs_l.name,
                'invisible': ifrs_l.invisible,
                'type': str(ifrs_l.type),
                'comparison': ifrs_l.comparison,
                'operator': ifrs_l.operator}

            if two:
                line['amount'] = ifrs_l._get_amount_with_operands(
                    ifrs_l, period_name, fiscalyear,
                    exchange_date, currency_wizard, period, target_move,
                    two=two, one_per=one_per, bag=bag, context=ctx)
            else:
                line['period'] = ifrs_l._get_dict_amount_with_operands(
                    ifrs_l, period_name, fiscalyear,
                    exchange_date, currency_wizard, None, target_move, bag=bag,
                    context=ctx)

            # NOTE:Only lines from current Ifrs report record are taken into
            # account given there are lines included from other reports to
            # compute values
            if ifrs_l.ifrs_id.id == self.id:
                data.append(line)

        data.sort(key=lambda x: int(x['sequence']))
        return data
