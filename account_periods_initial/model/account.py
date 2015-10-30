# -*- encoding: utf-8 -*-

from openerp.osv import osv


class AccountPeriod(osv.Model):
    _inherit = "account.period"

    def build_ctx_periods_initial(self, cr, uid, period_to_id):
        period_to = self.browse(cr, uid, period_to_id)
        period_date_start = period_to.date_start
        company_id = period_to.company_id.id
        fiscalyear_id = period_to.fiscalyear_id.id
        return self.search(cr, uid, [('date_stop', '<=', period_date_start),
                                     ('company_id', '=', company_id),
                                     ('id', '<>', period_to_id),
                                     ('fiscalyear_id', '=', fiscalyear_id)])
        # Falta validar cuando el period_to_id es special, ya que puede tomar
        # enero cuando no es necesario.
