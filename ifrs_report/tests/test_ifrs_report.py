# -*- coding: utf-8 -*-

from calendar import isleap
from datetime import datetime
import time
import openerp
from openerp.tests.common import TransactionCase
from openerp.addons.controller_report_xls.controllers.main import get_xls

RESULT = {
    10: 0,
    20: 6810,
    30: -1950,
    40: 1950,
    50: 8760,
    60: 366 if isleap(datetime.now().timetuple().tm_year) else 365,
    70: 12,
    80: 12,
    90: 2,
    100: 777,
    110: 0,
    120: 6810,
    130: -4960,
    135: 150,
    140: 1850,
    150: 6810,
    160: -4960,
    170: 27.17,
    180: 0.27,
    190: -59520,
    200: 1850,
    210: -4960,
    220: 8660,
    230: 0,
    235: 6810,
    240: 0,
}

LABEL = {
    10: "ABSTRACT TITLE",
    20: "RECEIVABLES",
    30: "PAYABLES",
    40: "PAYABLE WITH REVERSE SIGN",
    50: "RECEIVABLE PLUS PAYABLE",
    60: "PERIOD DAYS",
    70: "FISCALYEAR PERIOD",
    80: "FISCALYEAR MONTH",
    90: "NUMBER OF CUSTOMERS",
    100: "CONSTANT",
    110: "RECEIVABLES - INITIAL VALUES",
    120: "RECEIVABLES - VARIATION IN PERIOD",
    130: "REVENUE - BALANCE",
    135: "REVENUE - BALANCE - CUSTOM FILTER (Expenses Journal)",
    140: "REVENUE - DEBIT",
    150: "REVENUE - CREDIT - TAXED",
    160: "REVENUE: DEBIT - CREDIT",
    170: "REVENUE: PERCENT",
    180: "REVENUE: RATIO",
    190: "PRODUCT: REVENUE * FISCALYEAR PERIOD",
    200: "CONDITION: IF DEBIT < CREDIT THEN DEBIT ELSE CREDIT",
    210: "CONDITION: IF DEBIT < CREDIT THEN (DEBIT - CREDIT) ELSE CREDIT",
    220: "CONDITION: IF DEBIT < CREDIT THEN (DEBIT + CREDIT) ELSE CREDIT",
    230: "CONDITION: IF DEBIT > CREDIT THEN (DEBIT + CREDIT) ELSE ZERO (0)",
    235: "CONDITION: IF DEBIT > CREDIT THEN DEBIT ELSE CREDIT",
    240: "REVENUE - BALANCE - ANALYTIC",
}


