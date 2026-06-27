import importlib.metadata
import platform
import random
import os
import math
import asyncio
import io
import json
import ast
import signal
import struct
import sys
import time
import queue
import traceback
import threading
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from random import seed, randint, uniform, choice, choices
from threading import Thread
from typing import (
    List,
    Optional,
    Tuple,
    SupportsInt,
    Generator,
    SupportsIndex,
    Union,
    Self,
    Final,
    Dict,
    Any,
    final,
)


import requests
from fastapi import FastAPI, WebSocketDisconnect, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jinja2 import Environment, FileSystemLoader

from pydantic import BaseModel
import backtrader as bt

from chan import *
from strategies import *


def Nil(*args, **kwargs):
    return None


def 获取模块版本():
    versions = {}

    # 1.
    try:
        versions["chanlun"] = importlib.metadata.version("chanlun")
    except importlib.metadata.PackageNotFoundError:
        pass
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
    def 找到最大可整除周期(cls, 输入秒数: int) -> str:
        """
        输入秒数 → 返回 最大可整除的周期秒数
        周期范围：
        1~59分钟、1~23小时、1~28天
        """
        周期列表 = []

        # 1~59分钟
        for m in range(1, 60):
            周期列表.append(m * 60)

        # 1~23小时
        for h in range(1, 24):
            周期列表.append(h * 3600)

        # 1~28天
        for d in range(1, 29):
            周期列表.append(d * 86400)

        # 从大到小排序
        周期列表.sort(reverse=True)

        # 找第一个能整除的
        for 周期秒 in 周期列表:
            if 输入秒数 % 周期秒 == 0:
                return cls.秒数转周期(周期秒)

        return "1"

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

        if __object.标识 in ("线段", "线段<线段>"):
            if self.观察员 and self.观察员.配置.线段内部中枢图显:
                段: 虚线 = __object
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

    def 图表添加(self, 实线: Union["虚线", "中枢"], 行号: int):
        self.观察员 and self.观察员.报信(实线, 指令.添加(实线.标识), 行号)

    def 图表移除(self, 实线: Union["虚线", "中枢"], 行号: int):
        self.观察员 and self.观察员.报信(实线, 指令.删除(实线.标识), 行号)

    def 图表刷新(self, 实线: Union["虚线", "中枢"], 行号: int):
        self.观察员 and self.观察员.报信(实线, 指令.修改(实线.标识), 行号)


