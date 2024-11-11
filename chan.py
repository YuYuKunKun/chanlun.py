"""
# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 16:45
# @Author  : YuYuKunKun
# @File    : chan.py
"""

import json
import mmap
import time
import struct
import asyncio
import datetime
import traceback

from enum import Enum
from pathlib import Path
from threading import Thread
from functools import wraps
from typing import List, Self, Optional, Tuple, final, Dict, Any, Set, Final, SupportsInt, TypeVar, Union
from abc import ABCMeta, abstractmethod

import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from termcolor import colored

# __all__ = ["Line", "Bar", "NewBar", "RawBar", "Bi", "Duan", "ZhongShu", "FenXing", "BaseAnalyzer"]


SupportsHL = Union["Line", "Bar", "NewBar", "RawBar", "Bi", "Duan", "ZhongShu", "FenXing", "Bar", "Interval"]


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

    Left = "左包右"  # 顺序包含
    Right = "右包左"  # 逆序包含

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

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
            case Direction.Left:
                return Direction.Right
            case Direction.Right:
                return Direction.Left

    @staticmethod
    def includes() -> tuple:
        return Direction.Left, Direction.Right

    @staticmethod
    def jumps() -> tuple:
        return Direction.JumpUp, Direction.JumpDown


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

    elif (left.low > right.low) and (left.high > right.high):
        relation = Direction.Down  # "下跌"
        if left.low > right.high:
            relation = Direction.JumpDown  # "跳跌"

    return relation


def triple_relation(left: SupportsHL, mid: SupportsHL, right: SupportsHL, use_right: bool = False) -> tuple[Optional[Shape], tuple[Direction, Direction]]:
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

    shape = None
    lm = double_relation(left, mid)
    mr = double_relation(mid, right)
    # lr = double_relation(left, right)
    match (lm, mr):
        case (Direction.Left, _):
            raise ChanException("顺序包含 lm")
        case (_, Direction.Left):
            raise ChanException("顺序包含 mr")

        case (Direction.Up | Direction.JumpUp, Direction.Up | Direction.JumpUp):
            shape = Shape.S
        case (Direction.Up | Direction.JumpUp, Direction.Down | Direction.JumpDown):
            shape = Shape.G
        case (Direction.Up | Direction.JumpUp, Direction.Right) if use_right:
            shape = Shape.S

        case (Direction.Down | Direction.JumpDown, Direction.Up | Direction.JumpUp):
            shape = Shape.D
        case (Direction.Down | Direction.JumpDown, Direction.Down | Direction.JumpDown):
            shape = Shape.X
        case (Direction.Down | Direction.JumpDown, Direction.Right) if use_right:
            shape = Shape.X

        case (Direction.Right | Direction.Up, Direction.JumpUp) if use_right:
            shape = Shape.D
        case (Direction.Right | Direction.Down, Direction.JumpDown) if use_right:
            shape = Shape.G
        case (Direction.Right, Direction.Right) if use_right:
            shape = Shape.T

    if shape is None:
        print(colored("triple_relation: ", "red"), shape, (lm, mr), left, mid, right)

    return shape, (lm, mr)


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
    def Append(cls, stamp: str) -> "Command":
        return Command(cls.APPEND, stamp)

    @classmethod
    def Modify(cls, stamp: str) -> "Command":
        return Command(cls.MODIFY, stamp)

    @classmethod
    def Remove(cls, stamp: str) -> "Command":
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


