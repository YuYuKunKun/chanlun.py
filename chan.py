"""
# -*- coding: utf-8 -*-
# @Time    : 2024/04/26 16:30
# @Author  : YuYuKunKun
# @File    : chan.py
"""

import struct
import traceback
from typing import List, Union, Self, Literal, Optional, Tuple, final, Dict
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from importlib import reload
from random import choice
from enum import Enum

import requests

try:
    from termcolor import colored
except ImportError:

    def colored(text, *args):
        """彩色字"""
        return text


class Shape(Enum):
    D = "底分型"
    G = "顶分型"
    S = "上升分型"
    X = "下降分型"
    T = "喇叭口型"


class Direction(Enum):
    Up = "向上"
    Down = "向下"
    JumpUp = "缺口向上"
    JumpDown = "缺口向下"

    Left = "左包右"  # 顺序包含
    Right = "右包左"  # 逆序包含


class Freq(Enum):
    # 60 180 300 900 1800 3600 7200 14400 21600 43200 86400 259200
    S1: int = 1
    S3: int = 3
    S5: int = 5
    S12: int = 12
    m1: int = 60 * 1
    m3: int = 60 * 3
    m5: int = 60 * 5
    m15: int = 60 * 15
    m30: int = 60 * 30
    H1: int = 60 * 60 * 1
    H3: int = 60 * 60 * 3
    H4: int = 60 * 60 * 4


class ChanException(Exception):
    """exception"""

    ...


class ChartsID:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @staticmethod
    def get(size: int):
        return "".join([choice(ChartsID.chars) for _ in range(size)])


def charts_id_(cls):
    @property
    def charts_id(self) -> str:
        return ChartsID.get(6)

    cls.charts_id = charts_id
    return cls


def _print(*args, **kwords):
    result = []
    for i in args:
        if i in ("少阳", True, Shape.D, "底分型") or "少阳" in str(i):
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
    if 1:
        _print(*args, **kwords)


def bdp(*args, **kwargs):
    if not 1:
        dp(*args, **kwargs)


def ddp(*args, **kwargs):
    if not 1:
        dp(*args, **kwargs)


def Klines(cls):
    def cklines(self, news: list["NewBar"]):
        return news[self.start.left.index : self.end.right.index]

    cls.cklines = cklines
    return cls


class Base(metaclass=ABCMeta):
    @abstractmethod
    def high(self) -> float: ...

    @abstractmethod
    def low(self) -> float: ...


def double_relation(left, right) -> Direction:
    """
    两个带有[low, high]对象的所有关系
    """
    # assert hasattr(left, "low")
    # assert hasattr(left, "high")
    # assert hasattr(right, "low")
    # assert hasattr(right, "high")

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


def triple_relation(left, mid, right, use_right=False) -> tuple[Optional[Shape], tuple[Direction, Direction]]:
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

    if lm in (Direction.Up, Direction.JumpUp):
        # 涨
        if mr in (Direction.Up, Direction.JumpUp):
            # 涨
            shape = Shape.S
        if mr in (Direction.Down, Direction.JumpDown):
            # 跌
            shape = Shape.G
        if mr is Direction.Left:
            # 顺序包含
            print("顺序包含 mr")
            raise ChanException("顺序包含 mr")
        if mr is Direction.Right and use_right:
            # 逆序包含
            shape = Shape.S

    if lm in (Direction.Down, Direction.JumpDown):
        # 跌
        if mr in (Direction.Up, Direction.JumpUp):
            # 涨
            shape = Shape.D
        if mr in (Direction.Down, Direction.JumpDown):
            # 跌
            shape = Shape.X
        if mr is Direction.Left:
            # 顺序包含
            print("顺序包含 mr")
            raise ChanException("顺序包含 mr")
        if mr is Direction.Right and use_right:
            # 逆序包含
            shape = Shape.X

    if lm is Direction.Left:
        # 顺序包含
        print("顺序包含 lm")
        raise ChanException("顺序包含 lm")

    if lm is Direction.Right and use_right:
        # 逆序包含
        if mr in (Direction.Up, Direction.JumpUp):
            # 涨
            shape = Shape.D
        if mr in (Direction.Down, Direction.JumpDown):
            # 跌
            shape = Shape.G
        if mr is Direction.Left:
            # 顺序包含
            print("顺序包含 mr")
            raise ChanException("顺序包含 mr")
        if mr is Direction.Right and use_right:
            # 逆序包含
            shape = Shape.T  # 喇叭口型
    return shape, (lm, mr)


class RawBar:
    __slots__ = "dt", "open", "high", "low", "close", "volume", "index", "cache", "done", "dts", "lv"

    def __init__(self, dt: datetime, open: float, high: float, low: float, close: float, volume: float, index: int = 0):
        self.dt = dt
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.index = index
        self.cache = dict()
        self.done = False
        self.dts = [
            self.dt,
        ]
        self.lv = self.volume

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

    @classmethod
    def from_bytes(cls, buf: bytes):
        timestamp, open, high, low, close, vol = struct.unpack(">6d", buf)
        return cls(dt=datetime.fromtimestamp(timestamp), open=open, high=high, low=low, close=close, volume=vol)

    @property
    def ampl(self) -> float:
        """涨跌幅"""
        return (self.open - self.close) / self.open

    @property
    def direction(self) -> Direction:
        return Direction.Up if self.open < self.close else Direction.Down

    @property
    def new(self) -> "NewBar":
        if self.open > self.close:
            open_ = self.high
            close = self.low
        else:
            open_ = self.low
            close = self.high
        return NewBar(
            dt=self.dt,
            open=open_,
            high=self.high,
            low=self.low,
            close=close,
            index=0,
            volume=self.volume,
            elements=[
                self,
            ],
        )

    def candleDict(self):
        return {
            "dt": self.dt,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "vol": self.volume,
        }


class RawBars:
    __slots__ = "__bars", "__size", "freq", "klines"

    def __init__(self, bars: Optional[List[RawBar]] = None, freq: Optional[int] = None, merger: Optional[List] = None):
        if bars is None:
            bars = []
        self.__bars: List[RawBar] = bars  # 原始K线
        self.__size = len(bars)
        self.freq = freq
        self.klines = {freq: self.__bars}

        if merger:
            merger = set(merger)
            merger.remove(freq)
            for m in merger:
                self.klines[m] = []
        self.klines = {freq: self.__bars}

    def __getitem__(self, index: Union[slice, int]) -> Union[List[RawBar], RawBar]:
        return self.__bars[index]

    def __len__(self):
        return self.__size

    @property
    def last(self) -> RawBar:
        return self.__bars[-1] if self.__bars else None

    def push(self, bar: RawBar):
        for freq, bars in self.klines.items():
            ts = bar.dt.timestamp()
            d = ts // freq

            dt = datetime.fromtimestamp(d * freq)
            new = RawBar(dt=dt, open=bar.open, high=bar.high, low=bar.low, close=bar.close, volume=bar.volume)

            if freq == self.freq:
                self.__size += 1

            if bars:
                last = bars[-1]
                new.index = last.index + 1
                if last.dt == dt:
                    if last.dts[-1] == bar.dt:
                        last.volume += bar.volume - last.lv
                        last.lv = bar.volume
                        if freq == self.freq:
                            self.__size -= 1
                    else:
                        last.dts.append(bar.dt)
                        last.volume += bar.volume

                    last.high = max(last.high, bar.high)
                    last.low = min(last.low, bar.low)
                    last.close = bar.close

                else:
                    bars.append(new)
                    last.done = True
                    del last.dts
                    del last.lv

            else:
                bars.append(new)