class 观察者(观察者):
    当前事件循环: Any = None  # if __name__ == "__main__" else asyncio.get_event_loop()
    延迟时间: float = 0.01

    def __init__(self, 符号: str, 周期: int, 数据通道: Optional[WebSocket], 配置: 缠论配置, 数据队列: Optional[queue.Queue] = None):
        self.数据通道: Optional[Any] = 数据通道  # WebSocket
        self.数据队列: queue.Queue = 数据队列
        super().__init__(符号, 周期, 配置)
        self.__终止时间戳: Optional[datetime] = 转化为时间戳(self.配置.手动终止) if self.配置.手动终止 else None
        self.买卖点字典 = dict()

    @final
    def 增加原始K线(self, 普K: K线):
        if self.__终止时间戳 and 普K.时间戳 > self.__终止时间戳:
            return

        if self.配置.展示标签("RawBar"):
            self.报信(普K, 指令.添加("RawBar"), sys._getframe().f_lineno, 周期=普K.周期)

        try:
            super().增加原始K线(普K)
            self.数据队列 and self.数据队列.put((普K.时间戳, 普K.开盘价, 普K.高, 普K.低, 普K.收盘价, 普K.成交量, 0))
            if self.数据通道 is not None and self.配置.图表展示:
                time.sleep(self.延迟时间)
            try:
                self.图表刷新()
                self.识别买卖点()
            except:
                print("~~~~~~~~~~~~~~", self.当前K线)
                traceback.print_exc()

        except Exception as e:
            路径 = f"./templates/{self.符号}_err-{self.周期}-{int(self.普通K线序列[0].时间戳)}-{int(self.普通K线序列[-1].时间戳)}"
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

    def 重置基础序列(self):
        self.买卖点字典 = dict()
        super().重置基础序列()
        self.笔序列: List[虚线] = [] if not self.配置.图表展示 else 图表展示序列(self)
        self.笔_中枢序列: List[中枢] = [] if not self.配置.图表展示 else 图表展示序列(self)

        self.线段序列组: List[List[虚线],] = []  # 线段, 线段<线段>，线段<线段<线段>>...
        self.中枢序列组: List[List[中枢],] = []
        for i in range(self.线段分析层次):
            self.线段序列组.append(list() if not self.配置.图表展示 else 图表展示序列(self))
            self.中枢序列组.append(list() if not self.配置.图表展示 else 图表展示序列(self))

        self.扩展线段序列组: List[List[虚线],] = []  # 扩展线段, 扩展线段<扩展线段>, 扩展线段<扩展线段<扩展线段>>...
        self.扩展中枢序列组: List[List[中枢],] = []
        for i in range(self.扩展线段分析层次):
            self.扩展线段序列组.append(list() if not self.配置.图表展示 else 图表展示序列(self))
            self.扩展中枢序列组.append(list() if not self.配置.图表展示 else 图表展示序列(self))

        self.混合扩展线段序列组: List[List[虚线],] = []  # 扩展线段<线段>, 扩展线段<线段<线段>>, 扩展线段<线段<线段<线段>>>...
        self.混合扩展中枢序列组: List[List[中枢],] = []
        for i in range(self.混合扩展线段分析层次):
            self.混合扩展线段序列组.append(list() if not self.配置.图表展示 else 图表展示序列(self))
            self.混合扩展中枢序列组.append(list() if not self.配置.图表展示 else 图表展示序列(self))

    def 读取任意数据(self, 魔法, **魔法参数):
        魔法(**魔法参数)
        return self

    def 加载本地数据(self, 文件路径: str):
        self.重置基础序列()
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], self.周期, self.标识)
                self.增加原始K线(k线)

    def 静态重新分析(self):
        self.买卖点字典 = dict()
        super().静态重新分析()

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

        当前买卖点.备注 = f"{self.标识}" + 当前买卖点.备注
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
            pass  # return

        if 当前买卖点.买卖点K线.时间戳 not in 活跃时间戳序列:
            买卖点序列.add(当前买卖点)
            当前买卖点.买卖点K线.买卖点信息.add(当前买卖点.备注)
            print(当前买卖点, type(当前买卖点), 当前买卖点.备注)
            self.报信(当前买卖点, 指令.添加(当前买卖点.备注), sys._getframe().f_lineno)

    def 图表刷新(self):
        def 报信(序列):
            getattr(序列, "尾部刷新", Nil)(行号=-1)

        报信(self.笔序列)
        报信(self.笔_中枢序列)
        for i in range(self.线段分析层次):
            报信(self.线段序列组[i])
            报信(self.中枢序列组[i])
        for i in range(self.扩展线段分析层次):
            报信(self.扩展线段序列组[i])
            报信(self.扩展中枢序列组[i])
        for i in range(self.混合扩展线段分析层次):
            报信(self.混合扩展线段序列组[i])
            报信(self.混合扩展中枢序列组[i])

        # self.将图表数据固化到本地()

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

        配色表 = {
            "笔": "#6C4D7E",
            "线段": "#FEC187",
            "线段<线段>": "#8F6048",  # 以线段为基础的特征序列线段
            "扩展线段": "#09a4ff",  # 以笔为基础的
            "扩展线段<线段>": "#07d59e",  # 以线段为基础的
            "扩展线段<扩展线段>": "#ff29e3",
            "扩展线段<扩展线段<线段>>": "#07d59e",
        }
        for k, v in list(配色表.items()):
            配色表[f"中枢<{k}>"] = v

        if type(对象) is 买卖点:
            message["type"] = "shape"
            message["cmd"] = 命令.指令.upper()
            message["id"] = str(id(对象))
            message["name"] = "arrow_down" if 对象.类型.是卖点 else "arrow_up"
            message["points"] = [{"time": int(对象.买卖点K线.时间戳), "price": 对象.买卖点K线.分型特征值}]
            arrowColor = "#FF2800" if 对象.类型.是卖点 else "#00FF22"
            text = f"{str(对象.偏移)}, {对象.破位值}, {对象.备注}"
            message["overrides"] = {
                "color": "#CC62FF",
                "arrowColor": arrowColor,
                "text": text,
                "title": 对象.备注.split("_")[0],
                "showLabel": False if 对象.偏移 <= 1 else True,
            }

        if type(对象) in (虚线, 中枢, 线段特征) and not self.配置.展示标签(对象.标识):
            return

        if type(对象) in (虚线, 中枢, 线段特征):
            图标 = 对象.图表标题
            message["type"] = "shape"
            message["cmd"] = 命令.指令.upper()
            message["id"] = 图标
            message["name"] = "trend_line" if type(对象) is not 中枢 else "rectangle"
            if 命令.指令 != 指令.删:
                message["points"] = [
                    {"time": int(缠论K线.时间戳对齐(self.基础缠K序列, 对象.文.中)), "price": 对象.文.分型特征值 if type(对象) is not 中枢 else 对象.高},
                    {"time": int(缠论K线.时间戳对齐(self.基础缠K序列, 对象.武.中)), "price": 对象.武.分型特征值 if type(对象) is not 中枢 else 对象.低},
                ]
                linewidths = {"笔": 1, "线段": 2, "走势": 3, "线段特征": 2}
                message["overrides"] = {
                    "bold": True,
                    "linecolor": 配色表.get(对象.标识, 配色表["笔"]),
                    "textcolor": "#000000",
                    "text": "",
                    "title": 图标,
                    "linewidth": linewidths.get(对象.标识, 2) if type(对象) is not 中枢 else linewidths.get(对象.基础序列[0].标识, 2),
                    "backgroundColor": "rgba(242, 54, 69, 0.2)" if 对象.方向 is 相对方向.向下 else "rgba(76, 175, 80, 0.2)",  # 上下上 为 红色，反之为 绿色,
                    "color": 配色表.get(对象.标识, 配色表["笔"]) if type(对象) is not 中枢 else 配色表.get(对象.基础序列[0].标识, 配色表["笔"]),
                    "textColor": 配色表.get(对象.标识, 配色表["笔"]) if type(对象) is not 中枢 else 配色表.get(对象.基础序列[0].标识, 配色表["笔"]),
                    "visible": False,
                }

                if 对象.标识 in ("笔", "线段", "线段<线段>", "中枢<笔>", "中枢<线段>"):
                    message["overrides"]["visible"] = True

                if type(对象) is not 线段特征:
                    message["overrides"]["text"] = f"{对象.标识} {对象.序号} 周期:{self.周期} {getattr(对象, '四象', '')} {getattr(对象, '特征序列状态', '')} {getattr(对象, '级别', '')} {getattr(对象, '备注', '')}"

                if type(对象) is 中枢:
                    message["overrides"]["text"] = f"{对象.标识} {对象.序号} 周期:{self.周期} 基础序列数量: {len(对象.基础序列)}"

                if 对象.标识 in ("线段", "线段<线段>"):
                    message["overrides"]["text"] = f"{对象.标识} {对象.序号} 周期:{self.周期} {线段.四象(对象)} {线段.特征序列状态(对象)} {getattr(对象, '级别', '')} {getattr(对象, '备注', '')}"

                if 对象.标识 in ("线段", "线段<线段>", "线段<线段<线段>>"):
                    message["overrides"]["text"] += f" 内部中枢数量:{len(对象.实_中枢序列)}"

                if type(对象) is 线段特征:
                    message["overrides"].update({"linecolor": "#F1C40F" if 对象.方向 is 相对方向.向下 else "#fbc02d", "linewidth": 4, "linestyle": 1})
                    message["overrides"]["visible"] = True

                if type(对象) is 中枢:
                    del message["overrides"]["textcolor"]
                    del message["overrides"]["linecolor"]
                else:
                    del message["overrides"]["textColor"]
                    del message["overrides"]["backgroundColor"]
                    del message["overrides"]["color"]

        if len(message) < 3:
            return

        if self.数据通道 is not None and self.配置.图表展示:
            asyncio.set_event_loop(观察者.当前事件循环)
            asyncio.ensure_future(self.数据通道.send_text(json.dumps(message)))
        return

    def 将图表数据固化到本地(self, static_shapes=None):
        template_path = "./templates/static.html"
        # 初始化 Jinja2 环境，模板目录为当前目录
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path) or "."))
        template = env.get_template(os.path.basename(template_path))
        resolution = 时间周期.找到最大可整除周期(self.周期)
        static_data = {"bars": [[int(k.时间戳), k.开盘价, k.高, k.低, k.收盘价, k.成交量] for k in self.普通K线序列]}

        配色表 = {
            "笔": "#6C4D7E",
            "线段": "#FEC187",
            "线段<线段>": "#8F6048",  # 以线段为基础的特征序列线段
            "扩展线段": "#09a4ff",  # 以笔为基础的
            "扩展线段<线段>": "#07d59e",  # 以线段为基础的
            "扩展线段<扩展线段>": "#ff29e3",
            "扩展线段<扩展线段<线段>>": "#07d59e",
        }

        for k, v in list(配色表.items()):
            配色表[f"中枢<{k}>"] = v

        if not static_shapes:
            static_shapes = []
            全部 = []
            for o in dir(self):
                if "序列" in o and "K线序列" not in o and "分型" not in o:
                    oo = getattr(self, o)
                    if isinstance(oo, list):
                        全部.extend(oo)
            for o in self.买卖点字典.values():
                全部.extend(o)

            for 对象 in 全部:
                if type(对象) in (笔, 线段, 中枢, 线段特征):
                    message = dict()
                    图标 = 对象.图表标题
                    message["type"] = "shape"
                    message["id"] = 图标
                    message["shapeType"] = "trend_line" if type(对象) is not 中枢 else "rectangle"
                    message["points"] = [
                        {"time": int(缠论K线.时间戳对齐(self.缠论K线序列, 对象.文.中)), "price": 对象.文.分型特征值 if type(对象) is not 中枢 else 对象.高},
                        {"time": int(缠论K线.时间戳对齐(self.缠论K线序列, 对象.武.中)), "price": 对象.武.分型特征值 if type(对象) is not 中枢 else 对象.低},
                    ]
                    linewidths = {"笔": 1, "线段": 2, "走势": 3, "线段特征": 2}
                    message["overrides"] = {
                        "bold": True,
                        "linecolor": 配色表.get(对象.标识, 配色表["笔"]),
                        "textcolor": "#000000",
                        "text": "",
                        "title": 图标,
                        "linewidth": linewidths.get(对象.标识, 2) if type(对象) is not 中枢 else linewidths.get(对象[0].标识, 2),
                        "backgroundColor": "rgba(242, 54, 69, 0.2)" if 对象.方向 is 相对方向.向下 else "rgba(76, 175, 80, 0.2)",
                        # 上下上 为 红色，反之为 绿色,
                        "color": 配色表.get(对象.标识, 配色表["笔"]) if type(对象) is not 中枢 else 配色表.get(对象[0].标识, 配色表["笔"]),
                        "textColor": 配色表.get(对象.标识, 配色表["笔"]) if type(对象) is not 中枢 else 配色表.get(对象[0].标识, 配色表["笔"]),
                    }

                    if type(对象) is not 线段特征:
                        message["overrides"]["text"] = f"{对象.标识} {对象.序号} 周期:{self.周期} {getattr(对象, '四象', '')} {getattr(对象, '特征序列状态', '')} {getattr(对象, '级别', '')} "

                    if type(对象) is 线段:
                        message["overrides"]["text"] += f" 内部中枢数量:{len(对象.实_中枢序列)}"

                    if type(对象) is 线段特征:
                        message["overrides"].update({"linecolor": "#F1C40F" if 对象.方向 is 相对方向.向下 else "#fbc02d", "linewidth": 4, "linestyle": 1})

                    if type(对象) is 中枢:
                        del message["overrides"]["textcolor"]
                        del message["overrides"]["linecolor"]
                    else:
                        del message["overrides"]["textColor"]
                        del message["overrides"]["backgroundColor"]
                        del message["overrides"]["color"]
                    static_shapes.append(message)
                    continue

                if type(对象) is 买卖点:
                    message = dict()
                    message["type"] = "shape"
                    message["id"] = str(id(对象))
                    message["shapeType"] = "arrow_down" if 对象.类型.是卖点 else "arrow_up"
                    message["points"] = [{"time": int(对象.买卖点K线.时间戳), "price": 对象.买卖点K线.分型特征值}]
                    arrowColor = "#FF2800" if 对象.类型.是卖点 else "#00FF22"
                    text = f"{str(对象.偏移)}, {对象.破位值}, {对象.备注}"
                    message["overrides"] = {
                        "color": "#CC62FF",
                        "arrowColor": arrowColor,
                        "text": text,
                        "title": 对象.备注.split("_")[0],
                        "showLabel": False,
                    }
                    static_shapes.append(message)
                    continue

                else:
                    print(type(对象), 对象)
        for item in static_shapes:
            if item.get("overrides") and item["overrides"].get("intervalsVisibilities"):
                del item["overrides"]["intervalsVisibilities"]
        # 渲染
        rendered_html = template.render(static_data=static_data, static_shapes=static_shapes, symbol=self.符号, interval=resolution, chan_config=self.配置.to_dict())

        output_file = "./new.html"
        # 写入输出文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        print(f"✅ 成功生成文件: {output_file}, 需要另行开启服务器 如 python -m http.server 8081")

    @classmethod
    def 读取数据文件(cls, 文件路径: str, ws=None, 配置=缠论配置(), *, 观察员: Optional[观察者] = None) -> Self:
        """加载数据文件
        :param 文件路径: 数据文件路径 格式如: btcusd-300-1631772074-1632222374.nb
        :param 配置: 缠论配置
        :param 观察员: 可选，已有观察者实例；不传则自动创建
        :return: 观察者实例
        """
        if "_err-" in str(文件路径) and os.path.exists(str(文件路径).replace(".nb", ".json")):
            异常配置 = 缠论配置.加载配置(str(文件路径).replace(".nb", ".json"))
            差异 = 缠论配置().对比(异常配置)
            传入差异 = 缠论配置().对比(配置)
            传入差异.update(差异)
            配置 = 缠论配置(**传入差异)
            print(f"加载异常配置+传入差异: {传入差异}")

        name = Path(文件路径).name.split(".")[0]
        符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
        if 观察员 is None:
            观察员 = cls(符号=符号, 周期=int(周期), 数据通道=ws, 配置=配置)
        else:
            观察员.符号 = 符号
            观察员.周期 = int(周期)
            观察员.配置 = 配置
        观察员.加载本地数据(文件路径)
        return 观察员

    def 识别买卖点(self):
        """
        简单买卖策略
        """
        if not self.笔序列:
            return
        if self.分型序列[-1].中.序号 + 2 < self.当前缠K.序号:
            return
        if self.分型序列[-1].强度 not in "强中":
            pass


