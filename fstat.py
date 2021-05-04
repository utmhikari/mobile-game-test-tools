"""
fstat

a script to dump file stats
currently support android (with adb)

1. LSFileStats
list files by adb shell ls -l (-R), with a diff method to dump diffs
useful when testing patch updates
"""
from pydantic import BaseModel
from logger import LOGGER
from enum import IntEnum
from typing import List, Dict, Any
import config
import util
import re


class FileType(IntEnum):
    UNKNOWN = 0
    FILE = 1
    DIRECTORY = 2


class LSFileStat(BaseModel):
    """
    file stat info from cmd: ls
    example android: drwxrwxrwx 4 shell shell 3488 2020-10-18 11:24 .studio
    """
    name: str = ''
    file_type: FileType = FileType.UNKNOWN
    size: int = -1

    def __str__(self):
        return '[%s] name: %s, size: %d' % (self.file_type.name, self.name, self.size)

    def __eq__(self, other):
        if not isinstance(other, LSFileStat) or \
                not other.is_valid() or \
                not self.is_valid():
            return False
        return self.name == other.name and \
            self.file_type == other.file_type and \
            self.size == other.size

    def is_valid(self) -> bool:
        return self.name and self.size >= 0

    @classmethod
    def new_from_line(cls, line: str = ''):
        clean_line = re.sub(r'\s+', ' ', line.strip())
        splits = clean_line.split(' ')
        try:
            if splits[0].startswith('d'):
                file_type = FileType.DIRECTORY
            else:
                file_type = FileType.FILE
            return cls(
                name=splits[-1],
                file_type=file_type,
                size=int(splits[-4])
            )
        except Exception as e:
            util.pass_exc(e)
            # LOGGER.exception('[LSFileStat] failed to parse line %s! %s' % (clean_line, e))
            return cls()


class LSFileStats(BaseModel):
    """
    list of file stats
    """
    root: str = ''
    files: Dict[str, List[LSFileStat]] = []

    @staticmethod
    def __dump_internal(files: List[LSFileStat], **kwargs):
        lines = []
        is_group_by_type = kwargs.get('group_by_type')
        if not is_group_by_type:
            for f in files:
                lines.append(str(f))
        else:
            groups: List[List[str]] = [[], [], []]
            for f in files:
                groups[f.file_type.value].append(str(f))
            for g in groups:
                lines.extend(g)
        return '\n'.join(lines)

    def dump(self, **kwargs) -> str:
        lines = []
        for k in sorted(self.files.keys()):
            lines.append('%s (%d)' % (k, len(self.files[k])))
            lines.append(self.__dump_internal(self.files[k], **kwargs))
            lines.append('')
        return '\n'.join(lines)

    @staticmethod
    def __diff_internal(root: str, src: List[LSFileStat], dst: List[LSFileStat]) -> str:
        removed, added = [], []

        visited_other = set()
        for i in range(len(src)):
            is_removed = True
            for j in range(len(dst)):
                if j in visited_other:
                    continue
                if src[i] == dst[j]:
                    is_removed = False
                    visited_other.add(j)
                    break
            if is_removed:
                removed.append(src[i])
        for j in range(len(dst)):
            if j not in visited_other:
                added.append(dst[j])

        if len(removed) == 0 and len(added) == 0:
            return ''

        diffs = [
            'Root: %s' % root,
        ]
        if len(removed) > 0:
            diffs.extend([
                'Removed Files (%d)' % len(removed),
                LSFileStats.__dump_internal(removed, group_by_type=True),
                ''
            ])
        if len(added) > 0:
            diffs.extend([
                'Added Files (%d)' % len(added),
                LSFileStats.__dump_internal(added, group_by_type=True),
                ''
            ])
        return '\n'.join(diffs)

    def diff(self, other) -> str:
        if not isinstance(other, LSFileStats):
            return 'Invalid LSFileStats to diff'
        if not self.root == other.root:
            return 'Cannot diff at different roots'
        lines = []

        # added/removed directories
        removed_dirs, added_dirs, kept_dirs = set(), set(), set()
        for k in self.files.keys():
            if k in other.files.keys():
                kept_dirs.add(k)
            else:
                removed_dirs.add(k)
        for k in other.files.keys():
            if k not in self.files.keys():
                added_dirs.add(k)
        if len(removed_dirs) > 0:
            lines.append('Removed Directories (%d)' % len(removed_dirs))
            lines.extend(list(sorted(removed_dirs)))
            lines.append('')
        if len(added_dirs) > 0:
            lines.append('Added Directories (%d)' % len(added_dirs))
            lines.extend(list(sorted(added_dirs)))
            lines.append('')

        # diff kept directories
        for k in kept_dirs:
            kept_diff = self.__diff_internal(k, self.files[k], other.files[k])
            if kept_diff:
                lines.append(kept_diff)
                lines.append('')
        return '\n'.join(lines)

    def get_ls_l_output(self,
                        is_recursive: bool = False,
                        bridge_args: Dict[str, Any] = None,
                        *args,
                        **kwargs) -> List[str]:
        if not isinstance(bridge_args, dict):
            bridge_args = {}
        if not is_recursive:
            cmd = config.CFG.get_adb_cmd(ext=[
                'shell',
                'ls',
                '-l',
                self.root
            ], **bridge_args)
            return util.get_cmd_output_lines(cmd, *args, **kwargs)
        else:
            cmd = config.CFG.get_adb_cmd(ext=[
                'shell',
                'ls',
                '-l',
                '-R',
                self.root
            ], **bridge_args)
            return util.get_cmd_output_lines(cmd, *args, **kwargs)

    def ls_l(self,
             is_recursive: bool = False,
             *args,
             **kwargs):
        self.files = {}
        output = self.get_ls_l_output(is_recursive=is_recursive, *args, **kwargs)
        if not is_recursive:
            self.files[self.root] = []
            for line in output:
                if line.startswith('total'):
                    continue
                file_stat = LSFileStat.new_from_line(line)
                if file_stat.is_valid():
                    self.files[self.root].append(file_stat)
        else:
            rt = ''
            for line in output:
                if line.endswith(':'):
                    rt = line[:-1]
                    self.files[rt] = []
                elif line.startswith('total'):
                    continue
                else:
                    file_stat = LSFileStat.new_from_line(line)
                    if file_stat.is_valid():
                        self.files[rt].append(file_stat)

    @classmethod
    def new_from_ls_l(cls, root: str = '/', *args, **kwargs):
        o = cls(root=root)
        o.ls_l(*args, **kwargs)
        return o


if __name__ == '__main__':
    config.init()
    fst = LSFileStats.new_from_ls_l(
        root='/data/local/tmp',
        is_recursive=True)
    # print(file_stats.dump(group_by_type=True))
