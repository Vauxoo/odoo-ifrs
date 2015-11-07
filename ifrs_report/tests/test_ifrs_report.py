# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase


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

        self.assertEquals(
            res[0]['amount'], 0,
            '{name} should be {amount}!!!'.format(
                 name=res[0]['name'], amount=res[0]['amount']))
        self.assertEquals(
            res[1]['amount'], 6810.0,
            '{name} should be {amount}!!!'.format(
                 name=res[1]['name'], amount=res[1]['amount']))
        self.assertEquals(
            res[2]['amount'], -1950.0,
            '{name} should be {amount}!!!'.format(
                 name=res[2]['name'], amount=res[2]['amount']))
        self.assertEquals(
            res[3]['amount'], 1950.0,
            '{name} should be {amount}!!!'.format(
                 name=res[3]['name'], amount=res[3]['amount']))
        self.assertEquals(
            res[4]['amount'], 8760.0,
            '{name} should be {amount}!!!'.format(
                 name=res[4]['name'], amount=res[4]['amount']))
        return True