class NewBar:
    __slots__ = "dt", "open", "high", "low", "close", "volume", "index", "shape", "elements", "relation", "speck", "done", "jump", "cache", "bi", "duan", "_dt"

    def __init__(self, dt: datetime, open: float, high: float, low: float, close: float, volume: float, index: int = 0, elements=None):
        self.dt: datetime = dt
        self.open: float = open
        self.high: float = high
        self.low: float = low
        self.close: float = close
        self.volume: float = volume
        self.index: int = index
        self.shape: Optional[Shape] = None
        self.elements: Optional[List[RawBar]] = elements

        self.relation: Optional[Direction] = None  # 与前一个关系
        self.speck: Optional[float] = None  # 分型高低点
        self.done: bool = False  # 是否完成
        self.jump: bool = False  # 与前一个是否是跳空

        self.cache = dict()
        self.bi: Optional[bool] = None  # 是否是 笔
        self.duan: Optional[bool] = None  # 是否是 段
        self._dt = self.dt

    def __str__(self):
        return f"NewBar({self.dt}, {self.speck}, {self.shape})"

    def __repr__(self):
        return f"NewBar({self.dt}, {self.speck}, {self.shape})"

    @property
    def direction(self) -> Direction:
        return Direction.Up if self.open < self.close else Direction.Down

    @property
    def raw(self) -> RawBar:
        return RawBar(self.dt, self.open, self.high, self.low, self.close, self.volume)

    def candleDict(self) -> dict:
        return {
            "dt": self.dt,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "vol": self.volume,
        }

    @staticmethod
    def include(ck: "NewBar", k: RawBar, direction: Direction) -> tuple["NewBar", bool]:
        flag = False
        if double_relation(ck, k) in (Direction.Left, Direction.Right):
            if direction in (Direction.Down, Direction.JumpDown):
                # 向下取低低
                high = min(ck.high, k.high)
                low = min(ck.low, k.low)
                dt = k.dt if k.low < ck.low else ck.dt
                o = high
                c = low
            elif direction in (Direction.Up, Direction.JumpUp):
                # 向上取高高
                high = max(ck.high, k.high)
                low = max(ck.low, k.low)
                dt = k.dt if k.high > ck.high else ck.dt
                c = high
                o = low
            else:
                raise ChanException("合并方向错误")

            elements = ck.elements
            dts = [o.dt for o in elements]
            if k.dt not in dts:
                elements.append(k)
            else:
                if elements[-1].dt == k.dt:
                    elements[-1] = k
                else:
                    raise ChanException("元素重复")
            volume = sum([o.volume for o in elements])

            new = NewBar(
                dt=dt,
                open=o,
                high=high,
                low=low,
                close=c,
                index=ck.index,
                volume=volume,
                elements=elements,
            )
            flag = True
            # self.cklines[-1] = new
        else:
            new = k.new
            new.index = ck.index + 1
            ck.done = True
            # self.cklines.append(new)
        return new, flag


class NewBars:
    __slots__ = "bars", "__size"

    def __init__(self, bars: Optional[List[NewBar]] = None):
        if bars is None:
            bars = []
        self.bars: List[NewBar] = bars
        self.__size = len(bars)

    def __getitem__(self, index: Union[slice, int]) -> Union[List[NewBar], NewBar]:
        return self.bars[index]

    def __len__(self):
        return self.__size

    @property
    def last(self) -> NewBar:
        return self.bars[-1] if self.bars else None

    def push(self, bar: RawBar):
        if self.last is None:
            self.bars.append(bar.new)
        else:
            last = self.last
            relation = double_relation(last, bar)
            if relation in (Direction.Left, Direction.Right):
                direction = last.direction
                try:
                    direction = double_relation(self.bars[-2], last)
                except IndexError:
                    traceback.print_exc()

                new, flag = NewBar.include(last, bar, direction)
                new.index = last.index
                self.bars[-1] = new
            else:
                new = bar.new
                new.index = last.index + 1
                self.__size += 1
                self.bars.append(new)

        try:
            left, mid, right = self.bars[-3:]  # ValueError: not enough values to unpack (expected 3, got 2)
            shape, relations = triple_relation(left, mid, right)
            mid.shape = shape
            if relations[1] in (Direction.JumpDown, Direction.JumpUp):
                right.jump = True
            if relations[0] in (Direction.JumpDown, Direction.JumpUp):
                mid.jump = True

            if shape is Shape.S:
                right.shape = Shape.S
                mid.speck = mid.high
            elif shape is Shape.G:
                right.shape = Shape.X
                mid.speck = mid.high
            elif shape is Shape.D:
                right.shape = Shape.S
                mid.speck = mid.low
            elif shape is Shape.X:
                right.shape = Shape.X
                mid.speck = mid.low
            else:
                raise ChanException(shape)
        except ValueError:
            traceback.print_exc()


class FenXing:
    __slots__ = "left", "mid", "right", "index", "__shape", "__relations", "__speck", "real"

    def __init__(self, left: NewBar, mid: NewBar, right: NewBar, index: int = 0):
        self.left = left
        self.mid = mid
        self.right = right
        self.index = index

        self.__shape, self.__relations = triple_relation(self.left, self.mid, self.right)
        self.__speck = None
        if self.__shape is Shape.G:
            self.__speck = self.mid.high
            self.mid.speck = self.mid.high

        if self.__shape is Shape.D:
            self.__speck = self.mid.low
            self.mid.speck = self.mid.low
        self.mid.shape = self.__shape
        if self.__relations[0] in (Direction.JumpDown, Direction.JumpUp):
            self.mid.jump = True

    @property
    def raws(self) -> List[RawBar]:
        result = []
        for k in self.left.elements + self.mid.elements + self.right.elements:
            result.append(k)
        return result

    @property
    def dt(self) -> datetime:
        return self.mid.dt

    @property
    def relations(self) -> tuple[Direction, Direction]:
        return self.__relations

    @property
    def shape(self) -> Shape:
        return self.__shape

    @property
    def speck(self) -> float:
        return self.__speck

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


@charts_id_
class Bi:
    __slots__ = "index", "start", "end", "elements", "done", "real_high", "real_low", "direction", "ld"

    def __init__(self, index: int, start: FenXing, end: FenXing, elements: List[NewBar], done: bool = False):
        self.index: int = index
        self.start: FenXing = start
        self.end: FenXing = end
        self.elements: List[NewBar] = elements
        self.done: bool = done

        high = self.elements[0]
        low = self.elements[0]
        for k in self.elements:
            if high.high < k.high:
                high = k
            if low.low > k.low:
                low = k
        self.real_high = high
        self.real_low = low
        if self.start.shape is Shape.G and self.end.shape is Shape.D:
            self.direction = Direction.Down
        elif self.start.shape is Shape.D and self.end.shape is Shape.G:
            self.direction = Direction.Up
        else:
            raise ChanException(self.start.shape, self.end.shape)
        self.ld: Union[dict, None] = None

    @property
    def high(self) -> float:
        return max(self.start.speck, self.end.speck)

    @property
    def low(self) -> float:
        return min(self.start.speck, self.end.speck)

    @property
    def mid(self) -> float:
        return (self.start.speck + self.end.speck) / 2

    def __str__(self):
        return f"Bi({self.direction}, {colored(self.start.dt, 'green')}, {self.start.speck}, {colored(self.end.dt, 'green')}, {self.end.speck}, {self.index})"

    def __repr__(self):
        return f"Bi({self.direction}, {colored(self.start.dt, 'green')}, {self.start.speck}, {colored(self.end.dt, 'green')}, {self.end.speck}, {self.index})"

    @property
    def relation(self) -> bool:
        if self.direction is Direction.Down:
            return double_relation(self.start, self.end) in (
                Direction.Down,
                Direction.JumpDown,
            )
        return double_relation(self.start, self.end) in (Direction.Up, Direction.JumpUp)

    @property
    def length(self) -> int:
        return len(self.elements)