__代码执行器_全局声明__ = dir()


def 随机配置(随机源: Optional[random.Random] = None):
    """生成随机缠论配置，可传入独立的 Random 实例以保证线程安全"""
    rng = 随机源 if 随机源 is not None else random.Random()
    return 缠论配置.不推送().from_dict(
        {
            "缠K合并替换": rng.choice((True, False)),
            "笔内元素数量": rng.randint(3, 9),
            "笔内相同终点取舍": rng.choice((True, False)),
            "笔内起始分型包含整笔": rng.choice((True, False)),
            "笔内原始K线包含整笔": rng.choice((True, False)),
            "笔次级成笔": rng.choice((True, False)),
            "笔弱化": rng.choice((True, False)),
            "笔弱化_原始数量": rng.randint(3, 9),
            "线段_非缺口下穿刺": rng.choice((True, False)),
            "线段_特征序列忽视老阴老阳": rng.choice((True, False)),
            "线段_修正": rng.choice((True, False)),
            "线段_缺口后紧急修正": rng.choice((True, False)),
            "扩展线段_当下分析": rng.choice((True, False)),
            "买卖点激进识别": rng.choice((True, False)),
            "买卖点与MACD柱强相关": rng.choice((True, False)),
        }
    )


def 测试_随机生成(symbol: str = "btcusd", limit: int = 5000, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置()):
    def 魔法():
        随机生成实例 = 观察者(symbol + "_gen", 周期=int(freq), 数据通道=ws, 配置=配置)
        dt = datetime(2008, 8, 8)
        原始K线 = K线.创建普K("随机", int(dt.timestamp()), 8888.55, 10000.00, 9000.22, 9527.33, 888, 0, int(freq))
        随机生成实例.增加原始K线(原始K线)
        for 方向 in 相对方向.从序列中机选(
            int(limit),
            [相对方向.向上, 相对方向.向上缺口, 相对方向.衔接向上, 相对方向.向下, 相对方向.向下缺口, 相对方向.衔接向下],
        ):
            原始K线 = 原始K线.根据当前K线生成新K线(方向)
            随机生成实例.增加原始K线(原始K线)

        折线 = [元素.文.分型特征值 for 元素 in 随机生成实例.笔序列]
        折线.append(随机生成实例.笔序列[-1].武.分型特征值)
        print(折线)

        return 随机生成实例

    return 魔法


