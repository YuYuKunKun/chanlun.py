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
import io
import json
import math
import struct
import re
import ast
import signal
import sys
import time
import queue
import platform
import traceback
import threading
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from random import random
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
    SupportsIndex,
)
import importlib.metadata

import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from termcolor import colored

import backtrader as bt


def 获取模块版本():
    versions = {}

    # 2.
    try:
        versions["fastapi"] = importlib.metadata.version("fastapi")
    except importlib.metadata.PackageNotFoundError:
        pass
    try:
        versions["requests"] = importlib.metadata.version("requests")
    except importlib.metadata.PackageNotFoundError:
        pass

    # 3. 回测框架（你在用 backtrader 或类似）
    try:
        versions["backtrader"] = importlib.metadata.version("backtrader")
    except importlib.metadata.PackageNotFoundError:
        pass

    # 4. 配置/模型（你这个缠论配置用了 pydantic）
    try:
        versions["pydantic"] = importlib.metadata.version("pydantic")
    except importlib.metadata.PackageNotFoundError:
        pass

    return versions


def 收集异常信息(exception: Exception, 上下文: dict = None):
    """
    万能异常收集函数
    :param exception: 捕获到的异常
    :param 上下文: 自定义环境数据（当前K线、品种、配置等）
    :return: 完整错误报告
    """
    # 1. 基础信息
    exc_type, exc_obj, exc_tb = sys.exc_info()
    文件名 = exc_tb.tb_frame.f_code.co_filename
    行号 = exc_tb.tb_lineno
    函数名 = exc_tb.tb_frame.f_code.co_name

    # 2. 完整堆栈
    堆栈 = "".join(traceback.format_exception(exc_type, exc_obj, exc_tb))

    # 3. 代码片段
    代码行 = open(文件名, "r", encoding="utf-8").readlines()[行号 - 1].strip()

    # 4. 系统信息
    系统信息 = {
        "时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Python版本": sys.version,
        "系统": platform.platform(),
    }

    # 5. 组装最终报告
    错误报告 = f"""
==================== 程序异常 ====================
异常类型: {exc_type.__name__}
异常信息: {str(exception)}
文件: {文件名}
行号: {行号}
函数: {函数名}
代码行: {代码行}

-------------------- 堆栈信息 --------------------
{堆栈}

-------------------- 系统信息 --------------------
{系统信息}
-------------------- 模块信息 --------------------
{获取模块版本()}
-------------------- 上下文信息 --------------------
{上下文 or "无"}
==================================================
"""
    return 错误报告


def Nil(*args, **kwargs):
    return None


def 转化为时间戳(ts: Union[str, datetime, int, float]) -> datetime:
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


def 转化为时间戳_数字(ts: Union[str, datetime, int, float]) -> int:
    """
    将不同类型的时间戳转换为datetime对象（统一比较标准）
    支持：datetime对象、字符串（"%Y-%m-%d %H:%M:%S"）、数值型时间戳（秒级）
    可根据实际需求扩展时间格式（如毫秒级、仅日期等）
    """
    if isinstance(ts, datetime):
        return int(ts.timestamp())
    elif isinstance(ts, str):
        # 自定义时间字符串格式，按需修改（如"%Y-%m-%d"）
        return int(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp())
    elif isinstance(ts, (int, float)):
        # 若为毫秒级时间戳，需除以1000：return datetime.fromtimestamp(ts / 1000)
        return int(ts)
    else:
        raise TypeError(f"不支持的时间戳类型: {type(ts)}")