class Bis:
    __slots__ = "__size", "fxs", "_handlers", "__bis", "__fxs"

    def __init__(self, fxs: Optional[List[FenXing]], bis: Optional[List[Bi]], handlers: Tuple[Optional["ZhongShus"], Optional["Duans"]]):
        if fxs is None:
            fxs = []
        if bis is None:
            bis = []
        self.__bis: List[Bi] = bis
        self.__size = len(bis)
        self.__fxs: List[FenXing] = fxs
        self.fxs = fxs
        self._handlers: Tuple["ZhongShus", "Duans"] = handlers

    def __getitem__(self, index: Union[slice, int]) -> Union[List[Bi], Bi]:
        return self.__bis[index]

    def __len__(self):
        return self.__size

    @property
    def last(self) -> Bi:
        return self.__bis[-1] if self.__bis else None

    def __pop(self, fx, level: int):
        cmd = "Bis.POP"
        bdp("    " * level, cmd, fx)
        last = self.last
        if last:
            if last.end is fx:
                bi = self.__bis.pop()
                bdp("    " * level, cmd, bi)
                fx.mid.bi = False

                for handler in self._handlers:
                    if handler is not None:
                        handler.pop(bi)

            else:
                raise ChanException("最后一笔终点错误", fx, last.end)
        else:
            bdp("    " * level, cmd, "空")

    def __push(self, bi: Bi, level: int):
        cmd = "Bis.PUSH"
        bdp("    " * level, cmd, bi)
        last = self.last

        if last and last.end is not bi.start:
            raise ChanException("笔连续性错误")
        i = 0
        if last:
            i = last.index + 1
        bi.index = i
        self.__size += 1
        self.__bis.append(bi)
        bi.start.mid.bi = True
        bi.end.mid.bi = True
        for handler in self._handlers:
            if handler is not None:
                handler.push(bi)

    def analysis(self, fx: FenXing, cklines: List[NewBar], level: int):
        cmd = "Bis.ANALYSIS"
        bdp("    " * level, cmd, fx)
        fxs: List[FenXing] = self.__fxs

        last: Union[FenXing, None] = fxs[-1] if fxs else None
        _, mid, right = fx.left, fx.mid, fx.right
        if last is None:
            bdp("    " * level, cmd, "首次分析")
            if mid.shape in (Shape.G, Shape.D):
                fxs.append(fx)
            return

        if last.mid.dt > fx.mid.dt:
            raise ChanException("时序错误")

        if last.shape is Shape.G and fx.shape is Shape.D:
            bdp("    " * level, cmd, "GD")
            bi = Bi(0, last, fx, cklines[last.mid.index : fx.mid.index + 1])
            if bi.length > 4:
                if bi.real_high is not last.mid:
                    print("不是真顶")
                    top = bi.real_high
                    new = FenXing(cklines[top.index - 1], top, cklines[top.index + 1])
                    assert new.shape is Shape.G, new
                    self.analysis(new, cklines, level + 1)  # 处理新底
                    self.analysis(fx, cklines, level + 1)  # 再处理当前顶
                    return
                flag = bi.relation
                if flag and fx.mid is bi.real_low:
                    FenXing.append(fxs, fx)
                    self.__push(bi, level)
                else:
                    ...
            else:
                ...

        elif last.shape is Shape.D and fx.shape is Shape.G:
            bdp("    " * level, cmd, "DG")
            bi = Bi(0, last, fx, cklines[last.mid.index : fx.mid.index + 1])
            if bi.length > 4:
                if bi.real_low is not last.mid:
                    print("不是真底")
                    bottom = bi.real_low
                    new = FenXing(cklines[bottom.index - 1], bottom, cklines[bottom.index + 1])
                    assert new.shape is Shape.D, new
                    self.analysis(new, cklines, level + 1)  # 处理新底
                    self.analysis(fx, cklines, level + 1)  # 再处理当前顶
                    return
                flag = bi.relation
                if flag and fx.mid is bi.real_high:
                    FenXing.append(fxs, fx)
                    self.__push(bi, level)
                else:
                    ...
            else:
                ...

        elif last.shape is Shape.G and fx.shape is Shape.S:
            if last.speck < right.high:
                tmp = fxs.pop()
                assert tmp is last
                tmp.real = False
                self.__pop(tmp, level)

                if fxs:
                    # 查找
                    last = fxs[-1]
                    assert last.shape is Shape.D
                    bottom = min(cklines[last.mid.index : fx.mid.index + 1], key=lambda o: o.low)
                    assert bottom.shape is Shape.D
                    if last.speck > bottom.low:
                        tmp = fxs.pop()
                        assert tmp is last
                        tmp.real = False
                        self.__pop(tmp, level)

                        new = FenXing(cklines[bottom.index - 1], bottom, cklines[bottom.index + 1])
                        assert new.shape is Shape.D, new
                        self.analysis(new, cklines, level + 1)  # 处理新底
                        print("GS修正")

        elif last.shape is Shape.D and fx.shape is Shape.X:
            if last.speck > right.low:
                """
                底分型被突破
                1. 向上不成笔但出了高点，需要修正顶分型
                   修正后涉及循环破坏问题，即形似开口向右的扩散形态
                   解决方式
                       ①.递归调用，完全符合笔的规则，但此笔一定含有多个笔，甚至形成低级别一个走势。
                       ②.只修正一次
                2. 向上不成笔没出了高点，无需修正
                """
                tmp = fxs.pop()
                assert tmp is last
                tmp.real = False
                self.__pop(tmp, level)

                if fxs:
                    # 查找
                    last = fxs[-1]
                    assert last.shape is Shape.G
                    top = max(cklines[last.mid.index : fx.mid.index + 1], key=lambda o: o.high)
                    assert top.shape is Shape.G
                    if last.speck < top.high:
                        tmp = fxs.pop()
                        assert tmp is last
                        tmp.real = False
                        self.__pop(tmp, level)
                        new = FenXing(cklines[top.index - 1], top, cklines[top.index + 1])
                        assert new.shape is Shape.G, new
                        self.analysis(new, cklines, level + 1)  # 处理新顶
                        print("DX修正")

        elif last.shape is Shape.G and fx.shape is Shape.G:
            if last.speck < fx.speck:
                tmp = fxs.pop()
                assert tmp is last
                tmp.real = False
                self.__pop(tmp, level)

                if fxs:
                    # 查找
                    last = fxs[-1]
                    assert last.shape is Shape.D
                    bottom = min(cklines[last.mid.index : fx.mid.index + 1], key=lambda o: o.low)
                    assert bottom.shape is Shape.D
                    if last.speck > bottom.low:
                        tmp = fxs.pop()
                        assert tmp is last
                        tmp.real = False
                        self.__pop(tmp, level)
                        new = FenXing(cklines[bottom.index - 1], bottom, cklines[bottom.index + 1])
                        assert new.shape is Shape.D, new
                        self.analysis(new, cklines, level + 1)  # 处理新底
                        self.analysis(fx, cklines, level + 1)  # 再处理当前顶
                        print("GG修正")
                        return

                if not fxs:
                    FenXing.append(fxs, fx)
                    return
                bi = Bi(0, fxs[-1], fx, cklines[fxs[-1].mid.index : fx.mid.index + 1])
                FenXing.append(fxs, fx)
                self.__push(bi, level)

        elif last.shape is Shape.D and fx.shape is Shape.D:
            if last.speck > fx.speck:
                tmp = fxs.pop()
                assert tmp is last
                tmp.real = False
                self.__pop(tmp, level)

                if fxs:
                    # 查找
                    last = fxs[-1]
                    assert last.shape is Shape.G
                    top = max(cklines[last.mid.index : fx.mid.index + 1], key=lambda o: o.high)
                    assert top.shape is Shape.G
                    if last.speck < top.high:
                        tmp = fxs.pop()
                        assert tmp is last
                        tmp.real = False
                        self.__pop(tmp, level)
                        new = FenXing(cklines[top.index - 1], top, cklines[top.index + 1])
                        assert new.shape is Shape.G, new
                        self.analysis(new, cklines, level + 1)  # 处理新顶
                        self.analysis(fx, cklines, level + 1)  # 再处理当前底
                        print("DD修正")
                        return

                if not fxs:
                    FenXing.append(fxs, fx)
                    return
                bi = Bi(0, fxs[-1], fx, cklines[fxs[-1].mid.index : fx.mid.index + 1])
                FenXing.append(fxs, fx)
                self.__push(bi, level)

        elif last.shape is Shape.G and fx.shape is Shape.X:
            ...

        elif last.shape is Shape.D and fx.shape is Shape.S:
            ...

        else:
            raise ChanException(last.shape, fx.shape)


