# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from . import models
from . import services
from . import graphql
from . import wizards
from .hooks import post_init_hook, uninstall_hook

# logger = logging.getLogger(__name__)

# def post_init_hook(env):
#     logger.info("MONEI post_init_hook")
#     pass


# def uninstall_hook(env):
#     logger.info("MONEI uninstall_hook")
#     pass