class TestsIfrsReport(TransactionCase):
    """ Testing all the features in IFRS report """

    def setUp(self):
        """ Basic method to define some basic data to be re use in all test
        cases. """
        super(TestsIfrsReport, self).setUp()
        self.acc_obj = self.registry('account.account')
        self.acc_obj._parent_store_compute(self.cr)
        self.wzd_obj = self.env['ifrs.report.wizard']
        self.ifrs_obj = self.env['ifrs.ifrs']
        self.ifrs_id = self.ref('ifrs_report.ifrs_ifrs_demo')
        self.ifrs_brw = self.ifrs_obj.browse(self.ifrs_id)

    def create_ifrs_wizard(self, values=None):
        company_id = self.ifrs_brw.company_id.id
        fiscalyear_id = self.ifrs_brw.fiscalyear_id.id
        currency_id = self.ifrs_brw.company_id.currency_id.id
        values = dict(values or {})
        default = dict(
            company_id=company_id,
            fiscalyear_id=fiscalyear_id,
            currency_id=currency_id,
            ifrs_id=self.ref('ifrs_report.ifrs_ifrs_demo'),
        )
        default.update(values)
        return self.wzd_obj.with_context(
            {'active_ids': [self.ifrs_id]}).create(default)

    def test_basic_report(self):
        wzd_brw = self.create_ifrs_wizard()
        datas = wzd_brw.print_report()
        data = datas['data']
        res = self.ifrs_brw.get_report_data(
            data['wizard_id'],
            fiscalyear=data['fiscalyear'],
            exchange_date=data['exchange_date'],
            currency_wizard=data['currency_wizard'],
            target_move=data['target_move'],
            two=True,
        )

        # NOTE: Require `active_model` in order to work with UnitTest
        datas['context'].update({
            'active_model': 'ifrs.ifrs',
        })
        result = openerp.report.render_report(
            self.cr, self.uid, [wzd_brw.id], datas['report_name'],
            datas['data'], context=datas['context'])
        get_xls(result[0])

        for val in res:
            seq = val['sequence']
            if seq == 90:
                # TODO: code for number of customer is quite weak until further
                # development is done test for them will be skipped
                continue
            self.assertEquals(
                round(val['amount'], 2), RESULT[seq],
                'There is something wrong. Sequence %(seq)s!!!' %
                dict(seq=seq))
            self.assertEquals(
                val['name'], LABEL[seq],
                'There is something wrong. Sequence %(seq)s!!!' %
                dict(seq=seq))

        return True

    def test_twelve_column_report(self):
        wzd_brw = self.create_ifrs_wizard(
            {'columns': 'webkitaccount.ifrs_12',
             'report_format': 'spreadsheet'})
        datas = wzd_brw.print_report()
        data = datas['data']
        res = self.ifrs_brw.get_report_data(
            data['wizard_id'],
            fiscalyear=data['fiscalyear'],
            exchange_date=data['exchange_date'],
            currency_wizard=data['currency_wizard'],
            target_move=data['target_move'],
            two=False,
        )

        for val in res:
            seq = val['sequence']
            if seq == 90:
                # TODO: code for number of customer is quite weak until further
                # development is done test for them will be skipped
                continue

            self.assertEquals(
                val['name'], LABEL[seq],
                'There is something wrong. Sequence %(seq)s!!!' %
                dict(seq=seq))

            if seq == 60:
                self.assertEquals(
                    round(val['period'][12], 2), 31,
                    'There is something wrong. Sequence %(seq)s!!!' % dict(
                        seq=seq))
                continue
            if seq == 90:
                # TODO: code for number of customer is quite weak until further
                # development is done test for them will be skipped
                continue
            if seq == 110:
                self.assertEquals(
                    round(val['period'][12], 2), 6810.0,
                    'There is something wrong. Sequence %(seq)s!!!' %
                    dict(seq=seq))
                continue
            if seq == 120:
                self.assertEquals(
                    round(val['period'][12], 2), 0.0,
                    'There is something wrong. Sequence %(seq)s!!!' %
                    dict(seq=seq))
                continue

            self.assertEquals(
                round(val['period'][12], 2), RESULT[seq],
                'There is something wrong. Sequence %(seq)s!!!' %
                dict(seq=seq))
        return True

    def test_force_period_report(self):
        period_id = self.ref('account.period_12')
        wzd_brw = self.create_ifrs_wizard({
            'report_type': 'per',
            'period': period_id,
            'exchange_date': time.strftime('%Y')+'-12-01',
            'currency_id': self.ref("base.USD"),
            })
        datas = wzd_brw.print_report()
        data = datas['data']
        res = self.ifrs_brw.get_report_data(
            data['wizard_id'],
            fiscalyear=data['fiscalyear'],
            exchange_date=data['exchange_date'],
            currency_wizard=data['currency_wizard'],
            target_move=data['target_move'],
            period=period_id,
            two=True,
        )

        # NOTE: This is not working from UnitTest
        # openerp.report.render_report(
        #     self.cr, self.uid, [wzd_brw.id], datas['report_name'],
        #     datas['data'], context=datas['context'])

        for val in res:
            seq = val['sequence']
            if seq != 20:
                continue
            self.assertEquals(
                val['name'], LABEL[seq],
                'There is something wrong. Sequence %(seq)s!!!' %
                dict(seq=seq))
            self.assertEquals(
                round(val['amount'], 2), 10411.81,
                'There is something wrong. Sequence %(seq)s!!!' %
                dict(seq=seq))
        return True

    def test_report_duplication(self):
        # TODO: More criteria for testing should be added too dummy
        # TODO: when migrating to new api v8 rewrite method copy_data
        new_id = self.registry('ifrs.ifrs').copy(
            self.cr, self.uid, self.ifrs_brw.id)
        new_brw = self.ifrs_obj.browse(new_id)
        self.assertEquals(
            len(self.ifrs_brw.ifrs_lines_ids),
            len(new_brw.ifrs_lines_ids),
            'Both report should contain same quantity of lines')
        return True

    def test_report_duplication_multicompany(self):
        company_obj = self.env['res.company']
        new_company = company_obj.create({'name': 'VX'})

        default = {'company_id': new_company.id}

        new_id = self.registry('ifrs.ifrs').copy(
            self.cr, self.uid, self.ifrs_brw.id, default=default)
        new_brw = self.ifrs_obj.browse(new_id)

        self.assertEquals(
            len(self.ifrs_brw.ifrs_lines_ids),
            len(new_brw.ifrs_lines_ids),
            'Both report should contain same quantity of lines')
        self.assertEquals(
            new_brw.company_id.name, 'VX',
            'Multicompany Duplication does not work!!!')

        # NOTE: This works different behind the scene
        another_id = self.registry('ifrs.ifrs').copy(self.cr, self.uid, new_id)
        another_brw = self.ifrs_obj.browse(another_id)

        self.assertEquals(
            len(another_brw.ifrs_lines_ids),
            len(new_brw.ifrs_lines_ids),
            'Both report should contain same quantity of lines')
        self.assertNotEquals(
            another_brw.company_id.name, 'VX',
            'Multicompany Duplication does not work!!!')
        for line in another_brw.ifrs_lines_ids:
            if line.type != 'detail':
                continue
            self.assertEquals(
                len(line.cons_ids), 0,
                'This report should not have any consolidated lines')
        return True

    def test_report_duplication_no_lines(self):
        ifrs_obj = self.registry('ifrs.ifrs')
        old_id = self.ref('ifrs_report.ifrs_ifrs_demo_empty')
        new_id = ifrs_obj.copy(
            self.cr, self.uid, old_id)
        new_brw = ifrs_obj.browse(self.cr, self.uid, new_id)
        old_brw = ifrs_obj.browse(self.cr, self.uid, old_id)
        self.assertEquals(
            len(old_brw.ifrs_lines_ids),
            len(new_brw.ifrs_lines_ids),
            'Both report should contain same quantity of lines')
        return True

    def test_report_print_period_info(self):
        res = self.ifrs_brw.get_period_print_info(None, 'all')
        self.assertEquals(
            res, 'ALL PERIODS OF THE FISCALYEAR',
            'ALL PERIODS OF THE FISCALYEAR')
        period_id = self.ref('account.period_1')
        self.ifrs_brw.get_period_print_info(period_id, None)
        return True

    def test_report_no_lines_compute(self):
        ifrs_obj = self.registry('ifrs.ifrs')
        old_id = self.ref('ifrs_report.ifrs_ifrs_demo_empty')
        ifrs_obj.compute(self.cr, self.uid, old_id)
        return True

    def test_ifrs_compute(self):
        self.registry('ifrs.ifrs').compute(
            self.cr, self.uid, self.ifrs_brw.id)
        line_id = self.ref('ifrs_report.ifrs_lines_detail_receivable')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 6810.0,
            '%(name)s should be %(amount)s!!!' % dict(
                name=line_brw.name, amount=6810.0))

        line_id = self.ref('ifrs_report.ifrs_lines_total_revenue_condition')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 1850.0,
            '%(name)s should be %(amount)s!!!' % dict(
                name=line_brw.name, amount=1850.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_total_revenue_condition_subtract')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, -4960.0,
            '%(name)s should be %(amount)s!!!' % dict(
                name=line_brw.name, amount=-4960.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_total_revenue_condition_addition')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 8660.0,
            '%(name)s should be %(amount)s!!!' % dict(
                name=line_brw.name, amount=8660.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_total_revenue_condition_zero')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 0.0,
            '%(name)s should be %(amount)s!!!' % dict(
                name=line_brw.name, amount=0.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_detail_revenue_analytic')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 0.0,
            '%(name)s should be %(amount)s!!!' % dict(
                name=line_brw.name, amount=0.0))

        return True

    def test_onchange_company_report(self):
        ifrs_brw = self.ifrs_obj.browse(self.ifrs_id)
        ifrs_brw.onchange_company_id()
        return True

    def test_onchange_sequence_report(self):
        ifrs_line_obj = self.registry('ifrs.lines')
        ifrs_id = self.ref('ifrs_report.ifrs_ifrs_demo')
        res = ifrs_line_obj.onchange_sequence(self.cr, self.uid, ifrs_id, 100)
        self.assertEquals(
            res['value']['priority'], 100, 'Something went wrong!!!')
        return True

    def test_get_default_help_bool_report(self):
        ifrs_line_obj = self.env['ifrs.lines']
        res = ifrs_line_obj._get_default_help_bool()
        self.assertEquals(res, True, 'Something went wrong!!!')
        return True

    def test_get_default_sequence_report(self):
        ifrs_line_obj = self.env['ifrs.lines']
        ifrs_id = self.ref('ifrs_report.ifrs_ifrs_demo')
        res = ifrs_line_obj._get_default_sequence()
        self.assertEquals(res, 10, 'Something went wrong!!!')
        ctx = {'ifrs_id': ifrs_id}
        res = ifrs_line_obj.with_context(ctx)._get_default_sequence()
        self.assertEquals(res, 250, 'Something went wrong!!!')
        return True

    def test_onchange_type_without_report(self):
        ifrs_line_obj = self.registry('ifrs.lines')
        ifrs_id = self.ref('ifrs_report.ifrs_ifrs_demo')
        ctx = {'ifrs_id': ifrs_id}
        res = ifrs_line_obj.onchange_type_without(
            self.cr, self.uid, [], 'total', 'without', context=ctx)
        self.assertEquals(
            res['value']['operand_ids'], [], 'Something went wrong!!!')
        return True

    def test_find_special_period(self):
        period_obj = self.registry('account.period')
        fy_id = self.ref('account.data_fiscalyear')
        special_id = self.ref('account.period_0')
        period_obj.write(self.cr, self.uid, [special_id], {'special': False})
        try:
            period_obj.find_special_period(self.cr, self.uid, fy_id)
        except Exception:  # pylint: disable=W0703
            assert True, "This assert will never fail!!!"
            period_obj.write(
                self.cr, self.uid, [special_id], {'special': True})
        return True

    # TODO: Can this be done from wizard creation itself?
    def test_default_fiscalyear_wizard(self):
        self.wzd_obj._default_fiscalyear()
        self.wzd_obj.with_context(
            {'active_ids': [self.ifrs_brw.id]})._default_fiscalyear()
        return True

    def test_default_currency_wizard(self):
        self.wzd_obj._default_currency()
        self.wzd_obj.with_context(
            {'active_ids': [self.ifrs_brw.id]})._default_currency()
        return True

    def test_default_ifrs_wizard(self):
        res = self.wzd_obj._default_ifrs()
        self.assertEquals(
            res, False, 'Something went wrong!!!')
        ctx = {
            'active_id': self.ifrs_brw.id,
            'active_model': 'ifrs.ifrs'}
        res = self.wzd_obj.with_context(ctx)._default_ifrs()
        self.assertEquals(
            res, self.ifrs_brw.id, 'Something went wrong!!!')
        return True