States = Literal["老阳", "少阴", "老阴", "少阳"]


@charts_id_
class Duan:
    __slots__ = "index", "start", "end", "elements", "done", "pre", "features", "info", "direction"

    def __init__(self, index: int, start: FenXing, end: FenXing, elements: List[Bi]):
        self.index: int = index
        self.start: FenXing = start
        self.end: FenXing = end
        self.elements: List[Bi] = elements

        self.done: bool = False
        self.pre: Optional[Self] = None
        if self.start.shape is Shape.G and self.end.shape is Shape.D:
            self.direction = Direction.Down
        elif self.start.shape is Shape.D and self.end.shape is Shape.G:
            self.direction = Direction.Up
        else:
            raise ChanException(self.start, self.end)

        self.features: list[Union[FeatureSequence, None]] = [None, None, None]
        # self.pre = None
        self.info = []

    def __str__(self):
        return f"Duan({self.index}, {self.direction}, {len(self.elements)}, 完成否:{self.done}, {self.pre is not None})"

    def __repr__(self):
        return f"Duan({self.index}, {self.direction}, {len(self.elements)}, 完成否:{self.done}, {self.pre is not None})"

    def __setattr__(self, name, value):
        state = None
        if hasattr(self, "pre") and hasattr(self, "direction"):
            if self.pre is not None:
                state = "老阳" if self.direction is Direction.Down else "老阴"
            else:
                state = "少阳" if self.direction is Direction.Up else "少阴"

        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        else:
            if self.done:
                dp(state, "线段已完成 修改前", name, getattr(self, name), "修改后", value)
                if name != "done":
                    raise ChanException("尝试修改以完成线段")
            object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        return value

    def get_raw_bars_bytes(self, raw_bars: List[RawBar]) -> bytes:
        bytes_data = b""
        for raw in raw_bars:
            if self.start.left._dt <= raw.dt <= self.end.right.dt:
                bytes_data += bytes(raw)
        return bytes_data

    @property
    def state(self) -> States:
        if self.pre is not None:
            return "老阳" if self.direction is Direction.Down else "老阴"
        else:
            return "少阳" if self.direction is Direction.Up else "少阴"

    @property
    def high(self) -> float:
        return max(self.start.speck, self.end.speck)

    @property
    def low(self) -> float:
        return min(self.start.speck, self.end.speck)

    @property
    def mid(self) -> float:
        return (self.start.speck + self.end.speck) / 2

    @classmethod
    def new(cls, index, obj):
        return cls(
            index,
            obj.start,
            obj.end,
            [
                obj,
            ],
        )

    def charts(self):
        return [
            {"xd": self.start.speck, "dt": self.start.dt},
            {"xd": self.end.speck, "dt": self.end.dt},
        ]

    def clear(self):
        self.features = [None, None, None]
        self.pre = None
        self.done = False
        self.elements = []
        self.start = None
        self.end = None
        self.direction = None

    def check(self) -> bool:
        left, mid, right = self.features
        if left:
            if not left.elements:
                raise ChanException("左特征为空")
        if mid:
            if not mid.elements:
                raise ChanException("中特征为空")
        if right:
            if not right.elements:
                raise ChanException("右特征为空")
        return True

    def append_element(self, bi: Bi):
        if self.elements[-1].end is bi.start:
            self.elements.append(bi)
        else:
            dp("线段添加元素时，元素不连续", self.elements[-1], bi)
            raise ChanException("线段添加元素时，元素不连续", self.elements[-1], bi)

    def pop_element(self, bi: Bi) -> bool:
        if self.elements[-1] is bi:
            self.elements.pop()
            return True
        else:
            raise ChanException("线段弹出元素时，元素不匹配")

    def set_done(self, fx: FenXing, state: States):
        elements = []
        for obj in self.elements:
            if elements:
                elements.append(obj)
            if obj.start is fx:
                elements.append(obj)
        self.end = fx

        if not elements:
            dp("Duan.set_done 没有数据", state)
            # return elements

        for i in range(len(elements)):
            self.elements.pop()

        if self.elements[-1].end is not fx:
            raise ChanException("线段结束时，元素不匹配", self.elements[-1].end, fx)

        self.pre = None
        self.done = True
        # dp("Duan.set_done 完成线段", state, self)
        return elements

    def is_next(self, obj: "Self") -> bool:
        if self.end is obj.start:
            return True
        return False

    @staticmethod
    def pop(duans: List["Duan"], duan: "Duan"):
        # print("弹出段", duan)
        if duans[-1] is duan:
            return duans.pop()
        raise

    @staticmethod
    def append(duans: List["Duan"], duan: "Duan"):
        # print("添加段", duan)
        if duans:
            last = duans[-1]
            if last.end is duan.start:
                duans.append(duan)
            else:
                raise
            return
        raise