@final
class 缠论配置(BaseModel):
    标识: str = "bar"
    缠K合并替换: bool = False  # False: 在原缠K上合并, True: 产出新缠K

    笔内元素数量: int = 5  # 成BI最低长度

    笔内相同终点取舍: bool = False  # 一笔终点存在多个终点时 True: last, False: first
    笔内起始分型包含整笔: bool = False  # True: 一笔起始分型高低包含整支笔对象则不成笔, False: 只判断分型中间数据是否包含
    笔内原始K线包含整笔: bool = False  # 在非 [笔内起始分型包含整笔] 时判断原始K线包含整笔的情况

    笔次级成笔: bool = False
    笔弱化: bool = False
    笔弱化_原始数量: int = 3

    线段_非缺口下穿刺: bool = False  # True: 非缺口状态下[小阳, 少阴]时，存在贯穿伤与之后紧邻的三个元素有方向相同的线段时回退， 此举在当下是否有任何意义呢？
    线段_特征序列忽视老阴老阳: bool = False  # True 不用严格的特征序列包含，也就是忽视缺口全以无缺口对待

    线段内部中枢图显: bool = True
    扩展线段_当下分析: bool = False  # 以当下来看的分析规则，否则以事后来看

    分析笔: bool = True  # 是否计算BI
    分析线段: bool = True  # 是否计算XD
    分析扩展线段: bool = True  # 是否计算XD
    分析笔中枢: bool = True  # 是否计算BI中枢
    分析线段中枢: bool = True  # 是否计算XD中枢

    计算指标: bool = True
    指标计算方式: str = "收"  # (开, 高, 低, 收, 高低均值, 高低收均值, 开高低收均值), 默认 收盘价
    平滑异同移动平均线_快线周期: int = 13
    平滑异同移动平均线_慢线周期: int = 31
    平滑异同移动平均线_信号周期: int = 11

    相对强弱指数_周期: int = 13
    相对强弱指数_移动平均线周期: int = 13
    相对强弱指数_超买阈值: float = 75.0
    相对强弱指数_超卖阈值: float = 25.0

    随机指标_RSV周期: int = 13
    随机指标_K值平滑周期: int = 5
    随机指标_D值平滑周期: int = 5
    随机指标_超买阈值: float = 80.0
    随机指标_超卖阈值: float = 20.0

    图表展示: bool = True
    推送K线: bool = True
    推送笔: bool = True
    推送线段: bool = True
    推送中枢: bool = True

    图表展示_笔: bool = True
    图表展示_线段: bool = True
    图表展示_扩展线段: bool = True
    图表展示_扩展线段_线段: bool = True
    图表展示_线段_线段: bool = True

    图表展示_中枢_笔: bool = True
    图表展示_中枢_线段: bool = True
    图表展示_中枢_扩展线段: bool = True
    图表展示_中枢_扩展线段_线段: bool = True
    图表展示_中枢_线段_线段: bool = True
    图表展示_中枢_线段内部: bool = True

    买卖点偏移: int = 1  # 最大偏移
    买卖点激进识别: bool = False  # 激进模式下将不考虑分型的完整性
    买卖点与MACD柱强相关: bool = False  # True: 卖点需正值 买点需负值
    买卖点错过误差值: float = 0.01  # 距离买卖点值上下之内

    加载文件路径: str = "./templates/last.nb"

    @model_validator(mode="before")
    def 兼容旧版本配置(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动兼容：
        1. 旧版本少字段 → 使用默认值
        2. 新版本多字段 → 自动忽略多余字段
        3. 字段改名/删除 → 不报错
        """
        return values

    @field_validator("*", mode="wrap")
    def bool_parse_fallback_default(cls, value, handler, info):
        field = cls.model_fields.get(info.field_name)
        if not field:
            return handler(value)
        允许值 = {
            "指标计算方式": ["开", "高", "低", "收", "高低均值", "高低收均值", "开高低收均值"],
        }
        # 字段类型 & 默认值
        type_ = field.annotation
        default = field.default
        fname = info.field_name

        try:
            # --- 1. 处理 bool：使用内置 bool_parsing ---
            if type_ is bool:
                return handler(value)

            # --- 2. 处理 int：使用内置 int_parsing ---
            elif type_ is int:
                return handler(value)

            # --- 3. 处理指定 str：必须在允许列表内 ---
            elif fname in 允许值:
                result = handler(value)
                if result not in 允许值[fname]:
                    raise ValueError(f"值不在允许范围内: {result}")
                return result

            # 其他类型不处理
            else:
                return handler(value)

        # 验证失败 → 统一用默认值
        except ValidationError as e:
            if "bool_parsing" in str(e) or "int_parsing" in str(e):
                print(f"[{fname}] = {value} 解析失败，使用默认值：{default}")
                return default
            raise

        # 字符串不在允许列表 → 用默认值
        except ValueError as e:
            print(f"[{fname}] = {value} {str(e)}，使用默认值：{default}")
            return default

    def to_dict(self) -> dict:
        """对象 → 字典"""
        return self.model_dump()

    def to_json(self) -> str:
        """对象 → JSON字符串"""
        return self.model_dump_json(ensure_ascii=False, indent=2)

    def 保存配置(self, path="缠论配置.json"):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @staticmethod
    def 加载配置(path="缠论配置.json") -> "缠论配置":
        with open(path, "r", encoding="utf-8") as f:
            return 缠论配置.from_json(f.read())

    @classmethod
    def from_dict(cls, data: dict) -> "缠论配置":
        """字典 → 对象（自动兼容缺失/多余字段）"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "缠论配置":
        """JSON字符串 → 对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def 不推送(cls):
        return cls(
            线段内部中枢图显=False,
            图表展示=False,
            推送K线=False,
            推送笔=False,
            推送线段=False,
            推送中枢=False,
            图表展示_笔=False,
            图表展示_线段=False,
            图表展示_扩展线段=False,
            图表展示_扩展线段_线段=False,
            图表展示_线段_线段=False,
            图表展示_中枢_笔=False,
            图表展示_中枢_线段=False,
            图表展示_中枢_扩展线段=False,
            图表展示_中枢_扩展线段_线段=False,
            图表展示_中枢_线段_线段=False,
            图表展示_中枢_线段内部=False,
        )


class 时间周期:
    def __init__(self, 秒: int, 是否单笔交易: bool = False):
        self._秒 = 秒
        self.是否单笔交易 = 是否单笔交易

    def __repr__(self):
        return f"时间周期<{self._秒}, {self.是否单笔交易}>"

    def __str__(self):
        return f"时间周期<{self._秒}, {self.是否单笔交易}>"

    def __int__(self):
        return int(self._秒)

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
        return f"相对方向.{self.name}"

    def __repr__(self):
        return f"相对方向.{self.name}"

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
        return self in (相对方向.向上, 相对方向.向上缺口, 相对方向.衔接向上)

    def 是否向下(self) -> bool:
        return self in (相对方向.向下, 相对方向.向下缺口, 相对方向.衔接向下)

    def 是否包含(self) -> bool:
        return self in (相对方向.顺, 相对方向.逆, 相对方向.同)

    def 是否缺口(self) -> bool:
        return self in (相对方向.向下缺口, 相对方向.向上缺口)

    def 是否衔接(self) -> bool:
        return self in (相对方向.衔接向下, 相对方向.衔接向上)

    @classmethod
    def 分析(cls, 前高: float, 前低: float, 后高: float, 后低: float) -> "相对方向":
        if 前高 == 后高 and 前低 == 后低:
            return 相对方向.同

        if 前高 > 后高 and 前低 > 后低:
            if 前低 == 后高:
                return 相对方向.衔接向下
            if 前低 > 后高:
                return 相对方向.向下缺口
            return 相对方向.向下

        if 前高 < 后高 and 前低 < 后低:
            if 前高 == 后低:
                return 相对方向.衔接向上
            if 前高 < 后低:
                return 相对方向.向上缺口
            return 相对方向.向上

        if 前高 >= 后高 and 前低 <= 后低:
            return 相对方向.顺

        if 前高 <= 后高 and 前低 >= 后低:
            return 相对方向.逆
        raise RuntimeError("无法识别的方向")


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
    def 分析(cls, 左, 中, 右, 可以逆序包含: bool = False, 忽视顺序包含: bool = False) -> Optional["分型结构"]:
        左中关系 = 相对方向.分析(左.高, 左.低, 中.高, 中.低)
        中右关系 = 相对方向.分析(中.高, 中.低, 右.高, 右.低)
        # 左右关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
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

    def __repr__(self):
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
    def __init__(self, 高: float, 低: float) -> None:
        assert 高 > 低
        self.高 = 高
        self.低 = 低

    def __str__(self) -> str:
        return f"缺口区间<{self.低} <=> {self.高}>"

    def __repr__(self) -> str:
        return f"缺口区间<{self.低} <=> {self.高}>"


class 图表展示序列(list):
    def __init__(self, 观察员: "观察者"):
        super().__init__()
        self.观察员 = 观察员
        self.序号 = 0
        self.__类型标识 = None

    def append(self, __object):
        if self.序号 > 0:
            if __object.标识 != self.__类型标识:
                ...
            self.图表刷新(self[-1], sys._getframe().f_lineno)

        else:
            self.__类型标识 = __object.标识
        super().append(__object)
        self.图表添加(__object, sys._getframe().f_lineno)
        self.序号 += 1

        if type(__object) is 线段:
            if self.观察员 and self.观察员.配置.线段内部中枢图显:
                段: 线段 = __object
                段.合_中枢序列 = 图表展示序列(self.观察员)
                段.实_中枢序列 = 图表展示序列(self.观察员)
                段.虚_中枢序列 = 图表展示序列(self.观察员)

    def pop(self, __index: SupportsIndex = -1):
        弹出 = super().pop(__index)
        self.图表移除(弹出, sys._getframe().f_lineno)
        self.序号 -= 1
        return 弹出

    def clear(self) -> None:
        self.序号 = 0
        super().clear()

    def 尾部刷新(self, 行号: int):
        if self.序号:
            self.图表刷新(self[-1], 行号)

    def 图表添加(self, 实线: Union["笔", "线段", "中枢"], 行号: int):
        self.观察员 and self.观察员.报信(实线, 指令.添加(实线.标识), 行号, 周期=实线.周期)

    def 图表移除(self, 实线: Union["笔", "线段", "中枢"], 行号: int):
        self.观察员 and self.观察员.报信(实线, 指令.删除(实线.标识), 行号, 周期=实线.周期)

    def 图表刷新(self, 实线: Union["笔", "线段", "中枢"], 行号: int):
        self.观察员 and self.观察员.报信(实线, 指令.修改(实线.标识), 行号, 周期=实线.周期)


class 买卖点类型(str, Enum):
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
    def __init__(self, 类型: 买卖点类型, 当前K线: "K线", 买卖点分型: "分型", 备注: str, 中枢破位值: float):
        self.备注: str = 备注
        self.类型 = 类型
        self.买卖点分型 = 买卖点分型
        self.买卖点K线 = 买卖点分型.中  # .镜像
        self.__当前K线: "K线" = 当前K线
        self.失效K线: Optional["K线"] = None
        self.终结K线: Optional["K线"] = None  # 卖出 or 买入
        self.__破位值 = 中枢破位值
        self.结构 = None

    def __str__(self):
        return f"{self.类型.value}<{self.买卖点K线}, {self.偏移}, {self.失效偏移}>"

    def __repr__(self):
        return f"{self.类型.value}<{self.买卖点K线}, {self.偏移}, {self.失效偏移}>"

    @property
    def 当前K线(self):
        return self.__当前K线

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

    @property
    def 与MACD柱子匹配(self) -> bool:
        return self.买卖点K线.与MACD柱子匹配

    @property
    def 与MACD柱子分型匹配(self) -> bool:
        return self.买卖点分型.与MACD柱子分型匹配


@final
class 买卖点(基础买卖点):
    @classmethod
    def 一卖点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.一卖, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 一买点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.一买, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 二卖点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.二卖, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 二买点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.二买, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 三卖点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.三卖, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 三买点(cls, 买卖点分型: "分型", 当前K线: "K线", 标识: str, 备注: str, 中枢破位值: float) -> "买卖点":
        return 买卖点(备注=备注, 类型=买卖点类型.三买, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 生成买卖点(cls, 特征: str, 序号: str, 级别: str, 买卖点分型: "分型", 当前缠K: "缠论K线"):
        买卖 = "买" if 买卖点分型.结构 in (分型结构.底, 分型结构.下) else "卖"
        第几 = 序号
        备注 = f"{特征}_{级别}{第几}{买卖}"
        买卖点函数 = getattr(买卖点, f"{第几}{买卖}点")
        破位值 = 买卖点分型.分型特征值
        return 买卖点函数(买卖点分型, 当前缠K, 特征, 备注, 破位值)


class 指标:
    @classmethod
    def K线取值(cls, k线: "K线", 指标计算方式):
        match 指标计算方式:
            case "开":
                return k线.开盘价
            case "高":
                return k线.高
            case "低":
                return k线.低
            case "收":
                return k线.收盘价
            case "高低均值":
                return (k线.高 + k线.低) / 2
            case "高低收均值":
                return (k线.高 + k线.低 + k线.收盘价) / 3
            case "开高低收均值":
                return (k线.高 + k线.低 + k线.开盘价 + k线.收盘价) / 4
            case _:
                return k线.收盘价


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
    def 首次计算_K线(cls, k线: "K线", 计算方式: str, 快线周期: int = 12, 慢线周期: int = 26, 信号周期: int = 9) -> "平滑异同移动平均线":
        初始收盘价: float = 指标.K线取值(k线, 计算方式)
        初始时间: datetime = k线.时间戳
        return cls.首次计算(初始收盘价, 初始时间, 快线周期, 慢线周期, 信号周期)

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
            raise RuntimeError
        else:
            # 快线EMA = 当前收盘价 * 平滑系数(前一个MACD.快线周期) + 前一个MACD.快线EMA * (1 - 平滑系数(前一个MACD.快线周期))
            # 快线EMA = (当前收盘价 - 前一个MACD.快线EMA) * 平滑系数(前一个MACD.快线周期) + 前一个MACD.快线EMA
            快线EMA = 当前收盘价 * 平滑系数(前一个MACD.快线周期) + 前一个MACD.快线EMA * ((前一个MACD.快线周期 - 1) / (前一个MACD.快线周期 + 1))

        # 计算慢线EMA
        if 前一个MACD.慢线EMA is None:
            慢线EMA = 当前收盘价
            raise RuntimeError
        else:
            # 慢线EMA = 当前收盘价 * 平滑系数(前一个MACD.慢线周期) + 前一个MACD.慢线EMA * (1 - 平滑系数(前一个MACD.慢线周期))
            # 慢线EMA = (当前收盘价 - 前一个MACD.慢线EMA) * 平滑系数(前一个MACD.慢线周期) + 前一个MACD.慢线EMA
            慢线EMA = 当前收盘价 * 平滑系数(前一个MACD.慢线周期) + 前一个MACD.慢线EMA * ((前一个MACD.慢线周期 - 1) / (前一个MACD.慢线周期 + 1))

        # 计算DIF
        DIF = 快线EMA - 慢线EMA

        # 计算DEA的EMA
        if 前一个MACD.DEA_EMA is None:
            DEA_EMA = DIF
        else:
            # DEA_EMA = 当前收盘价 * 平滑系数(前一个MACD.信号周期) + 前一个MACD.DEA_EMA * (1 - 平滑系数(前一个MACD.信号周期))
            # DEA_EMA = (DIF - 前一个MACD.DEA_EMA) * 平滑系数(前一个MACD.信号周期) + 前一个MACD.DEA_EMA
            DEA_EMA = DIF * 平滑系数(前一个MACD.信号周期) + 前一个MACD.DEA_EMA * ((前一个MACD.信号周期 - 1) / (前一个MACD.信号周期 + 1))

        # 计算MACD柱
        MACD柱 = DIF - DEA_EMA  # * 2

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
            """if 当前收盘价 > 前一个MACD.收盘价 and DIF < 前一个MACD.DIF and 趋势 == MACD趋势方向.多头:
                信号 = MACD信号.顶背离
            elif 当前收盘价 < 前一个MACD.收盘价 and DIF > 前一个MACD.DIF and 趋势 == MACD趋势方向.空头:
                信号 = MACD信号.底背离"""

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

    @classmethod
    def 增量计算_K线(cls, 前一个MACD: "平滑异同移动平均线", 当前K线: "K线", 计算方式: "str") -> "平滑异同移动平均线":
        当前收盘价: float = 指标.K线取值(当前K线, 计算方式)
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个MACD, 当前收盘价, 当前时间)


class RSI趋势方向(str, Enum):
    """RSI趋势方向枚举"""

    超买 = "超买"
    超卖 = "超卖"
    中性 = "中性"


class RSI信号(str, Enum):
    """RSI交易信号枚举"""

    超卖回升 = "超卖回升"  # 从超卖区回升
    超买回落 = "超买回落"  # 从超买区回落
    无信号 = "无信号"


class 相对强弱指数(BaseModel):
    """
    相对强弱指数 (RSI) 指标
    使用 Wilder 平滑（RMA）进行增量计算，提供完整的中间平滑值，
    并支持对RSI值计算SMA（简单移动平均）
    """

    # 原始数据
    时间戳: datetime = Field(..., description="数据点对应的时间")
    收盘价: float = Field(..., description="当前K线的收盘价格")

    # 参数
    周期: int = Field(14, gt=0, description="RSI周期，默认为14")
    超买阈值: float = Field(70.0, description="超买阈值")
    超卖阈值: float = Field(30.0, description="超卖阈值")
    RSI_SMA周期: Optional[int] = Field(None, description="RSI的SMA周期（可选），用于生成信号线")

    # 核心指标值
    RSI: Optional[float] = Field(None, description="当前RSI值")

    # 中间平滑值（Wilder平滑）
    平均上涨: Optional[float] = Field(None, description="平均上涨幅度的平滑值")
    平均下跌: Optional[float] = Field(None, description="平均下跌幅度的平滑值")

    # 原始变化值（用于调试）
    上涨幅度: float = Field(0.0, description="当前价格变化中的上涨部分")
    下跌幅度: float = Field(0.0, description="当前价格变化中的下跌部分")

    # 平滑系数（α = 1/周期）
    平滑系数: float = Field(0.0, description="Wilder平滑系数")

    # 衍生指标
    趋势方向: Optional[RSI趋势方向] = Field(None, description="当前RSI趋势方向")
    信号: RSI信号 = Field(RSI信号.无信号, description="当前RSI交易信号")

    # RSI的SMA（信号线）相关字段
    RSI_SMA: Optional[float] = Field(None, description="RSI的简单移动平均值")
    RSI历史队列: List[float] = Field(default_factory=list, description="用于计算SMA的RSI历史队列")

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            Enum: lambda v: v.value,
        },
    }

    @classmethod
    def 首次计算(cls, 初始收盘价: float, 初始时间: datetime, 周期: int = 14, 超买阈值: float = 70.0, 超卖阈值: float = 30.0, RSI_SMA周期: Optional[int] = None) -> "相对强弱指数":
        """
        首次计算RSI（没有足够历史数据时使用）
        此时无法计算真实RSI，设为 None，但记录初始收盘价作为起点
        """
        return cls(
            时间戳=初始时间,
            收盘价=初始收盘价,
            周期=周期,
            RSI=None,
            平均上涨=0.0,
            平均下跌=0.0,
            上涨幅度=0.0,
            下跌幅度=0.0,
            平滑系数=1.0 / 周期,
            超买阈值=超买阈值,
            超卖阈值=超卖阈值,
            趋势方向=RSI趋势方向.中性,
            信号=RSI信号.无信号,
            RSI_SMA周期=RSI_SMA周期,
            RSI_SMA=None,
            RSI历史队列=[],
        )

    @classmethod
    def 首次计算_K线(cls, k线: "K线", 计算方式: str, 周期: int = 14, 超买阈值: float = 70.0, 超卖阈值: float = 30.0, RSI_SMA周期: Optional[int] = None) -> "相对强弱指数":
        初始收盘价: float = 指标.K线取值(k线, 计算方式)
        初始时间: datetime = k线.时间戳
        return cls.首次计算(初始收盘价, 初始时间, 周期, 超买阈值, 超卖阈值, RSI_SMA周期)

    @classmethod
    def 增量计算(cls, 前一个RSI: "相对强弱指数", 当前收盘价: float, 当前时间: datetime) -> "相对强弱指数":
        """
        基于前一个RSI指标增量计算当前RSI
        支持可选的RSI_SMA（简单移动平均）
        """
        # 复制参数
        周期 = 前一个RSI.周期
        超买阈值 = 前一个RSI.超买阈值
        超卖阈值 = 前一个RSI.超卖阈值
        RSI_SMA周期 = 前一个RSI.RSI_SMA周期
        平滑系数 = 1.0 / 周期

        # 计算价格变化
        变化 = 当前收盘价 - 前一个RSI.收盘价
        上涨 = max(变化, 0)
        下跌 = max(-变化, 0)

        # 更新平均上涨和平均下跌（Wilder平滑）
        if 前一个RSI.平均上涨 is None or 前一个RSI.平均下跌 is None:
            平均上涨 = 上涨
            平均下跌 = 下跌
        else:
            平均上涨 = 前一个RSI.平均上涨 * (1 - 平滑系数) + 上涨 * 平滑系数
            平均下跌 = 前一个RSI.平均下跌 * (1 - 平滑系数) + 下跌 * 平滑系数

        # 计算RSI
        if 平均下跌 == 0:
            RSI = 100.0 if 平均上涨 > 0 else 50.0
        else:
            RS = 平均上涨 / 平均下跌
            RSI = 100 - (100 / (1 + RS))

        # 确定趋势方向
        if RSI >= 超买阈值:
            趋势方向 = RSI趋势方向.超买
        elif RSI <= 超卖阈值:
            趋势方向 = RSI趋势方向.超卖
        else:
            趋势方向 = RSI趋势方向.中性

        # 生成交易信号（超买回落 / 超卖回升）
        信号 = RSI信号.无信号
        if 前一个RSI.RSI is not None:
            if 前一个RSI.RSI <= 超卖阈值 < RSI:
                信号 = RSI信号.超卖回升
            elif 前一个RSI.RSI >= 超买阈值 > RSI:
                信号 = RSI信号.超买回落

        # ----- 计算RSI的SMA（简单移动平均） -----
        RSI_SMA = None
        历史队列 = 前一个RSI.RSI历史队列.copy() if 前一个RSI.RSI历史队列 else []
        if RSI_SMA周期 is not None and RSI_SMA周期 > 0 and RSI is not None:
            # 将当前RSI加入队列
            历史队列.append(RSI)
            # 保持队列长度不超过周期
            if len(历史队列) > RSI_SMA周期:
                历史队列.pop(0)
            # 计算SMA（即使队列未满也计算当前平均值）
            if 历史队列:
                RSI_SMA = sum(历史队列) / len(历史队列)
        else:
            # 未启用SMA，清空队列
            历史队列 = []

        return cls(
            时间戳=当前时间,
            收盘价=当前收盘价,
            周期=周期,
            RSI=RSI,
            平均上涨=平均上涨,
            平均下跌=平均下跌,
            上涨幅度=上涨,
            下跌幅度=下跌,
            平滑系数=平滑系数,
            超买阈值=超买阈值,
            超卖阈值=超卖阈值,
            趋势方向=趋势方向,
            信号=信号,
            RSI_SMA周期=RSI_SMA周期,
            RSI_SMA=RSI_SMA,
            RSI历史队列=历史队列,
        )

    @classmethod
    def 增量计算_K线(cls, 前一个RSI: "相对强弱指数", 当前K线: "K线", 计算方式: "str") -> "相对强弱指数":
        当前收盘价: float = 指标.K线取值(当前K线, 计算方式)
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个RSI, 当前收盘价, 当前时间)


class KDJ趋势方向(str, Enum):
    """KDJ趋势方向枚举"""

    超买 = "超买"
    超卖 = "超卖"
    中性 = "中性"


class KDJ信号(str, Enum):
    """KDJ交易信号枚举"""

    金叉 = "金叉"
    死叉 = "死叉"
    超买死叉 = "超买死叉"  # 在超买区形成的死叉
    超卖金叉 = "超卖金叉"  # 在超卖区形成的金叉
    无信号 = "无信号"


class 随机指标(BaseModel):
    """
    KDJ 随机指标 (Stochastic Oscillator)
    使用标准参数：N=9, M1=3, M2=3
    支持增量计算，需提供当前K线的最高价、最低价、收盘价
    """

    # 原始数据
    时间戳: datetime = Field(..., description="数据点对应的时间")
    最高价: float = Field(..., description="当前K线的最高价")
    最低价: float = Field(..., description="当前K线的最低价")
    收盘价: float = Field(..., description="当前K线的收盘价")

    # 参数
    N: int = Field(9, ge=1, description="RSV的周期（取最近N根K线）")
    M1: int = Field(3, ge=1, description="K值的平滑周期")
    M2: int = Field(3, ge=1, description="D值的平滑周期")
    超买阈值: float = Field(80.0, description="超买阈值")
    超卖阈值: float = Field(20.0, description="超卖阈值")

    # 核心指标值
    RSV: Optional[float] = Field(None, description="未成熟随机值")
    K: Optional[float] = Field(None, description="K值（快速随机指标）")
    D: Optional[float] = Field(None, description="D值（慢速随机指标）")
    J: Optional[float] = Field(None, description="J值 = 3K - 2D")

    # 中间状态（用于增量计算）
    历史最高价队列: list[float] = Field(default_factory=list, description="最近N根K线的最高价队列")
    历史最低价队列: list[float] = Field(default_factory=list, description="最近N根K线的最低价队列")
    前一个RSV: Optional[float] = Field(None, description="上一个RSV值（用于平滑K）")
    前一个K: Optional[float] = Field(None, description="上一个K值")
    前一个D: Optional[float] = Field(None, description="上一个D值")

    # 衍生指标
    趋势方向: Optional[KDJ趋势方向] = Field(None, description="当前趋势方向")
    信号: KDJ信号 = Field(KDJ信号.无信号, description="当前KDJ信号")

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            Enum: lambda v: v.value,
        },
    }

    @classmethod
    def 首次计算(cls, 初始最高价: float, 初始最低价: float, 初始收盘价: float, 初始时间: datetime, N: int = 9, M1: int = 3, M2: int = 3, 超买阈值: float = 80.0, 超卖阈值: float = 20.0) -> "随机指标":
        """
        首次计算KDJ（无历史数据时）
        此时无法计算RSV和K/D/J，仅记录初始三价，初始化队列
        """
        # 初始化历史队列，放入当前三价
        return cls(
            时间戳=初始时间,
            最高价=初始最高价,
            最低价=初始最低价,
            收盘价=初始收盘价,
            N=N,
            M1=M1,
            M2=M2,
            超买阈值=超买阈值,
            超卖阈值=超卖阈值,
            RSV=None,
            K=None,
            D=None,
            J=None,
            历史最高价队列=[初始最高价],
            历史最低价队列=[初始最低价],
            前一个RSV=None,
            前一个K=None,
            前一个D=None,
            趋势方向=KDJ趋势方向.中性,
            信号=KDJ信号.无信号,
        )

    @classmethod
    def 首次计算_K线(cls, k线: "K线", 计算方式: str, RSV周期: int = 9, K值平滑周期: int = 3, D值平滑周期: int = 3, 超买阈值: float = 80.0, 超卖阈值: float = 20.0) -> "随机指标":
        初始最高价: float = k线.高
        初始最低价: float = k线.低
        初始收盘价: float = k线.收盘价
        初始时间: datetime = k线.时间戳
        return cls.首次计算(初始最高价, 初始最低价, 初始收盘价, 初始时间, RSV周期, K值平滑周期, D值平滑周期, 超买阈值, 超卖阈值)

    @classmethod
    def 增量计算(cls, 前一个KDJ: "随机指标", 当前最高价: float, 当前最低价: float, 当前收盘价: float, 当前时间: datetime) -> "随机指标":
        """
        基于前一个KDJ对象和当前三价，增量计算当前KDJ值
        """
        # 复制参数
        N = 前一个KDJ.N
        M1 = 前一个KDJ.M1
        M2 = 前一个KDJ.M2
        超买阈值 = 前一个KDJ.超买阈值
        超卖阈值 = 前一个KDJ.超卖阈值

        # 更新历史最高价队列
        历史最高价 = 前一个KDJ.历史最高价队列.copy()
        历史最高价.append(当前最高价)
        if len(历史最高价) > N:
            历史最高价.pop(0)

        # 更新历史最低价队列
        历史最低价 = 前一个KDJ.历史最低价队列.copy()
        历史最低价.append(当前最低价)
        if len(历史最低价) > N:
            历史最低价.pop(0)

        # 计算RSV（需要队列长度达到N才能计算）
        RSV = None
        if len(历史最高价) == N and len(历史最低价) == N:
            highest = max(历史最高价)
            lowest = min(历史最低价)
            if highest != lowest:
                RSV = (当前收盘价 - lowest) / (highest - lowest) * 100
            else:
                RSV = 50.0  # 如果最高=最低，RSV取50

        # 计算K值（使用前一天的K值平滑，首次使用RSV）
        K = None
        if RSV is not None:
            if 前一个KDJ.K is None:
                K = RSV  # 首次K值等于RSV
            else:
                # 标准公式：K = 2/3 * 前一日K + 1/3 * 当日RSV
                K = (前一个KDJ.K * (M1 - 1) + RSV) / M1
        else:
            # 数据不足时，K值沿用前一个（若没有则为None）
            K = 前一个KDJ.K

        # 计算D值（使用前一天的D值平滑，首次使用K值）
        D = None
        if K is not None:
            if 前一个KDJ.D is None:
                D = K  # 首次D值等于K
            else:
                # 标准公式：D = 2/3 * 前一日D + 1/3 * 当日K
                D = (前一个KDJ.D * (M2 - 1) + K) / M2
        else:
            D = 前一个KDJ.D

        # 计算J值
        J = None
        if K is not None and D is not None:
            J = 3 * K - 2 * D

        # 确定趋势方向
        if K is not None:
            if K >= 超买阈值:
                趋势方向 = KDJ趋势方向.超买
            elif K <= 超卖阈值:
                趋势方向 = KDJ趋势方向.超卖
            else:
                趋势方向 = KDJ趋势方向.中性
        else:
            趋势方向 = 前一个KDJ.趋势方向

        # 生成交易信号（金叉/死叉）
        信号 = KDJ信号.无信号
        if 前一个KDJ.K is not None and K is not None and 前一个KDJ.D is not None and D is not None:
            # 金叉：K上穿D
            if 前一个KDJ.K <= 前一个KDJ.D and K > D:
                信号 = KDJ信号.金叉
                # 如果在超卖区形成金叉，则记为超卖金叉
                if D < 超卖阈值:
                    信号 = KDJ信号.超卖金叉
            # 死叉：K下穿D
            elif 前一个KDJ.K >= 前一个KDJ.D and K < D:
                信号 = KDJ信号.死叉
                # 如果在超买区形成死叉，则记为超买死叉
                if D > 超买阈值:
                    信号 = KDJ信号.超买死叉

        return cls(
            时间戳=当前时间,
            最高价=当前最高价,
            最低价=当前最低价,
            收盘价=当前收盘价,
            N=N,
            M1=M1,
            M2=M2,
            超买阈值=超买阈值,
            超卖阈值=超卖阈值,
            RSV=RSV,
            K=K,
            D=D,
            J=J,
            历史最高价队列=历史最高价,
            历史最低价队列=历史最低价,
            前一个RSV=RSV,
            前一个K=K,
            前一个D=D,
            趋势方向=趋势方向,
            信号=信号,
        )

    @classmethod
    def 增量计算_K线(cls, 前一个KDJ: "随机指标", 当前K线: "K线", 计算方式: "str") -> "随机指标":
        当前最高价: float = 当前K线.高
        当前最低价: float = 当前K线.低
        当前收盘价: float = 当前K线.收盘价
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个KDJ, 当前最高价, 当前最低价, 当前收盘价, 当前时间)


class 背驰分析:
    @staticmethod
    def MACD背驰(进入段: Union["笔", "线段"], 离开段: Union["笔", "线段"], K线序列: List["K线"], 方式: str = "总") -> bool:
        """MACD柱状线面积背驰"""
        进入MACD = K线.获取MACD(K线序列, 进入段.文.中.标的K线, 进入段.武.中.标的K线)
        离开MACD = K线.获取MACD(K线序列, 离开段.文.中.标的K线, 离开段.武.中.标的K线)

        # 计算面积（绝对值求和）
        进入面积 = abs(进入MACD["总"] if 方式 == "总" else (进入MACD["阳"] if 进入段.方向 is 相对方向.向上 else 进入MACD["阴"]))
        离开面积 = abs(离开MACD["总"] if 方式 == "总" else (离开MACD["阳"] if 进入段.方向 is 相对方向.向上 else 离开MACD["阴"]))

        return 离开面积 < 进入面积

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

    @staticmethod
    def 测度背驰(进入段: Union["笔", "线段"], 离开段: Union["笔", "线段"]) -> bool:
        """价格斜率背驰"""
        dx = 进入段.武.时间戳.timestamp() - 进入段.文.时间戳.timestamp()  # 时间差 self.武.中.标的K线.序号 - self.文.中.标的K线.序号  #
        dy = 进入段.武.分型特征值 - 进入段.文.分型特征值  # 价格差的绝对值
        进入测度 = math.sqrt(dx * dx + dy * dy)

        dx = 离开段.武.时间戳.timestamp() - 离开段.文.时间戳.timestamp()  # 时间差 self.武.中.标的K线.序号 - self.文.中.标的K线.序号  #
        dy = 离开段.武.分型特征值 - 离开段.文.分型特征值  # 价格差的绝对值
        离开测度 = math.sqrt(dx * dx + dy * dy)

        if 进入段.方向 == 相对方向.向上:
            if 离开段.高 > 进入段.高 and abs(离开测度) < abs(进入测度):
                return True
        else:
            if 离开段.低 < 进入段.低 and abs(离开测度) < abs(进入测度):
                return True
        return False


class K线(object):
    __slots__ = ["标识", "序号", "周期", "时间戳", "高", "低", "开盘价", "收盘价", "成交量", "macd", "rsi", "kdj"]

    def __init__(
        self,
        标识: str,
        序号: int,
        周期: int,
        时间戳: datetime,
        开盘价: float,
        最高价: float,
        最低价: float,
        收盘价: float,
        成交量: float,
        macd: 平滑异同移动平均线 = None,
        rsi: 相对强弱指数 = None,
        kdj: 随机指标 = None,
    ):
        self.序号: int = 序号
        self.标识: str = 标识
        self.时间戳: datetime = 时间戳
        self.开盘价: float = 开盘价
        self.高: float = 最高价
        self.低: float = 最低价
        self.收盘价: float = 收盘价
        self.成交量: float = 成交量
        self.周期: int = 周期
        self.macd: 平滑异同移动平均线 = macd
        self.rsi: 相对强弱指数 = rsi
        self.kdj: 随机指标 = kdj

    def __str__(self):
        return f"{self.标识}<{self.序号}, {self.周期}, {self.方向}, {self.时间戳}, {self.开盘价}, {self.高}, {self.低}, {self.收盘价}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.周期}, {self.方向}, {self.时间戳}, {self.开盘价}, {self.高}, {self.低}, {self.收盘价}>"

    @property
    def 方向(self) -> 相对方向:
        return 相对方向.向上 if self.开盘价 < self.收盘价 else 相对方向.向下

    def __bytes__(self):
        return struct.pack(
            ">6d",
            int(self.时间戳.timestamp()),
            round(self.开盘价, 8),
            round(self.高, 8),
            round(self.低, 8),
            round(self.收盘价, 8),
            round(self.成交量, 8),
        )

    @classmethod
    def 创建普K(cls, 标识: str, 时间戳: datetime, 开盘价: float, 最高价: float, 最低价: float, 收盘价: float, 成交量: float, 序号: int, 周期: int) -> "K线":
        k线 = K线(
            标识=标识,
            序号=序号,
            周期=周期,
            时间戳=时间戳,
            开盘价=开盘价,
            最高价=最高价,
            最低价=最低价,
            收盘价=收盘价,
            成交量=成交量,
        )
        return k线

    @classmethod
    def 保存到DAT文件(cls, 路径: str, K线序列: List["K线"]):
        with open(路径, "wb") as f:
            for K in K线序列:
                f.write(bytes(K))
        print(f"保存到DAT文件: {路径}")

    @classmethod
    def 读取大端字节数组(cls, 字节组: bytes, 周期: int = 60, 标识: str = "Bar") -> "K线":
        时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量 = struct.unpack(">6d", 字节组[: struct.calcsize(">6d")])

        return cls(
            标识=标识,
            序号=0,
            周期=周期,
            时间戳=datetime.fromtimestamp(时间戳),
            开盘价=开盘价,
            最高价=最高价,
            最低价=最低价,
            收盘价=收盘价,
            成交量=成交量,
        )

    @classmethod
    def 获取MACD(cls, K线序列: List["K线"], 始: "K线", 终: "K线") -> Dict[str, float]:
        基序 = K线序列[K线序列.index(始) : K线序列.index(终) + 1]

        阳 = 0.0
        阴 = 0.0
        for k in 基序:
            histogram = k.macd.MACD柱
            if histogram >= 0:
                阳 += histogram
            else:
                阴 += histogram

        合 = 阳 + 阴
        return {"阳": 阳, "阴": 阴, "合": 合, "总": 阳 + abs(阴)}


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
        普K = K线.创建普K(
            标识=self.标识,
            序号=0,  # 原始数据序号不重要
            时间戳=时间戳,
            开盘价=开,
            最高价=高,
            最低价=低,
            收盘价=收,
            成交量=量,
            周期=0,  # 原始数据是0秒周期
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
        return K线.创建普K(
            标识=self.标识,
            序号=0 if not self.合成K线列表[周期] else self.合成K线列表[周期][-1].序号 + 1,
            时间戳=时间戳,
            开盘价=普K.开盘价,
            最高价=普K.高,
            最低价=普K.低,
            收盘价=普K.收盘价,
            成交量=普K.成交量,
            周期=周期,
        )

    def _更新K线(self, 当前K线: K线, 新数据: K线):
        """更新当前K线数据"""
        当前K线.高 = max(当前K线.高, 新数据.高)
        当前K线.低 = min(当前K线.低, 新数据.低)
        当前K线.收盘价 = 新数据.收盘价
        当前K线.成交量 += 新数据.成交量
        # 当前K线.原始结束序号 = 新数据.序号

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


class 缠论K线(object):
    __slots__ = ["序号", "时间戳", "高", "低", "方向", "分型", "周期", "标识", "分型特征值", "原始起始序号", "原始结束序号", "标的K线"]

    def __init__(
        self,
        序号: int,
        时间戳: datetime,
        最高价: float,
        最低价: float,
        最终方向: 相对方向,
        普K: "K线",
        原始起始序号: int,
        原始结束序号: int,
        分型: Optional[分型结构] = None,
    ):
        self.序号: int = 序号
        self.时间戳: datetime = 时间戳
        self.高: float = 最高价
        self.低: float = 最低价
        self.方向: 相对方向 = 最终方向
        self.分型: Optional[分型结构] = 分型
        self.周期: int = 普K.周期
        self.标识: str = 普K.标识
        self.分型特征值: float = 最高价

        self.原始起始序号: int = 原始起始序号
        self.原始结束序号: int = 原始结束序号
        self.标的K线: "K线" = 普K

    def __str__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.方向}, {self.时间戳}, {self.高}, {self.低}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.方向}, {self.时间戳}, {self.高}, {self.低}>"

    @property
    def 镜像(self):
        K = 缠论K线(self.序号, self.时间戳, self.高, self.低, self.方向, self.标的K线, self.原始起始序号, self.原始结束序号, self.分型)
        return K

    @property
    def 与MACD柱子匹配(self) -> bool:
        if self.分型 in (分型结构.底, 分型结构.下):
            return self.标的K线.macd.MACD柱 < 0

        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.标的K线.macd.MACD柱 > 0
        return False

    @property
    def 与RSI匹配(self) -> bool:
        if self.分型 in (分型结构.底, 分型结构.下):
            return self.标的K线.rsi.RSI < self.标的K线.rsi.RSI_SMA

        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.标的K线.rsi.RSI > self.标的K线.rsi.RSI_SMA
        return False

    @property
    def 与KDJ匹配(self) -> bool:
        if self.标的K线.kdj.K is None or self.标的K线.kdj.D is None:
            return None
        if self.分型 in (分型结构.底, 分型结构.下):
            return self.标的K线.kdj.K < self.标的K线.kdj.D

        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.标的K线.kdj.K > self.标的K线.kdj.D
        return False

    @classmethod
    def 时间戳对齐(cls, 基线: List["缠论K线"], k线: "缠论K线"):
        if 基线:
            for k in 基线[::-1]:
                if 基线[0].周期 < k线.周期:
                    if k线.时间戳.timestamp() <= k.时间戳.timestamp() <= k线.时间戳.timestamp() + k线.周期:
                        if k线.分型特征值 == k.分型特征值:
                            return k.时间戳
                else:
                    if k.时间戳.timestamp() <= k线.时间戳.timestamp() <= k.时间戳.timestamp() + k.周期:
                        if k线.分型特征值 == k.分型特征值:
                            return k.时间戳
        return k线.时间戳

    @classmethod
    def 创建缠K(cls, 时间戳: datetime, 高: float, 低: float, 方向: 相对方向, 结构: 分型结构, 原始序号: int, 普k: "K线", 之前: Optional["缠论K线"] = None) -> "缠论K线":
        assert 高 >= 低
        序号 = 0
        当前 = 缠论K线(
            序号=序号,
            时间戳=时间戳,
            最高价=高,
            最低价=低,
            最终方向=方向,
            分型=结构,
            原始起始序号=原始序号,
            原始结束序号=原始序号,
            普K=普k,
        )

        if 之前 is not None:
            当前.序号 = 之前.序号 + 1

            if 相对方向.分析(之前.高, 之前.低, 当前.高, 当前.低).是否包含():
                raise ValueError(f"\n    {相对方向.分析(之前.高, 之前.低, 当前.高, 当前.低)}\n    {之前},\n    {当前}")
        return 当前

    @classmethod
    def 兼并(cls, 之前缠K: Optional["缠论K线"], 当前缠K: "缠论K线", 当前普K: "K线", 配置: 缠论配置) -> Tuple[Optional["缠论K线"], Optional[str]]:
        关系 = 相对方向.分析(当前缠K.高, 当前缠K.低, 当前普K.高, 当前普K.低)
        if not 关系.是否包含():
            新缠K = 缠论K线.创建缠K(
                时间戳=当前普K.时间戳,
                高=当前普K.高,
                低=当前普K.低,
                方向=当前普K.方向,
                原始序号=当前普K.序号,
                之前=当前缠K,
                普k=当前普K,
                结构=分型结构.下 if 关系.是否向下() else 分型结构.上,
            )
            新缠K.序号 = 当前缠K.序号 + 1
            return 新缠K, "添加"

        if 当前普K.序号 == 当前缠K.原始结束序号:
            # 当序号相同时认为是重复提交K线
            ...

        if 当前普K.序号 - 1 != 当前缠K.原始结束序号 and 当前普K.序号 != 当前缠K.原始结束序号:
            raise ValueError(f"NewBar.merger: 不可追加不连续元素 缠K.原始结束序号: {当前缠K.原始结束序号}, 当前普K.序号: {当前普K.序号}.")

        # 方向 = 相对方向.向上
        取值函数 = max
        if 之前缠K is not None:
            if 相对方向.分析(之前缠K.高, 之前缠K.低, 当前缠K.高, 当前缠K.低).是否向下():
                取值函数 = min

        if 关系 is not 相对方向.顺:
            当前缠K.时间戳 = 当前普K.时间戳
            当前缠K.标的K线 = 当前普K
        当前缠K.高 = 取值函数(当前缠K.高, 当前普K.高)
        当前缠K.低 = 取值函数(当前缠K.低, 当前普K.低)
        当前缠K.原始结束序号 = 当前普K.序号
        当前缠K.方向 = 当前普K.方向  # FIXME 涉及 买卖点，MACD, 均线

        if 之前缠K is not None:
            当前缠K.序号 = 之前缠K.序号 + 1

        if 配置.缠K合并替换:
            return 当前缠K.镜像, "替换"
        return None, None

    @classmethod
    def 分析(cls, 当前K线: "K线", 缠K序列: List["缠论K线"], 普K序列: List["K线"], 配置: 缠论配置) -> tuple[str, Optional["分型"]]:
        当前K线.标识 = 配置.标识
        if not 普K序列:
            if 配置.计算指标:
                当前K线.macd = 平滑异同移动平均线.首次计算_K线(当前K线, 配置.指标计算方式, 配置.平滑异同移动平均线_快线周期, 配置.平滑异同移动平均线_慢线周期, 配置.平滑异同移动平均线_信号周期)
                当前K线.rsi = 相对强弱指数.首次计算_K线(当前K线, 配置.指标计算方式, 配置.相对强弱指数_周期, 配置.相对强弱指数_超买阈值, 配置.相对强弱指数_超卖阈值, 配置.相对强弱指数_移动平均线周期)
                当前K线.kdj = 随机指标.首次计算_K线(当前K线, 配置.指标计算方式, 配置.随机指标_RSV周期, 配置.随机指标_K值平滑周期, 配置.随机指标_D值平滑周期, 配置.随机指标_超买阈值, 配置.随机指标_超卖阈值)
            普K序列.append(当前K线)
        else:
            之前普K = 普K序列[-1]
            if 之前普K.时间戳 is 当前K线.时间戳:
                当前K线.序号 = 普K序列[-1].序号
                普K序列[-1] = 当前K线
                if 配置.计算指标:
                    try:
                        当前K线.macd = 平滑异同移动平均线.增量计算_K线(普K序列[-2].macd, 当前K线, 配置.指标计算方式)
                        当前K线.rsi = 相对强弱指数.增量计算_K线(普K序列[-2].rsi, 当前K线, 配置.指标计算方式)
                        当前K线.kdj = 随机指标.增量计算_K线(普K序列[-2].kdj, 当前K线, 配置.指标计算方式)
                    except IndexError:
                        pass  # traceback.print_exc()
            else:
                if 之前普K.时间戳 > 当前K线.时间戳:
                    raise RuntimeError("时序错误")
                当前K线.序号 = 之前普K.序号 + 1
                if 配置.计算指标:
                    当前K线.macd = 平滑异同移动平均线.增量计算_K线(之前普K.macd, 当前K线, 配置.指标计算方式)
                    当前K线.rsi = 相对强弱指数.增量计算_K线(之前普K.rsi, 当前K线, 配置.指标计算方式)
                    当前K线.kdj = 随机指标.增量计算_K线(之前普K.kdj, 当前K线, 配置.指标计算方式)
                普K序列.append(当前K线)

        之前缠K: Optional[缠论K线] = None
        状态, 形态 = None, None
        if 缠K序列:
            try:
                之前缠K = 缠K序列[-2]
            except IndexError:
                pass
            新缠K, 模式 = 缠论K线.兼并(之前缠K, 缠K序列[-1], 当前K线, 配置)
            if 新缠K is not None:
                if 模式 == "添加":
                    缠K序列.append(新缠K)
                    状态 = "创建"
                elif 模式 == "替换":
                    缠K序列[-1] = 新缠K
                    状态 = "替换"
                else:
                    raise RuntimeError()
            else:
                状态 = "兼并"
        else:
            新缠K = 缠论K线.创建缠K(时间戳=当前K线.时间戳, 高=当前K线.高, 低=当前K线.低, 方向=当前K线.方向, 原始序号=当前K线.序号, 之前=None, 普k=当前K线, 结构=None)
            缠K序列.append(新缠K)
            状态 = "新建"

        try:
            左, 中, 右 = 缠K序列[-3:]
        except ValueError:
            return 状态, 形态

        形态 = 分型(左=左, 中=中, 右=右)
        结构 = 分型结构.分析(左, 中, 右)
        中.分型 = 结构

        if 结构 is 分型结构.底:
            中.分型特征值 = 中.低
            右.分型特征值 = 右.高

        if 结构 is 分型结构.顶:
            中.分型特征值 = 中.高
            右.分型特征值 = 右.低

        if 结构 is 分型结构.上:
            中.分型特征值 = 中.高
            右.分型特征值 = 右.高

        if 结构 is 分型结构.下:
            中.分型特征值 = 中.低
            右.分型特征值 = 右.低

        if 中.分型 in (分型结构.底, 分型结构.顶):
            return 状态, 形态

        if 中.分型 in (分型结构.下, 分型结构.顶):
            右.分型 = 分型结构.底
            形态 = 分型(中, 右, None)

        if 中.分型 in (分型结构.上, 分型结构.底):
            右.分型 = 分型结构.顶
            形态 = 分型(中, 右, None)
        return 状态, 形态

    @staticmethod
    def 截取(序列: List["缠论K线"], 始: "缠论K线", 终: "缠论K线") -> List["缠论K线"]:
        return 序列[序列.index(始) : 序列.index(终) + 1]


class 分型(object):
    def __init__(self, 左: Optional[缠论K线], 中: 缠论K线, 右: Optional[缠论K线]):
        if 左 and 右:
            assert 左.时间戳 < 中.时间戳 < 右.时间戳
        self.左: Optional[缠论K线] = 左
        self.中: 缠论K线 = 中
        self.右: Optional[缠论K线] = 右
        self.结构 = 中.分型
        self.时间戳 = 中.时间戳
        self.分型特征值 = 中.分型特征值

    def __str__(self):
        return f"{self.中.分型}<{self.时间戳}, {self.分型特征值}, None: {self.左 is None}, None: {self.右 is None}>"

    def __repr__(self):
        return f"{self.中.分型}<{self.时间戳}, {self.分型特征值}, None: {self.左 is None}, None: {self.右 is None}>"

    @property
    def 关系组(self) -> Optional[Tuple[相对方向, 相对方向, 相对方向]]:
        if self.左 and self.右:
            return 相对方向.分析(self.左.高, self.左.低, self.中.高, self.中.低), 相对方向.分析(self.中.高, self.中.低, self.右.高, self.右.低), 相对方向.分析(self.左.高, self.左.低, self.右.高, self.右.低)
        return None

    @property
    def 强势分型关系(self):
        btc_1d = {
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.逆): 1,
            (相对方向.向下缺口, 相对方向.向上缺口, 相对方向.向下缺口): 2,
            (相对方向.向上缺口, 相对方向.向下, 相对方向.逆): 2,
            (相对方向.向上, 相对方向.向下缺口, 相对方向.顺): 4,
            (相对方向.向下缺口, 相对方向.向上缺口, 相对方向.向上缺口): 1,
            (相对方向.向上, 相对方向.向下缺口, 相对方向.向下): 5,
            (相对方向.向下, 相对方向.向上, 相对方向.向下): 21,
            (相对方向.向上, 相对方向.向下, 相对方向.向下): 28,
            (相对方向.向下, 相对方向.向上缺口, 相对方向.顺): 4,
            (相对方向.向上缺口, 相对方向.向下, 相对方向.向上缺口): 4,
            (相对方向.向下, 相对方向.向上, 相对方向.顺): 29,
            (相对方向.向上, 相对方向.向下, 相对方向.向上): 17,
            (相对方向.向下, 相对方向.向上缺口, 相对方向.向上): 6,
            (相对方向.向上, 相对方向.向下, 相对方向.顺): 24,
            (相对方向.向下缺口, 相对方向.向上, 相对方向.向下): 5,
            (相对方向.向下, 相对方向.向上, 相对方向.向上): 17,
            (相对方向.向上, 相对方向.向下, 相对方向.逆): 10,
            (相对方向.向下缺口, 相对方向.向上, 相对方向.向下缺口): 10,
            (相对方向.向下, 相对方向.向上, 相对方向.逆): 8,
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.向下): 1,
            (相对方向.向上, 相对方向.向下缺口, 相对方向.向下缺口): 7,
            (相对方向.向下, 相对方向.向上缺口, 相对方向.向上缺口): 2,
            (相对方向.向下缺口, 相对方向.向上, 相对方向.逆): 1,
            (相对方向.向上缺口, 相对方向.向下, 相对方向.向上): 3,
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.向上): 1,
        }
        btc_1d_r = {
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.逆): 2,
            (相对方向.向下缺口, 相对方向.向上缺口, 相对方向.向下缺口): 3,
            (相对方向.向上缺口, 相对方向.向下, 相对方向.逆): 4,
            (相对方向.向上, 相对方向.向下缺口, 相对方向.顺): 7,
            (相对方向.向下缺口, 相对方向.向上缺口, 相对方向.顺): 2,
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.向下缺口): 1,
            (相对方向.向下缺口, 相对方向.向上缺口, 相对方向.向上缺口): 2,
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.向上缺口): 1,
            (相对方向.向下, 相对方向.衔接向上, 相对方向.向上): 1,
            (相对方向.向上, 相对方向.向下, 相对方向.向下): 42,
            (相对方向.向下, 相对方向.向上缺口, 相对方向.顺): 6,
            (相对方向.向上缺口, 相对方向.向下, 相对方向.向上缺口): 12,
            (相对方向.向下缺口, 相对方向.向上缺口, 相对方向.向上): 1,
            (相对方向.向上, 相对方向.向下, 相对方向.向上): 31,
            (相对方向.衔接向上, 相对方向.向下, 相对方向.向上): 1,
            (相对方向.向下, 相对方向.向上, 相对方向.顺): 55,
            (相对方向.向下, 相对方向.向上, 相对方向.向上): 35,
            (相对方向.向上, 相对方向.向下, 相对方向.顺): 44,
            (相对方向.向上, 相对方向.向下缺口, 相对方向.向下): 13,
            (相对方向.向下, 相对方向.向上, 相对方向.向下): 37,
            (相对方向.向上, 相对方向.向下, 相对方向.逆): 19,
            (相对方向.向下, 相对方向.向上, 相对方向.逆): 17,
            (相对方向.向下缺口, 相对方向.向上, 相对方向.向下): 9,
            (相对方向.向下, 相对方向.向上缺口, 相对方向.向上): 10,
            (相对方向.向上, 相对方向.向下缺口, 相对方向.向下缺口): 11,
            (相对方向.向上缺口, 相对方向.向下, 相对方向.向上): 8,
            (相对方向.向下, 相对方向.向上缺口, 相对方向.向上缺口): 5,
            (相对方向.向下缺口, 相对方向.向上, 相对方向.向下缺口): 15,
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.向下): 2,
            (相对方向.向上缺口, 相对方向.向下缺口, 相对方向.向上): 3,
            (相对方向.向下缺口, 相对方向.向上, 相对方向.逆): 2,
        }
        return btc_1d_r

    @property
    def 强度(self):
        if self.结构 not in (分型结构.底, 分型结构.顶):
            return "未知"
        if not self.右 or not self.左:
            return "未知"

        if 关系组 := self.关系组:
            if self.结构 is 分型结构.底:
                if 关系组[-1].是否向下():
                    return "弱"
                elif 关系组[-1].是否向上():
                    return "强"
                else:
                    return "中"

            elif self.结构 is 分型结构.顶:
                if 关系组[-1].是否向上():
                    return "弱"
                elif 关系组[-1].是否向下():
                    return "强"
                else:
                    return "中"

        if self.右 and self.左:
            if self.结构 is 分型结构.底:
                if self.右.标的K线.收盘价 > self.左.标的K线.高:
                    return "强"
                elif self.右.标的K线.收盘价 > self.中.标的K线.高:
                    return "中"
                else:
                    return "弱"
            elif self.结构 is 分型结构.顶:
                if self.右.标的K线.收盘价 < self.左.标的K线.低:
                    return "强"
                elif self.右.标的K线.收盘价 < self.中.标的K线.低:
                    return "中"
                else:
                    return "弱"
        return "未知"

    @property
    def 与MACD柱子分型匹配(self) -> bool:
        if self.右 and self.左:
            if self.结构 is 分型结构.底:
                return self.左.标的K线.macd.MACD柱 > self.中.标的K线.macd.MACD柱 < self.右.标的K线.macd.MACD柱
            if self.结构 is 分型结构.顶:
                return self.左.标的K线.macd.MACD柱 < self.中.标的K线.macd.MACD柱 > self.右.标的K线.macd.MACD柱
        return False

    @classmethod
    def 判断分型(cls, 左: "分型", 右: "分型", 模式: str = "中") -> bool:
        return 左 is 右

    @staticmethod
    def 从缠K序列中获取分型(K线序列: List[缠论K线], 中: 缠论K线) -> "分型":
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


class 笔(object):
    __slots__ = ["标识", "序号", "周期", "级别", "配置", "文", "武", "方向", "高", "低", "有效性"]

    def __init__(self, 文: 分型, 武: 分型, 有效性: bool = True):
        self.标识 = "笔"
        self.级别 = 1
        self.周期: int = 文.中.周期

        self.序号: int = 0
        self.文: 分型 = 文
        self.武: 分型 = 武
        if 文.结构 is 分型结构.顶 and 武.结构 in (分型结构.底, 分型结构.下):
            self.方向 = 相对方向.向下
            self.高 = 文.中.高
            self.低 = 武.中.低
        elif 文.结构 is 分型结构.底 and 武.结构 in (分型结构.顶, 分型结构.上):
            self.方向 = 相对方向.向上
            self.高 = 武.中.高
            self.低 = 文.中.低
        else:
            raise RuntimeError("无法识别的方向", self.文.结构, self.武.结构)

        self.有效性: bool = 有效性

    def __str__(self):
        return f"笔({self.序号}, {self.方向}, {self.文}, {self.武}, 周期: {self.周期})"

    def __repr__(self):
        return f"笔({self.序号}, {self.方向}, {self.文}, {self.武}, 周期: {self.周期})"

    @property
    def 图表标题(self) -> str:
        return f"{self.文.右.标识}:{self.文.右.周期}:{self.标识}:{self.序号}"

    def 获取缠K数量(self, 缠K序列: List[缠论K线], 笔序列: List["笔"], 配置: 缠论配置) -> int:
        实际高点 = self.实际高点(缠K序列, 配置.笔内相同终点取舍)
        实际低点 = self.实际低点(缠K序列, 配置.笔内相同终点取舍)

        实际数量 = len(缠K序列)
        if 实际数量 >= 配置.笔内元素数量:
            return 实际数量

        if 实际数量 < 3:
            return 0

        if 配置.笔弱化:
            原始数量 = 1 + abs(实际低点.标的K线.序号 - 实际高点.标的K线.序号)
            if 原始数量 >= 配置.笔内元素数量:
                return 配置.笔内元素数量

            if 笔序列:
                筆 = self.根据缠K找笔(笔序列, 实际高点) or self.根据缠K找笔(笔序列, 实际低点)
                if 筆:
                    if 筆.方向 is 相对方向.向上 and 实际低点.低 < 筆.低:
                        if 原始数量 >= 配置.笔弱化_原始数量:
                            return 配置.笔内元素数量
                    if 筆.方向 is 相对方向.向下 and 实际低点.低 > 筆.高:
                        if 原始数量 >= 配置.笔弱化_原始数量:
                            return 配置.笔内元素数量

        return 实际数量

    @staticmethod
    def 次高(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        序列 = sorted(缠K序列, key=lambda k: k.高)
        highs: List[缠论K线] = [k for k in 序列 if k.高 != 序列[-1].高]  # 排除
        highs: List[缠论K线] = [k for k in highs if k.高 == highs[-1].高]  # 筛选
        highs.sort(key=lambda k: k.时间戳)  # 排序
        return highs[-1] if 笔内相同终点取舍 else highs[0]

    @staticmethod
    def 次低(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        序列 = sorted(缠K序列, key=lambda k: k.低)
        lows: List[缠论K线] = [k for k in 序列 if k.低 != 序列[0].低]
        lows: List[缠论K线] = [k for k in lows if k.低 == lows[0].低]
        lows.sort(key=lambda k: k.时间戳)
        return lows[-1] if 笔内相同终点取舍 else lows[0]

    @staticmethod
    def 实际高点(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        序列 = sorted(缠K序列, key=lambda k: k.高)
        highs: List[缠论K线] = [k for k in 序列 if k.高 == 序列[-1].高]
        highs.sort(key=lambda k: k.时间戳)
        return highs[-1] if 笔内相同终点取舍 else highs[0]

    @staticmethod
    def 实际低点(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        序列 = sorted(缠K序列, key=lambda k: k.低)
        lows: List[缠论K线] = [k for k in 序列 if k.低 == 序列[0].低]
        lows.sort(key=lambda k: k.时间戳)
        return lows[-1] if 笔内相同终点取舍 else lows[0]

    def 相对关系(self, 配置: 缠论配置) -> bool:
        if 配置.笔内起始分型包含整笔:
            有效序列 = [k线 for k线 in (self.文.左, self.文.中, self.文.右) if k线 is not None]
            文 = 缺口(max(有效序列, key=lambda k: k.高).高, min(有效序列, key=lambda k: k.低).低)
            有效序列 = [k线 for k线 in (self.武.左, self.武.中, self.武.右) if k线 is not None]
            武 = 缺口(max(有效序列, key=lambda k: k.高).高, min(有效序列, key=lambda k: k.低).低)
            相对关系 = 相对方向.分析(文.高, 文.低, 武.高, 武.低)
        else:
            相对关系 = 相对方向.分析(self.文.中.高, self.文.中.低, self.武.中.高, self.武.中.低)
            if 配置.笔内原始K线包含整笔 and 相对方向.分析(self.文.中.标的K线.高, self.文.中.标的K线.低, self.武.中.标的K线.高, self.武.中.标的K线.低).是否包含():  # TODO 建议增加相关配置
                if not 配置.笔弱化:
                    return False

        if self.方向 is 相对方向.向下:
            return 相对关系.是否向下()
        return 相对关系.是否向上()

    def 之前是(self, 之前: "笔") -> bool:
        if not isinstance(之前, 笔):
            return NotImplemented
        return 分型.判断分型(之前.武, self.文)

    def 之后是(self, 之后: "笔") -> bool:
        if not isinstance(之后, 笔):
            return NotImplemented
        return 分型.判断分型(self.武, 之后.文)

    @classmethod
    def 分析(cls, 当前分型: Optional[分型], 分型序列: List[分型], 笔序列: List["笔"], 缠K序列: List[缠论K线], 递归层次: int, 配置: 缠论配置):
        if 当前分型 is None:
            return 递归层次

        if 当前分型.结构 not in (分型结构.顶, 分型结构.底):
            return 递归层次

        if not 分型序列:
            if 当前分型.结构 in (分型结构.顶, 分型结构.底):
                分型序列.append(当前分型)
            return 递归层次

        笔递归分析 = 笔.分析

        def _弹出旧笔(行号):
            旧分型 = 分型序列.pop()
            if 笔序列:
                旧笔 = 笔序列.pop()
                assert 旧笔.武 is 旧分型, "最后一笔终点错误"
                旧笔.有效性 = False

        def _添加新笔(待添加分型: "分型", 待添加新笔: "笔", 行号):
            分型.向序列中添加(分型序列, 待添加分型)
            if 笔序列 and not 笔序列[-1].之后是(待添加新笔):
                raise ValueError("笔.向序列中添加 不连续", 笔序列[-1], 待添加新笔)

            if 笔序列:
                待添加新笔.序号 = 笔序列[-1].序号 + 1
                if 待添加新笔.武.左 is None and 待添加新笔.武.右 is None:
                    待添加新笔.有效性 = False
                if 笔序列[-1].武.结构 in (分型结构.上, 分型结构.下):
                    print(f"_添加新笔[{行号}] 出现无效分型", 笔序列[-1])

            笔序列.append(待添加新笔)

        之前分型 = 分型序列[-1]
        if (之前分型.中.时间戳 == 当前分型.中.时间戳) or (之前分型.结构 in (分型结构.上, 分型结构.下)):
            _弹出旧笔(sys._getframe().f_lineno)
            if not 分型序列:
                当前分型.右 and 分型序列.append(当前分型)
                return 递归层次

        之前分型 = 分型序列[-1]
        if 之前分型.中.时间戳 > 当前分型.中.时间戳:
            raise RuntimeError(f"时序错误-{递归层次}, {之前分型}, {当前分型}")

        if 配置.笔弱化 and 笔序列:
            前一笔 = 笔序列[-1]
            if 前一笔.武.中.序号 - 前一笔.文.中.序号 + 1 == 3:
                if (前一笔.方向.是否向上() and 前一笔.低 > 当前分型.分型特征值 and 当前分型.结构 is 分型结构.底) or (前一笔.方向.是否向下() and 前一笔.高 < 当前分型.分型特征值 and 当前分型.结构 is 分型结构.顶):
                    _弹出旧笔(sys._getframe().f_lineno)
                    return 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 递归层次 + 1, 配置)

        if 之前分型.结构 is not 当前分型.结构:
            基础序列 = 缠论K线.截取(缠K序列, 之前分型.中, 当前分型.中)
            当前笔 = 笔(文=之前分型, 武=当前分型)
            if 当前笔.获取缠K数量(基础序列, 笔序列, 配置) >= 配置.笔内元素数量:
                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    文官 = 当前笔.实际高点(基础序列, False)
                else:
                    文官 = 当前笔.实际低点(基础序列, False)

                if 文官 is not 之前分型.中:
                    临时分型 = 分型.从缠K序列中获取分型(缠K序列, 文官)
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        assert 临时分型.结构 is 分型结构.顶, 临时分型
                    else:
                        assert 临时分型.结构 is 分型结构.底, 临时分型
                    递归层次_ = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 递归层次 + 1, 配置)
                    递归层次_ += 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 递归层次 + 1, 配置)
                    return 递归层次_ - (递归层次 * 2)

                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    武将 = 当前笔.实际低点(基础序列, 配置.笔内相同终点取舍)
                else:
                    武将 = 当前笔.实际高点(基础序列, 配置.笔内相同终点取舍)

                if 当前笔.相对关系(配置) and 当前分型.中 is 武将:
                    _添加新笔(当前分型, 当前笔, sys._getframe().f_lineno)
                    return 递归层次

                if 配置.笔次级成笔:
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        武将 = 当前笔.次低(基础序列, 配置.笔内相同终点取舍)
                    else:
                        武将 = 当前笔.次高(基础序列, 配置.笔内相同终点取舍)
                    if 当前笔.相对关系(配置) and 当前分型.中 is 武将:
                        _添加新笔(当前分型, 当前笔, sys._getframe().f_lineno)
                        return 递归层次

        else:
            分型特征值 = 当前分型.分型特征值

            if (之前分型.结构 is 分型结构.顶 and 之前分型.分型特征值 < 分型特征值) or (之前分型.结构 is 分型结构.底 and 之前分型.分型特征值 > 分型特征值):
                _弹出旧笔(sys._getframe().f_lineno)
                if 分型序列:
                    之前分型 = 分型序列[-1]
                    if 当前分型.结构 is 分型结构.顶:
                        assert 之前分型.结构 is 分型结构.底, 之前分型.结构
                    else:
                        assert 之前分型.结构 is 分型结构.顶, 之前分型.结构

                    return 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 递归层次 + 1, 配置)
                else:
                    分型.向序列中添加(分型序列, 当前分型)

        return 递归层次

    @staticmethod
    def 以文会友(笔序列: List["笔"], 文: 分型) -> Optional["笔"]:
        for 筆 in 笔序列:
            if 筆.文 is 文:
                return 筆
        return None

    @staticmethod
    def 以武会友(笔序列: List["笔"], 武: 分型) -> Optional["笔"]:
        for 筆 in 笔序列[::-1]:
            if 筆.武 is 武:
                return 筆
        return None

    @staticmethod
    def 根据缠K找笔(笔序列: List["笔"], 缠K: "缠论K线", 偏移: int = 1):
        for 筆 in 笔序列[::-1]:
            if 筆.文.中.序号 - 偏移 <= 缠K.序号 <= 筆.武.中.序号:
                # if 缠K in 筆.缠K序列[偏移:]:
                return 筆

        return None


class 线段特征(list):
    def __init__(self, 标识: str, 基础序列: List["笔"] | List["线段"], 线段方向: 相对方向):
        super().__init__(基础序列)
        self.序号 = 0
        self.标识: str = 标识
        self.线段方向: 相对方向 = 线段方向

    @property
    def 图表标题(self) -> str:
        return self.标识  # f"{self.标识}:{self.序号}"

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
            return max([线.文 for 线 in self], key=lambda o: o.中.高)
        else:
            return min([线.文 for 线 in self], key=lambda o: o.中.低)

    @property
    def 武(self) -> 分型:
        if self.线段方向 is 相对方向.向上:  # 取高高
            return max([线.武 for 线 in self], key=lambda o: o.中.高)
        else:
            return min([线.武 for 线 in self], key=lambda o: o.中.低)

    @property
    def 高(self) -> float:
        return max([self.文, self.武], key=lambda fx: fx.中.高).中.高

    @property
    def 低(self) -> float:
        return min([self.文, self.武], key=lambda fx: fx.中.低).中.低

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
    def 静态分析(cls, 虚线序列: List["笔"] | List["线段"], 线段方向: 相对方向, 四象: str, 是否忽视: bool = False) -> List["线段特征"]:
        """
        :param 虚线序列:
        :param 线段方向:
        :param 四象: 老阴，老阳，少阴，小阳
            老阴 老阳 分别代表 缺口顶分型后的向下线段 与 缺口底分型后的向上线段
        :return: 特征序列元组
        """

        if 四象 in ("老阳", "老阴") and not 是否忽视:
            # 特征序列带有缺口时 要严格处理包含关系
            需要被合并方向序列 = (相对方向.顺, 相对方向.逆, 相对方向.同)
            # 需要被合并方向序列 = (相对方向.顺, 相对方向.同)
        else:
            需要被合并方向序列 = (相对方向.顺, 相对方向.同)

        # print("    线段特征.分析", 四象, 需要被合并方向序列, 虚线序列)
        特征序列: List[线段特征] = []
        for 当前虚线 in 虚线序列:
            if 当前虚线.方向 is 线段方向:
                if len(特征序列) >= 3:
                    左, 中, 右 = 特征序列[-3], 特征序列[-2], 特征序列[-1]
                    # 关系 = 相对方向.分析(左.高, 左.低, 中.高, 中.低)
                    结构 = 分型结构.分析(左, 中, 右, 可以逆序包含=True, 忽视顺序包含=True)
                    # print("    线段特征.分析", 四象, 结构, 关系)
                    if (线段方向 is 相对方向.向上 and 结构 is 分型结构.顶 and 当前虚线.高 > 中.高) or (线段方向 is 相对方向.向下 and 结构 is 分型结构.底 and 当前虚线.低 < 中.低):
                        小号虚线 = min(中, key=lambda o: o.序号)
                        大号虚线 = max(右, key=lambda o: o.序号)
                        fake = 笔(
                            文=小号虚线.文,
                            武=大号虚线.武,
                        )
                        特征序列.pop()
                        特征序列[-1] = 线段特征.新建([fake], 线段方向)
                        # print("    线段特征.分析 情况一:", 关系, 结构, 四象, 当前虚线)
                continue

            if 特征序列:
                之前线段特征 = 特征序列[-1]
                if 相对方向.分析(之前线段特征.高, 之前线段特征.低, 当前虚线.高, 当前虚线.低) in 需要被合并方向序列:
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
            结构 = 分型结构.分析(特征序列[i - 1], 特征序列[i], 特征序列[i + 1], True, True)
            结构序列.append(特征分型(特征序列[i - 1], 特征序列[i], 特征序列[i + 1], 结构))
        if 结构序列:
            assert 特征序列[-1] is 结构序列[-1].右
        return 结构序列


class 特征分型:
    def __init__(self, 左: 线段特征, 中: 线段特征, 右: 线段特征, 结构: 分型结构):
        self.左: 线段特征 = 左
        self.中: 线段特征 = 中
        self.右: 线段特征 = 右
        self.结构 = 结构

    def __str__(self):
        return f"特征分型<{self.结构}, {self.中}>"

    def __repr__(self):
        return f"特征分型<{self.结构}, {self.中}>"


class 线段(object):
    __slots__ = ["标识", "序号", "周期", "级别", "文", "武", "有效性", "__基础序列__", "特征序列", "实_中枢序列", "虚_中枢序列", "合_中枢序列", "确认K线", "模式", "_特征序列_显示", "前一缺口", "前一结束位置"]

    def __init__(self, 序号: int, 文: 分型, 武: 分型, 基础序列: List, 有效性: bool = True):
        # super().__init__(基础序列[:])
        self.__基础序列__ = 基础序列[:]
        self.标识 = self.__class__.__name__
        self.级别 = 1
        self.周期 = 文.中.周期

        self.序号: int = 序号
        self.文: 分型 = 文
        self.武: 分型 = 武

        self.有效性: bool = 有效性

        self.特征序列: List[Optional[线段特征]] = [None] * 3

        self.实_中枢序列: List["中枢"] = []
        self.虚_中枢序列: List["中枢"] = []
        self.合_中枢序列: List["中枢"] = []
        self.确认K线: Optional[缠论K线] = None
        self.模式: str = "文武"
        self._特征序列_显示 = False
        self.标识 = "线段" if type(self[0]) is 笔 else f"线段<{self[0].标识}>"
        self.级别 = self[0].级别 + 1
        self.前一缺口: Optional[缺口] = None
        self.前一结束位置 = None

    def append(self, 线):
        if len(self) and not 分型.判断分型(self[-1].武, 线.文):
            raise ValueError(f"{self.标识}.添加虚线 不连续", self[-1], 线)
        基础 = self.__基础序列__  # super()
        基础.append(线)

    def pop(self, index: int = -1):
        基础 = self.__基础序列__  # super()
        return 基础.pop(index)

    def index(self, item):
        基础 = self.__基础序列__  # super()
        return 基础.index(item)

    def __len__(self):
        基础 = self.__基础序列__  # super()
        return len(基础)

    def __getitem__(self, item):
        基础 = self.__基础序列__  # super()
        return 基础[item]

    def __setitem__(self, key, value):
        基础 = self.__基础序列__  # super()
        基础[key] = value

    def __str__(self):
        return f"{self.标识}<{self.序号}, {self.四象}, {self.方向}, {self.文}, {self.武}, 数量: {len(self)}, 缺口: {self.缺口}, {self.确认K线}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.四象}, {self.方向}, {self.文}, {self.武}, 数量: {len(self)}, 缺口: {self.缺口}, {self.确认K线}>"

    @property
    def 图表标题(self) -> str:
        return f"{self.文.右.标识}:{self.文.右.周期}:{self.标识}:{self.序号}"

    @property
    def 缠K序列(self) -> List[缠论K线]:
        结果 = []
        for 元素 in self:
            if type(元素) is 笔:
                if not 结果:
                    结果.extend(元素.缠K序列[:])
                else:
                    结果.extend(元素.缠K序列[1:])
            else:
                if not 结果:
                    结果.extend(元素.缠K序列)
                else:
                    结果.extend(元素.缠K序列[1:])
        return 结果

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
        """if self.模式 != "文武":
        if type(self[0] is 笔):
            return max(self.__基础序列__, key=lambda x: x.高).高"""

        if self.方向 is 相对方向.向上:
            return self.武.中.高
        return self.文.中.高

    @property
    def 低(self) -> float:
        """if self.模式 != "文武":
        if type(self[0] is 笔):
            return min(self.__基础序列__, key=lambda x: x.低).低"""
        if self.方向 is 相对方向.向下:
            return self.武.中.低
        return self.文.中.低

    def 武斗(self, 武: 分型, 行号: int):
        # print(f"{self.__class__.__name__}.武斗[{行号}], ", 武)
        if self.武.分型特征值 == 武.分型特征值:
            self.武 = 武
            return
        assert self.文.结构 is not 武.结构, ("文武结构相同", self.文, 武)
        if 武.右 is not None and 分型结构.分析(武.左, 武.中, 武.右) is not 武.结构:
            raise RuntimeError(分型结构.分析(武.左, 武.中, 武.右), 武.结构)
        if self.方向 is 相对方向.向上:
            if 武.分型特征值 < self.文.分型特征值:
                raise RuntimeError("向上虚线, 结束点 小于 起点", self.标识, self.文, 武)
            # if max([self._武, 武], key=lambda k: k.分型特征值) is not 武:
            #    pass  # print(colored(f"{self.__class__.__name__}.武斗[{行号}] 出现回退 从 {self._武} ==>>> {武}", "red", "on_green"))  # raise RuntimeError(self._武, 武)
        else:
            if 武.分型特征值 > self.文.分型特征值:
                raise RuntimeError("向下虚线, 结束点 大于 起点", self.标识, self.文, 武)
            # if min([self._武, 武], key=lambda k: k.分型特征值) is not 武:
            #    pass  # print(colored(f"{self.__class__.__name__}.武斗[{行号}] 出现回退 从 {self._武} ==>>> {武}", "red", "on_green"))  # raise RuntimeError(self._武, 武)
        self.武 = 武

    @property
    def 贯穿伤(self) -> Optional[Union[笔, "线段"]]:
        """
        反向一笔直接贯穿起点
        """
        return self.分割序列()[3]

    @property
    def 特征分型终结(self) -> bool:
        """
        是否符合特征序列 正常分型 终结
        """
        特征序列 = 线段特征.静态分析(self.__基础序列__, self.方向, self.四象)
        if len(特征序列) >= 3:
            结构 = 分型结构.分析(特征序列[-3], 特征序列[-2], 特征序列[-1], True, True)
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
    def 缺口(self) -> Optional[缺口]:
        if self.模式 != "文武":
            return None
        if self.左 is None:
            return None
        if self.中 is None:
            return None
        相对关系 = 相对方向.分析(self.左.高, self.左.低, self.中.高, self.中.低)
        if 相对关系.是否缺口():
            hl = [self.左.文.分型特征值, self.中.文.分型特征值]
            return 缺口(max(*hl), min(*hl))
        return None

    @property
    def 四象(self) -> str:
        """
        老阳: 向下线段第一二特征序列有缺口时，后一向上线段
        老阴: 向上线段第一二特征序列有缺口时，后一向下线段
        小阳: 向上线段
        少阴: 向下线段
        """
        if self.前一缺口 is not None:
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
                self[:] = 基础序列[:]
            else:
                raise RuntimeError()
        else:
            pass

    def 之前是(self, 之前: "线段") -> bool:
        if not isinstance(之前, 线段):
            return NotImplemented

        return 分型.判断分型(之前.武, self.文)

    def 之后是(self, 之后: "线段") -> bool:
        if not isinstance(之后, 线段):
            return NotImplemented

        return 分型.判断分型(self.武, 之后.文)

    def __设置特征(self, 偏移: int, 特征: Optional[线段特征]):
        if self.模式 != "文武":
            return
        if 特征 and 特征.方向 == self.方向:
            raise ValueError("特征序列方向不匹配")
        self.特征序列[偏移] = 特征

    def 设置特征序列(self, 序列, 行号):
        # print(f"线段.设置特征序列[{行号}]", self)
        if self.模式 != "文武":
            return
        self.左, self.中, self.右 = 序列

    def __刷新特征序列(self, 配置: 缠论配置):
        if self.模式 != "文武":
            return
        基础序列 = self
        if self.前一结束位置:
            基础序列 = self[self.index(self.前一结束位置) - 1 :]

        特征序列 = 线段特征.静态分析(基础序列, self.方向, self.四象, 配置.线段_特征序列忽视老阴老阳)
        if len(特征序列) >= 3:
            分型序列 = 线段特征.获取分型序列(特征序列)
            if (self.方向 is 相对方向.向上 and 分型序列[-1].结构 is 分型结构.顶) or (self.方向 is 相对方向.向下 and 分型序列[-1].结构 is 分型结构.底):
                self.设置特征序列([分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)

            else:
                self.设置特征序列([特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)
        else:
            特征序列.extend([None] * (3 - len(特征序列)))
            self.设置特征序列(特征序列, sys._getframe().f_lineno)

    def 分割序列(self, 所属中枢: Optional["中枢"] = None) -> Tuple[List[Union["笔", "线段"]], List[Union["笔", "线段"]], List[Union["笔", "线段"]], Optional[Union["笔", "线段"]]]:
        if self.模式 != "文武":
            return self[:], [], [], None
        if len(self) == 0:
            print(self.标识, self.序号)
        assert self[0].文 is self.文, (self[0].文, self.文)
        前: List["笔"] = []
        后: List["笔"] = []
        第三买卖线 = []
        贯穿伤 = None

        for 筆 in self:
            if not 前:
                前.append(筆)
                continue
            if 前[-1].武 is not self.武 and not 后:
                前.append(筆)

            if 后:
                后.append(筆)
            if 筆.文 is self.武:
                后.append(筆)

        状态 = None

        if 所属中枢:
            所属中枢.本级_第三买卖线 = None
            尾部 = self.武
            if 后:
                尾部 = 后[-1].武
            if 所属中枢.高 >= 尾部.分型特征值 >= 所属中枢.低:
                状态 = "中枢之中"
            elif 所属中枢.高 < 尾部.分型特征值:
                状态 = "中枢之上"
            elif 所属中枢.低 > 尾部.分型特征值:
                状态 = "中枢之下"
            assert "中枢" in 状态

        if 状态 == "中枢之上":
            for 筆 in self[::-1]:
                if 筆.方向 is 相对方向.向下:
                    关系 = 相对方向.分析(所属中枢.高, 所属中枢.低, 筆.高, 筆.低)
                    if 关系 is 相对方向.向上缺口:
                        第三买卖线.append(筆)
                    else:
                        break

        if 状态 == "中枢之下":
            for 筆 in self[::-1]:
                if 筆.方向 is 相对方向.向上:
                    关系 = 相对方向.分析(所属中枢.高, 所属中枢.低, 筆.高, 筆.低)
                    if 关系 is 相对方向.向下缺口:
                        第三买卖线.append(筆)
                    else:
                        break

        if 第三买卖线 and 所属中枢:
            第三买卖线.reverse()
            所属中枢.本级_第三买卖线 = 第三买卖线[0]

        if 后:
            if self.方向.是否向上():
                if 后[0].武.分型特征值 < self.文.分型特征值:
                    贯穿伤 = 后[0]
            else:
                if 后[0].武.分型特征值 > self.文.分型特征值:
                    贯穿伤 = 后[0]

        return 前, 后, 第三买卖线, 贯穿伤

    def 检查连续性(self) -> bool:
        for i in range(1, len(self)):
            if not self[i - 1].之后是(self[i]):
                print("    线段.检查连续性", list.__str__(self))
                print("    线段.检查连续性", self[i - 1], self[i])
                return False
        return True

    def 刷新(self, 配置: 缠论配置):
        if self.模式 != "文武":
            return
        if not len(self):
            print("    线段.刷新 基础序列为空")
            return
        self.__刷新特征序列(配置)
        有效特征序列 = [特征 for 特征 in self.特征序列 if 特征 is not None]
        if len(有效特征序列) == 3:
            self.武斗(self.中.文, sys._getframe().f_lineno)

        elif len(有效特征序列) >= 1:
            最近特征 = 有效特征序列[-1]

            if 最近特征[-1] not in self:
                特征后一笔 = 笔.以武会友(self.__基础序列__, 最近特征[-1].武)
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
        self.获取内部中枢序列(配置)

    def 序列重置(self, 序列: Sequence):
        基础序列 = []
        for 元素 in self:
            if 元素 not in 序列:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    break
            基础序列.append(元素)

        self[:] = 基础序列[:]
        self.右 = None

    def 查找贯穿伤(self) -> Optional[Union[笔, "线段"]]:
        for 贯穿伤 in self.__基础序列__[3:]:
            if self.方向.是否向上():
                if 贯穿伤.武.分型特征值 < self.文.分型特征值:
                    return 贯穿伤
            else:
                if 贯穿伤.武.分型特征值 > self.文.分型特征值:
                    return 贯穿伤
        return None

    def 获取内部中枢序列(self, 配置: 缠论配置) -> Tuple[List["中枢"], List["中枢"], List["中枢"]]:
        # 线段内部如存在中枢则级别比无中枢要大
        if self.模式 != "文武":
            return [], [], []
        实, 虚, _, _ = self.分割序列()

        中枢.分析(实, self.实_中枢序列, 标识=f"{self.标识}_{self.序号}_实_")
        中枢.分析(虚, self.虚_中枢序列, 标识=f"{self.标识}_{self.序号}_虚_")
        中枢.分析(self.__基础序列__, self.合_中枢序列, 标识=f"{self.标识}_{self.序号}_合_")
        return self.虚_中枢序列, self.实_中枢序列, self.合_中枢序列  # 阴 阳 合

    @classmethod
    def 基础判断(cls, 左: Union["笔", "线段"], 中: Union["笔", "线段"], 右: Union["笔", "线段"], 关系序列: List[相对方向]) -> bool:
        """
        连续三笔且重叠
        """

        if not 左.之后是(中):
            return False
        if not 中.之后是(右):
            return False

        if not 相对方向.分析(左.高, 左.低, 中.高, 中.低).是否包含():
            return False
        if not 相对方向.分析(中.高, 中.低, 右.高, 右.低).是否包含():
            return False

        关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
        if 关系 not in 关系序列:
            return False

        if 左.方向 is 相对方向.向下 and not 关系.是否向下():
            return False
        if 左.方向 is 相对方向.向上 and not 关系.是否向上():
            return False
        return True

    @classmethod
    def 新建(cls, 虚线序列: List["笔"]) -> "线段":
        段 = 线段(序号=0, 文=虚线序列[0].文, 武=虚线序列[-1].武, 基础序列=虚线序列)
        return 段

    @classmethod
    def 分析(cls, 笔序列: List[Union["笔", "线段"]], 线段序列: List["线段"], 配置: 缠论配置, 层级: int = 0, 关系序列=[相对方向.向上, 相对方向.向下]) -> None:
        """
        注意笔序列前三个元素必须符合线段基本要求
        四象: 老阴，老阳，少阴，小阳
            老阴 老阳 分别代表 缺口顶分型后的向下线段 与 缺口底分型后的向上线段
            当其分型完成时需要对 线段.前一缺口 设置为None，新线段不在考虑之前是否有缺口的问题
        无缺口: 即笔破坏
            笔破坏不去处理特征序列的逆序包含
        """
        if 层级 > 20:
            raise RuntimeError("线段分析 层级过深")

        线段递归分析 = 线段.分析

        def _添加线段(待添加线段: "线段", 行号):
            if 线段序列 and not 线段序列[-1].之后是(待添加线段):
                raise ValueError(f"线段.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)
            待添加线段.模式 = "文武"
            if 线段序列:
                之前线段 = 线段序列[-1]
                if not 之前线段.右:
                    assert 之前线段.右[-1] in 待添加线段
                    raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段.右 = None", 之前线段)
                if 之前线段[-1] not in 待添加线段:
                    raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段[-1] not in 待添加虚线!", 之前线段)
                待添加线段.序号 = 之前线段.序号 + 1
                待添加线段.前一缺口 = 之前线段.缺口
                待添加线段.前一结束位置 = 之前线段[-1]
                if 之前线段.四象 in ("老阴", "老阳"):
                    待添加线段.前一缺口 = None

                if 配置.图表展示_中枢_线段内部 and 配置.推送中枢:
                    getattr(之前线段.实_中枢序列, "尾部刷新", Nil)(sys._getframe().f_lineno)
                    # getattr(之前线段.虚_中枢序列, "尾部刷新", Nil)(sys._getframe().f_lineno)
                    while 之前线段.虚_中枢序列:
                        之前线段.虚_中枢序列.pop()
                    getattr(之前线段.合_中枢序列, "尾部刷新", Nil)(sys._getframe().f_lineno)

            线段序列.append(待添加线段)
            # print(f"线段._向序列中添加[{行号}]", 待添加虚线)

        def _弹出线段(待弹出线段: "线段", 行号):
            if not 线段序列:
                return None

            if 线段序列[-1] is 待弹出线段:
                if 待弹出线段.右 is not None:
                    结构 = 分型结构.分析(待弹出线段.左, 待弹出线段.中, 待弹出线段.右, True, True)
                    if 结构 in (分型结构.顶, 分型结构.底) and not 相对方向.分析(待弹出线段.左.高, 待弹出线段.左.低, 待弹出线段.中.高, 待弹出线段.中.低).是否缺口():
                        print(colored(f"[警告<{行号}>]:", "yellow"), colored("线段._从序列中删除 发现分型完毕, 且特征序列无缺口", "red"), 待弹出线段)  # 异常弹出
                线段序列.pop()
                待弹出线段.前一结束位置 = None
                待弹出线段.有效性 = False
                if 配置.图表展示_中枢_线段内部 and 配置.推送中枢:
                    for 中枢_ in 待弹出线段.实_中枢序列:
                        getattr(待弹出线段.实_中枢序列, "图表移除", Nil)(中枢_, sys._getframe().f_lineno)
                    for 中枢_ in 待弹出线段.虚_中枢序列:
                        getattr(待弹出线段.虚_中枢序列, "图表移除", Nil)(中枢_, sys._getframe().f_lineno)
                    for 中枢_ in 待弹出线段.合_中枢序列:
                        getattr(待弹出线段.合_中枢序列, "图表移除", Nil)(中枢_, sys._getframe().f_lineno)
                # print(f"线段._从序列中删除[{行号}]", 待弹出线段)
                return 待弹出线段
            raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

        if not 线段序列:
            for i in range(1, len(笔序列) - 1):
                左, 中, 右 = 笔序列[i - 1], 笔序列[i], 笔序列[i + 1]
                if not 线段.基础判断(左, 中, 右, 关系序列):  # FIXME 首个线段必须有明确方向
                    continue

                段 = 线段.新建([左, 中, 右])
                _添加线段(段, f"{sys._getframe().f_lineno}, {层级}")
                段.左 = 线段特征.新建([中], 段.方向)
                break
            if not 线段序列:
                return None

        while 线段序列 and 线段序列[-1].前一结束位置:
            if 线段序列[-1].前一结束位置 not in 笔序列:
                _弹出线段(线段序列[-1], f"{sys._getframe().f_lineno}, {层级}")
            else:
                break

        if not 线段序列:
            return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

        当前线段 = 线段序列[-1]
        当前线段.序列重置(笔序列)

        if len(当前线段) < 3:
            _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
            if not 线段序列:
                return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

        当前线段 = 线段序列[-1]

        if 当前线段.右 is not None:
            基础序列 = 当前线段.分割序列()[1]
            # print(colored(f"线段. 分析[{层级}] 特殊情况, 特征序列俱全时出现在 线段序列尾部, 基础序列: ", "red"), len(基础序列), 当前线段)
            新段 = 线段.新建(基础序列)
            _添加线段(新段, f"{sys._getframe().f_lineno}, {层级}")
            if 当前线段.四象 in ("老阴", "老阳"):
                新段.前一缺口 = None

        当前线段 = 线段序列[-1]
        当前线段.刷新(配置)
        当前虚线 = 当前线段[-1]
        四象 = 当前线段.四象
        if 四象 in ("老阳", "老阴") and 当前线段.右 is None:
            if (四象 == "老阳" and 当前虚线.低 < 当前线段.低) or (四象 == "老阴" and 当前虚线.高 > 当前线段.高):
                # 缺口{顶底}分型被突破
                序列 = 当前线段[:]
                _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                当前线段 = 线段序列[-1]
                assert 当前线段.右 is not None
                当前线段基础序列 = 当前线段.分割序列()[0]
                当前线段基础序列.extend(序列)

                当前线段[:] = 当前线段基础序列[:]
                当前线段.刷新(配置)

        if 配置.线段_非缺口下穿刺 and 四象 in ("小阳", "少阴") and 当前线段.右 is None:
            if 贯穿伤 := 当前线段.查找贯穿伤():
                基础序列 = 当前线段[当前线段.index(贯穿伤) :]
                if len(基础序列) == 4 and len(线段序列) >= 2:
                    左, 中, 右 = 基础序列[-3], 基础序列[-2], 基础序列[-1]
                    if 相对方向.分析(左.高, 左.低, 右.高, 右.低) is 当前线段.方向:
                        print(colored(f"[警告<{sys._getframe().f_lineno}, {层级}>]:", "yellow"), colored("线段.修复贯穿伤", "red"), 贯穿伤, 基础序列)  # 异常弹出
                        基础序列 = 当前线段[:]
                        _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                        当前线段 = 线段序列[-1]
                        当前线段.右 = None
                        for 临时虚线 in 基础序列[基础序列.index(当前线段[-1]) + 1 :]:
                            当前线段.append(临时虚线)
                        当前线段.刷新(配置)
                        if 当前线段.右:
                            段 = 线段.新建([左, 中, 右])
                            _添加线段(段, f"{sys._getframe().f_lineno}, {层级}")
                            段.左 = 线段特征.新建([中], 段.方向)

        序号 = 笔序列.index(当前线段[-1]) + 1

        for 当前虚线 in 笔序列[序号:]:
            当前线段 = 线段序列[-1]

            四象 = 当前线段.四象
            线段方向 = 当前线段.方向
            同向 = 当前虚线.方向 is 线段方向

            当前线段.append(当前虚线)
            当前线段.刷新(配置)

            if not 同向 and 四象 in ("老阳", "老阴") and 当前线段.右 is None:
                if (四象 == "老阳" and 当前虚线.低 < 当前线段.低) or (四象 == "老阴" and 当前虚线.高 > 当前线段.高):
                    序列 = 当前线段[:]
                    _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                    当前线段 = 线段序列[-1]
                    assert 当前线段.右 is not None
                    当前线段基础序列 = 当前线段.分割序列()[0]
                    当前线段基础序列.extend(序列)
                    当前线段[:] = 当前线段基础序列[:]
                    当前线段.刷新(配置)
                    continue

            if 配置.线段_非缺口下穿刺 and 四象 in ("小阳", "少阴") and 当前线段.右 is None:
                if 贯穿伤 := 当前线段.查找贯穿伤():
                    基础序列 = 当前线段[当前线段.index(贯穿伤) :]
                    if len(基础序列) == 4 and len(线段序列) >= 2:
                        左, 中, 右 = 基础序列[-3], 基础序列[-2], 基础序列[-1]
                        if 相对方向.分析(左.高, 左.低, 右.高, 右.低) is 当前线段.方向:
                            print(colored(f"[警告<{sys._getframe().f_lineno}, {层级}>]:", "yellow"), colored("线段.修复贯穿伤", "red"), 贯穿伤, 基础序列)  # 异常弹出
                            基础序列 = 当前线段[:]
                            _弹出线段(当前线段, f"{sys._getframe().f_lineno}, {层级}")
                            当前线段 = 线段序列[-1]
                            当前线段.右 = None
                            for 临时虚线 in 基础序列[基础序列.index(当前线段[-1]) + 1 :]:
                                当前线段.append(临时虚线)
                            当前线段.刷新(配置)
                            if 当前线段.右:
                                段 = 线段.新建([左, 中, 右])
                                _添加线段(段, f"{sys._getframe().f_lineno}, {层级}")
                                段.左 = 线段特征.新建([中], 段.方向)
                            continue

            if 当前线段.右 is not None:
                基础序列 = 当前线段.分割序列()[1]
                新段 = 线段.新建(基础序列)
                _添加线段(新段, f"{sys._getframe().f_lineno}, {层级}")
                if 四象 in ("老阴", "老阳"):
                    新段.前一缺口 = None
                if 新段[-1] is not 当前虚线:
                    if 新段[-1].之后是(当前虚线):
                        新段.append(当前虚线)
                        新段.刷新(配置)
                    else:
                        return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

                新段.刷新(配置)

        return None

    def _武终(self, 行号: int):
        if self.模式 != "文武":
            self.武斗(self[-1].武, 行号)

    def _验证序列(self, 序列: Sequence):
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
        if len(self) and len(self) % 2 == 0:
            self.pop()

    @classmethod
    def 扩展分析(cls, 虚线序列: List[Union["笔", "线段"]], 线段序列: List["线段"], 配置: 缠论配置) -> None:
        """
        即同级别分析
        将笔看成线段
        """
        if not 虚线序列:
            return None
        try:
            虚线序列[2]
        except IndexError:
            return None
        线段递归扩展分析 = 线段.扩展分析

        def _添加线段(待添加线段: "线段", 行号):
            if 线段序列 and not 线段序列[-1].之后是(待添加线段):
                raise ValueError(f"线段.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)

            待添加线段.模式 = "高低"
            待添加线段.标识 = f"扩展{待添加线段.标识}" if type(待添加线段[0]) is not 笔 else "扩展线段"
            if 线段序列:
                之前线段 = 线段序列[-1]
                待添加线段.序号 = 之前线段.序号 + 1

            线段序列.append(待添加线段)
            # print(f"线段._向序列中添加[{行号}]", 待添加线段)

        def _弹出线段(待弹出线段: "线段", 行号):
            if not 线段序列:
                return None

            if 线段序列[-1] is 待弹出线段:
                drop = 线段序列.pop()
                待弹出线段.有效性 = False
                # print(f"线段._从序列中删除[{行号}]", 待弹出线段)
                return drop
            raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

        if not 线段序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
                if 关系 not in (相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同):  # FIXME 此处为首个线段
                    continue

                段 = 线段.新建([左, 中, 右])
                _添加线段(段, sys._getframe().f_lineno)
                break

        # 检查线段元素
        if not 线段序列:
            return None

        当前线段 = 线段序列[-1]
        当前线段._验证序列(虚线序列)
        if len(当前线段) < 3:
            _弹出线段(当前线段, sys._getframe().f_lineno)
            return 线段递归扩展分析(虚线序列, 线段序列, 配置)

        if not 配置.扩展线段_当下分析:
            当前线段[:] = 当前线段[:3]
            当前线段._武终(sys._getframe().f_lineno)

        if 当前线段[-1].序号 + 3 > 虚线序列[-1].序号:
            return None

        序号 = 虚线序列.index(当前线段[-1]) + 1
        if 序号 >= len(虚线序列):
            return None
        for i in range(序号 + 1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            相对关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
            if 相对关系.是否缺口():
                当前线段.append(左)
                当前线段.append(中)
                当前线段._武终(sys._getframe().f_lineno)
                continue

            if 左 in 当前线段:
                continue

            段 = 线段.新建([左, 中, 右])
            _添加线段(段, sys._getframe().f_lineno)
            return 线段递归扩展分析(虚线序列, 线段序列, 配置)


class 中枢(list):
    __slots__ = ["序号", "标识", "级别", "周期", "支持延续", "支持扩张", "扩展序列", "扩展中枢序列", "第三买卖线", "本级_第三买卖线", "进入段"]

    def __init__(self, 序号: int, 标识: str, 级别: int, 基础序列: List[Union["笔", "线段"]]):
        super().__init__(基础序列[:3])
        self.标识: str = self.__class__.__name__
        self.序号: int = 序号
        self.标识: str = 标识
        self.级别: int = 级别
        self.周期 = 基础序列[0].周期
        self.扩展序列: List[Union["笔", "线段"]] = []  # FIXME 逢九变，以线段.扩展分析
        self.扩展中枢序列: List["中枢"] = []  # FIXME 高一级中枢
        self.第三买卖线: Optional[Union["笔", "线段"]] = None
        self.本级_第三买卖线: Optional[Union["笔", "线段"]] = None
        self.进入段: Optional[Union["笔", "线段"]] = None
        # self.离开段: Optional[Union["笔", "线段"]] = None

    def append(self, __object):
        super().append(__object)
        self.本级_第三买卖线 = None
        self.第三买卖线 = None

    def __str__(self):
        return f"{self.标识}({self.高}, {self.低}, 元素数量: {len(self)}, {self[0].文.时间戳} ===>>> {self[-1].武.时间戳})"

    def __repr__(self):
        return str(self)

    @property
    def 图表标题(self) -> str:
        return f"{self.文.右.标识}:{self.文.右.周期}:{getattr(self, '标识')}:{getattr(self, '序号', 0)}"

    @property
    def 离开段(self) -> Union["笔", "线段"]:
        return self[-1]

    @property
    def 完整性(self):
        """

        详情见 教你炒股票 43：有关背驰的补习课(2007-04-06 15:31:28)
        不完整时 下一个中枢大概率会与当前中枢发生扩展！

        """
        if type(self[0]) is not 线段:
            # 笔中枢
            return self.第三买卖线 is not None

        if type(self[0]) is 线段:
            # if self.本级_第三买卖线:
            #     return True
            线段内部中枢_实 = self[-1].合_中枢序列
            for 内部_实 in 线段内部中枢_实:
                if 相对方向.分析(self.高, self.低, 内部_实.高, 内部_实.低).是否缺口():
                    return True
        return False

    @property
    def 完整性_实(self):
        """

        详情见 教你炒股票 43：有关背驰的补习课(2007-04-06 15:31:28)
        不完整时 下一个中枢大概率会与当前中枢发生扩展！

        """
        if type(self[0]) is not 线段:
            # 笔中枢
            return self.第三买卖线 is not None

        if type(self[0]) is 线段:
            # if self.本级_第三买卖线:
            #     return True
            线段内部中枢_实 = self[-1].实_中枢序列
            for 内部_实 in 线段内部中枢_实:
                if 相对方向.分析(self.高, self.低, 内部_实.高, 内部_实.低).是否缺口():
                    return True
        return False

    @property
    def 方向(self) -> 相对方向:
        return self[0].方向.翻转()

    @property
    def 高(self) -> float:
        return min(self[:3], key=lambda o: o.高).高

    @property
    def 低(self) -> float:
        return max(self[:3], key=lambda o: o.低).低

    @property
    def 高高(self) -> float:
        if len(self) > 3:
            return max(self[:], key=lambda o: o.高).高
        return max(self, key=lambda o: o.高).高

    @property
    def 低低(self) -> float:
        if len(self) > 3:
            return min(self[:], key=lambda o: o.低).低
        return min(self, key=lambda o: o.低).低

    @property
    def 文(self) -> 分型:
        return self[0].文

    @property
    def 武(self) -> 分型:
        return self[-1].武

    def 获取序列(self) -> List[Union["笔", "线段"]]:
        序列: List = self[:]
        if self.第三买卖线 is not None:
            序列.append(self.第三买卖线)
        return 序列

    def 获取扩展中枢(self, 扩展中枢: List, 配置: 缠论配置):
        if len(self) >= 9:
            扩展线段 = []
            线段.扩展分析(self, 扩展线段, 配置)
            中枢.分析(扩展线段, 扩展中枢, False, f"{self.标识}_扩展中枢_")

    def 校验合法性(self, 序列: Sequence, 中枢序列) -> bool:
        有效序列 = self[:]
        无效序列 = []
        for 元素 in self:
            if 元素 not in 序列:
                无效序列.append(元素)

        if 无效序列:
            无效 = 无效序列[0]
            序号 = self.index(无效)
            有效序列 = self[:序号]

        if len(有效序列) < 3:
            self.第三买卖线 = None
            self.本级_第三买卖线 = None
            return False

        self[:] = 有效序列

        有效序列 = []
        for 元素 in self:
            if 相对方向.分析(self.高, self.低, 元素.高, 元素.低).是否缺口():
                break
            有效序列.append(元素)
        self[:] = 有效序列

        if len(self) < 3:
            return False

        for i in range(1, len(self)):
            前 = self[i - 1]
            后 = self[i]
            if not 前.之后是(后):
                return False

        if not 相对方向.分析(self[0].高, self[0].低, self[2].高, self[2].低).是否缺口():
            重叠高 = min(self[:3], key=lambda o: o.高).高
            重叠低 = max(self[:3], key=lambda o: o.低).低
            if 重叠低 > 重叠高:
                return False

        if self.第三买卖线 is not None:
            if self.第三买卖线 in 序列:
                if not self[-1].之后是(self.第三买卖线):
                    self.设置第三买卖线(None)
                    getattr(中枢序列, "尾部刷新", Nil)(行号=sys._getframe().f_lineno)
                else:
                    if not 相对方向.分析(self.高, self.低, self.第三买卖线.高, self.第三买卖线.低).是否缺口():
                        self.append(self.第三买卖线)
                        self.设置第三买卖线(None)
                        getattr(中枢序列, "尾部刷新", Nil)(行号=sys._getframe().f_lineno)

            else:
                self.设置第三买卖线(None)
                getattr(中枢序列, "尾部刷新", Nil)(行号=sys._getframe().f_lineno)
        return True

    def 设置第三买卖线(self, 线: Union[笔, 线段, None]):
        self.第三买卖线 = 线

    def 当前状态(self):
        """
        详情见 教你炒股票 49：利润率最大的操作模式(2007-04-26 08:16:56)
        当前中枢最后一段所处的位置关系

        一、当下在该中枢之中。
            因为在中枢里，由于这时候怎么演化都是对的，不操作是最好的操作，等待其演化第二、三类，
            当然，如果你技术好点，可以判断出次级别的第二类买点，这些买点很多情况下都是在中枢中出现的，那当然也是可以参与的。
            但如果没有这种技术，那就有了再说了。只把握你自己当下技术水平能把握的机会，这才是最重要的。
        二、当下在该中枢之下。
            1.当下之前未出现该中枢第三类卖点。
            2.当下之前已出现该中枢第三类卖点（正出现也包括在这种情况下，按最严格的定义，这最精确的卖点，是瞬间完成的，而具有操作意义的第三类卖点，其实是一个包含该最精确卖点的足够小区间）
        三、当下在该中枢之上。
            1.当下之前未出现该中枢第三类买点。
            2.当下之前已出现该中枢第三类买点。
        """
        状态 = "中枢之中"
        尾部 = self[-1].武
        if type(self[-1]) is 线段:
            尾部 = self[-1][-1].武
        关系 = 相对方向.分析(self.高, self.低, 尾部.高, 尾部.低)
        if 关系 is 相对方向.向上缺口:
            状态 = "中枢之上"
        elif 关系 is 相对方向.向下缺口:
            状态 = "中枢之下"

        return 状态

    @classmethod
    def 基础检查(cls, 左: Union["笔", "线段"], 中: Union["笔", "线段"], 右: Union["笔", "线段"]) -> bool:
        if not 左.之后是(中):
            return False
        if not 中.之后是(右):
            return False
        """
        if not 相对方向.分析(左.高, 左.低, 中.高, 中.低).是否包含():
            return False
        if not 相对方向.分析(中.高, 中.低, 右.高, 右.低).是否包含():
            return False
        """

        return 相对方向.分析(左.高, 左.低, 右.高, 右.低) in (相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同)

    @classmethod
    def 创建(cls, 左: Union["笔", "线段"], 中: Union["笔", "线段"], 右: Union["笔", "线段"], 级别: int, 标识: str = "") -> "中枢":
        assert 中枢.基础检查(左, 中, 右)
        return 中枢(
            序号=0,
            标识=f"{标识}中枢<{中.标识}>",
            基础序列=[左, 中, 右],
            级别=级别,
        )

    @classmethod
    def 从序列中获取中枢(cls, 虚线序列: List[Union["笔", "线段"]], 起始方向: 相对方向, 标识: str) -> Optional["中枢"]:
        if len(虚线序列) < 3:
            return None

        for i in range(1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            if 中枢.基础检查(左, 中, 右):
                if 左.方向 is 起始方向:
                    return 中枢.创建(左, 中, 右, 级别=0, 标识=标识)

        return None

    @classmethod
    def 分析(cls, 虚线序列: List[Union["笔", "线段"]], 中枢序列: List["中枢"], 跳过首部: bool = True, 标识: str = "", 层级: int = 0) -> None:
        if not 虚线序列:
            return None

        中枢递归分析 = 中枢.分析

        def 向中枢序列尾部添加(待添加中枢: "中枢"):
            if 中枢序列:
                待添加中枢.序号 = 中枢序列[-1].序号 + 1
                if 中枢序列[-1].获取序列()[-1].序号 > 待添加中枢.获取序列()[-1].序号:
                    raise ValueError()
            中枢序列.append(待添加中枢)

        def 从中枢序列尾部弹出(待弹出中枢: "中枢") -> Optional["中枢"]:
            if not 中枢序列:
                return None
            if 中枢序列[-1] is 待弹出中枢:
                return 中枢序列.pop()
            return None

        if not 中枢序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                if 中枢.基础检查(左, 中, 右):
                    新中枢 = 中枢.创建(左, 中, 右, 中.级别, 标识)
                    序号 = 虚线序列.index(左)
                    if 跳过首部 and (左.序号 == 0 or 序号 == 0):
                        continue  # 方便计算走势
                    if 序号 >= 2:
                        同向相对关系 = 相对方向.分析(虚线序列[序号 - 2].高, 虚线序列[序号 - 2].低, 左.高, 左.低)
                        if 同向相对关系.是否向上() and 左.方向.是否向上():
                            continue
                        if 同向相对关系.是否向下() and 左.方向.是否向下():
                            continue

                    向中枢序列尾部添加(新中枢)
                    return 中枢递归分析(虚线序列, 中枢序列, 跳过首部, 标识, 层级 + 1)

            return None

        当前中枢 = 中枢序列[-1]

        if not 当前中枢.校验合法性(虚线序列, 中枢序列):
            从中枢序列尾部弹出(当前中枢)
            return 中枢递归分析(虚线序列, 中枢序列, 跳过首部, 标识, 层级 + 1)

        序号 = 虚线序列.index(当前中枢[-1]) + 1

        基础序列 = []
        for 当前虚线 in 虚线序列[序号:]:
            if 相对方向.分析(当前中枢.高, 当前中枢.低, 当前虚线.高, 当前虚线.低).是否缺口():
                基础序列.append(当前虚线)
                if 当前中枢[-1].之后是(当前虚线):
                    当前中枢.设置第三买卖线(当前虚线)
                    getattr(中枢序列, "尾部刷新", Nil)(行号=sys._getframe().f_lineno)
                else:
                    ...
            else:
                if not 基础序列:
                    assert 当前中枢[-1].之后是(当前虚线), (当前中枢[-1], 当前虚线)
                    当前中枢.append(当前虚线)
                else:
                    基础序列.append(当前虚线)

            while len(基础序列) >= 3:
                新中枢 = 中枢.从序列中获取中枢(基础序列[:], 当前中枢[-1].方向.翻转(), 标识)
                if 新中枢 is None:
                    基础序列.pop(0)
                else:
                    """方向 = 相对方向.分析(当前中枢.高, 当前中枢.低, 新中枢.高, 新中枢.低)
                    if 方向.是否向上():
                        if 基础序列[0].方向 == 相对方向.向上:
                            基础序列.pop(0)
                            continue
                    elif 方向.是否向下():
                        if 基础序列[0].方向 == 相对方向.向下:
                            基础序列.pop(0)
                            continue
                    else:
                        print(colored(f"{方向}", "red"))"""

                    向中枢序列尾部添加(新中枢)
                    当前中枢 = 新中枢
                    基础序列 = []
        return None


@final
class _图表配色:
    配色表 = {
        "笔": "#6C4D7E",
        "线段": "#FEC187",
        "线段<线段>": "#8F6048",  # 以线段为基础的特征序列线段
        "扩展线段": "#09a4ff",  # 以笔为基础的
        "扩展线段<线段>": "#07d59e",  # 以线段为基础的
        "扩展线段<扩展线段>": "#ff29e3",
        "扩展线段<扩展线段<线段>>": "#07d59e",
    }
    笔: str = "#6C4D7E"
    线段: str = "#FEC187"
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
    def 点(cls, 对象: 买卖点, 命令: 指令, 基线: List[缠论K线]):

        message = dict()
        # return message
        message["标识"] = 对象.标识 if hasattr(对象, "标识") else 对象.__class__.__name__

        message["type"] = "shape"
        message["cmd"] = str(命令)
        message["id"] = str(id(对象))
        message["name"] = "arrow_down" if 对象.类型.是卖点 else "arrow_up"
        message["points"] = [{"time": int(对象.买卖点K线.时间戳.timestamp()), "price": 对象.买卖点K线.分型特征值}]

        arrowColor = "#FF2800" if 对象.类型.是卖点 else "#00FF22"
        text = f"{str(对象.偏移)}, {对象.破位值}, {对象.备注}"
        if 对象.失效偏移 > -1:
            arrowColor = 图表配色.灰色
            text = f"{str(对象.偏移)}, {对象.破位值}, {对象.备注}, {str(对象.失效K线.时间戳)}"
            if 对象.类型.是卖点:
                message["points"][0]["price"] = message["points"][0]["price"] * 1.01
            else:
                message["points"][0]["price"] = message["points"][0]["price"] * 0.99
        message["options"] = {
            "shape": "arrow_down" if 对象.类型.是卖点 else "arrow_up",
            "text": text,
        }
        message["properties"] = {
            "color": cls.invert_alpha("#CC62FF"),
            "arrowColor": arrowColor,
            "text": text,
            "title": 对象.备注.split("_")[0],
            "showLabel": False,
        }

        return message

    @classmethod
    def 线(cls, 对象: Union[笔, 线段, 线段特征], 命令: 指令, 周期: int, 基线: List[缠论K线]):
        linewidths = {"笔": 1, "线段": 2, "走势": 3, "线段特征": 2}
        标识 = 对象.图表标题
        message = dict()
        message["type"] = "shape"
        message["cmd"] = 命令.指令.upper()
        message["id"] = 标识
        message["name"] = "trend_line"
        if 命令.指令 == 指令.删:
            return message
        message["options"] = {"shape": "trend_line", "text": 对象.标识}

        message["points"] = [
            {"time": int(缠论K线.时间戳对齐(基线, 对象.文.中).timestamp()), "price": 对象.文.分型特征值},
            {"time": int(缠论K线.时间戳对齐(基线, 对象.武.中).timestamp()), "price": 对象.武.分型特征值},
        ]

        message["properties"] = {
            "bold": True,
            "textcolor": cls.invert_alpha("#000000"),
            "linecolor": cls.配色表.get(对象.标识, cls.笔),
            "linewidth": linewidths.get(对象.标识, 2),
            "title": 标识,
            "showLabel": False,
            "visible": True,
        }
        信息流 = [
            对象.标识,
            str(对象.序号),
        ]
        if type(对象) is 笔:
            对象: 笔 = 对象
            信息流.extend(
                [
                    f"周期:{周期}",
                    # f"{买卖点.买卖意义(对象) if hasattr(买卖点, '买卖意义') else None}",
                    # f"均值:{对象.武之MACD均值}, 极值:{对象.武之MACD极值} 分型:{对象.武.与MACD柱子分型匹配}, MACD匹配:{对象.武.中.与MACD柱子匹配}",
                    # f"背驰过:{len(买卖点.笔是否背驰过(对象)) != 0 if hasattr(买卖点, '笔是否背驰过') else None}",
                    # f"振幅强弱:{对象.振幅强弱(对象.观察员.笔序列)}",
                    # f"幅度强弱:{对象.幅度强弱(对象.观察员.笔序列)}",
                    # f"分型强弱:{对象.武.强度}",
                ]
            )

        if 对象.标识 in ("线段", "线段<线段>"):
            对象: 线段 = 对象
            信息流.extend(
                [
                    f"周期:{周期}",
                    对象.四象,
                    f"{对象.特征序列状态}",
                    str(对象.级别),
                    # str(买卖点.判断线段内部是否背驰(对象) if hasattr(买卖点, "判断线段内部是否背驰") else None),
                    f"内部中枢数量:{len(对象.实_中枢序列)}",
                ]
            )
            if 对象.确认K线 is not None:
                信息流.append(f"{对象.确认K线.时间戳.strftime('%Y-%m-%d %H:%M:%S')} 特征值: {str(对象.确认K线.分型特征值)}")

        elif 对象.标识 in ("扩展线段", "扩展线段<线段>"):
            信息流.extend(
                [
                    f"周期:{周期}",
                    str(对象.级别),
                ]
            )
            message["properties"]["text"] = " ".join(信息流)

        if type(对象) is 线段特征:
            message["properties"].update({"linecolor": "#F1C40F" if 对象.方向 is 相对方向.向下 else "#fbc02d", "linewidth": 4, "linestyle": 1})

        message["properties"]["text"] = " ".join(信息流)
        return message

    @classmethod
    def 面(cls, 对象: 中枢, 命令: 指令, 周期: int, 基线: List[缠论K线]):
        linewidths = {"笔": 1, "线段": 2, "走势": 3}
        标识 = 对象.图表标题
        message = dict()
        message["type"] = "shape"
        message["cmd"] = str(命令)
        message["id"] = 标识
        message["name"] = "rectangle"
        if 命令.指令 == 指令.删:
            return message
        message["options"] = {"shape": "rectangle", "text": 对象.标识}
        message["properties"] = {
            "title": 标识,
            "visible": True,
        }

        武_时间戳 = int(缠论K线.时间戳对齐(基线, 对象.第三买卖线.武.中).timestamp()) if 对象.第三买卖线 else int(缠论K线.时间戳对齐(基线, 对象.武.中).timestamp())
        if type(对象[0]) is 线段 and 对象.本级_第三买卖线 is not None:
            武_时间戳 = int(缠论K线.时间戳对齐(基线, 对象.本级_第三买卖线.武.中).timestamp())
        extendRight = False  # if 对象.第三买卖线 else True
        points = [
            {"time": int(对象.文.时间戳.timestamp()), "price": 对象.高},
            {
                "time": 武_时间戳,
                "price": 对象.低,
            },
        ]
        text = f"{对象.标识} {对象.序号} 周期: {周期}, 数量: {len(对象)} "
        if 对象.第三买卖线:
            text += f"第三卖点值: {对象.第三买卖线.武.分型特征值}, "
        message["properties"].update(
            {
                "backgroundColor": "rgba(242, 54, 69, 0.2)" if 对象.方向 is 相对方向.向下 else "rgba(76, 175, 80, 0.2)",  # 上下上 为 红色，反之为 绿色
                "color": cls.配色表.get(对象[0].标识, cls.笔),
                "linewidth": linewidths.get(对象[0].__class__.__name__, 2),
                "text": text,
                "textColor": cls.invert_alpha("rgba(156, 39, 176, 1)"),
                "horzLabelsAlign": "left",
                "vertLabelsAlign": "bottom",
                "showLabel": False,
                "extendRight": extendRight,
            }
        )

        message["points"] = points

        return message


图表配色 = _图表配色()


class 观察者:
    # thread: Any = None
    # queue: Any = asyncio.Queue()
    当前事件循环: Any = None if __name__ == "__main__" else asyncio.get_event_loop()
    延迟时间: float = 0.01

    def __init__(self, 符号: str, 周期: int, 数据通道: Optional[WebSocket], 配置: 缠论配置, 数据队列: Optional[queue.Queue] = None):
        配置.标识 = 符号
        self.符号: str = 符号
        self.周期: int = int(周期)
        self.配置: 缠论配置 = 配置
        self.数据通道: Optional[Any] = 数据通道  # WebSocket
        self.数据队列: queue.Queue = 数据队列

        self._重置基础序列()

    @property
    def 标识(self) -> str:
        return f"{self.符号}:{self.周期}"

    @property
    def 当前K线(self) -> Optional["K线"]:
        return self.普通K线序列[-1] if len(self.普通K线序列) else None

    @property
    def 当前缠K(self) -> Optional["缠论K线"]:
        return self.缠论K线序列[-1] if len(self.缠论K线序列) else None

    def _重置基础序列(self):
        self.买卖点字典 = dict()
        self.基础缠K序列: List[缠论K线] = []
        self.缓存: Dict[str, Any] = dict()

        self.普通K线序列: List[K线] = []
        self.缠论K线序列: List[缠论K线] = []

        self.分型序列: List[分型] = []

        self.笔序列: List[笔] = 图表展示序列(self) if self.配置.推送笔 else []
        self.笔_中枢序列: List[中枢] = 图表展示序列(self) if self.配置.推送中枢 else []

        self.线段序列: List[线段] = 图表展示序列(self) if self.配置.推送线段 else []
        self.中枢序列: List[中枢] = 图表展示序列(self) if self.配置.推送中枢 else []

        self.扩展线段序列: List[线段] = 图表展示序列(self) if self.配置.推送线段 else []
        self.扩展中枢序列: List[中枢] = 图表展示序列(self) if self.配置.推送中枢 else []

        self.扩展线段序列_线段: List[线段] = 图表展示序列(self) if self.配置.推送线段 else []
        self.扩展中枢序列_线段: List[中枢] = 图表展示序列(self) if self.配置.推送中枢 else []

        self.线段_线段序列: List[线段] = 图表展示序列(self) if self.配置.推送线段 else []
        self.线段_中枢序列: List[中枢] = 图表展示序列(self) if self.配置.推送中枢 else []

        self.扩展线段序列_扩展线段: List[线段] = 图表展示序列(self) if self.配置.推送线段 else []
        self.扩展中枢序列_扩展线段: List[中枢] = 图表展示序列(self) if self.配置.推送中枢 else []

    @final
    def 增加原始K线(self, 普K: K线):
        if 普K.时间戳 > 转化为时间戳("2026-04-17 04:05:33"):
            pass  # raise RuntimeError("手动终止")
        try:
            self.__处理数据(普K)
        except Exception as e:
            路径 = f"./templates/{self.符号}_err-{self.周期}-{int(self.普通K线序列[0].时间戳.timestamp())}-{int(self.普通K线序列[-1].时间戳.timestamp())}"
            K线.保存到DAT文件(
                路径 + ".nb",
                self.普通K线序列,
            )
            self.配置.保存配置(路径 + ".json")

            with open(路径 + ".log", "w") as f:
                f.write(收集异常信息(e))

            traceback.print_exc()
            print(f"K线数据已保存在: {路径}.nb")
            print(f"当前配置已保存在: {路径}.json")
            print(f"详细错误信息已保存在: {路径}.log")
            raise e

    def __处理数据(self, 普K: K线):
        状态, 当前分型 = 缠论K线.分析(普K, self.缠论K线序列, self.普通K线序列, self.配置)
        self.数据队列 and self.数据队列.put((普K.时间戳, 普K.开盘价, 普K.高, 普K.低, 普K.收盘价, 普K.成交量, 0))
        if 当前分型 is None:
            return

        if self.配置.推送K线:
            self.报信(普K, 指令.添加("RawBar"), sys._getframe().f_lineno, 周期=普K.周期)

        if self.数据通道 is not None and self.配置.图表展示:
            time.sleep(self.延迟时间)

        之前分型 = self.缓存.get("之前分型")
        if 之前分型:
            相等 = 之前分型 == 当前分型
            相同 = 之前分型 is 当前分型
            if 相同 and not 相等:
                print("分型相等但不相同")
            if 相同 or 相等:
                return

        self.缓存["之前分型"] = 当前分型

        self.配置.分析笔 and 笔.分析(当前分型, self.分型序列, self.笔序列, self.缠论K线序列, 0, self.配置)
        if not self.分型序列:
            return

        self.配置.分析笔中枢 and 中枢.分析(self.笔序列, self.笔_中枢序列)

        self.配置.分析线段 and 线段.分析(self.笔序列, self.线段序列, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.线段序列, self.中枢序列)

        self.配置.分析扩展线段 and 线段.扩展分析(self.笔序列, self.扩展线段序列, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列, self.扩展中枢序列)

        self.配置.分析扩展线段 and 线段.扩展分析(self.线段序列, self.扩展线段序列_线段, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列_线段, self.扩展中枢序列_线段)

        self.配置.分析线段 and 线段.分析(self.线段序列, self.线段_线段序列, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.线段_线段序列, self.线段_中枢序列)

        self.配置.分析扩展线段 and 线段.扩展分析(self.扩展线段序列, self.扩展线段序列_扩展线段, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列_扩展线段, self.扩展中枢序列_扩展线段)

        try:
            self.识别买卖点()
        except:
            print("~~~~~~~~~~~~~~", self.当前K线)
            traceback.print_exc()

    def 分部分析(self):
        for i in range(1, len(self.缠论K线序列) - 1):
            当前分型 = 分型(self.缠论K线序列[i - 1], self.缠论K线序列[i], self.缠论K线序列[i + 1])
            笔.分析(当前分型, self.分型序列, self.笔序列, self.缠论K线序列, 0, self.配置)

        self.配置.分析笔中枢 and 中枢.分析(self.笔序列, self.笔_中枢序列)

        self.配置.分析线段 and 线段.分析(self.笔序列, self.线段序列, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.线段序列, self.中枢序列)

        self.配置.分析扩展线段 and 线段.扩展分析(self.笔序列, self.扩展线段序列, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列, self.扩展中枢序列)

        self.配置.分析扩展线段 and 线段.扩展分析(self.线段序列, self.扩展线段序列_线段, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列_线段, self.扩展中枢序列_线段)

        self.配置.分析线段 and 线段.分析(self.线段序列, self.线段_线段序列, self.配置)
        self.配置.分析线段中枢 and 中枢.分析(self.线段_线段序列, self.线段_中枢序列)

    def 识别买卖点(self):
        """
        简单买卖策略
        """
        if not self.笔序列:
            return
        if self.分型序列[-1].中.序号 + 2 < self.当前缠K.序号:
            return
        if self.分型序列[-1].强度 not in "强中":
            return
        if len(self.笔序列) >= 3 and self.线段序列 and self.笔序列[-1].武 is self.线段序列[-1].武 and self.线段序列[-1].实_中枢序列:
            进入段, 离开段 = self.笔序列[-3], self.笔序列[-1]
            方向 = 相对方向.分析(进入段.高, 进入段.低, 离开段.高, 离开段.低)
            if 方向 is 相对方向.向上:
                if 背驰分析.测度背驰(进入段, 离开段):
                    self.添加买卖点("3笔", 离开段.武, "一", "次级")

            elif 方向 is 相对方向.向下:
                if 背驰分析.测度背驰(进入段, 离开段):
                    self.添加买卖点("3笔", 离开段.武, "一", "次级")

    @final
    def 添加买卖点(self, 特征: str, 买卖点分型: 分型, 序号: str, 级别: str):
        当前买卖点: 买卖点 = 买卖点.生成买卖点(特征, 序号, 级别, 买卖点分型, self.当前缠K)
        if "事后" in 特征:
            当前买卖点.失效K线 = self.当前缠K
        偏移 = self.配置.买卖点偏移
        if 当前买卖点.偏移 > 偏移 and "事后" not in 特征:
            return

        买卖点序列 = self.买卖点字典.get(特征, set())
        self.买卖点字典[特征] = 买卖点序列
        活跃序列 = [点 for 点 in 买卖点序列 if 点.失效K线 is None]
        活跃时间戳序列 = [点.买卖点K线.时间戳 for 点 in 活跃序列]

        if self.配置.买卖点与MACD柱强相关 and not 买卖点分型.中.与MACD柱子匹配:
            return
        分型匹配 = 买卖点分型.与MACD柱子分型匹配
        柱子匹配 = 买卖点分型.中.与MACD柱子匹配

        rsi匹配 = 买卖点分型.中.与RSI匹配
        kdj匹配 = 买卖点分型.中.与KDJ匹配

        当前买卖点.备注 = 当前买卖点.备注 + f"_{买卖点分型.强度}"
        if 分型匹配 is not None and not 分型匹配:
            当前买卖点.备注 = 当前买卖点.备注 + "_非MACD分型"

        if not 柱子匹配:
            当前买卖点.备注 = 当前买卖点.备注 + "_非普K柱子匹配"

        if rsi匹配 is not None and not rsi匹配:
            当前买卖点.备注 = 当前买卖点.备注 + "_非RSI匹配"

        if kdj匹配 is not None and not kdj匹配:
            当前买卖点.备注 = 当前买卖点.备注 + "_非KDJ匹配"

        if not self.配置.买卖点激进识别 and not 买卖点分型.右:
            return

        if 当前买卖点.买卖点K线.时间戳 not in 活跃时间戳序列:
            买卖点序列.add(当前买卖点)
            # 当前买卖点.买卖点K线.买卖点信息.add(当前买卖点.备注)
            self.报信(当前买卖点, 指令.添加(当前买卖点.备注), sys._getframe().f_lineno)

    def 图表刷新(self):
        for key in dir(self):
            if "序列" in key:
                getattr(getattr(self, key), "尾部刷新", Nil)(行号=-1)

    def 定位K线所在(self, k线: K线):
        return self.定位时间戳所在(k线.时间戳)

    def 定位时间戳所在(self, 时间戳: datetime):
        筆 = []
        段 = []
        段中枢 = []
        笔中枢 = []
        for 某笔 in self.笔序列:
            (某笔.文.中.时间戳.timestamp() <= 时间戳.timestamp() <= 某笔.武.中.时间戳.timestamp()) and 筆.append(某笔)  # 不考虑超越尾部

        for 某段 in self.线段序列:
            (某段.文.中.时间戳.timestamp() <= 时间戳.timestamp() <= 某段.武.中.时间戳.timestamp()) and 段.append(某段)

        if 段:
            for 某中枢 in self.中枢序列:
                for 某段 in 段:
                    某段 in 某中枢 and 某中枢 not in 段中枢 and 段中枢.append(某中枢)

        if 筆:
            for 某中枢 in self.笔_中枢序列:
                for 某笔 in 筆:
                    某笔 in 某中枢 and 某中枢 not in 笔中枢 and 笔中枢.append(某中枢)

        return 筆, 段, 中枢, 笔中枢

    def 报信(self, 对象: Any, 命令: 指令, 行号, **kwargs) -> None:
        if self.数据通道 is None or not self.配置.图表展示:
            return

        message = dict()

        if type(对象) is K线:
            message["type"] = "realtime"
            message["timestamp"] = str(对象.时间戳)
            message["open"] = 对象.开盘价
            message["high"] = 对象.高
            message["low"] = 对象.低
            message["close"] = 对象.收盘价
            message["volume"] = 对象.成交量

        if type(对象) is 买卖点:
            message.update(图表配色.点(对象, 命令, self.基础缠K序列))

        if type(对象) is 笔 and self.配置.推送笔:
            message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))

        if type(对象) is 线段 and self.配置.推送线段:
            if 对象.标识 == "线段" and self.配置.图表展示_线段:
                message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "扩展线段" and self.配置.图表展示_扩展线段:
                message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "扩展线段<线段>" and self.配置.图表展示_扩展线段_线段:
                message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "线段<线段>" and self.配置.图表展示_线段_线段:
                message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))

            if 对象.标识 == "扩展线段<扩展线段>" and self.配置.图表展示_扩展线段_线段:
                message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))

        if type(对象) is 线段特征:
            message.update(图表配色.线(对象, 命令, self.周期, self.基础缠K序列))

        if type(对象) is 中枢 and self.配置.推送中枢:
            if 对象.标识 == "中枢<笔>" and self.配置.图表展示_中枢_笔:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "中枢<线段>" and self.配置.图表展示_中枢_线段:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "中枢<扩展线段>" and self.配置.图表展示_中枢_扩展线段:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "中枢<扩展线段<线段>>" and self.配置.图表展示_中枢_扩展线段_线段:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))
            if 对象.标识 == "中枢<线段<线段>>" and self.配置.图表展示_中枢_线段_线段:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))

            if 对象.标识 == "中枢<扩展线段<扩展线段>>" and self.配置.图表展示_扩展线段_线段:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))

            if "_" in 对象.标识 and self.配置.图表展示_中枢_线段内部:
                message.update(图表配色.面(对象, 命令, self.周期, self.基础缠K序列))

        if len(message) < 3:
            return

        if self.数据通道 is not None and self.配置.图表展示 and self.数据通道.client_state.value == 1:
            asyncio.set_event_loop(self.当前事件循环)
            asyncio.ensure_future(self.数据通道.send_text(json.dumps(message)))
        return

    def 加载本地数据(self, 文件路径: str):
        self._重置基础序列()
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], self.周期)
                self.增加原始K线(k线)

    def 读取任意数据(self, 魔法, **魔法参数):
        魔法(**魔法参数)
        return self

    def 获取分型强度(self):
        分型统计 = dict()
        for fx in self.分型序列:
            关系组 = fx.关系组
            N = 分型统计.get(关系组, 0)
            分型统计[关系组] = N + 1
        return 分型统计

    @classmethod
    def 读取数据文件(cls, 文件路径: str, ws=None, 配置=缠论配置()) -> Self:
        # btcusd-300-1631772074-1632222374.nb
        name = Path(文件路径).name.split(".")[0]
        符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
        实例 = cls(符号=符号, 周期=int(周期), 数据通道=ws, 配置=配置)
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], int(周期))
                实例.增加原始K线(k线)

        return 实例


class 立体分析器:
    def __init__(self, 符号: str, 周期组: List[int], 数据通道: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置()):
        self.周期组 = 周期组

        self.__输入周期 = self.周期组[0]  # 最小输入K线周期
        self.__显示周期 = self.周期组[1]
        self._K线合成器 = K线合成器(符号, self.周期组, self.__K线回调)

        self._单体分析器 = dict()
        for 周期 in self.周期组:
            当前配置 = 配置.model_copy(
                update={
                    "推送K线": False,
                    # "推送笔": False,
                    "推送线段": False,
                    # "图表展示": False,
                },
                deep=True,
            )
            self._单体分析器[周期] = 观察者(符号=符号, 周期=周期, 数据通道=数据通道, 配置=当前配置)

        # self._单体分析器[self.__显示周期].上级缠K序列 = self._单体分析器[self.周期组[1]].缠论K线序列
        self._单体分析器[self.__显示周期].配置.推送K线 = True
        self._单体分析器[self.__显示周期].配置.推送笔 = True
        self._单体分析器[self.__显示周期].配置.推送线段 = True
        self._单体分析器[self.__显示周期].配置.图表展示 = True
        self._单体分析器[self.__显示周期]._重置基础序列()

        for 周期 in self.周期组:  # 将不同周期对其至显示周期
            if 周期 != self.__显示周期:
                self._单体分析器[周期].基础缠K序列 = self._单体分析器[self.__显示周期].缠论K线序列

    def 投喂K线(self, 普K: K线):
        if 普K.周期 != self.__输入周期:
            raise RuntimeError("立体分析器.投喂K线", 普K.周期, self.__输入周期)
        self._K线合成器.投喂K线(普K)

    def __K线回调(self, 信号: Dict):
        周期 = 信号["周期"]
        k线 = 信号["K线数据"]  # FIXME K线完成信号的滞后性，
        self._单体分析器[周期].增加原始K线(k线)
        if 当前K线 := self._K线合成器.获取当前K线(周期):
            self._单体分析器[周期].增加原始K线(当前K线)

    def 报信(self, 对象: Any, 命令: 指令, 行号) -> None:
        if self.数据通道 is None or not self.配置.图表展示:
            return

        message = dict()

        if type(对象) is K线:
            message["type"] = "realtime"
            message["timestamp"] = str(对象.时间戳)
            message["open"] = 对象.开盘价
            message["high"] = 对象.高
            message["low"] = 对象.低
            message["close"] = 对象.收盘价
            message["volume"] = 对象.成交量

        if type(对象) is 买卖点:
            message.update(图表配色.点(对象, 命令))

        if type(对象) is 笔 and self.配置.推送笔:
            message.update(图表配色.线(对象, 命令, self.周期))

        if type(对象) is 线段 and self.配置.推送线段:
            if 对象.标识 == "线段" and self.配置.图表展示_线段:
                message.update(图表配色.线(对象, 命令, self.周期))
            if 对象.标识 == "扩展线段" and self.配置.图表展示_扩展线段:
                message.update(图表配色.线(对象, 命令, self.周期))
            if 对象.标识 == "扩展线段<线段>" and self.配置.图表展示_扩展线段_线段:
                message.update(图表配色.线(对象, 命令, self.周期))
            if 对象.标识 == "线段<线段>" and self.配置.图表展示_线段_线段:
                message.update(图表配色.线(对象, 命令, self.周期))

            if 对象.标识 == "扩展线段<扩展线段>" and self.配置.图表展示_扩展线段_线段:
                message.update(图表配色.线(对象, 命令, self.周期))

        if type(对象) is 线段特征:
            message.update(图表配色.线(对象, 命令, self.周期))

        if type(对象) is 中枢 and self.配置.推送中枢:
            if 对象.标识 == "中枢<笔>" and self.配置.图表展示_中枢_笔:
                message.update(图表配色.面(对象, 命令, self.周期))
            if 对象.标识 == "中枢<线段>" and self.配置.图表展示_中枢_线段:
                message.update(图表配色.面(对象, 命令, self.周期))
            if 对象.标识 == "中枢<扩展线段>" and self.配置.图表展示_中枢_扩展线段:
                message.update(图表配色.面(对象, 命令, self.周期))
            if 对象.标识 == "中枢<扩展线段<线段>>" and self.配置.图表展示_中枢_扩展线段_线段:
                message.update(图表配色.面(对象, 命令, self.周期))
            if 对象.标识 == "中枢<线段<线段>>" and self.配置.图表展示_中枢_线段_线段:
                message.update(图表配色.面(对象, 命令, self.周期))

            if 对象.标识 == "中枢<扩展线段<扩展线段>>" and self.配置.图表展示_扩展线段_线段:
                message.update(图表配色.面(对象, 命令, self.周期))

            if "_" in 对象.标识 and self.配置.图表展示_中枢_线段内部:
                message.update(图表配色.面(对象, 命令, self.周期))

        if len(message) < 3:
            return

        if self.数据通道 is not None and self.配置.图表展示 and self.数据通道.client_state.value == 1:
            asyncio.set_event_loop(self.当前事件循环)
            asyncio.ensure_future(self.数据通道.send_text(json.dumps(message)))
        return


class Bitstamp(观察者):
    def __init__(self, 符号: str, 周期: int, 数据通道: WebSocket, 配置: 缠论配置):
        super().__init__(符号=符号, 周期=周期, 数据通道=数据通道, 配置=配置)

    def init(self, size):
        left_date_timestamp = int(datetime.now().timestamp() * 1000)
        left = int(left_date_timestamp / 1000) - self.周期 * size
        if left < 0:
            raise RuntimeError
        _next = left
        while 1:
            data = self.ohlc(self.符号, self.周期, _next, _next := _next + self.周期 * 1000)
            if not data.get("data"):
                print(data)
                raise ValueError("")
            for bar in data["data"]["ohlc"]:
                K = K线.创建普K(
                    "no",
                    转化为时间戳(int(bar["timestamp"])),
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
        # print(折线)
        K线.保存到DAT文件(
            f"./templates/{self.符号}-{self.周期}-{int(self.普通K线序列[0].时间戳.timestamp())}-{int(self.普通K线序列[-1].时间戳.timestamp())}.nb",
            self.普通K线序列,
        )
        K线.保存到DAT文件(
            "./templates/last.nb",
            self.普通K线序列,
        )

    @staticmethod
    def 获取K线数据(数量: int, 符号: str, 周期: int, obj):
        end_ts = int(datetime.now().timestamp())
        left = end_ts - 周期 * 数量
        if left < 0:
            raise RuntimeError
        _next = left
        while 1:
            data = Bitstamp.ohlc(符号, 周期, _next, _next := _next + 周期 * 1000)
            if not data.get("data"):
                print(data)
                raise ValueError
            for bar in data["data"]["ohlc"]:
                K = K线.创建普K(
                    符号,
                    转化为时间戳(int(bar["timestamp"])),
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
    def ohlc(pair: str, step: int, start: int, end: int, length: int = 1000, retries: int = 3) -> Dict:
        """执行HTTP请求，带重试机制"""
        url = f"https://www.bitstamp.net/api/v2/ohlc/{pair}/"
        session = requests.Session()
        session.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
            # "content-type": "application/json",
        }
        """proxies = {
            "http": "http://127.0.0.1:10808",
            "https": "http://127.0.0.1:10808",
        }"""

        params = {"step": step, "limit": length, "start": start, "end": end}

        for attempt in range(retries):
            try:
                # resp = session.get(url, params=params, timeout=10, proxies=proxies)
                resp = session.get(url, params=params, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"请求失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2**attempt)  # 指数退避


class 自定义实时数据源(bt.feed.DataBase):
    """
    一个用于模拟实时数据推送的数据源，继承自Backtrader的DataBase。
    在实际应用中，你需要将“模拟生成数据”的部分，替换为接收WebSocket等推送数据的代码。
    """

    def __init__(self, 数据队列: queue.Queue, 观察员: 观察者, 魔法, **魔法参数):
        # 调用父类初始化方法
        super(自定义实时数据源, self).__init__()
        # 存储外部传入的数据队列，用于接收实时数据
        self.数据队列 = 数据队列
        # 定义一个标志，用于控制数据加载的停止
        self.正在运行 = False
        self.观察员 = 观察员
        self.魔法 = 魔法
        self.__魔法参数 = 魔法参数
        self.已有数据 = False

    def start(self):
        """
        数据源开始工作时的初始化操作。
        这里可以不执行任何操作，或者启动数据接收线程等。
        """
        print(f"[{datetime.now()}] 自定义数据源已启动...")
        self.正在运行 = True

        def 运行回测():
            self.观察员.读取任意数据(self.魔法, **self.__魔法参数)
            self.正在运行 = False

        回测线程 = threading.Thread(target=运行回测, daemon=True)
        回测线程.start()

    def stop(self):
        """
        数据源停止时的清理操作。
        这里我们将正在运行的标志设为False，停止数据加载。
        """
        self.正在运行 = False
        print(f"[{datetime.now()}] 自定义数据源已停止。")

    def _load(self):
        """
        (核心方法) Backtrader会循环调用此方法来获取数据。
        每次被调用时，都应该返回新的数据行（一个K线/一个数据点）。
        如果没有新数据，返回 False，Backtrader会等待下次调用。
        """
        if not self.正在运行:
            return False
        # 当没有新数据且系统仍在运行时，进入等待
        # 从外部队列获取新数据

        while True:
            try:
                data_point = self.数据队列.get(timeout=0.5)
                break
            except queue.Empty:
                if not self.已有数据:
                    continue
                else:
                    if self.正在运行:
                        continue
                    return False
        # 解析数据元组
        dt, o, h, l, c, v, oi = data_point

        # 将数据写入Backtrader的数据线 (lines)
        self.lines.datetime[0] = bt.date2num(dt)
        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        self.lines.openinterest[0] = oi
        self.已有数据 = True
        # 返回 True 表示成功加载一行数据
        return True


class 高级策略基类(bt.Strategy):
    params = (
        ("允许做多", True),
        ("允许做空", True),
        ("资金类型", "现金"),  # '现金' 或 '总权益'
        ("仓位比例", 0.8),
        ("最小交易单位", 1),
        ("使用限价单", True),  # True时开仓使用限价单，False使用市价单
        ("限价偏移", 0.01),  # 限价单相对于当前价的偏移比例
        ("止损比例", 0.05),  # 固定止损比例（如0.05）
        ("止损类型", "市价"),  # '市价' 或 '限价'（止损单类型）
        ("移动止损比例", None),  # 移动止损回撤比例
    )

    def __init__(self):
        self.止损单 = None
        self.最高价跟踪 = None
        self.最低价跟踪 = None
        self.待处理订单 = None
        self.待处理方向 = None
        self.待处理限价 = None

    def 日志(self, 文本, 时间=None):
        时间 = 时间 or self.datas[0].datetime.datetime(0)
        print(f"{时间} {文本}")

    def 计算目标数量(self, 价格):
        """根据资金类型和仓位比例计算目标数量"""
        现金 = self.broker.getcash()
        总权益 = self.broker.getvalue()
        if self.params.资金类型 == "现金":
            可用资金 = 现金
        else:
            可用资金 = 总权益
        投入资金 = 可用资金 * self.params.仓位比例
        数量 = int(投入资金 / 价格)
        数量 = max(数量, self.params.最小交易单位)
        return 数量

    def 提交限价单(self, 数据, 是否做多, 价格, 数量):
        if 是否做多:
            订单 = self.buy(data=数据, exectype=bt.Order.Limit, price=价格, size=数量)
        else:
            订单 = self.sell(data=数据, exectype=bt.Order.Limit, price=价格, size=数量)
        self.日志(f"提交限价单: {'买入' if 是否做多 else '卖出'} 价格={价格:.2f} 数量={数量}")
        return 订单

    def 提交市价单(self, 数据, 是否做多, 数量):
        if 是否做多:
            订单 = self.buy(data=数据, exectype=bt.Order.Market, size=数量)
        else:
            订单 = self.sell(data=数据, exectype=bt.Order.Market, size=数量)
        self.日志(f"提交市价单: {'买入' if 是否做多 else '卖出'} 数量={数量}")
        return 订单

    def 提交止损单(self, 数据, 是否做多, 触发价):
        数量 = abs(self.position.size)
        if 数量 == 0:
            return None
        # 根据止损类型选择订单类型
        if self.params.止损类型 == "市价":
            exectype = bt.Order.Stop
        else:  # 限价止损
            exectype = bt.Order.StopLimit
        if 是否做多:
            订单 = self.sell(data=数据, exectype=exectype, price=触发价, size=数量)
        else:
            订单 = self.buy(data=数据, exectype=exectype, price=触发价, size=数量)
        self.日志(f"提交止损单: 触发价={触发价:.2f} 数量={数量}")
        return 订单

    def 取消止损单(self):
        if self.止损单 and self.止损单.alive():
            self.cancel(self.止损单)
            self.日志("取消现有止损单")
        self.止损单 = None

    def 更新移动止损(self, 是否做多, 当前价格):
        if 是否做多:
            if self.最高价跟踪 is None or 当前价格 > self.最高价跟踪:
                self.最高价跟踪 = 当前价格
            return self.最高价跟踪 * (1 - self.params.移动止损比例)
        else:
            if self.最低价跟踪 is None or 当前价格 < self.最低价跟踪:
                self.最低价跟踪 = 当前价格
            return self.最低价跟踪 * (1 + self.params.移动止损比例)

    def 设置初始止损(self, 是否做多, 入场价):
        if self.params.止损比例 is not None:
            # 固定止损
            止损价 = 入场价 * (1 - self.params.止损比例) if 是否做多 else 入场价 * (1 + self.params.止损比例)
            self.日志(f"初始固定止损价: {止损价:.2f}")
            self.止损单 = self.提交止损单(self.data, 是否做多, 止损价)
        elif self.params.移动止损比例 is not None:
            # 移动止损初始单
            self.最高价跟踪 = 入场价 if 是否做多 else None
            self.最低价跟踪 = 入场价 if not 是否做多 else None
            止损价 = self.更新移动止损(是否做多, 入场价)
            self.日志(f"初始移动止损价: {止损价:.2f}")
            self.止损单 = self.提交止损单(self.data, 是否做多, 止损价)

    def 更新止损订单(self, 是否做多, 当前价格):
        if self.params.移动止损比例 is None or self.止损单 is None:
            return
        新止损价 = self.更新移动止损(是否做多, 当前价格)
        if 新止损价 is None:
            return
        当前止损价 = self.止损单.price
        if (是否做多 and 新止损价 > 当前止损价) or (not 是否做多 and 新止损价 < 当前止损价):
            self.日志(f"移动止损: {当前止损价:.2f} -> {新止损价:.2f}")
            self.取消止损单()
            self.止损单 = self.提交止损单(self.data, 是否做多, 新止损价)

    def 开仓(self, 数据, 是否做多, 限价=None):
        # 检查方向是否允许
        if (是否做多 and not self.params.允许做多) or (not 是否做多 and not self.params.允许做空):
            self.日志("方向不允许")
            return

        # 如果已有持仓，先平仓
        if self.position:
            self.日志("已有持仓，先平仓")
            self.平仓(数据)

        当前价 = 数据.close[0]

        # 确定实际使用的限价和订单类型
        if 限价 is not None:
            # 显式传入限价，强制使用限价单，忽略参数 '使用限价单'
            实际限价 = 限价
            使用限价单标志 = True
        else:
            # 未传入限价，根据策略参数决定
            使用限价单标志 = self.params.使用限价单
            if 使用限价单标志:
                实际限价 = 当前价 * (1 - self.params.限价偏移) if 是否做多 else 当前价 * (1 + self.params.限价偏移)
            else:
                实际限价 = 当前价  # 用于计算数量，实际订单为市价单

        # 计算目标数量（基于实际限价或当前价）
        数量 = self.计算目标数量(实际限价)
        if 数量 == 0:
            self.日志("无法开仓：计算数量为0")
            return

        # 提交订单
        if 使用限价单标志:
            订单 = self.提交限价单(数据, 是否做多, 实际限价, 数量)
        else:
            订单 = self.提交市价单(数据, 是否做多, 数量)

        if 订单:
            self.待处理订单 = 订单
            self.待处理方向 = 是否做多
            self.待处理限价 = 实际限价

    def 平仓(self, 数据):
        if self.position:
            self.取消止损单()
            数量 = abs(self.position.size)
            if self.position.size > 0:
                self.sell(data=数据, exectype=bt.Order.Market, size=数量)
            else:
                self.buy(data=数据, exectype=bt.Order.Market, size=数量)
            self.日志(f"平{'多' if self.position.size > 0 else '空'}仓: 数量={数量}")
            self.最高价跟踪 = None
            self.最低价跟踪 = None

    def notify_order(self, 订单):
        if 订单.status in [订单.Completed]:
            方向 = "买入" if 订单.isbuy() else "卖出"
            self.日志(f"{方向}成交, 价格={订单.executed.price:.2f}, 数量={订单.executed.size}")

            # 开仓成交后设置止损
            if self.待处理订单 == 订单:
                self.设置初始止损(self.待处理方向, 订单.executed.price)
                self.待处理订单 = None
                self.待处理方向 = None

            # 若平仓后无持仓，取消止损单（已做）
            if self.position.size == 0:
                self.取消止损单()

        elif 订单.status in [订单.Canceled, 订单.Margin, 订单.Rejected]:
            self.日志(f"订单失败: {订单.getstatusname()}")
            if self.待处理订单 == 订单:
                self.待处理订单 = None

    def notify_trade(self, 交易):
        if 交易.isclosed:
            self.日志(f"交易结束, 净利润={交易.pnlcomm:.2f}")
            print()

    def next(self):
        pass


class 回测(高级策略基类):
    params = (
        ("资金类型", "总权益"),
        ("仓位比例", 0.95),
        ("最小交易单位", 0.001),
        ("使用限价单", True),  # 改为 True 启用限价单
        ("限价偏移", 0.002),
        ("止损比例", 0.05),
        ("止损类型", "市价"),
        ("移动止损比例", None),
        ("观察员", None),
    )

    def __init__(self):
        super().__init__()
        self.已处理信号 = set()

    def 获取开仓限价(self, 是否做多):
        # 根据缠论分型计算限价，若无则返回 None 使用基类默认逻辑
        try:
            最新K = self.观察员.缠论K线序列[-1]
            return 最新K.分型特征值
        except:
            pass
        return None

    def next(self):
        # 1. 更新移动止损（基类方法）
        if self.position:
            self.更新止损订单(self.position.size > 0, self.data.close[0])

        # 2. 检查信号
        买信号 = self.检查买信号()
        卖信号 = self.检查卖信号()
        当前K序号 = self.p.观察员.当前缠K.序号
        信号ID = f"{当前K序号}_买{买信号}_卖{卖信号}"
        if 信号ID in self.已处理信号:
            return
        self.已处理信号.add(信号ID)

        # 3. 执行交易（优先处理平仓，再开仓）
        if 买信号 and self.position.size < 0:
            self.平仓(self.data)  # 空仓反手前先平空
        if 卖信号 and self.position.size > 0:
            self.平仓(self.data)  # 多仓反手前先平多

        if 买信号 and not self.position:
            限价 = self.获取开仓限价(True)
            self.开仓(self.data, 是否做多=True, 限价=限价)
        elif 卖信号 and not self.position:
            限价 = self.获取开仓限价(False)
            self.开仓(self.data, 是否做多=False, 限价=限价)

    def 检查买信号(self):
        if self.p.观察员.笔序列:
            k线 = self.p.观察员.缠论K线序列[-1]
            首 = True if k线.买卖点信息 and "买" in next(iter(k线.买卖点信息)) else False
            if 首:
                原始差值 = self.p.观察员.当前K线.序号 - k线.标的K线.序号
                差值 = self.p.观察员.当前缠K.序号 - k线.序号
                self.日志(f"首_买入信号差值: {原始差值}, {差值}, 观察员.当前K线 时间戳: {self.p.观察员.当前K线.时间戳}")
            k线 = self.p.观察员.缠论K线序列[-2]

            尾 = True if self.p.观察员.缠论K线序列[-2].买卖点信息 and "买" in next(iter(self.p.观察员.缠论K线序列[-2].买卖点信息)) else False
            if 尾:
                原始差值 = self.p.观察员.当前K线.序号 - k线.标的K线.序号
                差值 = self.p.观察员.当前缠K.序号 - k线.序号
                self.日志(f"尾_买入信号差值: {原始差值}, {差值}, 观察员.当前K线 时间戳: {self.p.观察员.当前K线.时间戳}")
            return 首 or 尾

    def 检查卖信号(self):
        if self.p.观察员.笔序列:
            k线 = self.p.观察员.缠论K线序列[-1]
            首 = True if k线.买卖点信息 and "卖" in next(iter(k线.买卖点信息)) else False
            if 首:
                原始差值 = self.p.观察员.当前K线.序号 - k线.标的K线.序号
                差值 = self.p.观察员.当前缠K.序号 - k线.序号
                self.日志(f"首_买入信号差值: {原始差值}, {差值}, 观察员.当前K线 时间戳: {self.p.观察员.当前K线.时间戳}")
            k线 = self.p.观察员.缠论K线序列[-2]

            尾 = True if self.p.观察员.缠论K线序列[-2].买卖点信息 and "卖" in next(iter(self.p.观察员.缠论K线序列[-2].买卖点信息)) else False
            if 尾:
                原始差值 = self.p.观察员.当前K线.序号 - k线.标的K线.序号
                差值 = self.p.观察员.当前缠K.序号 - k线.序号
                self.日志(f"尾_买入信号差值: {原始差值}, {差值}, 观察员.当前K线 时间戳: {self.p.观察员.当前K线.时间戳}")
            return 首 or 尾

    def log(self, 文本, dt=None):
        dt = dt or bt.num2date(self.data.datetime[0])
        print(f"[{dt.strftime('%Y-%m-%d %H:%M')}] {self.p.符号} | {文本}")


def 同步_跟踪回测(观察员: 观察者, 数据源: bt.feed.DataBase):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(回测, 观察员=观察员)

    # 收益与风险指标
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="时间收益率")  # 需要指定timeframe? 默认用数据源的时间周期
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="年度收益率")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="总体收益率")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="夏普比率")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="年化夏普比率")
    cerebro.addanalyzer(bt.analyzers.Calmar, _name="卡尔玛比率")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="系统质量指数")
    cerebro.addanalyzer(bt.analyzers.VWR, _name="变异性加权回报")

    # 风险与资金管理
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="回撤分析")
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="时间周期回撤")  # 需要timeframe参数，下面会重设
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="交易分析")
    cerebro.addanalyzer(bt.analyzers.PeriodStats, _name="周期统计")  # 需要timeframe
    cerebro.addanalyzer(bt.analyzers.Transactions, _name="交易记录")
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio导出")

    # 其他
    cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, _name="滚动对数收益率")  # 需要timeframe和period

    cerebro.adddata(数据源)

    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%佣金

    初始资金 = cerebro.broker.getvalue()
    print("初始资金:", 初始资金)
    results = cerebro.run(live=True)
    最终资金 = cerebro.broker.getvalue()

    strat = results[0]
    print("回测结束，分析结果如下：")
    print("=" * 60)

    # 定义打印函数，安全获取分析结果
    def 打印分析(名称, 分析器对象):
        try:
            result = 分析器对象.get_analysis()
            print(f"\n【{名称}】")
            # 格式化输出，如果是字典则打印键值对
            if isinstance(result, dict):
                for k, v in result.items():
                    print(f"  {k}: {v}")
            else:
                print(f"  {result}")
        except Exception as e:
            print(f"【{名称}】获取失败: {e}")

    # 逐一打印各分析器结果
    打印分析("时间收益率", strat.analyzers.时间收益率)
    打印分析("年度收益率", strat.analyzers.年度收益率)
    打印分析("总体收益率", strat.analyzers.总体收益率)
    打印分析("夏普比率", strat.analyzers.夏普比率)
    打印分析("年化夏普比率", strat.analyzers.年化夏普比率)
    打印分析("卡尔玛比率", strat.analyzers.卡尔玛比率)
    打印分析("系统质量指数", strat.analyzers.系统质量指数)
    打印分析("变异性加权回报", strat.analyzers.变异性加权回报)
    打印分析("回撤分析", strat.analyzers.回撤分析)
    打印分析("时间周期回撤", strat.analyzers.时间周期回撤)
    打印分析("交易分析", strat.analyzers.交易分析)
    print(strat.analyzers.交易分析.get_analysis())
    打印分析("周期统计", strat.analyzers.周期统计)
    打印分析("交易记录", strat.analyzers.交易记录)
    # pyfolio 分析器不直接打印，需额外调用导出函数，此处略
    打印分析("滚动对数收益率", strat.analyzers.滚动对数收益率)

    # 最终资金
    print(f"\n最终账户价值: {cerebro.broker.getvalue():.2f}")
    print("最终资金:", 最终资金, (最终资金 - 初始资金) / 初始资金)


def 测试_邮局数据(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False)):
    def 魔法():
        观察员 = Bitstamp(symbol, int(freq), ws, 配置)
        观察员.init(int(limit))
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_读取数据(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False), 文件路径: str = "./templates/btcusd_ex-1800-1685795400-1713488400.nb"):
    def 魔法():
        启动时间 = datetime.now()
        观察员 = 观察者.读取数据文件(配置.加载文件路径, ws, 配置)
        # 观察员.分部分析()
        消耗用时 = datetime.now() - 启动时间
        print(消耗用时)
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_读取上一次数据(名称: str = "btcusd", 数量: int = 500, 周期: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False)):
    def 魔法():
        观察员 = 观察者(名称, int(周期), ws, 配置)
        观察员.加载本地数据("./templates/last.nb")
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_读取上一次数据_回测(名称: str = "btcusd", 数量: int = 500, 周期: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False)):
    def 魔法():
        数据队列 = queue.Queue(1)
        观察员 = 观察者(名称, int(周期), ws, 配置, 数据队列)
        数据源 = 自定义实时数据源(数据队列, 观察员, 观察员.加载本地数据, 文件路径="./templates/last.nb")
        同步_跟踪回测(观察员, 数据源)
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_邮局数据_同步回测(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置()):
    def 魔法():
        数据队列 = queue.Queue(1)
        观察员 = Bitstamp(symbol, int(freq), ws, 配置)
        观察员.数据队列 = 数据队列
        数据源 = 自定义实时数据源(数据队列, 观察员, 观察员.init, size=int(limit))
        同步_跟踪回测(观察员, 数据源)
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_周期合成(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置()):
    def 魔法():
        周期组 = [int(freq), int(freq) * 5, int(freq) * 5 * 6]
        多级别分析 = 立体分析器(symbol, 周期组, ws, 配置)
        Bitstamp.获取K线数据(int(limit), symbol, 周期组[0], 多级别分析)
        return 多级别分析

    return 魔法


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


class 代码执行器:
    """
    在母体进程中安全执行 Python 代码（受限环境）。
    支持超时（Unix 信号机制）、重置、帮助、历史。
    警告：无法完全阻止恶意代码访问主进程，请仅用于可信环境！
    """

    def __init__(self, 用户标识: str, 默认超时: float = 5.0):
        self.图表观察员 = None
        self.用户标识 = 用户标识
        self.超时 = 默认超时
        self.历史记录: List[Dict[str, Any]] = []
        # 安全内置函数白名单
        self.安全内置函数 = {
            # 基础函数
            "print": print,
            "len": len,
            "range": range,
            "int": int,
            "str": str,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "abs": abs,
            "round": round,
            "sum": sum,
            "min": min,
            "max": max,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "reversed": reversed,
            "isinstance": isinstance,
            "type": type,
            "id": id,
            "chr": chr,
            "ord": ord,
            "bin": bin,
            "hex": hex,
            "oct": oct,
            "all": all,
            "any": any,
            "next": next,
            "iter": iter,
            # 常量
            "True": True,
            "False": False,
            "None": None,
            "dir": dir,
            "math": math,
            "random": random,
            "datetime": datetime,
            "timedelta": timedelta,
            "time": __import__("time"),
            "help": self.获取帮助,
            "clear": self.重置,
        }
        self.安全内置函数.update(
            {
                "MACD信号": MACD信号,
                "MACD趋势方向": MACD趋势方向,
                "RSI信号": RSI信号,
                "RSI趋势方向": RSI趋势方向,
                "中枢": 中枢,
                "主线程": 主线程,
                "买卖点": 买卖点,
                "买卖点类型": 买卖点类型,
                "分型": 分型,
                "分型结构": 分型结构,
                "回测": 回测,
                "图表配色": 图表配色,
                "基础买卖点": 基础买卖点,
                "平滑异同移动平均线": 平滑异同移动平均线,
                "指令": 指令,
                "指标": 指标,
                "时间周期": 时间周期,
                "特征分型": 特征分型,
                "相对强弱指数": 相对强弱指数,
                "相对方向": 相对方向,
                "笔": 笔,
                "线段": 线段,
                "线段特征": 线段特征,
                "缠论配置": 缠论配置,
                "缺口": 缺口,
                "背驰分析": 背驰分析,
                "观察者": 观察者,
                "随机指标": 随机指标,
                "高级策略基类": 高级策略基类,
                "图表展示序列": 图表展示序列,
            }
        )
        # 初始化命名空间
        self.重置()

    def 设置图表观察员(self, observer):
        self.图表观察员 = observer
        self.全局命名空间["观察员"] = observer

    def _代码安全检查(self, 代码字符串: str) -> Optional[str]:
        """
        使用 AST 检查代码是否包含危险属性访问（如 .__class__ 或 ._xxx）。
        返回 None 表示安全，否则返回错误信息。
        """
        危险属性列表 = ["__class__", "__bases__", "__subclasses__", "__globals__", "__builtins__", "__import__", "__getattribute__", "__setattr__", "__delattr__", "__reduce__", "__reduce_ex__", "__code__"]
        try:
            树 = ast.parse(代码字符串)
        except SyntaxError as e:
            return f"语法错误: {e}"
        for 节点 in ast.walk(树):
            if isinstance(节点, ast.Attribute):
                if 节点.attr in 危险属性列表 or 节点.attr.startswith("__"):
                    return f"禁止访问属性 '{节点.attr}'"
            if isinstance(节点, ast.Call):
                # 禁止调用内置的 __import__
                if isinstance(节点.func, ast.Name) and 节点.func.id == "__import__":
                    return "禁止调用 __import__"
                # 禁止 eval/exec
                if isinstance(节点.func, ast.Name) and 节点.func.id in ("eval", "exec"):
                    return f"禁止使用 {节点.func.id}"
        return None

    def _超时处理(self, 信号编号, 帧):
        """信号处理函数，抛出超时异常"""
        raise TimeoutError(f"代码执行超时（超过 {self.超时} 秒）")

    def 执行(self, 代码字符串: str) -> Dict[str, Optional[str]]:
        """
        在主进程中执行代码，返回 {"标准输出": str, "错误输出": str, "异常信息": str or None}
        """
        # 安全检查
        检查结果 = self._代码安全检查(代码字符串)
        if 检查结果:
            return {
                "success": False,
                "output": "",
                "error": {"type": "安全检查", "message": 检查结果, "traceback": ""},
                "stdout": "",
                "stderr": "",
                "print_output": "",
                "execution_time": datetime.now().isoformat(),
            }

        # 重定向输出
        原始stdout = sys.stdout
        原始stderr = sys.stderr
        stdout缓冲区 = io.StringIO()
        stderr缓冲区 = io.StringIO()
        sys.stdout = stdout缓冲区
        sys.stderr = stderr缓冲区

        异常信息 = None
        # 保存原有信号处理（仅 Unix）
        原有信号处理 = None
        if hasattr(signal, "SIGALRM"):
            原有信号处理 = signal.signal(signal.SIGALRM, self._超时处理)
            signal.alarm(int(self.超时) + 1)  # 设置超时秒数，多给1秒宽松

        try:
            # 使用受限命名空间执行
            # 注意：每次执行使用同一个 self.全局命名空间 和 self.局部命名空间，以实现变量持久化
            exec(代码字符串, self.全局命名空间, self.局部命名空间)
        except TimeoutError as e:
            异常信息 = traceback.format_exc()
            异常信息 = {"type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        except Exception as e:
            异常信息 = traceback.format_exc()
            异常信息 = {"type": type(e).__name__, "message": str(e), "traceback": traceback.format_exc()}
        finally:
            # 取消超时报警
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
                if 原有信号处理:
                    signal.signal(signal.SIGALRM, 原有信号处理)
            # 恢复输出
            sys.stdout = 原始stdout
            sys.stderr = 原始stderr
            # 获取捕获的输出
            标准输出 = stdout缓冲区.getvalue()
            错误输出 = stderr缓冲区.getvalue()
            # 记录历史
            self.历史记录.append({"代码": 代码字符串, "结果": {"标准输出": 标准输出, "错误输出": 错误输出, "异常信息": 异常信息}})
        结果 = {
            "success": not 异常信息,
            "output": 标准输出,
            "error": 异常信息,
            "stdout": 标准输出,
            "stderr": 错误输出,
            "print_output": 标准输出,
            "execution_time": datetime.now().isoformat(),
        }
        print(结果)
        return 结果

    def 重置(self) -> None:
        """重置命名空间，清除所有已定义的变量"""
        self.全局命名空间 = {
            "__builtins__": self.安全内置函数,
            "__name__": "__沙箱__",
        }
        self.局部命名空间 = {}
        print("执行环境已重置")

    def 获取帮助(self) -> str:
        """返回帮助信息"""
        帮助文本 = "可用的内置函数/类型：\n"
        for 名称 in sorted(self.安全内置函数.keys()):
            if not 名称.startswith("__"):  # 过滤内部名称
                帮助文本 += f"  - {名称}\n"
        帮助文本 += "\n注意：不支持文件 I/O、系统命令、网络请求、属性访问（如 .__class__）。\n"
        帮助文本 += f"当前超时设置：{self.超时} 秒\n"
        帮助文本 += "使用 重置() 可清空变量，使用 设置超时(秒) 可修改超时。"
        return 帮助文本

    def 设置超时(self, 秒数: float) -> None:
        """动态修改超时时间"""
        self.超时 = max(0.5, 秒数)  # 至少0.5秒
        print(f"超时已设置为 {self.超时} 秒")

    def 获取历史(self, 最近条数: int = None) -> List[Dict]:
        """返回执行历史"""
        if 最近条数 is None:
            return self.历史记录.copy()
        return self.历史记录[-最近条数:]

    def 清空历史(self) -> None:
        """清空历史记录（不影响当前变量）"""
        self.历史记录.clear()

    def 关闭(self) -> None:
        """清理（预留）"""
        pass


class 连接管理器:
    def __init__(self):
        self.活跃连接字典: Dict[str, WebSocket] = {}
        self.环境字典: Dict[str, 代码执行器] = {}
        self.图表观察员字典: Dict[str, 观察者] = {}

    async def 进行连接(self, 用户标识: str, websocket: WebSocket):
        await websocket.accept()
        self.活跃连接字典[用户标识] = websocket

        if 用户标识 not in self.环境字典:
            self.环境字典[用户标识] = 代码执行器(用户标识)

        print(f"[连接] 用户 {用户标识} 已连接")

    def 切断连接(self, 用户标识: str):
        if 用户标识 in self.活跃连接字典:
            del self.活跃连接字典[用户标识]
        if 用户标识 in self.环境字典:
            del self.环境字典[用户标识]
        if 用户标识 in self.图表观察员字典:
            del self.图表观察员字典[用户标识]

        print(f"[断开] 用户 {用户标识} 已断开")

    async def 发送信息(self, 用户标识: str, message: Dict[str, Any]):
        if 用户标识 in self.活跃连接字典:
            try:
                await self.活跃连接字典[用户标识].send_json(message)
            except Exception as e:
                print(f"[错误] 发送消息到 {用户标识} 失败: {e}")

    def 设置图表观察员(self, 用户标识: str, observer):
        self.图表观察员字典[用户标识] = observer

        if 用户标识 in self.环境字典:
            self.环境字典[用户标识].设置图表观察员(observer)

    def 获取图表观察员(self, 用户标识: str):
        return self.图表观察员字典.get(用户标识)

    def 获取执行环境(self, 用户标识: str):
        if 用户标识 not in self.环境字典:
            self.环境字典[用户标识] = 代码执行器(用户标识)
        return self.环境字典[用户标识]


全局连接管理器 = 连接管理器()

# 全局线程变量
主线程 = None


# ============ WebSocket端点 ============
@app.websocket("/ws/{user_id}")
async def 全局消息分发器(websocket: WebSocket, user_id: str):
    """统一的WebSocket端点，处理所有类型的消息"""
    用户标识 = user_id
    await 全局连接管理器.进行连接(用户标识, websocket)

    try:
        # 发送欢迎消息
        await 全局连接管理器.发送信息(
            用户标识,
            {
                "type": "connected",
                "message": "✅ 已连接到服务器",
                "用户标识": 用户标识,
                "timestamp": datetime.now().isoformat(),
                "endpoint": "unified",
            },
        )

        while True:
            try:
                消息字典 = json.loads(await websocket.receive_text())
            except WebSocketDisconnect:
                全局连接管理器.切断连接(用户标识)
                break
            # 获取消息类型
            消息类型 = 消息字典.get("type", "")
            模块 = 消息字典.get("module", "chart")  # 默认是chart模块

            print(f"[消息] 用户 {用户标识} | 模块: {模块} | 类型: {消息类型}")

            if 模块 == "python":
                # Python执行相关消息
                await 处理代码消息(用户标识, 消息字典)
            elif 模块 == "chart":
                # 图表相关消息
                await 处理图表消息(用户标识, 消息字典, websocket)
            else:
                print(模块, 消息字典)

    except WebSocketDisconnect:
        全局连接管理器.切断连接(用户标识)

    except Exception as e:
        traceback.print_exc()
        print(f"[错误] WebSocket处理异常: {e}")
        await 全局连接管理器.发送信息(用户标识, {"type": "error", "message": f"服务器错误: {str(e)}", "timestamp": datetime.now().isoformat()})
        全局连接管理器.切断连接(用户标识)


async def 处理图表消息(用户标识: str, 消息字典: Dict, websocket: WebSocket):
    """处理图表消息"""
    print(消息字典)
    消息类型 = 消息字典.get("type", "")

    if 消息类型 == "ready":
        # 初始化分析器
        symbol = 消息字典.get("symbol", "btcusd")
        freq = 消息字典.get("freq", 300)
        limit = 消息字典.get("limit", 500)
        generator = 消息字典.get("generator", "True")

        config = 消息字典.get("config", dict())
        当前配置 = 缠论配置.from_dict(config)
        print(当前配置)

        # 停止现有线程
        global 主线程
        if 主线程 is not None:
            主线程.join(1)
            time.sleep(1)
            主线程 = None

        # 创建新的分析器
        if generator == "zqhc":
            魔法 = 测试_周期合成(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置)
        elif generator == "hc":
            魔法 = 测试_邮局数据_同步回测(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置)

        elif generator == "ex":
            魔法 = 测试_读取数据(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置)
        elif generator == "last":
            魔法 = 测试_读取上一次数据(名称=symbol, 数量=limit, 周期=freq, ws=websocket, 配置=当前配置)

        elif generator == "lasthc":
            魔法 = 测试_读取上一次数据_回测(名称=symbol, 数量=limit, 周期=freq, ws=websocket, 配置=当前配置)

        else:
            魔法 = 测试_邮局数据(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置)

        def 数据加载线程():
            try:
                全局连接管理器.设置图表观察员(用户标识, 魔法())
                print(f"[分析器] 用户 {用户标识} 的分析器已启动")
            except Exception as e:
                traceback.print_exc()
                print(f"[分析器错误] {e}")

        主线程 = Thread(target=数据加载线程, daemon=True)
        主线程.start()

        await 全局连接管理器.发送信息(
            用户标识,
            {
                "type": "ready_ack",
                "message": "图表分析器已启动",
                "symbol": symbol,
                "freq": freq,
                "timestamp": datetime.now().isoformat(),
            },
        )

    elif 消息类型 == "query_by_index":
        观察员: 观察者 = 全局连接管理器.获取图表观察员(用户标识)
        if 观察员 is not None:
            符号, 周期, 数据类型, 序号 = 消息字典.get("index").split(":")
            序号 = int(序号)
            print(符号, 周期, 数据类型, 序号)
            try:
                待发送消息 = {}
                if 数据类型 == "中枢<笔>":
                    待发送消息.update({"index": 序号, "data": str(观察员.笔_中枢序列[序号])})
                if 数据类型 == "中枢<线段>":
                    待发送消息.update({"index": 序号, "data": str(观察员.中枢序列[序号])})

                if 数据类型 == "中枢<线段<线段>>":
                    待发送消息.update({"index": 序号, "data": str(观察员.线段_中枢序列[序号])})

                if 数据类型 == "中枢<扩展线段>":
                    待发送消息.update({"index": 序号, "data": str(观察员.扩展中枢序列[序号])})
                if 数据类型 == "中枢<扩展线段<线段>>":
                    待发送消息.update({"index": 序号, "data": str(观察员.扩展中枢序列_线段[序号])})

                if 数据类型 == "笔":
                    待发送消息.update({"index": 序号, "data": str(观察员.笔序列[序号])})
                if 数据类型 == "线段":
                    待发送消息.update({"index": 序号, "data": str(观察员.线段序列[序号])})
                    段 = 观察员.线段序列[序号]
                    if 段._特征序列_显示:
                        段._特征序列_显示 = False
                        for 特征 in 段.特征序列:
                            if 特征 is not None:
                                观察员 and 观察员.报信(特征, 指令.删除(特征.标识), sys._getframe().f_lineno, 周期=段.周期)

                    else:
                        段._特征序列_显示 = True
                        序号 = 0
                        for 特征 in 段.特征序列:
                            if 特征 is not None:
                                特征.序号 = 序号
                                特征.标识 = f"{段.文.右.标识}:{段.文.右.周期}:{段.标识}_特征序列_{序号}:{段.序号}"
                                观察员 and 观察员.报信(特征, 指令.添加(特征.标识), sys._getframe().f_lineno, 周期=段.周期)
                            序号 += 1
                if 数据类型 == "扩展线段":
                    待发送消息.update({"index": 序号, "data": str(观察员.扩展线段序列[序号])})
                if 数据类型 == "扩展线段<线段>":
                    待发送消息.update({"index": 序号, "data": str(观察员.扩展线段序列_线段[序号])})

                if 数据类型 == "线段<线段>":
                    待发送消息.update({"index": 序号, "data": str(观察员.线段_线段序列[序号])})
                    段 = 观察员.线段_线段序列[序号]
                    if 段._特征序列_显示:
                        段._特征序列_显示 = False
                        for 特征 in 段.特征序列:
                            if 特征 is not None:
                                观察员 and 观察员.报信(特征, 指令.删除(特征.标识), sys._getframe().f_lineno, 周期=段.周期)

                    else:
                        段._特征序列_显示 = True
                        序号 = 0
                        for 特征 in 段.特征序列:
                            if 特征 is not None:
                                特征.序号 = 序号
                                特征.标识 = f"{段.文.右.标识}:{段.文.右.周期}:{段.标识}_特征序列_{序号}:{段.序号}"
                                观察员 and 观察员.报信(特征, 指令.添加(特征.标识), sys._getframe().f_lineno, 周期=段.周期)
                            序号 += 1

                if "_" in 数据类型 and "中枢" in 数据类型:  # 线段_0_实_中枢<笔>
                    数据类型, 线序, 虚实合, 类型 = 数据类型.split("_")

                    段序号 = int(线序)
                    if 数据类型 == "线段":
                        段: 线段 = 观察员.线段序列[段序号]
                        zs = getattr(段, f"{虚实合}_中枢序列")[序号]
                        待发送消息.update({"index": 序号, "data": str(zs)})

                    if 数据类型 == "线段<线段>":
                        段: 线段 = 观察员.线段_线段序列[段序号]
                        zs = getattr(段, f"{虚实合}_中枢序列")[序号]
                        待发送消息.update({"index": 序号, "data": str(zs)})

                await 全局连接管理器.发送信息(用户标识, {"type": "query_result", "success": True, "data_type": 数据类型, "data": 待发送消息})

            except IndexError:
                await 全局连接管理器.发送信息(用户标识, {"type": "query_result", "success": False, "message": f"索引 {序号} 超出范围"})
            except Exception as e:
                await 全局连接管理器.发送信息(用户标识, {"type": "query_result", "success": False, "message": str(e)})
        else:
            print(f"[query_by_index] 用户 {用户标识} 没有分析器！")

    elif 消息类型 == "save_path":
        print(f"[保存路径] 用户 {用户标识}: {消息字典}")
        await 全局连接管理器.发送信息(
            用户标识,
            {
                "type": "path_saved",
                "message": "路径已保存",
                "index": 消息字典.get("index"),
                "timestamp": datetime.now().isoformat(),
            },
        )

    elif 消息类型 == "ping":
        await 全局连接管理器.发送信息(用户标识, {"type": "pong", "timestamp": datetime.now().isoformat()})

    else:
        await 全局连接管理器.发送信息(用户标识, {"type": "error", "message": f"未知的图表消息类型: {消息类型}", "timestamp": datetime.now().isoformat()})


async def 处理代码消息(用户标识: str, 消息字典: Dict):
    """处理Python执行消息"""
    command = 消息字典.get("command", "")

    if command == "execute":
        code = 消息字典.get("code", "").strip()

        if not code:
            await 全局连接管理器.发送信息(用户标识, {"type": "execution_result", "success": False, "message": "❌ 代码不能为空", "module": "python"})
            return

        当前执行环境 = 全局连接管理器.获取执行环境(用户标识)
        result = 当前执行环境.执行(code)

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

        await 全局连接管理器.发送信息(用户标识, response)

    elif command == "reset":
        当前执行环境 = 全局连接管理器.获取执行环境(用户标识)
        当前执行环境.重置()

        await 全局连接管理器.发送信息(
            用户标识,
            {
                "type": "environment_reset",
                "message": "🔄 Python执行环境已重置",
                "timestamp": datetime.now().isoformat(),
                "module": "python",
            },
        )

    elif command == "help":
        当前执行环境 = 全局连接管理器.获取执行环境(用户标识)
        help_text = 当前执行环境.获取帮助()

        await 全局连接管理器.发送信息(用户标识, {"type": "help_response", "help": help_text, "timestamp": datetime.now().isoformat(), "module": "python"})

    elif command == "ping":
        await 全局连接管理器.发送信息(用户标识, {"type": "pong", "timestamp": datetime.now().isoformat(), "module": "python"})

    else:
        await 全局连接管理器.发送信息(
            用户标识,
            {
                "type": "error",
                "message": f"❌ 未知命令: {command}",
                "timestamp": datetime.now().isoformat(),
                "module": "python",
            },
        )


# ============ HTTP端点 ============
@app.get("/")
async def 主页(
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
        request,
        "index.html",
        context={
            "request": request,
            "exchange": exchange,
            "symbol": symbol,
            "interval": resolutions.get(step),
            "limit": str(limit),
            "step": str(step),
            "generator": generator,
        },
    )


if __name__ == "__main__":
    配置 = 缠论配置.不推送()
    配置.加载文件路径 = "./templates/btcusd-300-1761327300-1776327900.nb"
    g = 测试_读取数据("btc", 0, 60, None, 配置, "./templates/btcusd-300-1761327300-1776327900.nb")()
    print(len(g.缠论K线序列), len(g.笔序列))
