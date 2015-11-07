# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase
# import openerp


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

        # NOTE: This is not working from UnitTest
        # openerp.report.render_report(
        #     self.cr, self.uid, [wzd_brw.id], datas['report_name'],
        #     datas['data'], context=datas['context'])

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
        return True

    def test_twelve_column_report(self):
        wzd_brw = self.create_ifrs_wizard()
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
