"""
utilities
"""
import subprocess
from typing import List


ENCODING = 'utf-8'


def pass_exc(e):
    if e:
        pass


def get_cmd_output(*args, **kwargs) -> str:
    """
    get output of cmd
    :return:
    """
    output = subprocess.check_output(*args, **kwargs)
    return output.decode(ENCODING).replace('\r', '').strip()


def get_cmd_output_lines(*args, **kwargs) -> List[str]:
    """
    get output lines of cmd
    :param args:
    :param kwargs:
    :return:
    """
    output = get_cmd_output(*args, **kwargs)
    return output.split('\n')