class Duans:
    __slots__ = "__duans", "__bis", "_handler"

    def __init__(self, bis: Optional[List[Bi]], duans: Optional[List[Duan]], handler: Optional["ZhongShus"]):
        if bis is None:
            bis = []
        if duans is None:
            duans = []
        self.__duans: List[Duan] = duans
        self.__bis: List[Bi] = bis
        self._handler: "ZhongShus" = handler

    def __getitem__(self, index: Union[slice, int]) -> Union[List[Duan], Duan]:
        return self.__duans[index]

    def __len__(self):
        return len(self.__duans)

    def __iter__(self):
        yield from self.__duans

    @property
    def last(self) -> Duan:
        return self.__duans[-1] if self.__duans else None

    def pop(self, bi, level=0):
        ddp()
        handler = self._handler
        duans = self.__duans
        cmd = "Duans.POP"

        duan = duans[-1]
        last = duan.pre
        flag = last is not None
        if duan.done:
            dp("    " * level, cmd, colored("修改已完成的线段", "red"))
            duan.done = False
        if flag:
            state = "老阳" if duan.direction is Direction.Down else "老阴"
            if last.elements[-1] is bi:
                last.pop_element(bi)
            else:
                ddp("    " * level, cmd, state, "数据弹出异常", last.elements, bi)
                raise ChanException("数据弹出异常", last.elements[-1], bi)
        else:
            state = "少阳" if duan.direction is Direction.Up else "少阴"

        duan.pop_element(bi)

        if not duan.elements:
            Duan.pop(duans, duan)
            dp("要删除中枢元素4", duan)
            handler is not None and handler.pop(duan)
            if state in ("老阳", "老阴"):
                left, mid, right = last.features
                if right.elements[-1] is bi:
                    right.elements.pop()
                    if not right.elements:
                        dp("要删除中枢元素3", last)
                        last.done and handler is not None and handler.pop(last)
                        last.features = [left, mid, None]
                    else:
                        raise ChanException("有数据？？")
                    last.done = False
                    ddp("    " * level, cmd, state, "当前弹出的[笔]涉及上一[段]的特征序列，并修改特征序列")
            ddp("    " * level, cmd, state, "当前段为空 弹出返回")
            return

        if duan.direction is bi.direction:
            ddp("    " * level, cmd, state, "方向相同", bi)
            if state in ("老阳", "老阴"):
                left, mid, right = last.features
                if right.elements[-1] is bi:
                    right.elements.pop()
                    if not right.elements:
                        last.done and handler is not None and handler.pop(last)
                        if last.done:
                            last.done = False
                        last.features = [left, mid, None]
                        Duan.pop(duans, duan)
                        ddp("    " * level, cmd, state, colored("警告: 当前弹出的[笔]涉及上一[段]的特征序列，弹出当前[段]并修改特征序列", "blue"))
                    else:
                        raise ChanException("有数据？？")
                    last.done = False
                    ddp("    " * level, cmd, state, "当前弹出的[笔]涉及上一[段]的特征序列，修改后的特征序列: ", right.elements)
                    ddp("    " * level, "    当前[段]的元素: ", duan.elements)
                    ddp("    " * level, "    上一[段]的元素: ", last.elements)
            return

        left: Optional[FeatureSequence] = duan.features[0]
        mid: Optional[FeatureSequence] = duan.features[1]
        right: Optional[FeatureSequence] = duan.features[2]
        lmr: Tuple[bool, bool, bool] = (left is not None, mid is not None, right is not None)

        ddp(
            "    " * level,
            cmd,
            state,
            lmr,
            "Duan:",
            duan.direction,
            "Bi:",
            bi.direction,
        )
        ddp("    " * level, duan.features)
        features = FeatureSequence.analysis(duan.elements, bi.direction)

        if lmr == (True, False, False):
            assert left.elements.pop() is bi
            if not left.elements:
                duan.features = [None, None, None]
                if len(features) >= 1:
                    if features[-1] == left:
                        duan.features = [features[-1], None, None]
                        dp("    " * level, cmd, state, "修正1")
                    else:
                        dp("    " * level, cmd, state, "无法修正1", features)

        elif lmr == (True, True, False):
            assert mid.elements.pop() is bi
            if not mid.elements:
                duan.features = [left, None, None]
                if len(features) >= 2:
                    if features[-1] == left:
                        duan.features = [features[-2], features[-1], None]
                        dp("    " * level, cmd, state, "修正2")
                    else:
                        dp("    " * level, cmd, state, "无法修正2", features)

        elif lmr == (True, True, True):
            assert right.elements.pop() is bi
            if not right.elements:
                duan.features = [left, mid, None]
                ddp("    " * level, cmd, state, "特征序列", features)
                if len(features) >= 3:
                    shape, (lm, mr) = triple_relation(features[-3], features[-2], features[-1])
                    ddp("    " * level, cmd, state, "关系", shape, lm, mr)
                    if features[-1] == mid:
                        duan.features = [features[-3], features[-2], features[-1]]
                        dp("    " * level, cmd, state, "修正3")
                    else:
                        dp("    " * level, cmd, state, "无法修正3", features)

        else:
            raise ChanException("无法匹配的关系", lmr)
        ddp("    " * level, cmd, state, "end", duan.features)

        duan.check()

    def push(self, bi: Bi, level=0):
        ddp()
        handler: "ZhongShus" = self._handler
        duans: List[Duan] = self.__duans
        feature: FeatureSequence = FeatureSequence.new(bi)
        cmd = "Duans.PUSH"
        if not duans:
            duan = Duan.new(0, bi)
            duans.append(duan)
            duan.features = [None, None, None]
            ddp("    " * level, cmd, "首次创建新段")
            return

        duan: Duan = duans[-1]
        last: Optional[Duan] = duan.pre
        flag: bool = last is not None
        left: Optional[FeatureSequence] = duan.features[0]
        mid: Optional[FeatureSequence] = duan.features[1]
        right: Optional[FeatureSequence] = duan.features[2]
        lmr: Tuple[bool, bool, bool] = (left is not None, mid is not None, right is not None)

        if flag:
            state = "老阳" if duan.direction is Direction.Down else "老阴"
        else:
            state = "少阳" if duan.direction is Direction.Up else "少阴"

        ddp("    " * level, cmd, state, lmr, bi)
        ddp("    " * level, duan.features)
        ddp("    " * level, duan.elements)

        duan.append_element(bi)
        if flag:
            last.append_element(bi)

        if duan.direction is bi.direction:
            ddp("    " * level, cmd, state, "方向相同, 无需分析")
            return

        if lmr == (False, False, False):
            duan.features = [feature, None, None]

        elif lmr == (True, False, False):
            relation = double_relation(left, bi)
            ddp("    " * level, cmd, state, "第二特征序列左中关系", relation)
            if relation is Direction.Left:
                # 顺序包含
                if bi not in left.elements:
                    left.elements.append(bi)

            elif relation is Direction.Right:
                if state == "老阳":
                    if bi.high > last.high:
                        # 向上一笔突破前高, 且为第二特征序列
                        ddp("    " * level, cmd, state, "特殊处理, 线段是否完成：", last.done)
                        last.done = False
                        last.features = [last.features[-2], last.features[-1], None]
                        Duan.pop(duans, duan)
                        handler is not None and handler.pop(last)
                        duan.clear()
                        ddp("    " * level, cmd, state, "弹出 清空")
                    else:
                        if bi not in left.elements:
                            left.elements.append(bi)
                elif state == "老阴":
                    if bi.low < duan.pre.features[1].low:
                        # 向下一笔突破前低, 且为第二特征序列
                        ddp("    " * level, cmd, state, "特殊处理, 线段是否完成：", last.done)
                        last.done = False
                        duan.pre.features = [last.features[-2], last.features[-1], None]
                        Duan.pop(duans, duan)
                        handler is not None and handler.pop(last)
                        duan.clear()
                        ddp("    " * level, cmd, state, "弹出 清空")
                    else:
                        if bi not in left.elements:
                            left.elements.append(bi)
                elif state == "少阳" or state == "少阴":
                    duan.features = [left, feature, None]
                else:
                    raise ChanException("无法匹配的状态", lmr, relation, state)

            elif relation in (Direction.Down, Direction.JumpDown):
                if state == "老阳" or state == "少阴":
                    duan.features = [left, feature, None]
                    duan.end = feature.start
                elif state == "老阴":
                    ddp("    " * level, cmd, state, "线段是否完成：", last.done)
                    last.done = False
                    last.features = [last.features[-3], last.features[-2], None]
                    Duan.pop(duans, duan)
                    handler is not None and handler.pop(last)
                    duan.clear()
                    ddp("    " * level, cmd, state, "弹出 清空")
                elif state == "少阳":
                    """此处有待商榷
                         1. 前面有线段,
                         2. 前面无线段
                    """
                    duan.features = [left, feature, None]
                    duan.end = feature.start

                else:
                    raise ChanException("无法匹配的状态", lmr, relation, state)

            elif relation in (Direction.Up, Direction.JumpUp):
                if state == "老阳":
                    # 第二特征序列
                    dp("    " * level, cmd, state, "线段是否完成：", last.done)
                    last.done = False
                    last.features = [last.features[-3], last.features[-2], None]
                    Duan.pop(duans, duan)
                    handler is not None and handler.pop(last)
                    duan.clear()
                    ddp("    " * level, cmd, state, "弹出 清空")
                elif state == "老阴" or state == "少阳":
                    duan.features = [left, feature, None]
                    duan.end = feature.start

                elif state == "少阴":
                    """此处有待商榷
                        1. 前面有线段,
                        2. 前面无线段
                    """
                    duan.features = [left, feature, None]
                    duan.end = feature.start

                else:
                    raise ChanException("无法匹配的状态", lmr, relation, state)

            else:
                duan.features[1] = feature

        elif lmr == (True, True, False):
            relation = double_relation(mid, bi)
            ddp("    " * level, cmd, state, "第三特征序列中右关系", relation)
            if relation is Direction.Left:
                if bi not in mid.elements:
                    mid.elements.append(bi)

            elif relation is Direction.Right:
                if state == "老阳" or state == "老阴":
                    if bi not in mid.elements:
                        mid.elements.append(bi)

                elif state == "少阳":
                    if mid.high == bi.high:
                        # 终结
                        duan.features = [left, mid, feature]
                        mid.shape = Shape.G
                        start = mid.start
                        elements = duan.set_done(start, state)
                        handler is not None and handler.push(duan)
                        assert duan.direction is not elements[0].direction
                        new = Duan.new(duan.index + 1, elements[0])
                        Duan.append(duans, new)
                        for obj in elements[1:]:
                            self.push(obj, level + 1)
                        if new.elements[1]:
                            new.end = new.elements[1].start
                        ddp("    " * level, "特殊终结")

                    else:
                        duan.features = [mid, feature, None]
                        duan.end = feature.start

                elif state == "少阴":
                    if mid.low == bi.low:
                        # 终结
                        duan.features = [left, mid, feature]
                        mid.shape = Shape.D
                        start = mid.start
                        elements = duan.set_done(start, state)
                        handler is not None and handler.push(duan)
                        assert duan.direction is not elements[0].direction
                        new = Duan.new(duan.index + 1, elements[0])
                        Duan.append(duans, new)
                        for obj in elements[1:]:
                            self.push(obj, level + 1)
                        if new.elements[1]:
                            new.end = new.elements[1].start
                        ddp("    " * level, "特殊终结")
                    else:
                        duan.features = [mid, feature, None]
                        duan.end = feature.start
                else:
                    raise ChanException("无法匹配的状态", lmr, relation, state)

            elif relation in (Direction.Down, Direction.JumpDown):
                if state == "老阳" or state == "少阴":
                    duan.features = [mid, feature, None]
                elif state == "老阴" or state == "少阳":
                    duan.features = [left, mid, feature]
                    mid.shape = Shape.G
                    start = mid.start
                    elements = duan.set_done(start, state)
                    handler is not None and handler.push(duan)
                    assert duan.direction is not elements[0].direction
                    new = Duan.new(duan.index + 1, elements[0])
                    Duan.append(duans, new)
                    # handler is not None and handler.push(new)
                    for obj in elements[1:]:
                        self.push(obj, level + 1)
                    if new.elements[1]:
                        new.end = new.elements[1].start

                    t = "终结"
                    if double_relation(left, mid) is Direction.JumpUp:
                        new.pre = duan
                        for obj in elements:
                            duan.append_element(obj)
                        # duan.elements.extend(elements)
                        t = "缺口"
                    ddp("    " * level, cmd, state, "顶分型,", t)

                else:
                    raise ChanException("无法匹配的状态", lmr, relation, state)

            elif relation in (Direction.Up, Direction.JumpUp):
                if state == "老阳" or state == "少阴":
                    duan.features = [left, mid, feature]
                    mid.shape = Shape.D
                    start = mid.start
                    elements = duan.set_done(start, state)
                    handler is not None and handler.push(duan)
                    assert duan.direction is not elements[0].direction
                    new = Duan.new(duan.index + 1, elements[0])
                    Duan.append(duans, new)
                    # handler is not None and handler.push(new)
                    for obj in elements[1:]:
                        self.push(obj, level + 1)
                    if new.elements[1]:
                        new.end = new.elements[1].start

                    t = "终结"
                    if double_relation(left, mid) is Direction.JumpDown:
                        new.pre = duan
                        for obj in elements:
                            duan.append_element(obj)
                        # duan.elements.extend(elements)
                        t = "缺口"
                    ddp("    " * level, cmd, state, "底分型,", t)

                elif state == "老阴" or state == "少阳":
                    duan.features = [mid, feature, None]
                    duan.end = feature.start

                else:
                    raise ChanException("无法匹配的状态", lmr, relation, state)

            else:
                raise ChanException

        else:
            raise ChanException("无法匹配的状态", lmr, state)

        left, mid, right = duan.features
        if left and mid:
            if double_relation(left, mid) is Direction.Left:
                ddp("左中关系错误")

        # ddp("    " * level, cmd, state, "end features", duan.features)
        # ddp("    " * level, cmd, state, "end duan", duans[-1])
        # dp("    " * level, cmd, state, "end, duans", self[-3:])
        # dp("    " * level, cmd, state, "end, Zhongshu", handler)


