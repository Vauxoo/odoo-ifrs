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

    def create_ifrs_wizard(self, values=None):
        values = dict(values or {})
        default = dict()
        default.update(values)
        return self.wzd_obj.create(default)

    def test_basic_report(self):
        self.create_ifrs_wizard()
        return True
