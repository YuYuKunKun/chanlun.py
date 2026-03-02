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

import asyncio
import bisect
import builtins
import io
import json
import math
import os
import struct
import re
import sys
import time
import traceback
import uuid
from abc import abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from pprint import pprint
from random import randint, choice, sample, seed, random, uniform
from threading import Thread
from typing import (
    List,
    Self,
    Optional,
    Tuple,
    final,
    Dict,
    Any,
    Final,
    SupportsInt,
    Union,
    Sequence,
    Callable,
    Generator,
    Set,
)

import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from termcolor import colored


# from collections.abc import Sequence


def ts2int(timestamp: str):
    return int(time.mktime(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timetuple()))


def int2dt(timestamp: SupportsInt) -> datetime:
    return datetime.fromtimestamp(int(timestamp))  # .strftime("%Y-%m-%d %H:%M:%S")


def to_datetime(ts):
    """
    将不同类型的时间戳转换为datetime对象（统一比较标准）
    支持：datetime对象、字符串（"%Y-%m-%d %H:%M:%S"）、数值型时间戳（秒级）
    可根据实际需求扩展时间格式（如毫秒级、仅日期等）
    """
    if isinstance(ts, datetime):
        return ts
    elif isinstance(ts, str):
        # 自定义时间字符串格式，按需修改（如"%Y-%m-%d"）
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    elif isinstance(ts, (int, float)):
        # 若为毫秒级时间戳，需除以1000：return datetime.fromtimestamp(ts / 1000)
        return datetime.fromtimestamp(ts)
    else:
        raise TypeError(f"不支持的时间戳类型: {type(ts)}")


def 模糊查找目标时间戳(k线序列: List["K线"], 目标时间戳: datetime):
    时间戳序列 = [k.时间戳 for k in k线序列]
    # 二分查找插入位置（O(log n) 效率）
    序号 = bisect.bisect_left(时间戳序列, 目标时间戳)
    # 确定前驱和后继
    if 序号 == 0:
        # 目标小于所有元素
        prev, next_ = None, 时间戳序列[0]
    elif 序号 == len(时间戳序列):
        # 目标大于所有元素
        print("模糊查找目标时间戳: None, 当前时间戳: ", 时间戳序列[-1], 目标时间戳)
        prev, next_ = 时间戳序列[-1], None
        # prev, next_ = 时间戳序列[-1], 目标时间戳
    else:
        if 时间戳序列[序号] == 目标时间戳:
            # 目标存在于时序中
            prev = next_ = 时间戳序列[序号]
        else:
            # 目标在两个元素之间
            prev = 时间戳序列[序号 - 1]
            next_ = 时间戳序列[序号]

    return prev, next_


class 时间周期:
    def __init__(self, 秒: int, 是否单笔交易: bool = False):
        self._秒 = 秒
        self.是否单笔交易 = 是否单笔交易

    def __int__(self):
        return self._秒

    def __repr__(self):
        return f"时间周期<{self._秒}, {self.是否单笔交易}>"

    def __str__(self):
        return f"时间周期<{self._秒}, {self.是否单笔交易}>"

    @classmethod
    def BitstampSupport(cls):
        return {60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200}

    @classmethod
    def 秒(cls, value: int):
        return cls(value)

    @classmethod
    def 分(cls, value: int):
        return cls(60 * value)

    @classmethod
    def 时(cls, value: int):
        return cls(60 * 60 * value)

    @classmethod
    def 天(cls, value: int):
        return cls(60 * 60 * 24 * value)

    @classmethod
    def 周(cls, value: int):
        return cls(60 * 60 * 24 * 7 * value)

    @classmethod
    def 秒数转周期(cls, 秒数: int) -> str:
        """
        智能选择最精确的周期单位

        Args:
            秒数: 输入的秒数值，必须是正整数

        Returns:
            周期字符串，格式为：数字 + 单位（H=小时，D=天，W=周，M=月）
        """
        if not isinstance(秒数, int) or 秒数 <= 0:
            raise ValueError("秒数必须是正整数")

        一分钟秒数 = 60
        一小时秒数 = 一分钟秒数 * 60  # 3600
        一天秒数 = 24 * 一小时秒数
        一周秒数 = 7 * 一天秒数
        一月秒数 = 30 * 一天秒数

        # 计算各周期单位
        月数 = 秒数 // 一月秒数
        月余秒 = 秒数 % 一月秒数

        周数 = 秒数 // 一周秒数
        周余秒 = 秒数 % 一周秒数

        天数 = 秒数 // 一天秒数
        天余秒 = 秒数 % 一天秒数

        小时数 = 秒数 // 一小时秒数
        时余数 = 秒数 % 一小时秒数

        分钟数 = 秒数 // 一分钟秒数
        分钟余数 = 秒数 % 一分钟秒数

        if 分钟余数:
            return str(秒数)

        # 选择最精确的单位
        # 优先选择余数为0的单位，如果没有，选择余数最小的单位

        # 找出所有可能的表示方式及其余数
        选项 = [(月数, "M", 月余秒), (周数, "W", 周余秒), (天数, "D", 天余秒), (小时数, "H", 时余数), (分钟数, "", 分钟余数)]

        # 过滤掉数值为0的选项（小时除外）
        有效选项 = [(值, 单位, 余数) for 值, 单位, 余数 in 选项 if 值 > 0]

        # 如果没有有效选项，使用小时
        if not 有效选项:
            return str(秒数)

        # 优先选择余数为0的选项
        无余数选项 = [(值, 单位, 余数) for 值, 单位, 余数 in 有效选项 if 余数 == 0]
        if 无余数选项:
            # 选择单位最大的无余数选项
            值, 单位, _ = min(无余数选项, key=lambda x: (x[0], len(x[1])))
            return f"{值}{单位}"

        # 如果没有无余数选项，选择余数最小的选项
        值, 单位, _ = min(有效选项, key=lambda x: x[2])
        return f"{值}{单位}"

    @classmethod
    def 周期转秒数(cls, 周期字符串: str) -> int:
        """
        将带单位的周期字符串转换为秒数

        Args:
            周期字符串: 带单位的周期字符串，如 "15M", "60", "25H", "2D", "1W"

        Returns:
            对应的秒数值

        Raises:
            ValueError: 如果输入格式不正确或包含无效字符
        """
        # 去除字符串两端的空格
        周期字符串 = 周期字符串.strip().upper()

        # 如果字符串为空，抛出异常
        if not 周期字符串:
            raise ValueError("周期字符串不能为空")

        # 检查字符串是否以单位结尾
        if 周期字符串[-1].isalpha():
            # 提取数值部分和单位部分
            单位 = 周期字符串[-1]
            数值部分 = 周期字符串[:-1]

            # 验证数值部分是否为有效数字
            if not 数值部分.isdigit():
                raise ValueError(f"无效的数值部分: {数值部分}")

            数值 = int(数值部分)

            # 根据单位计算秒数
            if 单位 == "M":  # 月
                return 数值 * 2592000
            elif 单位 == "H":  # 小时
                return 数值 * 3600
            elif 单位 == "D":  # 天
                return 数值 * 86400
            elif 单位 == "W":  # 周
                return 数值 * 604800
            else:
                raise ValueError(f"不支持的单位: {单位}")
        else:
            # 没有单位，默认为分钟
            if not 周期字符串.isdigit():
                raise ValueError(f"无效的数值: {周期字符串}")

            数值 = int(周期字符串)
            return 数值 * 60


class 相对方向(Enum):
    向上 = "交叠向上"
    向下 = "交叠向下"
    向上缺口 = "向上缺口"
    向下缺口 = "向下缺口"
    衔接向上 = "衔接向上"  # 前终点为后起点
    衔接向下 = "衔接向下"  # 前终点为后起点
    顺 = "顺序包含"  # 左边包含右边
    逆 = "逆序包含"  # 右边包含左边
    同 = "相同包含"  # 左右两边数值相同

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __int__(self):
        match self:
            case 相对方向.向上缺口:
                return 3
            case 相对方向.衔接向上:
                return 2
            case 相对方向.向上:
                return 1
            case 相对方向.顺:
                return 8
            case 相对方向.同:
                return 0
            case 相对方向.逆:
                return -8
            case 相对方向.向下:
                return -1
            case 相对方向.衔接向下:
                return -2
            case 相对方向.向下缺口:
                return -3

    def 翻转(self) -> "相对方向":  # 反转
        match self:
            case 相对方向.向上:
                return 相对方向.向下
            case 相对方向.向下:
                return 相对方向.向上
            case 相对方向.向下缺口:
                return 相对方向.向上缺口
            case 相对方向.向上缺口:
                return 相对方向.向下缺口
            case 相对方向.衔接向上:
                return 相对方向.衔接向下
            case 相对方向.衔接向下:
                return 相对方向.衔接向上
            case 相对方向.顺:
                return 相对方向.逆
            case 相对方向.逆:
                return 相对方向.顺
            case _:
                return self

    def 是否向上(self) -> bool:
        if "上" in self.value:
            return True
        return False

    def 是否向下(self) -> bool:
        if "下" in self.value:
            return True
        return False

    def 是否包含(self) -> bool:
        if "包含" in self.value:
            return True
        return False

    def 是否缺口(self) -> bool:
        if "缺口" in self.value:
            return True
        return False

    def 是否衔接(self) -> bool:
        if "衔接" in self.value:
            return True
        return False

    @classmethod
    def 非包含序列(cls) -> Tuple["相对方向", "相对方向", "相对方向", "相对方向", "相对方向", "相对方向"]:
        return (
            相对方向.向上,
            相对方向.向下,
            相对方向.向上缺口,
            相对方向.向下缺口,
            相对方向.衔接向上,
            相对方向.衔接向下,
        )

    @classmethod
    def 包含序列(cls) -> Tuple["相对方向", "相对方向", "相对方向"]:
        return (
            相对方向.顺,
            相对方向.逆,
            相对方向.同,
        )

    @classmethod
    def 识别(cls, 前, 后) -> "相对方向":
        if 前.高 == 后.高 and 前.低 == 后.低:
            return 相对方向.同

        if 前.高 > 后.高 and 前.低 > 后.低:
            if 前.低 == 后.高:
                return 相对方向.衔接向下
            if 前.低 > 后.高:
                return 相对方向.向下缺口
            return 相对方向.向下

        if 前.高 < 后.高 and 前.低 < 后.低:
            if 前.高 == 后.低:
                return 相对方向.衔接向上
            if 前.高 < 后.低:
                return 相对方向.向上缺口
            return 相对方向.向上

        if 前.高 >= 后.高 and 前.低 <= 后.低:
            return 相对方向.顺

        if 前.高 <= 后.高 and 前.低 >= 后.低:
            return 相对方向.逆
        raise RuntimeError("无法识别的方向", 前, 后)

    @staticmethod
    def 从序列中机选(
        数量: int,
        可选方向: List["相对方向"],
        可重复: bool = True,  # 是否允许重复选择
    ) -> Generator["相对方向", None, None]:
        if not 可重复 and 数量 > len(可选方向):
            raise ValueError("数量超过可选方向数")

        if 可重复:
            while 数量 > 0:
                yield choice(可选方向)
                数量 -= 1
        else:
            yield from sample(可选方向, 数量)  # 使用random.sample


class 分型结构(Enum):
    上 = "三连向上"
    下 = "三连向下"
    顶 = "顶分型"
    底 = "底分型"
    散 = "向右扩散"

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @classmethod
    def 识别(cls, 左, 中, 右, 可以逆序包含: bool = False, 忽视顺序包含: bool = False) -> Optional["分型结构"]:
        左中关系 = 相对方向.识别(左, 中)
        中右关系 = 相对方向.识别(中, 右)
        左右关系 = 相对方向.识别(左, 右)

        match (左中关系, 中右关系):
            case (相对方向.顺, _):
                if 忽视顺序包含:
                    ...  # print("顺序包含 左中相对方向", 左, 中)
                else:
                    raise ValueError("顺序包含 左中相对方向", 左, 中)
            case (_, 相对方向.顺):
                if 忽视顺序包含:
                    ...  # print("顺序包含 中右相对方向", 中, 右)
                else:
                    raise ValueError("顺序包含 中右相对方向", 中, 右)

            case (相对方向.向上 | 相对方向.向上缺口 | 相对方向.衔接向上, 相对方向.向上 | 相对方向.向上缺口 | 相对方向.衔接向上):
                return 分型结构.上
            case (相对方向.向上 | 相对方向.向上缺口 | 相对方向.衔接向上, 相对方向.向下 | 相对方向.向下缺口 | 相对方向.衔接向下):
                return 分型结构.顶
            case (相对方向.向上 | 相对方向.向上缺口 | 相对方向.衔接向上, 相对方向.逆) if 可以逆序包含:
                return 分型结构.上

            case (相对方向.向下 | 相对方向.向下缺口 | 相对方向.衔接向下, 相对方向.向上 | 相对方向.向上缺口 | 相对方向.衔接向上):
                return 分型结构.底
            case (相对方向.向下 | 相对方向.向下缺口 | 相对方向.衔接向下, 相对方向.向下 | 相对方向.向下缺口 | 相对方向.衔接向下):
                return 分型结构.下
            case (相对方向.向下 | 相对方向.向下缺口 | 相对方向.衔接向下, 相对方向.逆) if 可以逆序包含:
                return 分型结构.下

            case (相对方向.逆, 相对方向.向上 | 相对方向.向上缺口 | 相对方向.衔接向上) if 可以逆序包含:
                return 分型结构.底
            case (相对方向.逆, 相对方向.向下 | 相对方向.向下缺口 | 相对方向.衔接向下) if 可以逆序包含:
                return 分型结构.顶
            case (相对方向.逆, 相对方向.逆) if 可以逆序包含:
                return 分型结构.散
            case _:
                print("未匹配的关系", 可以逆序包含, 左中关系, 中右关系)
        return None


class 指令:
    增: Final[str] = "APPEND"
    改: Final[str] = "MODIFY"
    删: Final[str] = "REMOVE"

    def __init__(self, 命令: str, 备注: str) -> None:
        self.指令 = 命令
        self.备注 = 备注

    def __str__(self):
        return f"{self.指令.upper()}"

    @classmethod
    def 添加(cls, 标识: str) -> Self:
        return cls(cls.增, 标识)

    @classmethod
    def 修改(cls, 标识: str) -> Self:
        return cls(cls.改, 标识)

    @classmethod
    def 删除(cls, 标识: str) -> Self:
        return cls(cls.删, 标识)


@final
class 缺口:
    """详情见 77课"""

    强势 = "强势"  # 不回补
    平势 = "平势"  # 回补后继续延续原有走势(新高；新低)
    弱势 = "弱势"  # 回补后走势翻转(与原有走势发生相反的走向)

    def __init__(self, 高: float, 低: float) -> None:
        self.高 = 高
        self.低 = 低

    def __str__(self) -> str:
        return f"缺口区间<{self.低} <=> {self.高}>"

    def __repr__(self) -> str:
        return f"缺口区间<{self.低} <=> {self.高}>"


class 三折叠(list):
    __slots__ = [
        "标识",
    ]

    def __init__(self, 左: Union["虚线", "笔", "线段"], 中: Union["虚线", "笔", "线段"], 右: Union["虚线", "笔", "线段"]):
        super().__init__([左, 中, 右])
        self.标识 = self.__class__.__name__

    @property
    def 左(self) -> Optional[Union["虚线", "笔", "线段"]]:
        return self[0] if len(self) > 0 else None

    @property
    def 中(self) -> Optional[Union["虚线", "笔", "线段"]]:
        return self[1] if len(self) > 1 else None

    @property
    def 右(self) -> Optional[Union["虚线", "笔", "线段"]]:
        return self[2] if len(self) > 2 else None

    @property
    def 连续性(self) -> bool:
        if self.左.之后是(self.中) and self.中.之后是(self.右):
            return True
        return False

    @property
    def 重叠区域(self) -> Optional[缺口]:
        if self.连续性 and not 相对方向.识别(self.左, self.右).是否缺口():
            return 缺口(
                高=min([self.左, self.中, self.右], key=lambda o: o.高).高,
                低=max([self.左, self.中, self.右], key=lambda o: o.低).低,
            )
        return None

    def 校验合法性(self) -> bool:
        if len(self) < 3:
            return False
        if self.重叠区域 is None:
            return False
        return True

    @classmethod
    def 基础判断(
        cls,
        左: Union["笔", "线段", "虚线"],
        中: Union["笔", "线段", "虚线"],
        右: Union["笔", "线段", "虚线"],
        关系=None,
    ) -> bool:
        if 关系 is None:
            关系 = [相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同]
        if not 左.之后是(中):
            return False
        if not 中.之后是(右):
            return False
        """
        if not 相对方向.识别(左, 中).是否包含():
            return False
        if not 相对方向.识别(中, 右).是否包含():
            return False
        """
        return 相对方向.识别(左, 右) in 关系


class 买卖点类型(Enum):
    一买 = "一买"
    一卖 = "一卖"
    二买 = "二买"
    二卖 = "二卖"
    三买 = "三买"
    三卖 = "三卖"

    @property
    def 是买点(self) -> bool:
        return "买" in self.value

    @property
    def 是卖点(self) -> bool:
        return "卖" in self.value


class 基础买卖点:
    def __init__(self, 类型: 买卖点类型, 当前K线: "K线", 买卖点K线: "K线", 备注: str, 中枢破位值: float):
        self.备注: str = 备注
        self.类型 = 类型
        self.买卖点K线 = 买卖点K线.镜像
        self.__当前K线: "K线" = 当前K线
        self.失效K线: Optional["K线"] = None
        self.终结K线: Optional["K线"] = None  # 卖出 or 买入
        self.__破位值 = 中枢破位值
        self.操作记录 = list()
        self.所属_笔 = None
        self.所属_线段 = None

    def __str__(self):
        return f"{self.类型.value}<{self.买卖点K线}, {self.偏移}, {self.失效偏移}>"

    def __repr__(self):
        return f"{self.类型.value}<{self.买卖点K线}, {self.偏移}, {self.失效偏移}>"

    @property
    def 破位值(self) -> float:
        return self.__破位值

    @property
    def 偏移(self) -> int:
        return self.__当前K线.序号 - self.买卖点K线.序号

    @property
    def 失效偏移(self) -> int:
        if self.失效K线 is None:
            return -1
        return self.失效K线.序号 - self.买卖点K线.序号

    @property
    def 有效性(self) -> bool:
        return self.失效K线 is not None


@final
class 买卖点(基础买卖点):
    @classmethod
    def 一卖点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.一卖, 买卖点K线=买卖点分型.中, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 一买点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.一买, 买卖点K线=买卖点分型.中, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 二卖点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.二卖, 买卖点K线=买卖点分型.中, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 二买点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.二买, 买卖点K线=买卖点分型.中, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 三卖点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.三卖, 买卖点K线=买卖点分型.中, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 三买点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.三买, 买卖点K线=买卖点分型.中, 当前K线=当前K线, 中枢破位值=中枢破位值)


class 缠论配置:
    def __init__(self):
        self.笔内元素数量: int = 5  # 成BI最低长度
        self.笔内缺口判定为元素: bool = False  # 跳空是否判定为 NewBar
        self.笔内缺口判定为元素比例: float = 0.07  # 当跳空是否判定为 NewBar时, 此值大于0时按照缺口所占比例判定是否为NewBar，等于0时直接判定为NerBar
        self.笔内缺口占比强制成笔: bool = False  # 依赖 <笔内缺口判定为元素>
        self.笔内缺口占比: float = 0.23

        self.笔内相同终点取舍: bool = False  # 一笔终点存在多个终点时 True: last, False: first
        self.笔内起始分型包含整笔: bool = False  # True: 一笔起始分型高低包含整支笔对象则不成笔, False: 只判断分型中间数据是否包含

        self.笔次级成笔: bool = False
        self.ANALYZER_AUTO_LEVEL: bool = True  # True 非同级别 反之同级别
        self.基础分析保存原始K线: bool = True  # 是否保存raw bar
        self.分析_笔: bool = True  # 是否计算BI
        self.分析_线段: bool = True  # 是否计算XD
        self.分析笔中枢: bool = True  # 是否计算BI中枢
        self.分析线段中枢: bool = True  # 是否计算XD中枢
        self.基础分析计算MACD: bool = True  # 是否计算MACD
        self.图表展示: bool = True
        self.MACD_FAST_PERIOD: int = 12
        self.MACD_SLOW_PERIOD: int = 26
        self.MACD_SIGNAL_PERIOD: int = 9
        self.通风报信: bool = False
        self.推送K线: bool = True
        self.推送笔: bool = True
        self.推送线段: bool = True
        self.图表显示详细信息_笔: bool = False
        self.图表显示详细信息_线段: bool = False
        self.图表显示详细信息_中枢: bool = False

        self.买卖点偏移 = 2  # 最小偏移


class MACD趋势方向(str, Enum):
    """MACD趋势方向枚举"""

    多头 = "多头"
    空头 = "空头"
    震荡 = "震荡"


class MACD信号(str, Enum):
    """MACD交易信号枚举"""

    金叉 = "金叉"
    死叉 = "死叉"
    顶背离 = "顶背离"
    底背离 = "底背离"
    无信号 = "无信号"