@charts_id_
class ZhongShu:
    __slots__ = "elements", "index", "level"

    def __init__(self, elements: List[Union[Bi, Duan]]):
        self.elements = elements
        self.index = 0
        self.level = 0

    def __str__(self):
        return f"中枢({self.elements})"

    def __repr__(self):
        return f"中枢({self.elements})"

    @property
    def left(self) -> Union[Bi, Duan]:
        return self.elements[0] if self.elements else None

    @property
    def mid(self) -> Union[Bi, Duan]:
        return self.elements[1] if len(self.elements) > 1 else None

    @property
    def right(self) -> Union[Bi, Duan]:
        return self.elements[2] if len(self.elements) > 2 else None

    @property
    def last(self) -> Union[Bi, Duan]:
        return self.elements[-1] if self.elements else None

    @property
    def direction(self) -> Direction:
        return Direction.Down if self.start.shape is Shape.D else Direction.Up

    @property
    def zg(self) -> float:
        return min(self.elements[:3], key=lambda o: o.high).high

    @property
    def zd(self) -> float:
        return max(self.elements[:3], key=lambda o: o.low).low

    @property
    def gg(self) -> float:
        return max(self.elements, key=lambda o: o.high).high

    @property
    def dd(self) -> float:
        return min(self.elements, key=lambda o: o.low).low

    def check(self) -> bool:
        return double_relation(self.left, self.right) in (
            Direction.Down,
            Direction.Up,
            Direction.Left,
            Direction.Right,
        )

    @property
    def high(self) -> float:
        return self.zg

    @property
    def low(self) -> float:
        return self.zd

    @property
    def start(self) -> FenXing:
        return self.left.start

    @property
    def end(self) -> FenXing:
        return self.elements[-1].end

    def pop_element(self, obj: Union[Bi, Duan]):
        # dp("准备删除中枢元素", obj)
        # dp("现有pop", self.elements)
        if self.last.start is obj.start:
            if self.last is not obj:
                dp("警告：中枢元素不匹配!!!", self.last, obj)
            self.elements.pop()
            # dp("完成删除中枢元素", obj)
        else:
            raise ChanException("中枢无法删除元素", self.last, obj)

    def append_element(self, obj: Union[Bi, Duan]):
        # dp("添加中枢元素", obj)
        # dp("现有中枢元素", self.elements)
        if self.last.end is obj.start:
            self.elements.append(obj)
        else:
            raise ChanException("中枢无法添加元素", self.last.end, obj.start)

    def is_next(self, obj: Union[Bi, Duan]) -> bool:
        return double_relation(self, obj) in (Direction.Right, Direction.Down)

    def charts(self):
        return [
            [
                self.start.mid.dt,
                self.start.mid.dt,
                self.end.mid.dt,
                self.end.mid.dt,
                self.start.mid.dt,
            ],
            [self.zg, self.zd, self.zd, self.zg, self.zg],
            "#993333" if self.direction is Direction.Up else "#99CC99",
            self.level + 1,
        ]

    def charts_jhl(self):
        return [
            [
                self.start.mid.dt,
                self.start.mid.dt,
                self.end.mid.dt,
                self.end.mid.dt,
                self.start.mid.dt,
            ],
            [self.zg, self.zd, self.zd, self.zg, self.zg],
            "#CC0033" if self.direction is Direction.Up else "#66CC99",
            self.level + 2,
        ]