class Bitstamp:
    @classmethod
    def init(cls, 观察员_, size):
        观察员 = 观察员_
        left_date_timestamp = int(datetime.now().timestamp() * 1000)
        left = int(left_date_timestamp / 1000) - 观察员.周期 * size
        if left < 0:
            raise RuntimeError
        _next = left
        while 1:
            data = cls.ohlc(观察员.符号, 观察员.周期, _next, _next := _next + 观察员.周期 * 1000)
            if not data.get("data"):
                print(data)
                raise ValueError("")
            for bar in data["data"]["ohlc"]:
                K = K线.创建普K(
                    观察员.符号,
                    转化为时间戳(int(bar["timestamp"])),
                    float(bar["open"]),
                    float(bar["high"]),
                    float(bar["low"]),
                    float(bar["close"]),
                    float(bar["volume"]),
                    0,
                    观察员.周期,
                )
                观察员.增加原始K线(K)

            # start = int(data["data"]["ohlc"][0]["timestamp"])
            end = int(data["data"]["ohlc"][-1]["timestamp"])

            _next = end
            if len(data["data"]["ohlc"]) < 100:
                break
        折线 = [元素.文.分型特征值 for 元素 in 观察员.笔序列]
        折线.append(观察员.笔序列[-1].武.分型特征值)
        # print(折线)
        K线.保存到DAT文件(
            f"./templates/{观察员.符号}-{观察员.周期}-{int(观察员.普通K线序列[0].时间戳)}-{int(观察员.普通K线序列[-1].时间戳)}.nb",
            观察员.普通K线序列,
        )
        K线.保存到DAT文件(
            "./templates/last.nb",
            观察员.普通K线序列,
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
        return
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


def 测试_读取数据(观察员, ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False)):
    def 魔法():
        启动时间 = datetime.now()
        观察者.读取数据文件(配置.加载文件路径, ws, 配置, 观察员=观察员)
        # 观察员.分部分析()
        消耗用时 = datetime.now() - 启动时间
        print(消耗用时)
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_邮局数据(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False)):
    def 魔法():
        观察员 = 观察者(symbol, int(freq), ws, 配置)
        Bitstamp.init(观察员, int(limit))
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
        观察员 = 观察者(symbol, int(freq), ws, 配置)
        观察员.数据队列 = 数据队列
        数据源 = 自定义实时数据源(数据队列, 观察员, Bitstamp.init, size=int(limit), 观察员_=观察员)
        同步_跟踪回测(观察员, 数据源)
        观察员.图表刷新()
        return 观察员

    return 魔法