class 平滑异同移动平均线(BaseModel):
    # 原始数据
    时间戳: datetime = Field(..., description="数据点对应的时间")
    收盘价: float = Field(..., description="当前K线的收盘价格")

    # 计算参数
    快线周期: int = Field(12, gt=0, description="短期EMA周期，默认为12")
    慢线周期: int = Field(26, gt=0, description="长期EMA周期，默认为26")
    信号周期: int = Field(9, gt=0, description="信号线EMA周期，默认为9")

    # 核心指标值
    DIF: Optional[float] = Field(None, description="差离值 = EMA(快线) - EMA(慢线)")
    DEA: Optional[float] = Field(None, description="信号线 = EMA(DIF, 信号周期)")
    MACD柱: Optional[float] = Field(None, description="MACD柱状图 = (DIF - DEA) * 2")

    # EMA中间值（用于增量计算）
    快线EMA: Optional[float] = Field(None, description="快线EMA的当前值")
    慢线EMA: Optional[float] = Field(None, description="慢线EMA的当前值")
    DEA_EMA: Optional[float] = Field(None, description="DEA的EMA当前值")

    # 衍生指标
    趋势方向: Optional[MACD趋势方向] = Field(None, description="当前MACD趋势方向")
    信号: MACD信号 = Field(MACD信号.无信号, description="当前MACD交易信号")

    # 模型配置
    model_config = {
        "arbitrary_types_allowed": True,  # 允许特殊类型
        "json_encoders": {
            datetime: lambda v: v.isoformat(),  # 日期时间序列化
            Enum: lambda v: v.value,  # 枚举值序列化
        },
    }

    def 生成交易信号(self, 前一指标: Optional["平滑异同移动平均线"] = None) -> MACD信号:
        """根据当前状态生成交易信号（简化逻辑）"""
        if not self.DIF or not self.DEA:
            return MACD信号.无信号

        # 金叉/死叉检测
        if 前一指标 and 前一指标.DIF and 前一指标.DEA:
            if self.DIF > self.DEA and 前一指标.DIF <= 前一指标.DEA:
                return MACD信号.金叉
            if self.DIF < self.DEA and 前一指标.DIF >= 前一指标.DEA:
                return MACD信号.死叉

        # 零轴穿越检测
        if self.DIF > 0 and 前一指标 and 前一指标.DIF and 前一指标.DIF <= 0:
            return MACD信号.金叉
        if self.DIF < 0 and 前一指标 and 前一指标.DIF and 前一指标.DIF >= 0:
            return MACD信号.死叉

        return self.信号

    @classmethod
    def 首次计算(cls, 初始收盘价: float, 初始时间: datetime, 快线周期: int = 12, 慢线周期: int = 26, 信号周期: int = 9) -> "平滑异同移动平均线":
        """
        首次计算MACD指标（没有历史数据时使用）

        :param 初始收盘价: 第一个数据点的收盘价
        :param 初始时间: 第一个数据点的时间戳
        :param 快线周期:
        :param 慢线周期:
        :param 信号周期:
        :return: MACD指标对象
        """
        # 初始化EMA值（使用第一个收盘价）
        快线EMA = 初始收盘价
        慢线EMA = 初始收盘价

        # 计算DIF（差离值）
        DIF = 快线EMA - 慢线EMA  # 首次计算为0

        # 初始化DEA（信号线）
        DEA_EMA = DIF  # 首次计算等于DIF

        # 计算MACD柱
        MACD柱 = 2 * (DIF - DEA_EMA)  # 首次计算为0

        # 首次计算没有趋势和信号
        趋势方向 = MACD趋势方向.震荡
        信号 = MACD信号.无信号

        return cls(
            时间戳=初始时间,
            收盘价=初始收盘价,
            快线周期=快线周期,
            慢线周期=慢线周期,
            信号周期=信号周期,
            DIF=DIF,
            DEA=DEA_EMA,
            MACD柱=MACD柱,
            快线EMA=快线EMA,
            慢线EMA=慢线EMA,
            DEA_EMA=DEA_EMA,
            趋势方向=趋势方向,
            信号=信号,
        )

    @classmethod
    def 增量计算(cls, 前一个MACD: "平滑异同移动平均线", 当前收盘价: float, 当前时间: datetime) -> "平滑异同移动平均线":
        """
        基于前一个MACD指标增量计算当前MACD指标
        适用于实时交易系统或流式数据处理

        :param 前一个MACD: 前一个周期的MACD指标对象
        :param 当前收盘价: 当前K线的收盘价
        :param 当前时间: 当前K线的时间戳
        :return: 当前MACD指标对象
        """

        # 计算EMA的平滑系数
        def 平滑系数(周期):
            return 2 / (周期 + 1)

        # 计算快线EMA
        if 前一个MACD.快线EMA is None:
            快线EMA = 当前收盘价
        else:
            快线EMA = (当前收盘价 - 前一个MACD.快线EMA) * 平滑系数(前一个MACD.快线周期) + 前一个MACD.快线EMA

        # 计算慢线EMA
        if 前一个MACD.慢线EMA is None:
            慢线EMA = 当前收盘价
        else:
            慢线EMA = (当前收盘价 - 前一个MACD.慢线EMA) * 平滑系数(前一个MACD.慢线周期) + 前一个MACD.慢线EMA

        # 计算DIF
        DIF = 快线EMA - 慢线EMA

        # 计算DEA的EMA
        if 前一个MACD.DEA_EMA is None:
            DEA_EMA = DIF
        else:
            DEA_EMA = (DIF - 前一个MACD.DEA_EMA) * 平滑系数(前一个MACD.信号周期) + 前一个MACD.DEA_EMA

        # 计算MACD柱
        MACD柱 = 2 * (DIF - DEA_EMA)

        # 确定趋势方向
        if DIF > 0 and DEA_EMA > 0:
            趋势 = MACD趋势方向.多头
        elif DIF < 0 and DEA_EMA < 0:
            趋势 = MACD趋势方向.空头
        else:
            趋势 = MACD趋势方向.震荡

        # 检测交易信号
        信号 = MACD信号.无信号
        if 前一个MACD.DIF is not None and 前一个MACD.DEA is not None:
            # 金叉/死叉检测
            if DIF > DEA_EMA and 前一个MACD.DIF <= 前一个MACD.DEA:
                信号 = MACD信号.金叉
            elif DIF < DEA_EMA and 前一个MACD.DIF >= 前一个MACD.DEA:
                信号 = MACD信号.死叉

            # 背离检测（简化版）
            if 当前收盘价 > 前一个MACD.收盘价 and DIF < 前一个MACD.DIF and 趋势 == MACD趋势方向.多头:
                信号 = MACD信号.顶背离
            elif 当前收盘价 < 前一个MACD.收盘价 and DIF > 前一个MACD.DIF and 趋势 == MACD趋势方向.空头:
                信号 = MACD信号.底背离

        return cls(
            时间戳=当前时间,
            收盘价=当前收盘价,
            快线周期=前一个MACD.快线周期,
            慢线周期=前一个MACD.慢线周期,
            信号周期=前一个MACD.信号周期,
            DIF=DIF,
            DEA=DEA_EMA,
            MACD柱=MACD柱,
            快线EMA=快线EMA,
            慢线EMA=慢线EMA,
            DEA_EMA=DEA_EMA,
            趋势方向=趋势,
            信号=信号,
        )


class 背驰分析:
    @staticmethod
    def MACD背驰(进入段: Union["笔", "线段"], 离开段: Union["笔", "线段"]) -> bool:
        """MACD柱状线面积背驰"""
        进入MACD = 进入段.计算MACD()
        离开MACD = 离开段.计算MACD()

        # 计算面积（绝对值求和）
        进入面积 = abs(进入MACD["sum"])
        离开面积 = abs(离开MACD["sum"])

        # 价格创新高/新低，但MACD面积减小
        if 进入段.方向 == 相对方向.向上:
            if 离开段.高 > 进入段.高 and 离开面积 < 进入面积:
                return True
        else:
            if 离开段.低 < 进入段.低 and 离开面积 < 进入面积:
                return True
        return False

    @staticmethod
    def 斜率背驰(进入段: Union["笔", "线段"], 离开段: Union["笔", "线段"]) -> bool:
        """价格斜率背驰"""
        进入斜率 = 进入段.计算速率()
        离开斜率 = 离开段.计算速率()

        if 进入段.方向 == 相对方向.向上:
            if 离开段.高 > 进入段.高 and abs(离开斜率) < abs(进入斜率):
                return True
        else:
            if 离开段.低 < 进入段.低 and abs(离开斜率) < abs(进入斜率):
                return True
        return False


class K线:
    def __init__(
        self,
        序号: int,
        标识: str,
        时间戳: datetime,
        开盘价: float,
        最高价: float,
        最低价: float,
        收盘价: float,
        成交量: float,
        最终方向: 相对方向,
        周期: int,
        macd: 平滑异同移动平均线,
        分型: Optional[分型结构] = None,
        原始起始序号: int = -1,
        原始结束序号: int = -1,
        完成标记: bool = False,
        # 买卖类型: Optional[Dict[str, str]] = None,  # 标记是否成为过买卖点 {从属标识: 买卖点类型}
        线段终点值: float = None,
    ):
        self.序号: int = 序号
        self.标识: str = 标识
        self.时间戳: datetime = 时间戳
        self.开盘价: float = 开盘价
        self.最高价: float = 最高价
        self.最低价: float = 最低价
        self.收盘价: float = 收盘价
        self.成交量: float = 成交量
        self.最终方向: 相对方向 = 最终方向
        self.周期: int = 周期
        self.macd: 平滑异同移动平均线 = macd
        self.分型: Optional[分型结构] = 分型
        self.原始起始序号: int = 原始起始序号
        self.原始结束序号: int = 原始结束序号
        self.完成标记: bool = 完成标记
        # self.买卖类型: Optional[Dict[str, str]] = 买卖类型  # 标记是否成为过买卖点 {从属标识: 买卖点类型}
        self.线段终点值: float = 线段终点值
        self.线段_以我为起点_计数 = 0
        self.笔_以我为起点_计数 = 0

    def __str__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.最终方向}, {self.时间戳}, {self.开盘价}, {self.最高价}, {self.最低价}, {self.收盘价}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.最终方向}, {self.时间戳}, {self.开盘价}, {self.最高价}, {self.最低价}, {self.收盘价}>"

    @property
    def 镜像(self):
        return K线(
            序号=self.序号,
            时间戳=self.时间戳,
            开盘价=self.开盘价,
            最高价=self.高,
            最低价=self.低,
            收盘价=self.收盘价,
            成交量=self.成交量,
            最终方向=self.方向,
            标识=self.标识,
            周期=self.周期,
            分型=self.分型,
            原始起始序号=self.原始起始序号,
            原始结束序号=self.原始结束序号,
            macd=self.macd,
        )

    @property
    def 高(self) -> float:
        return self.最高价

    @高.setter
    def 高(self, 高: float) -> None:
        self.最高价 = 高

    @property
    def 低(self) -> float:
        return self.最低价

    @低.setter
    def 低(self, 低: float) -> None:
        self.最低价 = 低

    @property
    def 方向(self) -> 相对方向:
        return self.最终方向

    @property
    def 分型特征值(self) -> float:
        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.高
        elif self.分型 in (分型结构.底, 分型结构.下):
            return self.低
        else:
            print("NewBar.分型特征值: 结构 is None")
            return self.高

    def __bytes__(self):
        return struct.pack(
            ">6d",
            int(self.时间戳.timestamp()),
            round(self.开盘价, 8),
            round(self.最高价, 8),
            round(self.最低价, 8),
            round(self.收盘价, 8),
            round(self.成交量, 8),
        )

    @classmethod
    def 创建缠K(
        cls,
        时间戳: datetime,
        高: float,
        低: float,
        方向: 相对方向,
        量: float,
        原始序号: int,
        周期: int,
        之前: Optional["K线"] = None,
    ) -> "K线":
        assert 高 >= 低
        if 方向 == 相对方向.向下:
            收 = 低
            开 = 高
        else:
            收 = 高
            开 = 低

        if 方向 is 相对方向.向上:
            结构 = 分型结构.上
        else:
            结构 = 分型结构.下

        序号 = 0
        macd = 平滑异同移动平均线.首次计算(收, 时间戳)
        当前 = K线(
            序号=序号,
            时间戳=时间戳,
            开盘价=开,
            最高价=高,
            最低价=低,
            收盘价=收,
            成交量=量,
            最终方向=方向,
            标识="NewBar",
            周期=周期,
            分型=结构,
            原始起始序号=原始序号,
            原始结束序号=原始序号,
            macd=macd,
        )

        if 之前 is not None:
            当前.序号 = 之前.序号 + 1

            if 相对方向.识别(之前, 当前).是否包含():
                raise ValueError(f"\n    {相对方向.识别(之前, 当前)}\n    {之前},\n    {当前}")
        return 当前

    @classmethod
    def 创建普K(cls, 时间戳: datetime, 开盘价: float, 最高价: float, 最低价: float, 收盘价: float, 成交量: float, 序号: int, 周期: int) -> "K线":
        macd = 平滑异同移动平均线.首次计算(收盘价, 时间戳)
        return K线(
            序号=序号,
            时间戳=时间戳,
            开盘价=开盘价,
            最高价=最高价,
            最低价=最低价,
            收盘价=收盘价,
            成交量=成交量,
            最终方向=相对方向.向上 if 收盘价 > 开盘价 else 相对方向.向下,
            标识="RawBar",
            周期=周期,
            分型=None,
            原始起始序号=-1,
            原始结束序号=-1,
            macd=macd,
        )

    @classmethod
    def 创建单K(cls, 时间戳: datetime, 开盘价: float, 最高价: float, 最低价: float, 收盘价: float, 成交量: float, 序号: int) -> "K线":
        return cls.创建普K(时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量, 序号, -1)

    @classmethod
    def 保存到DAT文件(cls, 路径: str, K线序列: List):
        with open(路径, "wb") as f:
            for K in K线序列:
                f.write(bytes(K))
        print(f"保存到DAT文件: {路径}")

    @classmethod
    def 读取大端字节数组(cls, 字节组: bytes, 标识: str = "RawBar") -> "K线":
        时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量 = struct.unpack(">6d", 字节组[: struct.calcsize(">6d")])
        macd = 平滑异同移动平均线.首次计算(收盘价, 时间戳)
        return cls(
            序号=0,
            时间戳=datetime.fromtimestamp(时间戳),
            开盘价=开盘价,
            最高价=最高价,
            最低价=最低价,
            收盘价=收盘价,
            成交量=成交量,
            最终方向=相对方向.向上 if 开盘价 <= 收盘价 else 相对方向.向下,
            标识=标识,
            周期=0,
            分型=None,
            原始起始序号=-1,
            原始结束序号=-1,
            macd=macd,
        )

    @classmethod
    def 根据当前缠K生成之后缠K(cls, 当前缠K: "K线", 方向: 相对方向, 周期: int, 居中: bool = False) -> "K线":
        时间偏移 = timedelta(seconds=周期)
        时间戳: datetime = 当前缠K.时间戳 + 时间偏移
        成交量: float = 998
        原始序号: int = 当前缠K.原始起始序号 + 1
        高: float = 0
        低: float = 0
        高低差 = 当前缠K.高 - 当前缠K.低
        match 方向:
            case 相对方向.向上:
                偏移 = 高低差 * 0.5 if 居中 else randint(int(高低差 * 0.1279), int(高低差 * 0.883))
                低 = 当前缠K.低 + 偏移
                高 = 当前缠K.高 + 偏移
            case 相对方向.向下:
                偏移 = 高低差 * 0.5 if 居中 else randint(int(高低差 * 0.1279), int(高低差 * 0.883))
                低 = 当前缠K.低 - 偏移
                高 = 当前缠K.高 - 偏移
            case 相对方向.向上缺口:
                偏移 = 高低差 * 1.5 if 居中 else randint(int(高低差 * 1.1279), int(高低差 * 1.883))
                低 = 当前缠K.低 + 偏移
                高 = 当前缠K.高 + 偏移
            case 相对方向.向下缺口:
                偏移 = 高低差 * 1.5 if 居中 else randint(int(高低差 * 1.1279), int(高低差 * 1.883))
                低 = 当前缠K.低 - 偏移
                高 = 当前缠K.高 - 偏移
            case 相对方向.衔接向上:
                偏移 = 当前缠K.高 - 当前缠K.低
                高 = 当前缠K.高 + 偏移
                低 = 当前缠K.高
            case 相对方向.衔接向下:
                偏移 = 当前缠K.高 - 当前缠K.低
                高 = 当前缠K.低
                低 = 当前缠K.低 - 偏移

        # 新缠K = K线.创建缠K(时间戳, 高, 低, 相对方向.向上 if 方向.是否向上() else 相对方向.向下, 成交量, 原始序号, 周期, 当前缠K)
        新缠K = K线.创建缠K(
            时间戳=时间戳,
            高=高,
            低=低,
            方向=相对方向.向上 if 方向.是否向上() else 相对方向.向下,
            量=成交量,
            原始序号=原始序号,
            周期=周期,
            之前=当前缠K,
        )

        新缠K.序号 = 当前缠K.序号 + 1
        assert 相对方向.识别(当前缠K, 新缠K) is 方向, (方向, 相对方向.识别(当前缠K, 新缠K))
        return 新缠K

    @classmethod
    def 兼并(cls, 之前缠K: Optional["K线"], 当前缠K: "K线", 当前普K: "K线") -> Optional["K线"]:
        关系 = 相对方向.识别(当前缠K, 当前普K)
        if not 关系.是否包含():
            新缠K = K线.创建缠K(
                时间戳=当前普K.时间戳,
                高=当前普K.高,
                低=当前普K.低,
                方向=当前普K.方向,
                量=当前普K.成交量,
                原始序号=当前普K.序号,
                周期=当前缠K.周期,
                之前=当前缠K,
            )
            新缠K.序号 = 当前缠K.序号 + 1
            return 新缠K

        if 当前普K.序号 == 当前缠K.原始结束序号:
            # 当序号相同时认为是重复提交K线
            ...

        if 当前普K.序号 - 1 != 当前缠K.原始结束序号 and 当前普K.序号 != 当前缠K.原始结束序号:
            raise ValueError(f"NewBar.merger: 不可追加不连续元素 缠K.原始结束序号: {当前缠K.原始结束序号}, 当前普K.序号: {当前普K.序号}.")

        # 方向 = 相对方向.向上
        取值函数 = max
        if 之前缠K is not None:
            if 相对方向.识别(之前缠K, 当前缠K).是否向下():
                # 方向 = 相对方向.向下
                取值函数 = min
        if 关系 is not 相对方向.顺:
            当前缠K.时间戳 = 当前普K.时间戳
        当前缠K.高 = 取值函数(当前缠K.高, 当前普K.高)
        当前缠K.低 = 取值函数(当前缠K.低, 当前普K.低)
        当前缠K.开盘价 = 当前缠K.高 if 当前缠K.方向 is 相对方向.向下 else 当前缠K.低
        当前缠K.收盘价 = 当前缠K.低 if 当前缠K.方向 is 相对方向.向下 else 当前缠K.高
        当前缠K.原始结束序号 = 当前普K.序号

        if 之前缠K is not None:
            当前缠K.序号 = 之前缠K.序号 + 1
        return None

    @classmethod
    def 处理原始K线(cls, K线列表: List["K线"]) -> List["K线"]:
        之前缠K = None
        当前缠K = None
        缠K列表 = []
        序号 = 0
        for k线 in K线列表:
            if 当前缠K is None:
                当前缠K = K线.创建缠K(k线.时间戳, k线.高, k线.低, k线.方向, k线.成交量, k线.周期, 序号)
                序号 += 1
                缠K列表.append(当前缠K)
                continue
            try:
                之前缠K = 缠K列表[-2]
            except IndexError:
                pass
            if nb := K线.兼并(之前缠K, 当前缠K, k线):
                之前缠K = 当前缠K
                当前缠K = nb
                缠K列表.append(nb)

        return 缠K列表

    @classmethod
    def 分析(cls, 当前K线: "K线", 缠K序列: List["K线"], 配置: "缠论配置") -> tuple[str, Optional["分型"]]:
        是否计算MACD = 配置.基础分析计算MACD if 配置 else False
        之前缠K: Optional[K线] = None
        状态, 形态 = None, None
        if 缠K序列:
            try:
                之前缠K = 缠K序列[-2]
            except IndexError:
                pass
            nb = K线.兼并(之前缠K, 缠K序列[-1], 当前K线)
            if nb is not None:
                if 是否计算MACD:
                    macd = 平滑异同移动平均线.增量计算(缠K序列[-1].macd, nb.收盘价, nb.时间戳)
                    nb.macd = macd
                缠K序列.append(nb)
                状态 = "创建"
            else:
                if 是否计算MACD and 之前缠K:
                    缠K序列[-1].macd = 平滑异同移动平均线.增量计算(之前缠K.macd, 缠K序列[-1].收盘价, 缠K序列[-1].时间戳)
                状态 = "兼并"
        else:
            nb = K线.创建缠K(
                时间戳=当前K线.时间戳,
                高=当前K线.高,
                低=当前K线.低,
                方向=当前K线.方向,
                量=当前K线.成交量,
                原始序号=当前K线.序号,
                周期=当前K线.周期,
                之前=None,
            )
            nb.macd = 平滑异同移动平均线.首次计算(
                nb.收盘价,
                nb.时间戳,
                快线周期=配置.MACD_FAST_PERIOD,
                慢线周期=配置.MACD_SLOW_PERIOD,
                信号周期=配置.MACD_SIGNAL_PERIOD,
            )
            缠K序列.append(nb)
            状态 = "新建"
        try:
            左, 中, 右 = 缠K序列[-3:]
        except ValueError:
            return 状态, 形态

        结构 = 分型结构.识别(左, 中, 右)
        中.分型 = 结构

        if 中.分型 is (分型结构.下, 分型结构.顶):
            右.分型 = 分型结构.下

        if 中.分型 in (分型结构.上, 分型结构.底):
            右.分型 = 分型结构.上

        形态 = 分型(左=左, 中=中, 右=右)
        return 状态, 形态

    @staticmethod
    def 截取(序列: List["K线"], 始: "K线", 终: "K线") -> List["K线"]:
        return 序列[序列.index(始) : 序列.index(终) + 1]

    @staticmethod
    def 统计MACD(对象: Union["笔", "线段", "虚线", "走势"], 序列: List["K线"]) -> float:
        正值 = 0.0
        负值 = 0.0
        for K in K线.截取(序列, 对象.文.中, 对象.武.中):
            if K.macd.MACD柱 > 0:
                正值 += K.macd.MACD柱
            else:
                负值 += K.macd.MACD柱

        return abs(正值 + 负值)