class ZhongShus:
    def __init__(self, duans: List[Duan], zss: List[ZhongShu], handler):
        if zss is None:
            zss = []
        self.__duans = duans
        self.__zhongshus = zss
        self.handler = handler

    def __len__(self):
        return len(self.__zhongshus)

    def __getitem__(self, item):
        return self.__zhongshus[item]

    def __setitem__(self, key, value):
        self.__zhongshus[key] = value

    def __delitem__(self, key):
        del self.__zhongshus[key]

    def __iter__(self):
        return iter(self.__zhongshus)

    def __str__(self):
        return f"中枢列表({self.__zhongshus})"

    def __repr__(self):
        return f"中枢列表({self.__zhongshus})"

    def push(self, obj: Union[Bi, Duan], level: int = 0):
        zss = self.__zhongshus
        new = ZhongShu([obj])
        if not zss:
            zss.append(new)
            return
        last = zss[-1]
        if len(last.elements) >= 3:
            if double_relation(last, obj) in (Direction.JumpDown, Direction.JumpUp):
                # 第三买卖点
                zss.append(new)
                return

        last.append_element(obj)
        size = len(last.elements)
        if size == 3:
            if double_relation(last.left, last.right) in (Direction.JumpUp, Direction.JumpDown):
                last.elements.pop(0)
                return

        if size >= 5 and size % 2 == 1:
            relation = double_relation(last, obj)
            if relation in (Direction.JumpUp, Direction.JumpDown):
                # 第三买卖点
                new.index = last.index + 1
                zss.append(new)

    def pop(self, obj: Union[Bi, Duan]):
        zss = self.__zhongshus

        if not zss:
            return
        last = zss[-1]
        last.pop_element(obj)
        if last.last is None:
            zss.pop()
            if zss:
                last = zss[-1]
                if obj is last.last:
                    dp("递归删除中枢元素", obj)
                    self.pop(obj)


@dataclass
class PanZheng:
    start: Union[Bi, Duan]
    body: ZhongShu
    end: Union[Bi, Duan]


@dataclass
class ZouShi:
    body: List[Union[PanZheng, Duan, Bi]]


@dataclass
class FeatureSequence:
    elements: List
    direction: Direction
    shape: Shape = None
    index: int = 0

    def __str__(self):
        if not self.elements:
            return f"空特征序列({self.direction})"
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)})"

    def __repr__(self):
        if not self.elements:
            return f"空特征序列({self.direction})"
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)})"

    @property
    def start(self) -> FenXing:
        if not self.elements:
            raise ChanException("数据异常", self)
        func = min
        if self.direction is Direction.Down:
            func = max
        return func([obj.start for obj in self.elements], key=lambda fx: fx.speck)

    @property
    def end(self) -> FenXing:
        if not self.elements:
            raise ChanException("数据异常", self)
        func = min
        if self.direction is Direction.Down:
            func = max
        return func([obj.end for obj in self.elements], key=lambda fx: fx.speck)

    @property
    def high(self) -> float:
        return max([self.end, self.start], key=lambda fx: fx.speck).speck

    @property
    def low(self) -> float:
        return min([self.end, self.start], key=lambda fx: fx.speck).speck

    def put(self, obj: Union[Bi, Duan], is_right=True):
        if self.direction is obj.direction:
            relation = double_relation(self, obj)
            if relation is Direction.Left:
                self.elements.append(obj)
            elif relation is Direction.Right and is_right:
                self.elements.append(obj)

    def check(self) -> bool:
        flag = True
        for obj in self.elements:
            if obj.direction is not self.direction:
                flag = False
                print(obj, self.direction)
        return flag

    @classmethod
    def new(cls, obj: Union[Bi, Duan]):
        return cls([obj], obj.direction)

    @staticmethod
    def analysis(bis, direction):
        result: List[FeatureSequence] = []
        for obj in bis:
            if obj.direction is not direction:
                continue
            if result:
                last = result[-1]

                if double_relation(last, obj) in (Direction.Left,):
                    last.elements.append(obj)
                else:
                    result.append(FeatureSequence([obj], obj.direction))
                    # dp("FS.ANALYSIS", double_relation(last, obj))
            else:
                result.append(FeatureSequence([obj], obj.direction))
        return result


class KlineGenerator:
    def __init__(self, arr=[3, 2, 5, 3, 7, 4, 7, 2.5, 5, 4, 8, 6]):
        self.dt = datetime(2021, 9, 3, 19, 50, 40, 916152)
        self.arr = arr

    def up(self, start, end, size=5):
        n = 0
        m = round(abs(start - end) * (1 / size), 8)
        o = start
        # c = round(o + m, 4)

        while n < size:
            c = round(o + m, 4)
            yield RawBar(self.dt, o, c, o, c, 1)
            o = c
            n += 1
            self.dt = datetime.fromtimestamp(self.dt.timestamp() + 60 * 60)

    def down(self, start, end, size=5):
        n = 0
        m = round(abs(start - end) * (1 / size), 8)
        o = start
        # c = round(o - m, 4)

        while n < size:
            c = round(o - m, 4)
            yield RawBar(self.dt, o, o, c, c, 1)
            o = c
            n += 1
            self.dt = datetime.fromtimestamp(self.dt.timestamp() + 60 * 60)

    @property
    def result(self):
        size = len(self.arr)
        i = 0
        # sizes = [5 for i in range(l)]
        result = []
        while i + 1 < size:
            s = self.arr[i]
            e = self.arr[i + 1]
            if s > e:
                for k in self.down(s, e):
                    result.append(k)
            else:
                for k in self.up(s, e):
                    result.append(k)
            i += 1
        return result