@final
class ChanConfig:
    __slots__ = "ANALYZER_CALC_BI", "ANALYZER_CALC_BI_ZS", "ANALYZER_CALC_XD", "ANALYZER_CALC_XD_ZS", "ANALYZER_SHON_TV", "BI_EQUAL", "BI_FENGXING", "BI_JUMP", "BI_LENGTH", "MACD_FAST_PERIOD", "MACD_SIGNAL_PERIOD", "MACD_SLOW_PERIOD"

    def __init__(self):
        self.BI_LENGTH = 5  # 成BI最低长度
        self.BI_JUMP = True  # 跳空是否判定为 NewBar
        self.BI_EQUAL = True  # True: 一笔终点存在多个终点时，取最后一个, False: 用max/min时只会取第一个值，会有这个情况 当首个出现时 小于[BI_LENGTH]而后个则大于[BI_LENGTH]但max/min函数不会取后一个. 例子: bitstamp btcusd 30m [2024-06-03 17:00]至[2024-06-05 01:00] 中 [NewBar(63, 2024-06-03 22:30:00, 69318.0, 68553.0, D, 2), NewBar(94, 2024-06-04 17:30:00, 68768.0, 68553.0, D, 1)]
        self.BI_FENGXING = False  # True: 一笔起始分型高低包含整支笔对象则不成笔, False: 只判断分型中间数据是否包含

        self.ANALYZER_CALC_BI = True  # 是否计算BI
        self.ANALYZER_CALC_XD = True  # 是否计算XD
        self.ANALYZER_CALC_BI_ZS = True  # 是否计算BI中枢
        self.ANALYZER_CALC_XD_ZS = True  # 是否计算XD中枢
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
        return MACD(_fast_ema, _slow_ema, _dif, _dea, fastperiod=pre.macd.fastperiod, slowperiod=pre.macd.slowperiod, signalperiod=pre.macd.signalperiod)


class Observer(metaclass=ABCMeta):
    thread = None
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    TIME = 0.05

    @abstractmethod
    def notify(self, obj: Any, cmd: Command): ...


class Interval:
    __slots__ = "elements", "__high", "__low"

    def __init__(self, elements: List, high, low):
        self.elements = elements
        self.__high = high
        self.__low = low

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

    @classmethod
    def new(cls, elements) -> Optional["Interval"]:
        if len(elements) < 3:
            return

        lr = double_relation(elements[0], elements[2])
        if lr in Direction.jumps():
            return

        lm = double_relation(elements[0], elements[1])
        if lm in Direction.jumps():
            return

        mr = double_relation(elements[1], elements[2])
        if mr in Direction.jumps():
            return

        high = min([hl.high for hl in elements[:3]])
        low = max([hl.low for hl in elements[:3]])
        return cls(elements, high, low)

    @classmethod
    def analyzer(cls, hls: List, intervals: List["Interval"]):
        if not intervals:
            for i in range(1, len(hls) - 1):
                new = cls.new([hls[i - 1], hls[i], hls[i + 1]])
                if new is not None:
                    intervals.append(new)
                    return cls.analyzer(hls, intervals)

        else:
            last = intervals[-1]
            tmp = cls.new(last.elements)
            if tmp is None:
                intervals.pop()
                return cls.analyzer(hls, intervals)
            else:
                if last.high == tmp.high and last.low == tmp.low:
                    ...
                else:
                    intervals.pop()
                    return cls.analyzer(hls, intervals)

            while 1:
                try:
                    index = hls.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    if len(last) > 3:
                        drop = last.elements.pop()
                    else:
                        intervals.pop()
                        return cls.analyzer(hls, intervals)

            elements = []
            for hl in hls[index:]:
                if double_relation(last, hl) in Direction.jumps():
                    elements.append(hl)
                else:
                    if not elements:
                        last.elements.append(hl)
                    else:
                        elements.append(hl)

                if len(elements) >= 3:
                    new = cls.new(elements[:])
                    if new is None:
                        elements.pop(0)
                    else:
                        intervals.append(new)
                        last = new
                        elements = []


