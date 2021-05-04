"""
config module
"""
from typing import Optional, List
from pydantic import BaseModel
from logger import LOGGER
import json


class Config(BaseModel):
    """
    config
    """
    adb: str = ''
    serial: str = ''

    def get_adb_cmd(self, **kwargs) -> List[str]:
        cmd = [self.adb]

        # -s
        serial = kwargs.get('serial', '')
        if serial:
            cmd.extend(['-s', str(serial)])
        elif self.serial:
            cmd.extend(['-s', self.serial])

        # other commands to extend
        ext = kwargs.get('ext', [])
        if isinstance(ext, list):
            cmd.extend([str(s) for s in ext])

        return cmd


CFG: Optional[Config] = None


def init():
    LOGGER.info('initialize config...')
    cfg_path = './config.json'
    global CFG
    CFG = Config(**json.loads(open(cfg_path).read()))
    LOGGER.info('initialize config successfully!')