class CZSCAnalyzer:
    def __init__(self, symbol: str, freq: int, freqs: List[int] = None):
        self.symbol = symbol
        self.freq = freq
        self.freqs = freqs or [freq]
        self._bars = []
        self._news = []
        self._fxs = []
        self._bis = []
        self._duans = []
        self._bi_zs = []
        self._duan_zs = []

        self.raws = RawBars(self._bars, self.freq)
        self.news = NewBars(self._news)
        self.bi_ZhongShus = ZhongShus(self._bis, self._bi_zs, None)
        self.duan_ZhongShus = ZhongShus(self._duans, self._duan_zs, None)
        self.duans = Duans(self._bis, self._duans, self.duan_ZhongShus)
        self.bis = Bis(None, self._bis, (self.bi_ZhongShus, self.duans))

    def check_duans(self):
        for i in range(1, len(self._duans)):
            print(self.duans[i], self.duans[i - 1].end is self.duans[i].start)
            if self.duans[i - 1].end is not self.duans[i].start:
                print(f"第{i}段段未结束")

    def process_zss(self):
        for duan in self.duans:
            self.duan_ZhongShus.push(duan)
        dp(f"共{len(self.duan_ZhongShus)}个段中枢")
        for bi in self.bis:
            self.bi_ZhongShus.push(bi)
        dp(f"共{len(self.bi_ZhongShus)}个笔中枢")

    @classmethod
    def load_bytes_file(cls, path: str):
        with open(path, "rb") as f:
            b = Bitstamp.load_bytes("btcusd", f.read())
            b.check_duans()
            b.process_zss()

    @final
    def step(
        self,
        dt: datetime | int | str,
        open: float | str,
        high: float | str,
        low: float | str,
        close: float | str,
        volume: float | str,
    ):
        if type(dt) is datetime:
            ...
        elif isinstance(dt, str):
            dt: datetime = datetime.fromtimestamp(int(dt))
        elif isinstance(dt, int):
            dt: datetime = datetime.fromtimestamp(dt)
        else:
            raise ChanException("类型不支持", type(dt))
        open = float(open)
        high = float(high)
        low = float(low)
        close = float(close)
        volume = float(volume)

        index = 0

        last = RawBar(
            dt=dt,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            index=index,
        )
        self.push(last)

    def push(self, k: RawBar):
        self.raws.push(k)
        self.news.push(self.raws[-1])
        try:
            fx = FenXing(self._news[-3], self._news[-2], self._news[-1])
            self.bis.analysis(fx, self._news, 0)

        except IndexError:
            traceback.print_exc()

        except Exception as e:
            self.toCharts()
            # with open(f"{self.symbol}-{int(self._bars[0].dt.timestamp())}-{int(self._bars[-1].dt.timestamp())}.dat", "wb") as f:
            #    f.write(self.save_bytes())

            raise e

    @classmethod
    def load_bytes(cls, symbol, bytes_data) -> "Self":
        size = struct.calcsize(">6d")
        obj = cls(symbol, Freq.m5)
        while bytes_data:
            t = bytes_data[:size]
            k = RawBar.from_bytes(t)
            obj.push(k)
            bytes_data = bytes_data[size:]
            if len(bytes_data) < size:
                break
        return obj

    def save_bytes(self) -> bytes:
        data = b""
        for k in self._bars:
            data += bytes(k)
        return data

    def toCharts(self, path: str = "czsc.html", useReal=False, freq=""):
        import echarts_plot  # czsc

        reload(echarts_plot)
        kline_pro = echarts_plot.kline_pro
        fx = [{"dt": fx.dt, "fx": fx.low if fx.shape is Shape.D else fx.high} for fx in self.bis.fxs]
        bi = [{"dt": fx.dt, "bi": fx.low if fx.shape is Shape.D else fx.high} for fx in self.bis.fxs]

        # xd = [{"dt": fx.dt, "xd": fx.low if fx.shape is Shape.D else fx.high} for fx in self.xd_fxs]

        xd = []
        mergers = []
        for duan in self._duans:
            xd.extend(duan.charts())
            left, mid, right = duan.features
            if left:
                if len(left.elements) > 1:
                    mergers.append(left)
            if mid:
                if len(mid.elements) > 1:
                    mergers.append(mid)
            if right:
                if len(right.elements) > 1:
                    mergers.append(right)
            else:
                print("right is None")
        bzs = None  # for zs in self.bi_zs]
        dzs = None  # [zs.charts() for zs in self.xd_zs]
        dzs = [zs.charts() for zs in self.duan_ZhongShus]
        bzs = [zs.charts() for zs in self.bi_ZhongShus]

        charts = kline_pro(
            [x.candleDict() for x in self._bars] if useReal else [x.candleDict() for x in self._news],
            fx=fx,
            bi=bi,
            xd=xd,
            mergers=mergers,
            bzs=bzs,
            dzs=dzs,
            title=self.symbol + "-" + freq,
            width="100%",
            height="80%",
        )

        charts.render(path)
        return charts

    def xd(self):
        _duans = []
        d = Duans(self._bis, _duans, None)
        for bi in self._bis:
            d.push(bi)
        self._duans = _duans
        self.toCharts()


class Bitstamp(CZSCAnalyzer):
    """ """

    def __init__(self, symbol: str, freq: Freq, size: int = 0):
        super().__init__(symbol, freq.value)
        self.freq: int = freq.value

    def init(self, size):
        self.left_date_timestamp: int = int(datetime.now().timestamp() * 1000)
        left = int(self.left_date_timestamp / 1000) - self.freq * size
        if left < 0:
            raise ChanException
        _next = left
        while 1:
            data = self.ohlc(self.symbol, self.freq, _next, _next := _next + self.freq * 1000)
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
                    raise e

            # start = int(data["data"]["ohlc"][0]["timestamp"])
            end = int(data["data"]["ohlc"][-1]["timestamp"])

            _next = end
            if len(data["data"]["ohlc"]) < 1000:
                break

    @staticmethod
    def ohlc(pair: str, step: int, start: int, end: int, length: int = 1000) -> Dict:
        proxies = {
            "http": '"http://127.0.0.1:11809',
            "https": "http://127.0.0.1:11809",
        }
        s = requests.Session()

        s.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "content-type": "application/json",
        }
        url = f"https://www.bitstamp.net/api/v2/ohlc/{pair}/?step={step}&limit={length}&start={start}&end={end}"
        resp = s.get(url, timeout=5, proxies=proxies)
        json = resp.json()
        # print(json)
        return json


if __name__ == "__main__":
    bitstamp = Bitstamp("btcusd", freq=Freq.m5, size=3500)
    bitstamp.init(3000)
    print(f"中枢[笔]", len(bitstamp.bi_ZhongShus))
    # bitstamp.check_duans()
    # bitstamp.process_zss()

    bitstamp.toCharts()
    # bitstamp.xd()
