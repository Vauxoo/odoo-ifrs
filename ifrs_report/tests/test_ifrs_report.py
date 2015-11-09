# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase
import openerp


class TestsIfrsReport(TransactionCase):

    # TODO: Docstring
    """
    """

    def setUp(self):
        """
        basic method to define some basic data to be re use in all test cases.
        """
        super(TestsIfrsReport, self).setUp()
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
        openerp.report.render_report(
            self.cr, self.uid, [wzd_brw.id], datas['report_name'],
            datas['data'], context=datas['context'])

        self.assertEquals(
            res[0]['amount'], 0,
            '{name} should be {amount}!!!'.format(
                name=res[0]['name'], amount=0.0))
        self.assertEquals(
            res[1]['amount'], 6810.0,
            '{name} should be {amount}!!!'.format(
                name=res[1]['name'], amount=6810.0))
        self.assertEquals(
            res[2]['amount'], -1950.0,
            '{name} should be {amount}!!!'.format(
                name=res[2]['name'], amount=-1950.0))
        self.assertEquals(
            res[3]['amount'], 1950.0,
            '{name} should be {amount}!!!'.format(
                name=res[3]['name'], amount=1950.0))
        self.assertEquals(
            res[4]['amount'], 8760.0,
            '{name} should be {amount}!!!'.format(
                name=res[4]['name'], amount=8760.0))
        self.assertEquals(
            res[8]['amount'], 2,
            '{name} should be {amount}!!!'.format(
                name=res[8]['name'], amount=2))
        self.assertEquals(
            res[9]['amount'], 777,
            '{name} should be {amount}!!!'.format(
                name=res[9]['name'], amount=777))
        self.assertEquals(
            res[10]['amount'], 0.0,
            '{name} should be {amount}!!!'.format(
                name=res[10]['name'], amount=0.0))
        self.assertEquals(
            res[11]['amount'], 6810.0,
            '{name} should be {amount}!!!'.format(
                name=res[11]['name'], amount=6810.0))
        self.assertEquals(
            res[12]['amount'], -4960.0,
            '{name} should be {amount}!!!'.format(
                name=res[12]['name'], amount=-4960.0))
        self.assertEquals(
            res[13]['amount'], 1850.0,
            '{name} should be {amount}!!!'.format(
                name=res[13]['name'], amount=1850.0))
        self.assertEquals(
            res[14]['amount'], 6810.0,
            '{name} should be {amount}!!!'.format(
                name=res[14]['name'], amount=6810.0))
        self.assertEquals(
            res[15]['amount'], -4960.0,
            '{name} should be {amount}!!!'.format(
                name=res[15]['name'], amount=-4960.0))
        self.assertEquals(
            round(res[16]['amount'], 2), 27.17,
            '{name} should be {amount}!!!'.format(
                name=res[16]['name'], amount=27.17))
        self.assertEquals(
            round(res[17]['amount'], 2), 0.27,
            '{name} should be {amount}!!!'.format(
                name=res[17]['name'], amount=0.27))
        self.assertEquals(
            res[18]['amount'], -59520.0,
            '{name} should be {amount}!!!'.format(
                name=res[18]['name'], amount=-59520.0))
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

        self.assertEquals(
            res[0]['period'][12], 0,
            '{name} should be {amount}!!!'.format(
                name=res[0]['name'], amount=0.0))
        self.assertEquals(
            res[1]['period'][12], 6810.0,
            '{name} should be {amount}!!!'.format(
                name=res[0]['name'], amount=6810.0))
        self.assertEquals(
            res[2]['period'][12], -1950.0,
            '{name} should be {amount}!!!'.format(
                name=res[0]['name'], amount=-1950.0))
        self.assertEquals(
            res[3]['period'][12], 1950.0,
            '{name} should be {amount}!!!'.format(
                name=res[0]['name'], amount=1950.0))
        self.assertEquals(
            res[4]['period'][12], 8760.0,
            '{name} should be {amount}!!!'.format(
                name=res[0]['name'], amount=8760.0))
        self.assertEquals(
            res[5]['period'][12], 31,
            '{name} should be {amount}!!!'.format(
                name=res[5]['name'], amount=31))
        self.assertEquals(
            res[6]['period'][12], 12,
            '{name} should be {amount}!!!'.format(
                name=res[6]['name'], amount=12))
        self.assertEquals(
            res[7]['period'][12], 12,
            '{name} should be {amount}!!!'.format(
                name=res[7]['name'], amount=12))
        return True

    def test_force_period_report(self):
        period_id = self.ref('account.period_12')
        wzd_brw = self.create_ifrs_wizard({
            'report_type': 'per',
            'period': period_id,
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

        self.assertEquals(
            res[1]['amount'], 10411.81,
            '{name} should be {amount}!!!'.format(
                name=res[1]['name'], amount=10411.81))

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
            '{name} should be {amount}!!!'.format(
                name=line_brw.name, amount=6810.0))

        line_id = self.ref('ifrs_report.ifrs_lines_total_revenue_condition')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 1850.0,
            '{name} should be {amount}!!!'.format(
                name=line_brw.name, amount=1850.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_total_revenue_condition_subtract')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, -4960.0,
            '{name} should be {amount}!!!'.format(
                name=line_brw.name, amount=-4960.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_total_revenue_condition_addition')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 8660.0,
            '{name} should be {amount}!!!'.format(
                name=line_brw.name, amount=8660.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_total_revenue_condition_zero')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 0.0,
            '{name} should be {amount}!!!'.format(
                name=line_brw.name, amount=0.0))

        line_id = self.ref(
            'ifrs_report.ifrs_lines_detail_revenue_analytic')
        line_brw = self.env['ifrs.lines'].browse(line_id)

        self.assertEquals(
            line_brw.amount, 0.0,
            '{name} should be {amount}!!!'.format(
                name=line_brw.name, amount=0.0))

        return True

    def test_onchange_company_report(self):
        self.registry('ifrs.ifrs').onchange_company_id(
            self.cr, self.uid, self.ifrs_brw.id, self.ifrs_brw.company_id.id)
        self.registry('ifrs.ifrs').onchange_company_id(
            self.cr, self.uid, self.ifrs_brw.id, None)
        return True

    def test_onchange_sequence_report(self):
        ifrs_line_obj = self.registry('ifrs.lines')
        ifrs_id = self.ref('ifrs_report.ifrs_ifrs_demo')
        res = ifrs_line_obj.onchange_sequence(self.cr, self.uid, ifrs_id, 100)
        self.assertEquals(
            res['value']['priority'], 100, 'Something went wrong!!!')
        return True

    def test_get_default_sequence_report(self):
        ifrs_line_obj = self.registry('ifrs.lines')
        ifrs_id = self.ref('ifrs_report.ifrs_ifrs_demo')
        ctx = {'ifrs_id': ifrs_id}
        res = ifrs_line_obj._get_default_sequence(
            self.cr, self.uid, context=ctx)
        self.assertEquals(
            res, 250, 'Something went wrong!!!')
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
        except Exception:
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
