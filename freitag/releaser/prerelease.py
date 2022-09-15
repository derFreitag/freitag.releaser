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
    path = f'{data["workingdir"]}/bin/i18ndude'
    if not os.path.exists(path):
        logger.debug(f'{path} not found, no translation check will be done')
        return

    process = subprocess.Popen(
        ['bin/i18ndude', 'find-untranslated', '-n', 'src/'],
        stdout=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if b'ERROR' not in stdout:
        logger.debug('i18ndude: everything up to date')
        return

    logger.info(stdout)
    msg = 'There are strings not marked as translatable, do you want to continue?'
    if not ask(msg, default=False):
        sys.exit(1)
