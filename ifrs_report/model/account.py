# -*- coding: utf-8 -*-

import datetime
import time
from openerp.osv import osv
from openerp.tools.translate import _


class AccountPeriod(osv.osv):
    _inherit = 'account.period'

    def _get_period_days(self, cr, uid, init_period, last_period,
                         context=None):
        context = context and dict(context) or {}
        # TODO: ERASE LINE BEFORE GO-LIVE
#        last_period = init_period = 2
        date_start = self.browse(
            cr, uid, init_period, context=context).date_start
        date_stop = self.browse(
            cr, uid, last_period, context=context).date_stop

        date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d')
        date_stop = datetime.datetime.strptime(date_stop, '%Y-%m-%d')
        return (date_stop - date_start).days + 1

    def previous(self, cr, uid, ids, step=1, context=None):
        context = context and dict(context) or {}
        period = self.pool.get('account.period').browse(
            cr, uid, ids, context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        # TODO: Take into account previous fiscalyear or just the fiscalyear
        # of the period
        ids = self.search(cr, uid, [('date_stop', '<=', period.date_start),
                                    ('special', '=', False),
                                    ('company_id', '=', user.company_id.id)])
        if len(ids) >= step:
            return ids[-step]

    def find_special_period(self, cr, uid, fy_id, context=None):
        context = dict(context or {})
        fy_obj = self.pool.get('account.fiscalyear')
        res = self.search(
            cr, uid, [('fiscalyear_id', '=', fy_id), ('special', '=', True)],
            context=context)
        if res:
            return res[0]
        fy_brw = fy_obj.browse(cr, uid, fy_id, context=context)
        raise osv.except_osv(
            _('Error !'),
            _('There are no special period in %s') % (fy_brw.name,))


class AccountFiscalyear(osv.osv):
    _inherit = "account.fiscalyear"

    def _get_fy_period_ids(self, cr, uid, ids, special=False, context=None):
        context = context and dict(context) or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = \
            self.pool.get('account.period').search(
                cr, uid, [special and ('fiscalyear_id', 'in', ids) or
                          ('fiscalyear_id', 'in', ids),
                          ('special', '=', special)], context=context)
        return res

    def _get_fy_periods(self, cr, uid, ids, special=False, context=None):
        context = context and dict(context) or {}
        return len(self._get_fy_period_ids(cr, uid, ids, special=special,
                                           context=context))

    def _get_fy_month(self, cr, uid, ids, period_id, special=False,
                      context=None):
        context = context and dict(context) or {}
        ap_obj = self.pool.get('account.period')
        ap_brw = ap_obj.browse(cr, uid, period_id, context=context)
        start_date = ap_brw.date_start
        return time.strptime(start_date, '%Y-%m-%d').tm_mon


class AccountMoveLine(osv.osv):
    _inherit = "account.move.line"

    def _query_get(self, cr, uid, obj='l', context=None):
        query = super(AccountMoveLine, self)._query_get(
            cr, uid, obj=obj, context=context)
        if context.get('analytic', False):
            list_analytic_ids = context.get('analytic')
            ids2 = self.pool.get('account.analytic.account').search(
                cr, uid, [('parent_id', 'child_of', list_analytic_ids)],
                context=context)
            query += 'AND ' + obj + '.analytic_account_id in (%s)' % (
                ','.join([str(idx) for idx in ids2]))

        if context.get('ifrs_partner', False):
            partner_ids = context.get('ifrs_partner')
            query += 'AND l.partner_id in (%s)' % (
                ','.join([str(idx) for idx in partner_ids]))

        if context.get('ifrs_tax', False):
            tax_ids = context.get('ifrs_tax')
            query += 'AND l.tax_code_id in (%s)' % (
                ','.join([str(idx) for idx in tax_ids]))

        # NOTE: This feature is not yet been implemented
        # if context.get('partner_detail', False):
        #     query += 'AND l.partner_id in (%s)' % (
        #         context.get('partner_detail'))
        return query