class K线合成器:
    def __init__(self, 标识: str, 周期组: List[int], 事件回调: Optional[Callable] = None):
        self.标识 = 标识
        self.周期组 = sorted(周期组)  # 按周期从小到大排序
        self.当前K线: Dict[int, Optional[K线]] = {周期: None for 周期 in 周期组}
        self.合成K线列表: Dict[int, List[K线]] = {周期: [] for 周期 in 周期组}
        self.事件回调 = 事件回调  # 新增：事件回调函数

    def 设置事件回调(self, 回调函数: Callable):
        """设置事件回调函数"""
        self.事件回调 = 回调函数

    def 搜索(self, 周期: int, k线: K线, 容差: float = 0.0001) -> Optional[Tuple[List[K线], List[K线]]]:
        """
        搜索指定周期中与给定K线高低点对应的K线

        Args:
            周期: 要搜索的周期
            k线: 参考K线（通常是较大周期的K线）
            容差: 价格匹配的容差范围

        Returns:
            Tuple[高点匹配K线列表, 低点匹配K线列表] 或 None
        """
        if 周期 not in self.周期组:
            print(f"错误: 周期 {周期} 不在合成器周期组中")
            return None

        if not self.合成K线列表[周期] and self.当前K线[周期] is None:
            print(f"警告: 周期 {周期} 没有可用的K线数据")
            return None

        # 计算时间范围 - 修正时间戳计算
        开始时间 = k线.时间戳
        结束时间 = 开始时间 + timedelta(seconds=k线.周期)

        print(f"搜索范围: {开始时间} 到 {结束时间}")
        print(f"目标高低点: 高={k线.高}, 低={k线.低}")

        # 收集所有候选K线（包括当前K线和历史K线）
        候选K线 = []

        # 添加当前K线（如果存在且在时间范围内
        当前K线 = self.当前K线[周期]
        if 当前K线 is not None:
            if 开始时间 <= 当前K线.时间戳 < 结束时间:
                候选K线.append(当前K线)

        # 添加历史K线（在时间范围内的）
        for 历史K线 in self.合成K线列表[周期]:
            if 开始时间 <= 历史K线.时间戳 < 结束时间:
                候选K线.append(历史K线)
            elif 历史K线.时间戳 >= 结束时间:
                # 由于K线是按时间顺序存储的，可以提前结束
                break

        if not 候选K线:
            print(f"在时间范围内没有找到周期 {周期} 的K线")
            return None

        print(f"找到 {len(候选K线)} 根候选K线")

        # 搜索高低点匹配的K线
        高点匹配K线 = []
        低点匹配K线 = []

        for 候选 in 候选K线:
            # 检查高点匹配（使用容差）
            if 候选 is None:
                continue
            if abs(候选.高 - k线.高) <= 容差:
                高点匹配K线.append(候选)
                print(f"找到高点匹配: {候选.时间戳}, 高={候选.高}")

            # 检查低点匹配（使用容差）
            if abs(候选.低 - k线.低) <= 容差:
                低点匹配K线.append(候选)
                print(f"找到低点匹配: {候选.时间戳}, 低={候选.低}")

        # 如果没有精确匹配，尝试寻找最接近的
        if not 高点匹配K线 or not 低点匹配K线:
            print("没有找到精确匹配，尝试寻找最接近的K线...")
            高点匹配K线, 低点匹配K线 = self._寻找最接近高低点(候选K线, k线, 容差)

        return 高点匹配K线, 低点匹配K线

    def _寻找最接近高低点(self, 候选K线: List[K线], 参考K线: K线, 容差: float) -> Tuple[List[K线], List[K线]]:
        """寻找最接近参考高低点的K线"""
        高点匹配 = []
        低点匹配 = []

        # 寻找最接近的高点
        最接近高点差异 = float("inf")
        最接近高点K线 = None

        for 候选 in 候选K线:
            高点差异 = abs(候选.高 - 参考K线.高)
            if 高点差异 < 最接近高点差异:
                最接近高点差异 = 高点差异
                最接近高点K线 = 候选

        # 寻找最接近的低点
        最接近低点差异 = float("inf")
        最接近低点K线 = None

        for 候选 in 候选K线:
            低点差异 = abs(候选.低 - 参考K线.低)
            if 低点差异 < 最接近低点差异:
                最接近低点差异 = 低点差异
                最接近低点K线 = 候选

        # 如果差异在容差范围内，则接受
        if 最接近高点差异 <= 容差 and 最接近高点K线:
            高点匹配.append(最接近高点K线)
            print(f"接受接近的高点匹配: {最接近高点K线.时间戳}, 高={最接近高点K线.高}, 差异={最接近高点差异}")

        if 最接近低点差异 <= 容差 and 最接近低点K线:
            低点匹配.append(最接近低点K线)
            print(f"接受接近的低点匹配: {最接近低点K线.时间戳}, 低={最接近低点K线.低}, 差异={最接近低点差异}")

        return 高点匹配, 低点匹配

    def 搜索跨周期高低点(self, 大周期: int, 小周期: int, 大周期K线: K线) -> Dict[str, Any]:
        """
        搜索大周期K线在小周期中的对应高低点

        Args:
            大周期: 参考K线的周期
            小周期: 要搜索的较小周期
            大周期K线: 参考的大周期K线

        Returns:
            包含搜索结果的字典
        """
        if 小周期 >= 大周期:
            return {"错误": "小周期必须小于大周期"}

        结果 = self.搜索(小周期, 大周期K线)

        if 结果 is None:
            return {"错误": "搜索失败"}

        高点K线列表, 低点K线列表 = 结果

        return {
            "大周期": 大周期,
            "小周期": 小周期,
            "大周期K线时间": 大周期K线.时间戳,
            "大周期高低点": {"高": 大周期K线.高, "低": 大周期K线.低},
            "找到的高点数量": len(高点K线列表),
            "找到的低点数量": len(低点K线列表),
            "高点匹配": [{"时间戳": k.时间戳, "高": k.高, "序号": k.序号} for k in 高点K线列表],
            "低点匹配": [{"时间戳": k.时间戳, "低": k.低, "序号": k.序号} for k in 低点K线列表],
            "搜索状态": "成功" if (高点K线列表 or 低点K线列表) else "未找到匹配",
        }

    def 批量搜索跨周期高低点(
        self,
        大周期: int,
        小周期: int,
        开始时间: Optional[datetime] = None,
        结束时间: Optional[datetime] = None,
        K线数量: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        批量搜索多个大周期K线在小周期中的对应高低点

        Args:
            大周期: 参考K线的周期
            小周期: 要搜索的较小周期
            开始时间: 搜索开始时间
            结束时间: 搜索结束时间
            K线数量: 要搜索的K线数量

        Returns:
            搜索结果列表
        """
        if 大周期 not in self.周期组:
            return [{"错误": f"大周期 {大周期} 不在周期组中"}]

        大周期K线列表 = self.获取合成K线(大周期)
        if not 大周期K线列表:
            return [{"错误": f"大周期 {大周期} 没有K线数据"}]

        # 过滤K线
        过滤后K线 = []
        for k线 in 大周期K线列表:
            if 开始时间 and k线.时间戳 < 开始时间:
                continue
            if 结束时间 and k线.时间戳 > 结束时间:
                continue
            过滤后K线.append(k线)

        # 如果指定了数量，取最新的
        if K线数量 and len(过滤后K线) > K线数量:
            过滤后K线 = 过滤后K线[-K线数量:]

        结果列表 = []
        for 大周期K线 in 过滤后K线:
            搜索结果 = self.搜索跨周期高低点(大周期, 小周期, 大周期K线)
            结果列表.append(搜索结果)

        return 结果列表

    def 投喂(self, 时间戳: datetime, 开: float, 高: float, 低: float, 收: float, 量: float):
        """投喂原始tick数据"""
        普K = K线(
            序号=0,  # 原始数据序号不重要
            标识=self.标识,
            时间戳=时间戳,
            开盘价=开,
            最高价=高,
            最低价=低,
            收盘价=收,
            成交量=量,
            最终方向=相对方向.向上 if 开 < 收 else 相对方向.向下,
            周期=0,  # 原始数据是0秒周期
            macd=平滑异同移动平均线.首次计算(收, 时间戳),
        )
        self.投喂K线(普K)

    def 投喂K线(self, 普K: K线):
        """投喂K线对象"""
        for 周期 in self.周期组:
            self._处理单个周期(周期, 普K)

    def _处理单个周期(self, 周期: int, 普K: K线):
        """处理单个周期的K线合成"""
        目标时间戳 = self._对齐时间戳(普K.时间戳, 周期)
        当前K线 = self.当前K线[周期]
        if 当前K线 is None:
            # 创建新的K线
            self.当前K线[周期] = self._创建新K线(周期, 目标时间戳, 普K)
        elif 当前K线.时间戳 == 目标时间戳:
            # 更新当前K线
            self._更新K线(当前K线, 普K)
        else:
            # 完成当前K线，创建新K线
            self._完成K线(周期)
            self.当前K线[周期] = self._创建新K线(周期, 目标时间戳, 普K)

    def _对齐时间戳(self, 时间戳: datetime, 周期: int) -> datetime:
        """将时间戳对齐到周期边界"""
        total_seconds = int(时间戳.timestamp())
        aligned_seconds = (total_seconds // 周期) * 周期
        return datetime.fromtimestamp(aligned_seconds)

    def _创建新K线(self, 周期: int, 时间戳: datetime, 普K: K线) -> K线:
        """创建新的合成K线"""
        return K线(
            序号=0 if not self.合成K线列表[周期] else self.合成K线列表[周期][-1].序号 + 1,
            标识=self.标识,
            时间戳=时间戳,
            开盘价=普K.开盘价,
            最高价=普K.最高价,
            最低价=普K.最低价,
            收盘价=普K.收盘价,
            成交量=普K.成交量,
            最终方向=相对方向.向上 if 普K.开盘价 < 普K.收盘价 else 相对方向.向下,
            周期=周期,
            macd=平滑异同移动平均线.首次计算(普K.收盘价, 时间戳),
            原始起始序号=普K.序号,
            原始结束序号=普K.序号,
        )

    def _更新K线(self, 当前K线: K线, 新数据: K线):
        """更新当前K线数据"""
        当前K线.最高价 = max(当前K线.最高价, 新数据.最高价)
        当前K线.最低价 = min(当前K线.最低价, 新数据.最低价)
        当前K线.收盘价 = 新数据.收盘价
        当前K线.成交量 += 新数据.成交量
        # 当前K线.原始结束序号 = 新数据.序号

        # 计算最终方向
        if 当前K线.收盘价 > 当前K线.开盘价:
            当前K线.最终方向 = 相对方向.向上
        elif 当前K线.收盘价 < 当前K线.开盘价:
            当前K线.最终方向 = 相对方向.向下
        else:
            当前K线.最终方向 = 相对方向.向上

    def _完成K线(self, 周期: int):
        """完成当前K线并添加到列表"""
        当前K线 = self.当前K线[周期]
        if 当前K线 is None:
            return

        # 这里可以添加最终的处理逻辑，比如计算MACD等
        if self.合成K线列表[周期]:
            当前K线.macd = 平滑异同移动平均线.增量计算(self.合成K线列表[周期][-1].macd, 当前K线.收盘价, 当前K线.时间戳)
            当前K线.序号 = self.合成K线列表[周期][-1].序号 + 1
        else:
            当前K线.macd = 平滑异同移动平均线.首次计算(当前K线.收盘价, 当前K线.时间戳)

        当前K线.完成标记 = True
        self.合成K线列表[周期].append(当前K线)

        # 新增：产生完成K线信号
        self._产生完成K线信号(周期, 当前K线)

    def _产生完成K线信号(self, 周期: int, 完成K线: K线):
        """产生K线完成信号"""
        if self.事件回调:
            try:
                信号数据 = {"类型": "K线完成", "合成器标识": self.标识, "周期": 周期, "K线数据": 完成K线}
                self.事件回调(信号数据)
            except Exception as e:
                print(f"K线合成器信号回调错误: {e}")

    def 获取合成K线(self, 周期: int) -> List[K线]:
        """获取指定周期的合成K线列表"""
        return self.合成K线列表[周期].copy()

    def 获取当前K线(self, 周期: int) -> Optional[K线]:
        """获取指定周期当前正在合成的K线"""
        return self.当前K线[周期]

    def 强制完成当前K线(self, 周期: int):
        """强制完成当前周期的K线"""
        self._完成K线(周期)
        self.当前K线[周期] = None


class 特征分型:
    def __init__(self, 左: Optional[K线], 中: K线, 右: Optional[K线], 真实性: bool = True, 结构: 分型结构 = None):
        self.左: Optional[K线] = 左
        self.中: K线 = 中
        self.右: Optional[K线] = 右
        self.真实性: bool = 真实性
        self._结构 = 结构

    def __str__(self):
        return f"特征分型<{self._结构}, {self.中}>"

    def __repr__(self):
        return f"特征分型<{self._结构}, {self.中}>"


class 分型(特征分型):
    def __init__(self, 左: Optional[K线], 中: K线, 右: Optional[K线], 真实性: bool = True):
        super().__init__(左, 中, 右, 真实性)

    def __str__(self):
        return f"{self.中.分型}<{self.时间戳}, {self.分型特征值}, {self.左 is None}, {self.右 is None}>"

    def __repr__(self):
        return f"{self.中.分型}<{self.时间戳}, {self.分型特征值}, {self.左 is None}, {self.右 is None}>"

    @property
    def 时间戳(self) -> datetime:
        if self.结构 in (分型结构.上, 分型结构.下):  # TODO 2025-11-14 16:54 对于 上下 分型的特征值取分型右侧，更加直观
            if self.右 is None:
                return self.中.时间戳
            return self.右.时间戳
        return self.中.时间戳

    @property
    def 结构(self) -> Optional[分型结构]:
        return self.中.分型

    @property
    def 分型特征值(self) -> float:
        if self.结构 in (分型结构.上, 分型结构.下):  # TODO 2025-11-14 16:54 对于 上下 分型的特征值取分型右侧，更加直观
            if self.右 is None:
                return self.中.分型特征值
            return self.右.分型特征值
        return self.中.分型特征值

    @property
    def 高(self) -> float:
        if self.左 is None:
            print("警告: 分型缺少左侧")
            if self.右 is not None:
                return max(self.中.高, self.右.高)
            return self.中.高

        if self.右 is None:
            return self.中.高
        return max(self.左.高, self.中.高, self.右.高)

    @property
    def 低(self) -> float:
        if self.左 is None:
            print("警告: 分型缺少左侧")
            if self.右 is not None:
                return min(self.中.低, self.右.高)
            return self.中.低
        if self.右 is None:
            return self.中.低
        return min(self.左.低, self.中.低, self.右.高)

    @staticmethod
    def 从缠K序列中获取分型(K线序列: Sequence[K线], 中: K线) -> "分型":
        索引 = K线序列.index(中)
        return 分型(左=K线序列[索引 - 1], 中=中, 右=K线序列[索引 + 1])

    @staticmethod
    def 向序列中添加(分型序列: List["分型"], 当前分型: "分型"):
        if not 分型序列 and 当前分型.结构 not in (分型结构.顶, 分型结构.底):
            raise ValueError("首次添加分型不为 顶底", 当前分型)
        if 分型序列:
            if 分型序列[-1].结构 is 当前分型.结构:
                raise ValueError("分型相同无法添加", 分型序列[-1], 当前分型)
            if 分型序列[-1].右 is None:
                print("分型.向序列中添加, 分型异常", 分型序列[-1])

        分型序列.append(当前分型)

    @staticmethod
    def 从序列中删除(分型序列: List["分型"], 当前分型: "分型"):
        if 分型序列 and 分型序列[-1] is not 当前分型:
            raise ValueError("分型相同无法删除", 分型序列[-1], 当前分型)
        return 分型序列.pop()

    @staticmethod
    def 从缠K序列中获取虚假分型(K线序列: Sequence[K线]) -> Optional["分型"]:
        try:
            中 = K线序列[-2]
            if 中.分型 in (分型结构.下, 分型结构.顶):
                K线序列[-1].分型 = 分型结构.底

            elif 中.分型 in (分型结构.上, 分型结构.底):
                K线序列[-1].分型 = 分型结构.顶

            else:
                raise ValueError("虚假分型 中.分型 = ", 中.分型)

            return 分型(左=None, 中=K线序列[-1], 右=None, 真实性=False)
        except IndexError:
            pass
        return None


class 线段特征(list):
    def __init__(self, 标识: str, 基础序列: List["笔"] | List["线段"], 线段方向: 相对方向):
        super().__init__(基础序列)
        self.标识: str = 标识
        self.线段方向: 相对方向 = 线段方向

    def __str__(self):
        if not len(self):
            return colored(f"{self.标识}<{self.线段方向}, 空>", "green")
        return f"{self.标识}<{self.线段方向}, {self.文}, {self.武}, {len(self)}>"

    def __repr__(self):
        if not len(self):
            return colored(f"{self.标识}<{self.线段方向}, 空>", "green")
        return f"{self.标识}<{self.线段方向}, {self.文}, {self.武}, {len(self)}>"

    @property
    def 文(self) -> 分型:
        if self.线段方向 is 相对方向.向上:  # 取高高
            func = max
        else:
            func = min
        return func([线.文 for 线 in self], key=lambda o: o.分型特征值)

    @property
    def 武(self) -> 分型:
        if self.线段方向 is 相对方向.向上:
            func = max
        else:
            func = min
        return func([线.武 for 线 in self], key=lambda o: o.分型特征值)

    @property
    def 高(self) -> float:
        return max([self.文, self.武], key=lambda fx: fx.分型特征值).分型特征值

    @property
    def 低(self) -> float:
        return min([self.文, self.武], key=lambda fx: fx.分型特征值).分型特征值

    @property
    def 方向(self) -> 相对方向:
        return self.线段方向.翻转()

    def 添加(self, 待添加虚线: Union["笔", "线段"]):
        if 待添加虚线.方向 == self.线段方向:
            raise ValueError("方向不匹配", self.线段方向, 待添加虚线, self)
        self.append(待添加虚线)

    def 删除(self, 待删除虚线: Union["笔", "线段"]):
        if 待删除虚线.方向 == self.方向:
            raise ValueError("方向不匹配", self.线段方向, 待删除虚线, self)
        self.remove(待删除虚线)

    @classmethod
    def 新建(cls, 虚线序列: List["笔"] | List["线段"], 线段方向: 相对方向) -> "线段特征":
        return 线段特征(标识=f"特征<{虚线序列[0].__class__.__name__}>", 基础序列=虚线序列, 线段方向=线段方向)

    @classmethod
    def 静态分析(cls, 虚线序列: List["笔"] | List["线段"], 线段方向: 相对方向, 四象: str) -> List["线段特征"]:
        """
        :param 虚线序列:
        :param 线段方向:
        :param 四象: 老阴，老阳，少阴，小阳
            老阴 老阳 分别代表 缺口顶分型后的向下线段 与 缺口底分型后的向上线段
        :return: 特征序列元组
        """

        if 四象 in ("老阳", "老阴"):
            # 特征序列带有缺口时 要严格处理包含关系
            需要被合并方向序列 = (相对方向.顺, 相对方向.逆, 相对方向.同)
        else:
            需要被合并方向序列 = (相对方向.顺, 相对方向.同)

        # print("    线段特征.分析", 四象, 需要被合并方向序列, 虚线序列)
        特征序列: List[线段特征] = []
        for 当前虚线 in 虚线序列:
            if 当前虚线.方向 is 线段方向:
                if len(特征序列) >= 3:
                    左, 中, 右 = 特征序列[-3], 特征序列[-2], 特征序列[-1]
                    关系 = 相对方向.识别(左, 中)
                    结构 = 分型结构.识别(左, 中, 右, 可以逆序包含=True, 忽视顺序包含=True)
                    # print("    线段特征.分析", 四象, 结构, 关系)
                    if (线段方向 is 相对方向.向上 and 结构 is 分型结构.顶 and 当前虚线.高 > 中.高) or (线段方向 is 相对方向.向下 and 结构 is 分型结构.底 and 当前虚线.低 < 中.低):
                        小号虚线 = min(中, key=lambda o: o.序号)
                        大号虚线 = max(右, key=lambda o: o.序号)
                        基础序列 = 虚线序列[虚线序列.index(小号虚线) : 虚线序列.index(大号虚线) + 1]
                        fake = 笔(
                            序号=-1,
                            文=小号虚线.文,
                            武=大号虚线.武,
                            基础序列=基础序列,  # [小号虚线.文.中, 大号虚线.武.中],
                            # 标识=f"组合{小号虚线.标识}",
                        )
                        特征序列.pop()
                        特征序列[-1] = 线段特征.新建([fake], 线段方向)
                        # print("    线段特征.分析 情况一:", 关系, 结构, 四象, 当前虚线)
                continue

            if 特征序列:
                之前线段特征 = 特征序列[-1]
                if 相对方向.识别(之前线段特征, 当前虚线) in 需要被合并方向序列:
                    之前线段特征.添加(当前虚线)
                else:
                    特征序列.append(线段特征.新建([当前虚线], 线段方向))
            else:
                特征序列.append(线段特征.新建([当前虚线], 线段方向))

        return 特征序列

    @classmethod
    def 获取分型序列(cls, 特征序列: List):
        结构序列 = []
        for i in range(1, len(特征序列) - 1):
            结构 = 分型结构.识别(特征序列[i - 1], 特征序列[i], 特征序列[i + 1], True, True)
            结构序列.append(特征分型(特征序列[i - 1], 特征序列[i], 特征序列[i + 1], True, 结构))
        if 结构序列:
            assert 特征序列[-1] is 结构序列[-1].右
        return 结构序列


class 虚线(三折叠):
    __slots__ = ["标识", "序号", "_文", "_武", "之前", "之后", "配置", "观察员", "有效性"]

    def __init__(self, 序号: int, 文: 分型, 武: 分型, 基础序列: List, 之前: Optional[Self] = None, 之后: Optional[Self] = None, 配置: 缠论配置 = 缠论配置(), 观察员: Optional["观察者"] = None, 有效性: bool = True):
        super().__init__(*基础序列[:3])
        self.extend(基础序列[3:])
        self.序号: int = 序号
        self._文: 分型 = 文
        self._武: 分型 = 武
        self.之前: Optional[Self] = 之前
        self.之后: Optional[Self] = 之后

        self.配置: 缠论配置 = 配置

        self.观察员: Optional["观察者"] = 观察员
        self.有效性: bool = 有效性

    @property
    def 文(self) -> 分型:
        return self._文

    @property
    def 武(self) -> 分型:
        return self._武

    def 武斗(self, 武: 分型, 行号):
        # print(f"{self.__class__.__name__}.武斗[{行号}], ", 武)
        if self._武.分型特征值 == 武.分型特征值:
            self._武 = 武
            return
        assert self._文.结构 is not 武.结构, ("文武结构相同", 武)
        if 武.右 is not None and 分型结构.识别(武.左, 武.中, 武.右) is not 武.结构:
            raise RuntimeError
        if self.方向 is 相对方向.向上:
            if 武.分型特征值 < self.文.分型特征值:
                raise RuntimeError("向上虚线, 结束点 小于 起点", 武)
            if max([self._武, 武], key=lambda k: k.分型特征值) is not 武:
                print(colored(f"{self.__class__.__name__}.武斗[{行号}] 出现回退 从 {self._武} ==>>> {武}", "red", "on_yellow"))  # raise RuntimeError(self._武, 武)
        else:
            if 武.分型特征值 > self.文.分型特征值:
                raise RuntimeError("向下虚线, 结束点 大于 起点", 武)
            if min([self._武, 武], key=lambda k: k.分型特征值) is not 武:
                print(colored(f"{self.__class__.__name__}.武斗[{行号}] 出现回退 从 {self._武} ==>>> {武}", "red", "on_yellow"))  # raise RuntimeError(self._武, 武)
        self._武 = 武
        self.观察员 and self.观察员.报信(self, 指令.修改(self.__class__.__name__))

    def 计算角度(self) -> float:
        # 计算线段的角度
        dx = self.武.中.序号 - self.文.中.序号  # self.武.时间戳.timestamp() - self.文.时间戳.timestamp()  # self.武.时间戳 - self.文.时间戳  # 时间差
        dy = self.武.分型特征值 - self.文.分型特征值  # 价格差

        if dx == 0:
            return 90.0 if dy > 0 else -90.0

        angle = math.degrees(math.atan2(dy, dx))
        return angle

    def 计算速率(self) -> float:
        # 计算线段的速度
        dx = self.武.中.序号 - self.文.中.序号  # self.武.时间戳 - self.文.时间戳  # 时间差
        dy = self.武.分型特征值 - self.文.分型特征值  # 价格差
        return dy / dx

    def 计算测度(self) -> float:
        # 计算线段测度
        dx = self.武.中.序号 - self.文.中.序号  # self.武.时间戳.timestamp() - self.文.时间戳.timestamp()  # 时间差
        dy = abs(self.武.分型特征值 - self.文.分型特征值)  # 价格差的绝对值
        return math.sqrt(dx * dx + dy * dy)  # 返回线段的欧几里得长度作为测度

    def 计算振幅(self) -> float:
        # 计算线段振幅比例
        amplitude = self.武.分型特征值 - self.文.分型特征值
        return amplitude / self.文.分型特征值 if self.文.分型特征值 != 0 else 0

    def 计算MACD(self) -> Dict[str, float]:
        result = {"up": 0.0, "down": 0.0, "sum": 0.0}
        for 元素 in self:
            if hasattr(元素, "macd"):
                macd = 元素.macd
                key = "up" if macd.MACD柱 > 0 else "down"
                result[key] = result[key] + macd.MACD柱

            else:
                macd = 元素.计算MACD()
                result["up"] = result["up"] + macd["up"]
                result["down"] = result["down"] + macd["down"]

        result["sum"] = abs(result["up"]) + abs(result["down"])
        return result

    def 之前是(self, 之前: "虚线") -> bool:
        return hasattr(之前, "武") and 之前.武.中 == self.文.中

    def 之后是(self, 之后: "虚线") -> bool:
        结果 = hasattr(之后, "文") and self.武.中 == 之后.文.中
        if hasattr(之后, "文") and not 结果:
            if self.武.中 is 之后.文.中:
                print(f"虚线.之后是: {self.武 == 之后.文}, {self.武 is 之后.文}, 之后是: 相同对象({self.武}), 不同对象({self.武.右} != {之后.文.右})")
        return 结果

    def 枚举下一位置(self, 区间序列: List) -> set:
        def 区间随机数(x, n):
            if x > n:
                # 向上
                a = uniform(n * 1.00001, x * 0.9999)
                b = uniform(x * 1.00001, x * 1.3999)
                return a, b
            else:
                # 向下
                a = uniform(x * 1.00001, n * 0.99999)
                b = uniform(x * 0.99999, x * 0.79999)
                return a, b

        可能位置 = []
        符合位置 = set(区间序列)
        符合位置.add(self.高)
        符合位置.add(self.低)
        if self.方向 is 相对方向.向上:
            符合位置 = [n for n in 符合位置 if n < self.高]
            符合位置.sort()
            可能位置.extend(符合位置)
            if len(符合位置) == 1:
                可能位置.extend(区间随机数(符合位置[0], self.高))
            else:
                for i in range(1, len(符合位置)):
                    s, e = 符合位置[i - 1], 符合位置[i]
                    while 1:
                        m = uniform(s, e)
                        if m != s and m != e and m not in 可能位置:
                            可能位置.append(m)
                            break

        else:
            符合位置 = [n for n in 符合位置 if n > self.低]
            符合位置.sort()
            可能位置.extend(符合位置)
            if len(符合位置) == 1:
                可能位置.extend(区间随机数(符合位置[0], self.低))
            else:
                for i in range(1, len(符合位置)):
                    s, e = 符合位置[i - 1], 符合位置[i]
                    while 1:
                        m = random.uniform(s, e)
                        if m != s and m != e and m not in 可能位置:
                            可能位置.append(m)
                            break
        可能位置.sort()
        return 可能位置

    @property
    def 方向(self) -> "相对方向":
        match (self.文.结构, self.武.结构):
            case (分型结构.顶, 分型结构.底):
                return 相对方向.向下
            case (分型结构.顶, 分型结构.下):
                return 相对方向.向下

            case (分型结构.底, 分型结构.顶):
                return 相对方向.向上
            case (分型结构.底, 分型结构.上):
                return 相对方向.向上

            case _:
                raise RuntimeError("无法识别的方向", self.文.结构, self.武.结构)

    @property
    def 高(self) -> float:
        if self.方向 is 相对方向.向上:
            return self.武.分型特征值
        return self.文.分型特征值

    @property
    def 低(self) -> float:
        if self.方向 is 相对方向.向下:
            return self.武.分型特征值
        return self.文.分型特征值

    @property
    def 同向不存在关系(self) -> tuple:
        """
        下一同向虚线与我不可能存在的关系
        上下上, 两个向上虚线 不会出现[相对方向.向上缺口, 相对方向.衔接向上]的关系
        """
        if self.方向 is 相对方向.向上:
            return 相对方向.向上缺口, 相对方向.衔接向上
        return 相对方向.向下缺口, 相对方向.衔接向下

    @property
    def 异向存在关系(self) -> tuple:
        return 相对方向.顺, 相对方向.逆, 相对方向.同


class 笔(虚线):
    def __str__(self):
        return f"笔({self.序号}, {self.方向}, {self.文}, {self.武}, 周期: {self.周期}, {self.缠K数量})"

    def __repr__(self):
        return f"笔({self.序号}, {self.方向}, {self.文}, {self.武}, 周期: {self.周期}, {self.缠K数量})"

    @classmethod
    def 新建(cls, 文: 分型, 武: 分型, 缠K序列: List["K线"], 配置: 缠论配置, **一带一路) -> "笔":
        if 缠K序列[0] is not 文.中:
            raise ValueError("笔.新建，文不在序列首位！")
        之前: Optional["笔"] = 一带一路.get("之前", None)
        if 之前 and 之前.武.中 is not 缠K序列[0]:
            raise ValueError("笔.新建，之前笔与当前新建不连续！")
        return cls(
            序号=一带一路.get("序号", 0),
            文=文,
            武=武,
            基础序列=缠K序列[:],
            之前=之前,
            配置=配置,
        )

    @property
    def 周期(self) -> int:
        assert self[0].周期 == self[-1].周期
        return self[0].周期

    @property
    def 元素缺口序列(self):
        缺口序列 = []
        基础序列 = self
        for i in range(1, len(基础序列)):
            左 = 基础序列[i - 1]
            右 = 基础序列[i]
            assert 左.序号 + 1 == 右.序号, (
                左.序号,
                右.序号,
            )
            相对关系 = 相对方向.识别(左, 右)
            if 相对关系.是否缺口():
                if 相对关系.是否向上():
                    high = 右.低
                    low = 左.高
                else:
                    high = 左.低
                    low = 右.高
                缺口序列.append(缺口(high, low))
        return 缺口序列

    @property
    def 缠K数量(self) -> int:
        缺口序列 = self.元素缺口序列
        实际高点 = self.实际高点
        实际低点 = self.实际低点

        实际数量 = len(self)
        if 实际数量 >= self.配置.笔内元素数量:
            return 实际数量

        符合缺口数量 = 0
        if self.配置.笔内缺口判定为元素:  # FIXME 缺口是否看成一个单独k线
            for _缺口 in 缺口序列:
                if (_缺口.高 - _缺口.低) / (实际高点.高 - 实际低点.低) >= self.配置.笔内缺口判定为元素比例:
                    符合缺口数量 += 1
            return 符合缺口数量 + 实际数量

        if self.配置.笔内缺口占比强制成笔 and 实际数量 >= 3:
            缺口差值序列 = [o.高 - o.低 for o in 缺口序列]
            总缺口 = sum(缺口差值序列)
            if (总缺口 / (实际高点.高 - 实际低点.低)) >= self.配置.笔内缺口占比:
                return self.配置.笔内元素数量
        return 实际数量

    @property
    def 次高(self) -> K线:
        序列 = sorted(self, key=lambda k: k.高)
        highs: List[K线] = [k for k in 序列 if k.高 != 序列[-1].高]  # 排除
        highs: List[K线] = [k for k in highs if k.高 == highs[-1].高]  # 筛选
        highs.sort(key=lambda k: k.时间戳)  # 排序
        return highs[-1] if self.配置.笔内相同终点取舍 else highs[0]

    @property
    def 次低(self) -> K线:
        序列 = sorted(self, key=lambda k: k.低)
        lows: List[K线] = [k for k in 序列 if k.低 != 序列[0].低]
        lows: List[K线] = [k for k in lows if k.低 == lows[0].低]
        lows.sort(key=lambda k: k.时间戳)
        return lows[-1] if self.配置.笔内相同终点取舍 else lows[0]

    @property
    def 实际高点(self) -> K线:
        序列 = sorted(self, key=lambda k: k.高)
        highs: List[K线] = [k for k in 序列 if k.高 == 序列[-1].高]
        highs.sort(key=lambda k: k.时间戳)
        return highs[-1] if self.配置.笔内相同终点取舍 else highs[0]

    @property
    def 实际低点(self) -> K线:
        序列 = sorted(self, key=lambda k: k.低)
        lows: List[K线] = [k for k in 序列 if k.低 == 序列[0].低]
        lows.sort(key=lambda k: k.时间戳)
        return lows[-1] if self.配置.笔内相同终点取舍 else lows[0]

    @property
    def 相对关系(self) -> bool:
        if self.配置.笔内起始分型包含整笔:
            相对关系 = 相对方向.识别(self.文, self.武)
        else:
            相对关系 = 相对方向.识别(self.文.中, self.武.中)

        if self.方向 is 相对方向.向下:
            return 相对关系.是否向下()
        return 相对关系.是否向上()

    def 自检(self) -> bool:
        if self.缠K数量 >= self.配置.笔内元素数量:
            # assert self.文.中 is self[0]
            # assert self.武.中 is self[-1]
            if self.方向 is 相对方向.向下 and self.文.中 is self.实际高点 and self.武.中 is self.实际低点:
                return True
            if self.方向 is 相对方向.向上 and self.文.中 is self.实际低点 and self.武.中 is self.实际高点:
                return True
        return False

    @classmethod
    def 搜索(cls, 序列: List["笔"], 待搜索: K线) -> Optional["笔"]:
        for _笔 in 序列:
            if _笔.文.中 is 待搜索:
                return _笔
        return None

    @classmethod
    def 端点验证(cls, 左: "笔", 右: "笔"):
        if 左.文.中 is 右.文.中 and 左.武.中 is 右.武.中:
            return True
        return False

    @classmethod
    def 分析(
        cls,
        当前分型: Optional[分型],
        分型序列: List[分型],
        笔序列: List["笔"],
        缠K序列: List[K线],
        来源渠道: str,
        递归层次: int,
        全局配置: 缠论配置,
        观察员: "观察者",
    ):
        if 当前分型 is None:
            return

        if not 分型序列:
            if 当前分型.结构 in (分型结构.顶, 分型结构.底):
                分型序列.append(当前分型)
            return

        def _弹出旧笔(行号):
            旧分型 = 分型序列.pop()
            if 笔序列:
                旧笔 = 笔序列.pop()
                assert 旧笔.武 is 旧分型, "最后一笔终点错误"
                旧笔.有效性 = False
                旧笔.之前 = None
                旧笔.之后 = None

                if 来源渠道 == "分析":
                    观察员 and 观察员.报信(旧笔, 指令.删除(f"笔{行号}"))
                    观察员 and 线段.分析(观察员.缠论K线序列[-1], 观察员.笔序列, 观察员.线段序列, 观察员.中枢序列, 观察员, 观察员.配置)
                    # 观察员 and 中枢.分析(观察员.缠论K线序列[-1], 观察员.笔序列, 观察员.笔_中枢序列, 观察员)

        def _添加新笔(待添加分型: "分型", 待添加新笔: "笔", 行号):
            分型.向序列中添加(分型序列, 待添加分型)
            if 笔序列 and not 笔序列[-1].之后是(待添加新笔):
                raise ValueError("笔.向序列中添加 不连续", 笔序列[-1], 待添加新笔)

            if 笔序列:
                待添加新笔.序号 = 笔序列[-1].序号 + 1
                待添加新笔.之前 = 笔序列[-1]
                笔序列[-1].之后 = 待添加新笔
                if 待添加新笔.武.左 is None and 待添加新笔.武.右 is None:
                    待添加新笔.有效性 = False
                if 笔序列[-1].武.结构 in (分型结构.上, 分型结构.下):
                    print(f"_添加新笔[{行号}] 出现无效分型", 笔序列[-1])

            笔序列.append(待添加新笔)
            待添加新笔.文.中.笔_以我为起点_计数 += 1
            if 来源渠道 == "分析":
                观察员 and 观察员.报信(待添加新笔, 指令.添加(f"笔{行号}"))
                观察员 and 线段.分析(观察员.缠论K线序列[-1], 观察员.笔序列, 观察员.线段序列, 观察员.中枢序列, 观察员, 观察员.配置)
                # 观察员 and 中枢.分析(观察员.缠论K线序列[-1], 观察员.笔序列, 观察员.笔_中枢序列, 观察员)

        之前分型 = 分型序列[-1]

        if 之前分型.中.时间戳 > 当前分型.中.时间戳:
            raise TimeoutError(f"时序错误, {之前分型.中.时间戳}, {当前分型.中.时间戳}, {当前分型}")

        if 之前分型.中.时间戳 == 当前分型.中.时间戳 and 之前分型.中.分型特征值 == 当前分型.中.分型特征值:
            # print("特殊处理，处理图表显示问题", 之前分型, 当前分型)

            if 当前分型.结构 in (分型结构.顶, 分型结构.底):
                笔序列 and 观察员 and 观察员.报信(笔序列[-1], 指令.删除(f"笔{sys._getframe().f_lineno}"))
                之前分型.左, 之前分型.中, 之前分型.右, 之前分型.真实性, 之前分型._结构 = 当前分型.左, 当前分型.中, 当前分型.右, 当前分型.真实性, 当前分型._结构
                笔序列 and 观察员 and 观察员.报信(笔序列[-1], 指令.添加(f"笔{sys._getframe().f_lineno}"))
            else:
                _弹出旧笔(sys._getframe().f_lineno)
                笔.分析(当前分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)

            # _弹出旧笔(sys._getframe().f_lineno)
            # 笔.分析(当前分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)
            return

        if (之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底) or (之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.顶):
            基础序列 = K线.截取(缠K序列, 之前分型.中, 当前分型.中)
            if len(基础序列) < 3:
                # GD or DG
                if (当前分型.右 and 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底 and 当前分型.右.高 > 之前分型.分型特征值) or (当前分型.右 and 之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.顶 and 当前分型.右.低 < 之前分型.分型特征值):
                    _弹出旧笔(sys._getframe().f_lineno)
                    临时分型 = None
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        临时分型 = 分型(None, 当前分型.右, None, False)
                        临时分型.中.分型 = 分型结构.顶

                    elif 之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.顶:
                        临时分型 = 分型(None, 当前分型.右, None, False)
                        临时分型.中.分型 = 分型结构.底

                    笔.分析(临时分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)
                return

            当前笔 = 笔(序号=0, 文=之前分型, 武=当前分型, 基础序列=基础序列, 配置=全局配置)
            if 当前笔.缠K数量 >= 全局配置.笔内元素数量:
                eq = 全局配置.笔内相同终点取舍
                全局配置.笔内相同终点取舍 = False  # 起始点检测时不考虑相同起始点情况，避免递归

                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    文点 = 当前笔.实际高点
                else:
                    文点 = 当前笔.实际低点

                if 文点 is not 之前分型.中:
                    # print("    文: 不是真", 之前分型.结构)
                    临时分型 = 分型.从缠K序列中获取分型(缠K序列, 文点)
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        assert 临时分型.结构 is 分型结构.顶, 临时分型
                    else:
                        assert 临时分型.结构 is 分型结构.底, 临时分型
                    笔.分析(临时分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)  # 处理新顶
                    笔.分析(当前分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)  # 再处理当前底
                    全局配置.笔内相同终点取舍 = eq
                    return
                全局配置.笔内相同终点取舍 = eq

                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    武点 = 当前笔.实际低点
                else:
                    武点 = 当前笔.实际高点

                if 当前笔.相对关系 and 当前分型.中 is 武点:
                    _添加新笔(当前分型, 当前笔, sys._getframe().f_lineno)
                else:
                    pass
                    if 全局配置.笔次级成笔:
                        if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                            武点 = 当前笔.次低
                        else:
                            武点 = 当前笔.次高
                        if 当前笔.相对关系 and 当前分型.中 is 武点:
                            _添加新笔(当前分型, 当前笔, sys._getframe().f_lineno)
            else:
                # GD or DG
                振幅 = 当前笔.计算振幅()
                if abs(振幅) > 0.033:
                    # print("笔振幅：", 当前笔)
                    pass  # TODO 待定得到特殊识别
                if (当前分型.右 and 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底 and 当前分型.右.高 > 之前分型.分型特征值) or (当前分型.右 and 之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.顶 and 当前分型.右.低 < 之前分型.分型特征值):
                    _弹出旧笔(sys._getframe().f_lineno)
                    临时分型 = None
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        临时分型 = 分型(None, 当前分型.右, None, False)
                        临时分型.中.分型 = 分型结构.顶

                    elif 之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.顶:
                        临时分型 = 分型(None, 当前分型.右, None, False)
                        临时分型.中.分型 = 分型结构.底

                    笔.分析(临时分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)
                return

        elif (之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.顶) or (之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.底):
            分型特征值 = 当前分型.分型特征值
            # 关系 = 相对方向.识别(之前分型.中, 当前分型.中)

            if (之前分型.结构 is 分型结构.顶 and 之前分型.分型特征值 < 分型特征值) or (之前分型.结构 is 分型结构.底 and 之前分型.分型特征值 > 分型特征值):
                _弹出旧笔(sys._getframe().f_lineno)
                if 分型序列:
                    之前分型 = 分型序列[-1]
                    if 当前分型.结构 in (分型结构.上, 分型结构.顶):
                        assert 之前分型.结构 is 分型结构.底, 之前分型.结构
                    else:
                        assert 之前分型.结构 is 分型结构.顶, 之前分型.结构

                    笔.分析(当前分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)  # 处理新顶
                else:
                    # if 当前分型.结构 in (分型结构.底, 分型结构.顶) and 当前分型.右:
                    分型.向序列中添加(分型序列, 当前分型)

        elif (之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.下) or (之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.上):
            临时分型 = None
            if 当前分型.结构 is 分型结构.上:
                临时分型 = 分型(None, 当前分型.右 if 当前分型.右 else 当前分型.中, None, False)
                临时分型.中.分型 = 分型结构.顶
            elif 当前分型.结构 is 分型结构.下:
                临时分型 = 分型(None, 当前分型.右 if 当前分型.右 else 当前分型.中, None, False)
                临时分型.中.分型 = 分型结构.底

            笔.分析(临时分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)  # 处理新顶

        elif (之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.上) or (之前分型.结构 is 分型结构.底 and 当前分型.结构 is 分型结构.下):
            临时分型 = None
            if 当前分型.结构 is 分型结构.上:
                临时分型 = 分型(None, 当前分型.右 if 当前分型.右 else 当前分型.中, None, False)
                临时分型.中.分型 = 分型结构.顶
            elif 当前分型.结构 is 分型结构.下:
                临时分型 = 分型(None, 当前分型.右 if 当前分型.右 else 当前分型.中, None, False)
                临时分型.中.分型 = 分型结构.底

            笔.分析(临时分型, 分型序列, 笔序列, 缠K序列, 来源渠道, 递归层次 + 1, 全局配置, 观察员)  # 处理新顶

        else:
            raise TypeError(之前分型, 当前分型)

    @staticmethod
    def 检查序列(总: List["笔"], 分: List["笔"]) -> bool:
        for _笔 in 分:
            if not (_笔 in 总):
                return False
        return True

    @staticmethod
    def 截取(笔序列: List["笔"], 文: K线, 武: K线) -> List["笔"]:
        序列 = []
        for B in 笔序列:
            if 序列:
                序列.append(B)
            if B.文.中 is 文:
                序列.append(B)
            if B.武.中 is 武:
                break
        if not 序列:
            return 序列
        assert 序列[0].文.中 is 文, (序列[0].文.中, 文)
        assert 序列[-1].武.中 is 武 or 序列[-1].武.中.时间戳 > 武.时间戳, (序列[-1].武.中, 武)
        return 序列

    @staticmethod
    def 以武会友(笔序列: List["笔"], 武: K线) -> Optional["笔"]:
        for _笔 in 笔序列[::-1]:
            if _笔.武.中 is 武:
                return _笔
        return None

    @staticmethod
    def 获取序列中顶底K线(笔序列: List["笔"]) -> List[K线]:
        分型K线序列 = [k.文.中 for k in 笔序列]
        分型K线序列.append(笔序列[-1].武.中)
        return 分型K线序列

    @staticmethod
    def 根据缠K找笔(笔序列: list["笔"], 缠K: "K线", 配置: "缠论配置", 偏移: int = 1):
        for 筆 in 笔序列[::-1]:
            if 缠K in 筆[偏移:]:
                return 筆

        return None

    @staticmethod
    def 根据缠K时间戳找笔(笔序列: list["笔"], 缠K: "K线", 配置: "缠论配置", 偏移: int = 1):
        for 筆 in 笔序列[::-1]:
            时间戳序列 = [K.时间戳 for K in 筆[偏移:]]
            if 缠K.时间戳 in 时间戳序列:
                return 筆

        return None


class 线段(虚线):
    __solts__ = ["特征序列", "实_中枢序列", "虚_中枢序列", "合_中枢序列", "确认K线", "模式", "_特征序列_显示", "第三买卖线"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.特征序列: List[Optional[线段特征]] = [None] * 3

        self.实_中枢序列 = []
        self.虚_中枢序列 = []
        self.合_中枢序列 = []
        self.确认K线: Optional[K线] = None
        self.模式 = "文武"
        self._特征序列_显示 = None
        self.第三买卖线: bool = False
        self.标识 = "线段" if type(self[0]) is 笔 else f"线段<{self[0].标识}>"

    def __str__(self):
        return f"线段<{self.序号}, {self.四象}, {self.方向}, {self.文}, {self.武}, 数量: {len(self)}, 缺口: {self.缺口}, {self.确认K线}>"

    def __repr__(self):
        return f"线段<{self.序号}, {self.四象}, {self.方向}, {self.文}, {self.武}, 数量: {len(self)}, 缺口: {self.缺口}, {self.确认K线}>"

    @property
    def 副本(self) -> Self:
        段 = 线段.新建(self[:], None)
        段._武 = self[2].武
        段.刷新()
        段.观察员 = self.观察员
        return 段

    @property
    def 特征分型终结(self) -> bool:
        """
        是否符合特征序列 正常分型 终结
        """
        特征序列 = 线段特征.静态分析(self, self.方向, self.四象)
        if len(特征序列) >= 3:
            结构 = 分型结构.识别(特征序列[-3], 特征序列[-2], 特征序列[-1], True, True)
            if self.方向 is 相对方向.向上:
                if 结构 is 分型结构.顶:
                    return True
            else:
                if 结构 is 分型结构.底:
                    return True

        return False

    @property
    def 特征序列状态(self) -> Tuple[bool, bool, bool]:
        return tuple(特征 is not None for 特征 in self.特征序列)

    @property
    def 高(self) -> float:
        if self.模式 != "文武":
            return max(self, key=lambda x: x.高).高
        if self.方向 is 相对方向.向上:
            return self.武.分型特征值
        return self.文.分型特征值

    @property
    def 低(self) -> float:
        if self.模式 != "文武":
            return min(self, key=lambda x: x.低).低
        if self.方向 is 相对方向.向下:
            return self.武.分型特征值
        return self.文.分型特征值

    @property
    def 缺口(self) -> Optional[缺口]:
        if self.左 is None:
            return None
        if self.中 is None:
            return None
        相对关系 = 相对方向.识别(self.左, self.中)
        if 相对关系.是否缺口():
            hl = [self.左.文.分型特征值, self.中.文.分型特征值]
            return 缺口(max(*hl), min(*hl))
        return None

    @property
    def 方向(self) -> "相对方向":
        return self[0].方向 if len(self) else super().方向

    @property
    def 四象(self) -> str:
        if self.之前 is not None and self.之前.缺口:
            return "老阳" if self.方向 is 相对方向.向上 else "老阴"
        return "小阳" if self.方向 is 相对方向.向上 else "少阴"

    @property
    def 左(self) -> Optional[线段特征]:
        return self.特征序列[0]

    @左.setter
    def 左(self, 特征: Optional[线段特征]):
        self.__设置特征(0, 特征)

    @property
    def 中(self) -> Optional[线段特征]:
        return self.特征序列[1]

    @中.setter
    def 中(self, 特征: Optional[线段特征]):
        self.__设置特征(1, 特征)
        # self.刷新()

    @property
    def 右(self) -> Optional[线段特征]:
        return self.特征序列[2]

    @右.setter
    def 右(self, 特征: Optional[线段特征]):
        self.__设置特征(2, 特征)
        if 特征 is not None:
            基础序列 = []
            if 特征[-1] not in self:
                raise ValueError()
            for 元素 in self:
                基础序列.append(元素)
                if 元素 is 特征[-1]:
                    break

            if (len(基础序列) >= 6) and (len(基础序列) % 2 == 0):
                # print(colored("   线段.右 基础序列被重置", "yellow"), len(self), len(基础序列), self)
                self[:] = 基础序列[:]
            else:
                raise RuntimeError()
        else:
            # print(colored("线段.右 = None", "yellow"), self.观察员.当前K线)
            pass

    def __设置特征(self, 偏移: int, 特征: Optional[线段特征]):
        if self.模式 != "文武":
            return
        if 特征 and 特征.方向 == self.方向:
            raise ValueError("特征序列方向不匹配")
        特征序列: List = self.特征序列
        观察员: Optional[观察者] = self.观察员
        old = 特征序列[偏移]
        特征序列[偏移] = 特征

        # old and 观察员 and 观察员.报信(old, 指令.删除(old.标识))
        # 特征 and 观察员 and 观察员.报信(特征, 指令.添加(特征.标识))

    def 设置特征序列(self, 序列, 行号):
        # print(f"线段.设置特征序列[{行号}]", self)
        if self.模式 != "文武":
            return
        self.左, self.中, self.右 = 序列

    def __刷新特征序列(self):
        if self.模式 != "文武":
            return
        特征序列 = 线段特征.静态分析(self, self.方向, self.四象)
        if len(特征序列) >= 3:
            分型序列 = 线段特征.获取分型序列(特征序列)
            if (self.方向 is 相对方向.向上 and 分型序列[-1]._结构 is 分型结构.顶) or (self.方向 is 相对方向.向下 and 分型序列[-1]._结构 is 分型结构.底):
                self.设置特征序列([分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)

            elif (self.方向 is 相对方向.向上 and 分型序列[-1]._结构 is 分型结构.上) or (self.方向 is 相对方向.向下 and 分型序列[-1]._结构 is 分型结构.下):
                self.设置特征序列([特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)

            else:
                if self.之前:
                    基础序列 = self[self.index(self.之前[-2]) :]
                    特征序列: List[Optional[线段特征]] = 线段特征.静态分析(基础序列, self.方向, self.四象)
                    分型序列 = 线段特征.获取分型序列(特征序列)

                    if not 分型序列:
                        特征序列.extend([None] * (3 - len(特征序列)))
                        self.设置特征序列(特征序列, sys._getframe().f_lineno)
                        return

                    if (self.方向 is 相对方向.向上 and 分型序列[-1]._结构 is 分型结构.顶) or (self.方向 is 相对方向.向下 and 分型序列[-1]._结构 is 分型结构.底):
                        self.设置特征序列([分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)
                    else:
                        self.设置特征序列([特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)

                else:
                    # 处理 2
                    基础序列 = self[-6:]
                    特征序列: List[Optional[线段特征]] = 线段特征.静态分析(基础序列, self.方向, self.四象)
                    分型序列 = 线段特征.获取分型序列(特征序列)
                    if not 分型序列:
                        特征序列.extend([None] * (3 - len(特征序列)))
                        self.设置特征序列(特征序列, sys._getframe().f_lineno)
                        return

                    if (self.方向 is 相对方向.向上 and 分型序列[-1]._结构 is 分型结构.顶) or (self.方向 is 相对方向.向下 and 分型序列[-1]._结构 is 分型结构.底):
                        self.设置特征序列([分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)
                    else:
                        self.设置特征序列([特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)

        else:
            之前, 之后, _ = self.分割序列()
            if len(之后) >= 3:
                if self.之前:
                    基础序列 = self[self.index(self.之前[-2]) :]
                    特征序列: List[Optional[线段特征]] = 线段特征.静态分析(基础序列, self.方向, self.四象)
                    分型序列 = 线段特征.获取分型序列(特征序列)

                    if not 分型序列:
                        特征序列.extend([None] * (3 - len(特征序列)))
                        self.设置特征序列(特征序列, sys._getframe().f_lineno)
                        return

                    if (self.方向 is 相对方向.向上 and 分型序列[-1]._结构 is 分型结构.顶) or (self.方向 is 相对方向.向下 and 分型序列[-1]._结构 is 分型结构.底):
                        self.设置特征序列([分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)
                    else:
                        self.设置特征序列([特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)
                else:
                    # 处理 2
                    基础序列 = self[-6:]
                    特征序列: List[Optional[线段特征]] = 线段特征.静态分析(基础序列, self.方向, self.四象)
                    分型序列 = 线段特征.获取分型序列(特征序列)
                    if not 分型序列:
                        特征序列.extend([None] * (3 - len(特征序列)))
                        self.设置特征序列(特征序列, sys._getframe().f_lineno)
                        return

                    if (self.方向 is 相对方向.向上 and 分型序列[-1]._结构 is 分型结构.顶) or (self.方向 is 相对方向.向下 and 分型序列[-1]._结构 is 分型结构.底):
                        self.设置特征序列([分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)
                    else:
                        self.设置特征序列([特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)
            else:
                特征序列.extend([None] * (3 - len(特征序列)))
                self.设置特征序列(特征序列, sys._getframe().f_lineno)

    def 武斗(self, 武: 分型, 行号):
        super().武斗(武, 行号)

    def 获取内部中枢序列(self) -> Optional[List["中枢"]]:
        # 线段内部如存在中枢则级别比无中枢要大
        实, 虚, _ = self.分割序列()
        self.观察员 and 中枢.分析(self.观察员.缠论K线序列[-1], 实, self.实_中枢序列, self.观察员, 标识=f"段内<{self.序号}>")  # FIXME 此处需注意观察员
        self.观察员 and 中枢.分析(self.观察员.缠论K线序列[-1], 虚, self.虚_中枢序列, self.观察员, 标识=f"段后<{self.序号}>")  # FIXME 此处需注意观察员

        self.观察员 and 中枢.分析(self.观察员.缠论K线序列[-1], self, self.合_中枢序列, self.观察员, 标识=f"段合<{self.序号}>")  # FIXME 此处需注意观察员

        return self.虚_中枢序列, self.实_中枢序列, self.合_中枢序列  # 阴 阳 合

    def 图表添加(self):
        self.左, self.中, self.右 = self.左, self.中, self.右
        self.观察员 and self.观察员.报信(self, 指令.添加("线段"))

    def 图表刷新(self):
        self.左, self.中, self.右 = self.左, self.中, self.右
        self.观察员 and self.观察员.报信(self, 指令.修改("线段"))
        self.观察员 and self.观察员.中枢序列 and self in self.观察员.中枢序列[-1] and self.观察员.中枢序列[-1].图表刷新(self.观察员)

    def 图表移除(self):
        self.图表移除特征序列()
        self.观察员 and self.观察员.报信(self, 指令.删除("线段"))
        self.之前 = None
        self.之后 = None
        self.有效性 = False
        if self.实_中枢序列:
            for zs in self.实_中枢序列:
                self.观察员 and self.观察员.报信(zs, 指令.删除(zs.标识))
        if self.虚_中枢序列:
            for zs in self.虚_中枢序列:
                self.观察员 and self.观察员.报信(zs, 指令.删除(zs.标识))
        if self.合_中枢序列:
            for zs in self.合_中枢序列:
                self.观察员 and self.观察员.报信(zs, 指令.删除(zs.标识))

    def 图表移除特征序列(self):
        if self._特征序列_显示:
            self._特征序列_显示 = False
            for 特征 in self.特征序列:
                if 特征 is not None:
                    self.观察员 and self.观察员.报信(特征, 指令.删除(特征.标识))

    def 图表显示特征序列(self):
        if not self._特征序列_显示:
            self.__刷新特征序列()
            self._特征序列_显示 = True
            for 特征 in [self.左, self.中, self.右]:
                if 特征 is not None:
                    self.观察员 and self.观察员.报信(特征, 指令.添加(特征.标识))

    def 分割序列(self, 所属中枢: Optional["中枢"] = None):
        assert self[0].文 is self.文, (self[0].文, self.文)
        前: List["笔"] = []
        后: List["笔"] = []
        第三买卖线 = []

        for 筆 in self:
            if not 前:
                前.append(筆)
                continue
            if 前[-1].武.中 is not self.武.中:
                前.append(筆)
                if 筆.方向 is not self.方向 and 所属中枢:
                    关系 = 相对方向.识别(所属中枢, 筆)
                    if (self.方向 is 相对方向.向下 and 关系 is 相对方向.向下缺口) or (self.方向 is 相对方向.向上 and 关系 is 相对方向.向上缺口):
                        if not 所属中枢.本级_第三买卖线:
                            所属中枢.本级_第三买卖线 = 筆
                        第三买卖线.append(筆)

            if 后:
                后.append(筆)
                if 筆.方向 is not self.方向.翻转() and 所属中枢:
                    关系 = 相对方向.识别(所属中枢, 筆)
                    if (self.方向.翻转() is 相对方向.向下 and 关系 is 相对方向.向下缺口) or (self.方向.翻转() is 相对方向.向上 and 关系 is 相对方向.向上缺口):
                        if not 所属中枢.本级_第三买卖线:
                            所属中枢.本级_第三买卖线 = 筆
                        第三买卖线.append(筆)

            if 筆.文.中 is self.武.中:
                后.append(筆)
                if 筆.方向 is not self.方向 and 所属中枢:
                    关系 = 相对方向.识别(所属中枢, 筆)
                    if (self.方向 is 相对方向.向下 and 关系 is 相对方向.向下缺口) or (self.方向 is 相对方向.向上 and 关系 is 相对方向.向上缺口):
                        if not 所属中枢.本级_第三买卖线:
                            所属中枢.本级_第三买卖线 = 筆
                        第三买卖线.append(筆)

        return 前, 后, 第三买卖线

    def 获取基础序列(self) -> List["笔"]:
        assert self[0].文 is self.文, (self[0].文, self.文)
        基础序列: List["笔"] = []
        for 笔_ in self:
            基础序列.append(笔_)
            if 笔_.武.中 is self.武.中:
                break
        return 基础序列

    def 检查连续性(self) -> bool:
        for i in range(1, len(self)):
            if not self[i - 1].之后是(self[i]):
                print("    线段.检查连续性", list.__str__(self))
                print("    线段.检查连续性", self[i - 1], self[i])
                return False
        return True

    def 删除虚线(self, 线: "笔") -> "笔":
        if self[-1] is 线:
            self.pop()
        else:
            raise ValueError("线段.删除虚线 不在序列中")
        self.刷新()
        self.观察员 and self.观察员.报信(self, 指令.修改("线段"))
        return 线

    def 添加虚线(self, 线: "笔"):
        if len(self) and self[-1].武.中 is not 线.文.中:
            raise IndexError("线段.添加虚线 不连续", self[-1], 线)
        self.append(线)
        self.刷新()

    def 刷新(self):
        if self.模式 != "文武":
            return
        if not len(self):
            print("    线段.刷新 基础序列为空")
            return
        self.__刷新特征序列()
        有效特征序列 = [特征 for 特征 in self.特征序列 if 特征 is not None]
        if len(有效特征序列) == 3:
            self.武斗(self.中.文, sys._getframe().f_lineno)
        elif len(有效特征序列) >= 1:
            最近特征 = 有效特征序列[-1]

            if 最近特征[-1] not in self:
                特征后一笔 = 笔.以武会友(self, 最近特征[-1].武.中)
            else:
                特征后一笔 = 最近特征[-1]
            if 特征后一笔 is not None:
                序号 = self.index(特征后一笔)
                if len(self) - 1 > 序号:
                    下一笔 = self[序号 + 1]
                    if self.方向 is 相对方向.向上:
                        if self.高 <= 下一笔.高:
                            self.武斗(下一笔.武, sys._getframe().f_lineno)
                    else:
                        if self.低 >= 下一笔.低:
                            self.武斗(下一笔.武, sys._getframe().f_lineno)
            else:
                print("    线段.刷新 特征后一笔 = None, ", self, 有效特征序列)
        else:
            raise RuntimeError(len(有效特征序列))

        self.获取内部中枢序列()
        self.观察员 and self.观察员.中枢序列 and self.观察员.中枢序列[-1].识别第三买卖点(self.观察员.缠论K线序列[-1], self.观察员)  # TODO 识别买卖点
        self.观察员 and self.观察员.中枢序列 and self.观察员.中枢序列[-1].第三买卖点失效判定(self.观察员.缠论K线序列[-1], self.观察员)
        self.图表刷新()

    def 序列重置(self, 序列: List):
        异常序列 = []
        for 元素 in self:
            if 元素 not in 序列:
                assert 元素.有效性 == False, f"有效性：{元素.有效性}, {元素}，{序列[元素.序号]}"
                异常序列.append(元素)
            if 元素.武.结构 in (分型结构.上, 分型结构.下):
                # print("    线段.序列重置 发现临时笔", self.index(元素), len(self))
                ...

        # print(colored(f"线段.序列重置 线段id={self.序号} 发现异常元素数量: {len(异常序列)}", "red"))

        原始序列 = self[:]
        基础序列 = []
        for 元素 in self:
            if 元素 not in 序列:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    print("    线线.序列重置 数据不连续")
                    break
            基础序列.append(元素)

        self[:] = 基础序列[:]
        if not 异常序列:
            return []

        assert len(异常序列) + len(self) == len(原始序列)

        try:
            序号 = 序列.index(self[-1])
        except IndexError:
            print("线段.序列重置 内部元素非预期的不存在")  # raise RuntimeError()

        """if len(异常序列) == 1:
            if self.特征序列[2] is not None:
                替代物 = 序列[序号 + 1]
                assert 替代物.序号 == 异常序列[0].序号
                self.append(替代物)
                self.刷新()
                异常序列 = [] if self.右 else 异常序列
            else:
                if 序号 < len(序列) - 1:
                    替代物 = 序列[序号 + 1]
                    assert 替代物.序号 == 异常序列[0].序号
                    self.append(替代物)
                    异常序列 = []"""

        # self.刷新()
        if self.右 is not None:
            self.右 = None
        return 异常序列

    def 计算内部是否背驰(self, 当前K线: K线, 观察员: "观察者", 配置: 缠论配置):
        pass

    @classmethod
    def 基础线段判断(cls, 左: 虚线, 中: 虚线, 右: 虚线, 关系序列=None) -> bool:
        """
        连续三笔且重叠
        """
        if 关系序列 is None:
            关系序列 = [相对方向.向上, 相对方向.向下, 相对方向.顺, 相对方向.逆, 相对方向.同]
        if not 三折叠.基础判断(左, 中, 右, 关系序列):
            return False

        if 左.文.结构 is 分型结构.顶 and not 相对方向.识别(左, 右).是否向下():
            return False
        if 左.文.结构 is 分型结构.底 and not 相对方向.识别(左, 右).是否向上():
            return False
        return True

    @classmethod
    def 新建(cls, 线: Union["笔", List["笔"]], 观察员: Optional["观察者"]) -> "线段":
        if isinstance(线, list):
            虚线序列 = 线[:]
        else:
            虚线序列 = [
                线,
            ]
        段 = 线段(
            序号=0,
            之前=None,
            之后=None,
            文=虚线序列[0].文,
            武=虚线序列[-1].武,
            基础序列=虚线序列,
            观察员=观察员,
        )
        return 段

    @classmethod
    def 分析(cls, 当前K线: K线, 笔序列: List["笔"], 线段序列: List["线段"], 中枢序列: List["中枢"], 观察员: "观察者", 配置: 缠论配置, 层级: int = 0) -> None:
        """
        注意笔序列前三个元素必须符合线段基本要求
        四象: 老阴，老阳，少阴，小阳
            老阴 老阳 分别代表 缺口顶分型后的向下线段 与 缺口底分型后的向上线段
            当其分型完成时需要对 线段.之前 设置为None，新线段不在考虑之前是否有缺口的问题
        无缺口: 即笔破坏
            笔破坏不去处理特征序列的逆序包含
        """
        if 层级 > 20:
            raise RuntimeError("线段分析 层级过深")

        def _添加线段(待添加线段: "线段", 行号):
            if 线段序列 and not 线段序列[-1].之后是(待添加线段):
                raise ValueError(f"线段.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)

            if 线段序列:
                之前线段 = 线段序列[-1]
                if not 之前线段.右 and 之前线段.模式 == "文武":
                    assert 之前线段.右[-1] in 待添加线段
                    raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段.右 = None", 之前线段)
                if 之前线段[-1] not in 待添加线段 and 之前线段.模式 == "文武":
                    raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段[-1] not in 待添加虚线!", 之前线段)
                待添加线段.序号 = 之前线段.序号 + 1
                待添加线段.之前 = 之前线段
                if 观察员:
                    if 之前线段.确认K线 is None:
                        之前线段.确认K线 = 观察员.缠论K线序列[-1]

                之前线段.图表移除特征序列()
                之前线段.图表刷新()
                之前线段.之后 = 待添加线段

            待添加线段.文.中.线段_以我为起点_计数 += 1
            线段序列.append(待添加线段)
            待添加线段.图表添加()
            # print(f"线段._向序列中添加[{行号}]", 待添加虚线)
            待添加线段.获取内部中枢序列()
            中枢.分析(当前K线, 线段序列, 中枢序列, 观察员)
            # 观察员 and 线段.扩展分析(当前K线, 线段序列, 观察员.扩展线段序列, 观察员.扩展中枢序列, 观察员, 配置)

        def _弹出线段(待弹出线段: "线段", 行号):
            if not 线段序列:
                return None

            if 线段序列[-1] is 待弹出线段:
                if 待弹出线段.右 is not None:
                    结构 = 分型结构.识别(待弹出线段.左, 待弹出线段.中, 待弹出线段.右, True, True)
                    if 结构 in (分型结构.顶, 分型结构.底) and not 相对方向.识别(待弹出线段.左, 待弹出线段.中).是否缺口():
                        raise ValueError("线段._从序列中删除 发现分型完毕, 且特征序列无缺口", 待弹出线段)
                线段序列.pop()
                if 线段序列:
                    线段序列[-1].之后 = None
                待弹出线段.图表移除()
                # print(f"线段._从序列中删除[{行号}]", 待弹出线段)
                中枢.分析(当前K线, 线段序列, 中枢序列, 观察员)
                # 观察员 and 线段.扩展分析(当前K线, 线段序列, 观察员.扩展线段序列, 观察员.扩展中枢序列, 观察员, 配置)
                return 待弹出线段
            raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

        if not 线段序列:
            for i in range(1, len(笔序列) - 1):
                左, 中, 右 = 笔序列[i - 1], 笔序列[i], 笔序列[i + 1]
                if not 线段.基础线段判断(左, 中, 右, [相对方向.向上, 相对方向.向下]):  # FIXME 此处为首个线段
                    continue

                段 = 线段.新建([左, 中, 右], 观察员)
                _添加线段(段, f"{sys._getframe().f_lineno}, {层级}")
                段.左 = 线段特征.新建([中], 段.方向)
                break

        # 检查线段元素
        if not 线段序列:
            return None

        try:
            之前线段 = 线段序列[-2]
        except IndexError:
            之前线段 = None
        当前线段 = 线段序列[-1]

        if 当前线段.序列重置(笔序列) and 之前线段:
            # 检查异常元素是否涉及上一段
            异常元素序列 = 之前线段.序列重置(笔序列)
            if 异常元素序列:
                # print(colored(f"线段.分析[{层级}] 当前线段 异常元素 涉及上一段", "red"), len(异常元素序列))
                _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                当前线段 = 之前线段
                # return 线段.分析(当前K线, 笔序列, 线段序列, 中枢序列, 观察员, 配置, 层级+1)
            else:
                # 之前线段.__刷新特征序列()
                assert 之前线段.右 is not None

        if len(当前线段) < 3:
            _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
            return 线段.分析(当前K线, 笔序列, 线段序列, 中枢序列, 观察员, 配置, 层级 + 1)

        if 当前线段.右 is not None:
            基础序列 = 当前线段.分割序列()[1]
            print(
                colored(f"线段.分析[{层级}] 特殊情况, 特征序列俱全时出现在 线段序列尾部, 基础序列: ", "red"),
                len(基础序列),
                当前线段,
            )
            """
            if not 基础序列:
                线段._从序列中删除(线段序列, 当前线段, f"{sys._getframe().f_lineno}, {层级}")
                return 线段.分析(当前K线, 笔序列, 线段序列, 中枢序列, 观察员, 配置, 层级 + 1)
            """
            新段 = 线段.新建(基础序列, 观察员)
            _添加线段(新段, f"{sys._getframe().f_lineno}, {层级}")
            当前线段.图表移除特征序列()
            """if 当前线段.四象 in ("老阴", "老阳"):
                新段.之前 = None"""

        当前线段 = 线段序列[-1]
        当前线段.刷新()
        序号 = 笔序列.index(当前线段[-1]) + 1

        for 当前虚线 in 笔序列[序号:]:
            当前线段 = 线段序列[-1]

            四象 = 当前线段.四象
            线段方向 = 当前线段.方向
            同向 = 当前虚线.方向 is 线段方向
            if not 当前线段.检查连续性():
                raise IndexError(f"线段.分析[{层级}] 当前线段.检查连续性 失败")
            当前线段.添加虚线(当前虚线)

            if 同向:
                match 四象:
                    case "老阳":
                        assert 线段方向.是否向上()
                        continue
                    case "老阴":
                        assert 线段方向.是否向下()
                        continue
                    case "小阳":
                        assert 线段方向.是否向上()
                        continue
                    case "少阴":
                        assert 线段方向.是否向下()
                        continue
            else:
                match 四象:
                    case "老阳":
                        assert 线段方向.是否向上()
                        if 当前虚线.低 < 当前线段.低 and 当前线段.右 is None:
                            # 缺口底分型被突破
                            序列 = 当前线段[:]
                            _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                            当前线段 = 线段序列[-1]
                            assert 当前线段.右 is not None
                            当前线段基础序列 = 当前线段.分割序列()[0]
                            当前线段基础序列.extend(序列)

                            当前线段[:] = 当前线段基础序列[:]
                            当前线段.刷新()
                            continue

                    case "老阴":
                        assert 线段方向.是否向下()
                        if 当前虚线.高 > 当前线段.高 and 当前线段.右 is None:
                            # 缺口顶分型被突破
                            序列 = 当前线段[:]
                            _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")

                            当前线段 = 线段序列[-1]
                            assert 当前线段.右 is not None
                            当前线段基础序列 = 当前线段.分割序列()[0]
                            当前线段基础序列.extend(序列)

                            当前线段[:] = 当前线段基础序列[:]
                            当前线段.刷新()
                            continue
                    case "小阳":
                        assert 线段方向.是否向上()
                        if len(当前线段.分割序列()[0]) == 3 and 相对方向.识别(当前线段[0], 当前线段[2]).是否包含() and 当前虚线.低 < 当前线段.低 and 当前线段.右 is None:
                            if len(线段序列) > 1:
                                _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                                assert 线段序列[-1].四象 in ("老阴", "老阳")  # FIXME 异常时可以注释掉当前行
                                线段序列[-1].之前 = None
                                print("============================================")
                                print("=================异常1线段====================")
                                print(当前线段, 当前虚线)
                                print("============================================")
                                线段序列[-1].刷新()
                                return 线段.分析(当前K线, 笔序列, 线段序列, 中枢序列, 观察员, 配置, 层级 + 1)
                    case "少阴":
                        assert 线段方向.是否向下()
                        if len(当前线段.分割序列()[0]) == 3 and 相对方向.识别(当前线段[0], 当前线段[2]).是否包含() and 当前虚线.高 > 当前线段.高 and 当前线段.右 is None:
                            if len(线段序列) > 1:
                                _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                                assert 线段序列[-1].四象 in ("老阴", "老阳")  # FIXME 异常时可以注释掉当前行
                                线段序列[-1].之前 = None
                                print("============================================")
                                print("=================异常2线段====================")
                                print(当前线段, 当前虚线)
                                print("============================================")
                                # bitstamp 日线 btc/usd [2014-6-2 8:00] >>> [2017-1-5 8:00] # 在此区间出现 向下线段终点大于起点的情况
                                线段序列[-1].刷新()
                                return 线段.分析(当前K线, 笔序列, 线段序列, 中枢序列, 观察员, 配置, 层级 + 1)

                if 当前线段.右 is not None:
                    基础序列 = 当前线段.分割序列()[1]
                    新段 = 线段.新建(基础序列, 观察员)
                    _添加线段(新段, f"{sys._getframe().f_lineno}, {层级}")
                    当前线段.图表移除特征序列()
                    if 四象 in ("老阴", "老阳"):
                        新段.之前 = None

                    if 笔序列.index(当前虚线) - 笔序列.index(新段[-1]) != 0:
                        print(f"线段.分析[{层级}] 序列差", 笔序列.index(当前虚线) - 笔序列.index(新段[-1]))
                        新段.刷新()
                        return 线段.分析(当前K线, 笔序列, 线段序列, 中枢序列, 观察员, 配置, 层级 + 1)

                    if 新段[-1].之后是(当前虚线):
                        新段.添加虚线(当前虚线)

                    新段.刷新()

        return None

    def _武终(self):
        if self.模式 != "文武":
            self.武斗(self[-1].武, "扩展模式")

    def _验证序列(self, 序列):
        基础序列 = []
        for 元素 in self:
            if 元素 not in 序列:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    print("    线段._验证序列 数据不连续")
                    break
            基础序列.append(元素)
        self[:] = 基础序列[:]
        if len(self) % 2 == 0:
            self.pop()

    @classmethod
    def 扩展分析(cls, 当前K线: K线, 虚线序列: List["笔"], 线段序列: List["线段"], 中枢序列: List["中枢"], 观察员: "观察者", 配置: 缠论配置) -> None:
        if not 虚线序列:
            return None
        try:
            虚线序列[2]
        except IndexError:
            return None

        def _添加线段(待添加线段: "线段", 行号):
            if 线段序列 and not 线段序列[-1].之后是(待添加线段):
                raise ValueError(f"线段.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)

            if 线段序列:
                待添加线段.序号 = 线段序列[-1].序号 + 1
                待添加线段.之前 = 线段序列[-1]
                之前线段 = 线段序列[-1]
                if 观察员:
                    if 之前线段.确认K线 is None:
                        之前线段.确认K线 = 观察员.缠论K线序列[-1]

                之前线段.图表刷新()
                if not 之前线段.右 and 之前线段.模式 == "文武":
                    assert 之前线段.右[-1] in 待添加线段
                    raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段.右 = None", 之前线段)
                if 之前线段[-1] not in 待添加线段 and 之前线段.模式 == "文武":
                    raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段[-1] not in 待添加虚线!", 之前线段)
                之前线段.之后 = 待添加线段

            待添加线段.文.中.线段_以我为起点_计数 += 1
            线段序列.append(待添加线段)
            待添加线段.标识 = f"扩展线段<{待添加线段.标识}>"
            待添加线段.图表添加()
            # print(f"线段._向序列中添加[{行号}]", 待添加虚线)
            中枢.分析(当前K线, 线段序列, 中枢序列, 观察员)

        def _弹出线段(待弹出线段: "线段", 行号):
            if not 线段序列:
                return None

            if 线段序列[-1] is 待弹出线段:
                if 待弹出线段.右 is not None:
                    结构 = 分型结构.识别(待弹出线段.左, 待弹出线段.中, 待弹出线段.右, True, True)
                    if 结构 in (分型结构.顶, 分型结构.底) and not 相对方向.识别(待弹出线段.左, 待弹出线段.中).是否缺口():
                        raise ValueError("线段._从序列中删除 发现分型完毕, 且特征序列无缺口", 待弹出线段)
                drop = 线段序列.pop()
                待弹出线段.图表移除()
                # print(f"线段._从序列中删除[{行号}]", 待弹出线段)
                中枢.分析(当前K线, 线段序列, 中枢序列, 观察员)
                return drop
            raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

        if not 线段序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                if not 三折叠.基础判断(左, 中, 右):  # FIXME 此处为首个线段
                    continue

                段 = 线段.新建([左, 中, 右], 观察员)
                段.模式 = "高低"
                _添加线段(段, sys._getframe().f_lineno)
                break

        # 检查线段元素
        if not 线段序列:
            return None

        当前线段 = 线段序列[-1]
        当前线段._验证序列(虚线序列)
        if len(当前线段) < 3:
            _弹出线段(当前线段, sys._getframe().f_lineno)
            return 线段.扩展分析(当前K线, 虚线序列, 线段序列, 中枢序列, 观察员, 配置)

        当前线段._武终()
        # 当前线段 = 线段序列[-1]

        try:
            序号 = 虚线序列.index(当前线段[-1]) + 1
            if 序号 >= len(虚线序列):
                return None
            for i in range(序号 + 1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                相对关系 = 相对方向.识别(左, 右)
                if 相对关系.是否缺口():
                    当前线段.添加虚线(左)
                    当前线段.添加虚线(中)
                    当前线段._武终()
                    continue

                if 左 in 当前线段:
                    continue

                段 = 线段.新建([左, 中, 右], 观察员)
                段.模式 = "高低"
                _添加线段(段, sys._getframe().f_lineno)
                return 线段.扩展分析(当前K线, 虚线序列, 线段序列, 中枢序列, 观察员, 配置)
        except ValueError as e:
            traceback.print_exc()
            _ = 当前线段.pop()
            if len(当前线段) < 3:
                _弹出线段(当前线段, sys._getframe().f_lineno)
            return 线段.扩展分析(当前K线, 虚线序列, 线段序列, 中枢序列, 观察员, 配置)


class 中枢(三折叠):
    __slots__ = ["序号", "级别", "支持延续", "支持扩张", "扩展序列", "标记时间戳", "第三买卖线", "本级_第三买卖线", "进入段", "离开段", "买卖点字典", "观察员"]

    def __init__(self, 序号: int, 标识: str, 级别: int, 支持延续: bool, 支持扩张: bool, 基础序列: List[Union["笔", "线段"]], 观察员: Optional["观察者"]):
        super().__init__(*基础序列[:3])
        self.序号: int = 序号
        self.标识: str = 标识
        self.级别: int = 级别
        self.支持延续: bool = 支持延续
        self.支持扩张: bool = 支持扩张
        self.扩展序列: List[Union["笔", "线段"]] = []  # FIXME 此处包含
        self.标记时间戳: Optional[datetime] = None  # 用于显示
        self.第三买卖线: Optional[Union["笔", "线段"]] = None
        self.本级_第三买卖线: Optional[Union["笔", "线段"]] = None
        self.进入段: Optional[Union["笔", "线段"]] = None
        self.离开段: Optional[Union["笔", "线段"]] = None
        self.买卖点字典: Dict[str, Set[买卖点]] = dict()
        # self.失效买卖点字典: Dict[str, Set[买卖点]] = dict()
        self.观察员: Optional["观察者"] = 观察员

    @property
    def 完整性(self):
        """

        详情见 教你炒股票 43：有关背驰的补习课(2007-04-06 15:31:28)
        不完整时 下一个中枢大概率会与当前中枢发生扩展！

        """
        if type(self[0]) is 线段:
            if len(self.动态获取本级第三买卖线()):
                return True

        return False

    def 动态获取本级第三买卖线(self):
        """

        详情见 教你炒股票 43：有关背驰的补习课(2007-04-06 15:31:28)
        不完整时 下一个中枢大概率会与当前中枢发生扩展！

        """
        if type(self[0]) is not 线段:
            return
        self.本级_第三买卖线 = None
        _, _, 动态序列 = self[-1].分割序列(self)
        if self[-1].之后 is not None:
            动态序列 = [筆 for 筆 in 动态序列 if 筆.武.中.时间戳 < self[-1].武.中.时间戳]
        return 动态序列

    @property
    def 特征(self) -> str:
        return f"{self.标识}_{int(self.左.文.中.时间戳.timestamp())}_{int(self.中.文.中.时间戳.timestamp())}_{int(self.右.文.中.时间戳.timestamp())}"

    @property
    def 方向(self) -> 相对方向:
        if self.中 is None:
            print(colored("中枢.方向 无法获取", "red", attrs=["bold"]))
            return self.左.方向.翻转()
        return self.中.方向

    @property
    def 中高(self) -> float:
        return min(self[:3], key=lambda o: o.高).高

    @property
    def 中低(self) -> float:
        return max(self[:3], key=lambda o: o.低).低

    @property
    def g(self) -> float:
        return min(self, key=lambda o: o.高).高

    @property
    def d(self) -> float:
        return max(self, key=lambda o: o.低).低

    @property
    def 高高(self) -> float:
        return max(self, key=lambda o: o.高).高

    @property
    def 低低(self) -> float:
        return min(self, key=lambda o: o.低).低

    @property
    def 高(self) -> float:
        return self.中高

    @property
    def 低(self) -> float:
        return self.中低

    @property
    def 文(self) -> 分型:
        return self[0].文

    @property
    def 武(self) -> 分型:
        return self[-1].武

    @property
    def 是否延伸(self) -> bool:
        if len(self) > 3:
            return True
        return False

    @property
    def 是否延续(self) -> bool:
        return self.是否延伸

    @property
    def 是否扩展(self) -> bool:
        if len(self.扩展序列) > 0:
            return True
        return False

    def 获取高级中枢(self) -> List["中枢"]:  # FIXME 待定方法
        扩展线段序列 = []
        扩展中枢序列 = []
        if len(self) >= 9:
            观察员 = self.观察员
            观察员 and 线段.扩展分析(观察员.缠论K线序列[-1], self, 扩展线段序列, 扩展中枢序列, 观察员, 观察员.配置)
        return 扩展中枢序列

    def 获取序列(self) -> List[Union["笔", "线段"]]:
        序列: List = self[:]
        if self.第三买卖线 is not None:
            序列.append(self.第三买卖线)
        return 序列

    def 移除非法元素(self, 序列: Sequence):
        有效序列 = []
        for 元素 in self:
            if 元素 not in 序列:
                break
            有效序列.append(元素)
        self[:] = 有效序列
        有效序列 = []

        if not self.校验合法性():
            self[:] = []
            return

        for 元素 in self:
            if 相对方向.识别(self, 元素).是否缺口():
                break
            有效序列.append(元素)
        self[:] = 有效序列

        if self.第三买卖线 is not None:
            if not self[-1].之后是(self.第三买卖线):
                self.第三买卖线 = None
            elif not 相对方向.识别(self, self.第三买卖线).是否缺口():
                self.append(self.第三买卖线)
                self.第三买卖线 = None

    def 处理K线(self, 当前K线: K线):
        pass

    def 设置第三买卖线(self, 当前K线: "K线", 线: Union[笔, 线段, None], 观察员: "观察者", 行号):
        old = self.第三买卖线
        self.第三买卖线 = 线
        self.观察员 and self.观察员.报信(self, 指令.修改(self.标识))
        if 线 is not None:
            线.第三买卖线 = True
        if old is not None:
            old.第三买卖线 = False
        if "笔" in self.标识:
            ...
        self.识别第三买卖点(当前K线, 观察员)
        self.第三买卖点失效判定(当前K线, 观察员)

    def 第三买卖点失效判定(self, 当前K线: "K线", 观察员: "观察者"):
        pass

    def 识别第三买卖点(self, 当前K线: "K线", 观察员: "观察者"):
        pass

    def 识别盘背(self, 当前K线: "K线", 观察员: "观察者"):
        if not self.校验合法性():
            return
        # if self.第三买卖线:
        #     return
        进入段 = self[0].之前

        离开段 = self[-1]
        关系 = 相对方向.识别(进入段, 离开段)

        基础信息 = {"无": ""}
        # if not 关系.是否包含():
        ii = 进入段.计算MACD()
        oo = 离开段.计算MACD()
        基础信息 = {
            "MACD背驰": {
                "阳": False,
                "阴": False,
                "合": False,
            },
            "斜率背驰": False,
            "测度背驰": False,
        }
        基础信息["MACD背驰"]["阳"] = ii["up"] > oo["up"]
        基础信息["MACD背驰"]["阴"] = ii["down"] > oo["down"]
        基础信息["MACD背驰"]["合"] = ii["sum"] > oo["sum"]
        基础信息["斜率背驰"] = 进入段.计算速率() > 离开段.计算速率()
        基础信息["测度背驰"] = 进入段.计算测度() > 离开段.计算测度()
        return 基础信息

    def 当前信息(self):
        try:
            背驰信息 = self.识别盘背(None, None)
            if 背驰信息:
                return "阴阳合" + f"{(背驰信息['MACD背驰']['阴'], 背驰信息['MACD背驰']['阳'], 背驰信息['MACD背驰']['合'])}" + "; 斜率, 测度 " + f"{背驰信息['斜率背驰'], 背驰信息['测度背驰']}"
        except Exception as ex:
            return str(ex)
        return ""

    def 图表刷新(self, 观察员: Optional["观察者"]):
        观察员 and 观察员.报信(self, 指令.删除(self.标识))
        观察员 and 观察员.报信(self, 指令.添加(self.标识))

    def 图表移除(self):
        self.观察员 and self.观察员.报信(self, 指令.删除(self.标识))

    @classmethod
    def 图表检查(cls, 当前中枢: "中枢", 观察员: Optional["观察者"]):
        if 当前中枢.标记时间戳 != 当前中枢[-1].武.时间戳:
            观察员 and 观察员.报信(当前中枢, 指令.删除(当前中枢.标识))
            观察员 and 观察员.报信(当前中枢, 指令.添加(当前中枢.标识))
            当前中枢.标记时间戳 = 当前中枢[-1].武.时间戳

    @classmethod
    def 基础检查(cls, 左: Union["笔", "线段"], 中: Union["笔", "线段"], 右: Union["笔", "线段"]) -> bool:
        return 三折叠.基础判断(左, 中, 右, [相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同])

    @classmethod
    def 创建(cls, 左: Union["笔", "线段"], 中: Union["笔", "线段"], 右: Union["笔", "线段"], 支持延续: bool, 支持扩张: bool, 级别: int, 观察员: Optional["观察者"], 标识: str = "") -> "中枢":
        assert 中枢.基础检查(左, 中, 右)
        return 中枢(
            序号=0,
            标识=f"{标识}中枢<{中.标识}>",
            基础序列=[左, 中, 右],
            级别=级别,
            支持延续=支持延续,
            支持扩张=支持扩张,
            观察员=观察员,
        )

    @classmethod
    def 从序列中获取中枢(cls, 虚线序列: List[Union["笔", "线段"]], 起始方向: 相对方向, 观察员: Optional["观察者"], 标识: str) -> Optional["中枢"]:
        if len(虚线序列) < 3:
            return None

        for i in range(1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            if 中枢.基础检查(左, 中, 右):
                if 起始方向 is not None and 左.方向 is not 起始方向:
                    continue
                return 中枢.创建(左, 中, 右, 支持延续=True, 支持扩张=True, 级别=0, 观察员=观察员, 标识=标识)

        return None

    @classmethod
    def 分析(cls, 当前K线: K线, 虚线序列: Sequence[Union["笔", "线段"]], 中枢序列: List["中枢"], 观察员: Optional["观察者"], 支持延续: bool = True, 支持扩张: bool = True, 标识: str = "", 层级: int = 0) -> None:
        if not 虚线序列:
            return None

        def 向中枢序列尾部添加(待添加中枢: "中枢"):
            if 中枢序列:
                待添加中枢.序号 = 中枢序列[-1].序号 + 1
                if 中枢序列[-1].获取序列()[-1].序号 > 待添加中枢.获取序列()[-1].序号:
                    raise ValueError()
            中枢序列.append(待添加中枢)
            观察员 and 观察员.报信(待添加中枢, 指令.添加(待添加中枢.标识))

        def 从中枢序列尾部弹出(待弹出中枢: "中枢") -> Optional["中枢"]:
            if not 中枢序列:
                return None
            if 中枢序列[-1] is 待弹出中枢:
                观察员 and 观察员.报信(待弹出中枢, 指令.删除(待弹出中枢.标识))
                return 中枢序列.pop()
            return None

        if not 中枢序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                if 中枢.基础检查(左, 中, 右):
                    新中枢 = 中枢.创建(左, 中, 右, 支持延续, 支持扩张, 0, 观察员, 标识)
                    序号 = 虚线序列.index(左)
                    if 左.序号 == 0 or 序号 == 0:
                        continue  # 方便计算走势
                    if 序号 >= 2:
                        同向相对关系 = 相对方向.识别(虚线序列[序号 - 2], 左)
                        if 同向相对关系.是否向上() and 左.方向.是否向上():
                            continue
                        if 同向相对关系.是否向下() and 左.方向.是否向下():
                            continue

                    向中枢序列尾部添加(新中枢)
                    return 中枢.分析(当前K线, 虚线序列, 中枢序列, 观察员, 支持延续, 支持扩张, 标识, 层级 + 1)

            return None

        当前中枢 = 中枢序列[-1]
        当前序列备份 = 当前中枢[:]
        当前中枢.移除非法元素(虚线序列)
        if not 当前中枢.校验合法性():
            从中枢序列尾部弹出(当前中枢)
            return 中枢.分析(当前K线, 虚线序列, 中枢序列, 观察员, 支持延续, 支持扩张, 标识, 层级 + 1)

        if 当前中枢.第三买卖线 is not None:
            if not 当前中枢.第三买卖线.有效性:
                # print("中枢.分析 第三买卖线 已经无效", 当前K线)
                当前中枢.设置第三买卖线(当前K线, None, 观察员, sys._getframe().f_lineno)

            else:
                if not 相对方向.识别(当前中枢, 当前中枢.第三买卖线).是否缺口():
                    # print("中枢.分析 第三买卖线 弹出", 当前K线)
                    当前中枢.append(当前中枢.第三买卖线)
                    当前中枢.设置第三买卖线(当前K线, None, 观察员, sys._getframe().f_lineno)

        if 当前中枢[-1] not in 虚线序列:
            print(f"中枢<{标识}{虚线序列[-1].__class__.__name__}>.分析 {当前中枢[-1]} not in 虚线序列", 虚线序列[-1])
            当前中枢.移除非法元素(虚线序列)
            if not 当前中枢.校验合法性():
                从中枢序列尾部弹出(当前中枢)
                return 中枢.分析(当前K线, 虚线序列, 中枢序列, 观察员, 支持延续, 支持扩张, 标识, 层级 + 1)

        序号 = 虚线序列.index(当前中枢[-1]) + 1

        基础序列 = []
        for 当前虚线 in 虚线序列[序号:]:
            if 相对方向.识别(当前中枢, 当前虚线).是否缺口():
                基础序列.append(当前虚线)
                if 当前中枢[-1].之后是(当前虚线):
                    当前中枢.设置第三买卖线(当前K线, 当前虚线, 观察员, sys._getframe().f_lineno)
                else:
                    ...
            else:
                if not 基础序列:
                    assert 当前中枢[-1].之后是(当前虚线)
                    当前中枢.append(当前虚线)
                    观察员 and 观察员.报信(当前中枢, 指令.修改(当前中枢.标识))
                else:
                    基础序列.append(当前虚线)
            当前中枢.第三买卖点失效判定(当前K线, 观察员)
            if len(基础序列) >= 3:
                新中枢 = 中枢.从序列中获取中枢(基础序列[:], 当前中枢.第三买卖线.方向, 观察员, 标识)
                if 新中枢 is None:
                    基础序列.pop(0)
                else:
                    方向 = 相对方向.识别(当前中枢, 新中枢)
                    if 方向.是否向上():
                        if 基础序列[0].方向 == 相对方向.向上:
                            基础序列.pop(0)
                            continue
                    elif 方向.是否向下():
                        if 基础序列[0].方向 == 相对方向.向下:
                            基础序列.pop(0)
                            continue
                    else:
                        print(colored(f"{方向}", "red"))

                    向中枢序列尾部添加(新中枢)
                    当前中枢 = 新中枢
                    基础序列 = []
        return None


class 走势类型(Enum):
    # situation
    基盘 = "基础盘整"  # 大于3个连续的线，同向的线存在包含关系
    基涨 = "基础上涨"  # 大于3个连续的线，结束点比起始点高
    基跌 = "基础下跌"  # 大于3个连续的线，结束点比起始点低
    盘 = "盘整"
    涨 = "上涨"
    跌 = "下跌"

    @classmethod
    def 分析(cls, 虚线序列: List[Union["笔", "线段"]]) -> Optional["走势类型"]:

        length = len(虚线序列)

        if length == 3:
            关系 = 相对方向.识别(虚线序列[0], 虚线序列[-1])
            if 关系.是否向上():
                return 走势类型.基涨
            if 关系.是否向下():
                return 走势类型.基跌
            if 关系.是否包含():
                return 走势类型.基盘

        中枢序列 = []
        中枢.分析(None, 虚线序列, 中枢序列, None)

        if length > 3:
            if length % 2 == 1:
                if not 中枢序列:
                    if 虚线序列[0].方向 is 相对方向.向上:
                        return 走势类型.基涨
                    return 走势类型.基跌

            相对关系 = 相对方向.识别(虚线序列[0], 虚线序列[-1])
            if 相对关系.是否向上():
                return 走势类型.基涨 if type(虚线序列[0]) is not type(走势) else 走势类型.涨
            elif 相对关系.是否向下():
                return 走势类型.基跌 if type(虚线序列[0]) is not type(走势) else 走势类型.跌
            elif 相对关系.是否包含():
                return 走势类型.基盘 if type(虚线序列[0]) is not type(走势) else 走势类型.盘
            else:
                raise RuntimeError(f"无法通过关系判断走势类型 : {相对关系}")
        return None


class 走势(虚线):
    @classmethod
    def 滑动分析(cls, 当前K线, 数量: int, 线段序列: List[线段], 买卖点序列: list, 观察员: "观察者"):
        pass


@final
class _图表配色:
    笔: str = "#FF82D5"
    线段: str = "#F1C40F"
    走势: str = "#00C40F"  # 二级线段
    灰色: str = "#BEBEBE"

    @staticmethod
    def invert_alpha(color_str, default_alpha=1.0):
        """
        将颜色字符串的透明度取反，并以 rgba() 格式返回。

        参数:
            color_str (str): 颜色字符串，支持 HEX (#RGB, #RRGGBB, #RGBA, #RRGGBBAA) 或
                             RGB/RGBA (rgb(r,g,b), rgba(r,g,b,a)) 格式。
            default_alpha (float): 当输入字符串不包含透明度时使用的原始透明度值，默认 1.0。

        返回:
            str: 格式为 "rgba(r, g, b, a)" 的字符串，其中 a 为取反后的透明度。
        """
        color_str = color_str.strip()

        # 匹配 HEX 格式
        hex_pattern = re.compile(r"^#([0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
        # 匹配 RGB/RGBA 格式
        rgba_pattern = re.compile(r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9.]+)\s*)?\)$", re.IGNORECASE)

        if hex_pattern.match(color_str):
            # 处理 HEX
            hex_part = color_str.lstrip("#")
            # 扩展简写
            if len(hex_part) == 3:
                hex_part = "".join([c * 2 for c in hex_part])  # #RGB -> #RRGGBB
            elif len(hex_part) == 4:
                hex_part = "".join([c * 2 for c in hex_part])  # #RGBA -> #RRGGBBAA

            r = int(hex_part[0:2], 16)
            g = int(hex_part[2:4], 16)
            b = int(hex_part[4:6], 16)

            if len(hex_part) == 8:
                # 包含透明度分量
                original_alpha = int(hex_part[6:8], 16) / 255.0
            else:
                original_alpha = default_alpha

        elif rgba_pattern.match(color_str):
            # 处理 RGB/RGBA
            match = rgba_pattern.match(color_str)
            r = int(match.group(1))
            g = int(match.group(2))
            b = int(match.group(3))
            if match.group(4) is not None:
                original_alpha = float(match.group(4))
            else:
                original_alpha = default_alpha
        else:
            raise ValueError("不支持的格式，请输入 HEX 或 RGBA 颜色字符串")

        # 透明度取反
        new_alpha = 1.0 - original_alpha

        return f"rgba({r}, {g}, {b}, {new_alpha})"

    @classmethod
    def 点(cls, 对象: 买卖点, 命令: 指令):

        message = dict()
        # return message
        message["标识"] = 对象.标识 if hasattr(对象, "标识") else 对象.__class__.__name__

        message["type"] = "shape"
        message["cmd"] = str(命令)
        message["id"] = str(id(对象))
        message["name"] = "arrow_down" if 对象.类型.是卖点 else "arrow_up"
        message["points"] = [{"time": int(对象.买卖点K线.时间戳.timestamp()), "price": 对象.买卖点K线.分型特征值}]

        message["properties"] = {"color": "#CC00FF", "title": 对象.备注, "showLabel": True}
        arrowColor = "#FF2800" if 对象.类型.是卖点 else "#00FF22"
        text = f"{str(对象.偏移)}, {对象.破位值}, {对象.备注}"
        if 对象.失效偏移 > -1:
            arrowColor = 图表配色.灰色
            text = f"{str(对象.偏移)}, {对象.破位值}, {对象.备注}, {str(对象.失效K线.时间戳)}"
        message["options"] = {
            "shape": "arrow_down" if 对象.类型.是卖点 else "arrow_up",
            "text": text,
        }
        message["properties"] = {
            "color": cls.invert_alpha("#CC62FF"),
            "arrowColor": arrowColor,
            "text": text,
            "title": 对象.备注,
            "showLabel": False,
        }

        return message

    @classmethod
    def 线(cls, 对象: Union[虚线, 笔, 线段, 线段特征], 命令: 指令):
        linewidths = {"笔": 1, "线段": 2, "走势": 3, "线段特征": 2}
        message = dict()
        message["命令备注"] = 命令.备注
        message["标识"] = 对象.标识 if hasattr(对象, "标识") else 对象.__class__.__name__

        message["type"] = "shape"
        message["cmd"] = str(命令)
        message["id"] = str(id(对象))
        message["name"] = "trend_line"
        message["points"] = [
            {"time": int(对象.文.时间戳.timestamp()), "price": 对象.文.分型特征值},
            {"time": int(对象.武.时间戳.timestamp()), "price": 对象.武.分型特征值},
        ]
        message["options"] = {"shape": "trend_line", "text": message["标识"]}
        message["properties"] = {
            "bold": True,
            "textcolor": cls.invert_alpha("#f4ff00"),
            "linecolor": getattr(cls, 对象.__class__.__name__, cls.笔),
            "linewidth": linewidths.get(message["标识"], 2),
            "title": f"{message['标识']}-{getattr(对象, '序号', 0)}",
            "showLabel": False,
        }

        if type(对象) is 线段:
            text = f"{message['标识']} {对象.四象} {对象.特征序列状态}"
            if 对象.左 is not None and 对象.中 is not None and 对象.右 is not None:
                结构 = 分型结构.识别(对象.左, 对象.中, 对象.右, 可以逆序包含=True, 忽视顺序包含=True)
                text = f"{message['标识']} {结构} {对象.四象} {对象.特征序列状态}"
                if 对象.确认K线 is not None:
                    text += f", {对象.确认K线.时间戳.strftime('%Y-%m-%d %H:%M:%S')} 特征值: {str(对象.确认K线.分型特征值)}"
            message["properties"]["text"] = text

        if type(对象) is 线段特征:
            message["properties"].update({"linecolor": "#F1C40F" if 对象.方向 is 相对方向.向下 else "#fbc02d", "linewidth": 4, "linestyle": 1})
        return message

    @classmethod
    def 面(cls, 对象: 中枢, 命令: 指令):
        linewidths = {"笔": 1, "线段": 2, "走势": 3}
        message = dict()
        message["标识"] = 对象.标识 if hasattr(对象, "标识") else 对象.__class__.__name__
        message["type"] = "shape"
        message["cmd"] = str(命令)
        message["id"] = str(id(对象))
        message["name"] = "rectangle"
        message["properties"] = {}

        if 命令.指令 == 指令.增 or 命令.指令 == 指令.改:
            # 武_时间戳 = int(对象[-1].文.中.时间戳.timestamp()) if len(对象) <= 3 else int(对象[-1].武.中.时间戳.timestamp())
            武_时间戳 = int(对象.第三买卖线.武.中.时间戳.timestamp()) if 对象.第三买卖线 else int(对象[-1].武.中.时间戳.timestamp())
            points = [
                {"time": int(对象.文.时间戳.timestamp()), "price": 对象.中高},
                {
                    "time": 武_时间戳,
                    "price": 对象.中低,
                },
            ]
            text = f"{对象.标识} 周期: , 数量: {len(对象)} "
            if 对象.第三买卖线:
                text += f"第三卖点值: {对象.第三买卖线.武.分型特征值}, "
            text += 对象.当前信息()
            message["properties"] = {
                "backgroundColor": "rgba(242, 54, 69, 0.2)" if 对象.方向 is 相对方向.向下 else "rgba(76, 175, 80, 0.2)",  # 上下上 为 红色，反之为 绿色
                "color": getattr(cls, 对象[0].__class__.__name__, cls.笔),
                "linewidth": linewidths.get(对象[0].__class__.__name__, 2),
                "title": f"{对象.标识}-{对象.序号}",
                "text": text,
                "textColor": cls.invert_alpha("rgba(156, 39, 176, 1)"),
                "horzLabelsAlign": "left",
                "vertLabelsAlign": "bottom",
                "showLabel": False,
            }

        elif 命令.指令 == 指令.删:
            points = []
        else:
            points = []

        message["points"] = points
        message["options"] = {"shape": "rectangle", "text": 对象.标识}

        return message


图表配色 = _图表配色()


class 观察者:
    # thread: Any = None
    # queue: Any = asyncio.Queue()
    当前事件循环: Any = None if __name__ == "__main__" else asyncio.get_event_loop()
    延迟时间: float = 0.01

    def __init__(self, 符号: str, 周期: int, 数据通道: Optional[WebSocket] = None):
        self.符号: str = 符号
        self.周期: int = 周期
        self.当前K线: Optional[K线] = None
        self.普通K线序列: List[K线] = []
        self.缠论K线序列: List[K线] = []
        self.分型序列: List[分型] = []
        self.笔序列: List[笔] = []
        self.笔_中枢序列: List[中枢] = []
        self.线段序列: List[线段] = []
        self.扩展线段序列: List[线段] = []
        self.中枢序列: List[中枢] = []
        self.扩展中枢序列: List[中枢] = []
        self.走势序列: List[走势] = []
        self.走势中枢序列: List[中枢] = []
        self.上级缠K序列: List[K线] = []
        self.数据通道: Optional[Any] = 数据通道  # WebSocket
        self.缓存: Dict[str, Any] = dict()
        self.配置: 缠论配置 = 缠论配置()
        self.段内中枢字典 = dict()

        self.买卖点序列 = []

    @final
    def 增加原始K线(self, 普K: K线):
        if len(self.笔序列) > 14:
            pass  # raise RuntimeError("手动终止")
        if 普K.时间戳 > to_datetime("2024-02-24 16:00:33"):
            pass  # return  # raise RuntimeError("手动终止")

        if self.当前K线 is not None:
            if self.当前K线.时间戳 is 普K.时间戳:
                普K.序号 = self.当前K线.序号
            else:
                普K.序号 = self.当前K线.序号 + 1
        self.当前K线 = 普K
        if self.配置.基础分析保存原始K线:
            if self.普通K线序列 and self.普通K线序列[-1].时间戳 is 普K.时间戳:
                self.普通K线序列[-1] = 普K
            else:
                self.普通K线序列.append(普K)

        状态, 当前分型 = K线.分析(普K, self.缠论K线序列, self.配置)

        # self.报信(self.缠论K线序列[-1], 指令.添加("NewBar"))
        self.报信(普K, 指令.添加("NewBar"))

        self.中枢序列 and self.中枢序列[-1].处理K线(self.缠论K线序列[-1])

        if self.数据通道 is not None and self.配置.图表展示:
            time.sleep(self.延迟时间)

        if not self.配置.分析_笔:
            return

        if not self.分型序列:
            笔.分析(当前分型, self.分型序列, self.笔序列, self.缠论K线序列, "分析", 0, self.配置, self)
            return

        之前分型 = self.分型序列[-1]
        if 当前分型.中.时间戳 < 之前分型.中.时间戳:
            当前分型 = 分型.从缠K序列中获取虚假分型(self.缠论K线序列)
        笔.分析(当前分型, self.分型序列, self.笔序列, self.缠论K线序列, "分析", 0, self.配置, self)
        走势.滑动分析(self.缠论K线序列[-1], 3, self.线段序列, self.买卖点序列, self)

    def 报信(self, 对象: Any, 命令: 指令, 行号: int = 0) -> None:
        if self.数据通道 and not self.配置.图表展示:
            return
        message = dict()
        message["标识"] = 对象.标识 if hasattr(对象, "标识") else 对象.__class__.__name__

        if type(对象) is K线:
            if not self.配置.推送K线:
                return
            message["type"] = "realtime"
            message["timestamp"] = str(对象.时间戳)
            message["open"] = 对象.开盘价
            message["high"] = 对象.最高价
            message["low"] = 对象.最低价
            message["close"] = 对象.收盘价
            message["volume"] = 对象.成交量

        if type(对象) is 买卖点:
            message.update(图表配色.点(对象, 命令))
        if type(对象) is 笔:
            if not self.配置.推送笔:
                return
            message.update(图表配色.线(对象, 命令))

        if type(对象) is 线段 or type(对象) is 走势 or type(对象) is 线段特征:
            if not self.配置.推送线段:
                return
            message.update(图表配色.线(对象, 命令))

        if type(对象) is 中枢:
            message.update(图表配色.面(对象, 命令))

        if self.数据通道 is not None and self.配置.图表展示 and self.数据通道.client_state.value == 1:
            asyncio.set_event_loop(self.当前事件循环)
            asyncio.ensure_future(self.数据通道.send_text(json.dumps(message)))
        return

    @classmethod
    def 读取数据文件(cls, 文件路径: str) -> Self:
        # btcusd-300-1631772074-1632222374.nb
        name = Path(文件路径).name.split(".")[0]
        符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
        实例 = cls(符号=符号, 周期=int(周期), 数据通道=None)
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size])
                实例.增加原始K线(k线)

        return 实例


class Bitstamp(观察者):
    def __init__(self, 符号: str, 周期: int, 数据通道: WebSocket):
        super().__init__(符号=符号, 周期=周期, 数据通道=数据通道)

    def init(self, size):
        left_date_timestamp = int(datetime.now().timestamp() * 1000)
        left = int(left_date_timestamp / 1000) - self.周期 * size
        if left < 0:
            raise IndexError
        _next = left
        while 1:
            data = self.ohlc(self.符号, self.周期, _next, _next := _next + self.周期 * 1000)
            if not data.get("data"):
                print(data)
                raise ValueError("")
            for bar in data["data"]["ohlc"]:
                K = K线.创建普K(
                    int2dt(bar["timestamp"]),
                    float(bar["open"]),
                    float(bar["high"]),
                    float(bar["low"]),
                    float(bar["close"]),
                    float(bar["volume"]),
                    0,
                    self.周期,
                )
                self.增加原始K线(K)

            # start = int(data["data"]["ohlc"][0]["timestamp"])
            end = int(data["data"]["ohlc"][-1]["timestamp"])

            _next = end
            if len(data["data"]["ohlc"]) < 100:
                break
        折线 = [元素.文.分型特征值 for 元素 in self.笔序列]
        折线.append(self.笔序列[-1].武.分型特征值)
        print(折线)

    @staticmethod
    def 获取K线数据(数量: int, 符号: str, 周期: int, obj):
        left_date_timestamp: int = int(datetime.now().timestamp() * 1000)
        left = int(left_date_timestamp / 1000) - 周期 * 数量
        if left < 0:
            raise IndexError
        _next = left
        while 1:
            data = Bitstamp.ohlc(符号, 周期, _next, _next := _next + 周期 * 1000)
            if not data.get("data"):
                print(data)
                raise ValueError
            for bar in data["data"]["ohlc"]:
                K = K线.创建普K(
                    int2dt(bar["timestamp"]),
                    float(bar["open"]),
                    float(bar["high"]),
                    float(bar["low"]),
                    float(bar["close"]),
                    float(bar["volume"]),
                    0,
                    周期,
                )
                obj.投喂K线(K)

            # start = int(data["data"]["ohlc"][0]["timestamp"])
            end = int(data["data"]["ohlc"][-1]["timestamp"])

            _next = end
            if len(data["data"]["ohlc"]) < 100:
                break

    @staticmethod
    def ohlc(pair: str, step: int, start: int, end: int, length: int = 1000) -> Dict:
        proxies = {
            "http": "http://127.0.0.1:10808",
            "https": "http://127.0.0.1:10808",
        }
        s = requests.Session()

        s.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
            # "content-type": "application/json",
        }
        url = f"https://www.bitstamp.net/api/v2/ohlc/{pair}/?step={step}&limit={length}&start={start}&end={end}"
        resp = s.get(url, timeout=30, proxies=proxies)
        js = resp.json()
        # print(json)
        return js


def main_bitstamp(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Bitstamp(symbol, int(freq), ws)
        bitstamp.init(int(limit))
        return bitstamp

    return func


app = FastAPI()
# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/charting_library",
    StaticFiles(directory="charting_library"),
    name="charting_library",
)
templates = Jinja2Templates(directory="templates")

random_lock = asyncio.Lock()  # 保证并发安全
PERIOD = 10  # 种子更新周期（单位：秒），可自定义
current_seed = None  # 记录当前生效的种子，方便API返回


async def periodic_seed_task():
    """后台定时任务：每隔PERIOD秒，随机生成一个种子并设置"""
    global current_seed
    while True:  # 无限循环，持续执行定时任务
        async with random_lock:
            # 生成随机种子（用1-100000的随机整数作为种子，范围可自定义）
            new_seed = os.urandom(8)
            # 设置种子
            seed(new_seed)  # FIXME random.seed
            # 更新当前种子记录
            current_seed = new_seed
            print(f"[定时任务] 已更新种子：{current_seed}，下次更新将在{PERIOD}秒后")

        # 等待周期时间（释放CPU，不阻塞其他协程）
        await asyncio.sleep(PERIOD)


'''
@app.on_event("startup")
async def startup_event():
    """服务启动时触发：创建并启动周期性种子任务"""
    # 用create_task启动后台任务，避免阻塞服务启动
    asyncio.create_task(periodic_seed_task())
    print(f"服务启动成功！种子将每{PERIOD}秒自动随机更新")
'''


# ============ Python代码执行环境 ============
class PythonExecutionEnvironment:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.globals_dict = {}
        self.execution_history = []
        self.last_execution_time = None
        self.chart_observer = None
        self.output_buffer = []  # 存储输出
        self._init_environment()

    def set_chart_observer(self, observer):
        self.chart_observer = observer
        self.globals_dict["观察员"] = observer
        # self._inject_chart_data()

    def _init_environment(self):
        import math
        import random
        from datetime import datetime, date, timedelta
        import statistics
        import json as json_module

        # 创建原始print的引用
        self._original_print = builtins.print

        self.globals_dict = {
            "__builtins__": {name: getattr(builtins, name) for name in dir(builtins) if not name.startswith("_") or name in ["__import__"]},
            "观察员": self.chart_observer,
            "中枢": 中枢,
            "print": self._capturing_print,
            "math": math,
            "random": random,
            "statistics": statistics,
            "datetime": datetime,
            "date": date,
            "timedelta": timedelta,
            "time": __import__("time"),
            "json": json_module,
            "背驰分析": 背驰分析,
            "__user_id__": self.user_id,
            "__env__": self,
            "help": self._help_function,
            "clear": self._clear_function,
            "get_history": self._get_history_function,
            "get_variables": self._get_variables_function,
            "current_price": 100.0,
            "price_history": [],
            "indicators": {},
        }

        # 清除输出缓冲区
        self.output_buffer.clear()

    def _capturing_print(self, *args, **kwargs):
        output = io.StringIO()
        kwargs.setdefault("file", output)
        kwargs.setdefault("end", "\n")
        self._original_print(*args, **kwargs)
        printed = output.getvalue()
        # 存储到缓冲区
        self.output_buffer.append(printed)
        self._original_print(f"[用户{self.user_id}]", *args, **kwargs)
        return printed

    def _help_function(self):
        help_text = """
        === Python执行环境帮助 ===

        可用函数:
        - help(): 显示此帮助
        - clear(): 清除环境变量
        - get_history(): 获取执行历史
        - get_variables(): 查看所有变量

        可用变量:
        - bi_sequence: 笔序列数据
        - duan_sequence: 线段序列数据
        - fenxing_sequence: 分型序列数据
        - bi_count: 笔数量
        - duan_count: 线段数量
        - fenxing_count: 分型数量
        - symbol: 交易对
        - frequency: 时间周期
        - last_update: 最后更新时间
        - is_running: 分析器运行状态
        - current_price: 当前价格
        - price_history: 价格历史

        统计指标:
        - bi_statistics: 笔统计
        - duan_statistics: 线段统计
        - fenxing_statistics: 分型统计
        """
        return help_text

    def _clear_function(self):
        self._init_environment()
        self.output_buffer.clear()
        return "环境已清空"

    def _get_history_function(self):
        return self.execution_history[-10:] if self.execution_history else []

    def _get_variables_function(self):
        variables = []
        for key, value in self.globals_dict.items():
            if not key.startswith("_"):
                variables.append(
                    {
                        "name": key,
                        "type": type(value).__name__,
                        "value": str(value)[:50] + "..." if len(str(value)) > 50 else str(value),
                    }
                )
        return variables

    def execute_code(self, code: str) -> Dict[str, Any]:
        """执行Python代码并正确捕获输出"""
        # 清除之前的输出
        self.output_buffer.clear()

        # 创建输出捕获器
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # 保存原始标准输出
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            # 重定向标准输出到我们的捕获器
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # 临时重定向builtins.print到我们的捕获函数
            original_builtins_print = builtins.print
            builtins.print = self._capturing_print

            # 准备执行环境
            exec_globals = self.globals_dict.copy()

            # 执行代码
            try:
                # 尝试exec执行
                exec(code, exec_globals)

                # 检查是否有表达式结果
                output = self._get_expression_result(code, exec_globals)

                if output:
                    # 将表达式结果添加到输出
                    result_output = f"\n表达式结果: {output}"
                    print(result_output)  # 这会触发我们的_capturing_print

            except SyntaxError:
                # 如果是SyntaxError，可能是单个表达式，尝试eval
                try:
                    result = eval(code, exec_globals)
                    output = self._format_result(result)
                    if output:
                        print(f"\n表达式结果: {output}")  # 这会触发我们的_capturing_print
                except Exception as e:
                    # 真正的语法错误
                    raise e

            # 获取所有输出
            captured_stdout = stdout_capture.getvalue()
            captured_stderr = stderr_capture.getvalue()
            captured_print = "".join(self.output_buffer)

            # 合并所有输出
            all_output = ""
            if captured_print:
                all_output += captured_print
            if captured_stdout:
                all_output += captured_stdout
            if captured_stderr:
                all_output += captured_stderr

            # 记录执行历史
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "code": code[:100] + "..." if len(code) > 100 else code,
                "success": True,
                "output": all_output,
                "output_length": len(all_output),
            }
            self.execution_history.append(execution_record)
            self.last_execution_time = datetime.now()

            return {
                "success": True,
                "output": all_output,
                "error": None,
                "stdout": captured_stdout,
                "stderr": captured_stderr,
                "print_output": captured_print,
                "execution_time": self.last_execution_time.isoformat(),
                "output_buffer": self.output_buffer.copy(),
            }

        except Exception as e:
            # 获取错误信息
            error_output = f"错误类型: {type(e).__name__}\n错误信息: {str(e)}\n\n堆栈跟踪:\n{traceback.format_exc()}"

            # 获取已捕获的输出
            captured_stdout = stdout_capture.getvalue()
            captured_stderr = stderr_capture.getvalue()
            captured_print = "".join(self.output_buffer)

            # 合并输出
            all_output = ""
            if captured_print:
                all_output += captured_print
            if captured_stdout:
                all_output += captured_stdout
            if captured_stderr:
                all_output += captured_stderr
            if error_output:
                all_output += f"\n\n{error_output}"

            # 记录错误历史
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "code": code[:100] + "..." if len(code) > 100 else code,
                "success": False,
                "error": str(e),
                "output": all_output,
            }
            self.execution_history.append(execution_record)

            return {
                "success": False,
                "output": all_output,
                "error": {"type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()},
                "stdout": captured_stdout,
                "stderr": captured_stderr,
                "print_output": captured_print,
                "execution_time": datetime.now().isoformat(),
            }

        finally:
            # 恢复原始标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # 恢复原始builtins.print
            builtins.print = original_builtins_print

    def _get_expression_result(self, code: str, globals_dict: Dict) -> str:
        """获取表达式的结果"""
        try:
            # 尝试解析最后一行是否为表达式
            lines = code.strip().split("\n")
            if lines:
                last_line = lines[-1].strip()
                # 检查是否是表达式（不是语句）
                if not last_line.startswith((" ", "\t", "#", "import ", "from ", "def ", "class ", "if ", "for ", "while ", "try ", "with ")) and not last_line.endswith(":") and last_line:
                    try:
                        # 尝试评估最后一行
                        result = eval(last_line, globals_dict)
                        return self._format_result(result)
                    except:
                        pass
        except:
            pass
        return ""

    def _format_result(self, result) -> str:
        """格式化结果用于显示"""
        if result is None:
            return ""
        try:
            return repr(result)
        except:
            try:
                return str(result)
            except:
                return f"<无法表示的对象: {type(result)}>"


# ============ 连接管理器 ============
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.python_environments = {}
        self.chart_observers = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

        if user_id not in self.python_environments:
            self.python_environments[user_id] = PythonExecutionEnvironment(user_id)

        print(f"[连接] 用户 {user_id} 已连接")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.python_environments:
            del self.python_environments[user_id]
        if user_id in self.chart_observers:
            del self.chart_observers[user_id]

        print(f"[断开] 用户 {user_id} 已断开")

    async def send_message(self, user_id: str, message: Dict[str, Any]):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"[错误] 发送消息到 {user_id} 失败: {e}")

    def set_chart_observer(self, user_id: str, observer):
        self.chart_observers[user_id] = observer

        if user_id in self.python_environments:
            self.python_environments[user_id].set_chart_observer(observer)

    def get_chart_observer(self, user_id: str):
        return self.chart_observers.get(user_id)

    def get_python_environment(self, user_id: str):
        if user_id not in self.python_environments:
            self.python_environments[user_id] = PythonExecutionEnvironment(user_id)
        return self.python_environments[user_id]


# 全局连接管理器
connection_manager = ConnectionManager()

# 全局线程变量
主线程 = None


# ============ WebSocket端点 ============
@app.websocket("/ws/{user_id}")
async def unified_websocket_endpoint(websocket: WebSocket, user_id: str):
    """统一的WebSocket端点，处理所有类型的消息"""
    await connection_manager.connect(user_id, websocket)

    try:
        # 发送欢迎消息
        await connection_manager.send_message(
            user_id,
            {
                "type": "connected",
                "message": "✅ 已连接到服务器",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "endpoint": "unified",
            },
        )

        while True:
            data = await websocket.receive_text()
            消息字典 = json.loads(data)

            # 获取消息类型
            消息类型 = 消息字典.get("type", "")
            模块 = 消息字典.get("module", "chart")  # 默认是chart模块

            print(f"[消息] 用户 {user_id} | 模块: {模块} | 类型: {消息类型}")

            if 模块 == "python":
                # Python执行相关消息
                await handle_python_message(user_id, 消息字典)
            else:
                # 图表相关消息
                await handle_chart_message(user_id, 消息字典, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
    except Exception as e:
        traceback.print_exc()
        print(f"[错误] WebSocket处理异常: {e}")
        await connection_manager.send_message(user_id, {"type": "error", "message": f"服务器错误: {str(e)}", "timestamp": datetime.now().isoformat()})
        connection_manager.disconnect(user_id)


async def handle_chart_message(user_id: str, 消息字典: Dict, websocket: WebSocket):
    """处理图表消息"""
    print(消息字典)
    消息类型 = 消息字典.get("type", "")

    if 消息类型 == "ready":
        # 初始化分析器
        symbol = 消息字典.get("symbol", "btcusd")
        freq = 消息字典.get("freq", 300)
        limit = 消息字典.get("limit", 500)
        generator = 消息字典.get("generator", "True")

        # 停止现有线程
        global 主线程
        if 主线程 is not None:
            主线程.join(1)
            time.sleep(1)
            主线程 = None

        # 创建新的分析器
        if generator == "True":
            analyzer_func = 随机生成(symbol=symbol, freq=freq, limit=limit, ws=websocket)
        elif generator == "3":
            analyzer_func = main_bitstamp2(symbol=symbol, freq=freq, limit=limit, ws=websocket)
        elif generator == "bi":
            analyzer_func = main_bi(symbol=symbol, freq=freq, limit=limit, ws=websocket, 顶底序列=消息字典.get("points"))
        else:
            analyzer_func = main_bitstamp(symbol=symbol, freq=freq, limit=limit, ws=websocket)

        def thread_func():
            try:
                分析_ = analyzer_func()
                connection_manager.set_chart_observer(user_id, 分析_)
                print(f"[分析器] 用户 {user_id} 的分析器已启动")
            except Exception as e:
                traceback.print_exc()
                print(f"[分析器错误] {e}")

        主线程 = Thread(target=thread_func)
        主线程.daemon = True
        主线程.start()

        await connection_manager.send_message(
            user_id,
            {
                "type": "ready_ack",
                "message": "图表分析器已启动",
                "symbol": symbol,
                "freq": freq,
                "timestamp": datetime.now().isoformat(),
            },
        )

    elif 消息类型 == "query_by_index":
        分析 = connection_manager.get_chart_observer(user_id)
        if 分析:
            data_type = 消息字典.get("index").split("-")[0]
            序号 = int(消息字典.get("index").split("-")[-1])

            print(data_type, 序号)

            try:
                待发送消息 = {}
                if "笔" == data_type:
                    if hasattr(分析, "笔序列") and 序号 < len(分析.笔序列):
                        筆: 笔 = 分析.笔序列[序号]
                        待发送消息.update(
                            {
                                "index": 筆.序号,
                                "start_time": 筆.文.时间戳.timestamp(),
                                "end_time": 筆.武.时间戳.timestamp(),
                                "start_price": 筆.文.分型特征值,
                                "end_price": 筆.武.分型特征值,
                                "direction": str(筆.方向),
                                "angle": 筆.计算角度(),
                                "speed": 筆.计算速率(),
                                "measure": 筆.计算测度(),
                                "macd": 筆.计算MACD(),
                            }
                        )
                    else:
                        raise IndexError(f"笔索引 {序号} 超出范围")

                elif "线段" == data_type:
                    if hasattr(分析, "线段序列") and 序号 < len(分析.线段序列):
                        段: 线段 = 分析.线段序列[序号]
                        if 段._特征序列_显示:
                            段.图表移除特征序列()
                        else:
                            段.图表显示特征序列()
                        待发送消息.update(
                            {
                                "index": 段.序号,
                                "start_time": 段.文.时间戳.timestamp(),
                                "end_time": 段.武.时间戳.timestamp(),
                                "start_price": 段.文.分型特征值,
                                "end_price": 段.武.分型特征值,
                                "direction": str(段.方向),
                                "angle": 段.计算角度(),
                                "speed": 段.计算速率(),
                                "measure": 段.计算测度(),
                                "macd": 段.计算MACD(),
                            }
                        )

                elif "中枢<线段>" == data_type:
                    if hasattr(分析, "中枢序列") and 序号 < len(分析.中枢序列):
                        当前中枢: 中枢 = 分析.中枢序列[序号]
                        待发送消息.update(当前中枢.识别盘背(分析.当前K线, 分析))
                    else:
                        raise IndexError(f"中枢索引 {序号} 超出范围")

                elif "中枢<笔>" == data_type:
                    if hasattr(分析, "笔_中枢序列") and 序号 < len(分析.笔_中枢序列):
                        当前中枢: 中枢 = 分析.笔_中枢序列[序号]
                        待发送消息.update(当前中枢.识别盘背(分析.当前K线, 分析))
                    else:
                        raise IndexError(f"笔_中枢索引 {序号} 超出范围")
                elif "段内" == data_type[:2] and "中枢" in data_type:
                    i = data_type.index(">")
                    段序号 = int(data_type[3:i])
                    段: 线段 = 分析.线段序列[段序号]
                    待发送消息.update(段.实_中枢序列[序号].识别盘背(分析.当前K线, 分析))
                else:
                    raise ValueError(f"不支持的数据类型: {data_type}")

                await connection_manager.send_message(user_id, {"type": "query_result", "success": True, "data_type": data_type, "data": 待发送消息})

            except IndexError:
                await connection_manager.send_message(user_id, {"type": "query_result", "success": False, "message": f"索引 {序号} 超出范围"})
            except Exception as e:
                await connection_manager.send_message(user_id, {"type": "query_result", "success": False, "message": str(e)})
        else:
            print(f"[query_by_index] 用户 {user_id} 没有分析器！")

    elif 消息类型 == "save_path":
        分析 = connection_manager.get_chart_observer(user_id)
        if 分析:
            data = 消息字典.get("data")
            print(f"[保存路径] 用户 {user_id}: {data}")

            await connection_manager.send_message(
                user_id,
                {
                    "type": "path_saved",
                    "message": "路径已保存",
                    "index": 消息字典.get("index"),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    elif 消息类型 == "ping":
        await connection_manager.send_message(user_id, {"type": "pong", "timestamp": datetime.now().isoformat()})

    else:
        await connection_manager.send_message(user_id, {"type": "error", "message": f"未知的图表消息类型: {消息类型}", "timestamp": datetime.now().isoformat()})


async def handle_python_message(user_id: str, 消息字典: Dict):
    """处理Python执行消息"""
    command = 消息字典.get("command", "")

    if command == "execute":
        code = 消息字典.get("code", "").strip()

        if not code:
            await connection_manager.send_message(user_id, {"type": "execution_result", "success": False, "message": "❌ 代码不能为空", "module": "python"})
            return

        python_env = connection_manager.get_python_environment(user_id)
        result = python_env.execute_code(code)

        response = {
            "type": "execution_result",
            "success": result["success"],
            "timestamp": datetime.now().isoformat(),
            "execution_time": result.get("execution_time"),
            "module": "python",
        }

        if result["success"]:
            response.update({"message": "✅ 执行成功", "output": result.get("output", ""), "has_output": bool(result.get("output"))})
        else:
            response.update(
                {
                    "message": f"❌ 执行失败: {result.get('error', {}).get('message', '未知错误')}",
                    "error": result.get("error"),
                    "output": result.get("output", ""),
                }
            )

        await connection_manager.send_message(user_id, response)

    elif command == "get_environment":
        python_env = connection_manager.get_python_environment(user_id)
        variables = python_env._get_variables_function()
        history = python_env._get_history_function()

        await connection_manager.send_message(
            user_id,
            {
                "type": "environment_info",
                "variables": variables,
                "history": history,
                "user_id": user_id,
                "chart_linked": python_env.chart_observer is not None,
                "execution_count": len(python_env.execution_history),
                "chart_data_available": {
                    "bi_count": python_env.globals_dict.get("bi_count", 0),
                    "duan_count": python_env.globals_dict.get("duan_count", 0),
                    "fenxing_count": python_env.globals_dict.get("fenxing_count", 0),
                },
                "module": "python",
            },
        )

    elif command == "reset":
        python_env = connection_manager.get_python_environment(user_id)
        python_env._clear_function()

        await connection_manager.send_message(
            user_id,
            {
                "type": "environment_reset",
                "message": "🔄 Python执行环境已重置",
                "timestamp": datetime.now().isoformat(),
                "module": "python",
            },
        )

    elif command == "help":
        python_env = connection_manager.get_python_environment(user_id)
        help_text = python_env._help_function()

        await connection_manager.send_message(user_id, {"type": "help_response", "help": help_text, "timestamp": datetime.now().isoformat(), "module": "python"})

    elif command == "get_chart_data":
        python_env = connection_manager.get_python_environment(user_id)
        chart_data = python_env._get_chart_data_function()

        await connection_manager.send_message(user_id, {"type": "chart_data", "data": chart_data, "timestamp": datetime.now().isoformat(), "module": "python"})

    elif command == "ping":
        await connection_manager.send_message(user_id, {"type": "pong", "timestamp": datetime.now().isoformat(), "module": "python"})

    else:
        await connection_manager.send_message(
            user_id,
            {
                "type": "error",
                "message": f"❌ 未知命令: {command}",
                "timestamp": datetime.now().isoformat(),
                "module": "python",
            },
        )


# ============ HTTP端点 ============
@app.get("/")
async def main_page(
    request: Request,
    nol: str = "network",
    exchange: str = "bitstamp",
    symbol: str = "btcusd",
    step: int = 300,
    limit: int = 500,
    generator: str = "True",
):
    """主页面"""
    resolutions = {
        60: "1",
        180: "3",
        300: "5",
        900: "15",
        1800: "30",
        2400: "40",
        3600: "1H",
        7200: "2H",
        14400: "4H",
        21600: "6H",
        43200: "12H",
        86400: "1D",
        259200: "3D",
        604800: "1W",
    }

    if step not in resolutions:
        return {"error": "不支持的时间周期", "支持的周期": list(resolutions.keys())}

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "exchange": exchange,
            "symbol": symbol,
            "interval": resolutions.get(step),
            "limit": str(limit),
            "step": str(step),
            "generator": generator,
        },
    )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(connection_manager.active_connections),
        "python_environments": len(connection_manager.python_environments),
        "chart_observers": len(connection_manager.chart_observers),
    }
