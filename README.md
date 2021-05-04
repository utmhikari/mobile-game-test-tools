# mobile-game-test-tools

some python scripts maybe useful in mobile game testing

## prerequisites

- python 3.6+, pycharm
- venv
- pip3 install -r requirements.txt


## tools

some envs should be configured in `config.json`

- adb: adb path in your PC
- serial: default serial of mobile to debug

init config before using tools

```python
import config
config.init()
```

### fstat

- list file stats of specific directory
- diff listed file stats
- android support

```python
# android
from fstat import LSFileStats
fst1 = LSFileStats.new_from_ls_l(
    root='/data/local/tmp',
    is_recursive=True)
print(fst1.dump(group_by_type=True))
# after some changes...
fst2 = LSFileStats.new_from_ls_l(
    root='/data/local/tmp',
    is_recursive=True)
print(fst2.dump(group_by_type=True))
print(fst1.diff(fst2))  # file diff between 2 ls command stats
```

### fgrep

- grep lines of specific file
- ue4 log support
- android support

```python
# UE4 log
# android
from fgrep import UELogGrep
ue_log = UELogGrep(
    path='/sdcard/UE4Game/FounDerBoy/FounDerBoy/Saved/Logs/FounDerBoy.log'
)
ue_log.grep(keyword='LogPluginManager')
print(ue_log.dump())
```
