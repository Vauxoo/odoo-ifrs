# -*- coding: utf-8 -*-

import logging


_logger = logging.getLogger(__name__)


def post_init_hook(cr_default, registry):
    """Recompute parenthood on account.account"""
    with registry.cursor() as cr:
        _logger.info('Recomputing Parenthood on account.account')
        registry['account.account']._parent_store_compute(cr)
