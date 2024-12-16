"""
MIT License

Copyright (c) 2024 YuYuKunKun

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 16:45
# @Author  : YuYuKunKun
# @File    : chan.py

import json
import math
import mmap
import time
import struct
import asyncio
import datetime
import traceback

from enum import Enum
from random import randint, choice
from pathlib import Path
from threading import Thread
from functools import wraps, lru_cache
from typing import List, Self, Optional, Tuple, final, Dict, Any, Set, Final, SupportsInt, Union
from abc import ABCMeta, abstractmethod

import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query
from termcolor import colored
from collections import defaultdict


# __all__ = ["Line", "Bar", "Bi", "Duan", "ZhongShu", "FenXing", "BaseAnalyzer"]
SupportsHL = Union["Line", "Bar", "Bi", "Duan", "ZhongShu", "FenXing", "Interval", "Pillar"]


def timer(func):
    @wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
        return value

    return wrapper_timer


def ts2int(timestamp: str):
    return int(time.mktime(datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timetuple()))


def int2ts(timestamp: int):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timestamp)))


class Freq(Enum):
    # 60 180 300 900 1800 3600 7200 14400 21600 43200 86400 259200
    S1: int = 1
    S3: int = 3
    S5: int = 5
    S12: int = 12
    m1: int = 60 * 1
    m3: int = 60 * 3  # 180
    m5: int = 60 * 5  # 300
    m15: int = 60 * 15  # 900
    m30: int = 60 * 30  # 1800
    H1: int = 60 * 60 * 1  # 3600
    H2: int = 60 * 60 * 2  # 7200
    H4: int = 60 * 60 * 4  # 14400
    H6: int = 60 * 60 * 6  # 21600
    H12: int = 60 * 60 * 12  # 43200
    D1: int = 60 * 60 * 24  # 86400
    D3: int = 60 * 60 * 24 * 3  # 259200

    def __int__(self):
        return self.value


class Pillar:
    __slots__ = "high", "low"

    def __init__(self, high: float, low: float):
        assert high > low
        self.high = high
        self.low = low


class Shape(Enum):
    D = "底分型"
    G = "顶分型"
    S = "上升分型"
    X = "下降分型"
    T = "喇叭口型"

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Direction(Enum):
    Up = "向上"
    Down = "向下"
    JumpUp = "缺口向上"
    JumpDown = "缺口向下"
    NextUp = "连接向上"  # 高点与后一 低点相同
    NextDown = "连接向下"  # 低点与后一 高点相同

    Left = "左包右"  # 顺序包含
    Right = "右包左"  # 逆序包含

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __int__(self):
        match self:
            case Direction.Up:
                return 1
            case Direction.Down:
                return -1
            case Direction.JumpUp:
                return 2
            case Direction.JumpDown:
                return -2
            case Direction.NextUp:
                return 3
            case Direction.NextDown:
                return -3
            case Direction.Left:
                return 7
            case Direction.Right:
                return 9

    def reversal(self) -> Self:
        match self:
            case Direction.Up:
                return Direction.Down
            case Direction.Down:
                return Direction.Up
            case Direction.JumpUp:
                return Direction.JumpDown
            case Direction.JumpDown:
                return Direction.JumpUp
            case Direction.NextUp:
                return Direction.NextDown
            case Direction.NextDown:
                return Direction.NextUp
            case Direction.Left:
                return Direction.Right
            case Direction.Right:
                return Direction.Left

    def is_down(self) -> bool:
        match self:
            case Direction.Down | Direction.JumpDown | Direction.NextDown:
                return True
            case _:
                return False

    def is_up(self) -> bool:
        match self:
            case Direction.Up | Direction.JumpUp | Direction.NextUp:
                return True
            case _:
                return False

    def is_jump(self) -> bool:
        match self:
            case Direction.JumpDown | Direction.JumpUp:
                return True
            case _:
                return False

    def is_include(self) -> bool:
        match self:
            case Direction.Left | Direction.Right:
                return True
            case _:
                return False

    def is_next(self):
        match self:
            case Direction.NextUp | Direction.NextDown:
                return True
            case _:
                return False

    @staticmethod
    def generator(obj: int, directions):
        i: int = obj
        while i >= 0:
            yield choice(directions)
            i -= 1


class ChanException(Exception):
    """exception"""

    ...


def _print(*args, **kwords):
    result = []
    for i in args:
        if i in ("小阳", True, Shape.D, "底分型") or "小阳" in str(i):
            result.append(colored(i, "green"))

        elif i in ("老阳", False, Shape.G, "顶分型") or "老阳" in str(i):
            result.append(colored(i, "red"))

        elif i in ("少阴",) or "少阴" in str(i):
            result.append("\33[07m" + colored(i, "yellow"))

        elif i in ("老阴",) or "老阴" in str(i):
            result.append("\33[01m" + colored(i, "blue"))

        elif "PUSH" in str(i):
            result.append(colored(i, "red"))

        elif "POP" in str(i):
            result.append(colored(i, "green"))

        elif "ANALYSIS" in str(i):
            result.append(colored(i, "blue"))

        else:
            result.append(i)
    result = tuple(result)
    print(*result, **kwords)


def dp(*args, **kwords):
    if not 1:
        _print(*args, **kwords)


def bdp(*args, **kwargs):
    if not 1:
        dp(*args, **kwargs)


def ddp(*args, **kwargs):
    if not 0:
        dp(*args, **kwargs)


def zsdp(*args, **kwargs):
    if not 1:
        dp(*args, **kwargs)


@lru_cache(maxsize=128)
def double_relation(left: SupportsHL, right: SupportsHL) -> Direction:
    """
    两个带有[low, high]对象的所有关系
    """
    relation = None
    assert left is not right, ChanException("相同对象无法比较", left, right)

    if (left.low <= right.low) and (left.high >= right.high):
        relation = Direction.Left  # "左包右" # 顺序

    elif (left.low >= right.low) and (left.high <= right.high):
        relation = Direction.Right  # "右包左" # 逆序

    elif (left.low < right.low) and (left.high < right.high):
        relation = Direction.Up  # "上涨"
        if left.high < right.low:
            relation = Direction.JumpUp  # "跳涨"

        if left.high == right.low:
            relation = Direction.NextUp

    elif (left.low > right.low) and (left.high > right.high):
        relation = Direction.Down  # "下跌"
        if left.low > right.high:
            relation = Direction.JumpDown  # "跳跌"
        if left.low == right.high:
            relation = Direction.NextDown

    return relation


def triple_relation(left: SupportsHL, mid: SupportsHL, right: SupportsHL, use_right: bool = False, ignore: bool = False) -> tuple[Optional[Shape], tuple[Direction, Direction], Optional[Pillar]]:
    """
    三棵缠论k线的所有关系#, 允许逆序包含存在。
    顶分型: 中间高点为三棵最高点。
    底分型: 中间低点为三棵最低点。
    上升分型: 高点从左至右依次升高
    下降分型: 低点从左至右依次降低
    喇叭口型: 高低点从左至右依次更高更低

    """
    if any((left == mid, mid == right, left == right)):
        raise ChanException("相同对象无法比较")

    zg = min(left.high, mid.high, right.high)
    zd = max(left.low, mid.low, right.low)
    if zg > zd:
        pillar = Pillar(high=zg, low=zd)
    else:
        pillar = None

    shape = None
    lm = double_relation(left, mid)
    mr = double_relation(mid, right)
    # lr = double_relation(left, right)
    match (lm, mr):
        case (Direction.Left, _):
            if ignore:
                ...  # print("顺序包含 lm", left, mid)
            else:
                raise ChanException("顺序包含 lm", left, mid)
        case (_, Direction.Left):
            if ignore:
                ...  # print("顺序包含 mr", mid, right)
            else:
                raise ChanException("顺序包含 mr", mid, right)

        case (Direction.Up | Direction.JumpUp | Direction.NextUp, Direction.Up | Direction.JumpUp | Direction.NextUp):
            shape = Shape.S
        case (Direction.Up | Direction.JumpUp | Direction.NextUp, Direction.Down | Direction.JumpDown | Direction.NextDown):
            shape = Shape.G
        case (Direction.Up | Direction.JumpUp | Direction.NextUp, Direction.Right) if use_right:
            shape = Shape.S

        case (Direction.Down | Direction.JumpDown | Direction.NextDown, Direction.Up | Direction.JumpUp | Direction.NextUp):
            shape = Shape.D
        case (Direction.Down | Direction.JumpDown | Direction.NextDown, Direction.Down | Direction.JumpDown | Direction.NextDown):
            shape = Shape.X
        case (Direction.Down | Direction.JumpDown | Direction.NextDown, Direction.Right) if use_right:
            shape = Shape.X

        case (Direction.Right, Direction.Up | Direction.JumpUp | Direction.NextUp) if use_right:
            shape = Shape.D
        case (Direction.Right, Direction.Down | Direction.JumpDown | Direction.NextDown) if use_right:
            shape = Shape.G
        case (Direction.Right, Direction.Right) if use_right:
            shape = Shape.T
        case _:
            print("未匹配的关系", use_right, lm, mr)

    if shape is None:
        ...  # print(colored("triple_relation: ", "red"), shape, (lm, mr), left, mid, right)

    return shape, (lm, mr), pillar


class Command:
    APPEND: Final[str] = "APPEND"
    MODIFY: Final[str] = "MODIFY"
    REMOVE: Final[str] = "REMOVE"

    def __init__(self, cmd: str, info: str) -> None:
        self.cmd = cmd
        self.info = info

    def __str__(self):
        # return f"{self.cmd.upper()}({self.info})"
        return f"{self.cmd.upper()}"

    @classmethod
    def Append(cls, stamp: str) -> Self:
        return Command(cls.APPEND, stamp)

    @classmethod
    def Modify(cls, stamp: str) -> Self:
        return Command(cls.MODIFY, stamp)

    @classmethod
    def Remove(cls, stamp: str) -> Self:
        return Command(cls.REMOVE, stamp)


@final
class BSPoint:
    __slots__ = "info", "tp", "dt", "price", "valid", "creation_offset", "fix_offset", "stamp"

    def __init__(self, info: str, tp: str, dt: datetime, price: float, valid: bool, creation_offset: int, fix_offset: int, stamp: str) -> None:
        self.info = info
        self.tp = tp
        self.dt = dt
        self.price = price
        self.valid = valid
        self.creation_offset = creation_offset
        self.fix_offset = fix_offset
        self.stamp = stamp


class ZShuCondition(Enum):
    """中枢的三种情况"""

    New: str = "新生"
    Continue: str = "延续"
    Expand: str = "扩张"


@final
class ChanConfig:
    __slots__ = (
        "ANALYZER_CALC_BI",
        "ANALYZER_CALC_BI_ZS",
        "ANALYZER_CALC_XD",
        "ANALYZER_CALC_XD_ZS",
        "ANALYZER_SHON_TV",
        "BI_LASTorFIRST",
        "BI_FENGXING",
        "BI_JUMP",
        "BI_JUMP_SCALE",
        "BI_LENGTH",
        "MACD_FAST_PERIOD",
        "MACD_SIGNAL_PERIOD",
        "MACD_SLOW_PERIOD",
        "ANALYZER_CALC_MACD",
    )

    def __init__(self):
        self.BI_LENGTH = 5  # 成BI最低长度
        self.BI_JUMP = True  # 跳空是否判定为 NewBar
        self.BI_JUMP_SCALE = 0.15  # 当跳空是否判定为 NewBar时, 此值大于0时按照缺口所占比例判定是否为NewBar，等于0时直接判定为NerBar
        self.BI_LASTorFIRST = True  # 一笔终点存在多个终点时 True: last, False: first
        self.BI_FENGXING = False  # True: 一笔起始分型高低包含整支笔对象则不成笔, False: 只判断分型中间数据是否包含

        self.ANALYZER_CALC_BI = True  # 是否计算BI
        self.ANALYZER_CALC_XD = True  # 是否计算XD
        self.ANALYZER_CALC_BI_ZS = True  # 是否计算BI中枢
        self.ANALYZER_CALC_XD_ZS = True  # 是否计算XD中枢
        self.ANALYZER_CALC_MACD = True  # 是否计算MACD
        self.ANALYZER_SHON_TV = True
        self.MACD_FAST_PERIOD = 12.0
        self.MACD_SLOW_PERIOD = 26.0
        self.MACD_SIGNAL_PERIOD = 9.0


@final
class MACD:
    __slots__ = "fast_ema", "slow_ema", "DIF", "DEA", "fastperiod", "slowperiod", "signalperiod"

    def __init__(self, fast_ema: float, slow_ema: float, dif: float, dea: float, fastperiod: float = 12.0, slowperiod: float = 26.0, signalperiod: float = 9.0):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.DIF = dif
        self.DEA = dea
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

    @classmethod
    def calc(cls, pre: "Bar", bar: "Bar") -> Self:
        value = bar.close
        _fast_ema = (2.0 * value + (pre.macd.fastperiod - 1.0) * pre.macd.fast_ema) / (pre.macd.fastperiod + 1.0)
        _slow_ema = (2.0 * value + (pre.macd.slowperiod - 1.0) * pre.macd.slow_ema) / (pre.macd.slowperiod + 1.0)
        _dif = _fast_ema - _slow_ema
        _dea = (2.0 * _dif + (pre.macd.signalperiod - 1.0) * pre.macd.DEA) / (pre.macd.signalperiod + 1.0)
        macd = MACD(_fast_ema, _slow_ema, _dif, _dea, fastperiod=pre.macd.fastperiod, slowperiod=pre.macd.slowperiod, signalperiod=pre.macd.signalperiod)
        bar.macd = macd
        return macd


class Observer(metaclass=ABCMeta):
    thread = None
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    TIME = 0.01

    @abstractmethod
    def notify(self, obj: Any, cmd: Command): ...


class Bar:
    __slots__ = "index", "dt", "open", "high", "low", "close", "volume", "direction", "__stamp", "macd", "shape", "_raw_start_index", "raw_end_index"

    def __init__(self, dt: datetime, o: float, high: float, low: float, c: float, v: float, i: int, stamp: str):
        self.index: int = i
        self.dt: datetime = dt
        self.open: float = o
        self.high: float = high
        self.low: float = low
        self.close: float = c
        self.volume: float = v
        if self.open > self.close:
            self.direction = Direction.Down
        else:
            self.direction = Direction.Up
        self.__stamp = stamp
        self.macd = MACD(c, c, 0.0, 0.0)

        self.shape: Optional[Shape] = None
        self._raw_start_index: int = i
        self.raw_end_index: int = i

    @property
    def stamp(self) -> str:
        return self.__stamp

    @property
    def speck(self) -> float:
        if self.shape is Shape.G:
            return self.high
        elif self.shape is Shape.S:
            return self.high
        elif self.shape is Shape.D:
            return self.low
        elif self.shape is Shape.X:
            return self.low
        else:
            print("NewBar.speck: shape is None")
            return self.high

    def __str__(self):
        return f"{self.__class__.__name__}<{self.__stamp}>({self.dt}, {self.high}, {self.low}, index={self.index})"

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.__stamp}>({self.dt}, {self.high}, {self.low}, index={self.index})"

    def __bytes__(self):
        return struct.pack(
            ">6d",
            int(self.dt.timestamp()),
            round(self.open, 8),
            round(self.high, 8),
            round(self.low, 8),
            round(self.close, 8),
            round(self.volume, 8),
        )

    def to_new_bar(self, pre) -> Self:
        if self.stamp == "NewBar":
            return self
        return Bar.creat_new_bar_from_raw(self, pre)

    @classmethod
    def creat_new_bar_from_raw(cls, bar: Self, pre: Optional[Self] = None):
        return cls.creat_new_bar(bar.dt, bar.high, bar.low, bar.direction, bar.volume, bar.index, pre=pre)

    @classmethod
    def creat_new_bar(
        cls,
        dt: datetime,
        high: float,
        low: float,
        direction: Direction,
        volume: float,
        raw_index: int,
        pre: Optional[Self] = None,
    ):
        assert high >= low
        if direction == Direction.Down:
            close = low
            _open = high
        else:
            close = high
            _open = low

        if direction is Direction.Up:
            shape = Shape.S
        else:
            shape = Shape.X

        index = 0
        nb = Bar(dt=dt, o=_open, high=high, low=low, c=close, v=volume, i=index, stamp="NewBar")
        nb._raw_start_index = raw_index
        nb.raw_end_index = raw_index
        nb.shape = shape

        if pre is not None:
            nb.index = pre.index + 1

            if double_relation(pre, nb).is_include():
                raise ChanException(f"\n    {double_relation(pre, nb)}\n    {pre},\n    {nb}")
        return nb

    @classmethod
    def creat_raw_bar(cls, dt: datetime, o: float, h: float, low: float, c: float, v: float, i: int) -> Self:
        return cls(dt, o, h, low, c, v, i, "RawBar")

    @classmethod
    def bars_save_as_dat(cls, path: str, bars: List):
        with open(path, "wb") as f:
            for bar in bars:
                f.write(bytes(bar))
        print(f"Saved {len(bars)} bars to {path}")

    @classmethod
    def from_be_bytes(cls, buf: bytes, stamp: str = "RawBar") -> Self:
        timestamp, open_, high, low, close, vol = struct.unpack(">6d", buf[: struct.calcsize(">6d")])
        return cls(
            dt=datetime.datetime.fromtimestamp(timestamp),
            o=open_,
            high=high,
            low=low,
            c=close,
            v=vol,
            i=0,
            stamp=stamp,
        )

    @classmethod
    def from_csv_file(cls, path: str, stamp: str = "RawBar") -> List[Self]:
        raws: List = []
        with open(path, "r") as f:
            stamps = f.readline().split(",")
            ts = stamps.index("timestamp")
            o = stamps.index("open")
            h = stamps.index("high")
            low = stamps.index("low")
            c = stamps.index("close")
            v = stamps.index("volume")
            i = 0
            for line in f.readlines():
                info = line.split(",")
                rb = Bar(datetime.datetime.strptime(info[ts], "%Y-%m-%d %H:%M:%S"), float(info[o]), float(info[h]), float(info[low]), float(info[c]), float(info[v]), i, stamp)
                raws.append(rb)
                i += 1

        return raws

    @classmethod
    def generate(cls, bar: "Bar", direction: Direction, seconds: int, half: bool = False) -> Self:
        offset = datetime.timedelta(seconds=seconds)
        dt: datetime = bar.dt + offset
        volume: float = 998
        raw_index: int = bar._raw_start_index + 1
        high: float = 0
        low: float = 0
        d = bar.high - bar.low
        match direction:
            case Direction.Up:
                i = d * 0.5 if half else randint(int(d * 0.1279), int(d * 0.883))
                low: float = bar.low + i
                high: float = bar.high + i
            case Direction.Down:
                i = d * 0.5 if half else randint(int(d * 0.1279), int(d * 0.883))
                low: float = bar.low - i
                high: float = bar.high - i
            case Direction.JumpUp:
                i = d * 1.5 if half else randint(int(d * 1.1279), int(d * 1.883))
                low: float = bar.low + i
                high: float = bar.high + i
            case Direction.JumpDown:
                i = d * 1.5 if half else randint(int(d * 1.1279), int(d * 1.883))
                low: float = bar.low - i
                high: float = bar.high - i
            case Direction.NextUp:
                i = bar.high - bar.low
                high: float = bar.high + i
                low: float = bar.high
            case Direction.NextDown:
                i = bar.high - bar.low
                high: float = bar.low
                low: float = bar.low - i

        nb = Bar.creat_new_bar(dt, high, low, Direction.Up if direction.is_up() else Direction.Down, volume, raw_index, bar)
        nb.index = bar.index + 1
        assert double_relation(bar, nb) is direction, (direction, double_relation(bar, nb))
        return nb

    @classmethod
    def merger(cls, pre: Optional[Self], bar: Self, next_raw_bar: Self) -> Optional[Self]:
        if not double_relation(bar, next_raw_bar).is_include():
            nb = next_raw_bar.to_new_bar(bar)
            nb.index = bar.index + 1
            return nb

        if next_raw_bar.index - 1 != bar.raw_end_index:
            raise ChanException(f"NewBar.merger: 不可追加不连续元素 bar.raw_end_index: {bar.raw_end_index}, next_raw_bar.index: {next_raw_bar.index}.")

        direction = Direction.Up
        if pre is not None:
            if double_relation(pre, bar).is_down():
                direction = Direction.Down

        func = max
        if direction is Direction.Down:
            func = min
        bar.high = func(bar.high, next_raw_bar.high)
        bar.low = func(bar.low, next_raw_bar.low)
        bar.open = bar.high if bar.direction is Direction.Down else bar.low
        bar.close = bar.low if bar.direction is Direction.Down else bar.high
        bar.raw_end_index = next_raw_bar.index

        if pre is not None:
            bar.index = pre.index + 1
        return None


class FenXing:
    __slots__ = "index", "left", "mid", "right"

    def __init__(self, left: Bar, mid: Bar, right: Bar, index: int = 0):
        self.left = left
        self.mid = mid
        self.right = right
        self.index = index

    @property
    def dt(self) -> datetime.datetime:
        return self.mid.dt

    @property
    def shape(self) -> Shape:
        return self.mid.shape

    @property
    def speck(self) -> float:
        return self.mid.speck

    @property
    def high(self) -> float:
        return max(self.left.high, self.mid.high)

    @property
    def low(self) -> float:
        return min(self.left.low, self.mid.low)

    def __str__(self):
        return f"FenXing({self.shape}, {self.speck}, {self.dt})"

    def __repr__(self):
        return f"FenXing({self.shape}, {self.speck}, {self.dt})"

    def get_shape(self) -> Shape:
        shape, (_, _), _ = triple_relation(self.left, self.mid, self.right)
        return shape

    def get_relations(self) -> (Direction, Direction):
        _, (lm, mr), _ = triple_relation(self.left, self.mid, self.right)
        return lm, mr

    @staticmethod
    def get_fenxing(bars: List[Bar], mid: Bar) -> "FenXing":
        index = bars.index(mid)
        return FenXing(bars[index - 1], mid, bars[index + 1])

    @staticmethod
    def append(fxs, fx):
        if fxs and fxs[-1].shape is fx.shape:
            raise ChanException("分型相同无法添加", fxs[-1], fx)
        i = 0
        if fxs:
            i = fxs[-1].index + 1
        fx.index = i
        fxs.append(fx)

    @staticmethod
    def pop(fxs, fx):
        if fxs and fxs[-1] is not fx:
            raise ChanException("分型相同无法删除", fxs[-1], fx)
        return fxs.pop()


class Line(metaclass=ABCMeta):
    __slots__ = "pre", "next", "index", "__start", "__end", "__stamp", "__elements"

    def __init__(self, start: FenXing, end: FenXing, index: int, elements: List | Set, stamp: str = "Line"):
        self.index: int = index
        self.pre: Optional[Self] = None
        self.next: Optional[Self] = None
        self.__start = start
        self.__end = end
        self.__stamp = stamp
        self.__elements = elements

    def __len__(self):
        return len(self.elements)

    def __iter__(self):
        return iter(self.elements)

    def __hash__(self):
        return hash(f"{self.stamp} {self.start.mid}")

    def __eq__(self, other):
        return type(other) is self and self.stamp == other.stamp and self.start == other.start and self.end == other.end and self.elements == other.elements and self.index == other.index

    @property
    @final
    def stamp(self) -> str:
        return self.__stamp

    @property
    @final
    def elements(self) -> List[Self]:
        return self.__elements

    @elements.setter
    def elements(self, elements: List[Self]):
        self.__elements = elements

    @property
    def start(self) -> FenXing:
        return self.__start

    @property
    def end(self) -> FenXing:
        return self.__end

    @end.setter
    @final
    def end(self, end: FenXing):
        self.__end = end

    @property
    @final
    def direction(self) -> Direction:
        if self.start.shape is Shape.G and self.end.shape is Shape.D:
            return Direction.Down
        elif self.start.shape is Shape.D and self.end.shape is Shape.G:
            return Direction.Up
        else:
            raise ChanException(f"{self.stamp}.direction: {self.start.shape}, {self.end.shape}, {self.stamp}")

    @property
    def high(self) -> float:
        if self.direction == Direction.Down:
            return self.start.speck
        else:
            return self.end.speck

    @property
    def low(self) -> float:
        if self.direction == Direction.Up:
            return self.start.speck
        else:
            return self.end.speck

    @property
    def open(self) -> float:
        if self.direction == Direction.Down:
            return self.high
        else:
            return self.low

    @property
    def close(self) -> float:
        if self.direction == Direction.Up:
            return self.high
        else:
            return self.low

    def calc_angle(self) -> float:
        # 计算线段的角度
        dx = self.end.dt.timestamp() - self.start.dt.timestamp()  # self.end.dt - self.start.dt  # 时间差
        dy = self.end.speck - self.start.speck  # 价格差

        if dx == 0:
            return 90.0 if dy > 0 else -90.0

        angle = math.degrees(math.atan2(dy, dx))
        return angle

    def calc_speed(self) -> float:
        # 计算线段的速度
        dx = self.end.mid.index - self.start.mid.index  # self.end.dt - self.start.dt  # 时间差
        dy = self.end.speck - self.start.speck  # 价格差
        return dy / dx

    def calc_measure(self) -> float:
        # 计算线段测度
        dx = self.end.dt.timestamp() - self.start.dt.timestamp()  # 时间差
        dy = abs(self.end.speck - self.start.speck)  # 价格差的绝对值
        return math.sqrt(dx * dx + dy * dy)  # 返回线段的欧几里得长度作为测度

    def calc_amplitude(self) -> float:
        # 计算线段振幅比例
        amplitude = self.end.speck - self.start.speck
        return amplitude / self.start.speck if self.start.speck != 0 else 0

    def is_previous(self, line: "Line") -> bool:
        return line.end is self.start

    def is_next(self, line: "Line") -> bool:
        return self.end is line.start

    def get_line(self) -> "Line":
        return Line(self.start, self.end, self.index, self.elements, self.stamp)

    def get_bars(self, bars: list) -> List[Bar]:
        return bars[bars.index(self.start.mid) : bars.index(self.end.mid) + 1]

    @classmethod
    def append(cls, lines: List["Line"], line: "Line"):
        if lines and not lines[-1].is_next(line):
            raise ChanException("Line.append 不连续", lines[-1], line)

        if lines:
            line.index = lines[-1].index + 1
            line.pre = lines[-1]
            if len(lines) > 1:
                lines[-2].next = lines[-1]

        lines.append(line)

    @classmethod
    def pop(cls, lines: List["Line"], line: "Line") -> Optional["Line"]:
        if not lines:
            return

        if lines[-1] is line:
            drop = lines.pop()
            return drop
        raise ChanException("Line.pop 弹出数据不在列表中")

    @classmethod
    @final
    def create(cls, obj: List | "Line", stamp: str) -> "Line":
        if type(obj) is list:
            lines: List["Line"] = obj[:]
            return Line(lines[0].start, lines[-1].end, 0, lines, stamp)
        line: "Line" = obj
        return Line(line.start, line.end, 0, [line], stamp)


class Interval:
    __slots__ = "index", "elements", "__high", "__low"

    def __init__(self, elements: List, high: float, low: float):
        self.elements = elements
        self.__high = high
        self.__low = low
        self.index = 0

    def __str__(self):
        return f"Interval({self.index}, {len(self)}, {self.__high}, {self.__low})"

    def __len__(self):
        return len(self.elements)

    def __iter__(self):
        return iter(self.elements)

    @property
    def high(self) -> int | float:
        return self.__high

    @property
    def low(self) -> int | float:
        return self.__low

    def check(self) -> Optional[bool]:
        tmp = Interval.new(self.elements)
        if tmp:
            for i in range(3, len(self.elements) - 1):
                hl = self.elements[i]
                if double_relation(self, hl).is_jump():
                    if i != len(self.elements) - 1:
                        self.elements = self.elements[:i]
                    return None
            return True
        return False

    @classmethod
    def new(cls, elements) -> Optional["Interval"]:
        if len(elements) < 3:
            return

        lr = double_relation(elements[0], elements[2])
        if lr.is_jump():
            return

        lm = double_relation(elements[0], elements[1])
        if lm.is_jump():
            return

        mr = double_relation(elements[1], elements[2])
        if mr.is_jump():
            return

        high = min([hl.high for hl in elements[:3]])
        low = max([hl.low for hl in elements[:3]])
        return cls(elements, high, low)

    @classmethod
    def analyzer(cls, hls: List, intervals: List["Interval"], observer: Observer):
        if not intervals:
            for i in range(1, len(hls) - 1):
                new = cls.new([hls[i - 1], hls[i], hls[i + 1]])
                if new is not None:
                    intervals.append(new)
                    observer.notify(new, Command.Append("nb"))
                    return cls.analyzer(hls, intervals, observer)

        else:
            last = intervals[-1]
            flag: Optional[bool] = last.check()
            if flag is None:
                index = hls.index(last.elements[2]) + 1
            elif flag is True:
                index = hls.index(last.elements[-1]) + 1
            else:
                intervals.pop()
                observer.notify(last, Command.Remove("nb"))
                return cls.analyzer(hls, intervals, observer)

            observer.notify(last, Command.Modify("nb"))

            while index == -1:
                try:
                    index = hls.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    if len(last) > 3:
                        last.elements.pop()
                    else:
                        drop = intervals.pop()
                        observer.notify(drop, Command.Remove("nb"))
                        return cls.analyzer(hls, intervals, observer)

            elements = []
            for hl in hls[index:]:
                if double_relation(last, hl).is_jump():
                    if not elements:
                        elements.append(last.elements[-1])
                    elements.append(hl)
                else:
                    if not elements:
                        if hl not in last.elements:
                            last.elements.append(hl)
                        observer.notify(last, Command.Modify("nb"))
                    else:
                        elements.append(hl)

                if len(elements) >= 3:
                    new = cls.new(elements[:])
                    if new is None:
                        elements.pop(0)
                    else:
                        intervals.append(new)
                        new.index = last.index + 1
                        observer.notify(new, Command.Append("nb"))
                        last = new
                        elements.clear()


class Lines:
    def __init__(self, elements: List[Line]):
        self.__elements = elements

    def __len__(self):
        return len(self.__elements)

    def __iter__(self):
        return iter(self.__elements)

    def __next__(self):
        return next(self)

    def __getitem__(self, index):
        return self.__elements[index]

    def __setitem__(self, index, value):
        self.__elements[index] = value

    def __delitem__(self, index):
        del self.__elements[index]

    def append(self, element: Line):
        length = len(self.__elements)
        if length > 0:
            last = self.__elements[-1]
            assert last.end is element.start
            if last.index + 1 != element.index:
                element.index = last.index + 1
                element.pre = last
                if length > 1:
                    pre = self.__elements[-2]
                    pre.next = last

        self.__elements.append(element)

    def pop(self, index=-1):
        return self.__elements.pop(index)

    def index(self, element: Line):
        return self.__elements.index(element)

    def clear(self):
        self.__elements.clear()

    def reset_line_index(self):
        """reset line index"""
        for index, element in enumerate(self.__elements):
            element.index = index
        print("Lines reset line index done!", len(self.__elements))

    def reset_line_next_and_pre(self):
        for i in range(1, len(self.__elements)):
            if hasattr(self.__elements[i - 1], "next"):
                self.__elements[i - 1].next = self.__elements[i]
            if hasattr(self.__elements[i - 1], "pre"):
                self.__elements[i].pre = self.__elements[i - 1]


@final
class FeatureSequence(Line):
    def __init__(self, elements: Set[Line]):
        start: FenXing = tuple(elements)[0].start
        end: FenXing = tuple(elements)[0].end
        super().__init__(start, end, 0, elements, f"FeatureSequence<{tuple(elements)[0].stamp if len(elements) > 0 else None}>")

    def __str__(self):
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)}, {self.stamp})"

    def __repr__(self):
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)}, {self.stamp})"

    @property
    def start(self) -> FenXing:
        direction = tuple(self.elements)[0].direction
        if direction is Direction.Down:  # Down特征序列 为 Up线段, 取高高
            func = max
        else:
            func = min
        fx = func([line.start for line in self.elements], key=lambda o: o.speck)
        assert fx.shape in (Shape.G, Shape.D)
        return fx

    @property
    def end(self) -> FenXing:
        direction = tuple(self.elements)[0].direction
        if direction is Direction.Down:  # Down特征序列 为 Up线段, 取高高
            func = max
        else:
            func = min
        fx = func([line.end for line in self.elements], key=lambda o: o.speck)
        assert fx.shape in (Shape.G, Shape.D)
        return fx

    @property
    def high(self) -> float:
        return max([self.end, self.start], key=lambda fx: fx.speck).speck

    @property
    def low(self) -> float:
        return min([self.end, self.start], key=lambda fx: fx.speck).speck

    def add(self, line: Line):
        direction = tuple(self.elements)[0].direction
        if line.direction != direction:
            raise ChanException("方向不匹配", direction, line, self)
        self.elements.add(line)

    def remove(self, line: Line):
        direction = tuple(self.elements)[0].direction
        if line.direction != direction:
            raise ChanException("方向不匹配", direction, line, self)

        try:
            self.elements.remove(line)
        except Exception as e:
            print(self)
            raise e

    @classmethod
    def analyzer(cls, lines: List[Line], direction: Direction, combines: Tuple[Direction] = (Direction.Left,)) -> Tuple[Optional["FeatureSequence"], Optional["FeatureSequence"], Optional["FeatureSequence"]]:
        if combines is None:
            combines = (Direction.Left,)
        features: List[FeatureSequence] = []
        for obj in lines:
            if obj.direction is direction:
                if len(features) >= 3:
                    left, mid, right = features[-3], features[-2], features[-1]
                    shape, (_, _), _ = triple_relation(left, mid, right, use_right=True, ignore=True)
                    if (direction is Direction.Up and shape is Shape.G and obj.high > mid.high) or (direction is Direction.Down and shape is Shape.D and obj.low < mid.low):
                        start = min(mid.elements, key=lambda o: o.index)
                        end = max(right.elements, key=lambda o: o.index)
                        elements = lines[lines.index(start) : lines.index(end) + 1]
                        fake = Line(start.start, end.end, 0, elements, f"Fake-{start.stamp}")
                        feature = FeatureSequence({fake})
                        features.pop()
                        features[-1] = feature

                continue
            if features:
                last = features[-1]

                if double_relation(last, obj) in combines:
                    last.add(obj)
                else:
                    features.append(FeatureSequence({obj}))
            else:
                features.append(FeatureSequence({obj}))

        length = len(features)
        if length == 1:
            return features[0], None, None
        if length == 2:
            return features[0], features[1], None
        if length >= 3:
            relation = double_relation(features[-2], features[-1])
            if direction is Direction.Up:
                if relation.is_down():
                    return features[-3], features[-2], features[-1]
                else:
                    return features[-2], features[-1], None
            else:
                if relation.is_up():
                    return features[-3], features[-2], features[-1]
                else:
                    return features[-2], features[-1], None

        return None, None, None


class ZhongShu:
    __slots__ = "index", "elements", "third", "__stamp", "__direction"

    def __init__(self, direction: Direction, lines: List[Line]):
        self.index: int = 0
        self.__direction = direction
        self.elements: List[Line] = list(lines)
        self.third: Optional[Line] = None
        self.__stamp = lines[0].stamp

    def __str__(self):
        return f"{self.stamp}中枢({self.index}, {self.direction}, {self.third is not None}, {self.zg}, {self.zd}, elements size={len(self.elements)})"

    def __repr__(self):
        return f"{self.stamp}中枢({self.index}, {self.direction}, {self.third is not None}, {self.zg}, {self.zd}, elements size={len(self.elements)})"

    @property
    def stamp(self) -> str:
        return f"ZhongShu<{self.__stamp}>"

    @property
    def left(self) -> Optional[Line]:
        return self.elements[0] if self.elements else None

    @property
    def mid(self) -> Optional[Line]:
        return self.elements[1] if len(self.elements) > 1 else None

    @property
    def right(self) -> Optional[Line]:
        return self.elements[2] if len(self.elements) > 2 else None

    @property
    def direction(self) -> Direction:
        return self.__direction
        # return Direction.Down if self.start.shape is Shape.D else Direction.Up

    @property
    def zg(self) -> float:
        return min(self.elements[:3], key=lambda o: o.high).high

    @property
    def zd(self) -> float:
        return max(self.elements[:3], key=lambda o: o.low).low

    @property
    def g(self) -> float:
        return min(self.elements, key=lambda o: o.high).high

    @property
    def d(self) -> float:
        return max(self.elements, key=lambda o: o.low).low

    @property
    def gg(self) -> float:
        return max(self.elements, key=lambda o: o.high).high

    @property
    def dd(self) -> float:
        return min(self.elements, key=lambda o: o.low).low

    @property
    def high(self) -> float:
        return self.zg

    @property
    def low(self) -> float:
        return self.zd

    @property
    def start(self) -> FenXing:
        return self.elements[0].start

    @property
    def end(self) -> FenXing:
        return self.elements[-1].end

    @property
    def last(self) -> Line:
        return self.elements[-1]

    def update(self, lines: List[Line]) -> bool:
        i = self.elements[-1].index

        while 1:
            try:
                lines.index(self.elements[-1])
                break
            except ValueError:
                _ = Line.pop(self.elements, self.elements[-1])

        fixed = False
        for line in lines:
            if self.elements[-1].is_next(line):
                self.elements.append(line)
                fixed = True
                if line.index == i:
                    break
        return fixed

    def check(self) -> bool:
        return double_relation(self.left, self.right) in (
            Direction.Down,
            Direction.Up,
            Direction.Left,
            Direction.Right,
        )

    def get_elements(self) -> List[Line]:
        elements: List[Line] = self.elements[:]
        if self.third is not None:
            elements.append(self.third)
        return elements

    @classmethod
    def append(cls, zss: List["ZhongShu"], zs: "ZhongShu", observer: Observer):
        if zss:
            zs.index = zss[-1].index + 1
            if zss[-1].get_elements()[-1].index > zs.get_elements()[-1].index:
                raise ChanException()
        zss.append(zs)
        zsdp(f"ZhongShu.append: {zs}")
        observer and observer.notify(zs, Command.Append(zs.stamp + "_zs"))

    @classmethod
    def pop(cls, zss: List["ZhongShu"], zs: "ZhongShu", observer: Observer) -> Optional["ZhongShu"]:
        if not zss:
            return
        if zss[-1] is zs:
            zsdp(f"ZhongShu.pop: {zs}")
            observer and observer.notify(zs, Command.Remove(zs.stamp + "_zs"))
            return zss.pop()

    @classmethod
    def new(cls, elements: List[Line]) -> Optional["ZhongShu"]:
        if Interval.new(elements) is not None:
            return ZhongShu(elements[1].direction, elements)

    @classmethod
    def analyzer(cls, lines: List[Line], zss: List["ZhongShu"], observer: Optional[Observer]):
        if not lines:
            return

        if not zss:
            for i in range(1, len(lines) - 1):
                left, mid, right = lines[i - 1], lines[i], lines[i + 1]
                new = cls.new([left, mid, right])
                if new is not None:
                    if left.index == 0:
                        continue  # 方便计算走势

                    cls.append(zss, new, observer)
                    return cls.analyzer(lines, zss, observer)

        else:
            last = zss[-1]
            tmp = Interval.new(last.elements)
            if tmp is None:
                cls.pop(zss, last, observer)
                return cls.analyzer(lines, zss, observer)
            else:
                if last.high == tmp.high and last.low == tmp.low:
                    ...
                else:
                    cls.pop(zss, last, observer)
                    return cls.analyzer(lines, zss, observer)

            if last.third is not None:
                if not double_relation(last, last.third).is_jump():
                    last.elements.append(last.third)
                    last.third = None
                    observer and observer.notify(last, Command.Modify(last.stamp))

            while 1:
                try:
                    index = lines.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    if len(last.elements) > 3:
                        last.elements.pop()
                        observer and observer.notify(last, Command.Modify(last.stamp))
                    else:
                        cls.pop(zss, last, observer)
                        return cls.analyzer(lines, zss, observer)

            elements = []
            for hl in lines[index:]:
                if double_relation(last, hl).is_jump():
                    elements.append(hl)
                    if last.elements[-1].is_next(hl):
                        last.third = hl
                else:
                    if not elements:
                        last.elements.append(hl)
                        observer and observer.notify(last, Command.Modify(last.stamp))
                    else:
                        elements.append(hl)

                if len(elements) >= 3:
                    new = cls.new(elements[:])
                    if new is None:
                        elements.pop(0)
                    else:
                        relation = double_relation(last, new)
                        if relation.is_up():
                            if elements[0].direction == Direction.Up:
                                elements.pop(0)
                                continue
                        elif relation.is_down():
                            if elements[0].direction == Direction.Down:
                                elements.pop(0)
                                continue
                        else:
                            print(colored(f"{relation}", "red"))

                        cls.append(zss, new, observer)
                        last = new
                        elements = []


@final
class Bi(Line):
    __slots__ = "fake", "config"

    def __init__(
        self,
        pre: Optional["Self"],
        start: FenXing,
        end: FenXing,
        elements: List[Bar],
        fake: bool,
        config: ChanConfig,
    ):
        super().__init__(start, end, 0, elements, "Bi")
        self.pre = pre
        self.fake = fake
        self.config = config

        if pre is not None:
            assert pre.end is start, (pre.end, start)
            self.index = pre.index + 1

    def __str__(self):
        return f"Bi({self.index}, {self.direction}, {colored(self.start.dt, 'green')}, {self.start.speck}, {colored(self.end.dt, 'green')}, {self.end.speck}, {self.elements[-1]}, fake: {self.fake})"

    def __repr__(self):
        return f"Bi({self.index}, {self.direction}, {colored(self.start.dt, 'green')}, {self.start.speck}, {colored(self.end.dt, 'green')}, {self.end.speck}, {self.elements[-1]}, fake: {self.fake})"

    @property
    def length(self) -> int:
        size = 1
        elements = self.elements
        for i in range(1, len(elements)):
            left = elements[i - 1]
            right = elements[i]
            assert left.index + 1 == right.index, (
                left.index,
                right.index,
            )
            relation = double_relation(left, right)
            if self.config.BI_JUMP and relation.is_jump():
                if self.config.BI_JUMP_SCALE > 0.0:
                    if relation.is_up():
                        high = right.low
                        low = left.high
                    else:
                        high = left.low
                        low = right.high

                    real_high = self.real_high
                    real_low = self.real_low
                    if (high - low) / (real_high.high - real_low.low) >= self.config.BI_JUMP_SCALE:
                        size += 1

                else:
                    size += 1
            size += 1
        if not self.config.BI_JUMP:
            assert size == len(elements)
        if self.config.BI_JUMP:
            return size
        return len(elements)

    @property
    def real_high(self) -> Optional[Bar]:
        if not self.elements:
            return None
        highs: List[Bar] = [self.elements[0]]
        for bar in self.elements[1:]:
            if bar.high >= highs[-1].high:
                if bar.high > highs[-1].high:
                    highs.clear()
                highs.append(bar)
        if len(highs) > 1:
            dp("", highs)
        return highs[-1] if self.config.BI_LASTorFIRST else highs[0]

    @property
    def real_low(self) -> Optional[Bar]:
        if not self.elements:
            return None
        lows: List[Bar] = [self.elements[0]]
        for bar in self.elements[1:]:
            if bar.low <= lows[-1].low:
                if bar.low < lows[-1].low:
                    lows.clear()
                lows.append(bar)
        if len(lows) > 1:
            dp("", lows)
        return lows[-1] if self.config.BI_LASTorFIRST else lows[0]

    @property
    def relation(self) -> bool:
        if self.config.BI_FENGXING:
            start = self.start
            relation = double_relation(start, self.end)
        else:
            start = self.start.mid
            relation = double_relation(start, self.end)

        if self.direction is Direction.Down:
            return relation.is_down()
        return relation.is_jump()

    def check(self) -> bool:
        if len(self.elements) >= self.config.BI_FENGXING:
            # assert self.start.mid is self.elements[0]
            # assert self.end.mid is self.elements[-1]
            if self.direction is Direction.Down and self.start.mid is self.real_high and self.end.mid is self.real_low:
                return True
            if self.direction is Direction.Up and self.start.mid is self.real_low and self.end.mid is self.real_high:
                return True
        return False

    @staticmethod
    def get_elements(bars: List[Bar], start: FenXing, end: FenXing) -> List[Bar]:
        return bars[bars.index(start.mid) : bars.index(end.mid) + 1]

    @classmethod
    def analyzer(
        cls,
        fx: FenXing,
        fxs: List[FenXing],
        bis: List["Bi"],
        bars: List[Bar],
        _from: str,
        level: int,
        config: ChanConfig,
        observer: Observer,
    ):
        if not fxs:
            if fx.shape in (Shape.G, Shape.D):
                fxs.append(fx)
            return

        def pop():
            tmp_ = fxs.pop()
            if bis:
                bi_ = bis.pop()
                assert bi_.end is tmp_, "最后一笔终点错误"
                if _from == "analyzer":
                    bdp(f"Bi. pop: {bi_}")
                    observer and observer.notify(bi_, Command.Remove("Bi"))

        last = fxs[-1]

        if last.mid.dt > fx.mid.dt:
            raise ChanException("时序错误")

        if (last.shape is Shape.G and fx.shape is Shape.D) or (last.shape is Shape.D and fx.shape is Shape.G):
            bi = Bi(None, last, fx, Bi.get_elements(bars, last, fx), False, config)
            if bi.length > 4:
                eq = config.BI_LASTorFIRST
                config.BI_LASTorFIRST = False  # 起始点检测时不考虑相同起始点情况，避免递归

                if last.shape is Shape.G and fx.shape is Shape.D:
                    start = bi.real_high
                else:
                    start = bi.real_low
                if start is not last.mid:
                    # print("不是真底")
                    new = FenXing.get_fenxing(bars, start)
                    if last.shape is Shape.G and fx.shape is Shape.D:
                        assert new.shape is Shape.G, new
                    else:
                        assert new.shape is Shape.D, new
                    Bi.analyzer(new, fxs, bis, bars, _from, level + 1, config, observer)  # 处理新顶
                    Bi.analyzer(fx, fxs, bis, bars, _from, level + 1, config, observer)  # 再处理当前底
                    config.BI_LASTorFIRST = eq
                    return
                config.BI_LASTorFIRST = eq

                if last.shape is Shape.G and fx.shape is Shape.D:
                    end = bi.real_low
                else:
                    end = bi.real_high

                if bi.relation and fx.mid is end:
                    FenXing.append(fxs, fx)
                    Line.append(bis, bi)
                    if _from == "analyzer":
                        bdp(f"Bi. append: {bi}")
                        observer and observer.notify(bi, Command.Append("Bi"))
                else:
                    # 2024 05 21 修正
                    if len(fxs) < 3:
                        return
                    _bars = bars[bars.index(last.mid) :]
                    _fx, _bi = Bi.analysis_one(_bars, level, config, observer)
                    if _bi is None:
                        return

                    start = fxs[-3]
                    end = _bi.start
                    nb = Bi(None, start, end, Bi.get_elements(bars, start, end), False, config)
                    if not nb.check():
                        return
                    # print(_bi)
                    pop()
                    Bi.analyzer(_bi.start, fxs, bis, bars, _from, level + 1, config, observer)

            else:
                ...
                # GD or DG
                if (last.shape is Shape.G and fx.shape is Shape.D and fx.right.high > last.speck) or (last.shape is Shape.D and fx.shape is Shape.G and fx.right.low < last.speck):
                    pop()

        elif (last.shape is Shape.G and (fx.shape is Shape.S or fx.shape is Shape.G)) or (last.shape is Shape.D and (fx.shape is Shape.X or fx.shape is Shape.D)):
            if last.shape is Shape.G:
                func = min

                def okey(o):
                    return o.low
            else:
                func = max

                def okey(o):
                    return o.high

            if fx.shape is Shape.S:
                speck = fx.right.high
            elif fx.shape is Shape.X:
                speck = fx.right.low
            else:
                speck = fx.speck

            if (last.shape is Shape.G and last.speck < speck) or (last.shape is Shape.D and last.speck > speck):
                pop()
                if fxs:
                    last = fxs[-1]
                    if fx.shape is Shape.S or fx.shape is Shape.G:
                        assert last.shape is Shape.D, last.shape
                    else:
                        assert last.shape is Shape.G, last.shape

                    new = FenXing.get_fenxing(
                        bars,
                        func(
                            Bi.get_elements(bars, last, fx),
                            key=okey,
                        ),
                    )

                    if fx.shape is Shape.S or fx.shape is Shape.G:
                        assert new.shape is Shape.D
                    else:
                        assert new.shape is Shape.G

                    if (last.shape is Shape.G and last.speck > new.mid.low) or (last.shape is Shape.D and last.speck < new.mid.high):
                        pop()
                        Bi.analyzer(new, fxs, bis, bars, _from, level + 1, config, observer)  # 处理新底
                        # print("GS修正") or print("DX修正")
                        if fx.shape in (Shape.S, Shape.X):
                            return
                        Bi.analyzer(fx, fxs, bis, bars, _from, level + 1, config, observer)  # 再处理当前顶
                        # print("GG修正") or print("DD修正")
                        return

                if fx.shape in (Shape.S, Shape.X):
                    return

                if not fxs:
                    FenXing.append(fxs, fx)
                    return

                bi = Bi(None, last, fx, Bi.get_elements(bars, last, fx), False, config)

                FenXing.append(fxs, fx)
                Line.append(bis, bi)
                if _from == "analyzer":
                    bdp(f"Bi. append: {bi}")
                    observer and observer.notify(bi, Command.Append("Bi"))

        elif (last.shape is Shape.G and fx.shape is Shape.X) or (last.shape is Shape.D and fx.shape is Shape.S):
            ...

        else:
            raise ChanException(last.shape, fx.shape)

    @staticmethod
    def analysis_one(bars: List[Bar], level: int, config: ChanConfig, observer: Observer) -> tuple[Optional[FenXing], Optional["Bi"]]:
        try:
            bars[2]
        except IndexError:
            return None, None
        bis = []
        fxs = []
        fx = None
        size = len(bars)
        for i in range(1, size - 2):
            left, mid, right = bars[i - 1], bars[i], bars[i + 1]
            fx = FenXing(left, mid, right)
            Bi.analyzer(fx, fxs, bis, bars, "tmp", level + 1, config, observer)
            if bis:
                return fx, bis[0]
        if bis:
            return fx, bis[0]
        return None, None


@final
class Duan(Line):
    __slots__ = "features", "observer"

    def __init__(
        self,
        start: FenXing,
        end: FenXing,
        elements: List[Line],
        stamp: str = "Duan",
        *,
        observer: Optional[Observer] = None,
    ):
        super().__init__(start, end, 0, elements, stamp)
        self.observer: Optional[Observer] = observer
        self.features: list[Optional[FeatureSequence]] = [None, None, None]

    def __str__(self):
        return f"{self.stamp}({self.index}, {self.direction}, has pre: {self.pre is not None}, done: {self.done}, {self.state}, {self.start}, {self.end}, size={len(self.elements)})"

    def __repr__(self):
        return str(self)

    @property
    def gap(self) -> Optional[Pillar]:
        if not self.mid:
            return
        if double_relation(self.left, self.mid).is_jump():
            hl = [self.left.start.speck, self.mid.start.speck]
            return Pillar(max(*hl), min(*hl))

    @property
    def done(self) -> bool:
        return self.right is not None

    @property
    def lmr(self) -> tuple[bool, bool, bool]:
        return self.left is not None, self.mid is not None, self.right is not None

    @property
    def state(self) -> Optional[str]:
        if self.pre is not None and self.pre.gap:
            return "老阳" if self.direction is Direction.Up else "老阴"
        return "小阳" if self.direction is Direction.Up else "少阴"

    @property
    def left(self) -> FeatureSequence:
        return self.features[0]

    @left.setter
    def left(self, feature: FeatureSequence):
        self.__feature_setter(0, feature)

    @property
    def mid(self) -> FeatureSequence:
        return self.features[1]

    @mid.setter
    def mid(self, feature: FeatureSequence):
        self.__feature_setter(1, feature)

    @property
    def right(self) -> FeatureSequence:
        return self.features[2]

    @right.setter
    def right(self, feature: FeatureSequence):
        self.__feature_setter(2, feature)

    def __feature_setter(self, offset: int, feature: Optional[FeatureSequence]):
        if feature and feature.direction == self.direction:
            raise ChanException("特征序列方向不匹配")
        features: List = self.features
        observer: Optional[Observer] = self.observer
        old = features[offset]
        features[offset] = feature

        old and observer and observer.notify(old, Command.Remove(old.stamp))
        feature and observer and observer.notify(feature, Command.Append(feature.stamp))

    def clear_features(self):
        for feature in self.features:
            if feature is not None:
                self.observer and self.observer.notify(feature, Command.Remove(feature.stamp))

    def update(self, lines: List[Line]) -> bool:
        assert self.done is True, (self, self.features)
        i = self.elements[-1].index
        while 1:
            try:
                lines.index(self.elements[-1])
                break
            except ValueError:
                self.pop_element(self.elements[-1])

        for line in lines:
            if self.elements[-1].is_next(line):
                self.add_element(line)
                if line.index == i:
                    break
        # assert size == len(self.elements)
        return self.done

    def get_next_elements(self) -> List[Line]:
        assert self.elements[0].start is self.start, (self.elements[0].start, self.start)
        elements = []
        for line in self.elements:
            if elements:
                elements.append(line)
            if line.start is self.end:
                elements.append(line)
        return elements

    def set_elements(self, elements: List[Line]):
        assert elements[0].start is self.start, (elements[0].start, self.start)
        self.clear_features()
        self.elements.clear()
        last = None
        for i in range(1, len(elements) - 1):
            pre = elements[i - 1]
            last = elements[i]
            assert last.is_previous(pre) is True
            self.add_element(pre)
            if self.done:
                print("set_elements done", i, len(elements))
        if last:
            self.add_element(last)

    def get_elements(self) -> List[Line]:
        assert self.elements[0].start is self.start, (self.elements[0].start, self.start)
        elements = []
        for obj in self.elements:
            elements.append(obj)
            if obj.end is self.end:
                break
        return elements

    def pop_element(self, line: Line) -> Line:
        duan = self
        drop = Line.pop(duan.elements, line)
        duan.left, duan.mid, duan.right = FeatureSequence.analyzer(duan.elements, duan.direction)
        return drop

    def add_element(self, line: Line):
        duan = self
        Line.append(duan.elements, line)
        if self.done:
            ...

        duan.left, duan.mid, duan.right = FeatureSequence.analyzer(duan.elements, duan.direction)
        if duan.mid is not None:
            duan.end = duan.mid.start

        if duan.direction == line.direction:
            if duan.mid is not None:
                if duan.direction == Direction.Up:
                    if duan.high < line.high:
                        duan.end = line.end
                    else:
                        duan.end = duan.mid.start
                else:
                    if duan.low > line.low:
                        duan.end = line.end
                    else:
                        duan.end = duan.mid.start
            else:
                duan.end = line.end

    @classmethod
    def new(cls, line: Line | List[Line], observer: Optional[Observer]) -> "Duan":
        if type(line) is list:
            lines = line[:]
            return Duan(line[0].start, line[2].end, lines, "Duan" if lines[0].stamp == "Bi" else lines[0].stamp + "Duan", observer=observer)
        return Duan(line.start, line.end, [line], "Duan" if line.stamp == "Bi" else line.stamp + "Duan", observer=observer)

    @classmethod
    def analyzer(cls, lines: List[Line], xds: List["Duan"], observer: Observer):
        if not lines:
            return
        try:
            lines[5]
        except IndexError:
            return

        if not xds:
            for i in range(1, len(lines) - 1):
                left, mid, right = lines[i - 1], lines[i], lines[i + 1]
                if double_relation(left, right).is_jump():
                    continue
                duan = Duan.new([left, mid, right], observer)
                Line.append(xds, duan)
                observer and observer.notify(duan, Command.Append(duan.stamp))
                return Duan.analyzer(lines, xds, observer)

        else:
            last = xds[-1]
            while 1:
                try:
                    index = lines.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    line = last.pop_element(last.elements[-1])
                    ddp("Duan.analyzer 弹出", line)

                    if not last.elements:
                        print("Duan.analyzer 无法找到", last)
                        if Line.pop(xds, last) is not None:
                            observer and observer.notify(last, Command.Remove(last.stamp))
                            last.clear_features()
                        return Duan.analyzer(lines, xds, observer)
            duan = last

            # for line in lines[index:]:
            for i in range(index, len(lines)):
                line = lines[i]
                last = duan.pre
                if last and last.elements[-1] not in lines:
                    if not last.update(lines):
                        # print("异常", last)
                        Line.pop(xds, duan)
                        observer and observer.notify(duan, Command.Remove(duan.stamp))
                        duan.clear_features()
                        return Duan.analyzer(lines, xds, observer)

                if last and last.gap and len(duan.elements) == 3:
                    if (last.direction is Direction.Up and line.high > last.high) or (last.direction is Direction.Down and line.low < last.low):
                        Line.pop(xds, duan)
                        observer and observer.notify(duan, Command.Remove(duan.stamp))
                        duan.clear_features()
                        last.add_element(line)
                        observer and observer.notify(last, Command.Modify(last.stamp))
                        # print("修正")
                        duan = last
                        continue

                duan.add_element(line)
                observer and observer.notify(duan, Command.Modify(duan.stamp))
                if duan.done:
                    elements = duan.get_next_elements()
                    duan.clear_features()
                    for feature in duan.features:
                        if feature is not None:
                            observer and observer.notify(feature, Command.Append(feature.stamp))

                    if duan.direction is Direction.Up:
                        fx = "顶分型"
                    else:
                        fx = "底分型"

                    ddp("    ", f"{fx}终结, 缺口: {duan.gap}")
                    size = len(elements)
                    if size >= 3:
                        duan = Duan.new(elements[:3], observer)
                        Line.append(xds, duan)
                        observer and observer.notify(duan, Command.Append(duan.stamp))
                        for feature in duan.features:
                            if feature is not None:
                                observer and observer.notify(feature, Command.Append(feature.stamp))

                        return Duan.analyzer(lines, xds, observer)

                    duan = Duan.new(elements, observer)
                    Line.append(xds, duan)
                    observer and observer.notify(duan, Command.Append(duan.stamp))
                    for feature in duan.features:
                        if feature is not None:
                            observer and observer.notify(feature, Command.Append(feature.stamp))


class BaseAnalyzer(Observer):
    __slots__ = "symbol", "freq", "ws", "last_raw_bar", "raws", "news", "fxs", "bis", "xds", "bzss", "dzss", "cache", "config"

    def __init__(self, symbol: str, freq: SupportsInt, ws: WebSocket = None):
        self.symbol: str = symbol
        self.freq: int = int(freq)
        self.ws = ws
        self.last_raw_bar: Optional[Bar] = None
        self.raws: list[Bar] = []
        self.news: list[Bar] = []
        self.fxs: list[FenXing] = []
        self.bis: list[Bi] = []
        self.xds: list[Duan] = []
        self.bzss: list[ZhongShu] = []
        self.dzss: list[ZhongShu] = []
        self.cache = dict()
        self.config = ChanConfig()

        self.zs = []

    def notify(self, obj: Any, cmd: Command):
        if not self.config.ANALYZER_SHON_TV:
            return
        message = dict()
        message["stamp"] = obj.stamp if hasattr(obj, "stamp") else obj.__class__.__name__

        if type(obj) is Bar:
            message["type"] = "realtime"
            message["timestamp"] = str(obj.dt)
            message["open"] = obj.open
            message["high"] = obj.high
            message["low"] = obj.low
            message["close"] = obj.close
            message["volume"] = obj.volume

        if type(obj) is Bi:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(hash(obj))
            message["name"] = "trend_line"
            message["points"] = [{"time": int(obj.start.dt.timestamp()), "price": obj.start.speck}, {"time": int(obj.end.dt.timestamp()), "price": obj.end.speck}]
            message["options"] = {"shape": "trend_line", "text": obj.stamp}
            message["properties"] = {"linecolor": "#CC62FF", "linewidth": 2, "title": f"{obj.stamp}-{obj.index}"}

            if cmd.cmd == Command.APPEND:
                ...
            elif cmd.cmd == Command.MODIFY:
                ...
            elif cmd.cmd == Command.REMOVE:
                ...

        if type(obj) is Duan:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(id(obj))
            message["name"] = "trend_line"
            message["points"] = [{"time": int(obj.start.dt.timestamp()), "price": obj.start.speck}, {"time": int(obj.end.dt.timestamp()), "price": obj.end.speck}]
            message["options"] = {"shape": "trend_line", "text": obj.stamp}
            message["properties"] = {"linecolor": "#F1C40F" if obj.stamp == "Duan" else "#00C40F", "linewidth": 3, "title": f"{obj.stamp}-{obj.index}", "text": obj.stamp}

        if type(obj) is Interval:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(id(obj))
            message["name"] = "rectangle"
            message["points"] = [{"time": int(obj.elements[0].dt.timestamp()), "price": obj.high}, {"time": int(obj.elements[-1].dt.timestamp()), "price": obj.low}]
            message["options"] = {"shape": "rectangle", "text": "nb"}
            message["properties"] = {"color": "#00C40F", "backgroundColor": "#00C40F"}

        if type(obj) is ZhongShu:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(hash(obj))
            message["name"] = "rectangle"
            if cmd.cmd == Command.APPEND or cmd.cmd == Command.MODIFY:
                points = (
                    [
                        {"time": int(obj.start.dt.timestamp()), "price": obj.zg},
                        {
                            "time": int(obj.elements[-1].end.mid.dt.timestamp()),
                            "price": obj.zd,
                        },
                    ]
                    if len(obj.elements) <= 3
                    else [
                        {"time": int(obj.start.dt.timestamp()), "price": obj.zg},
                        {
                            "time": int(obj.elements[-1].start.mid.dt.timestamp()),
                            "price": obj.zd,
                        },
                    ]
                )

            elif cmd.cmd == Command.REMOVE:
                points = []
            else:
                points = []

            message["points"] = points
            message["options"] = {"shape": "rectangle", "text": obj.stamp}
            message["properties"] = {
                "color": "#993333" if obj.direction is Direction.Down else "#99CC99",  # 上下上 为 红色，反之为 绿色
                "linewidth": 1 if obj.elements[0].stamp == "Bi" else 2,
                "title": f"{obj.stamp}-{obj.index}",
                "text": obj.stamp,
            }

        if type(obj) is FeatureSequence:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(id(obj))
            message["name"] = "trend_line"
            start = obj.start.dt
            end = obj.end.dt
            if start > end:
                start, end = end, start
            message["points"] = [{"time": int(start.timestamp()), "price": obj.start.speck}, {"time": int(end.timestamp()), "price": obj.end.speck}]
            message["options"] = {"shape": "trend_line", "text": obj.stamp}
            message["properties"] = {
                "linecolor": "#FFFFFF" if obj.direction.reversal() is Direction.Down else "#fbc02d",
                "linewidth": 4,
                "linestyle": 1,
                # "showLabel": True,
                "title": obj.stamp,
            }

        if cmd.cmd == Command.APPEND:
            ...
        elif cmd.cmd == Command.MODIFY:
            ...
        elif cmd.cmd == Command.REMOVE:
            ...

        # future = asyncio.ensure_future(self.ws.send_text('{"type": "websocket.send", "text": data}'))
        # self.loop.run_until_complete(future)
        if self.ws is not None and self.config.ANALYZER_SHON_TV:
            asyncio.set_event_loop(self.loop)
            asyncio.ensure_future(self.ws.send_text(json.dumps(message)))
        # print(message)
        return

    @final
    def step(
        self,
        dt: Union[datetime, int, str],
        open_: Union[float, str],
        high: Union[float, str],
        low: Union[float, str],
        close: Union[float, str],
        volume: Union[float, str],
    ) -> None:
        if type(dt) is datetime.datetime:
            ...
        elif isinstance(dt, str):
            dt: datetime.datetime = datetime.datetime.fromtimestamp(int(dt))
        elif isinstance(dt, int):
            dt: datetime.datetime = datetime.datetime.fromtimestamp(dt)
        else:
            raise ChanException("类型不支持", type(dt))
        open_ = float(open_)
        high = float(high)
        low = float(low)
        close = float(close)
        volume = float(volume)

        index = 0

        last = Bar.creat_raw_bar(
            dt=dt,
            o=open_,
            h=high,
            low=low,
            c=close,
            v=volume,
            i=index,
        )
        self.push(last)

    @final
    def push(self, bar: Bar):
        if self.last_raw_bar is not None:
            bar.index = self.last_raw_bar.index + 1
        self.last_raw_bar = bar
        # self.raws.append(bar)
        pre = None
        if self.news:
            try:
                pre = self.news[-2]
            except IndexError:
                pass
            nb = Bar.merger(pre, self.news[-1], bar)
            if nb is not None:
                if self.config.ANALYZER_CALC_MACD:
                    MACD.calc(self.news[-1], nb)
                self.news.append(nb)
            else:
                if self.config.ANALYZER_CALC_MACD and pre:
                    MACD.calc(pre, self.news[-1])
        else:
            nb = bar.to_new_bar(None)
            nb.macd = MACD(fast_ema=nb.close, slow_ema=nb.close, dif=0.0, dea=0.0, fastperiod=self.config.MACD_FAST_PERIOD, slowperiod=self.config.MACD_SLOW_PERIOD, signalperiod=self.config.MACD_SIGNAL_PERIOD)
            self.news.append(nb)

        # Interval.analyzer(self.news, self.zs, self)

        self.notify(self.news[-1], Command.Append("NewBar"))

        # left, mid, right = None, None, None
        try:
            left, mid, right = self.news[-3:]
        except ValueError:
            return

        (shape, _, _) = triple_relation(left, mid, right)
        mid.shape = shape
        fx = FenXing(left, mid, right)
        if self.ws is not None and self.config.ANALYZER_SHON_TV:
            time.sleep(self.TIME)

        if not self.config.ANALYZER_CALC_BI:
            return

        Bi.analyzer(fx, self.fxs, self.bis, self.news, "analyzer", 0, self.config, self)
        # return
        if self.bis and self.cache.get("bi", None) is self.bis[-1]:
            return
        if self.bis:
            self.cache["bi"] = self.bis[-1]
        if self.config.ANALYZER_CALC_BI_ZS:
            ZhongShu.analyzer(self.bis, self.bzss, self)

        if self.config.ANALYZER_CALC_XD:
            try:
                Duan.analyzer(self.bis, self.xds, self)
            except Exception as e:
                traceback.print_exc()
                xds = self.xds[-3:]
                news = self.news[xds[0].start.left.index :]
                Bar.bars_save_as_dat(f"./templates/{self.symbol}_duan_exception-{self.freq}-{int(news[0].dt.timestamp())}-{int(news[-1].dt.timestamp())}.nb", news)
                raise e
            if self.xds and self.cache.get("xd", None) is self.xds[-1]:
                return
            if self.xds:
                self.cache["xd"] = self.xds[-1]
            if self.config.ANALYZER_CALC_XD_ZS:
                ZhongShu.analyzer(self.xds, self.dzss, self)

    @classmethod
    def read_from_dat_file(cls, path: str) -> "BaseAnalyzer":
        name = Path(path).name.split(".")[0]
        symbol, freq, s, e = name.split("-")
        size = struct.calcsize(">6d")
        obj = cls(symbol, int(freq))
        with open(path, "rb") as f:
            # if not f.seek(size * 1000000):
            #    return obj
            start = time.time()
            half = start
            length = 0
            with mmap.mmap(f.fileno(), size * 6000000, access=mmap.ACCESS_READ) as mm:
                # for buffer in chunked_file_reader(f):

                while buffer := mm.read(size * 10000):
                    try:
                        for i in range(len(buffer) // size):
                            bar = Bar.from_be_bytes(buffer[i * size : i * size + size], stamp="RawBar")
                            obj.push(bar)
                            length += 1
                            if length % 100000 == 0:
                                print(length, f" read in {time.time() - start}s")
                                print(f"news:{len(obj.news)}")
                                print(f"bis: {len(obj.bis)}")
                                print(f"xds: {len(obj.xds)}")
                                print(f"bzss:{len(obj.bzss)}")
                                print(f"dzss:{len(obj.dzss)}")
                                print(f"{time.time() - half}s")
                                print(f"{time.time() - start}s")
                                half = time.time()
                    except KeyboardInterrupt:
                        print(traceback.format_exc())
                        break
            print(f"\nnews:{len(obj.news)} read in {time.time() - start}s")
            print(f"bis: {len(obj.bis)}")
            print(f"xds: {len(obj.xds)}")
            print(f"bzss:{len(obj.bzss)}")
            print(f"dzss:{len(obj.dzss)}")
            print(dir(obj.config))

        return obj


class Generator(BaseAnalyzer):
    def __init__(self, symbol: str, freq: int, ws: WebSocket):
        super().__init__(symbol, freq, ws)

    def save_nb_file(self):
        Bar.bars_save_as_dat(f"./templates/{self.symbol}-{self.freq}-{int(self.news[0].dt.timestamp())}-{int(self.news[-1].dt.timestamp())}.nb", self.news)

    def load_nb_file(self, path: str):
        with open(path, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                bar = Bar.from_be_bytes(buffer[i * size : i * size + size])
                self.push(bar)

    def push_new_bar(self, nb: Bar):
        self.news.append(nb)
        # Interval.analyzer(self.news, self.zs, self)
        self.notify(self.news[-1], Command.Append("NewBar"))
        # return
        # left, mid, right = None, None, None
        try:
            left, mid, right = self.news[-3:]
        except ValueError:
            return

        (shape, _, _) = triple_relation(left, mid, right)
        mid.shape = shape
        fx = FenXing(left, mid, right)
        if self.ws is not None and self.config.ANALYZER_SHON_TV:
            time.sleep(self.TIME)

        if not self.config.ANALYZER_CALC_BI:
            return

        Bi.analyzer(fx, self.fxs, self.bis, self.news, "analyzer", 0, self.config, self)
        # return
        if self.bis and self.cache.get("bi", None) is self.bis[-1]:
            return
        if self.bis:
            self.cache["bi"] = self.bis[-1]
        if self.config.ANALYZER_CALC_BI_ZS:
            ZhongShu.analyzer(self.bis, self.bzss, self)

        if self.config.ANALYZER_CALC_XD:
            try:
                Duan.analyzer(self.bis, self.xds, self)
            except Exception as e:
                traceback.print_exc()
                xds = self.xds[-3:]
                news = self.news[xds[0].start.left.index :]
                Bar.bars_save_as_dat(f"./templates/{self.symbol}_duan_exception_byGenerator-{self.freq}-{int(news[0].dt.timestamp())}-{int(news[-1].dt.timestamp())}.nb", news)
                raise e
            if self.xds and self.cache.get("xd", None) is self.xds[-1]:
                return
            if self.xds:
                self.cache["xd"] = self.xds[-1]
            if self.config.ANALYZER_CALC_XD_ZS:
                ZhongShu.analyzer(self.xds, self.dzss, self)

    @classmethod
    def generator(cls, points: List[int | dict], seconds=300):
        news = []

        def append(array, new):
            if not array:
                array.append(new)
                return
            if double_relation(array[-1], new) is Direction.Left:
                array[-1] = new
            elif double_relation(array[-1], new) is Direction.Right:
                print(array[-1], new)
            else:
                print(double_relation(array[-1], new))
                array.append(new)

        dt = datetime.datetime(2008, 8, 8)
        offset = datetime.timedelta(seconds=seconds)
        index = 0
        for i in range(1, len(points)):
            if type(points[i]) is dict:
                o = int(points[i - 1]["price"])
                c = int(points[i]["price"])
            else:
                o = int(points[i - 1])
                c = int(points[i])
            direction = Direction.Up if o < c else Direction.Down
            high = max(o, c)
            low = min(o, c)
            d = high - low
            m = d / 5
            if direction == Direction.Up:
                nb = Bar.creat_new_bar(dt, low + m, low, direction, 8, index, None)
                append(news, nb)
                dt = dt + offset
                for dd in [Direction.NextUp] * 4:
                    nb = Bar.generate(nb, dd, seconds, True)
                    append(news, nb)
                    dt = dt + offset
            else:
                nb = Bar.creat_new_bar(dt, high, low + m * 4, direction, 8, index, None)
                append(news, nb)
                dt = dt + offset
                for dd in [Direction.NextDown] * 4:
                    nb = Bar.generate(nb, dd, seconds, True)
                    append(news, nb)
                    dt = dt + offset

        lines = Lines(news)
        lines.reset_line_index()
        return news


class Bitstamp(BaseAnalyzer):
    def __init__(self, symbol: str, freq: SupportsInt, ws: WebSocket = None):
        super().__init__(symbol, freq, ws)

    def init(self, size):
        self.left_date_timestamp: int = int(datetime.datetime.now().timestamp() * 1000)
        left = int(self.left_date_timestamp / 1000) - self.freq * size
        if left < 0:
            raise ChanException
        _next = left
        while 1:
            data = self.ohlc(self.symbol, self.freq, _next, _next := _next + self.freq * 1000)
            if not data.get("data"):
                print(data)
                raise ChanException
            for bar in data["data"]["ohlc"]:
                try:
                    self.step(
                        bar["timestamp"],
                        bar["open"],
                        bar["high"],
                        bar["low"],
                        bar["close"],
                        bar["volume"],
                    )
                except ChanException as e:
                    # continue
                    # self.save_file()
                    raise e

            # start = int(data["data"]["ohlc"][0]["timestamp"])
            end = int(data["data"]["ohlc"][-1]["timestamp"])

            _next = end
            if len(data["data"]["ohlc"]) < 100:
                break

    @staticmethod
    def ohlc(pair: str, step: int, start: int, end: int, length: int = 1000) -> Dict:
        proxies = {
            "http": "http://127.0.0.1:11809",
            "https": "http://127.0.0.1:11809",
        }
        s = requests.Session()

        s.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "content-type": "application/json",
        }
        url = f"https://www.bitstamp.net/api/v2/ohlc/{pair}/?step={step}&limit={length}&start={start}&end={end}"
        resp = s.get(url, timeout=5, proxies=proxies)
        js = resp.json()
        # print(json)
        return js


def main_bitstamp(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = Freq.m5, ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Bitstamp(symbol, freq=int(freq), ws=ws)
        bitstamp.init(int(limit))
        return bitstamp

    return func


def gen(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = Freq.m5, ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Generator(symbol + "_gen", freq=int(freq), ws=ws)
        bitstamp.config.BI_JUMP = False
        dt = datetime.datetime(2008, 8, 8)
        nb = Bar.creat_new_bar(dt, 10000, 9900, Direction.Up, 8.8, 0)
        bitstamp.push_new_bar(nb)
        for direction in Direction.generator(int(limit), [Direction.Up, Direction.JumpUp, Direction.NextUp, Direction.Down, Direction.JumpDown, Direction.NextDown]):
            nb = Bar.generate(nb, direction, int(freq))
            bitstamp.push_new_bar(nb)

        for duan in bitstamp.xds:
            if duan.gap:
                bitstamp.save_nb_file()
                break
        return bitstamp

    return func


def gen2(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = Freq.m5, ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Generator(symbol, freq=int(freq), ws=ws)
        bitstamp.config.BI_JUMP = False
        a = [
            {"price": 11070.490547079706, "time": 1218098700},
            {"price": 11477.076230434637, "time": 1218100200},
            {"price": 10311.530604817166, "time": 1218102000},
            {"price": 10728.958573061562, "time": 1218103200},
            {"price": 9856.15463945964, "time": 1218104700},
            {"price": 10132.632904140995, "time": 1218105900},
            {"price": 9969.998630799022, "time": 1218107700},
            {"price": 10224.792325701446, "time": 1218109200},
            {"price": 9682.168101337797, "time": 1218111900},
            {"price": 9891.448028901257, "time": 1218114000},
        ]
        for nb in Generator.generator(a, int(freq)):
            bitstamp.push_new_bar(nb)

        for duan in bitstamp.xds:
            if duan.gap:
                bitstamp.save_nb_file()
                break

    return func


app = FastAPI()
# priority_queue = asyncio.PriorityQueue()
# queue = Observer.queue  # asyncio.Queue()
app.mount(
    "/charting_library",
    StaticFiles(directory="charting_library"),
    name="charting_library",
)
templates = Jinja2Templates(directory="templates")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.analyzers: Dict[str, BaseAnalyzer] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.analyzers:
            del self.analyzers[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    def get_analyzer(self, client_id: str) -> Optional[BaseAnalyzer]:
        return self.analyzers.get(client_id)

    def set_analyzer(self, client_id: str, analyzer: BaseAnalyzer):
        self.analyzers[client_id] = analyzer


# 创建连接管理器实例
manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "ready":
                # 初始化分析器
                symbol = message["symbol"]
                freq = message["freq"]
                limit = message["limit"]

                # 停止现有线程
                if Observer.thread is not None:
                    tmp = Observer.thread
                    Observer.thread = None
                    tmp.join(1)
                    time.sleep(1)

                # 创建新的analyzer实例并运行
                if message["generator"] == "True":
                    analyzer_func = gen(symbol=symbol, freq=freq, limit=limit, ws=websocket)
                else:
                    analyzer_func = main_bitstamp(symbol=symbol, freq=freq, limit=limit, ws=websocket)

                def thread_func():
                    analyzer = analyzer_func()
                    manager.set_analyzer(client_id, analyzer)

                Observer.thread = Thread(target=thread_func)
                Observer.thread.start()

            elif message["type"] == "query_by_index":
                analyzer = manager.get_analyzer(client_id)
                if analyzer:
                    data_type = message.get("data_type")
                    index = int(message.get("index").split("-")[-1])

                    try:
                        if data_type == "Bi":
                            bi = analyzer.bis[index]
                            data = {
                                "index": bi.index,
                                "start_time": bi.start.dt.timestamp(),
                                "end_time": bi.end.dt.timestamp(),
                                "start_price": bi.start.speck,
                                "end_price": bi.end.speck,
                                "direction": str(bi.direction),
                                "angle": bi.calc_angle(),
                                "speed": bi.calc_speed(),
                                "measure": bi.calc_measure(),
                            }
                        elif data_type == "Duan":
                            duan = analyzer.xds[index]
                            data = {
                                "index": duan.index,
                                "start_time": duan.start.dt.timestamp(),
                                "end_time": duan.end.dt.timestamp(),
                                "start_price": duan.start.speck,
                                "end_price": duan.end.speck,
                                "direction": str(duan.direction),
                                "angle": duan.calc_angle(),
                                "speed": duan.calc_speed(),
                                "measure": duan.calc_measure(),
                            }
                        else:
                            raise ValueError(f"不支持的数据类型: {data_type}")

                        await manager.send_message(client_id, {"type": "query_result", "success": True, "data_type": data_type, "data": data})

                    except IndexError:
                        await manager.send_message(client_id, {"type": "query_result", "success": False, "message": f"索引 {index} 超出范围"})
                    except Exception as e:
                        await manager.send_message(client_id, {"type": "query_result", "success": False, "message": str(e)})

    except WebSocketDisconnect:
        manager.disconnect(client_id)


@app.get("/")
async def main_page(
    request: Request,
    nol: str = "network",
    exchange: str = "bitstamp",
    symbol: str = "btcusd",
    step: int = 300,
    limit: int = 500,
    generator: bool = False,
):
    resolutions = {
        60: "1",
        180: "3",
        300: "5",
        900: "15",
        1800: "30",
        3600: "1H",
        7200: "2H",
        14400: "4H",
        21600: "6H",
        43200: "12H",
        86400: "1D",
        259200: "3D",
    }
    if resolutions.get(step) is None:
        return resolutions

    # Observer.CAN = True
    return templates.TemplateResponse("index.html", {"request": request, "exchange": exchange, "symbol": symbol, "interval": resolutions.get(step), "limit": str(limit), "step": str(step), "generator": generator})


if __name__ == "__main__":
    BaseAnalyzer.read_from_dat_file("btcusd-60-0-0.dat")