class Bar:
    __slots__ = "index", "macd", "__timestamp", "__high", "__low", "__volume", "__direction"

    def __init__(self, ts: int, o: float, h: float, low: float, c: float, v: float, i: int):
        self.__timestamp = ts
        self.__high = h
        self.__low = low
        self.__volume = v
        self.__direction = Direction.Up if o < c else Direction.Down
        self.index = i
        self.macd = MACD(c, c, 0.0, 0.0)

    @property
    def open(self) -> float:
        return self.low if self.direction is Direction.Up else self.high

    @property
    def high(self) -> float:
        return self.__high

    @property
    def low(self) -> float:
        return self.__low

    @property
    def close(self) -> float:
        return self.high if self.direction is Direction.Up else self.low

    @property
    def volume(self) -> float:
        return self.__volume

    @property
    def timestamp(self) -> int:
        return self.__timestamp

    @property
    def direction(self) -> Direction:
        return self.__direction

    @property
    def dt(self) -> datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    def __str__(self):
        return f"{self.__class__.__name__}({self.dt}, {self.high}, {self.low}, index={self.index})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.dt}, {self.high}, {self.low}, index={self.index})"

    def __bytes__(self) -> bytes:
        return self.to_be_bytes()

    def to_be_bytes(self) -> bytes:
        return struct.pack(
            ">6d",
            int(self.dt.timestamp()),
            round(self.open, 8),
            round(self.high, 8),
            round(self.low, 8),
            round(self.close, 8),
            round(self.volume, 8),
        )

    @classmethod
    def from_be_bytes(cls, bs: bytes) -> "Bar":
        timestamp, _open, high, low, close, vol = struct.unpack(">6d", bs[: struct.calcsize(">6d")])
        return cls(
            ts=timestamp,
            o=_open,
            h=high,
            low=low,
            c=close,
            v=vol,
            i=0,
        )


class RawBar:
    __slots__ = "open", "high", "low", "close", "volume", "dt", "index", "macd"

    def __init__(self, dt: datetime, o: float, h: float, low: float, c: float, v: float, i: int):
        self.dt: datetime = dt
        self.open: float = o
        self.high: float = h
        self.low: float = low
        self.close: float = c
        self.volume: float = v
        self.index: int = i
        self.macd = MACD(c, c, 0.0, 0.0)

    @property
    def direction(self):
        if self.open > self.close:
            return Direction.Down
        else:
            return Direction.Up

    def __str__(self):
        return f"{self.__class__.__name__}({self.dt}, {self.high}, {self.low}, index={self.index})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.dt}, {self.high}, {self.low}, index={self.index})"

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

    def to_new_bar(self, pre) -> "NewBar":
        return NewBar(
            raw=self,
            pre=pre,
        )

    @classmethod
    def from_be_bytes(cls, buf: bytes) -> "RawBar":
        timestamp, open_, high, low, close, vol = struct.unpack(">6d", buf[: struct.calcsize(">6d")])
        return cls(
            dt=datetime.datetime.fromtimestamp(timestamp),
            o=open_,
            h=high,
            low=low,
            c=close,
            v=vol,
            i=0,
        )


class NewBar:
    __slots__ = "index", "dt", "high", "low", "__shape", "__raw_start_index", "raw_end_index", "__direction", "volume", "macd"

    def __init__(
        self,
        raw: RawBar,
        pre: Optional["NewBar"] = None,
    ):
        self.index: int = 0
        self.dt: datetime = raw.dt
        self.high: float = raw.high
        self.low: float = raw.low
        self.__shape: Shape = Shape.S

        if raw.direction is Direction.Up:
            self.__shape = Shape.S
        else:
            self.__shape = Shape.X

        self.__raw_start_index: int = raw.index
        self.raw_end_index: int = raw.index
        self.__direction: Direction = raw.direction
        self.volume: float = raw.volume
        self.macd = MACD(self.close, self.close, 0.0, 0.0)

        if pre is not None:
            self.index = pre.index + 1

            if double_relation(pre, self) in (Direction.Left, Direction.Right):
                raise ChanException(f"\n    {double_relation(pre, self)}\n    {pre},\n    {self}")

    def __str__(self):
        return f"{self.__class__.__name__}({self.index}, {self.dt}, {self.high}, {self.low}, {self.shape})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index}, {self.dt}, {self.high}, {self.low}, {self.shape})"

    @property
    def raw_start_index(self) -> int:
        return self.__raw_start_index

    @property
    def timestamp(self) -> int:
        return int(self.dt.timestamp())

    @property
    def direction(self) -> Direction:
        return self.__direction

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

    @property
    def shape(self) -> Optional[Shape]:
        return self.__shape

    @shape.setter
    def shape(self, shape: Shape):
        self.__shape = shape

    @property
    def open(self) -> float:
        return self.high if self.direction == Direction.Down else self.low

    @property
    def close(self) -> float:
        return self.low if self.direction == Direction.Down else self.high

    def to_bar(self) -> Bar:
        return Bar(self.dt.timestamp(), self.open, self.high, self.low, self.close, self.volume, self.index)

    @classmethod
    def get_fx(cls, bars: List["NewBar"], bar: "NewBar") -> "FenXing":
        i = bars.index(bar)
        return FenXing(bars[i - 1], bars[i], bars[i + 1])

    @classmethod
    def merger(cls, pre: Optional["NewBar"], bar: "NewBar", next_bar: RawBar) -> Optional["NewBar"]:
        relation = double_relation(bar, next_bar)
        if relation in (Direction.JumpUp, Direction.JumpDown, Direction.Up, Direction.Down):
            nb = next_bar.to_new_bar(bar)
            nb.index = bar.index + 1
            return nb

        if next_bar.index - 1 != bar.raw_end_index:
            raise ChanException(f"NewBar.merger: 不可追加不连续元素 bar.raw_end_index: {bar.raw_end_index}, next_bar.index: {next_bar.index}.")

        direction = Direction.Up
        if pre is not None:
            if double_relation(pre, bar) in (Direction.Down, Direction.JumpDown):
                direction = Direction.Down

        func = max
        if direction is Direction.Down:
            func = min
        bar.high = func(bar.high, next_bar.high)
        bar.low = func(bar.low, next_bar.low)
        bar.raw_end_index = next_bar.index

        if pre is not None:
            bar.index = pre.index + 1

        return None


