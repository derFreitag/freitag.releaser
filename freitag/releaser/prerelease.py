# -*- coding: utf-8 -*-
from zest.releaser.utils import ask

import logging
import os
import subprocess
import sys


logger = logging.getLogger(__name__)


def check_translations(data):
    """Check that all strings are marked as translatable.

    :param data: information coming from zest.releaser
    :type data: dict
    """
    path = '{0}/bin/i18ndude'.format(data['workingdir'])
    if not os.path.exists(path):
        msg = '{0} not found, no translation check will be done'
        logger.debug(msg.format(path))
        return

    process = subprocess.Popen(
        ['bin/i18ndude', 'find-untranslated', '-n', 'src/', ],
        stdout=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    if 'ERROR' not in stdout:
        logger.debug('i18ndude: everything up to date')
        return

    logger.info(stdout)
    msg = 'There are strings not marked as translatable, ' \
          'do you want to continue?'
    if not ask(msg, default=False):
        sys.exit(1)
