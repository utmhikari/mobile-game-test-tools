"""
utilities
"""
import subprocess


ENCODING = 'utf-8'


def pass_exc(e):
    if e:
        pass


def get_cmd_output(*args, **kwargs):
    """
    get output of cmd
    :return:
    """
    output = subprocess.check_output(*args, **kwargs)
    return output.decode(ENCODING).replace('\r', '')