class FenXing:
    __slots__ = "index", "left", "mid", "right"

    def __init__(self, left: NewBar, mid: NewBar, right: NewBar, index: int = 0):
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
        shape, (_, _) = triple_relation(self.left, self.mid, self.right)
        return shape

    def get_relations(self) -> (Direction, Direction):
        _, (lm, mr) = triple_relation(self.left, self.mid, self.right)
        return lm, mr

    @staticmethod
    def get_fenxing(bars: List[NewBar], mid: NewBar) -> "FenXing":
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
    __slots__ = "index", "__start", "__end", "__stamp", "__elements"

    def __init__(self, start: FenXing, end: FenXing, index: int, elements: List | Set, stamp: str = "Line"):
        self.index: int = index
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
    def elements(self) -> List | Set:
        return self.__elements

    @elements.setter
    def elements(self, elements: List):
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
            raise ChanException("Line.append 不连续")

        if lines:
            line.index = lines[-1].index + 1

        lines.append(line)

    @classmethod
    def pop(cls, lines: List["Line"], line: "Line") -> Optional["Line"]:
        if not lines:
            return

        if lines[-1] is line:
            return lines.pop()
        raise ChanException("Line.pop 弹出数据不在列表中")


@final
class FeatureSequence(Line):
    def __init__(self, elements: Set[Line]):
        start: FenXing = tuple(elements)[0].start
        end: FenXing = tuple(elements)[0].end
        super().__init__(start, end, 0, elements, f"FeatureSequence<{tuple(elements)[0].stamp if len(elements) > 0 else None}>")

    def __str__(self):
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)})"

    def __repr__(self):
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)})"

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

    @staticmethod
    def analyzer(lines: List[Line], direction: Direction, combines: Tuple[Direction] = (Direction.Left,)) -> Tuple[Optional["FeatureSequence"], Optional["FeatureSequence"], Optional["FeatureSequence"]]:
        features: List[FeatureSequence] = []
        for obj in lines:
            if obj.direction is direction:
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
                if relation in (Direction.Down, Direction.JumpDown):
                    return features[-3], features[-2], features[-1]
                else:
                    return features[-2], features[-1], None
            else:
                if relation in (Direction.Up, Direction.JumpUp):
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
        if observer:
            observer.notify(zs, Command.Append(zs.stamp + "_zs"))

    @classmethod
    def pop(cls, zss: List["ZhongShu"], zs: "ZhongShu", observer: Observer) -> Optional["ZhongShu"]:
        if not zss:
            return
        if zss[-1] is zs:
            zsdp(f"ZhongShu.pop: {zs}")
            if observer:
                observer.notify(zs, Command.Remove(zs.stamp + "_zs"))
            return zss.pop()

    @classmethod
    def new(cls, elements: List) -> Optional["ZhongShu"]:
        if Interval.new(elements) is not None:
            return ZhongShu(elements[1], elements)

    @classmethod
    def analyzer(cls, lines: List[Line], zss: List["ZhongShu"], observer: Observer):
        if not lines:
            return

        if not zss:
            for i in range(1, len(lines) - 1):
                left, mid, right = lines[i - 1], lines[i], lines[i + 1]
                new = cls.new([left, mid, right])
                if new is not None:
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
                if double_relation(last, last.third) not in (Direction.JumpDown, Direction.JumpUp):
                    last.elements.append(last.third)
                    last.third = None
                    observer.notify(last, Command.Modify(last.stamp))

            while 1:
                try:
                    index = lines.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    if len(last.elements) > 3:
                        drop = last.elements.pop()
                        observer.notify(last, Command.Modify(last.stamp))
                    else:
                        cls.pop(zss, last, observer)
                        return cls.analyzer(lines, zss, observer)

            elements = []
            for hl in lines[index:]:
                if double_relation(last, hl) in Direction.jumps():
                    elements.append(hl)
                    if last.elements[-1].is_next(hl):
                        last.third = hl
                else:
                    if not elements:
                        last.elements.append(hl)
                        observer.notify(last, Command.Modify(last.stamp))
                    else:
                        elements.append(hl)

                if len(elements) >= 3:
                    new = cls.new(elements[:])
                    if new is None:
                        elements.pop(0)
                    else:
                        cls.append(zss, new, observer)
                        last = new
                        elements = []