def 测试_周期合成(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(), 配置组: Dict[int, 缠论配置] = None):
    def 魔法():
        周期组 = [int(freq), int(freq) * 5, int(freq) * 5 * 6]
        多级别分析 = 立体分析器(symbol, 周期组, ws, 配置, 配置组)
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
        self.安全内置函数.update({k: globals()[k] for k in __代码执行器_全局声明__ if k[0] != "_"})
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
    消息类型 = 消息字典.get("type", "")

    if 消息类型 == "ready":
        # 初始化分析器
        symbol = 消息字典.get("symbol", "btcusd")
        freq = 消息字典.get("freq", 300)
        limit = 消息字典.get("limit", 500)
        generator = 消息字典.get("generator", "True")

        config = 消息字典.get("config", dict())
        print("RAW config:", repr(config))
        当前配置 = 缠论配置.from_dict(config)
        print("", 当前配置.to_dict())

        差异 = 缠论配置().对比(当前配置)
        print(差异)
        配置组 = 缠论配置.按序号重组字典(当前配置, config)
        print(配置组)

        # 停止现有线程
        global 主线程
        if 主线程 is not None:
            主线程.join(1)
            time.sleep(1)
            主线程 = None

        观察员 = 观察者("", 60, websocket, 当前配置)
        # 创建新的分析器
        if generator == "zqhc":
            魔法 = 测试_周期合成(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置, 配置组=配置组)
        elif generator == "hc":
            魔法 = 测试_邮局数据_同步回测(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置)

        elif generator == "ex":
            魔法 = 测试_读取数据(观察员=观察员, ws=websocket, 配置=当前配置)
        elif generator == "last":
            魔法 = 测试_读取上一次数据(名称=symbol, 数量=limit, 周期=freq, ws=websocket, 配置=当前配置)

        elif generator == "lasthc":
            魔法 = 测试_读取上一次数据_回测(名称=symbol, 数量=limit, 周期=freq, ws=websocket, 配置=当前配置)

        else:
            魔法 = 测试_邮局数据(symbol=symbol, freq=freq, limit=limit, ws=websocket, 配置=当前配置)

        def 数据加载线程():
            try:
                if generator == "ex":
                    全局连接管理器.设置图表观察员(用户标识, 观察员)
                    魔法()
                else:
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

            if type(观察员) is 立体分析器:
                观察员 = 观察员._单体分析器[int(周期)]

            try:
                待发送消息 = {}
                if 数据类型 == "中枢<笔>":
                    待发送消息.update({"index": 序号, "data": str(观察员.笔_中枢序列[序号])})
                if 数据类型 == "笔":
                    待发送消息.update({"index": 序号, "data": str(观察员.笔序列[序号])})

                if "中枢" in 数据类型 and 数据类型 != "中枢<笔>":
                    for i in range(观察员.中枢分析层次):
                        if 观察员.中枢序列组[i] and 观察员.中枢序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.中枢序列组[i][序号])})
                    for i in range(观察员.扩展中枢分析层次):
                        if 观察员.扩展中枢序列组[i] and 观察员.扩展中枢序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.扩展中枢序列组[i][序号])})
                    for i in range(观察员.混合扩展中枢分析层次):
                        if 观察员.混合扩展中枢序列组[i] and 观察员.混合扩展中枢序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.混合扩展中枢序列组[i][序号])})

                elif "线段" in 数据类型 and 数据类型 != "笔":
                    for i in range(观察员.线段分析层次):
                        if 观察员.线段序列组[i] and 观察员.线段序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.线段序列组[i][序号])})
                            段 = 观察员.线段序列组[i][序号]
                            if 段._特征序列_显示:
                                段._特征序列_显示 = False
                                for 特征 in 段.特征序列:
                                    if 特征 is not None:
                                        观察员 and 观察员.报信(特征, 指令.删除(特征.标识), sys._getframe().f_lineno)

                            else:
                                段._特征序列_显示 = True
                                序号 = 0
                                for 特征 in 段.特征序列:
                                    if 特征 is not None:
                                        特征.序号 = 序号
                                        特征.标识 = f"{段.文.中.标识}:{段.文.中.周期}:{段.标识}_特征序列_{序号}:{段.序号}"
                                        观察员 and 观察员.报信(特征, 指令.添加(特征.标识), sys._getframe().f_lineno)
                                    序号 += 1

                    for i in range(观察员.扩展线段分析层次):
                        if 观察员.扩展线段序列组[i] and 观察员.扩展线段序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.扩展线段序列组[i][序号])})
                    for i in range(观察员.混合扩展线段分析层次):
                        if 观察员.混合扩展线段序列组[i] and 观察员.混合扩展线段序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.混合扩展线段序列组[i][序号])})

                if "_" in 数据类型 and "中枢" in 数据类型:  # 线段_0_实_中枢<笔>
                    数据类型, 线序, 虚实合, 类型 = 数据类型.split("_")

                    段序号 = int(线序)
                    if 数据类型 == "线段":
                        段: 虚线 = 观察员.线段序列[段序号]
                        zs = getattr(段, f"{虚实合}_中枢序列")[序号]
                        待发送消息.update({"index": 序号, "data": str(zs)})

                    if 数据类型 == "线段<线段>":
                        段: 虚线 = 观察员.线段_线段序列[段序号]
                        zs = getattr(段, f"{虚实合}_中枢序列")[序号]
                        待发送消息.update({"index": 序号, "data": str(zs)})

                    for i in range(观察员.线段分析层次):
                        if 观察员.线段序列组[i] and 观察员.线段序列组[i][0].标识 == 数据类型:
                            段 = 观察员.线段序列组[i][段序号]
                            zs = getattr(段, f"{虚实合}_中枢序列")[序号]
                            待发送消息.update({"index": 序号, "data": str(zs)})

                    for i in range(观察员.扩展线段分析层次):
                        if 观察员.扩展线段序列组[i] and 观察员.扩展线段序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.扩展线段序列组[i][序号])})
                            段 = 观察员.扩展线段序列组[i][序号]
                            zs = getattr(段, f"{虚实合}_中枢序列")[序号]
                            待发送消息.update({"index": 序号, "data": str(zs)})

                    for i in range(观察员.混合扩展线段分析层次):
                        if 观察员.混合扩展线段序列组[i] and 观察员.混合扩展线段序列组[i][0].标识 == 数据类型:
                            待发送消息.update({"index": 序号, "data": str(观察员.混合扩展线段序列组[i][序号])})
                            段 = 观察员.混合扩展线段序列组[i][序号]
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

    elif 消息类型 == "sync_shape_overrides":
        shapes_data = 消息字典["data"]
        观察员: 观察者 = 全局连接管理器.获取图表观察员(用户标识)
        if 观察员:
            观察员.将图表数据固化到本地(shapes_data)
            await 全局连接管理器.发送信息(用户标识, {"type": "sync_response", "status": "received", "count": len(shapes_data)})
        else:
            print(f"[sync_shape_overrides] 用户 {用户标识} 没有分析器！")

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
    观察者.当前事件循环 = asyncio.get_event_loop()
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


set_log_level("error")


if __name__ == "__main__":

    def 运行单个回测(线程编号: int):
        """单个线程执行的函数，内部捕获异常以免影响其他线程"""
        try:
            本地随机 = random.Random(os.urandom(64))
            配置 = 随机配置(本地随机)
            print(f"[线程{线程编号:02d}] 开始 ...")
            测试函数 = 测试_随机生成(symbol="btcusd", limit=10000, freq=时间周期.分(5), ws=None, 配置=配置)
            结果 = 测试函数()  # 实际执行
            print(f"[线程{线程编号:02d}] 完成 | 笔序列长度: {len(结果.笔序列)}")
        except Exception as e:
            print(f"[线程{线程编号:02d}] 异常: {e}")
            traceback.print_exc()

    # 创建并启动 50 个线程
    线程列表 = []
    for i in range(1, 51):
        线程 = threading.Thread(target=运行单个回测, args=(i,), name=f"回测线程-{i}")
        线程列表.append(线程)
        线程.start()

    # 等待所有线程结束
    for 线程 in 线程列表:
        线程.join()

    print("\n全部 50 个随机回测线程已完成。")
