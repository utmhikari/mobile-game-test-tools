"""
file grep
"""
from pydantic import BaseModel
from typing import List, Any, Dict
from logger import LOGGER
import datetime
import util
import config


class UELogLine(BaseModel):
    """
    a single line of ue4 game log
    ue log format:
    [yyyy.mm.dd-HH.MM.SS:fff][no]LogCategory: content
    """
    raw: str = ''
    t: datetime.datetime = datetime.datetime.now()
    no: int = 0
    category: str = ''
    content: str = ''

    def __str__(self):
        return self.content

    def is_valid(self) -> bool:
        return len(self.category) > 0 and len(self.content) > 0

    @classmethod
    def new(cls, line: str):
        o = cls(raw=line)
        try:
            tag_cnt = 0
            lb, rb = -1, -1
            for i in range(len(line)):
                if line[i] == '[':
                    lb = i
                if line[i] == ']':
                    rb = i
                    if tag_cnt == 0:
                        time_str = line[lb + 1:rb].strip()
                        o.t = datetime.datetime.strptime(
                            time_str,
                            '%Y.%m.%d-%H.%M.%S:%f'
                        )
                        tag_cnt += 1
                    else:
                        o.no = int(line[lb + 1:rb].strip())
                        tag_cnt += 1
                if line[i] == ':':
                    if tag_cnt > 0:
                        o.category = line[rb + 1:i]
                        o.content = line[i + 2:]
                        break
        except Exception as e:
            LOGGER.exception('UELogLine exception: %s -> %s' % (e, line))
            util.pass_exc(e)
        return o


class UELogGrep(BaseModel):
    """
    ue log grep instance
    """
    path: str = ''
    lines: List[UELogLine] = []
    group_lines: Dict[str, List[UELogLine]] = {}  # group by ue log category

    def grep_output_lines(self,
                          keyword: str,
                          bridge_args: Dict[str, Any] = None,
                          *args,
                          **kwargs) -> List[str]:
        if not isinstance(bridge_args, dict):
            bridge_args = {}
        ext = ['shell', 'cat', self.path]
        if keyword:
            ext.extend(['|', 'grep', keyword])
        cmd = config.CFG.get_adb_cmd(ext=ext, **bridge_args)
        return util.get_cmd_output_lines(cmd, *args, **kwargs)

    def grep(self, keyword: str = '', *args, **kwargs):
        assert self.path
        output = self.grep_output_lines(keyword, *args, **kwargs)
        cnt = 0
        for line in output:
            try:
                o = UELogLine.new(line)
                if o.is_valid():
                    self.lines.append(o)
                    if o.category not in self.group_lines.keys():
                        self.group_lines[o.category] = []
                    self.group_lines[o.category].append(o)
                cnt += 1
            except Exception as e:
                util.pass_exc(e)
        LOGGER.info('grepped %d lines...' % cnt)

    @staticmethod
    def __dump_lines(lines: List[UELogLine], content_only: bool = True) -> str:
        if content_only:
            dump_lines = [str(line) for line in lines]
        else:
            dump_lines = [line.raw for line in lines]
        return '\n'.join(dump_lines)

    def dump(self, is_group=True, *args, **kwargs) -> str:
        if not is_group:
            return '%s\nOverall %d lines' % (
                UELogGrep.__dump_lines(self.lines, *args, **kwargs),
                len(self.lines)
            )
        lines = []
        for category in sorted(self.group_lines.keys()):
            if len(self.group_lines[category]) != 0:
                lines.extend([
                    'Category: %s' % category,
                    UELogGrep.__dump_lines(self.group_lines[category], *args, **kwargs),
                    'Overall %d lines' % len(self.group_lines[category]),
                    ''
                ])
        return '\n'.join(lines)


if __name__ == '__main__':
    config.init()
    ue_log = UELogGrep(
        path='/sdcard/UE4Game/FounDerBoy/FounDerBoy/Saved/Logs/FounDerBoy.log'
    )
    ue_log.grep(keyword='LogPluginManager')
    print(ue_log.dump())