class ZouShi(Line):
    PANZHENG: Final[str] = "盘整"
    SHANGZHANG: Final[str] = "上涨"
    XIADIE: Final[str] = "下跌"

    def __init__(self, elements: List[Union[Line, ZhongShu]], config: ChanConfig):
        super().__init__(elements[0].start, elements[-1].end, 0, elements, "ZouShi")
        self.config = config

    @classmethod
    def analyzer(cls, lines: List[Line], zss: List["ZouShi"], config: ChanConfig):
        if len(lines) < 3:
            return


@final
class Bi(Line):
    __slots__ = "pre", "fake", "config"

    def __init__(
        self,
        pre: Optional["Self"],
        start: FenXing,
        end: FenXing,
        elements: List[NewBar],
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
            if self.config.BI_JUMP and relation in Direction.jumps():
                size += 1
            size += 1
        if not self.config.BI_JUMP:
            assert size == len(elements)
        if self.config.BI_JUMP:
            return size
        return len(elements)

    @property
    def real_high(self) -> Optional[NewBar]:
        if not self.elements:
            return None
        if self.config.BI_EQUAL:
            high = [self.elements[0]]
            for bar in self.elements[1:]:
                if bar.high >= high[-1].high:
                    if bar.high > high[-1].high:
                        high.clear()
                    high.append(bar)
            if len(high) > 1:
                dp("", high)
            return high[-1]

        return max(self.elements, key=lambda x: x.high)

    @property
    def real_low(self) -> Optional[NewBar]:
        if not self.elements:
            return None
        if self.config.BI_EQUAL:
            low = [self.elements[0]]
            for bar in self.elements[1:]:
                if bar.low <= low[-1].low:
                    if bar.low < low[-1].low:
                        low.clear()
                    low.append(bar)
            if len(low) > 1:
                dp("", low)
            return low[-1]
        return min(self.elements, key=lambda x: x.low)

    @property
    def relation(self) -> bool:
        if self.config.BI_FENGXING:
            start = self.start
            relation = double_relation(start, self.end)
        else:
            start = self.start.mid
            relation = double_relation(start, self.end)

        if self.direction is Direction.Down:
            return relation in (
                Direction.Down,
                Direction.JumpDown,
            )
        return relation in (Direction.Up, Direction.JumpUp)

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
    def get_elements(bars: List[NewBar], start: FenXing, end: FenXing) -> List[NewBar]:
        return bars[bars.index(start.mid) : bars.index(end.mid) + 1]

    @classmethod
    def analyzer(
        cls,
        fx: FenXing,
        fxs: List[FenXing],
        bis: List["Bi"],
        bars: List[NewBar],
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
                    if observer:
                        observer.notify(bi_, Command.Remove("Bi"))

        last = fxs[-1]

        if last.mid.dt > fx.mid.dt:
            raise ChanException("时序错误")

        if (last.shape is Shape.G and fx.shape is Shape.D) or (last.shape is Shape.D and fx.shape is Shape.G):
            bi = Bi(None, last, fx, Bi.get_elements(bars, last, fx), False, config)
            if bi.length > 4:
                eq = config.BI_EQUAL
                config.BI_EQUAL = False  # 起始点检测时不考虑相同起始点情况，避免递归

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
                    config.BI_EQUAL = eq
                    return
                config.BI_EQUAL = eq

                if last.shape is Shape.G and fx.shape is Shape.D:
                    end = bi.real_low
                else:
                    end = bi.real_high

                if bi.relation and fx.mid is end:
                    FenXing.append(fxs, fx)
                    Line.append(bis, bi)
                    if _from == "analyzer":
                        bdp(f"Bi. append: {bi}")
                        if observer:
                            observer.notify(bi, Command.Append("Bi"))
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
                lkey = lambda o: o.low
            else:
                func = max
                lkey = lambda o: o.high

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
                            key=lkey,
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
                    if observer:
                        observer.notify(bi, Command.Append("Bi"))

        elif (last.shape is Shape.G and fx.shape is Shape.X) or (last.shape is Shape.D and fx.shape is Shape.S):
            ...

        else:
            raise ChanException(last.shape, fx.shape)

    @staticmethod
    def analysis_one(bars: List[NewBar], level: int, config: ChanConfig, observer: Observer) -> tuple[Optional[FenXing], Optional["Bi"]]:
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
    __slots__ = "pre", "features", "jump"

    def __init__(
        self,
        pre: Optional[Self],
        start: FenXing,
        end: FenXing,
        elements: List[Line],
        stamp: str = "Duan",
    ):
        super().__init__(start, end, 0, elements, stamp)
        self.jump: bool = False  # 特征序列是否有缺口
        self.features: list[Optional[FeatureSequence]] = [None, None, None]
        self.pre = pre

        if pre is not None:
            assert pre.end is start
            self.index = pre.index + 1

    def __str__(self):
        return f"{self.stamp}({self.index}, {self.direction}, {self.pre is not None}, {self.start}, {self.end}, size={len(self.elements)})"

    def __repr__(self):
        return str(self)

    @property
    def done(self) -> bool:
        return self.right is not None

    @property
    def lmr(self) -> tuple[bool, bool, bool]:
        return self.left is not None, self.mid is not None, self.right is not None

    @property
    def state(self) -> Optional[str]:
        if self.pre is not None:
            if self.pre.mid is None:
                return None
            relation = double_relation(self.pre.left, self.pre.mid)
            if relation is Direction.JumpUp and self.direction is Direction.Up:
                return "老阳"
            elif relation is Direction.JumpDown and self.direction is Direction.Down:
                return "老阴"
            else:
                return "小阳" if self.direction is Direction.Up else "少阴"
        else:
            return "小阳" if self.direction is Direction.Up else "少阴"

    @property
    def left(self) -> FeatureSequence:
        return self.features[0]

    @left.setter
    def left(self, feature: FeatureSequence):
        self.features[0] = feature

    @property
    def mid(self) -> FeatureSequence:
        return self.features[1]

    @mid.setter
    def mid(self, feature: FeatureSequence):
        self.features[1] = feature

    @property
    def right(self) -> FeatureSequence:
        return self.features[2]

    @right.setter
    def right(self, feature: FeatureSequence):
        self.features[2] = feature

    def get_elements(self) -> List[Line]:
        elements = []
        for obj in self.elements:
            elements.append(obj)
            if obj.end is self.end:
                break
        return elements

    def append_element(self, line: Line, observer: Observer):
        if self.elements[-1].end is line.start:
            self.elements.append(line)
        else:
            raise ChanException("线段添加元素时，元素不连续", self.elements[-1], line)

    def pop_element(self, line: Line) -> bool:
        if self.elements[-1] is line:
            self.elements.pop()
            return True
        else:
            raise ChanException("线段弹出元素时，元素不匹配")

    @classmethod
    def new(cls, line: Line | List[Line], stamp: str) -> "Duan":
        if type(line) is list:
            return Duan(None, line[0].start, line[-1].end, line, stamp)
        return Duan(None, line.start, line.end, [line], stamp)

    @classmethod
    def feature_setter(cls, offset: int, feature: Optional[FeatureSequence], features: List[Optional[FeatureSequence]], direction: Direction, observer: Observer):
        if feature and feature.direction != direction:
            raise ChanException("特征序列方向不匹配")

        if feature is None:
            if old := features[offset]:
                observer.notify(old, Command.Remove(old.stamp))
            features[offset] = feature
            return

        if features[offset] is None:
            features[offset] = feature
            observer.notify(feature, Command.Append(feature.stamp))

        else:
            observer.notify(features[offset], Command.Remove(features[offset].stamp))
            observer.notify(feature, Command.Append(feature.stamp))
            features[offset] = feature

    @classmethod
    def set_features(cls, duan: "Duan", observer: Observer):
        (left, mid, right) = FeatureSequence.analyzer(duan.elements, duan.direction)
        Duan.feature_setter(0, left, duan.features, duan.direction.reversal(), observer)
        Duan.feature_setter(1, mid, duan.features, duan.direction.reversal(), observer)
        Duan.feature_setter(2, right, duan.features, duan.direction.reversal(), observer)

    @classmethod
    def clear_features(cls, duan: "Duan", observer: Observer):
        (left, mid, right) = (None, None, None)
        Duan.feature_setter(0, left, duan.features, duan.direction.reversal(), observer)
        Duan.feature_setter(1, mid, duan.features, duan.direction.reversal(), observer)
        Duan.feature_setter(2, right, duan.features, duan.direction.reversal(), observer)

    @classmethod
    def set_done(cls, duan: "Duan", fx: FenXing, observer: Observer):
        assert fx is duan.mid.start

        elements = []
        for obj in duan.elements:
            if elements:
                elements.append(obj)
            if obj.start is fx:
                elements.append(obj)
        duan.end = fx
        duan.jump = double_relation(duan.left, duan.mid) in (
            Direction.JumpUp,
            Direction.JumpDown,
        )
        return elements

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
                if double_relation(left, right) in Direction.jumps():
                    continue
                duan = Duan.new([left, mid, right], "Duan" if mid.stamp == "Bi" else mid.stamp + "Duan")
                Line.append(xds, duan)
                observer.notify(duan, Command.Append(duan.stamp))
                return Duan.analyzer(lines, xds, observer)

        else:
            last = xds[-1]
            elements = last.get_elements()
            while 1:
                try:
                    index = lines.index(elements[-1]) + 1
                    break
                except ValueError:
                    line = elements.pop()
                    ddp("Duan.analyzer 弹出", line)
                    if last.done:
                        if line in last.right:
                            if len(last.right) == 1:
                                if line in last.right:
                                    Duan.feature_setter(2, None, last.features, last.direction.reversal(), observer)
                                else:
                                    raise ChanException
                            else:
                                last.right.remove(line)
                                Duan.feature_setter(2, last.right, last.features, last.direction.reversal(), observer)

                    if not elements:
                        print("Duan.analyzer 无法找到", last)
                        if Line.pop(xds, last) is not None:
                            observer.notify(last, Command.Remove(last.stamp))
                            # Duan.clear_features(duan, observer)
                        return Duan.analyzer(lines, xds, observer)
            last.elements = elements[:]
            Duan.set_features(last, observer)

            duan = last
            for line in lines[index:]:
                Line.append(duan.elements, line)
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
                    observer.notify(duan, Command.Modify(duan.stamp))
                else:
                    Duan.set_features(duan, observer)
                    if duan.right is not None:
                        elements = Duan.set_done(duan, duan.mid.start, observer)
                        observer.notify(duan, Command.Modify(duan.stamp))
                        if duan.jump:
                            pre = duan
                        else:
                            pre = None

                        if xds:
                            if duan is not xds[-1]:
                                Line.append(xds, duan)
                                observer.notify(duan, Command.Append(duan.stamp))
                                for feature in duan.features:
                                    if feature is not None:
                                        observer.notify(feature, Command.Append(feature.stamp))
                            else:
                                ...
                        else:
                            Line.append(xds, duan)
                            observer.notify(duan, Command.Append(duan.stamp))
                            for feature in duan.features:
                                if feature is not None:
                                    observer.notify(feature, Command.Append(feature.stamp))

                        if duan.direction is Direction.Up:
                            fx = "顶分型"
                        else:
                            fx = "底分型"

                        ddp("    ", f"{fx}终结, 缺口: {duan.jump}")
                        duan = Duan.new(elements, "Duan" if line.stamp == "Bi" else line.stamp + "Duan")
                        duan.pre = pre
                        Line.append(xds, duan)
                        observer.notify(duan, Command.Append(duan.stamp))
                        for feature in duan.features:
                            if feature is not None:
                                observer.notify(feature, Command.Append(feature.stamp))


class BaseAnalyzer(Observer):
    __slots__ = "symbol", "freq", "ws", "last_raw_bar", "raws", "news", "fxs", "bis", "xds", "bzss", "dzss", "cache", "config"

    def __init__(self, symbol: str, freq: SupportsInt, ws: WebSocket = None):
        self.symbol = symbol
        self.freq = int(freq)
        self.ws = ws
        self.last_raw_bar = None
        self.raws = []
        self.news = []
        self.fxs = []
        self.bis = []
        self.xds = []
        self.bzss = []
        self.dzss = []
        self.cache = dict()
        self.config = ChanConfig()

    def notify(self, obj: Any, cmd: Command):
        if not self.config.ANALYZER_SHON_TV:
            return
        message = dict()
        message["stamp"] = obj.stamp if hasattr(obj, "stamp") else obj.__class__.__name__

        if type(obj) is NewBar:
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
            message["properties"] = {"linecolor": "#F1C40F" if obj.elements[0].stamp == "Bi" else "#00C40F", "linewidth": 3, "title": f"{obj.stamp}-{obj.index}", "text": obj.stamp}

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
                "linecolor": "#FFFFFF" if obj.direction.reversal() is Direction.Down else "#000000",
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
        dt: datetime.datetime | int | str,
        open_: float | str,
        high: float | str,
        low: float | str,
        close: float | str,
        volume: float | str,
    ):
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

        last = RawBar(
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
    def push(self, bar: RawBar):
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
            nb = NewBar.merger(pre, self.news[-1], bar)
            if nb is not None:
                self.news.append(nb)
        else:
            nb = bar.to_new_bar(None)
            self.news.append(nb)

        self.notify(self.news[-1], Command.Append("NewBar"))

        # left, mid, right = None, None, None
        try:
            left, mid, right = self.news[-3:]
        except ValueError:
            return

        (shape, _) = triple_relation(left, mid, right)
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
            Duan.analyzer(self.bis, self.xds, self)
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
                            bar = RawBar.from_be_bytes(buffer[i * size : i * size + size])
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

    return func


def test_thread(ws):
    def func():
        bitstamp = Bitstamp("btcusd", freq=Freq.m5, ws=ws)
        bitstamp.notify("test", Command("test", "test"))

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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            message = json.loads(data)
            if message["type"] == "ready":
                # exchange = message["exchange"]
                symbol = message["symbol"]
                freq = message["freq"]
                limit = message["limit"]
                if Observer.thread is not None:
                    tmp = Observer.thread
                    Observer.thread = None

                    tmp.join(1)
                    time.sleep(1)

                Observer.thread = Thread(target=main_bitstamp(symbol=symbol, freq=freq, limit=limit, ws=websocket))  # 使用线程来运行main函数
                Observer.thread.start()
    except WebSocketDisconnect:
        ...


@app.get("/")
async def main_page(
    request: Request,
    nol: str = "network",
    exchange: str = "bitstamp",
    symbol: str = "btcusd",
    step: int = 300,
    limit: int = 500,
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
    return templates.TemplateResponse("index.html", {"request": request, "exchange": exchange, "symbol": symbol, "interval": resolutions.get(step), "limit": str(limit), "step": str(step)})


if __name__ == "__main__":
    BaseAnalyzer.read_from_dat_file("btcusd-60-0-0.dat")
