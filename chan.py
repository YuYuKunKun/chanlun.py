"""
MIT License

Copyright (c) 2026 YuYuKunKun

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

-----------------------------------------------------------------------------
第三方代码声明 / Third-Party Code Notice
-----------------------------------------------------------------------------

本文件末尾 信号匹配框架（Signal / Factor / Event / Position / SignalsParser
等类）摘录自 czsc 项目（https://github.com/zengbin93/czsc），
根据 Apache License 2.0 授权使用。

原始许可协议全文见 https://www.apache.org/licenses/LICENSE-2.0

已做修改：中文命名适配、类型标注增强、与 chan 分析器集成的扩展。


Copyright [2025] [zengbin93]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-----------------------------------------------------------------------------
"""

# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 16:45
# @Author  : YuYuKunKun
# @File    : chan.py
from __future__ import annotations

import json
import math
import os
import re
from collections import deque, OrderedDict, defaultdict
import random
import struct
import sys
import tempfile
import hashlib
import traceback
import datetime as datetime_module
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import (
    List,
    Self,
    Optional,
    Tuple,
    final,
    Dict,
    Any,
    Union,
    Sequence,
    Callable,
    Set,
    Generator,
)

from loguru import logger
from parse import parse

__all__ = [
    "K线",
    "K线合成器",
    "中枢",
    "买卖点",
    "买卖点类型",
    "分型",
    "分型结构",
    "基础买卖点",
    "平滑异同移动平均线",
    "指标",
    "指标容器",
    "测试_读取数据",
    "特征分型",
    "相对强弱指数",
    "相对方向",
    "立体分析器",
    "笔",
    "线段",
    "线段特征",
    "缠论K线",
    "缠论配置",
    "缺口",
    "背驰分析",
    "虚线",
    "观察者",
    "转化为时间戳",
    "转化为时间戳_数字",
    "随机指标",
    "布林带",
    "set_log_level",
    "get_log_level",
    "import_by_name",
    "Signal",
    "Factor",
    "Event",
    "SignalsParser",
    "get_signals_config",
    "create_single_signal",
    "Position",
    "信号计算器",
]

# 日志级别映射: 名称 → loguru 级别名
_级别映射 = {
    "trace": "TRACE",
    "debug": "DEBUG",
    "info": "INFO",
    "warn": "WARNING",
    "error": "ERROR",
    "off": "OFF",
}
_有效级别 = frozenset(_级别映射.keys())
_当前日志级别 = "info"


def set_log_level(level: str):
    """设置 Python 侧日志级别。

    :param level: 日志级别，不区分大小写 (trace / debug / info / warn / error / off)
    """
    global _当前日志级别
    _level = level.lower()
    if _level not in _有效级别:
        raise ValueError(f"无效日志级别 '{level}'，有效值: {', '.join(sorted(_有效级别))}")

    _当前日志级别 = _level
    _loguru_level = _级别映射[_level]

    try:
        logger.remove(0)
    except ValueError:
        pass
    if _loguru_level != "OFF":
        logger.add(sys.stderr, level=_loguru_level)


def get_log_level() -> str:
    """获取 Python 侧当前日志级别。

    :return: 日志级别字符串 (trace / debug / info / warn / error / off)
    """
    return _当前日志级别


set_log_level("error")

REGISTRY = {}


def 注册(obj):
    """
    通用装饰器：支持函数和类。
    obj 可以是 function，也可以是 class。
    """
    REGISTRY[obj.__name__] = obj
    return obj


def 注入依赖(目标模块):
    """批量注入到目标模块"""
    for name, obj in REGISTRY.items():
        setattr(目标模块, name, obj)
    logger.warning(f"成功自动注入: {list(REGISTRY.keys())}")


@注册
class 买卖点类型(str, Enum):
    """买卖点类型 — 缠论的三类买卖点及扩展类型。

    :ivar 是买点: 是否为买入类型
    :ivar 是卖点: 是否为卖出类型
    """

    # 传统分类
    一买 = "一买"
    一卖 = "一卖"
    二买 = "二买"
    二卖 = "二卖"
    三买 = "三买"
    三卖 = "三卖"
    # 缠论六类买卖点
    T1买 = "T1买"
    T1卖 = "T1卖"
    T1P买 = "T1P买"
    T1P卖 = "T1P卖"
    T2买 = "T2买"
    T2卖 = "T2卖"
    T2S买 = "T2S买"
    T2S卖 = "T2S卖"
    T3A买 = "T3A买"
    T3A卖 = "T3A卖"
    T3B买 = "T3B买"
    T3B卖 = "T3B卖"

    def __str__(self) -> str:
        """返回买卖点类型名称"""
        return self.name

    def __repr__(self) -> str:
        """返回买卖点类型名称"""
        return self.name

    @property
    def 是买点(self) -> bool:
        """判断是否为买入类型（名称中含"买"字）

        :return: 是否为买入类型
        """
        return "买" in self.value

    @property
    def 是卖点(self) -> bool:
        """判断是否为卖出类型（名称中含"卖"字）

        :return: 是否为卖出类型
        """
        return "卖" in self.value


@注册
class 基础买卖点:
    """基础买卖点 — 描述偏离买入/卖出位置的程度。

    :ivar 备注: 描述文本
    :ivar 偏移: 当前K线相对于买卖点K线的偏移量
    :ivar 失效偏移: 失效K线相对于买卖点K线的偏移量（-1表示未失效）
    :ivar 有效性: 是否已失效（存在失效K线）
    :ivar 破位值: 中枢破位价格
    :ivar 与MACD柱子匹配: MACD柱子是否匹配买卖点方向
    :ivar 与MACD柱子分型匹配: MACD柱子分型是否匹配
    """

    def __init__(self, 类型: 买卖点类型, 当前K线: K线, 买卖点分型: 分型, 备注: str, 中枢破位值: float):
        """
        :param 类型: 买卖点类型
        :param 当前K线: 触发买卖点的K线
        :param 买卖点分型: 买卖点对应的分型
        :param 备注: 描述文本（如"笔_1买"）
        :param 中枢破位值: 中枢破位价格
        """
        self.备注: str = 备注
        self.类型 = 类型
        self.买卖点分型 = 买卖点分型
        self.买卖点K线 = 买卖点分型.中  # .镜像
        self.__当前K线: K线 = 当前K线
        self.失效K线: Optional[K线] = None
        self.终结K线: Optional[K线] = None  # 卖出 or 买入
        self.__破位值 = 中枢破位值
        self.结构 = None

    def __str__(self):
        return f"{self.类型.value}<{self.买卖点K线}, {self.偏移}, {self.失效偏移}>"

    def __repr__(self):
        return f"{self.类型.value}<{self.买卖点K线}, {self.偏移}, {self.失效偏移}>"

    @property
    def 当前K线(self):
        """触发该买卖点的原始K线"""
        return self.__当前K线

    @property
    def 破位值(self) -> float:
        """中枢破位价格。

        :return: 买卖点K线突破中枢边界的价位
        """
        return self.__破位值

    @property
    def 偏移(self) -> int:
        """当前K线与买卖点K线的序号差。

        :return: 买卖点产生后经过的K线根数
        """
        return self.__当前K线.序号 - self.买卖点K线.序号

    @property
    def 失效偏移(self) -> int:
        """失效K线与买卖点K线的序号差。

        :return: 序号差值，-1 表示尚未失效
        """
        if self.失效K线 is None:
            return -1
        return self.失效K线.序号 - self.买卖点K线.序号

    @property
    def 有效性(self) -> bool:
        """是否已失效。

        :return: 存在失效K线时返回 True
        """
        return self.失效K线 is not None

    @property
    def 与MACD柱子匹配(self) -> bool:
        """MACD柱方向是否与买卖点方向一致。

        :return: 一致返回 True
        """
        return self.买卖点K线.与MACD柱子匹配

    @property
    def 与MACD柱子分型匹配(self) -> bool:
        """买卖点分型的MACD柱面积方向是否与买卖点方向一致。

        :return: 一致返回 True
        """
        return self.买卖点分型.与MACD柱子分型匹配


@注册
@final
class 买卖点(基础买卖点):
    """一二三类买卖点及扩展类型（T1/T1P/T2/T2S/T3A/T3B）的构造器。

    提供18种类方法创建对应买卖点实例，以及一个通用路由方法：

    主要方法:
      :meth:`一卖点` / :meth:`一买点` / :meth:`二卖点` / :meth:`二买点` / :meth:`三卖点` / :meth:`三买点`
      :meth:`T1卖点` / :meth:`T1买点` / :meth:`T1P卖点` / :meth:`T1P买点`
      :meth:`T2卖点` / :meth:`T2买点` / :meth:`T2S卖点` / :meth:`T2S买点`
      :meth:`T3A卖点` / :meth:`T3A买点` / :meth:`T3B卖点` / :meth:`T3B买点`
      :meth:`生成买卖点` — 根据特征和序号路由到对应构造函数
    """

    @classmethod
    def 一卖点(cls, 买卖点分型: 分型, 当前K线: K线, 标识: str, 备注: str, 中枢破位值: float) -> 买卖点:
        """
        :param 买卖点分型: 买卖点对应的分型
        :param 当前K线: 当前K线
        :param 标识: 标识（未使用，仅保持接口一致）
        :param 备注: 描述文本
        :param 中枢破位值: 中枢破位价格
        :return: '买卖点'
        """
        return 买卖点(备注=备注, 类型=买卖点类型.一卖, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 一买点(cls, 买卖点分型: 分型, 当前K线: K线, 标识: str, 备注: str, 中枢破位值: float) -> 买卖点:
        """
        :param 买卖点分型: 买卖点对应的分型
        :param 当前K线: 当前K线
        :param 标识: 标识（未使用，仅保持接口一致）
        :param 备注: 描述文本
        :param 中枢破位值: 中枢破位价格
        :return: '买卖点'
        """
        return 买卖点(备注=备注, 类型=买卖点类型.一买, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 二卖点(cls, 买卖点分型: 分型, 当前K线: K线, 标识: str, 备注: str, 中枢破位值: float) -> 买卖点:
        """
        :param 买卖点分型: 买卖点对应的分型
        :param 当前K线: 当前K线
        :param 标识: 标识（未使用，仅保持接口一致）
        :param 备注: 描述文本
        :param 中枢破位值: 中枢破位价格
        :return: '买卖点'
        """
        return 买卖点(备注=备注, 类型=买卖点类型.二卖, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 二买点(cls, 买卖点分型: 分型, 当前K线: K线, 标识: str, 备注: str, 中枢破位值: float) -> 买卖点:
        """
        :param 买卖点分型: 买卖点对应的分型
        :param 当前K线: 当前K线
        :param 标识: 标识（未使用，仅保持接口一致）
        :param 备注: 描述文本
        :param 中枢破位值: 中枢破位价格
        :return: '买卖点'
        """
        return 买卖点(备注=备注, 类型=买卖点类型.二买, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 三卖点(cls, 买卖点分型: 分型, 当前K线: K线, 标识: str, 备注: str, 中枢破位值: float) -> 买卖点:
        """
        :param 买卖点分型: 买卖点对应的分型
        :param 当前K线: 当前K线
        :param 标识: 标识（未使用，仅保持接口一致）
        :param 备注: 描述文本
        :param 中枢破位值: 中枢破位价格
        :return: '买卖点'
        """
        return 买卖点(备注=备注, 类型=买卖点类型.三卖, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 三买点(cls, 买卖点分型: 分型, 当前K线: K线, 标识: str, 备注: str, 中枢破位值: float) -> 买卖点:
        """
        :param 买卖点分型: 买卖点对应的分型
        :param 当前K线: 当前K线
        :param 标识: 标识（未使用，仅保持接口一致）
        :param 备注: 描述文本
        :param 中枢破位值: 中枢破位价格
        :return: '买卖点'
        """
        return 买卖点(备注=备注, 类型=买卖点类型.三买, 买卖点分型=买卖点分型, 当前K线=当前K线, 中枢破位值=中枢破位值)

    @classmethod
    def 生成买卖点(cls, 特征: str, 序号: str, 级别: str, 买卖点分型: 分型, 当前缠K: 缠论K线):
        """
        :param 特征: 特征字符串
        :param 序号: 序号（如"一"、"二"、"三"）
        :param 级别: 级别字符串
        :param 买卖点分型: 买卖点对应的分型
        :param 当前缠K: 当前缠论K线
        """
        买卖 = "买" if 买卖点分型.结构 in (分型结构.底, 分型结构.下) else "卖"
        第几 = 序号
        备注 = f"{特征}_{级别}{第几}{买卖}"
        买卖点函数 = getattr(买卖点, f"{第几}{买卖}点")
        破位值 = 买卖点分型.分型特征值
        return 买卖点函数(买卖点分型, 当前缠K, 特征, 备注, 破位值)


@注册
class datetime(datetime):  # 用于对齐C输出
    def __s2tr__(self):
        return f"{int(self.timestamp())}"

    def __re2pr__(self):
        return f"{int(self.timestamp())}"

    def __int__(self) -> int:
        return int(self.timestamp())


@注册
def 转化为时间戳(ts: Union[str, datetime, int, float]) -> datetime:
    """
    将不同类型的时间戳转换为datetime对象（统一比较标准）
    支持：datetime对象、字符串（"%Y-%m-%d %H:%M:%S"）、数值型时间戳（秒级）
    可根据实际需求扩展时间格式（如毫秒级、仅日期等）

    :param ts: 待转换的时间戳
    :return: datetime对象
    :raises TypeError: 不支持的类型
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


@注册
def 转化为时间戳_数字(ts: Union[str, datetime, int, float]) -> int:
    """
    将不同类型的时间戳转换为整数秒级时间戳

    :param ts: 待转换的时间戳
    :return: 整数秒级时间戳
    :raises TypeError: 不支持的类型
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


# 模拟 Pydantic 的 ValidationError，保持原有异常逻辑兼容
class ValidationError(Exception):
    pass


@注册
@final
class 缠论配置:
    """控制缠论分析各阶段行为的全局参数集。

    共 60+ 个字段，均有合理默认值。按功能分组：

    **[基础]** 标识 \\
    **[缠K]** 缠K合并替换 \\
    **[笔]** 笔内元素数量, 笔弱化, 笔次成笔, 笔内相同终点取舍 等 \\
    **[线段]** 线段_特征序列忽视老阴老阳, 线段_缺口后紧急修正, 线段内部中枢图显 等 \\
    **[分析开关]** 分析笔, 分析线段, 分析扩展线段, 分析笔中枢, 分析线段中枢 \\
    **[指标]** 计算指标, 指标计算方式, MACD/RSI/KDJ 参数 \\
    **[推送/显示]** 图表展示 (主开关), 图表展示标签 (标签列表) 等 \\
    **[买卖点]** 买卖点偏移, 买卖点激进识别, 买卖点_背离率, 买卖点_计算方式 等 \\
    **[背驰]** 线段内部背驰_MACD, 线段内部背驰_斜率 等 \\
    **[其他]** 手动终止, 加载文件路径

    主要方法:
        :meth:`to_dict` / :meth:`to_json` — 序列化 \\
        :meth:`from_dict` / :meth:`from_json` — 反序列化 \\
        :meth:`保存配置` / :meth:`加载配置` — 文件读写 \\
        :meth:`不推送` — 创建静默配置 \\
        :meth:`对比` — 比较两个配置
    """

    def __init__(
        self,
        标识: str = "bar",
        缠K合并替换: bool = False,  # False: 在原缠K上合并, True: 产出新缠K
        笔内元素数量: int = 5,  # 成笔最低长度
        笔内相同终点取舍: bool = False,  # 一笔终点存在多个终点时 True: last, False: first
        笔内起始分型包含整笔: bool = False,  # True: 一笔起始分型高低包含整支笔对象则不成笔, False: 只判断分型中间数据是否包含
        笔内起始分型包含整笔_包括右: bool = False,  # True: 将笔之武.右纳入
        笔内原始K线包含整笔: bool = False,  # 在非 [笔内起始分型包含整笔] 时判断原始K线包含整笔的情况
        笔次级成笔: bool = False,
        笔弱化: bool = False,
        笔弱化_原始数量: int = 3,
        # 笔_必须对齐:bool = False # 强迫症设为True, 将获得无与伦比满足。。。
        线段_非缺口下穿刺: bool = False,  # True: 非缺口状态下[小阳, 少阴]时，存在贯穿伤与之后紧邻的三个元素有方向相同的线段时回退， 此举在当下是否有任何意义呢？
        线段_特征序列忽视老阴老阳: bool = False,  # True 不用严格的特征序列包含，也就是忽视缺口全以无缺口对待
        线段_缺口后紧急修正: bool = True,  # True: 当 线段_特征序列忽视老阴老阳=False 时生效，同样 线段_特征序列忽视老阴老阳=True时等同于修正武斗不异常，但只产出一个线段
        线段_修正: bool = False,  # 短路修正，不建议使用，但此修正将走势显示的更加清晰
        线段内部中枢图显: bool = True,
        扩展线段_当下分析: bool = False,  # 以当下来看的分析规则，否则以事后来看
        分析笔: bool = True,
        分析线段: bool = True,
        分析扩展线段: bool = True,
        分析笔中枢: bool = True,
        分析线段中枢: bool = True,
        手动终止: str = "",  # 2099-12-31 00:00:00
        计算指标: bool = True,
        指标计算方式: str = "收",  # 均线计算方式
        均线参数列表: List[tuple] = None,  # [(key, 计算方式, 类型, 周期), ...]
        # 多参数指标列表（None/空列表 = 使用默认单参数）
        MACD_参数列表: List[tuple] = None,  # [(key, 计算方式, 快线, 慢线, 信号), ...]
        RSI_周期列表: List[tuple] = None,  # [(key, 计算方式, 周期), ...]
        KDJ_参数列表: List[tuple] = None,  # [(key, 计算方式, RSV周期, K平滑, D平滑), ...]
        BOLL_参数列表: List[tuple] = None,  # [(key, 计算方式, 周期, 标准差倍数), ...]
        图表展示: bool = True,  # 图表系统主开关
        图表展示标签: Optional[List[str]] = None,  # None=全部展示, []=不展示, [\"笔\",\"线段\"]=指定
        买卖点偏移: int = 1,  # 最大偏移
        买卖点激进识别: bool = False,  # 激进模式下将不考虑分型的完整性
        买卖点与MACD柱强相关: bool = False,  # True: 卖点需正值 买点需负值
        买卖点错过误差值: float = 0.01,  # 距离买卖点值上下之内
        买卖点_指标模式: str = "配置",  # 【任意，配置，全量, 相对】 对应K线
        买卖点_指标匹配_MACD: bool = True,  # 买在负，卖在正！
        买卖点_指标匹配_KDJ: bool = True,  # 买在死叉之后，卖在金叉之后
        买卖点_指标匹配_RSI: bool = True,  # 买在均线之下，卖在均线之上
        线段内部背驰_MACD: bool = True,
        线段内部背驰_斜率: bool = True,
        线段内部背驰_测度: bool = True,
        线段内部背驰_模式: str = "相对",  # 【任意，配置，全量，相对】
        加载文件路径: str = "",
    ):
        # 所有字段赋值
        self.标识 = 标识
        self.缠K合并替换 = 缠K合并替换
        self.笔内元素数量 = 笔内元素数量
        self.笔内相同终点取舍 = 笔内相同终点取舍
        self.笔内起始分型包含整笔 = 笔内起始分型包含整笔
        self.笔内起始分型包含整笔_包括右 = 笔内起始分型包含整笔_包括右
        self.笔内原始K线包含整笔 = 笔内原始K线包含整笔
        self.笔次级成笔 = 笔次级成笔
        self.笔弱化 = 笔弱化
        self.笔弱化_原始数量 = 笔弱化_原始数量
        self.线段_非缺口下穿刺 = 线段_非缺口下穿刺
        self.线段_特征序列忽视老阴老阳 = 线段_特征序列忽视老阴老阳
        self.线段_缺口后紧急修正 = 线段_缺口后紧急修正
        self.线段_修正 = 线段_修正
        self.线段内部中枢图显 = 线段内部中枢图显
        self.扩展线段_当下分析 = 扩展线段_当下分析
        self.分析笔 = 分析笔
        self.分析线段 = 分析线段
        self.分析扩展线段 = 分析扩展线段
        self.分析笔中枢 = 分析笔中枢
        self.分析线段中枢 = 分析线段中枢
        self.手动终止 = 手动终止
        self.计算指标 = 计算指标
        self.指标计算方式 = 指标计算方式
        self.均线参数列表 = 均线参数列表 if 均线参数列表 is not None else []
        self.MACD_参数列表 = MACD_参数列表 if MACD_参数列表 is not None else [("macd", "收", 13, 31, 11)]
        self.RSI_周期列表 = RSI_周期列表 if RSI_周期列表 is not None else [("rsi", "收", 14, 13, 75.0, 25.0)]
        self.KDJ_参数列表 = KDJ_参数列表 if KDJ_参数列表 is not None else [("kdj", "收", 13, 5, 5, 80.0, 20.0)]
        self.BOLL_参数列表 = BOLL_参数列表 if BOLL_参数列表 is not None else [("boll", "收", 20, 2.0)]
        self.图表展示 = 图表展示
        self.图表展示标签 = set(图表展示标签) if 图表展示标签 is not None else None
        self.买卖点偏移 = 买卖点偏移
        self.买卖点激进识别 = 买卖点激进识别
        self.买卖点与MACD柱强相关 = 买卖点与MACD柱强相关
        self.买卖点错过误差值 = 买卖点错过误差值
        self.买卖点_指标模式 = 买卖点_指标模式
        self.买卖点_指标匹配_MACD = 买卖点_指标匹配_MACD
        self.买卖点_指标匹配_KDJ = 买卖点_指标匹配_KDJ
        self.买卖点_指标匹配_RSI = 买卖点_指标匹配_RSI
        self.线段内部背驰_MACD = 线段内部背驰_MACD
        self.线段内部背驰_斜率 = 线段内部背驰_斜率
        self.线段内部背驰_测度 = 线段内部背驰_测度
        self.线段内部背驰_模式 = 线段内部背驰_模式
        self.加载文件路径 = 加载文件路径

        # 执行初始化验证
        self._validate_all_fields()

    # 定义所有字段名列表（替代 model_fields）
    @classmethod
    def model_fields(cls) -> Dict[str, Dict[str, Any]]:
        """返回类所有字段的元信息。

        :return: 字段名到类型/默认值元信息的映射
        """
        return {
            "标识": {"annotation": str, "default": "bar"},
            "缠K合并替换": {"annotation": bool, "default": False},
            "笔内元素数量": {"annotation": int, "default": 5},
            "笔内相同终点取舍": {"annotation": bool, "default": False},
            "笔内起始分型包含整笔": {"annotation": bool, "default": False},
            "笔内起始分型包含整笔_包括右": {"annotation": bool, "default": False},
            "笔内原始K线包含整笔": {"annotation": bool, "default": False},
            "笔次级成笔": {"annotation": bool, "default": False},
            "笔弱化": {"annotation": bool, "default": False},
            "笔弱化_原始数量": {"annotation": int, "default": 3},
            "线段_非缺口下穿刺": {"annotation": bool, "default": False},
            "线段_特征序列忽视老阴老阳": {"annotation": bool, "default": False},
            "线段_缺口后紧急修正": {"annotation": bool, "default": True},
            "线段_修正": {"annotation": bool, "default": False},
            "线段内部中枢图显": {"annotation": bool, "default": True},
            "扩展线段_当下分析": {"annotation": bool, "default": False},
            "分析笔": {"annotation": bool, "default": True},
            "分析线段": {"annotation": bool, "default": True},
            "分析扩展线段": {"annotation": bool, "default": True},
            "分析笔中枢": {"annotation": bool, "default": True},
            "分析线段中枢": {"annotation": bool, "default": True},
            "手动终止": {"annotation": str, "default": ""},
            "计算指标": {"annotation": bool, "default": True},
            "指标计算方式": {"annotation": str, "default": "收"},
            "均线参数列表": {"annotation": List[tuple], "default": []},
            "MACD_参数列表": {"annotation": List[tuple], "default": [("macd", "收", 13, 31, 11)]},
            "RSI_周期列表": {"annotation": List[tuple], "default": [("rsi", "收", 14, 13, 75.0, 25.0)]},
            "KDJ_参数列表": {"annotation": List[tuple], "default": [("kdj", "收", 13, 5, 5, 80.0, 20.0)]},
            "BOLL_参数列表": {"annotation": List[tuple], "default": [("boll", "收", 20, 2.0)]},
            "图表展示": {"annotation": bool, "default": True},
            "图表展示标签": {"annotation": Optional[List[str]], "default": None},
            "买卖点偏移": {"annotation": int, "default": 1},
            "买卖点激进识别": {"annotation": bool, "default": False},
            "买卖点与MACD柱强相关": {"annotation": bool, "default": False},
            "买卖点错过误差值": {"annotation": float, "default": 0.01},
            "买卖点_指标模式": {"annotation": str, "default": "配置"},
            "买卖点_指标匹配_MACD": {"annotation": bool, "default": True},
            "买卖点_指标匹配_KDJ": {"annotation": bool, "default": True},
            "买卖点_指标匹配_RSI": {"annotation": bool, "default": True},
            "线段内部背驰_MACD": {"annotation": bool, "default": True},
            "线段内部背驰_斜率": {"annotation": bool, "default": True},
            "线段内部背驰_测度": {"annotation": bool, "default": True},
            "线段内部背驰_模式": {"annotation": str, "default": "相对"},
            "加载文件路径": {"annotation": str, "default": ""},
        }

    def _validate_all_fields(self):
        """统一验证所有字段，替代原 field_validator"""
        允许值 = {
            "指标计算方式": ["开", "高", "低", "收", "高低均值", "高低收均值", "开高低收均值"],
        }
        fields = self.model_fields()

        for fname, field_info in fields.items():
            value = getattr(self, fname)
            type_ = field_info["annotation"]
            default = field_info["default"]

            try:
                # 布尔类型验证（与 Rust 绑定层 coerce_strings_to_numbers 对齐）
                if type_ is bool:
                    if not isinstance(value, bool):
                        if isinstance(value, str) and value.lower() in ("true", "false"):
                            setattr(self, fname, value.lower() == "true")
                        else:
                            setattr(self, fname, default)

                # 整数类型验证
                elif type_ is int:
                    if not isinstance(value, int):
                        setattr(self, fname, int(value))

                # 枚举字符串验证
                elif fname in 允许值:
                    if value not in 允许值[fname]:
                        logger.warning(f"[{fname}] = {value} 值不在允许范围内，使用默认值：{default}")
                        setattr(self, fname, default)

            except (ValueError, TypeError) as e:
                logger.warning(f"[{fname}] = {value} 解析失败，使用默认值：{default}")
                setattr(self, fname, default)

    def 设置指标(
        self,
        *,
        均线: List[tuple] = None,
        MACD: List[tuple] = None,
        RSI: List[tuple] = None,
        KDJ: List[tuple] = None,
        BOLL: List[tuple] = None,
    ):
        """统一设置所有指标参数。

        元组格式 ``(key, 计算方式, *params)``：
        - 均线: ``("SMA_5", "收", "SMA", 5)`` — key/计算方式/类型/周期
        - MACD: ``("默认", "收", 13, 31, 11)`` — 快线/慢线/信号
        - RSI:  ``("默认", "收", 14, 13, 75, 25)`` — 周期/MA周期/超买/超卖
        - KDJ:  ``("默认", "收", 13, 5, 5, 80, 20)`` — RSV/K平滑/D平滑/超买/超卖
        - BOLL: ``("默认", "收", 20, 2.0)`` — 周期/标准差倍数

        :param 均线: key 即均线名（如 ``"SMA_5"``），同时编码类型和周期
        :param MACD: 首个 key 同时写入 ``"macd"`` 兼容槽位
        :param BOLL: BOLL 参数元组列表，为空则不计算
        """
        self.计算指标 = True
        if 均线 is not None:
            self.均线参数列表 = 均线
        if MACD is not None:
            self.MACD_参数列表 = MACD
        if RSI is not None:
            self.RSI_周期列表 = RSI
        if KDJ is not None:
            self.KDJ_参数列表 = KDJ
        if BOLL is not None:
            self.BOLL_参数列表 = BOLL

    def 展示标签(self, 标签: str) -> bool:
        """判断指定标签是否应展示。None = 全部展示，空列表 = 全部隐藏。"""
        if self.图表展示标签 is None:
            return True
        return 标签 in self.图表展示标签

    @classmethod
    def 兼容旧版本配置(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """过滤字典中不属于当前配置类的字段，实现前后版本兼容。

        :param values: 包含配置键值对的原始字典
        :return: 仅保留当前类已知字段的字典
        """
        valid_fields = cls.model_fields().keys()
        cleaned = {}
        for k, v in values.items():
            if k not in valid_fields:
                continue
            # 字符串值类型强制转换（与 Rust 绑定层 coerce_strings_to_numbers 对齐）
            if isinstance(v, str):
                if v.lower() in ("true", "false"):
                    v = v.lower() == "true"
                elif v.lstrip("-").isdigit():
                    v = int(v)
                else:
                    try:
                        v = float(v)
                    except ValueError:
                        pass
            cleaned[k] = v
        return cleaned

    def to_dict(self) -> dict:
        """将配置序列化为字典。

        :return: 包含所有配置字段的字典
        """
        result = {}
        for k in self.model_fields().keys():
            v = getattr(self, k)
            if isinstance(v, set):
                v = list(v)
            result[k] = v
        return result

    def to_json(self) -> str:
        """将配置序列化为 JSON 字符串。

        :return: 格式化的 JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def 保存配置(self, path="缠论配置.json"):
        """将配置保存为 JSON 文件。

        :param path: 文件保存路径，默认 "缠论配置.json"
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def 加载配置(cls, path="缠论配置.json") -> 缠论配置:
        """从 JSON 文件加载配置。

        :param path: JSON 文件路径，默认 "缠论配置.json"
        :return: 从文件反序列化的配置对象
        """
        with open(path, encoding="utf-8") as f:
            return cls.from_json(f.read())

    @classmethod
    def from_dict(cls, data: dict) -> 缠论配置:
        """从字典构造配置对象。

        :param data: 包含配置键值对的字典
        :return: 新的配置实例
        """
        cleaned_data = cls.兼容旧版本配置(data)
        return cls(**cleaned_data)

    @classmethod
    def from_json(cls, json_str: str) -> 缠论配置:
        """从 JSON 字符串构造配置对象。

        :param json_str: JSON 格式的配置字符串
        :return: 新的配置实例
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def 不推送(cls):
        """创建不推送任何图表的静默配置。

        所有图表推送开关关闭，适用于纯计算场景。
        """
        return cls(
            线段内部中枢图显=False,
            图表展示=False,
            图表展示标签=[],
        )

    def model_copy(self, update: dict = None, deep: bool = True):
        """创建配置副本，可选覆盖部分字段。

        :param update: 需要覆盖的字段字典
        :param deep: 是否深拷贝（保留参数兼容性，内部始终深拷贝）
        :return: 新的配置实例
        """
        data = self.to_dict()
        if update:
            data.update(update)
        return 缠论配置.from_dict(data)

    @classmethod
    def 按序号重组字典(cls, 默认配置, 原始字典: dict) -> dict:
        """将带数字前缀的扁平字典重组成按序号索引的配置组。

        键名格式如 "1_笔模式" 会拆分出序号 1，同序号的键归入同一子配置。
        无法拆分序号前缀的键合并为通用配置。

        :param 默认配置: 用作模板的默认配置对象
        :param 原始字典: 带数字前缀的扁平键值对字典
        :return: dict[int, 缠论配置] 按序号索引的配置组
        """
        结果 = {}
        无法拆分项 = {}

        for 复合键, 值 in 原始字典.items():
            if "_" in 复合键:
                序号部分, 键部分 = 复合键.split("_", 1)
                try:
                    序号 = int(序号部分)
                    if 序号 not in 结果:
                        结果[序号] = {}
                    结果[序号][键部分] = 值
                except:
                    无法拆分项[复合键] = 值
            else:
                无法拆分项[复合键] = 值

        配置组 = dict()
        for k, v in 结果.items():
            配置组[k] = 默认配置.model_copy(update=v, deep=True)

        return 配置组

    def 对比(self, other: 缠论配置) -> dict:
        """比较两个配置的差异。

        :param other: 要比较的另一个配置对象
        :return: 差异字段及其在新配置中的值
        """
        diff_dict = {}
        for field_name in self.model_fields().keys():
            old_value = getattr(self, field_name)
            new_value = getattr(other, field_name)
            if old_value != new_value:
                diff_dict[field_name] = new_value
        return diff_dict


@注册
class 相对方向(Enum):
    """相对方向 — 描述两个K线/分型之间相对位置关系的枚举。

    类属性: 向上, 向下, 向上缺口, 向下缺口, 衔接向上, 衔接向下, 顺, 逆, 同

    :ivar 是否向上: 判断是否为向上方向
    :ivar 是否向下: 判断是否为向下方向
    :ivar 是否包含: 判断是否为包含关系
    :ivar 是否缺口: 判断是否有缺口
    :ivar 是否衔接: 判断是否为首尾衔接
    """

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

    def 翻转(self) -> 相对方向:
        """返回方向的对立面。

        :return: 对立方向 (向上↔向下, 向上缺口↔向下缺口, 顺↔逆, 衔接向上↔衔接向下, 同不变)
        """
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
        """判断是否为向上方向。

        :return: 方向为 向上/向上缺口/衔接向上 时返回 True
        """
        return self in (相对方向.向上, 相对方向.向上缺口, 相对方向.衔接向上)

    def 是否向下(self) -> bool:
        """判断是否为向下方向。

        :return: 方向为 向下/向下缺口/衔接向下 时返回 True
        """
        return self in (相对方向.向下, 相对方向.向下缺口, 相对方向.衔接向下)

    def 是否包含(self) -> bool:
        """判断是否为包含关系。

        :return: 方向为 顺/逆/同 时返回 True
        """
        return self in (相对方向.顺, 相对方向.逆, 相对方向.同)

    def 是否缺口(self) -> bool:
        """判断是否有缺口。

        :return: 方向为 向下缺口/向上缺口 时返回 True
        """
        return self in (相对方向.向下缺口, 相对方向.向上缺口)

    def 是否衔接(self) -> bool:
        """判断是否为首尾衔接。

        :return: 方向为 衔接向下/衔接向上 时返回 True
        """
        return self in (相对方向.衔接向下, 相对方向.衔接向上)

    @classmethod
    def 分析(cls, 前高: float, 前低: float, 后高: float, 后低: float) -> 相对方向:
        """分析两个价格区间（前、后）的相对位置关系。

        :param 前高: 前方价格区间的最高价
        :param 前低: 前方价格区间的最低价
        :param 后高: 后方价格区间的最高价
        :param 后低: 后方价格区间的最低价
        :return: 相对方向枚举值（向上/向下/向上缺口/向下缺口/衔接向上/衔接向下/顺/逆/同）
        :raises RuntimeError: 无法识别的方向
        """
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

    @classmethod
    def 从序列中机选(
        cls,
        数量: int,
        可选方向: List["相对方向"],
        可重复: bool = True,  # 是否允许重复选择
    ) -> Generator["相对方向", None, None]:
        if not 可重复 and 数量 > len(可选方向):
            raise ValueError("数量超过可选方向数")

        if 可重复:
            while 数量 > 0:
                yield random.choice(可选方向)
                数量 -= 1
        else:
            yield from random.sample(可选方向, 数量)


@注册
class 分型结构(Enum):
    """描述三根K线构成的顶底分型形态。

    :ivar 上: 三连向上 — 左中右逐步抬高
    :ivar 下: 三连向下 — 左中右逐步走低
    :ivar 顶: 顶分型 — 左右低、中间高
    :ivar 底: 底分型 — 左右高、中间低
    :ivar 散: 向右扩散 — 无法判定
    """

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
    def 分析(cls, 左, 中, 右, 可以逆序包含: bool = False, 忽视顺序包含: bool = False) -> Optional[分型结构]:
        """分析左中右三个元素构成的分型形态。

        :param 左: 左侧元素（必须有 高/低 属性）
        :param 中: 中间元素
        :param 右: 右侧元素
        :param 可以逆序包含: True 时允许逆序包含关系（如 右>左>中）
        :param 忽视顺序包含: True 时跳过顺序包含检查（如 左>中>右）
        :return: 分型结构（顶/底/上/下/散），无法判定返回 None
        """
        左中关系 = 相对方向.分析(左.高, 左.低, 中.高, 中.低)
        中右关系 = 相对方向.分析(中.高, 中.低, 右.高, 右.低)
        # 左右关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
        match (左中关系, 中右关系):
            case (相对方向.顺, _):
                if 忽视顺序包含:
                    ...  # logger.warning("顺序包含 左中相对方向", 左, 中)
                else:
                    raise ValueError("顺序包含 左中相对方向", 左, 中)
            case (_, 相对方向.顺):
                if 忽视顺序包含:
                    ...  # logger.warning("顺序包含 中右相对方向", 中, 右)
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
                logger.warning(f"未匹配的关系 {可以逆序包含}, {左中关系}, {中右关系}")
        return None


@注册
@final
class 缺口:
    """缺口 — 描述价格区间之间的缺口（未重叠部分）。

    :ivar 高: 缺口上沿
    :ivar 低: 缺口下沿
    """

    def __init__(self, 高: float, 低: float) -> None:
        """
        :param 高: 缺口上沿
        :param 低: 缺口下沿
        """
        assert 高 > 低
        self.高 = 高
        self.低 = 低

    def __str__(self) -> str:
        return f"缺口区间<{self.低:g} <=> {self.高:g}>"

    def __repr__(self) -> str:
        return f"缺口区间<{self.低:g} <=> {self.高:g}>"

    @classmethod
    def 居中截取区间(cls, 起点: float, 终点: float, 比例: float = 0.15) -> Optional[缺口]:
        """
        以原区间中心为基准，向两侧各取总长度的 `比例` 作为新区间。
        如果新区间超出原边界则裁剪到边界；若完全越界则返回 None。

        :param 起点: 区间起始值
        :param 终点: 区间结束值
        :param 比例: 向两侧扩展的长度占总长度的比例（0~1 之间）
        :return: Optional[缺口]
        """
        if 起点 > 终点:
            起点, 终点 = 终点, 起点
        总长 = 终点 - 起点
        偏移 = 总长 * 比例
        中心 = (起点 + 终点) / 2
        下界 = 中心 - 偏移
        上界 = 中心 + 偏移

        # 完全越界：新区间与原区间无重叠
        if 下界 > 终点 or 上界 < 起点:
            return None

        # 裁剪到原边界
        if 下界 < 起点:
            下界 = 起点
        if 上界 > 终点:
            上界 = 终点

        高 = max(下界, 上界)
        低 = min(下界, 上界)
        return 缺口(高, 低)


class 指标:
    """静态工具类，提供K线取值的辅助方法。

    主要方法:
      :meth:`K线取值` — 根据计算方式从K线中取对应价格（开/高/低/收/均值）
    """

    @classmethod
    def K线取值(cls, k线: K线, 指标计算方式):
        """根据计算方式从K线中取值

        :param k线: K线对象
        :param 指标计算方式: "开"/"高"/"低"/"收"/"高低均值"/"高低收均值"/"开高低收均值"
        :return: 对应价格
        """
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


class 平滑异同移动平均线:
    """平滑异同移动平均线（MACD）— 基于EMA快慢线差值的趋势指标。

    :ivar 时间戳: K线时间戳
    :ivar 收盘价: 当前收盘价
    :ivar 快线周期: 短期EMA周期（默认12）
    :ivar 慢线周期: 长期EMA周期（默认26）
    :ivar 信号周期: 信号线EMA周期（默认9）
    :ivar EMA快线: 短期EMA值
    :ivar EMA慢线: 长期EMA值
    :ivar DIF: 快线减慢线
    :ivar DEA: DIF的信号线EMA
    :ivar MACD柱子: DIF减DEA

    主要方法:
      :meth:`首次计算` / :meth:`增量计算` / :meth:`增量计算_K线`
    """

    def __init__(
        self,
        时间戳: datetime,
        收盘价: float,
        快线周期: int = 12,
        慢线周期: int = 26,
        信号周期: int = 9,
        DIF: Optional[float] = None,
        DEA: Optional[float] = None,
        MACD柱: Optional[float] = None,
        快线EMA: Optional[float] = None,
        慢线EMA: Optional[float] = None,
        DEA_EMA: Optional[float] = None,
    ):
        # 原始数据
        self.时间戳 = 时间戳
        self.收盘价 = 收盘价

        # 计算参数
        self.快线周期 = 快线周期
        self.慢线周期 = 慢线周期
        self.信号周期 = 信号周期

        # 核心指标值
        self.DIF = DIF
        self.DEA = DEA
        self.MACD柱 = MACD柱

        # EMA中间值（用于增量计算）
        self.快线EMA = 快线EMA
        self.慢线EMA = 慢线EMA
        self.DEA_EMA = DEA_EMA

    def __repr__(self):
        return f"平滑异同移动平均线(时间戳={self.时间戳}, 收盘价={self.收盘价}, 快线周期={self.快线周期}, 慢线周期={self.慢线周期}, 信号周期={self.信号周期}, DIF={self.DIF}, DEA={self.DEA}, MACD柱={self.MACD柱}, 快线EMA={self.快线EMA}, 慢线EMA={self.慢线EMA}, DEA_EMA={self.DEA_EMA})"

    @classmethod
    def 首次计算(cls, 初始收盘价: float, 初始时间: datetime, 快线周期: int = 12, 慢线周期: int = 26, 信号周期: int = 9) -> 平滑异同移动平均线:
        """
        首次计算MACD指标（没有历史数据时使用）

        :param 初始收盘价: 第一个数据点的收盘价
        :param 初始时间: 第一个数据点的时间戳
        :param 快线周期: 快线EMA周期
        :param 慢线周期: 慢线EMA周期
        :param 信号周期: 信号线EMA周期
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

        return cls(
            时间戳=初始时间,
            收盘价=初始收盘价,
            快线周期=快线周期,
            慢线周期=慢线周期,
            信号周期=信号周期,
            DIF=round(DIF, 2),
            DEA=round(DEA_EMA, 2),
            MACD柱=round(MACD柱, 2),
            快线EMA=round(快线EMA, 2),
            慢线EMA=round(慢线EMA, 2),
            DEA_EMA=round(DEA_EMA, 2),
        )

    @classmethod
    def 首次计算_K线(cls, k线: K线, 计算方式: str, 快线周期: int = 12, 慢线周期: int = 26, 信号周期: int = 9) -> 平滑异同移动平均线:
        """
        :param k线: 原始K线
        :param 计算方式: 指标计算方式（开/高/低/收/均值等）
        :param 快线周期: 快线EMA周期
        :param 慢线周期: 慢线EMA周期
        :param 信号周期: 信号线EMA周期
        :return: MACD指标对象
        """
        初始收盘价: float = 指标.K线取值(k线, 计算方式)
        初始时间: datetime = k线.时间戳
        return cls.首次计算(初始收盘价, 初始时间, 快线周期, 慢线周期, 信号周期)

    @classmethod
    def 增量计算(cls, 前一个MACD: 平滑异同移动平均线, 当前收盘价: float, 当前时间: datetime) -> 平滑异同移动平均线:
        """
        基于前一个MACD指标增量计算当前MACD指标
        适用于实时交易系统或流式数据处理

        :param 前一个MACD: 前一个周期的MACD指标对象
        :param 当前收盘价: 当前K线的收盘价
        :param 当前时间: 当前K线的时间戳
        :return: 当前MACD指标对象
        :raises RuntimeError: 前一个MACD中快线EMA或慢线EMA为None时抛出
        """

        # 计算EMA的平滑系数
        def 平滑系数(周期):
            return 2 / (周期 + 1)

        # 计算快线EMA
        if 前一个MACD.快线EMA is None:
            快线EMA = 当前收盘价
            raise RuntimeError
        else:
            快线EMA = 当前收盘价 * 平滑系数(前一个MACD.快线周期) + 前一个MACD.快线EMA * ((前一个MACD.快线周期 - 1) / (前一个MACD.快线周期 + 1))

        # 计算慢线EMA
        if 前一个MACD.慢线EMA is None:
            慢线EMA = 当前收盘价
            raise RuntimeError
        else:
            慢线EMA = 当前收盘价 * 平滑系数(前一个MACD.慢线周期) + 前一个MACD.慢线EMA * ((前一个MACD.慢线周期 - 1) / (前一个MACD.慢线周期 + 1))

        # 计算DIF
        DIF = 快线EMA - 慢线EMA

        # 计算DEA的EMA
        if 前一个MACD.DEA_EMA is None:
            DEA_EMA = DIF
        else:
            DEA_EMA = DIF * 平滑系数(前一个MACD.信号周期) + 前一个MACD.DEA_EMA * ((前一个MACD.信号周期 - 1) / (前一个MACD.信号周期 + 1))

        # 计算MACD柱
        MACD柱 = DIF - DEA_EMA  # * 2

        return cls(
            时间戳=当前时间,
            收盘价=当前收盘价,
            快线周期=前一个MACD.快线周期,
            慢线周期=前一个MACD.慢线周期,
            信号周期=前一个MACD.信号周期,
            DIF=round(DIF, 2),
            DEA=round(DEA_EMA, 2),
            MACD柱=round(MACD柱, 2),
            快线EMA=round(快线EMA, 2),
            慢线EMA=round(慢线EMA, 2),
            DEA_EMA=round(DEA_EMA, 2),
        )

    @classmethod
    def 增量计算_K线(cls, 前一个MACD: 平滑异同移动平均线, 当前K线: K线, 计算方式: str) -> 平滑异同移动平均线:
        """
        :param 前一个MACD: 前一个MACD指标对象
        :param 当前K线: 当前K线
        :param 计算方式: 指标计算方式
        :return: 当前MACD指标对象
        """
        当前收盘价: float = 指标.K线取值(当前K线, 计算方式)
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个MACD, 当前收盘价, 当前时间)


class 相对强弱指数:
    """相对强弱指数（RSI）— 使用 Wilder 平滑（RMA）进行增量计算。

    :ivar 时间戳: K线时间戳
    :ivar 收盘价: 当前收盘价
    :ivar 周期: RSI计算周期（默认14）
    :ivar 超买阈值: 超买线（默认70.0）
    :ivar 超卖阈值: 超卖线（默认30.0）
    :ivar RSI: 当前RSI值
    :ivar RSI_SMA周期: RSI的SMA平滑周期（可选）
    :ivar RSI_SMA: RSI的SMA值
    :ivar 平均上涨: Wilder平均上涨幅度
    :ivar 平均下跌: Wilder平均下跌幅度

    主要方法:
      :meth:`首次计算` / :meth:`增量计算` / :meth:`增量计算_K线`
    """

    def __init__(
        self,
        时间戳: datetime,
        收盘价: float,
        周期: int = 14,
        超买阈值: float = 70.0,
        超卖阈值: float = 30.0,
        RSI_SMA周期: Optional[int] = None,
        RSI: Optional[float] = None,
        平均上涨: Optional[float] = None,
        平均下跌: Optional[float] = None,
        上涨幅度: float = 0.0,
        下跌幅度: float = 0.0,
        平滑系数: float = 0.0,
        RSI_SMA: Optional[float] = None,
        RSI历史队列: Optional[deque[float]] = None,
        RSI和: float = 0.0,
    ):
        if RSI历史队列 is None:
            RSI历史队列 = deque()

        # 原始数据
        self.时间戳 = 时间戳
        self.收盘价 = 收盘价

        # 参数
        self.周期 = 周期
        self.超买阈值 = 超买阈值
        self.超卖阈值 = 超卖阈值
        self.RSI_SMA周期 = RSI_SMA周期

        # 核心指标值
        self.RSI = RSI

        # 中间平滑值（Wilder平滑）
        self.平均上涨 = 平均上涨
        self.平均下跌 = 平均下跌

        # 原始变化值（用于调试）
        self.上涨幅度 = 上涨幅度
        self.下跌幅度 = 下跌幅度

        # 平滑系数（α = 1/周期）
        self.平滑系数 = 平滑系数

        # RSI的SMA（信号线）相关字段
        self.RSI_SMA = RSI_SMA
        self.RSI历史队列 = RSI历史队列
        self.RSI和 = RSI和

    @classmethod
    def 首次计算(cls, 初始收盘价: float, 初始时间: datetime, 周期: int = 14, 超买阈值: float = 70.0, 超卖阈值: float = 30.0, RSI_SMA周期: Optional[int] = None) -> 相对强弱指数:
        """
        首次计算RSI（没有足够历史数据时使用）
        此时无法计算真实RSI，设为 None，但记录初始收盘价作为起点

        :param 初始收盘价: 第一个数据点的收盘价
        :param 初始时间: 第一个数据点的时间戳
        :param 周期: RSI周期
        :param 超买阈值: 超买阈值
        :param 超卖阈值: 超卖阈值
        :param RSI_SMA周期: RSI的SMA周期（可选）
        :return: RSI指标对象
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
            RSI_SMA周期=RSI_SMA周期,
            RSI_SMA=None,
            RSI历史队列=[],
        )

    @classmethod
    def 首次计算_K线(cls, k线: K线, 计算方式: str, 周期: int = 14, 超买阈值: float = 70.0, 超卖阈值: float = 30.0, RSI_SMA周期: Optional[int] = None) -> 相对强弱指数:
        """
        :param k线: 原始K线
        :param 计算方式: 指标计算方式
        :param 周期: RSI周期
        :param 超买阈值: 超买阈值
        :param 超卖阈值: 超卖阈值
        :param RSI_SMA周期: RSI的SMA周期
        :return: RSI指标对象
        """
        初始收盘价: float = 指标.K线取值(k线, 计算方式)
        初始时间: datetime = k线.时间戳
        return cls.首次计算(初始收盘价, 初始时间, 周期, 超买阈值, 超卖阈值, RSI_SMA周期)

    @classmethod
    def 增量计算(cls, 前一个RSI: 相对强弱指数, 当前收盘价: float, 当前时间: datetime) -> 相对强弱指数:
        """
        基于前一个RSI指标增量计算当前RSI
        支持可选的RSI_SMA（简单移动平均）

        :param 前一个RSI: 前一个RSI指标对象
        :param 当前收盘价: 当前收盘价
        :param 当前时间: 当前时间戳
        :return: 当前RSI指标对象
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

        # ----- 计算RSI的SMA（简单移动平均） -----
        RSI_SMA = None
        历史队列 = 前一个RSI.RSI历史队列.copy() if 前一个RSI.RSI历史队列 else deque()
        RSI和 = 前一个RSI.RSI和
        if RSI_SMA周期 is not None and RSI_SMA周期 > 0 and RSI is not None:
            历史队列.append(RSI)
            RSI和 += RSI
            if len(历史队列) > RSI_SMA周期:
                RSI和 -= 历史队列.popleft()
            if 历史队列:
                RSI_SMA = RSI和 / len(历史队列)
        else:
            历史队列 = deque()
            RSI和 = 0.0

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
            RSI_SMA周期=RSI_SMA周期,
            RSI_SMA=RSI_SMA,
            RSI历史队列=历史队列,
            RSI和=RSI和,
        )

    @classmethod
    def 增量计算_K线(cls, 前一个RSI: 相对强弱指数, 当前K线: K线, 计算方式: str) -> 相对强弱指数:
        """
        :param 前一个RSI: 前一个RSI指标对象
        :param 当前K线: 当前K线
        :param 计算方式: 指标计算方式
        :return: 当前RSI指标对象
        """
        当前收盘价: float = 指标.K线取值(当前K线, 计算方式)
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个RSI, 当前收盘价, 当前时间)


class 随机指标:
    """KDJ 随机指标（Stochastic Oscillator）— 基于RSV的三线指标。

    :ivar 时间戳: K线时间戳
    :ivar 最高价: 当前最高价
    :ivar 最低价: 当前最低价
    :ivar 收盘价: 当前收盘价
    :ivar N: RSV计算周期（默认9）
    :ivar M1: K值平滑周期（默认3）
    :ivar M2: D值平滑周期（默认3）
    :ivar 超买阈值: 超买线（默认80.0）
    :ivar 超卖阈值: 超卖线（默认20.0）
    :ivar RSV: 未成熟随机值
    :ivar K: K值（RSV的M1周期移动平均）
    :ivar D: D值（K的M2周期移动平均）
    :ivar J: J值（3K - 2D）

    主要方法:
      :meth:`首次计算` / :meth:`增量计算` / :meth:`增量计算_K线`
    """

    def __init__(
        self,
        时间戳: datetime,
        最高价: float,
        最低价: float,
        收盘价: float,
        N: int = 9,
        M1: int = 3,
        M2: int = 3,
        超买阈值: float = 80.0,
        超卖阈值: float = 20.0,
        RSV: Optional[float] = None,
        K: Optional[float] = None,
        D: Optional[float] = None,
        J: Optional[float] = None,
        历史最高价队列: Optional[deque[float]] = None,
        历史最低价队列: Optional[deque[float]] = None,
        前一个RSV: Optional[float] = None,
        前一个K: Optional[float] = None,
        前一个D: Optional[float] = None,
    ):
        if 历史最高价队列 is None:
            历史最高价队列 = deque()
        if 历史最低价队列 is None:
            历史最低价队列 = deque()

        # 原始数据
        self.时间戳 = 时间戳
        self.最高价 = 最高价
        self.最低价 = 最低价
        self.收盘价 = 收盘价

        # 参数
        self.N = N
        self.M1 = M1
        self.M2 = M2
        self.超买阈值 = 超买阈值
        self.超卖阈值 = 超卖阈值

        # 核心指标值
        self.RSV = RSV
        self.K = K
        self.D = D
        self.J = J

        # 中间状态（用于增量计算）
        self.历史最高价队列 = 历史最高价队列
        self.历史最低价队列 = 历史最低价队列
        self.前一个RSV = 前一个RSV
        self.前一个K = 前一个K
        self.前一个D = 前一个D

    @classmethod
    def 首次计算(cls, 初始最高价: float, 初始最低价: float, 初始收盘价: float, 初始时间: datetime, N: int = 9, M1: int = 3, M2: int = 3, 超买阈值: float = 80.0, 超卖阈值: float = 20.0) -> 随机指标:
        """
        首次计算KDJ（无历史数据时）
        此时无法计算RSV和K/D/J，仅记录初始三价，初始化队列

        :param 初始最高价: 第一个数据点的最高价
        :param 初始最低价: 第一个数据点的最低价
        :param 初始收盘价: 第一个数据点的收盘价
        :param 初始时间: 第一个数据点的时间戳
        :param N: RSV周期
        :param M1: K值平滑周期
        :param M2: D值平滑周期
        :param 超买阈值: 超买阈值
        :param 超卖阈值: 超卖阈值
        :return: KDJ指标对象
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
            历史最高价队列=deque([初始最高价]),
            历史最低价队列=deque([初始最低价]),
            前一个RSV=None,
            前一个K=None,
            前一个D=None,
        )

    @classmethod
    def 首次计算_K线(cls, k线: K线, 计算方式: str, RSV周期: int = 9, K值平滑周期: int = 3, D值平滑周期: int = 3, 超买阈值: float = 80.0, 超卖阈值: float = 20.0) -> 随机指标:
        """
        :param k线: 原始K线
        :param 计算方式: 指标计算方式（未使用，仅为接口一致）
        :param RSV周期: RSV周期
        :param K值平滑周期: K值平滑周期
        :param D值平滑周期: D值平滑周期
        :param 超买阈值: 超买阈值
        :param 超卖阈值: 超卖阈值
        :return: KDJ指标对象
        """
        初始最高价: float = k线.高
        初始最低价: float = k线.低
        初始收盘价: float = k线.收盘价
        初始时间: datetime = k线.时间戳
        return cls.首次计算(初始最高价, 初始最低价, 初始收盘价, 初始时间, RSV周期, K值平滑周期, D值平滑周期, 超买阈值, 超卖阈值)

    @classmethod
    def 增量计算(cls, 前一个KDJ: 随机指标, 当前最高价: float, 当前最低价: float, 当前收盘价: float, 当前时间: datetime) -> 随机指标:
        """
        基于前一个KDJ对象和当前三价，增量计算当前KDJ值

        :param 前一个KDJ: 前一个KDJ指标对象
        :param 当前最高价: 当前最高价
        :param 当前最低价: 当前最低价
        :param 当前收盘价: 当前收盘价
        :param 当前时间: 当前时间戳
        :return: 当前KDJ指标对象
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
            历史最高价.popleft()

        # 更新历史最低价队列
        历史最低价 = 前一个KDJ.历史最低价队列.copy()
        历史最低价.append(当前最低价)
        if len(历史最低价) > N:
            历史最低价.popleft()

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
        )

    @classmethod
    def 增量计算_K线(cls, 前一个KDJ: 随机指标, 当前K线: K线, 计算方式: str) -> 随机指标:
        """
        :param 前一个KDJ: 前一个KDJ指标对象
        :param 当前K线: 当前K线
        :param 计算方式: 指标计算方式（未使用，仅为接口一致）
        :return: 当前KDJ指标对象
        """
        当前最高价: float = 当前K线.高
        当前最低价: float = 当前K线.低
        当前收盘价: float = 当前K线.收盘价
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个KDJ, 当前最高价, 当前最低价, 当前收盘价, 当前时间)


class 布林带:
    """布林带（BOLL）— 基于移动平均和标准差的波动率通道。

    :ivar 时间戳: K线时间戳
    :ivar 周期: 移动平均周期（默认20）
    :ivar 标准差倍数: 通道宽度倍数（默认2.0）
    :ivar 上轨: 中轨 + 标准差倍数 × 标准差
    :ivar 中轨: 简单移动平均
    :ivar 下轨: 中轨 - 标准差倍数 × 标准差

    主要方法:
      :meth:`首次计算` / :meth:`增量计算`
    """

    __slots__ = ["时间戳", "周期", "标准差倍数", "上轨", "中轨", "下轨", "_历史队列", "_均值", "_方差和"]

    def __init__(self, 时间戳: datetime, 周期: int = 20, 标准差倍数: float = 2.0, 上轨: float = 0.0, 中轨: float = 0.0, 下轨: float = 0.0, 历史队列: Optional[List[float]] = None, _均值: float = 0.0, _方差和: float = 0.0):
        self.时间戳 = 时间戳
        self.周期 = 周期
        self.标准差倍数 = 标准差倍数
        self.上轨 = 上轨
        self.中轨 = 中轨
        self.下轨 = 下轨
        self._历史队列 = 历史队列 if 历史队列 is not None else deque()
        self._均值 = _均值
        self._方差和 = _方差和

    @classmethod
    def 首次计算(cls, k线: K线, 计算方式: str, 周期: int = 20, 标准差倍数: float = 2.0) -> 布林带:
        """首次计算布林带，三条轨线初始化为当前价格。

        :param k线: 当前K线
        :param 计算方式: 取值方式（"收"/"高低均值" 等）
        :param 周期: 移动平均周期
        :param 标准差倍数: 标准差倍数
        :return: 初始的布林带实例
        """
        价格 = 指标.K线取值(k线, 计算方式)
        return cls(时间戳=k线.时间戳, 周期=周期, 标准差倍数=标准差倍数, 上轨=价格, 中轨=价格, 下轨=价格, 历史队列=deque([价格]))

    @classmethod
    def 增量计算(cls, prev: 布林带, 当前K线: K线, 计算方式: str) -> 布林带:
        """基于前一个布林带实例增量计算当前布林带。

        :param prev: 前一个布林带实例
        :param 当前K线: 当前K线
        :param 计算方式: 取值方式
        :return: 新的布林带实例
        """
        当前价 = 指标.K线取值(当前K线, 计算方式)
        周期 = prev.周期
        标准差倍数 = prev.标准差倍数

        q = prev._历史队列.copy()
        q.append(当前价)
        if len(q) > 周期:
            q.popleft()

        # 增量均值和方差
        if len(q) < 周期:
            _均值 = sum(q) / len(q)
            _方差和 = sum((v - _均值) ** 2 for v in q)
        else:
            n = float(周期)
            old_val = prev._历史队列[0] if len(prev._历史队列) >= 周期 else q[0]
            new_mean = prev._均值 + (当前价 - old_val) / n
            _均值 = new_mean
            # Welford 增量方差
            _方差和 = prev._方差和 + (当前价 - old_val) * (当前价 - _均值 + old_val - prev._均值)

        std = (_方差和 / len(q)) ** 0.5
        return cls(时间戳=当前K线.时间戳, 周期=周期, 标准差倍数=标准差倍数, 中轨=_均值, 上轨=_均值 + 标准差倍数 * std, 下轨=_均值 - 标准差倍数 * std, 历史队列=q, _均值=_均值, _方差和=_方差和)


class 指标容器:
    """挂载在每根K线上，持有该时刻所有指标的快照与增量计算内部状态。

    基于注册表模式，所有指标统一存储在内部 dict，通过 ``__getattr__`` / ``__setattr__`` 访问。
    运行中可随时添加新指标，无需修改类定义。同指标不同参数通过 key 区分
    （如 ``k线.指标.均线["SMA_5"]`` vs ``k线.指标.均线["SMA_20"]``）。

    :ivar macd: MACD指标快照
    :ivar rsi: RSI指标快照
    :ivar kdj: KDJ指标快照
    :ivar boll: BOLL指标快照
    :ivar 均线: 均线组 dict — key 格式 ``"{类型}_{周期}"``（如 ``"SMA_5"`` / ``"EMA_20"``）
    :ivar 单值: 单值指标 dict — key 格式 ``"{名称}_{周期}"``（如 ``"CCI_14"`` / ``"ATR_14"``）

    主要方法:
      :meth:`获取` — 读取指标值，不存在时返回默认值
      :meth:`设置默认值` — 指标不存在时写入默认值
      :meth:`项目` — 返回所有非None指标的迭代器
    """

    __slots__ = ["_数据"]

    def __init__(self):
        object.__setattr__(
            self,
            "_数据",
            {
                "macd": None,
                "rsi": None,
                "kdj": None,
                "boll": None,
                "均线": {},
                "单值": {},
            },
        )

    def __getattr__(self, name: str):
        _数据 = object.__getattribute__(self, "_数据")
        if name not in _数据:
            raise AttributeError(f"指标 '{name}' 不存在于 指标容器 中")
        return _数据[name]

    def __setattr__(self, name: str, value):
        if name == "_数据":
            object.__setattr__(self, name, value)
        else:
            object.__getattribute__(self, "_数据")[name] = value

    def __delattr__(self, name: str):
        if name == "_数据":
            object.__delattr__(self, name)
        else:
            object.__getattribute__(self, "_数据").pop(name, None)

    def __getitem__(self, name: str):
        return self.__getattr__(name)

    def __setitem__(self, name: str, value):
        self.__setattr__(name, value)

    def __contains__(self, name: str) -> bool:
        return name in object.__getattribute__(self, "_数据")

    def __repr__(self) -> str:
        _数据 = object.__getattribute__(self, "_数据")
        keys = [k for k in _数据 if _数据[k] is not None]
        return f"指标容器({', '.join(keys)})"

    def 注册(self, 名称: str, 默认值=None):
        """预注册指标，让 __getattr__ 能查询到该指标，不存在时返回默认值而不抛出异常。

        :param 名称: 指标名称
        :param 默认值: 指标不存在时返回的默认值
        """
        _数据 = object.__getattribute__(self, "_数据")
        if 名称 not in _数据:
            _数据[名称] = 默认值

    def 项目(self):
        """返回所有已注册的非 None 指标的 (名称, 值) 迭代器，供调试/遍历。"""
        return ((k, v) for k, v in object.__getattribute__(self, "_数据").items() if v is not None)


class 均线工具:
    """增量 SMA/EMA 计算的静态方法容器。

    主要方法:
      :meth:`增量SMA` — 基于前一根K线的SMA值增量计算当前SMA
      :meth:`增量EMA` — 用前一根K线的EMA值递推计算当前EMA
    """

    @staticmethod
    def 增量SMA(普K序列: List[K线], period: int, 计算方式: str) -> float:
        """基于前一根K线的 SMA 值，增量计算当前 SMA。

        :param 普K序列: 原始K线序列（最近 period+1 根至少）
        :param period: 移动平均周期
        :param 计算方式: 取值方式（"收"/"高低均值" 等）
        :return: 当前 SMA 值
        """
        if len(普K序列) <= period:
            return sum(指标.K线取值(k, 计算方式) for k in 普K序列[-period:]) / max(len(普K序列), 1)
        prev_key = f"SMA_{period}"
        prev = 普K序列[-2].指标.均线.get(prev_key)
        if prev is None:
            当前价序列 = [指标.K线取值(k, 计算方式) for k in 普K序列[-period:]]
            return sum(当前价序列) / period
        当前价 = 指标.K线取值(普K序列[-1], 计算方式)
        oldest = 指标.K线取值(普K序列[-period - 1], 计算方式)
        return prev + (当前价 - oldest) / period

    @staticmethod
    def 增量EMA(普K序列: List[K线], period: int, 计算方式: str, 前值: Optional[float] = None) -> float:
        """用前一根K线的 EMA 值递推计算当前 EMA。

        :param 普K序列: 原始K线序列
        :param period: 平滑周期
        :param 计算方式: 取值方式（"收"/"高低均值" 等）
        :param 前值: 前一根K线已缓存的 EMA 值，None 则自动查找
        :return: 当前 EMA 值
        """
        当前价 = 指标.K线取值(普K序列[-1], 计算方式)
        if 前值 is None:
            return 当前价
        k = 2.0 / (period + 1)
        return 当前价 * k + 前值 * (1.0 - k)


class 指标计算器:
    """在缠K合并之前，增量计算所有开启的指标并挂载到K线上。

    遍历 :class:`缠论配置` 中的参数列表，支持同一指标多种参数变体共存。
    参数列表为空时自动回退到默认单参数（向后兼容）。

    主要方法:
      :meth:`计算并挂载` — 增量计算所有开启的指标，将结果写入 ``当前K线.指标``
    """

    @staticmethod
    def 计算并挂载(当前K线: K线, 全序列: List[K线], 配置: 缠论配置):
        """增量计算所有开启的指标，将结果写入 当前K线.指标

        :param 当前K线: 当前传入的K线（已在全序列末尾）
        :param 全序列: 完整普K序列（包含当前K线）
        :param 配置: 缠论配置
        """
        if 当前K线.指标 is None:
            当前K线.指标 = 指标容器()

        # 全序列[-2] 一定是不同时间戳的前一根K线
        # （同时间戳更新时，[-1]已被替换为新值，[-2]即为前一不同时间戳）
        prev = 全序列[-2].指标 if len(全序列) > 1 else None

        if 配置.计算指标:
            指标计算器._计算MACD组(当前K线, prev, 配置)
            指标计算器._计算RSI组(当前K线, prev, 配置)
            指标计算器._计算KDJ组(当前K线, prev, 配置)
            指标计算器._计算BOLL组(当前K线, prev, 配置)

        指标计算器._更新均线(当前K线, 全序列, 配置)

        if prev is not None:
            指标计算器._回填新指标(全序列, 配置)

    @staticmethod
    def _计算MACD组(当前K线: K线, prev: Optional[指标容器], 配置: 缠论配置):
        idx = 当前K线.指标
        for i, (key, 计算方式, *params) in enumerate(配置.MACD_参数列表):
            快, 慢, 信号 = params[0], params[1], params[2]
            prev_val = prev[key] if prev is not None and key in prev else None
            if prev_val is not None:
                idx[key] = 平滑异同移动平均线.增量计算_K线(prev_val, 当前K线, 计算方式)
            else:
                idx[key] = 平滑异同移动平均线.首次计算_K线(当前K线, 计算方式, 快, 慢, 信号)
            if i == 0:
                idx["macd"] = idx[key]

    @staticmethod
    def _计算RSI组(当前K线: K线, prev: Optional[指标容器], 配置: 缠论配置):
        idx = 当前K线.指标
        for key, 计算方式, *params in 配置.RSI_周期列表:
            周期, MA周期, 超买, 超卖 = params[0], params[1], params[2], params[3]
            prev_val = prev[key] if prev is not None and key in prev else None
            if prev_val is not None:
                idx[key] = 相对强弱指数.增量计算_K线(prev_val, 当前K线, 计算方式)
            else:
                idx[key] = 相对强弱指数.首次计算_K线(
                    当前K线,
                    计算方式,
                    周期,
                    超买,
                    超卖,
                    MA周期,
                )

    @staticmethod
    def _计算KDJ组(当前K线: K线, prev: Optional[指标容器], 配置: 缠论配置):
        idx = 当前K线.指标
        for key, 计算方式, *params in 配置.KDJ_参数列表:
            rsv, k平滑, d平滑, 超买, 超卖 = params[0], params[1], params[2], params[3], params[4]
            prev_val = prev[key] if prev is not None and key in prev else None
            if prev_val is not None:
                idx[key] = 随机指标.增量计算_K线(prev_val, 当前K线, 计算方式)
            else:
                idx[key] = 随机指标.首次计算_K线(
                    当前K线,
                    计算方式,
                    rsv,
                    k平滑,
                    d平滑,
                    超买,
                    超卖,
                )

    @staticmethod
    def _计算BOLL组(当前K线: K线, prev: Optional[指标容器], 配置: 缠论配置):
        idx = 当前K线.指标
        for key, 计算方式, *params in 配置.BOLL_参数列表:
            周期, 标准差倍数 = params[0], params[1]
            prev_val = prev[key] if prev is not None and key in prev else None
            if prev_val is not None:
                idx[key] = 布林带.增量计算(prev_val, 当前K线, 计算方式)
            else:
                idx[key] = 布林带.首次计算(当前K线, 计算方式, 周期, 标准差倍数)

    @staticmethod
    def _更新均线(当前K线: K线, 普K序列: List[K线], 配置: 缠论配置):
        if not 配置.均线参数列表:
            return
        for key, 计算方式, ma_type, period in 配置.均线参数列表:
            if ma_type == "SMA":
                当前K线.指标.均线[key] = 均线工具.增量SMA(普K序列, period, 计算方式)
            elif ma_type == "EMA":
                前值 = None
                if len(普K序列) >= 2:
                    前值 = 普K序列[-2].指标.均线.get(key)
                当前K线.指标.均线[key] = 均线工具.增量EMA(普K序列, period, 计算方式, 前值)

    @staticmethod
    def _回填新指标(全序列: List[K线], 配置: 缠论配置):
        """运行中新增指标参数时，回填所有历史K线。

        比较首尾K线的指标键，检测运行中动态添加到配置的新指标参数，
        然后从第一根K线开始逐根重新计算，使历史K线也能获得新指标值。
        """
        首K指标 = 全序列[0].指标
        尾K指标 = 全序列[-1].指标
        if 首K指标 is None or 尾K指标 is None:
            return

        def _新键(尾指标, 首指标, 参数列表):
            新参数 = []
            for params in 参数列表:
                key = params[0]
                if key in 尾指标 and key not in 首指标:
                    新参数.append(params)
            return 新参数

        新MACD = _新键(尾K指标, 首K指标, 配置.MACD_参数列表)
        新RSI = _新键(尾K指标, 首K指标, 配置.RSI_周期列表)
        新KDJ = _新键(尾K指标, 首K指标, 配置.KDJ_参数列表)
        新BOLL = _新键(尾K指标, 首K指标, 配置.BOLL_参数列表)

        if not (新MACD or 新RSI or 新KDJ or 新BOLL):
            return

        for i, k线 in enumerate(全序列):
            if k线.指标 is None:
                k线.指标 = 指标容器()

            idx = k线.指标
            prev = 全序列[i - 1].指标 if i > 0 else None

            for key, 计算方式, *params in 新MACD:
                快, 慢, 信号 = params[0], params[1], params[2]
                prev_val = prev[key] if prev is not None and key in prev else None
                if prev_val is not None:
                    idx[key] = 平滑异同移动平均线.增量计算_K线(prev_val, k线, 计算方式)
                else:
                    idx[key] = 平滑异同移动平均线.首次计算_K线(k线, 计算方式, 快, 慢, 信号)

            for key, 计算方式, *params in 新RSI:
                周期, MA周期, 超买, 超卖 = params[0], params[1], params[2], params[3]
                prev_val = prev[key] if prev is not None and key in prev else None
                if prev_val is not None:
                    idx[key] = 相对强弱指数.增量计算_K线(prev_val, k线, 计算方式)
                else:
                    idx[key] = 相对强弱指数.首次计算_K线(k线, 计算方式, 周期, 超买, 超卖, MA周期)

            for key, 计算方式, *params in 新KDJ:
                rsv, k平滑, d平滑, 超买, 超卖 = params[0], params[1], params[2], params[3], params[4]
                prev_val = prev[key] if prev is not None and key in prev else None
                if prev_val is not None:
                    idx[key] = 随机指标.增量计算_K线(prev_val, k线, 计算方式)
                else:
                    idx[key] = 随机指标.首次计算_K线(k线, 计算方式, rsv, k平滑, d平滑, 超买, 超卖)

            for key, 计算方式, *params in 新BOLL:
                周期, 标准差倍数 = params[0], params[1]
                prev_val = prev[key] if prev is not None and key in prev else None
                if prev_val is not None:
                    idx[key] = 布林带.增量计算(prev_val, k线, 计算方式)
                else:
                    idx[key] = 布林带.首次计算(k线, 计算方式, 周期, 标准差倍数)


@注册
class 背驰分析:
    """静态方法容器，提供背驰/背离检测算法。

    主要方法:
      :meth:`MACD背驰` — MACD柱状线面积背驰
      :meth:`斜率背驰` — 线段斜率背驰
      :meth:`测度背驰` — 线段测度背驰
      :meth:`全量背驰` — 综合所有背驰检测方式
      :meth:`配置背驰` — 根据配置选择检测方式
    """

    @staticmethod
    def MACD背驰(进入段: 虚线, 离开段: 虚线, K线序列: List[K线], 方式: str = "总") -> bool:
        """MACD柱状线面积背驰

        :param 进入段: 进入中枢的虚线
        :param 离开段: 离开中枢的虚线
        :param K线序列: 完整K线序列
        :param 方式: "总" 或 "阳"/"阴"
        :return: 背驰为True
        """
        进入MACD = K线.获取MACD(K线序列, 进入段.文.中.标的K线, 进入段.武.中.标的K线)
        离开MACD = K线.获取MACD(K线序列, 离开段.文.中.标的K线, 离开段.武.中.标的K线)

        # 计算面积（绝对值求和）
        进入面积 = abs(进入MACD["总"] if 方式 == "总" else (进入MACD["阳"] if 进入段.方向 is 相对方向.向上 else 进入MACD["阴"]))
        离开面积 = abs(离开MACD["总"] if 方式 == "总" else (离开MACD["阳"] if 进入段.方向 is 相对方向.向上 else 离开MACD["阴"]))

        return 离开面积 < 进入面积

    @staticmethod
    def 斜率背驰(进入段: 虚线, 离开段: 虚线) -> bool:
        """价格斜率背驰

        :param 进入段: 进入中枢的虚线
        :param 离开段: 离开中枢的虚线
        :return: 背驰为True
        """
        # 计算线段的速度
        dx = 进入段.武.时间戳.timestamp() - 进入段.文.时间戳.timestamp()  # self.武.时间戳 - self.文.时间戳  # 时间差
        dy = 进入段.武.分型特征值 - 进入段.文.分型特征值  # 价格差
        进入斜率 = dy / dx
        # 计算线段的速度
        dx = 离开段.武.时间戳.timestamp() - 离开段.文.时间戳.timestamp()  # self.武.时间戳 - self.文.时间戳  # 时间差
        dy = 离开段.武.分型特征值 - 离开段.文.分型特征值  # 价格差
        离开斜率 = dy / dx

        if 进入段.方向 == 相对方向.向上:
            if 离开段.高 > 进入段.高 and abs(离开斜率) < abs(进入斜率):
                return True
        else:
            if 离开段.低 < 进入段.低 and abs(离开斜率) < abs(进入斜率):
                return True
        return False

    @staticmethod
    def 测度背驰(进入段: 虚线, 离开段: 虚线) -> bool:
        """价格测度背驰（欧氏距离）

        :param 进入段: 进入中枢的虚线
        :param 离开段: 离开中枢的虚线
        :return: 背驰为True
        """
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

    @staticmethod
    def 全量背驰(进入段: 虚线, 离开段: 虚线, 普K序列: List[K线]) -> bool:
        """判断是否满足全部三种背驰条件（MACD + 测度 + 斜率）

        :param 进入段: 进入中枢的线段
        :param 离开段: 离开中枢的线段
        :param 普K序列: 完整K线序列
        :return: 三者全满足返回True
        """
        return all([背驰分析.MACD背驰(进入段, 离开段, 普K序列), 背驰分析.测度背驰(进入段, 离开段), 背驰分析.斜率背驰(进入段, 离开段)])

    @staticmethod
    def 任意背驰(进入段: 虚线, 离开段: 虚线, 普K序列: List[K线]) -> bool:
        """判断是否满足任一背驰条件

        :param 进入段: 进入中枢的线段
        :param 离开段: 离开中枢的线段
        :param 普K序列: 完整K线序列
        :return: 任一满足返回True
        """
        return any([背驰分析.MACD背驰(进入段, 离开段, 普K序列), 背驰分析.测度背驰(进入段, 离开段), 背驰分析.斜率背驰(进入段, 离开段)])

    @staticmethod
    def 配置背驰(进入段: 虚线, 离开段: 虚线, 普K序列: List[K线], 配置: 缠论配置) -> bool:
        """根据配置选择对应的背驰检测组合

        :param 进入段: 进入中枢的线段
        :param 离开段: 离开中枢的线段
        :param 普K序列: 完整K线序列
        :param 配置: 缠论配置（控制MACD/测度/斜率开关）
        :return: 背驰结果
        """
        match 配置.线段内部背驰_MACD, 配置.线段内部背驰_测度, 配置.线段内部背驰_斜率:
            case True, True, True:
                return 背驰分析.MACD背驰(进入段, 离开段, 普K序列) and 背驰分析.测度背驰(进入段, 离开段) and 背驰分析.斜率背驰(进入段, 离开段)
            case False, False, False:
                ...

            case True, False, True:
                return 背驰分析.MACD背驰(进入段, 离开段, 普K序列) and 背驰分析.斜率背驰(进入段, 离开段)
            case False, True, False:
                return 背驰分析.测度背驰(进入段, 离开段)

            case True, False, False:
                return 背驰分析.MACD背驰(进入段, 离开段, 普K序列)
            case False, True, True:
                return 背驰分析.测度背驰(进入段, 离开段) and 背驰分析.斜率背驰(进入段, 离开段)

            case False, False, True:
                return 背驰分析.斜率背驰(进入段, 离开段)
            case True, True, False:
                return 背驰分析.MACD背驰(进入段, 离开段, 普K序列) and 背驰分析.测度背驰(进入段, 离开段)

        return False

    @staticmethod
    def 任选背驰(进入段: 虚线, 离开段: 虚线, 普K序列: List[K线]) -> bool:
        """三个背驰条件中至少两个满足即视为背驰

        :param 进入段: 进入中枢的线段
        :param 离开段: 离开中枢的线段
        :param 普K序列: 完整K线序列
        :return: 至少两个满足返回True
        """
        混沌槽 = [背驰分析.MACD背驰(进入段, 离开段, 普K序列), 背驰分析.测度背驰(进入段, 离开段), 背驰分析.斜率背驰(进入段, 离开段)]
        return len([背驰 for 背驰 in 混沌槽 if 背驰]) >= 2

    @staticmethod
    def 背驰模式(进入段: 虚线, 离开段: 虚线, 普K序列: List[K线], 配置: 缠论配置, 模式: str) -> bool:
        """根据模式字符串选择背驰检测策略

        :param 进入段: 进入中枢的线段
        :param 离开段: 离开中枢的线段
        :param 普K序列: 完整K线序列
        :param 配置: 缠论配置
        :param 模式: "全量"/"任意"/"配置"/"相对"
        :return: 背驰结果
        """
        match 模式:
            case "全量":
                return 背驰分析.全量背驰(进入段, 离开段, 普K序列)
            case "任意":
                return 背驰分析.任意背驰(进入段, 离开段, 普K序列)
            case "配置":
                return 背驰分析.配置背驰(进入段, 离开段, 普K序列, 配置)
            case "相对":
                return 背驰分析.任选背驰(进入段, 离开段, 普K序列)
        return False


class K线:
    """原始 K 线 — OHLCV 数据，通过 :class:`指标容器` 挂载所有技术指标。

    :ivar 标识: 标识符
    :ivar 序号: 序号
    :ivar 周期: K线周期（秒）
    :ivar 时间戳: 时间戳
    :ivar 高: 最高价
    :ivar 低: 最低价
    :ivar 开盘价: 开盘价
    :ivar 收盘价: 收盘价
    :ivar 成交量: 成交量
    :ivar 指标: 指标容器（含 macd/rsi/kdj/boll/均线/单值）
    :ivar 方向: 涨跌方向（只读）

    构造:
      :meth:`创建普K` — 创建原始K线实例

    序列化:
      :meth:`保存到DAT文件` — 将K线序列批量保存为DAT文件
      :meth:`读取大端字节数组` — 从大端字节数组解析K线

    工具:
      :meth:`获取MACD` — 计算指定区间内的MACD柱子面积
      :meth:`截取` — 截取起始K线到终止K线之间的子序列
    """

    __slots__ = ["标识", "序号", "周期", "时间戳", "高", "低", "开盘价", "收盘价", "成交量", "指标"]

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
    ):
        """
        :param 标识: K线标识符
        :param 序号: K线序号
        :param 周期: K线周期（秒）
        :param 时间戳: K线时间
        :param 开盘价: 开盘价
        :param 最高价: 最高价
        :param 最低价: 最低价
        :param 收盘价: 收盘价
        :param 成交量: 成交量
        :param macd: MACD指标对象（可选，存入 指标容器）
        :param rsi: RSI指标对象（可选，存入 指标容器）
        :param kdj: KDJ指标对象（可选，存入 指标容器）
        """
        self.序号: int = 序号
        self.标识: str = 标识
        self.时间戳: datetime = 时间戳
        self.开盘价: float = 开盘价
        self.高: float = 最高价
        self.低: float = 最低价
        self.收盘价: float = 收盘价
        self.成交量: float = 成交量
        self.周期: int = 周期
        self.指标: 指标容器 = 指标容器()

    @property
    def 最高价(self):
        return self.高

    @property
    def 最低价(self):
        return self.低

    # ---- property 兼容层：k线.macd → k线.指标.macd ----
    @property
    def macd(self) -> Optional[平滑异同移动平均线]:
        """该K线绑定的 MACD 指标快照。

        :return: MACD 实例，未计算时返回 None
        """
        return self.指标.macd

    @property
    def rsi(self) -> Optional[相对强弱指数]:
        """该K线绑定的 RSI 指标快照。

        :return: RSI 实例，未计算时返回 None
        """
        return self.指标.rsi

    @property
    def kdj(self) -> Optional[随机指标]:
        """该K线绑定的 KDJ 指标快照。

        :return: KDJ 实例，未计算时返回 None
        """
        return self.指标.kdj

    def __str__(self):
        return f"{self.标识}<{self.序号}, {self.周期}, {self.方向}, {self.时间戳}, {self.开盘价:g}, {self.高:g}, {self.低:g}, {self.收盘价:g}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.周期}, {self.方向}, {self.时间戳}, {self.开盘价:g}, {self.高:g}, {self.低:g}, {self.收盘价:g}>"

    @property
    def 方向(self) -> 相对方向:
        """
        :return: 相对方向.向上（开盘<收盘）或 相对方向.向下（开盘>收盘）
        """
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
    def 创建普K(cls, 标识: str, 时间戳: datetime | int, 开盘价: float, 最高价: float, 最低价: float, 收盘价: float, 成交量: float, 序号: int, 周期: int) -> K线:
        """快捷构造普通K线

        :param 标识: K线标识符
        :param 时间戳: K线时间
        :param 开盘价: 开盘价
        :param 最高价: 最高价
        :param 最低价: 最低价
        :param 收盘价: 收盘价
        :param 成交量: 成交量
        :param 序号: K线序号
        :param 周期: K线周期（秒）
        :return: K线实例
        """
        k线 = K线(
            标识=标识,
            序号=序号,
            周期=周期,
            时间戳=时间戳 if isinstance(时间戳, datetime_module.datetime) else 转化为时间戳(时间戳),  # 注意此处只为兼容Rust绑定
            开盘价=开盘价,
            最高价=最高价,
            最低价=最低价,
            收盘价=收盘价,
            成交量=成交量,
        )
        return k线

    @classmethod
    def 保存到DAT文件(cls, 路径: str, K线序列: List[K线]):
        """将K线序列保存为二进制DAT文件

        :param 路径: 保存路径
        :param K线序列: K线列表
        """
        with open(路径, "wb") as f:
            for K in K线序列:
                f.write(bytes(K))
        logger.info(f"保存到DAT文件: {路径}")

    @classmethod
    def 读取大端字节数组(cls, 字节组: bytes, 周期: int, 标识: str) -> K线:
        """从大端字节序二进制数据反序列化K线（兼容.dat/.nb文件格式）

        :param 字节组: 二进制数据（48字节）
        :param 周期: 周期（秒）
        :param 标识: K线标识
        :return: K线实例
        """
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
    def 获取MACD(cls, K线序列: List[K线], 始: K线, 终: K线) -> Dict[str, float]:
        """计算指定K线区间的MACD柱面积

        :param K线序列: 完整K线序列
        :param 始: 起始K线
        :param 终: 终点K线
        :return: {"阳": 正值面积和, "阴": 负值面积和, "合": 净面积, "总": 绝对面积和}
        """
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

    @staticmethod
    def 截取(序列: List[K线], 始: K线, 终: K线) -> List[K线]:
        """按起止K线截取K线子序列

        :param 序列: 完整K线序列
        :param 始: 起始K线
        :param 终: 终点K线
        :return: K线子列表
        """
        return 序列[序列.index(始) : 序列.index(终) + 1]

    def 根据当前K线生成新K线(self, 方向: 相对方向, 居中: bool = False) -> "K线":
        时间偏移 = timedelta(seconds=self.周期)
        时间戳: datetime = self.时间戳 + 时间偏移
        成交量: float = 998
        高: float = 0
        低: float = 0
        高低差 = self.高 - self.低
        match 方向:
            case 相对方向.向上:
                偏移 = 高低差 * 0.5 if 居中 else random.randint(int(高低差 * 0.1279), int(高低差 * 0.883))
                低 = self.低 + 偏移
                高 = self.高 + 偏移
            case 相对方向.向下:
                偏移 = 高低差 * 0.5 if 居中 else random.randint(int(高低差 * 0.1279), int(高低差 * 0.883))
                低 = self.低 - 偏移
                高 = self.高 - 偏移
            case 相对方向.向上缺口:
                偏移 = 高低差 * 1.5 if 居中 else random.randint(int(高低差 * 1.1279), int(高低差 * 1.883))
                低 = self.低 + 偏移
                高 = self.高 + 偏移
            case 相对方向.向下缺口:
                偏移 = 高低差 * 1.5 if 居中 else random.randint(int(高低差 * 1.1279), int(高低差 * 1.883))
                低 = self.低 - 偏移
                高 = self.高 - 偏移
            case 相对方向.衔接向上:
                偏移 = self.高 - self.低
                高 = self.高 + 偏移
                低 = self.高
            case 相对方向.衔接向下:
                偏移 = self.高 - self.低
                高 = self.低
                低 = self.低 - 偏移

        try:
            小数点 = [len(str(n).split(".")[-1]) for n in (self.开盘价, self.高, self.低, self.收盘价)]
        except:
            小数点 = [2, 1]
        新K线 = K线.创建普K(
            标识=self.标识,
            时间戳=时间戳,
            开盘价=round(random.uniform(高, 低), max(小数点)),
            最高价=round(高, max(小数点)),
            最低价=round(低, max(小数点)),
            收盘价=round(random.uniform(高, 低), max(小数点)),
            成交量=成交量 * random.random(),
            序号=self.序号 + 1,
            周期=self.周期,
        )

        # assert 相对方向.分析(self, 新K线) is 方向, (方向, 相对方向.分析(self, 新K线))
        return 新K线


class 缠论K线:
    """经包含处理后的标准化K线，有方向和分型结构标记。

    :ivar 序号: 序号
    :ivar 时间戳: 时间戳
    :ivar 高: 最高价
    :ivar 低: 最低价
    :ivar 方向: 运行方向
    :ivar 分型: 分型结构（顶/底/上/下等）
    :ivar 周期: 周期（秒）
    :ivar 标识: 标识符
    :ivar 分型特征值: 分型特征值（顶取高，底取低）
    :ivar 原始起始序号: 合并前的原始K线起始序号
    :ivar 原始结束序号: 合并前的原始K线结束序号
    :ivar 标的K线: 对应的原始K线
    :ivar 买卖点信息: 买卖点信息（预留）
    :ivar 镜像: 镜像缠K（底↔顶、上↔下，只读）
    :ivar 与MACD柱子匹配: 是否与MACD柱子方向匹配（只读）
    :ivar 与RSI匹配: 是否与RSI超买超卖匹配（只读）
    :ivar 与KDJ匹配: 是否与KDJ超买超卖匹配（只读）

    构造:
      :meth:`创建缠K` — 从原始K线创建缠论K线（含包含继承）

    算法:
      :meth:`分析` — 包含处理 + 合并，增量更新缠K序列（主入口）
      :meth:`时间戳对齐` — 将缠K序列时间戳对齐到指定基线

    工具:
      :meth:`截取` — 截取起始缠K到终止缠K之间的子序列
    """

    __slots__ = ["序号", "时间戳", "高", "低", "方向", "分型", "周期", "标识", "分型特征值", "原始起始序号", "原始结束序号", "标的K线", "买卖点信息"]

    def __init__(
        self,
        序号: int,
        时间戳: datetime,
        最高价: float,
        最低价: float,
        最终方向: 相对方向,
        普K: K线,
        原始起始序号: int,
        原始结束序号: int,
        分型: Optional[分型结构] = None,
    ):
        """
        :param 序号: 缠论K线序号
        :param 时间戳: 时间戳
        :param 最高价: 最高价
        :param 最低价: 最低价
        :param 最终方向: 方向
        :param 普K: 对应的原始K线
        :param 原始起始序号: 合并起始序号
        :param 原始结束序号: 合并结束序号
        :param 分型: 分型结构（可选）
        """
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
        self.标的K线: K线 = 普K
        self.买卖点信息: Set[str] = set()

    def __str__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.方向}, {self.时间戳}, {self.高:g}, {self.低:g}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.方向}, {self.时间戳}, {self.高:g}, {self.低:g}>"

    @property
    def 镜像(self):
        """创建当前缠K的浅拷贝副本

        :return: 新的缠论K线实例
        """
        K = 缠论K线(self.序号, self.时间戳, self.高, self.低, self.方向, self.标的K线, self.原始起始序号, self.原始结束序号, self.分型)
        K.买卖点信息.update(self.买卖点信息)
        return K

    @property
    def 与MACD柱子匹配(self) -> bool:
        """
        :return: 底分型时MACD柱<0，顶分型时MACD柱>0
        """
        if self.分型 in (分型结构.底, 分型结构.下):
            return self.标的K线.macd.MACD柱 < 0

        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.标的K线.macd.MACD柱 > 0
        return False

    @property
    def 与RSI匹配(self) -> bool:
        """
        :return: 底分型时RSI < RSI_SMA，顶分型时RSI > RSI_SMA
        """
        if self.分型 in (分型结构.底, 分型结构.下):
            return self.标的K线.rsi.RSI < self.标的K线.rsi.RSI_SMA

        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.标的K线.rsi.RSI > self.标的K线.rsi.RSI_SMA
        return False

    @property
    def 与KDJ匹配(self) -> bool:
        """
        :return: 底分型时K<D，顶分型时K>D
        """
        if self.标的K线.kdj.K is None or self.标的K线.kdj.D is None:
            return False
        if self.分型 in (分型结构.底, 分型结构.下):
            return self.标的K线.kdj.K < self.标的K线.kdj.D

        if self.分型 in (分型结构.顶, 分型结构.上):
            return self.标的K线.kdj.K > self.标的K线.kdj.D
        return False

    @classmethod
    def 时间戳对齐(cls, 基线: List[缠论K线], k线: 缠论K线):
        """在基线序列中找到与k线时间戳对齐的时间戳

        :param 基线: 参照缠K序列
        :param k线: 需要对齐的缠K
        :return: 对齐后的时间戳
        """
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
    def 创建缠K(cls, 时间戳: datetime, 高: float, 低: float, 方向: 相对方向, 结构: 分型结构, 原始序号: int, 普k: K线, 之前: Optional[缠论K线] = None) -> 缠论K线:
        """创建新的缠论K线

        :param 时间戳: K线时间
        :param 高: 最高价
        :param 低: 最低价
        :param 方向: K线运行方向
        :param 结构: 分型结构
        :param 原始序号: 原始K线序号
        :param 普k: 标的原始K线
        :param 之前: 前一缠K（可选，自动校验包含关系）
        :return: 缠论K线实例
        :raises ValueError: 包含关系错误
        """
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
    def _兼并(cls, 之前缠K: Optional[缠论K线], 当前缠K: 缠论K线, 当前普K: K线, 配置: 缠论配置) -> Tuple[Optional[缠论K线], Optional[str]]:
        """K线包含处理（合并）

        :param 之前缠K: 前一缠K
        :param 当前缠K: 当前待处理的缠K
        :param 当前普K: 当前原始K线
        :param 配置: 缠论配置
        :return: (新缠K或None, 操作模式:"添加"/"替换"/None)
        """
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
    def 分析(cls, 当前K线: K线, 缠K序列: List[缠论K线], 普K序列: List[K线], 配置: 缠论配置) -> tuple[str, Optional[分型]]:
        """分析K线，执行指标计算+包含处理+分型判定

        :param 当前K线: 新到的原始K线
        :param 缠K序列: 现有缠K序列（会被原地修改）
        :param 普K序列: 现有普K序列（会被原地修改）
        :param 配置: 缠论配置
        :return: (操作状态, 新形成的分型或None)
        """
        当前K线.标识 = 配置.标识
        if not 普K序列:
            普K序列.append(当前K线)
        else:
            之前普K = 普K序列[-1]
            if 之前普K.时间戳 == 当前K线.时间戳:
                当前K线.序号 = 普K序列[-1].序号
                普K序列[-1] = 当前K线
            else:
                if 之前普K.时间戳 > 当前K线.时间戳:
                    raise RuntimeError("时序错误")
                当前K线.序号 = 之前普K.序号 + 1
                普K序列.append(当前K线)

        if 配置.计算指标:
            指标计算器.计算并挂载(当前K线, 普K序列, 配置)

        之前缠K: Optional[缠论K线] = None
        状态, 形态 = None, None
        if 缠K序列:
            try:
                之前缠K = 缠K序列[-2]
            except IndexError:
                pass
            新缠K, 模式 = 缠论K线._兼并(之前缠K, 缠K序列[-1], 当前K线, 配置)
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

        结构 = 分型结构.分析(左, 中, 右)
        中.分型 = 结构

        if 结构 is 分型结构.底:
            中.分型特征值 = 中.低
            右.分型特征值 = 右.高
            右.分型 = 分型结构.顶

        if 结构 is 分型结构.顶:
            中.分型特征值 = 中.高
            右.分型特征值 = 右.低
            右.分型 = 分型结构.底

        if 结构 is 分型结构.上:
            中.分型特征值 = 中.高
            右.分型特征值 = 右.高
            右.分型 = 分型结构.顶

        if 结构 is 分型结构.下:
            中.分型特征值 = 中.低
            右.分型特征值 = 右.低
            右.分型 = 分型结构.底

        形态 = 分型(左=左, 中=中, 右=右)
        if 结构 in (分型结构.上, 分型结构.下):
            形态 = 分型(中, 右, None)
        return 状态, 形态

    @staticmethod
    def 截取(序列: List[缠论K线], 始: 缠论K线, 终: 缠论K线) -> List[缠论K线]:
        """
        :param 序列: 缠K序列
        :param 始: 起始缠K
        :param 终: 终点缠K
        :return: 缠K子列表
        """
        return 序列[序列.index(始) : 序列.index(终) + 1]


分型模式 = True


@注册
class 分型:
    """由左中右三根缠论K线构成的顶/底分型结构。

    :ivar 左: 左侧缠K（可能为None）
    :ivar 中: 中间缠K（分型顶点/底点）
    :ivar 右: 右侧缠K（可能为None）
    :ivar 结构: 分型结构（顶/底，受 :data:`分型模式` 控制缓存/实时读取）
    :ivar 时间戳: 分型时间戳（受 :data:`分型模式` 控制）
    :ivar 分型特征值: 顶分型取最高价，底分型取最低价（受 :data:`分型模式` 控制）
    :ivar 关系组: 左中、中右、左右三对相对方向（只读）
    :ivar 强度: 分型强度 — 强/中/弱/未知（只读）
    :ivar 与MACD柱子分型匹配: 是否与MACD柱子分型匹配（只读）

    构造:
      :meth:`从缠K序列中获取分型` — 从缠K序列中按中间缠K定位分型

    工具:
      :meth:`判断分型` — 判断左分型的武与右分型的文是否相连
      :meth:`向序列中添加` — 将分型添加到序列（自动去重）
    """

    __slots__ = ["左", "中", "右", "_结构", "_时间戳", "_分型特征值"]

    def __init__(self, 左: Optional[缠论K线], 中: 缠论K线, 右: Optional[缠论K线]):
        """
        :param 左: 左侧缠K
        :param 中: 中间缠K
        :param 右: 右侧缠K
        """
        if 左 and 右:
            assert 左.时间戳 < 中.时间戳 < 右.时间戳
        self.左: Optional[缠论K线] = 左
        self.中: 缠论K线 = 中
        self.右: Optional[缠论K线] = 右
        self._结构 = 中.分型
        self._时间戳 = 中.时间戳
        self._分型特征值 = 中.分型特征值

    def __str__(self):
        return f"{self.结构}<{self.时间戳}, {self.分型特征值:g}, None: {self.左 is None}, None: {self.右 is None}>"

    def __repr__(self):
        return f"{self.结构}<{self.时间戳}, {self.分型特征值:g}, None: {self.左 is None}, None: {self.右 is None}>"

    @property
    def 时间戳(self):
        """分型时间戳 — 分型模式为 True 时返回构造时缓存值，否则从中间缠K实时读取。

        :return: 分型的时间戳
        """
        if 分型模式:
            return self._时间戳
        return self.中.时间戳

    @property
    def 分型特征值(self):
        """分型特征值 — 顶分型为最高价，底分型为最低价。

        :return: 分型的特征价格
        """
        if 分型模式:
            return self._分型特征值
        return self.中.分型特征值

    @property
    def 结构(self):
        """分型结构 — 分型模式为 True 时返回构造时缓存值，否则从中间缠K实时读取。

        :return: 分型结构（顶/底/上/下/散）
        """
        if 分型模式:
            return self._结构
        return self.中.分型

    @property
    def 关系组(self) -> Optional[Tuple[相对方向, 相对方向, 相对方向]]:
        """左、中、右三对相对方向关系

        :return: (左中关系, 中右关系, 左右关系) 或 None
        """
        if self.左 and self.右:
            return 相对方向.分析(self.左.高, self.左.低, self.中.高, self.中.低), 相对方向.分析(self.中.高, self.中.低, self.右.高, self.右.低), 相对方向.分析(self.左.高, self.左.低, self.右.高, self.右.低)
        return None

    @property
    def 强度(self):
        """分型强度（强/中/弱/未知）

        :return: 强度字符串
        """
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
        """
        :return: 底分型时左右MACD柱 > 中MACD柱，顶分型时左右MACD柱 < 中MACD柱
        """
        if self.右 and self.左:
            if self.结构 is 分型结构.底:
                return self.左.标的K线.macd.MACD柱 > self.中.标的K线.macd.MACD柱 < self.右.标的K线.macd.MACD柱
            if self.结构 is 分型结构.顶:
                return self.左.标的K线.macd.MACD柱 < self.中.标的K线.macd.MACD柱 > self.右.标的K线.macd.MACD柱
        return False

    @classmethod
    def 判断分型(cls, 左: 分型, 右: 分型, 模式: str = "中") -> bool:
        """判断两个分型是否相同（identity比较）

        :param 左: 左分型
        :param 右: 右分型
        :param 模式: 比较模式（默认"中"）
        :return: 是否为同一对象
        """
        return 左 is 右

    @staticmethod
    def 从缠K序列中获取分型(K线序列: List[缠论K线], 中: 缠论K线) -> 分型:
        """从缠K序列中提取以指定缠K为中元素的分型

        :param K线序列: 缠K列表
        :param 中: 中间K线
        :return: 分型实例（右可能为None）
        """
        索引 = K线序列.index(中)
        try:
            return 分型(左=K线序列[索引 - 1], 中=中, 右=K线序列[索引 + 1])
        except IndexError:
            return 分型(左=K线序列[索引 - 1], 中=中, 右=None)

    @staticmethod
    def 向序列中添加(分型序列: List[分型], 当前分型: 分型):
        """向分型序列尾部添加，自动校验顶底交替

        :param 分型序列: 现有分型列表
        :param 当前分型: 待添加分型
        :raises ValueError: 首元素非顶底、连续同向分型时抛出
        """
        if not 分型序列 and 当前分型.结构 not in (分型结构.顶, 分型结构.底):
            raise ValueError("首次添加分型不为 顶底", 当前分型)
        if 分型序列:
            if 分型序列[-1].结构 is 当前分型.结构:
                raise ValueError("分型相同无法添加", 分型序列[-1], 当前分型)
            if 分型序列[-1].右 is None:
                logger.warning(f"分型.向序列中添加, 分型异常, {分型序列[-1]}")

        分型序列.append(当前分型)


扩展线段模式 = True  # TODO 虚线高低取值 暂定，此举将符合同级别分解时正确的高低取值涉及中枢等问题


@注册
class 虚线:
    """笔/线段的通用数据结构，持有一组分型端点（文=起点分型, 武=终点分型）。

    :ivar 标识: 类型标识（"笔"/"线段"/"扩展线段"等）
    :ivar 序号: 序号
    :ivar 级别: 级别
    :ivar 文: 起点分型
    :ivar 武: 终点分型
    :ivar 有效性: 是否有效
    :ivar 基础序列: 内部虚线序列（笔序列/线段序列）
    :ivar 特征序列: 特征序列列表（线段专用）
    :ivar 实_中枢序列: 实中枢列表
    :ivar 虚_中枢序列: 虚中枢列表
    :ivar 合_中枢序列: 合中枢列表
    :ivar 确认K线: 确认K线
    :ivar 模式: 买卖点模式
    :ivar 前一缺口: 前一缺口
    :ivar 前一结束位置: 前一笔/线段的终点
    :ivar 短路修正: 是否短路修正
    :ivar 方向: 运行方向（只读）
    :ivar 高: 最高价（只读）
    :ivar 低: 最低价（只读）
    :ivar 笔序列: 所有笔（只读）
    :ivar 图表标题: 图表显示标题（只读）

    构造:
      :meth:`创建笔` — 从两个分型创建笔虚线
      :meth:`创建线段` — 从虚线序列创建线段虚线

    实例方法:
      :meth:`之前是` / :meth:`之后是` — 判断两个虚线的先后关系
      :meth:`获取普K序列` — 获取虚线范围内的原始K线序列
      :meth:`获取缠K序列` — 获取虚线范围内的缠论K线序列
      :meth:`获取数据文本` — 返回关键数据的文本表示

    买卖点匹配:
      :meth:`缠K买卖点模式` / :meth:`买卖点配置匹配` — 按配置模式匹配买卖点
      :meth:`买卖点任意匹配` / :meth:`买卖点全量匹配` / :meth:`买卖点相对匹配` — 不同匹配策略
      :meth:`买卖意义` — 判断虚线是否具有买卖意义

    MACD计算:
      :meth:`计算MACD柱子均值` / :meth:`计算MACD柱子均值_阴` / :meth:`计算MACD柱子均值_阳`
      :meth:`武之全量MACD均值` / :meth:`武之MACD均值` / :meth:`武之MACD均值_阴` / :meth:`武之MACD均值_阳`
      :meth:`武之MACD极值` — 基于MACD极值判断背驰
      :meth:`计算K线序列MACD趋向背驰` — 检测MACD趋向背驰
      :meth:`计算MACD柱子分段` — 将K线序列按MACD柱子符号分段
      :meth:`统计MACD行为` — 统计密集区域的MACD交叉行为

    辅助:
      :meth:`密集区域按间隔` — 按最大间隔和最少交叉数查找密集区域
      :meth:`获取_武` — 获取虚线的有效武分型
    """

    __slots__ = ["标识", "序号", "级别", "文", "武", "有效性", "基础序列", "特征序列", "实_中枢序列", "虚_中枢序列", "合_中枢序列", "确认K线", "模式", "_特征序列_显示", "前一缺口", "前一结束位置", "短路修正"]

    def __init__(self, 序号: int, 标识: str, 文: 分型, 武: 分型, 级别: int, 有效性: bool = True):
        """
        :param 序号: 序号
        :param 标识: 类型标识
        :param 文: 起点分型
        :param 武: 终点分型
        :param 级别: 级别
        :param 有效性: 是否有效
        """
        self.序号 = 序号
        self.标识 = 标识
        self.级别 = 级别

        self.文 = 文
        self.武 = 武

        self.有效性 = 有效性

        self.基础序列: List[虚线] = []
        self.特征序列: List[Optional[线段特征]] = [None, None, None]

        self.实_中枢序列: List[中枢] = []
        self.虚_中枢序列: List[中枢] = []
        self.合_中枢序列: List[中枢] = []
        self.确认K线: Optional[缠论K线] = None
        self.模式: str = "文武"
        self._特征序列_显示 = False
        self.前一缺口: Optional[缺口] = None
        self.前一结束位置 = None
        self.短路修正 = False

    def __str__(self):
        if self.标识 == "笔":
            return f"笔({self.序号}, {self.方向}, {self.文}, {self.武}, 周期: {self.文.中.周期}, 数量: {self.武.中.序号 - self.文.中.序号 + 1})"
        else:
            return f"{self.标识}<{self.序号}, {线段.四象(self)}, {self.方向}, {self.文}, {self.武}, 数量: {len(self.基础序列)}, 缺口: {线段.获取缺口(self)}, {self.确认K线}>"

    def __repr__(self):
        return self.__str__()

    @property
    def 笔序列(self):
        """笔序列"""
        return self.基础序列

    @property
    def 图表标题(self) -> str:
        """
        :return: 图表显示标题
        """
        return f"{self.文.中.标识}:{self.文.中.周期}:{self.标识}:{self.序号}"

    @property
    def 方向(self) -> 相对方向:
        """
        :return: 运行方向
        :raises RuntimeError: 无法识别的方向
        """
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
    def 端点高(self) -> float:
        if self.方向 is 相对方向.向上:
            return self.武.中.高
        return self.文.中.高

    @property
    def 端点低(self) -> float:
        if self.方向 is 相对方向.向下:
            return self.武.中.低
        return self.文.中.低

    @property
    def 高(self) -> float:
        """虚线区间的最高价。

        :return: 向上虚线取武.中.高，向下虚线取文.中.高
        """
        if 扩展线段模式 and self.模式 != "文武" and self.标识 != "笔" and "扩展" in self.标识:  # 扩展线段
            端点序列 = [筆.文 for 筆 in self.基础序列]
            端点序列.append(self.基础序列[-1].武)
            return max(端点序列, key=lambda o: o.中.高).中.高
        return self.端点高

    @property
    def 低(self) -> float:
        """虚线区间的最低价。

        :return: 向下虚线取武.中.低，向上虚线取文.中.低
        """
        if 扩展线段模式 and self.模式 != "文武" and self.标识 != "笔" and "扩展" in self.标识:  # 扩展线段
            端点序列 = [筆.文 for 筆 in self.基础序列]
            端点序列.append(self.基础序列[-1].武)
            return min(端点序列, key=lambda o: o.中.低).中.低
        return self.端点低

    def 之前是(self, 之前: 虚线) -> bool:
        """
        :param 之前: 前一条虚线
        :return: 当前虚线的起点是否为前一条虚线的终点
        """
        if self.标识 == 之前.标识:
            return 分型.判断分型(之前.武, self.文)
        return False

    def 之后是(self, 之后: 虚线) -> bool:
        """
        :param 之后: 后一条虚线
        :return: 当前虚线的终点是否为后一条虚线的起点
        """
        if self.标识 == 之后.标识:
            return 分型.判断分型(self.武, 之后.文)
        return False

    def 获取普K序列(self, 观察员: 观察者) -> List[K线]:
        """
        :param 观察员: 观察者实例
        :return: 区间内的原始K线列表
        """
        return K线.截取(观察员.普通K线序列, self.文.中.标的K线, self.武.中.标的K线)

    def 获取缠K序列(self, 观察员: 观察者) -> List[缠论K线]:
        """
        :param 观察员: 观察者实例
        :return: 区间内的缠K列表
        """
        return 缠论K线.截取(观察员.缠论K线序列, self.文.中, self.武.中)

    def 获取数据文本(self):
        """获取用于保存的数据文本"""
        if self.标识 == "笔":
            return f"{self.标识}, {self.序号}, {self.级别}, 文:({int(self.文.时间戳.timestamp())},{self.文.分型特征值:g}), 武:({int(self.武.时间戳.timestamp())},{self.武.分型特征值:g}), {self.有效性}"
        前, 后, 三, 贯穿伤 = 线段.分割序列(self)
        return f"{self.标识}, {self.序号}, {self.级别}, 文:({int(self.文.时间戳.timestamp())},{self.文.分型特征值:g}), 武:({int(self.武.时间戳.timestamp())},{self.武.分型特征值:g}), {self.有效性}, {len(self.基础序列)}, {线段.特征序列状态(self)}, (前: {str(前)}, 后: {str(后)}, 三: {str(三)}, 伤: {str(贯穿伤)}), 实: {str(self.实_中枢序列)}, 虚: {str(self.虚_中枢序列)}, 合: {str(self.合_中枢序列)}, {self.模式}, {str(self.前一缺口)}, {str(self.前一结束位置)}, {self.短路修正}"

    @classmethod
    def 创建笔(cls, 文: 分型, 武: 分型, 有效性: bool = True) -> 虚线:
        """
        :param 文: 起点分型
        :param 武: 终点分型
        :param 有效性: 是否有效
        :return: 虚线实例（标识="笔"）
        """
        return 虚线(0, "笔", 文, 武, 1, 有效性)

    @classmethod
    def 创建线段(cls, 虚线序列: List[虚线]) -> 虚线:
        """
        :param 虚线序列: 构成线段的虚线列表（笔）
        :return: 虚线实例（标识="线段"或"线段<...>"）
        """
        序列数量 = len(虚线序列)
        if 序列数量 < 3:
            raise RuntimeError(f"创建线段 虚线序列 数量 {序列数量} < 3")
        if 序列数量 % 2 == 0:
            raise RuntimeError(f"创建线段 虚线序列 数量 {序列数量} 不是单数!")
        文 = 虚线序列[0].文
        武 = 虚线序列[-1].武
        assert 文.结构 != 武.结构
        标识 = "线段" if 虚线序列[0].标识 == "笔" else f"线段<{虚线序列[0].标识}>"
        段 = 虚线(0, 标识, 文, 武, 虚线序列[0].级别 + 1)
        段.特征序列 = [None] * 3
        段.实_中枢序列 = []
        段.虚_中枢序列 = []
        段.合_中枢序列 = []
        段.基础序列 = 虚线序列[:]
        return 段

    @classmethod
    def 缠K买卖点模式(cls, 模式: str, 缠K: 缠论K线, 配置: 缠论配置):
        """
        :param 模式: "全量"/"任意"/"配置"/"相对"
        :param 缠K: 待检测的缠论K线
        :param 配置: 缠论配置
        :return: 是否满足买卖点条件
        """
        match 模式:
            case "全量":
                return cls.买卖点全量匹配(缠K)
            case "任意":
                return cls.买卖点任意匹配(缠K)
            case "配置":
                return cls.买卖点配置匹配(缠K, 配置)
            case "相对":
                return cls.买卖点相对匹配(缠K)
        return False

    @classmethod
    def 买卖点配置匹配(cls, 缠K: 缠论K线, 配置: 缠论配置):
        """根据配置中的指标开关检测缠K匹配情况。

        :param 缠K: 待检测的缠论K线
        :param 配置: 包含指标开关的缠论配置
        :return: 是否满足配置中开启的指标匹配条件
        """
        match 配置.买卖点_指标匹配_MACD, 配置.买卖点_指标匹配_KDJ, 配置.买卖点_指标匹配_RSI:
            case True, True, True:
                return 缠K.与MACD柱子匹配 and 缠K.与KDJ匹配 and 缠K.与RSI匹配
            case False, False, False:
                ...

            case True, False, True:
                return 缠K.与MACD柱子匹配 and 缠K.与RSI匹配
            case False, True, False:
                return 缠K.与KDJ匹配

            case True, False, False:
                return 缠K.与MACD柱子匹配
            case False, True, True:
                return 缠K.与KDJ匹配 and 缠K.与RSI匹配

            case False, False, True:
                return 缠K.与RSI匹配
            case True, True, False:
                return 缠K.与MACD柱子匹配 and 缠K.与KDJ匹配
        return False

    @classmethod
    def 买卖点任意匹配(cls, 缠K: 缠论K线):
        """
        :param 缠K: 缠论K线
        :return: MACD/KDJ/RSI 任一匹配
        """
        return any([缠K.与MACD柱子匹配, 缠K.与KDJ匹配, 缠K.与RSI匹配])

    @classmethod
    def 买卖点全量匹配(csl, 缠K: 缠论K线):
        """
        :param 缠K: 缠论K线
        :return: MACD/KDJ/RSI 全部匹配
        """
        return all([缠K.与MACD柱子匹配, 缠K.与KDJ匹配, 缠K.与RSI匹配])

    @classmethod
    def 买卖点相对匹配(cls, 缠K: 缠论K线):
        """
        :param 缠K: 缠论K线
        :return: 三个指标中至少两个匹配
        """
        混沌槽 = [缠K.与MACD柱子匹配, 缠K.与KDJ匹配, 缠K.与RSI匹配]
        return len([匹配 for 匹配 in 混沌槽 if 匹配]) >= 2

    @classmethod
    def 计算MACD柱子均值(cls, 普K序列: List[K线], 实线: 虚线) -> float:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线（笔/线段）
        :return: 区间内MACD柱绝对值的平均值
        """
        K线序列: List[K线] = K线.截取(普K序列, 实线.文.中.标的K线, 实线.武.中.标的K线)
        return sum([abs(K.macd.MACD柱) for K in K线序列]) / len(K线序列)

    @classmethod
    def 计算MACD柱子均值_阴(cls, 普K序列: List[K线], 实线: 虚线) -> float:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 区间内负数MACD柱绝对值的平均值，无负数时返回False
        """
        K线序列: List[K线] = K线.截取(普K序列, 实线.文.中.标的K线, 实线.武.中.标的K线)
        总 = [abs(K.macd.MACD柱) for K in K线序列 if K.macd.MACD柱 < 0]
        if 总:
            return sum(总) / len(总)
        return False

    @classmethod
    def 计算MACD柱子均值_阳(cls, 普K序列: List[K线], 实线: 虚线) -> float:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 区间内正数MACD柱绝对值的平均值，无正数时返回False
        """
        K线序列: List[K线] = K线.截取(普K序列, 实线.文.中.标的K线, 实线.武.中.标的K线)
        总 = [abs(K.macd.MACD柱) for K in K线序列 if K.macd.MACD柱 > 0]
        if 总:
            return sum(总) / len(总)
        return False

    @classmethod
    def 武之全量MACD均值(cls, 普K序列: List[K线], 实线: 虚线) -> bool:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 终点K线的MACD柱是否小于区间均值（全量背驰信号）
        """
        return abs(实线.武.中.标的K线.macd.MACD柱) < cls.计算MACD柱子均值(普K序列, 实线)

    @classmethod
    def 武之MACD均值(cls, 普K序列: List[K线], 实线: 虚线) -> bool:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 根据方向选择阳/阴均值判断
        """
        if 实线.方向 is 相对方向.向上:
            return cls.武之MACD均值_阳(普K序列, 实线)
        else:
            return cls.武之MACD均值_阴(普K序列, 实线)

    @classmethod
    def 武之MACD均值_阴(cls, 普K序列: List[K线], 实线: 虚线) -> bool:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 终点MACD柱绝对值小于阴均值时True（背驰）
        """
        return abs(实线.武.中.标的K线.macd.MACD柱) < abs(cls.计算MACD柱子均值_阴(普K序列, 实线))

    @classmethod
    def 武之MACD均值_阳(cls, 普K序列: List[K线], 实线: 虚线) -> bool:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 终点MACD柱绝对值小于阳均值时True（背驰）
        """
        return abs(实线.武.中.标的K线.macd.MACD柱) < abs(cls.计算MACD柱子均值_阳(普K序列, 实线))

    @classmethod
    def 武之MACD极值(cls, 普K序列: List[K线], 实线: 虚线) -> bool:
        """
        :param 普K序列: 完整K线序列
        :param 实线: 虚线
        :return: 终点MACD柱是否为区间内极值
        """
        K线序列: List[K线] = K线.截取(普K序列, 实线.文.中.标的K线, 实线.武.中.标的K线)
        所有柱子 = [K.macd.MACD柱 for K in K线序列]
        if 实线.武.中.标的K线.macd.MACD柱 > 0:
            取值函数 = max
        else:
            取值函数 = min
        if 取值函数(所有柱子) == 实线.武.中.标的K线.macd.MACD柱:
            return True
        return False

    @classmethod
    def _计算K线序列MACD趋向背驰(cls, 普K序列: Sequence[K线], 方向: 相对方向):
        """计算K线序列的MACD柱/DIF/DEA趋向背驰（三元素判断）

        :param 普K序列: K线序列
        :param 方向: 运行方向
        :return: [柱子背驰, DIF背驰, DEA背驰]
        """
        if 方向 is 相对方向.向上:
            柱子序列 = []
            离差值序列 = []
            信号线序列 = []
            for k线 in 普K序列:
                m = k线.macd
                if m.MACD柱 > 0:
                    柱子序列.append(k线)
                if m.DIF > 0:
                    离差值序列.append(k线)
                if m.DEA > 0:
                    信号线序列.append(k线)

            if not 柱子序列:
                return [False, False, False]
            最高柱子 = max(柱子序列, key=lambda k线: k线.macd.MACD柱)
            最高离差值 = max(离差值序列, key=lambda k线: k线.macd.DIF) if 离差值序列 else None
            最高信号线 = max(信号线序列, key=lambda k线: k线.macd.DEA) if 信号线序列 else None

            结果 = []
            柱子 = [最高柱子, 普K序列[-1]]
            柱子.sort(key=lambda k线: k线.时间戳)
            if 柱子[0].macd.MACD柱 > 柱子[1].macd.MACD柱 and 柱子[0].高 < 柱子[1].高:
                结果.append(True)
            else:
                结果.append(False)

            if 最高离差值 is not None:
                柱子 = [最高离差值, 普K序列[-1]]
                柱子.sort(key=lambda k线: k线.时间戳)
                if 柱子[0].macd.DIF > 柱子[1].macd.DIF and 柱子[0].高 < 柱子[1].高:
                    结果.append(True)
                else:
                    结果.append(False)
            else:
                结果.append(False)

            if 最高信号线 is not None:
                柱子 = [最高信号线, 普K序列[-1]]
                柱子.sort(key=lambda k线: k线.时间戳)
                if 柱子[0].macd.DEA > 柱子[1].macd.DEA and 柱子[0].高 < 柱子[1].高:
                    结果.append(True)
                else:
                    结果.append(False)
            else:
                结果.append(False)

            return 结果
        else:
            柱子序列 = []
            离差值序列 = []
            信号线序列 = []
            for k线 in 普K序列:
                m = k线.macd
                if m.MACD柱 < 0:
                    柱子序列.append(k线)
                if m.DIF < 0:
                    离差值序列.append(k线)
                if m.DEA < 0:
                    信号线序列.append(k线)

            if not 柱子序列:
                return [False, False, False]
            最高柱子 = max(柱子序列, key=lambda k线: abs(k线.macd.MACD柱))
            最高离差值 = max(离差值序列, key=lambda k线: abs(k线.macd.DIF)) if 离差值序列 else None
            最高信号线 = max(信号线序列, key=lambda k线: abs(k线.macd.DEA)) if 信号线序列 else None

            结果 = []
            柱子 = [最高柱子, 普K序列[-1]]
            柱子.sort(key=lambda k线: k线.时间戳)
            if 柱子[0].macd.MACD柱 < 柱子[1].macd.MACD柱 and 柱子[0].低 > 柱子[1].低:
                结果.append(True)
            else:
                结果.append(False)

            if 最高离差值 is not None:
                柱子 = [最高离差值, 普K序列[-1]]
                柱子.sort(key=lambda k线: k线.时间戳)
                if 柱子[0].macd.DIF < 柱子[1].macd.DIF and 柱子[0].低 > 柱子[1].低:
                    结果.append(True)
                else:
                    结果.append(False)
            else:
                结果.append(False)

            if 最高信号线 is not None:
                柱子 = [最高信号线, 普K序列[-1]]
                柱子.sort(key=lambda k线: k线.时间戳)
                if 柱子[0].macd.DEA < 柱子[1].macd.DEA and 柱子[0].低 > 柱子[1].低:
                    结果.append(True)
                else:
                    结果.append(False)
            else:
                结果.append(False)

            return 结果

    @classmethod
    def 计算K线序列MACD趋向背驰(cls, 普K序列: Sequence[K线], 方向: 相对方向):
        """计算K线序列的MACD柱/DIF/DEA趋向背驰（三元素判断）

        :param 普K序列: K线序列
        :param 方向: 运行方向
        :return: [柱子背驰, DIF背驰, DEA背驰]
        """
        if 方向 is 相对方向.向上:
            柱子序列 = [k线 for k线 in 普K序列 if k线.macd.MACD柱 > 0]
            if not 柱子序列:
                return [False, False, False]
            最高柱子 = max(柱子序列, key=lambda k线: k线.macd.MACD柱)
            最低柱子 = min(柱子序列, key=lambda k线: k线.macd.MACD柱)
            排序柱子 = sorted(柱子序列, key=lambda k线: k线.macd.MACD柱)
            离差值序列 = [k线 for k线 in 普K序列 if k线.macd.DIF > 0]
            最高离差值 = max(柱子序列, key=lambda k线: k线.macd.DIF)
            最低离差值 = min(柱子序列, key=lambda k线: k线.macd.DIF)
            信号线序列 = [k线 for k线 in 普K序列 if k线.macd.DEA > 0]
            最高信号线 = max(柱子序列, key=lambda k线: k线.macd.DEA)
            最低信号线 = min(柱子序列, key=lambda k线: k线.macd.DEA)

            结果 = []
            柱子 = [最高柱子, 普K序列[-1]]
            柱子.sort(key=lambda k线: k线.时间戳)
            if 柱子[0].macd.MACD柱 > 柱子[1].macd.MACD柱 and 柱子[0].高 < 柱子[1].高:
                结果.append(True)
            else:
                结果.append(False)

            柱子 = [最高离差值, 普K序列[-1]]
            if 柱子[0].macd.DIF > 柱子[1].macd.DIF and 柱子[0].高 < 柱子[1].高:
                结果.append(True)
            else:
                结果.append(False)

            柱子 = [最高信号线, 普K序列[-1]]
            if 柱子[0].macd.DEA > 柱子[1].macd.DEA and 柱子[0].高 < 柱子[1].高:
                结果.append(True)
            else:
                结果.append(False)

            return 结果
        else:
            柱子序列 = [k线 for k线 in 普K序列 if k线.macd.MACD柱 < 0]
            if not 柱子序列:
                return [False, False, False]
            最高柱子 = max(柱子序列, key=lambda k线: abs(k线.macd.MACD柱))
            最低柱子 = min(柱子序列, key=lambda k线: abs(k线.macd.MACD柱))
            排序柱子 = sorted(柱子序列, key=lambda k线: abs(k线.macd.MACD柱))
            离差值序列 = [k线 for k线 in 普K序列 if k线.macd.DIF < 0]
            最高离差值 = max(柱子序列, key=lambda k线: abs(k线.macd.DIF))
            最低离差值 = min(柱子序列, key=lambda k线: abs(k线.macd.DIF))
            信号线序列 = [k线 for k线 in 普K序列 if k线.macd.DEA < 0]
            最高信号线 = max(柱子序列, key=lambda k线: abs(k线.macd.DEA))
            最低信号线 = min(柱子序列, key=lambda k线: abs(k线.macd.DEA))

            结果 = []
            柱子 = [最高柱子, 普K序列[-1]]
            柱子.sort(key=lambda k线: k线.时间戳)
            if 柱子[0].macd.MACD柱 < 柱子[1].macd.MACD柱 and 柱子[0].低 > 柱子[1].低:
                结果.append(True)
            else:
                结果.append(False)

            柱子 = [最高离差值, 普K序列[-1]]
            if 柱子[0].macd.DIF < 柱子[1].macd.DIF and 柱子[0].低 > 柱子[1].低:
                结果.append(True)
            else:
                结果.append(False)

            柱子 = [最高信号线, 普K序列[-1]]
            if 柱子[0].macd.DEA < 柱子[1].macd.DEA and 柱子[0].低 > 柱子[1].低:
                结果.append(True)
            else:
                结果.append(False)

            return 结果

    @classmethod
    def 买卖意义(cls, 实线: 虚线, 观察员: 观察者) -> Tuple[bool, str]:
        """
        静止是相对的，而运动是绝对的

        :param 实线: 虚线（笔/线段）
        :param 观察员: 观察者实例
        :return: (是否具有买卖意义, 原因字符串)
        """
        普K序列: List[K线] = 观察员.普通K线序列
        配置: 缠论配置 = 观察员.配置
        if 实线.标识 not in ("笔", "线段", "线段<线段>"):
            return False, "标识不在范围内"
        if 实线.武.中.标的K线.kdj.K is None or 实线.武.中.标的K线.kdj.D is None or 实线.武.中.标的K线.kdj.J is None:
            return False, "KDJ指标不完整"
        意义 = cls.缠K买卖点模式(配置.买卖点_指标模式, 实线.武.中, 配置)
        结果 = False
        背驰过 = 笔.是否背驰过(实线, 观察员) if 实线.标识 == "笔" else 线段.是否背驰过(实线, 观察员)
        if 意义:  # and self.武.强度 in ("强", ""):
            if 实线.标识 == "笔":
                if cls.武之MACD均值(普K序列, 实线):
                    return True, "武之MACD均值"
                if cls.武之MACD极值(普K序列, 实线) and 背驰过:
                    return True, "背驰过且极值"
                else:
                    if 实线.武.与MACD柱子分型匹配:
                        return True, f"背驰过:{len(背驰过)},极值:{cls.武之MACD极值(普K序列, 实线)},柱子分型匹配"
            if 实线.标识 != "笔" and 线段.判断线段内部是否背驰(实线, 观察员):
                return True, "线段内部背驰"

        if not 结果 and 意义 and 实线.武.中.与MACD柱子匹配:
            if cls.武之MACD极值(普K序列, 实线) and len(背驰过) > 2:
                return True, "没结果, 极值, 柱子分型匹配, 背驰过大于2次"
        return 结果, ""

    @classmethod
    def 计算MACD柱子分段(cls, k线序列: List[K线]) -> Tuple[List[List[K线]], ...]:
        """
        :param k线序列: K线序列
        :return: 按正负分段的MACD柱列表
        """
        if not k线序列:
            return ()

        def 符号(x: float) -> str:
            if x > 0:
                return "正"
            else:
                return "负"

        当前符号 = 符号(k线序列[0].macd.MACD柱)
        当前段柱子 = [k线序列[0].macd.MACD柱]
        结果 = []

        for i in range(1, len(k线序列)):
            新符号 = 符号(k线序列[i].macd.MACD柱)
            if 新符号 == 当前符号:
                当前段柱子.append(k线序列[i].macd.MACD柱)
            else:
                结果.append(当前段柱子)
                当前段柱子 = [k线序列[i].macd.MACD柱]
                当前符号 = 新符号
        if 当前段柱子:
            结果.append(当前段柱子)
        """a = [x for sub in 结果 for x in sub]
        b = [sub.macd.MACD柱 for sub in k线序列]
        if list(a) != list(b):
            for i,(j,k) in enumerate(zip(a, b)):
                if j is not k:
                    raise RuntimeError( f"序列不一致,{len(a)}, {len(b)}, {(i,j,k)}")"""
        return tuple(结果)

    @classmethod
    def 密集区域按间隔(cls, 交叉标记: List[int], 最大间隔: int = 5, 最少交叉数: int = 3) -> List[Tuple[int, int, int]]:
        """将交叉信号按间隔聚类成密集区域。

        :param 交叉标记: 长度为N的列表，0=无交叉, 1=金叉, -1=死叉
        :param 最大间隔: 相邻交叉索引差 ≤ 此值则归入同一密集区
        :param 最少交叉数: 一个密集区内至少包含的交叉次数
        :return: 密集区域列表 [(起始交叉索引, 结束交叉索引, 区内交叉次数), ...]
        """
        # 提取所有交叉点的索引
        交叉索引 = [i for i, v in enumerate(交叉标记) if v != 0]
        if not 交叉索引:
            return []

        密集区 = []
        当前块起始 = 交叉索引[0]
        当前块交叉数 = 1

        for i in range(1, len(交叉索引)):
            prev_idx = 交叉索引[i - 1]
            curr_idx = 交叉索引[i]
            if curr_idx - prev_idx <= 最大间隔:
                当前块交叉数 += 1
            else:
                # 当前块结束
                if 当前块交叉数 >= 最少交叉数:
                    密集区.append((当前块起始, prev_idx, 当前块交叉数))
                # 开始新块
                当前块起始 = curr_idx
                当前块交叉数 = 1

        # 处理最后一个块
        if 当前块交叉数 >= 最少交叉数:
            密集区.append((当前块起始, 交叉索引[-1], 当前块交叉数))

        return 密集区

    @classmethod
    def 统计MACD行为(cls, 普K序列: List[K线], 最大间隔: int = 8, 最少交叉数: int = 3) -> dict:
        """
        :param 普K序列: K线序列
        :param 最大间隔: 最大间隔 8
        :param 最少交叉数: 最少交叉数 3
        :return: 统计字典
        """
        # 1. 穿越零轴计数
        dif_up = dif_down = dea_up = dea_down = 0
        for i in range(1, len(普K序列)):
            pre, cur = 普K序列[i - 1].macd, 普K序列[i].macd
            if pre is None or cur is None or pre.DIF is None or cur.DIF is None:
                continue
            if pre.DIF < 0 <= cur.DIF:
                dif_up += 1
            elif pre.DIF > 0 >= cur.DIF:
                dif_down += 1
            if pre.DEA is not None and cur.DEA is not None:
                if pre.DEA < 0 <= cur.DEA:
                    dea_up += 1
                elif pre.DEA > 0 >= cur.DEA:
                    dea_down += 1

        # 2. DIF与DEA交叉（带标记）
        golden = death = 0
        交叉标记 = [0]  # 第0个位置无前值，先填0
        for i in range(1, len(普K序列)):
            pre, cur = 普K序列[i - 1].macd, 普K序列[i].macd
            if pre is None or cur is None or pre.DIF is None or cur.DIF is None or pre.DEA is None or cur.DEA is None:
                交叉标记.append(0)
                continue
            if pre.DIF <= pre.DEA and cur.DIF > cur.DEA:
                golden += 1
                交叉标记.append(1)
            elif pre.DIF >= pre.DEA and cur.DIF < cur.DEA:
                death += 1
                交叉标记.append(-1)
            else:
                交叉标记.append(0)

        # 3. 按间隔密集区域
        密集区 = cls.密集区域按间隔(交叉标记, 最大间隔=最大间隔, 最少交叉数=最少交叉数)

        return {
            "DIF上穿0": dif_up,
            "DIF下穿0": dif_down,
            "DEA上穿0": dea_up,
            "DEA下穿0": dea_down,
            "金叉次数": golden,
            "死叉次数": death,
            "密集交叉区域": 密集区,  # (起始交叉索引, 结束交叉索引, 交叉次数)
        }

    @classmethod
    def 获取_武(cls, 实线: 虚线) -> 分型:
        """递归获取虚线的终点分型（笔直接返回武，线段递归到底层笔的武）
        :param 实线: 虚线
        :return: 分型
        """
        if 实线.标识 == "笔":
            return 实线.武
        tmp = 实线
        while tmp.标识 != "笔":
            tmp = tmp.基础序列[-1]
        return tmp.武


@注册
class 笔:
    """纯静态方法容器，提供笔划分算法的所有函数。

    主要方法:
      :meth:`分析` — 流式分析，增量识别笔
      :meth:`以文会友` — 根据起始点找笔
      :meth:`以武会友` — 根据结束点找笔
      :meth:`根据缠K找笔` — 判断缠K是否在文武序号之间
      :meth:`获取所有停顿位置` — 获取笔内所有停顿位置
      :meth:`是否背驰过` — 判断笔是否经过背驰
    """

    __slots__ = []

    @staticmethod
    def _获取缠K数量(缠K序列: List[缠论K线], 笔序列: List[虚线], 配置: 缠论配置) -> int:
        """获取笔内有效缠K数量（考虑笔弱化等配置）

        :param 缠K序列: 候选笔的基础缠K序列
        :param 笔序列: 已有笔序列
        :param 配置: 缠论配置
        :return: 有效缠K数量
        """
        实际数量 = len(缠K序列)
        if 实际数量 >= 配置.笔内元素数量:
            return 实际数量

        if 配置.笔弱化 and 实际数量 >= 3:
            _实际高点 = 笔._实际高点(缠K序列, 配置.笔内相同终点取舍)
            _实际低点 = 笔._实际低点(缠K序列, 配置.笔内相同终点取舍)
            原始数量 = 1 + abs(_实际低点.标的K线.序号 - _实际高点.标的K线.序号)
            if 原始数量 >= 配置.笔内元素数量:
                return 配置.笔内元素数量

            if 笔序列:
                筆 = 笔.根据缠K找笔(笔序列, _实际高点) or 笔.根据缠K找笔(笔序列, _实际低点)
                if 筆:
                    if 筆.方向 is 相对方向.向上 and _实际低点.低 < 筆.低:
                        if 原始数量 >= 配置.笔弱化_原始数量:
                            return 配置.笔内元素数量
                    if 筆.方向 is 相对方向.向下 and _实际低点.低 > 筆.高:
                        if 原始数量 >= 配置.笔弱化_原始数量:
                            return 配置.笔内元素数量

        return 实际数量

    @staticmethod
    def _次高(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        """_次高

        :param 缠K序列: 缠K序列
        :param 笔内相同终点取舍: 终点取舍方式
        :return: 次高缠K
        """
        序列 = sorted(缠K序列, key=lambda k: k.高)
        highs: List[缠论K线] = [k for k in 序列 if k.高 != 序列[-1].高]  # 排除
        highs: List[缠论K线] = [k for k in highs if k.高 == highs[-1].高]  # 筛选
        highs.sort(key=lambda k: k.时间戳)  # 排序
        return highs[-1] if 笔内相同终点取舍 else highs[0]

    @staticmethod
    def _次低(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        """_次低

        :param 缠K序列: 缠K序列
        :param 笔内相同终点取舍: 终点取舍方式
        :return: 次低缠K
        """
        序列 = sorted(缠K序列, key=lambda k: k.低)
        lows: List[缠论K线] = [k for k in 序列 if k.低 != 序列[0].低]
        lows: List[缠论K线] = [k for k in lows if k.低 == lows[0].低]
        lows.sort(key=lambda k: k.时间戳)
        return lows[-1] if 笔内相同终点取舍 else lows[0]

    @staticmethod
    def _实际高点(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        """_实际高点

        :param 缠K序列: 缠K序列
        :param 笔内相同终点取舍: 终点取舍方式
        :return: 实际高点缠K
        """
        序列 = sorted(缠K序列, key=lambda k: k.高)
        highs: List[缠论K线] = [k for k in 序列 if k.高 == 序列[-1].高]
        highs.sort(key=lambda k: k.时间戳)
        return highs[-1] if 笔内相同终点取舍 else highs[0]

    @staticmethod
    def _实际低点(缠K序列: List[缠论K线], 笔内相同终点取舍: bool) -> 缠论K线:
        """_实际低点

        :param 缠K序列: 缠K序列
        :param 笔内相同终点取舍: 终点取舍方式
        :return: 实际低点缠K
        """
        序列 = sorted(缠K序列, key=lambda k: k.低)
        lows: List[缠论K线] = [k for k in 序列 if k.低 == 序列[0].低]
        lows.sort(key=lambda k: k.时间戳)
        return lows[-1] if 笔内相同终点取舍 else lows[0]

    @staticmethod
    def _相对关系(筆: 虚线, 配置: 缠论配置) -> bool:
        """相对关系

        :param 筆: 笔虚线
        :param 配置: 缠论配置
        :return: 方向是否匹配
        """
        if 配置.笔内起始分型包含整笔:
            有效序列 = [k线 for k线 in (筆.文.左, 筆.文.中, 筆.文.右) if k线 is not None]
            文 = 缺口(max(有效序列, key=lambda k: k.高).高, min(有效序列, key=lambda k: k.低).低)
            有效序列 = [k线 for k线 in (筆.武.左, 筆.武.中, 筆.武.右 if 配置.笔内起始分型包含整笔_包括右 else None) if k线 is not None]  # 排除 右
            武 = 缺口(max(有效序列, key=lambda k: k.高).高, min(有效序列, key=lambda k: k.低).低)
            相对关系 = 相对方向.分析(文.高, 文.低, 武.高, 武.低)
        else:
            相对关系 = 相对方向.分析(筆.文.中.高, 筆.文.中.低, 筆.武.中.高, 筆.武.中.低)
            if 配置.笔内原始K线包含整笔 and 相对方向.分析(筆.文.中.标的K线.高, 筆.文.中.标的K线.低, 筆.武.中.标的K线.高, 筆.武.中.标的K线.低).是否包含():  # TODO 建议增加相关配置
                return False

        if 筆.方向 is 相对方向.向下:
            return 相对关系.是否向下()
        return 相对关系.是否向上()

    @classmethod
    def _弹出旧笔(cls, 分型序列: List[分型], 笔序列: List[虚线], 行号):
        """内部方法：弹出最后一个分型和笔

        :param 分型序列: 分型列表
        :param 笔序列: 笔列表
        :param 行号: 调用行号
        """
        旧分型 = 分型序列.pop()
        if 笔序列:
            旧笔 = 笔序列.pop()
            assert 旧笔.武 is 旧分型, f"最后一笔终点错误{行号}"
            旧笔.有效性 = False

    @classmethod
    def _添加新笔(cls, 分型序列: List[分型], 笔序列: List[虚线], 待添加分型: 分型, 待添加新笔: 虚线, 行号):
        """内部方法：添加新分型和新笔

        :param 分型序列: 分型列表
        :param 笔序列: 笔列表
        :param 待添加分型: 待添加的分型
        :param 待添加新笔: 待添加的笔
        :param 行号: 调用行号
        :raises ValueError: 分型相同或笔不连续时抛出
        """
        if not 分型序列 and 待添加分型.结构 not in (分型结构.顶, 分型结构.底):
            raise ValueError("首次添加分型不为 顶底", 待添加分型)
        if 分型序列:
            if 分型序列[-1].结构 is 待添加分型.结构:
                raise ValueError("分型相同无法添加", 分型序列[-1], 待添加分型)
            if 分型序列[-1].右 is None:
                logger.warning(f"分型.向序列中添加, 分型异常 {分型序列[-1]}")

        分型序列.append(待添加分型)
        if 笔序列 and not 笔序列[-1].之后是(待添加新笔):
            raise ValueError("笔.向序列中添加 不连续", 笔序列[-1], 待添加新笔)

        if 笔序列:
            待添加新笔.序号 = 笔序列[-1].序号 + 1
            if 待添加新笔.武.左 is None or 待添加新笔.武.右 is None:
                待添加新笔.有效性 = False
            if 笔序列[-1].武.结构 in (分型结构.上, 分型结构.下):
                logger.error(f"_添加新笔[{行号}] 出现无效分型 {笔序列[-1]}")

        笔序列.append(待添加新笔)

    @classmethod
    def 分析(cls, 当前分型: Optional[分型], 分型序列: List[分型], 笔序列: List[虚线], 缠K序列: List[缠论K线], 普K序列: List[K线], 递归层次: int, 配置: 缠论配置):
        """笔划分核心递归算法

        :param 当前分型: 新形成的分型（可能为None）
        :param 分型序列: 现有分型列表（原地修改）
        :param 笔序列: 现有笔列表（原地修改）
        :param 缠K序列: 缠K序列
        :param 普K序列: 普K序列
        :param 递归层次: 递归深度计数
        :param 配置: 缠论配置
        :return: 递归层次（int）
        """
        if 当前分型 is None:
            return 递归层次

        if 递归层次 > 64:
            logger.warning(f"笔.分析 递归深度超出 64 < {递归层次}")
            # return 递归层次

        if 当前分型.结构 not in (分型结构.顶, 分型结构.底):
            return 递归层次

        if not 分型序列:
            if 当前分型.结构 in (分型结构.顶, 分型结构.底):
                分型序列.append(当前分型)
            return 递归层次

        笔递归分析 = 笔.分析

        之前分型 = 分型序列[-1]
        if (之前分型.时间戳 == 当前分型.时间戳) or (之前分型.结构 in (分型结构.上, 分型结构.下)):
            笔._弹出旧笔(分型序列, 笔序列, sys._getframe().f_lineno)
            if not 分型序列:
                if 当前分型.右 is not None:
                    分型.向序列中添加(分型序列, 当前分型)
                return 递归层次

        之前分型 = 分型序列[-1]
        if 之前分型.时间戳 > 当前分型.时间戳 and 之前分型.中.序号 - 当前分型.中.序号 > 1:
            # raise RuntimeError(f"时序错误-{递归层次}, {之前分型}, {当前分型}")
            logger.error(f"时序错误-{递归层次}, {之前分型}, {当前分型}")
            return 递归层次

        if 配置.笔弱化 and 笔序列:
            前一笔 = 笔序列[-1]
            if 前一笔.武.中.序号 - 前一笔.文.中.序号 + 1 == 3:
                if (前一笔.方向.是否向上() and 前一笔.低 > 当前分型.分型特征值 and 当前分型.结构 is 分型结构.底) or (前一笔.方向.是否向下() and 前一笔.高 < 当前分型.分型特征值 and 当前分型.结构 is 分型结构.顶):
                    笔._弹出旧笔(分型序列, 笔序列, sys._getframe().f_lineno)
                    return 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)

        if 之前分型.结构 is not 当前分型.结构:
            基础序列 = 缠论K线.截取(缠K序列, 之前分型.中, 当前分型.中)
            当前笔 = 虚线.创建笔(文=之前分型, 武=当前分型, 有效性=True)
            if 笔._获取缠K数量(基础序列, 笔序列, 配置) >= 配置.笔内元素数量:
                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    文官 = 笔._实际高点(基础序列, False)
                else:
                    文官 = 笔._实际低点(基础序列, False)

                if 文官 is not 之前分型.中:
                    临时分型 = 分型.从缠K序列中获取分型(缠K序列, 文官)
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        assert 临时分型.结构 is 分型结构.顶, 临时分型
                    else:
                        assert 临时分型.结构 is 分型结构.底, 临时分型
                    递归层次 = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                    递归层次 = 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                    return 递归层次

                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    武将 = 笔._实际低点(基础序列, 配置.笔内相同终点取舍)
                else:
                    武将 = 笔._实际高点(基础序列, 配置.笔内相同终点取舍)

                if 笔._相对关系(当前笔, 配置) and 当前分型.中 is 武将:
                    笔._添加新笔(分型序列, 笔序列, 当前分型, 当前笔, sys._getframe().f_lineno)
                    return 递归层次

                if 配置.笔次级成笔:
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        武将 = 笔._次低(基础序列, 配置.笔内相同终点取舍)
                    else:
                        武将 = 笔._次高(基础序列, 配置.笔内相同终点取舍)
                    if 笔._相对关系(当前笔, 配置) and 当前分型.中 is 武将:
                        笔._添加新笔(分型序列, 笔序列, 当前分型, 当前笔, sys._getframe().f_lineno)
                        return 递归层次

            else:
                if 当前分型.右:
                    临时分型 = 分型.从缠K序列中获取分型(缠K序列, 当前分型.右)
                    递归层次 = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)

        else:
            分型特征值 = 当前分型.分型特征值

            if (之前分型.结构 is 分型结构.顶 and 之前分型.分型特征值 < 分型特征值) or (之前分型.结构 is 分型结构.底 and 之前分型.分型特征值 > 分型特征值):
                笔._弹出旧笔(分型序列, 笔序列, sys._getframe().f_lineno)
                k线序列 = 缠论K线.截取(缠K序列, 之前分型.中, 当前分型.中)
                if 之前分型.结构 is 分型结构.顶:
                    武将 = 笔._实际低点(k线序列, 配置.笔内相同终点取舍)
                else:
                    武将 = 笔._实际高点(k线序列, 配置.笔内相同终点取舍)
                临时分型 = 分型.从缠K序列中获取分型(缠K序列, 武将)

                if 分型序列:
                    递归层次 = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                    if 分型序列 and 分型序列[-1] is 临时分型:
                        # 进行修复错过的笔
                        for ck in 缠K序列[缠K序列.index(武将) :]:
                            if ck.分型 in (分型结构.底, 分型结构.顶) and 分型序列[-1].时间戳 < ck.时间戳:
                                临时分型 = 分型.从缠K序列中获取分型(缠K序列, ck)
                                递归层次 = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                                if 分型序列 and 分型序列[-1] is 临时分型:
                                    logger.warning(f"笔.分析 事后修复错过的笔:{临时分型}, 当前分型: {当前分型}")

                    递归层次 = 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                    return 递归层次
                else:
                    分型.向序列中添加(分型序列, 当前分型)

        return 递归层次

    @staticmethod
    def 以文会友(笔序列: List[虚线], 文: 分型) -> Optional[虚线]:
        """以文会友

        :param 笔序列: 笔列表
        :param 文: 起点分型
        :return: 匹配的笔或None
        """
        for 筆 in 笔序列:
            if 筆.文 is 文:
                return 筆
        return None

    @staticmethod
    def 以武会友(笔序列: List[虚线], 武: 分型) -> Optional[虚线]:
        """以武会友

        :param 笔序列: 笔列表
        :param 武: 终点分型
        :return: 匹配的笔或None
        """
        for 筆 in 笔序列[::-1]:
            if 筆.武 is 武:
                return 筆
        return None

    @staticmethod
    def 根据缠K找笔(笔序列: List[虚线], 缠K: 缠论K线, 偏移: int = 1):
        """根据缠K找笔

        :param 笔序列: 笔列表
        :param 缠K: 缠论K线
        :param 偏移: 序号偏移量
        :return: 包含该缠K的笔或None
        """
        for 筆 in 笔序列[::-1]:
            if 筆.文.中.序号 - 偏移 <= 缠K.序号 <= 筆.武.中.序号:
                if 筆.文.中.周期 == 缠K.周期 and 筆.文.中.标识 == 缠K.标识:
                    return 筆

        return None

    @classmethod
    def _自检(cls, 筆: 虚线, 观察员: 观察者) -> bool:
        """校验笔的有效性：高/低点是否为实际极值

        :param 筆: 待校验的笔
        :param 观察员: 观察者
        :return: 有效为True
        """
        笔序列: List[虚线] = 观察员.笔序列
        配置: 缠论配置 = 观察员.配置
        基础序列 = 筆.获取缠K序列(观察员)
        if 笔._获取缠K数量(基础序列, 笔序列, 配置) >= 配置.笔内元素数量:
            if 筆.方向 is 相对方向.向下 and 筆.文.中 is 笔._实际高点(基础序列, False) and 筆.武.中 is 笔._实际低点(基础序列, 配置.笔内相同终点取舍):
                return True
            if 筆.方向 is 相对方向.向上 and 筆.文.中 is 笔._实际低点(基础序列, False) and 筆.武.中 is 笔._实际高点(基础序列, 配置.笔内相同终点取舍):
                return True
        return False

    @classmethod
    def 获取所有停顿位置(cls, 筆: 虚线, 观察员: 观察者) -> List[虚线]:
        """获取笔内所有可能的停顿位置（用于背驰检测）

        :param 筆: 笔
        :param 观察员: 观察者
        :return: 停顿位置的笔列表
        """
        笔序列 = []
        文 = 筆.文
        基础序列 = 筆.获取缠K序列(观察员.观察员)
        for i in range(3, len(基础序列) - 1):
            K = 基础序列[i]
            武 = 分型(基础序列[i - 1], K, 基础序列[i + 1])
            if K.分型 is 分型结构.顶 and 筆.方向 is 相对方向.向上:
                当前笔 = 虚线.创建笔(文=文, 武=武)
                当前笔.序号 = 筆.序号
                笔._自检(当前笔, 观察员) and 笔序列.append(当前笔)

            if K.分型 is 分型结构.底 and 筆.方向 is 相对方向.向下:
                当前笔 = 虚线.创建笔(文=文, 武=武)
                当前笔.序号 = 筆.序号
                笔._自检(当前笔, 观察员) and 笔序列.append(当前笔)

        return 笔序列

    @classmethod
    def 是否背驰过(cls, 当前筆: 虚线, 观察员: 观察者) -> List[缠论K线]:
        """判断笔内是否发生过MACD趋向背驰

        :param 当前筆: 笔
        :param 观察员: 观察者
        :return: 发生背驰的停顿位置列表
        """
        停顿位置 = 笔.获取所有停顿位置(当前筆, 观察员)
        结果 = []

        for 筆 in 停顿位置:
            if all(虚线.计算K线序列MACD趋向背驰(K线.截取(观察员.普通K线序列, 当前筆.文.中.标的K线, 当前筆.武.中.标的K线), 筆.方向)):  # if 筆.武之MACD均值:
                结果.append(筆.武.中)
        return 结果


class 线段特征:
    """持有一组同向虚线（笔），是线段划分的中间结构。

    特征序列用于线段划分算法中的包含处理和缺口判断。

    :ivar 序号: 序号
    :ivar 标识: 标识
    :ivar 线段方向: 线段运行方向（特征序列方向为其翻转）
    :ivar 基础序列: 虚线序列
    :ivar 文: 第一个元素的起点分型（根据方向选取极值）
    :ivar 武: 最后一个元素的终点分型（根据方向选取极值）
    :ivar 高: 最高价
    :ivar 低: 最低价
    :ivar 方向: 特征序列方向（线段方向的翻转）
    :ivar 图表标题: 图表标题

    主要方法:
      :meth:`新建` — 从虚线序列创建单个线段特征
      :meth:`静态分析` — 将虚线序列静态划分为线段特征列表（含包含处理）
      :meth:`获取分型序列` — 从特征序列中提取分型序列

    注意:
      Rust 绑定层仅导出 ``静态分析``，字段除了 ``标识`` 其余仅可读。
    """

    __slots__ = ["序号", "标识", "线段方向", "基础序列"]

    def __init__(self, 标识: str, 基础序列: List[虚线], 线段方向: 相对方向):
        """
        :param 标识: 标识符
        :param 基础序列: 基础虚线列表
        :param 线段方向: 线段运行方向
        """
        self.基础序列 = 基础序列[:]
        self.序号 = 0
        self.标识: str = 标识
        self.线段方向: 相对方向 = 线段方向

    @property
    def 图表标题(self) -> str:
        """
        :return: 图表标题
        """
        return self.标识  # f"{self.标识}:{self.序号}"

    def __str__(self):
        if not len(self.基础序列):
            return f"{self.标识}<{self.线段方向}, 空>"
        return f"{self.标识}<{self.线段方向}, {self.文}, {self.武}, {len(self.基础序列)}>"

    def __repr__(self):
        if not len(self.基础序列):
            return f"{self.标识}<{self.线段方向}, 空>"
        return f"{self.标识}<{self.线段方向}, {self.文}, {self.武}, {len(self.基础序列)}>"

    @property
    def 文(self) -> 分型:
        """线段特征的起点分型。

        :return: 向上取高高中的最大分型，向下取低低中的最小分型
        """
        if self.线段方向 is 相对方向.向上:  # 取高高
            return max(
                [线.文 for 线 in self.基础序列],
                key=lambda o: (o.分型特征值, o.时间戳),
            )
        else:
            return min(
                [线.文 for 线 in self.基础序列],
                key=lambda o: (o.分型特征值, -o.时间戳.timestamp()),
            )

    @property
    def 武(self) -> 分型:
        """线段特征的终点分型。

        :return: 向上取高高中的最大分型，向下取低低中的最小分型
        """
        if self.线段方向 is 相对方向.向上:
            return max(
                [线.武 for 线 in self.基础序列],
                key=lambda o: (o.分型特征值, o.时间戳),
            )
        else:
            return min(
                [线.武 for 线 in self.基础序列],
                key=lambda o: (o.分型特征值, -o.时间戳.timestamp()),
            )

    @property
    def 高(self) -> float:
        """
        :return: 文和武中分型特征值的较大者
        """
        return max([self.文, self.武], key=lambda fx: fx.分型特征值).分型特征值

    @property
    def 低(self) -> float:
        """
        :return: 文和武中分型特征值的较小者
        """
        return min([self.文, self.武], key=lambda fx: fx.分型特征值).分型特征值

    @property
    def 方向(self) -> 相对方向:
        """
        :return: 特征序列方向（线段方向的翻转）
        """
        return self.线段方向.翻转()

    def _添加(self, 待添加虚线: Union[虚线]):
        """
        :param 待添加虚线: 待添加的虚线
        :raises ValueError: 方向不匹配时抛出
        """
        if 待添加虚线.方向 == self.线段方向:
            raise ValueError("方向不匹配", self.线段方向, 待添加虚线, self)
        self.基础序列.append(待添加虚线)

    def _删除(self, 待删除虚线: Union[虚线]):
        """
        :param 待删除虚线: 待删除的虚线
        :raises ValueError: 方向不匹配时抛出
        """
        if 待删除虚线.方向 == self.方向:
            raise ValueError("方向不匹配", self.线段方向, 待删除虚线, self)
        self.基础序列.remove(待删除虚线)

    @classmethod
    def 新建(cls, 虚线序列: List[虚线], 线段方向: 相对方向) -> 线段特征:
        """
        :param 虚线序列: 基础虚线列表
        :param 线段方向: 线段方向
        :return: 线段特征实例
        """
        return 线段特征(标识=f"特征<{虚线序列[0].__class__.__name__}>", 基础序列=虚线序列, 线段方向=线段方向)

    @classmethod
    def 静态分析(cls, 虚线序列: List[虚线], 线段方向: 相对方向, 四象: str, 是否忽视: bool = False) -> List[线段特征]:
        """静态分析虚线序列，生成特征序列

        :param 虚线序列: 笔/虚线列表
        :param 线段方向: 线段运行方向
        :param 四象: "老阳"/"老阴"/"小阳"/"少阴"
        :param 是否忽视: True时不严格处理缺口包含
        :return: 特征序列列表
        """
        # 确定需要合并的方向序列
        if 四象 in ("老阳", "老阴") and not 是否忽视:
            # 特征序列带有缺口时 要严格处理包含关系
            需要被合并方向序列 = (相对方向.顺, 相对方向.逆, 相对方向.同)
            # 需要被合并方向序列 = (相对方向.顺, 相对方向.同)
        else:
            需要被合并方向序列 = (相对方向.顺, 相对方向.同)

        特征序列: List[线段特征] = []

        for 当前虚线 in 虚线序列:
            # ----- 情况1：方向相同（可能触发分型替换）-----
            if 当前虚线.方向 is 线段方向:
                # 守卫：特征序列不足3个时，直接跳过本虚线（不执行任何合并）
                if len(特征序列) < 3:
                    continue

                左, 中, 右 = 特征序列[-3], 特征序列[-2], 特征序列[-1]
                结构 = 分型结构.分析(左, 中, 右, 可以逆序包含=True, 忽视顺序包含=True)

                # 条件：向上线段形成顶分型且当前虚线高点高于中，或向下线段形成底分型且当前虚线低点低于中
                if (线段方向 is 相对方向.向上 and 结构 is 分型结构.顶 and 当前虚线.高 > 中.高) or (线段方向 is 相对方向.向下 and 结构 is 分型结构.底 and 当前虚线.低 < 中.低):
                    小号虚线 = min(中.基础序列, key=lambda o: o.序号)
                    大号虚线 = max(右.基础序列, key=lambda o: o.序号)
                    fake = 虚线.创建笔(文=小号虚线.文, 武=大号虚线.武, 有效性=False)
                    特征序列.pop()
                    特征序列[-1] = 线段特征.新建([fake], 线段方向)
                # 无论是否替换，本虚线不进入合并逻辑
                continue

            # ----- 情况2：方向不同（执行特征序列的合并/添加）-----
            # 若特征序列为空，直接添加新特征序列
            if not 特征序列:
                特征序列.append(线段特征.新建([当前虚线], 线段方向))
                continue

            # 特征序列非空：检查与最后一个特征序列的方向关系
            之前线段特征 = 特征序列[-1]
            if 相对方向.分析(之前线段特征.高, 之前线段特征.低, 当前虚线.高, 当前虚线.低) in 需要被合并方向序列:
                之前线段特征._添加(当前虚线)
            else:
                特征序列.append(线段特征.新建([当前虚线], 线段方向))

        return 特征序列

    @classmethod
    def 获取分型序列(cls, 特征序列: List):
        """从特征序列提取特征分型序列

        :param 特征序列: 线段特征列表
        :return: 特征分型列表
        """
        结构序列 = []
        for i in range(1, len(特征序列) - 1):
            结构 = 分型结构.分析(特征序列[i - 1], 特征序列[i], 特征序列[i + 1], True, True)
            结构序列.append(特征分型(特征序列[i - 1], 特征序列[i], 特征序列[i + 1], 结构))
        if 结构序列:
            assert 特征序列[-1] is 结构序列[-1].右
        return 结构序列


class 特征分型:
    """特征分型 — 由左右中三个线段特征构成的顶/底分型，用于线段划分算法。
    注意: Rust 绑定层不导！
    :ivar 左: 左侧特征序列
    :ivar 中: 中间特征序列
    :ivar 右: 右侧特征序列
    :ivar 结构: 分型结构（顶/底）
    """

    __slots__ = ["左", "中", "右", "结构"]

    def __init__(self, 左: 线段特征, 中: 线段特征, 右: 线段特征, 结构: 分型结构):
        """
        :param 左: 左侧特征序列
        :param 中: 中间特征序列
        :param 右: 右侧特征序列
        :param 结构: 分型结构
        """
        self.左: 线段特征 = 左
        self.中: 线段特征 = 中
        self.右: 线段特征 = 右
        self.结构 = 结构

    def __str__(self):
        return f"特征分型<{self.结构}, {self.中}>"

    def __repr__(self):
        return f"特征分型<{self.结构}, {self.中}>"


@注册
class 线段:
    """纯静态方法容器，提供线段划分算法的所有函数。

    核心方法:
      :meth:`分析` — 流式分析，增量识别线段（主入口）
      :meth:`扩展分析` — 流式扩展线段分析（基于线段生成更高级别线段）

    特征序列:
      :meth:`特征分型终结` — 判断线段是否被特征分型终结
      :meth:`特征序列状态` — 返回特征序列的缺口/突破/包含状态
      :meth:`获取缺口` — 获取线段特征序列之间的缺口
      :meth:`四象` — 判断线段的四象模式（涨跌盘等）

    序列操作:
      :meth:`分割序列` — 按中枢将线段基础序列分割为进入段/中枢段/离开段
      :meth:`查找贯穿伤` — 查找贯穿中枢的线段
      :meth:`获取内部中枢序列` — 获取线段内部的笔中枢/段中枢/扩展中枢

    辅助判断:
      :meth:`判断线段内部是否背驰` — 判断线段内部是否存在背驰
      :meth:`获取所有停顿位置` — 获取线段内所有停顿位置（买卖点候选）
      :meth:`是否背驰过` — 返回线段内背驰对应的缠K列表
    """

    __slots__ = []

    @staticmethod
    def _索引(序列: list, 项) -> int:
        """O(1) index lookup — 序列元素序号连续递增。"""
        # return 项.序号 - 序列[0].序号
        return 序列.index(项)

    @classmethod
    def _添加虚线(cls, 段: 虚线, 筆: 虚线):
        """向线段中添加一笔

        :param 段: 线段
        :param 筆: 待添加的笔
        :raises ValueError: 不连续或标识不符时抛出
        """
        if len(段.基础序列) and not 分型.判断分型(段.基础序列[-1].武, 筆.文):
            raise ValueError(f"{段.标识}.添加虚线 不连续", 段.基础序列[-1], 筆)

        if len(段.基础序列) and 段.基础序列[-1].标识 != 筆.标识:
            raise ValueError(f"{段.标识}.添加虚线 标识不符", 段.基础序列[-1].标识, 筆.标识)
        段.基础序列.append(筆)

    @classmethod
    def _武斗(cls, 段: 虚线, 武: 分型, 行号: int):
        """更新线段的终点分型（武）

        :param 段: 线段
        :param 武: 新的终点分型
        :param 行号: 调用行号（用于调试）
        """
        # logger.warning(f"{段.标识}.武斗[{行号}], ", 武)
        if 段.武 is 武:
            # logger.warning(f"{段.标识}.武斗[{行号}], 相同")
            return
        if 段.武.分型特征值 == 武.分型特征值 and 段.武.时间戳 != 武.时间戳:
            logger.warning(f"{段.标识}.武斗[{行号}], 发现特征值相等但时间戳不同, {段.武}, {武}")
        assert 段.文.结构 is not 武.结构, (f"文武结构相同 {行号}", 段.文, 武)
        if 武.右 is not None and 分型结构.分析(武.左, 武.中, 武.右) is not 武.结构:
            raise RuntimeError(分型结构.分析(武.左, 武.中, 武.右), 武.结构)
        if 段.方向 is 相对方向.向上:
            if 武.分型特征值 < 段.文.分型特征值:
                raise RuntimeError(f"向上{段.标识}, 结束点 小于 起点", 段.标识, 段.文, 武)

            if 段.武.分型特征值 > 武.分型特征值 and 段.模式 == "文武":
                logger.warning(f"{段.标识}.武斗[{行号}] 出现回退 从 {段.武} ==>>> {武}")  # raise RuntimeError(段.武, 武)
        else:
            if 武.分型特征值 > 段.文.分型特征值:
                raise RuntimeError(f"向下{段.标识}, 结束点 大于 起点", 段.标识, 段.文, 武)
            if 段.武.分型特征值 < 武.分型特征值 and 段.模式 == "文武":
                logger.warning(f"{段.标识}.武斗[{行号}] 出现回退 从 {段.武} ==>>> {武}")  # raise RuntimeError(段.武, 武)
        段.武 = 武

    @classmethod
    def 特征分型终结(cls, 段: 虚线) -> bool:
        """是否符合特征序列正常分型终结

        :param 段: 线段
        :return: 是否终结
        """
        特征序列 = 线段特征.静态分析(段.基础序列, 段.方向, 线段.四象(段))
        if len(特征序列) >= 3:
            结构 = 分型结构.分析(特征序列[-3], 特征序列[-2], 特征序列[-1], True, True)
            if 段.方向 is 相对方向.向上:
                if 结构 is 分型结构.顶:
                    return True
            else:
                if 结构 is 分型结构.底:
                    return True

        return False

    @classmethod
    def 特征序列状态(cls, 段: 虚线) -> Tuple[bool, bool, bool]:
        """
        :param 段: 线段
        :return: (左是否存在, 中是否存在, 右是否存在)
        """
        return tuple(特征 is not None for 特征 in 段.特征序列)

    @classmethod
    def 获取缺口(cls, 段: 虚线) -> Optional[缺口]:
        """获取线段特征序列第一二元素间的缺口

        :param 段: 线段
        :return: 缺口或None
        """
        if 段.模式 != "文武":
            return None
        左, 中, 右 = 段.特征序列
        if 左 is None:
            return None
        if 中 is None:
            return None
        相对关系 = 相对方向.分析(左.高, 左.低, 中.高, 中.低)
        if 相对关系.是否缺口():
            高低 = [左.文.分型特征值, 中.文.分型特征值]
            return 缺口(max(*高低), min(*高低))
        return None

    @classmethod
    def 四象(cls, 段: 虚线) -> str:
        """判断线段的四象属性

        :param 段: 线段
        :return: "老阳"(向下线段后继缺口向上线段) / "老阴"(向上线段后继缺口向下线段) / "小阳"(普通向上) / "少阴"(普通向下)
        """
        if 段.前一缺口 is not None:
            return "老阳" if 段.方向 is 相对方向.向上 else "老阴"
        return "小阳" if 段.方向 is 相对方向.向上 else "少阴"

    @classmethod
    def _设置特征序列(cls, 段: 虚线, 序列, 行号):
        """设置特征序列

        :param 段: 线段
        :param 序列: 特征序列三元组 (左,中,右)
        :param 行号: 调用行号
        """
        # logger.warning(f"线段.设置特征序列[{行号}]", self)
        if 段.模式 != "文武":
            return

        for 特征 in 序列:
            if 特征 and 特征.方向 == 段.方向:
                raise ValueError(f"特征序列方向不匹配[{行号}]")
        左, 中, 右 = 序列
        段.特征序列 = [左, 中, 右]
        if 右 is not None:
            基础序列 = []
            if 右.基础序列[-1] not in 段.基础序列:
                raise ValueError()
            for 元素 in 段.基础序列:
                基础序列.append(元素)
                if 元素 is 右.基础序列[-1]:
                    break

            if (len(基础序列) >= 6) and (len(基础序列) % 2 == 0):
                段.基础序列[:] = 基础序列
            else:
                raise RuntimeError()
        else:
            pass

    @classmethod
    def _刷新特征序列(cls, 段: 虚线, 配置: 缠论配置):
        """刷新特征序列

        :param 段: 线段
        :param 配置: 缠论配置
        """
        if 段.模式 != "文武":
            return
        基础序列 = 段.基础序列
        if 段.前一结束位置 and 段.前一结束位置 in 基础序列:
            基础序列 = 段.基础序列[cls._索引(段.基础序列, 段.前一结束位置) - 1 :]

        特征序列 = 线段特征.静态分析(基础序列, 段.方向, 线段.四象(段), 配置.线段_特征序列忽视老阴老阳)
        if len(特征序列) >= 3:
            分型序列 = 线段特征.获取分型序列(特征序列)
            if (段.方向 is 相对方向.向上 and 分型序列[-1].结构 is 分型结构.顶) or (段.方向 is 相对方向.向下 and 分型序列[-1].结构 is 分型结构.底):
                线段._设置特征序列(段, [分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)

            else:
                线段._设置特征序列(段, [特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)
        else:
            特征序列.extend([None] * (3 - len(特征序列)))
            线段._设置特征序列(段, 特征序列, sys._getframe().f_lineno)

    @classmethod
    def 分割序列(cls, 段: 虚线, 所属中枢: Optional[中枢] = None) -> Tuple[List[虚线], List[虚线], List[虚线], Optional[虚线]]:
        """将线段基础序列分割为前/后/第三买卖/贯穿伤四部分

        :param 段: 线段
        :param 所属中枢: 所属中枢（用于第三买卖点检测）
        :return: (前序列, 后序列, 第三买卖线, 贯穿伤)
        """
        if 段.模式 != "文武":
            return 段.基础序列[:], [], [], None

        assert 段.基础序列[0].文 is 段.文, (段.基础序列[0].文, 段.文)
        前: List[虚线] = []
        后: List[虚线] = []
        第三买卖线 = []
        贯穿伤 = None

        for 筆 in 段.基础序列:
            if not 前:
                前.append(筆)
                continue
            if 前[-1].武 is not 段.武 and not 后:
                前.append(筆)

            if 后:
                后.append(筆)
            if 筆.文 is 段.武:
                后.append(筆)

        状态 = None

        if 所属中枢:
            所属中枢.本级_第三买卖线 = None
            尾部 = 段.武
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
            for 筆 in 段.基础序列[::-1]:
                if 筆.方向 is 相对方向.向下:
                    关系 = 相对方向.分析(所属中枢.高, 所属中枢.低, 筆.高, 筆.低)
                    if 关系 is 相对方向.向上缺口:
                        第三买卖线.append(筆)
                    else:
                        break

        if 状态 == "中枢之下":
            for 筆 in 段.基础序列[::-1]:
                if 筆.方向 is 相对方向.向上:
                    关系 = 相对方向.分析(所属中枢.高, 所属中枢.低, 筆.高, 筆.低)
                    if 关系 is 相对方向.向下缺口:
                        第三买卖线.append(筆)
                    else:
                        break

        if 第三买卖线 and 所属中枢:
            第三买卖线.reverse()
            所属中枢.本级_第三买卖线 = 第三买卖线[0]
            # 所属中枢.本级_第三买卖线.备注 = 所属中枢.标识

        if 后:
            if 段.方向.是否向上():
                if 后[0].武.分型特征值 < 段.文.分型特征值:
                    贯穿伤 = 后[0]
            else:
                if 后[0].武.分型特征值 > 段.文.分型特征值:
                    贯穿伤 = 后[0]

        return 前, 后, 第三买卖线, 贯穿伤

    @classmethod
    def _刷新(cls, 段: 虚线, 配置: 缠论配置):
        """刷新线段的特征序列和内部中枢序列

        :param 段: 线段
        :param 配置: 缠论配置
        """
        if 段.模式 != "文武":
            return
        if not len(段.基础序列):
            logger.warning("    线段.刷新 基础序列为空")
            return

        线段._刷新特征序列(段, 配置)
        有效特征序列 = [特征 for 特征 in 段.特征序列 if 特征 is not None]
        if len(有效特征序列) == 3:
            线段._武斗(段, 段.特征序列[1].文, sys._getframe().f_lineno)

        elif len(有效特征序列) >= 1:
            最近特征 = 有效特征序列[-1]

            if 最近特征.基础序列[-1] not in 段.基础序列:
                特征后一笔 = 笔.以武会友(段.基础序列, 最近特征.基础序列[-1].武)
            else:
                特征后一笔 = 最近特征.基础序列[-1]

            if 特征后一笔 is not None:
                序号 = cls._索引(段.基础序列, 特征后一笔)
                if 序号 < len(段.基础序列) - 1:
                    下一笔 = 段.基础序列[序号 + 1]
                    if (段.方向 is 相对方向.向上 and 段.高 <= 下一笔.高) or (段.方向 is 相对方向.向下 and 段.低 >= 下一笔.低):
                        线段._武斗(段, 下一笔.武, sys._getframe().f_lineno)
            else:
                logger.warning(f"    线段.刷新 特征后一笔 = None, {段}, {有效特征序列}")
        else:
            raise RuntimeError(len(有效特征序列))
        线段.获取内部中枢序列(段, 配置)

    @classmethod
    def _序列重置(cls, 段: 虚线, 序列: Sequence):
        """序列重置

        :param 段: 线段
        :param 序列: 参考序列
        """
        基础序列 = []
        序列集 = set(序列) if not isinstance(序列, set) else 序列
        for 元素 in 段.基础序列:
            if 元素 not in 序列集:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    break
            基础序列.append(元素)

        段.基础序列[:] = 基础序列
        段.特征序列[2] = None

    @classmethod
    def 查找贯穿伤(cls, 段: 虚线) -> Optional[虚线]:
        """查找贯穿伤

        :param 段: 线段
        :return: 贯穿伤虚线或None
        """
        for 贯穿伤 in 段.基础序列[3:]:
            if 段.方向.是否向上():
                if 贯穿伤.武.分型特征值 < 段.文.分型特征值:
                    return 贯穿伤
            else:
                if 贯穿伤.武.分型特征值 > 段.文.分型特征值:
                    return 贯穿伤
        return None

    @classmethod
    def 获取内部中枢序列(cls, 段: 虚线, 配置: 缠论配置) -> Tuple[List[中枢], List[中枢], List[中枢]]:
        """获取内部中枢序列

        :param 段: 线段
        :param 配置: 缠论配置
        :return: (虚中枢列表, 实中枢列表, 合中枢列表)
        """
        if 段.模式 != "文武":
            中枢.分析(段.基础序列, 段.合_中枢序列, 标识=f"{段.标识}_{段.序号}_合_")
            return [], [], 段.合_中枢序列
        实, 虚, _, _ = 线段.分割序列(段)

        中枢.分析(实, 段.实_中枢序列, 标识=f"{段.标识}_{段.序号}_实_")
        中枢.分析(虚, 段.虚_中枢序列, 标识=f"{段.标识}_{段.序号}_虚_")
        中枢.分析(段.基础序列, 段.合_中枢序列, 标识=f"{段.标识}_{段.序号}_合_")
        return 段.虚_中枢序列, 段.实_中枢序列, 段.合_中枢序列  # 阴 阳 合

    @classmethod
    def _基础判断(cls, 左: 虚线, 中: 虚线, 右: 虚线, 关系序列: List[相对方向]) -> bool:
        """
        连续三笔且重叠

        :param 左: 左侧虚线
        :param 中: 中间虚线
        :param 右: 右侧虚线
        :param 关系序列: 允许的方向关系
        :return: 是否满足基础条件
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
    def _添加线段(cls, 线段序列: List[虚线], 待添加线段: 虚线, 配置: 缠论配置, 行号: int, 层级: int):
        """内部方法：向线段序列添加新线段

        :param 线段序列: 线段列表
        :param 待添加线段: 新线段
        :param 配置: 缠论配置
        :param 行号: 调用行号
        :param 层级: 递归层级
        """
        if 线段序列 and not 线段序列[-1].之后是(待添加线段):
            raise ValueError(f"线段.向序列中添加 不连续[{行号}, {层级}]", 线段序列[-1].武, 待添加线段.文)
        待添加线段.模式 = "文武"

        if not 线段序列:
            线段序列.append(待添加线段)
            return

        之前线段 = 线段序列[-1]

        if not 之前线段.特征序列[2] and not 之前线段.短路修正:
            assert not 待添加线段.短路修正 and 之前线段.特征序列[2][-1] in 待添加线段.基础序列
            raise RuntimeError(f"线段._向序列中添加[{行号}, {层级}], 之前线段.右 = None", 之前线段)

        if 之前线段.基础序列[-1] not in 待添加线段.基础序列 and not 之前线段.短路修正:
            raise RuntimeError(f"线段._向序列中添加[{行号}, {层级}], 之前线段[-1] not in 待添加虚线!", 之前线段)

        待添加线段.序号 = 之前线段.序号 + 1
        待添加线段.前一缺口 = 线段.获取缺口(之前线段) if not 之前线段.短路修正 else None
        待添加线段.前一结束位置 = 之前线段.基础序列[-1]

        if 线段.四象(之前线段) in ("老阴", "老阳"):
            待添加线段.前一缺口 = None

        线段序列.append(待添加线段)
        # logger.warning(f"线段._向序列中添加[{行号}]", 待添加虚线)

    @classmethod
    def _弹出线段(cls, 线段序列: List[虚线], 待弹出线段: 虚线, 配置: 缠论配置, 行号: int, 层级: int):
        """内部方法：从线段序列弹出最后一个线段

        :param 线段序列: 线段列表
        :param 待弹出线段: 待弹出的线段
        :param 配置: 缠论配置
        :param 行号: 调用行号
        :param 层级: 递归层级
        :return: 弹出的线段或None
        """
        if not 线段序列:
            return None

        if 线段序列[-1] is not 待弹出线段:
            raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

        左, 中, 右 = 待弹出线段.特征序列
        if 右 is not None:
            结构 = 分型结构.分析(左, 中, 右, True, True)
            if 结构 in (分型结构.顶, 分型结构.底) and not 相对方向.分析(左.高, 左.低, 中.高, 中.低).是否缺口():
                logger.warning(f"警告<{行号}, {层级}>] 线段._从序列中删除 发现分型完毕, 且特征序列无缺口 {待弹出线段}")

        线段序列.pop()
        待弹出线段.前一结束位置 = None
        待弹出线段.有效性 = False

        return 待弹出线段

    @classmethod
    def _缺口突破(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        """内部方法：处理缺口突破修正, 正常修正
        除此之外的修正皆为短路修正，此修正为正常处理
        :param 线段序列: 线段列表
        :param 配置: 缠论配置
        :param 层级: 递归深度
        :return: 是否执行了修正
        """
        当前线段 = 线段序列[-1]
        assert 当前线段.基础序列, "缺口突破: 当前线段.基础序列为空！"
        当前虚线: 虚线 = 当前线段.基础序列[-1]
        四象 = 线段.四象(当前线段)
        同向 = 当前虚线.方向 is 当前线段.方向

        # 条件1：不能同向
        if 同向:
            return False

        # 条件2：四象必须是老阳或老阴
        if 四象 not in ("老阳", "老阴"):
            return False

        # 条件3：当前线段特征序列[2]必须为None
        if 当前线段.特征序列[2] is not None:
            return False

        # 条件4：具体突破方向判断
        if not ((四象 == "老阳" and 当前虚线.低 < 当前线段.低) or (四象 == "老阴" and 当前虚线.高 > 当前线段.高)):
            return False

        # 已被修正
        if 线段序列[-2].短路修正:
            return False

        # 执行修正
        序列 = 当前线段.基础序列[:]
        线段._弹出线段(线段序列, 当前线段, 配置, sys._getframe().f_lineno, 层级)
        assert 线段序列, "缺口突破: 线段序列为第二次空！"
        当前线段 = 线段序列[-1]

        assert 当前线段.特征序列[2] is not None
        当前线段基础序列 = 线段.分割序列(当前线段)[0]
        assert 当前线段基础序列[-1].之后是(序列[0]), "缺口突破: 子序列不连续!"
        当前线段基础序列.extend(序列)

        当前线段.基础序列[:] = 当前线段基础序列
        线段._刷新(当前线段, 配置)
        return True

    @classmethod
    def _非缺口下穿刺(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        """内部方法：处理非缺口下穿刺修正

        :param 线段序列: 线段列表
        :param 配置: 缠论配置
        :param 层级: 递归深度
        :return: 是否执行了修正
        """
        assert 线段序列, "非缺口下穿刺: 线段序列为空！"
        当前线段 = 线段序列[-1]
        四象 = 线段.四象(当前线段)

        # 外层条件
        if not (配置.线段_非缺口下穿刺 and 四象 in ("小阳", "少阴") and 当前线段.特征序列[2] is None):
            return False

        # 查找贯穿伤
        贯穿伤 = 线段.查找贯穿伤(当前线段)
        if not 贯穿伤:
            return False

        assert 贯穿伤 in 当前线段.基础序列, "非缺口下穿刺: 贯穿伤不在基础序列中！"
        # 切割基础序列
        基础序列 = 当前线段.基础序列[cls._索引(当前线段.基础序列, 贯穿伤) :]

        # 长度条件
        if not (len(基础序列) == 4 and len(线段序列) >= 2):
            return False

        左, 中, 右 = 基础序列[-3], 基础序列[-2], 基础序列[-1]

        # 方向条件
        if 相对方向.分析(左.高, 左.低, 右.高, 右.低) is not 当前线段.方向:
            return False

        # 执行修正
        logger.warning(f"[警告<{sys._getframe().f_lineno}, {层级}>]: {当前线段.标识}.修复贯穿伤, 序号:{当前线段.序号} {贯穿伤} {基础序列}")  # 异常弹出

        基础序列 = 当前线段.基础序列[:]
        线段._弹出线段(线段序列, 当前线段, 配置, sys._getframe().f_lineno, 层级)
        assert 线段序列, "非缺口下穿刺: 第二次线段序列为空！"
        当前线段 = 线段序列[-1]
        当前线段.特征序列[2] = None
        # assert 当前线段.基础序列[-1] in 基础序列, "非缺口下穿刺: 当前线段.基础序列[-1] 不在 基础序列中！"
        if 当前线段.基础序列[-1] not in 基础序列:
            logger.error(f"非缺口下穿刺: 当前线段.基础序列[-1] 不在 基础序列中！")
            序号 = 0
        else:
            序号 = cls._索引(基础序列, 当前线段.基础序列[-1]) + 1

        for 临时虚线 in 基础序列[序号:]:
            线段._添加虚线(当前线段, 临时虚线)
        线段._刷新(当前线段, 配置)
        当前线段.短路修正 = True

        if 当前线段.特征序列[2] is not None:
            段 = 虚线.创建线段([左, 中, 右])
            线段._添加线段(线段序列, 段, 配置, sys._getframe().f_lineno, 层级)
            段.特征序列[0] = 线段特征.新建([中], 段.方向)

        return True

    @classmethod
    def _缺口后紧急修正(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        """内部方法：处理缺口后紧急修正

        执行逻辑: 在缺口

        :param 线段序列: 线段列表
        :param 配置: 缠论配置
        :param 层级: 递归深度
        :return: 是否执行了修正
        """
        assert 线段序列, "缺口后紧急修正: 线段序列为空！"
        当前线段 = 线段序列[-1]
        四象 = 线段.四象(当前线段)

        # 外层条件检查
        if not (配置.线段_缺口后紧急修正 and not 配置.线段_特征序列忽视老阴老阳 and 四象 in ("小阳", "少阴") and 当前线段.特征序列[2] is None):
            return False

        # 内层条件：长度和前一线的四象
        if not (len(线段序列) >= 2 and 线段.四象(线段序列[-2]) in ("老阴", "老阳")):
            return False

        基础序列 = 线段.分割序列(当前线段)[1]
        if len(基础序列) < 3:
            return False

        需要修正 = False
        if 当前线段.方向 is 相对方向.向上:
            if 相对方向.分析(基础序列[0].高, 基础序列[0].低, 基础序列[2].高, 基础序列[2].低) is 相对方向.向下:
                需要修正 = True
        else:  # 向下方向
            if 相对方向.分析(基础序列[0].高, 基础序列[0].低, 基础序列[2].高, 基础序列[2].低) is 相对方向.向上:
                需要修正 = True

        if not 需要修正:
            return False

        # 执行修正
        当前线段.短路修正 = True
        新段 = 虚线.创建线段(基础序列)
        线段._添加线段(线段序列, 新段, 配置, sys._getframe().f_lineno, 层级)
        return True

    @classmethod
    def _修正(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        """内部方法：处理线段修正
        执行逻辑: 当线段第二特征序列超过两次合并后且尾部元素出现与当前线段相同方向时执行修正，
                生成两个线段，生成的线段符合一段被一段破坏的基础逻辑

        :param 线段序列: 线段列表
        :param 配置: 缠论配置
        :param 层级: 递归深度
        :return: 是否执行了修正
        """
        assert 线段序列, "修正: 线段序列为空！"
        当前线段 = 线段序列[-1]

        # 条件1：配置允许修正且当前线段基础序列长度足够
        if not (配置.线段_修正 and len(当前线段.基础序列) >= 9):
            return False

        # 分割序列
        当前基础序列, 之后基础序列, _, _ = 线段.分割序列(当前线段)

        # 条件2：之后基础序列长度至少为6
        if len(之后基础序列) < 6:
            return False
        if len(之后基础序列) % 2 != 0:
            return False

        # 取倒数第3和第1个元素
        前, 后 = 之后基础序列[-3], 之后基础序列[-1]

        # 条件3：当前线段方向与后两个元素形成的方向一致
        if 当前线段.方向 is not 相对方向.分析(前.高, 前.低, 后.高, 后.低):
            return False

        # 所有条件满足，执行修正
        当前线段.短路修正 = True

        # 创建第一个新段（之后基础序列去掉最后3个）
        新段 = 虚线.创建线段(之后基础序列[:-3])
        新段.短路修正 = True
        线段._添加线段(线段序列, 新段, 配置, sys._getframe().f_lineno, 层级)

        # 根据当前线段的四象决定是否清空前一个缺口
        if 线段.四象(当前线段) in ("老阴", "老阳"):
            新段.前一缺口 = None

        # 创建第二个新段（最后3个元素）
        新段 = 虚线.创建线段(之后基础序列[-3:])
        线段._添加线段(线段序列, 新段, 配置, sys._getframe().f_lineno, 层级)

        return True

    @classmethod
    def 分析(cls, 笔序列: List[虚线], 线段序列: List[虚线], 配置: 缠论配置, 层级: int = 0, 关系序列=[相对方向.向上, 相对方向.向下]) -> None:
        """线段划分核心递归算法 — 从笔序列递归生成线段。

        :param 笔序列: 笔列表
        :param 线段序列: 线段列表（原地修改）
        :param 配置: 缠论配置
        :param 层级: 递归深度
        :param 关系序列: 允许的方向关系
        :return: None（结果写入线段序列）
        """
        # 递归深度守卫
        if 层级 > 256:
            logger.warning("线段.分析 递归深度超出 256")
            return None
            # raise RuntimeError("线段分析 层级过深")

        # if len(笔序列) < 3:return None
        try:
            笔序列[2]
        except IndexError:
            return None

        线段递归分析 = 线段.分析

        # -------------------- 1. 初始化第一个线段 --------------------
        if not 线段序列:
            for i in range(1, len(笔序列) - 1):
                左, 中, 右 = 笔序列[i - 1], 笔序列[i], 笔序列[i + 1]
                if not 线段._基础判断(左, 中, 右, 关系序列):  # FIXME 首个线段必须有明确方向
                    continue
                段 = 虚线.创建线段([左, 中, 右])
                线段._添加线段(线段序列, 段, 配置, sys._getframe().f_lineno, 层级)
                段.特征序列[0] = 线段特征.新建([中], 段.方向)
                break
            if not 线段序列:
                return None

        # -------------------- 2. 清理无效的尾部引用 --------------------
        while 线段序列 and 线段序列[-1].前一结束位置:
            if 线段序列[-1].前一结束位置 not in 笔序列:
                线段._弹出线段(线段序列, 线段序列[-1], 配置, sys._getframe().f_lineno, 层级)
            else:
                break

        if not 线段序列:
            return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

        # -------------------- 3. 确保当前线段有效 --------------------
        当前线段 = 线段序列[-1]
        线段._序列重置(当前线段, 笔序列)

        if len(当前线段.基础序列) < 3:
            线段._弹出线段(线段序列, 当前线段, 配置, sys._getframe().f_lineno, 层级)
            if not 线段序列:
                return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

        当前线段 = 线段序列[-1]

        # -------------------- 4. 特征序列已完整时的处理 --------------------
        if 当前线段.特征序列[2] is not None:
            基础序列 = 线段.分割序列(当前线段)[1]
            新段 = 虚线.创建线段(基础序列)
            线段._添加线段(线段序列, 新段, 配置, sys._getframe().f_lineno, 层级)
            if 线段.四象(当前线段) in ("老阴", "老阳"):
                新段.前一缺口 = None

        当前线段 = 线段序列[-1]
        线段._刷新(当前线段, 配置)

        # -------------------- 5. 调用一次全局修正（不循环） --------------------
        线段._缺口突破(线段序列, 配置, 层级)
        线段._非缺口下穿刺(线段序列, 配置, 层级)
        线段._缺口后紧急修正(线段序列, 配置, 层级)
        线段._修正(线段序列, 配置, 层级)

        # -------------------- 6. 循环处理后续的笔 --------------------
        当前线段 = 线段序列[-1]
        if not 当前线段.基础序列:
            raise RuntimeError
        起始索引 = cls._索引(笔序列, 当前线段.基础序列[-1]) + 1

        for idx in range(起始索引, len(笔序列)):
            当前虚线 = 笔序列[idx]
            当前线段 = 线段序列[-1]
            四象 = 线段.四象(当前线段)

            线段._添加虚线(当前线段, 当前虚线)
            线段._刷新(当前线段, 配置)

            # 依次尝试四种修正，任意一个成功则跳过后续处理
            修正触发 = False
            if 线段._缺口突破(线段序列, 配置, 层级):
                修正触发 = "缺口突破"
            elif 线段._非缺口下穿刺(线段序列, 配置, 层级):
                修正触发 = "非缺口下穿刺"
            elif 线段._缺口后紧急修正(线段序列, 配置, 层级):
                修正触发 = "缺口后紧急修正"
            elif 线段._修正(线段序列, 配置, 层级):
                修正触发 = "修正"
            if 修正触发:
                logger.warning(f"分析.修正触发={修正触发}, 笔序列长度={len(笔序列)}, 线段序列长度={len(线段序列)}")
                continue

            # 无修正触发，且特征序列[2]已存在 → 创建新段
            if 当前线段.特征序列[2] is None:
                continue

            基础序列 = 线段.分割序列(当前线段)[1]
            新段 = 虚线.创建线段(基础序列)
            线段._添加线段(线段序列, 新段, 配置, sys._getframe().f_lineno, 层级)
            if 四象 in ("老阴", "老阳"):
                新段.前一缺口 = None

            # 检查新段与当前虚线的连续性
            if 新段.基础序列[-1] is not 当前虚线:
                if not 新段.基础序列[-1].之后是(当前虚线):
                    return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)
                线段._添加虚线(新段, 当前虚线)

            线段._刷新(新段, 配置)

        return None

    @classmethod
    def _武终(cls, 段: 虚线, 行号: int):
        """武终

        :param 段: 线段
        :param 行号: 调用行号
        """
        if 段.模式 != "文武":
            线段._武斗(段, 段.基础序列[-1].武, 行号)

    @classmethod
    def _验证序列(cls, 段: 虚线, 序列: Sequence):
        """验证序列

        :param 段: 线段
        :param 序列: 参考序列
        """
        基础序列 = []
        序列集 = set(序列) if not isinstance(序列, set) else 序列
        for 元素 in 段.基础序列:
            if 元素 not in 序列集:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    logger.warning("    线段._验证序列 数据不连续")
                    break
            基础序列.append(元素)
        段.基础序列[:] = 基础序列
        if len(段.基础序列) % 2 == 0:
            段.基础序列 and 段.基础序列.pop()

    @classmethod
    def _添加扩展线段(cls, 线段序列: List[虚线], 待添加线段: 虚线, 行号: int):
        """内部方法：向扩展线段序列添加新线段

        :param 线段序列: 扩展线段列表
        :param 待添加线段: 新线段
        :param 行号: 调用行号
        """
        待添加线段.模式 = "高低"
        待添加线段.标识 = f"扩展{待添加线段.标识}" if 待添加线段.基础序列[0].标识 != "笔" else "扩展线段"
        if 线段序列 and not 线段序列[-1].之后是(待添加线段):
            raise ValueError(f"{线段序列[-1].标识}.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)
        if 线段序列:
            之前线段 = 线段序列[-1]
            待添加线段.序号 = 之前线段.序号 + 1

        线段序列.append(待添加线段)
        # logger.warning(f"线段._向序列中添加[{行号}]", 待添加线段)

    @classmethod
    def _弹出扩展线段(cls, 线段序列: List[虚线], 待弹出线段: 虚线, 行号: int):
        """内部方法：从扩展线段序列弹出最后一个线段

        :param 线段序列: 扩展线段列表
        :param 待弹出线段: 待弹出的线段
        :param 行号: 调用行号
        :return: 弹出的线段或None
        """
        if not 线段序列:
            return None

        if 线段序列[-1] is 待弹出线段:
            drop = 线段序列.pop()
            待弹出线段.有效性 = False
            # logger.warning(f"线段._从序列中删除[{行号}]", 待弹出线段)
            return drop
        raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

    @classmethod
    def 扩展分析(cls, 虚线序列: List[虚线], 线段序列: List[虚线], 配置: 缠论配置) -> None:
        """同级别分析 — 将虚线视为线段进行递归段划分。

        :param 虚线序列: 基础虚线列表
        :param 线段序列: 扩展线段列表（原地修改）
        :param 配置: 缠论配置
        :return: None（结果写入线段序列）
        """
        if not 虚线序列:
            return None
        try:
            虚线序列[2]
        except IndexError:
            return None
        线段递归扩展分析 = 线段.扩展分析

        if not 线段序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                关系 = 相对方向.分析(左.端点高, 左.端点低, 右.端点高, 右.端点低)
                if 关系 not in (相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同):  # FIXME 此处为首个线段
                    continue

                段 = 虚线.创建线段([左, 中, 右])
                线段._添加扩展线段(线段序列, 段, sys._getframe().f_lineno)
                break

        # 检查线段元素
        if not 线段序列:
            return None

        当前线段 = 线段序列[-1]
        线段._验证序列(当前线段, 虚线序列)
        if len(当前线段.基础序列) < 3:
            线段._弹出扩展线段(线段序列, 当前线段, sys._getframe().f_lineno)
            return 线段递归扩展分析(虚线序列, 线段序列, 配置)

        if not 配置.扩展线段_当下分析:
            左, 中, 右 = 当前线段.基础序列[:3]
            if not 相对方向.分析(左.端点高, 左.端点低, 右.端点高, 右.端点低).是否缺口():
                当前线段.基础序列[:] = 当前线段.基础序列[:3]
                线段._武终(当前线段, sys._getframe().f_lineno)
            else:
                线段._弹出扩展线段(线段序列, 当前线段, sys._getframe().f_lineno)
                return 线段递归扩展分析(虚线序列, 线段序列, 配置)

        线段._武终(当前线段, sys._getframe().f_lineno)  # TODO 添加错误处理机制
        if 当前线段.基础序列[-1].序号 + 3 > 虚线序列[-1].序号:
            return None

        序号 = cls._索引(虚线序列, 当前线段.基础序列[-1]) + 1
        if 序号 >= len(虚线序列):
            return None

        for i in range(序号 + 1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            相对关系 = 相对方向.分析(左.端点高, 左.端点低, 右.端点高, 右.端点低)
            if 相对关系.是否缺口():
                线段._添加虚线(当前线段, 左)
                线段._添加虚线(当前线段, 中)
                线段._武终(当前线段, sys._getframe().f_lineno)
                continue

            if 左 in 当前线段.基础序列:
                continue

            段 = 虚线.创建线段([左, 中, 右])
            线段._添加扩展线段(线段序列, 段, sys._getframe().f_lineno)
            return 线段递归扩展分析(虚线序列, 线段序列, 配置)

    @classmethod
    def 判断线段内部是否背驰(cls, 当前段: 虚线, 观察员: 观察者) -> bool:
        """判断线段内部是否发生背驰（基于内部中枢和MACD）

        :param 当前段: 线段
        :param 观察员: 观察者
        :return: bool
        """
        阳, 阴, _, _ = 线段.分割序列(当前段)
        if len(阴) > 0:
            """
            1.大于2且未完成，第二特征序列正在合并中，
                0.继续合并
                1.之后突破第二序列线段延续
                2.反之 出现第三特征序列线段完成 出现相反线段
                    1.有缺口
                    2.无缺口

            总之就是有 阴 则不判断
            """
        笔之实数 = len(阳)
        if 笔之实数 < 3:
            return False

        进入段 = 阳[-3]
        离开段 = 阳[-1]
        assert 进入段.序号 < 离开段.序号
        关系 = 相对方向.分析(进入段.高, 进入段.低, 离开段.高, 离开段.低)
        背驰 = False
        盘整背驰 = False
        if ((进入段.方向.是否向上() and 关系.是否向上()) or (进入段.方向.是否向下() and 关系.是否向下())) and 背驰分析.背驰模式(进入段, 离开段, 观察员.普通K线序列, 观察员.配置, 观察员.配置.线段内部背驰_模式):
            k线序列 = K线.截取(观察员.普通K线序列, 阳[-3].文.中.标的K线, 阳[-1].武.中.标的K线)
            if len(虚线.计算MACD柱子分段(k线序列)) >= 3:
                盘整背驰 = True  # and MACD均值背驰

        """进入段 = 阳[0]
        离开段 = 阳[-1]
        if ((进入段.方向.是否向上() and 关系.是否向上()) or (进入段.方向.是否向下() and 关系.是否向下())) and 背驰分析.背驰模式(进入段, 离开段, 观察员.普通K线序列, 观察员.配置, 观察员.配置.线段内部背驰_模式):
            盘整背驰 = 阳[-1].武之MACD均值 if not 盘整背驰 else 盘整背驰"""

        if 当前段.实_中枢序列:
            if 阳[-1] in 当前段.实_中枢序列[-1].基础序列:
                # 当前最后一笔在最后一中枢里
                序号 = cls._索引(当前段.基础序列, 当前段.实_中枢序列[-1].基础序列[0])
                进入段 = 当前段.基础序列[序号 - 1]
                离开段 = 阳[-1]
                assert 进入段.序号 < 离开段.序号, (进入段.序号, 离开段.序号)
                if 进入段.方向 is not 离开段.方向:
                    return 背驰分析.测度背驰(进入段, 离开段) and 虚线.买卖意义(离开段, 观察员)
                关系 = 相对方向.分析(进入段.高, 进入段.低, 离开段.高, 离开段.低)
                if ((进入段.方向.是否向上() and 关系.是否向上()) or (进入段.方向.是否向下() and 关系.是否向下())) and 背驰分析.背驰模式(进入段, 离开段, 观察员.普通K线序列, 观察员.配置, 观察员.配置.线段内部背驰_模式):
                    return True

            elif 当前段.实_中枢序列[-1].第三买卖线:
                # 第三买卖点后后 盘整背驰
                进入段 = 阳[-3]
                离开段 = 阳[-1]
                assert 进入段.序号 < 离开段.序号
                if 进入段.方向 is not 离开段.方向:
                    return 背驰分析.测度背驰(进入段, 离开段) and 虚线.买卖意义(离开段, 观察员)
                关系 = 相对方向.分析(进入段.高, 进入段.低, 离开段.高, 离开段.低)
                if ((进入段.方向.是否向上() and 关系.是否向上()) or (进入段.方向.是否向下() and 关系.是否向下())) and 背驰分析.背驰模式(进入段, 离开段, 观察员.普通K线序列, 观察员.配置, 观察员.配置.线段内部背驰_模式):
                    return True
        else:
            # 没有中枢
            if 笔之实数 == 3:
                背驰 = 盘整背驰

        return 背驰 or 盘整背驰

    @classmethod
    def 获取所有停顿位置(cls, 段: 虚线, 观察员: 观察者) -> List[虚线]:
        """获取所有停顿位置

        :param 段: 线段
        :param 观察员: 观察者
        :return: 停顿位置的线段列表
        """
        self = 段
        结果 = []
        if self.模式 != "文武":
            return 结果
        if self.标识 != "线段":  # 不考虑段的段，不如直接更换K线周期
            return 结果
        阳, 阴, _, _ = 线段.分割序列(段, None)
        线段序列 = []
        笔序列 = []
        当前停顿 = None

        for 筆 in 阳:
            if len(笔序列) >= 3:
                筆停顿 = 笔.获取所有停顿位置(筆, 观察员)
                筆停顿.append(筆)
                for 停顿 in 筆停顿:
                    笔序列.append(停顿)
                    线段.分析(笔序列, 线段序列, 观察员.配置, 关系序列=[相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同])
                    if 线段序列 and 线段序列[-1].武 is not 当前停顿 and len(线段序列[-1].基础序列) % 2 == 1:
                        新段 = 虚线.创建线段(线段序列[-1].基础序列)
                        新段.序号 = self.序号
                        线段._刷新(新段, 观察员.配置)
                        if 新段.方向 is self.方向:
                            结果.append(新段)
                            当前停顿 = 线段序列[-1].武

                    if 停顿 is not 筆:
                        笔序列.pop().有效性 = False
            else:
                笔序列.append(筆)
        return 结果

    @classmethod
    def 是否背驰过(cls, 当前段: 虚线, 观察员: 观察者) -> List[缠论K线]:
        """判断线段内是否发生过背驰（遍历所有停顿位置）

        :param 当前段: 线段
        :param 观察员: 观察者
        :return: 背驰点列表
        """
        停顿位置 = 线段.获取所有停顿位置(当前段, 观察员)
        结果 = []

        for 段 in 停顿位置:
            线段.获取内部中枢序列(段, 观察员.配置)
            if 线段.判断线段内部是否背驰(段, 观察员):
                结果.append(段.武.中)
        return 结果


@注册
class 中枢:
    """三段虚线重叠区间构成的价格中枢，支持延伸和扩展。

    :ivar 序号: 序号
    :ivar 标识: 标识
    :ivar 级别: 级别
    :ivar 基础序列: 构成中枢的基础虚线（至少3条）
    :ivar 第三买卖线: 第三类买卖点关联虚线
    :ivar 本级_第三买卖线: 本级第三类买卖点虚线
    :ivar 高: 中枢上沿（虚线低点的最大值）
    :ivar 低: 中枢下沿（虚线高点的最小值）
    :ivar 高高: 全区间最高价
    :ivar 低低: 全区间最低价
    :ivar 文: 起点分型
    :ivar 武: 终点分型
    :ivar 方向: 中枢方向（首条虚线的方向翻转）
    :ivar 离开段: 最后一条虚线

    构造方法:
      :meth:`创建` — 从左右中三条虚线构造中枢
      :meth:`从序列中获取中枢` — 从虚线序列中提取第一个中枢

    流式分析:
      :meth:`分析` — 流式分析，增量识别中枢（主入口）
      :meth:`基础检查` — 检查三条虚线是否满足中枢重叠条件

    实例方法:
      :meth:`获取序列` — 获取中枢包含的所有虚线
      :meth:`获取扩展中枢` — 获取中枢的扩展中枢序列
      :meth:`完整性` — 检查中枢虚实序列的完整性
      :meth:`获取数据文本` — 返回中枢关键数据的文本表示
      :meth:`当前状态` — 返回中枢当前状态描述
      :meth:`设置第三买卖线` — 设置第三类买卖点关联虚线
    """

    __slots__ = ["序号", "标识", "级别", "基础序列", "第三买卖线", "本级_第三买卖线"]

    def __init__(self, 序号: int, 标识: str, 级别: int, 基础序列: List[虚线]):
        """
        :param 序号: 序号
        :param 标识: 标识
        :param 级别: 级别
        :param 基础序列: 基础虚线列表
        """
        self.基础序列 = 基础序列[:3]
        self.序号: int = 序号
        self.标识: str = 标识
        self.级别: int = 级别
        self.第三买卖线: Optional[虚线] = None
        self.本级_第三买卖线: Optional[虚线] = None

    def _添加虚线(self, 实线: 虚线):
        """向中枢添加新虚线（延伸），重置第三买卖线

        :param 实线: 新虚线
        """
        self.基础序列.append(实线)
        self.本级_第三买卖线: Optional[虚线] = None
        self.第三买卖线: Optional[虚线] = None

    def __str__(self):
        return f"{self.标识}({self.高:g}, {self.低:g}, 元素数量: {len(self.基础序列)}, {str(self.基础序列)}, {self.基础序列[0].文} ===>>> {self.基础序列[-1].武})"

    def __repr__(self):
        return str(self)

    @property
    def 图表标题(self) -> str:
        """
        :return: 图表标题
        """
        return f"{self.文.中.标识}:{self.文.中.周期}:{self.标识}:{self.序号}"

    @property
    def 离开段(self) -> 虚线:
        """
        :return: 最后一条虚线
        """
        return self.基础序列[-1]

    @property
    def 方向(self) -> 相对方向:
        """
        :return: 中枢方向（首条虚线的方向翻转）
        """
        return self.基础序列[0].方向.翻转()

    @property
    def 高(self) -> float:
        """
        :return: 中枢上沿（前三段中虚线高点的最小值）
        """
        return min(self.基础序列[:3], key=lambda o: o.高).高

    @property
    def 低(self) -> float:
        """
        :return: 中枢下沿（前三段中虚线低点的最大值）
        """
        return max(self.基础序列[:3], key=lambda o: o.低).低

    @property
    def 高高(self) -> float:
        """
        :return: 全区间最高价
        """
        return max(self.基础序列, key=lambda o: o.高).高

    @property
    def 低低(self) -> float:
        """
        :return: 全区间最低价
        """
        return min(self.基础序列, key=lambda o: o.低).低

    @property
    def 文(self) -> 分型:
        """
        :return: 起点分型
        """
        return self.基础序列[0].文

    @property
    def 武(self) -> 分型:
        """
        :return: 终点分型
        """
        return self.基础序列[-1].武

    def 获取数据文本(self):
        """获取用于保存的数据文本"""
        return f"{self.标识}, {self.序号}, {self.级别}, 文:({int(self.文.时间戳.timestamp())},{self.文.分型特征值:g}), 武:({int(self.武.时间戳.timestamp())},{self.武.分型特征值:g}), {self.第三买卖线}, {self.本级_第三买卖线}"

    def 完整性(self, 虚实: str):
        """判断中枢是否完整（是否有第三买卖点或内部中枢离开）

        详情见 教你炒股票 43：有关背驰的补习课(2007-04-06 15:31:28)
        不完整时 下一个中枢大概率会与当前中枢发生扩展！

        :param 虚实: "实"/"虚"/"合"
        :return: 完整为True
        """
        if self.基础序列[0].标识 == "笔":
            # 笔中枢
            return self.第三买卖线 is not None

        else:
            # if self.本级_第三买卖线:
            #     return True
            中枢状态 = self.当前状态()
            if 中枢状态 == "中枢之中":
                return False
            线段内部中枢 = self.基础序列[-1].合_中枢序列 if 虚实 == "合" else self.基础序列[-1].实_中枢序列
            if not 线段内部中枢:
                return False
            高, 低 = self.高, self.低
            for 内部中枢 in 线段内部中枢:
                内部中枢高, 内部中枢低 = 内部中枢.高, 内部中枢.低
                if 中枢状态 == "中枢之下":
                    if 低 <= 内部中枢高:
                        continue
                else:
                    # 中枢之上
                    if 高 >= 内部中枢低:
                        continue
                if 相对方向.分析(self.高, self.低, 内部中枢高, 内部中枢低).是否缺口():
                    return True
        return False

    def 获取序列(self) -> List[虚线]:
        """获取中枢的完整虚线序列（基础序列+第三买卖线）

        :return: 虚线列表
        """
        序列: List = self.基础序列[:]
        if self.第三买卖线 is not None:
            序列.append(self.第三买卖线)
        return 序列

    def 获取扩展中枢(self, 扩展中枢: List, 配置: 缠论配置):
        """当基础序列>=9时，从中枢中提取扩展线段中枢

        :param 扩展中枢: 存放扩展中枢的列表
        :param 配置: 缠论配置
        """
        if len(self.基础序列) >= 9:
            扩展线段 = []
            线段.扩展分析(self.基础序列, 扩展线段, 配置)
            中枢.分析(扩展线段, 扩展中枢, False, f"{self.标识}_扩展中枢_")

    def _校验合法性(self, 序列: Sequence[虚线]) -> bool:
        """校验当前中枢在给定序列中是否仍然合法

        :param 序列: 基础虚线序列
        :return: 合法为True，不合法会原地裁剪基础序列
        """
        有效序列 = self.基础序列[:]
        无效序列 = []
        序列集 = set(序列)
        for 元素 in self.基础序列:
            if 元素 not in 序列集:
                无效序列.append(元素)

        if 无效序列:
            无效 = 无效序列[0]
            序号 = 线段._索引(self.基础序列, 无效)
            有效序列 = self.基础序列[:序号]

        if len(有效序列) < 3:
            self.第三买卖线 = None
            self.本级_第三买卖线 = None
            return False

        self.基础序列[:] = 有效序列

        有效序列 = []
        for 元素 in self.基础序列:
            if 相对方向.分析(self.高, self.低, 元素.高, 元素.低).是否缺口():
                break
            有效序列.append(元素)
        self.基础序列[:] = 有效序列

        if len(self.基础序列) < 3:
            return False

        for i in range(1, len(self.基础序列)):
            前 = self.基础序列[i - 1]
            后 = self.基础序列[i]
            if not 前.之后是(后):
                return False

        if not 相对方向.分析(self.基础序列[0].高, self.基础序列[0].低, self.基础序列[2].高, self.基础序列[2].低).是否缺口():
            重叠高 = min(self.基础序列[:3], key=lambda o: o.高).高
            重叠低 = max(self.基础序列[:3], key=lambda o: o.低).低
            if 重叠低 > 重叠高:
                return False

        if self.第三买卖线 is not None:
            if self.第三买卖线 in 序列:
                if not self.基础序列[-1].之后是(self.第三买卖线):
                    self.设置第三买卖线(None)
                else:
                    if not 相对方向.分析(self.高, self.低, self.第三买卖线.高, self.第三买卖线.低).是否缺口():
                        self._添加虚线(self.第三买卖线)
                        self.设置第三买卖线(None)

            else:
                self.设置第三买卖线(None)
        return True

    def 设置第三买卖线(self, 线: Union[虚线, None]):
        """设置第三类买卖点关联虚线

        :param 线: 第三买卖虚线或None
        """
        self.第三买卖线 = 线

    def 当前状态(self):
        """获取中枢当前状态：中枢之中/中枢之上/中枢之下

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

        :return: "中枢之中" / "中枢之上" / "中枢之下"
        """
        状态 = "中枢之中"
        尾部 = 虚线.获取_武(self.基础序列[-1])
        关系 = 相对方向.分析(self.高, self.低, 尾部.中.高, 尾部.中.低)
        if 关系 is 相对方向.向上缺口:
            状态 = "中枢之上"
        elif 关系 is 相对方向.向下缺口:
            状态 = "中枢之下"
        return 状态

    @classmethod
    def 基础检查(cls, 左: 虚线, 中: 虚线, 右: 虚线) -> bool:
        """检查三条虚线是否构成中枢（连续且重叠）

        :param 左: 左侧虚线
        :param 中: 中间虚线
        :param 右: 右侧虚线
        :return: bool
        """
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
    def 创建(cls, 左: 虚线, 中: 虚线, 右: 虚线, 级别: int, 标识: str = "") -> 中枢:
        """从三条连续且重叠的虚线创建中枢

        :param 左: 左侧虚线
        :param 中: 中间虚线
        :param 右: 右侧虚线
        :param 级别: 中枢级别
        :param 标识: 中枢标识前缀
        :return: 中枢实例
        """
        assert 中枢.基础检查(左, 中, 右)
        return 中枢(
            序号=0,
            标识=f"{标识}中枢<{中.标识}>",
            基础序列=[左, 中, 右],
            级别=级别,
        )

    @classmethod
    def 从序列中获取中枢(cls, 虚线序列: Sequence[虚线], 起始方向: 相对方向, 标识: str) -> Optional[中枢]:
        """从虚线序列中按起始方向查找第一个中枢

        :param 虚线序列: 虚线列表
        :param 起始方向: 第一条虚线的方向
        :param 标识: 中枢标识前缀
        :return: 中枢或None
        """
        if len(虚线序列) < 3:
            return None

        for i in range(1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            if 中枢.基础检查(左, 中, 右):
                if 左.方向 is 起始方向:
                    return 中枢.创建(左, 中, 右, 级别=0, 标识=标识)

        return None

    @classmethod
    def _向中枢序列尾部添加(cls, 中枢序列: List[中枢], 待添加中枢: 中枢):
        """
        :param 中枢序列: 中枢列表
        :param 待添加中枢: 待添加的中枢
        """
        if 中枢序列:
            待添加中枢.序号 = 中枢序列[-1].序号 + 1
            if 中枢序列[-1].获取序列()[-1].序号 > 待添加中枢.获取序列()[-1].序号:
                raise ValueError()
        中枢序列.append(待添加中枢)

    @classmethod
    def _从中枢序列尾部弹出(cls, 中枢序列: List[中枢], 待弹出中枢: 中枢) -> Optional[中枢]:
        """
        :param 中枢序列: 中枢列表
        :param 待弹出中枢: 待弹出的中枢
        :return: 弹出的中枢或None
        """
        if not 中枢序列:
            return None
        if 中枢序列[-1] is 待弹出中枢:
            return 中枢序列.pop()
        return None

    @classmethod
    def 分析(cls, 虚线序列: Sequence[虚线], 中枢序列: List[中枢], 跳过首部: bool = True, 标识: str = "", 层级: int = 0) -> None:
        """中枢识别核心递归算法 — 从虚线序列递归生成中枢。

        :param 虚线序列: 基础虚线列表
        :param 中枢序列: 中枢列表（原地修改）
        :param 跳过首部: True 时跳过首元素中枢
        :param 标识: 中枢标识前缀
        :param 层级: 递归深度
        :return: None（结果写入中枢序列）
        """
        if len(虚线序列) < 3:
            return None

        中枢递归分析 = 中枢.分析

        if not 中枢序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                if 中枢.基础检查(左, 中, 右):
                    新中枢 = 中枢.创建(左, 中, 右, 中.级别, 标识)
                    序号 = 线段._索引(虚线序列, 左)
                    if 跳过首部 and (左.序号 == 0 or 序号 == 0):
                        continue  # 方便计算走势
                    if 序号 >= 2:
                        同向相对关系 = 相对方向.分析(虚线序列[序号 - 2].高, 虚线序列[序号 - 2].低, 左.高, 左.低)
                        if 同向相对关系.是否向上() and 左.方向.是否向上():
                            continue
                        if 同向相对关系.是否向下() and 左.方向.是否向下():
                            continue

                    中枢._向中枢序列尾部添加(中枢序列, 新中枢)
                    return 中枢递归分析(虚线序列, 中枢序列, 跳过首部, 标识, 层级 + 1)

            return None

        当前中枢 = 中枢序列[-1]

        if not 当前中枢._校验合法性(虚线序列):
            中枢._从中枢序列尾部弹出(中枢序列, 当前中枢)
            return 中枢递归分析(虚线序列, 中枢序列, 跳过首部, 标识, 层级 + 1)

        序号 = 线段._索引(虚线序列, 当前中枢.基础序列[-1]) + 1

        基础序列 = []
        for 当前虚线 in 虚线序列[序号:]:
            if 相对方向.分析(当前中枢.高, 当前中枢.低, 当前虚线.高, 当前虚线.低).是否缺口():
                基础序列.append(当前虚线)
                if 当前中枢.基础序列[-1].之后是(当前虚线):
                    当前中枢.设置第三买卖线(当前虚线)
                else:
                    ...
            else:
                if not 基础序列:
                    assert 当前中枢.基础序列[-1].之后是(当前虚线), (当前中枢.基础序列[-1], 当前虚线)
                    当前中枢._添加虚线(当前虚线)
                else:
                    基础序列.append(当前虚线)

            while len(基础序列) >= 3:
                新中枢 = 中枢.从序列中获取中枢(基础序列, 当前中枢.基础序列[-1].方向.翻转(), 标识)
                if 新中枢 is None:
                    基础序列.pop(0)
                else:
                    中枢._向中枢序列尾部添加(中枢序列, 新中枢)
                    当前中枢 = 新中枢
                    基础序列 = []
        return None


@注册
class 观察者:
    """单周期缠论分析器，接收K线流式输入并逐层计算所有层级序列。

    核心入口为 :meth:`增加原始K线`，每收到一根新K线就增量更新：
    原始K线 → 缠论K线（包含处理+合并）→ 分型 → 笔 → 线段 → 中枢 → 买卖点

    :ivar 标识: "{符号}:{周期}"
    :ivar 当前K线: 最后一根原始K线（只读）
    :ivar 当前缠K: 最后一根缠论K线（只读）
    :ivar 观察员: 自身引用（只读，便于内部回调）

    序列字段:
      :ivar 普通K线序列 / :ivar 缠论K线序列 / :ivar 分型序列
      :ivar 笔序列 / :ivar 线段序列 / :ivar 中枢序列
      :ivar 买卖点序列 / :ivar 扩展线段序列

    数据输入:
      :meth:`投喂原始数据` — 投喂原始OHLCV数据（自动创建K线）
      :meth:`增加原始K线` — 投入一根K线，触发全链路增量分析（主入口）

    控制:
      :meth:`重置基础序列` — 清空并重置所有基础序列
      :meth:`识别买卖点` — 基于中枢和分型扫描买卖点
      :meth:`静态重新分析` — 清空后根据已有中枢和买卖点重新分析

    持久化:
      :meth:`加载本地数据` — 从文件路径加载数据
      :meth:`读取数据文件` — 类方法，读取数据文件并返回观察者实例
    """

    def __init__(self, 符号: str, 周期: int, 配置: 缠论配置):
        """初始化观察者

        :param 符号: 交易对符号
        :param 周期: K线周期（秒）
        :param 配置: 缠论配置
        """
        配置.标识 = 符号
        self.符号: str = 符号
        self.周期: int = int(周期)
        self.配置: 缠论配置 = 配置
        self.__终止时间戳: Optional[datetime] = 转化为时间戳(self.配置.手动终止) if self.配置.手动终止 else None

        self.线段分析层次 = 3
        self.扩展线段分析层次 = 3
        self.混合扩展线段分析层次 = 3
        self.重置基础序列()

    def 重置基础序列(self):
        """清空所有分析序列，重置为初始状态"""
        self.基础缠K序列: List[缠论K线] = []

        self.普通K线序列: List[K线] = []
        self.缠论K线序列: List[缠论K线] = []

        self.分型序列: List[分型] = []

        self.笔序列: List[虚线] = []
        self.笔_中枢序列: List[中枢] = []

        self.线段序列组: List[List[虚线],] = []  # 线段, 线段<线段>，线段<线段<线段>>...
        self.中枢序列组: List[List[中枢],] = []
        for i in range(self.线段分析层次):
            self.线段序列组.append(list())
            self.中枢序列组.append(list())

        self.扩展线段序列组: List[List[虚线],] = []  # 扩展线段, 扩展线段<扩展线段>, 扩展线段<扩展线段<扩展线段>>...
        self.扩展中枢序列组: List[List[中枢],] = []
        for i in range(self.扩展线段分析层次):
            self.扩展线段序列组.append(list())
            self.扩展中枢序列组.append(list())

        self.混合扩展线段序列组: List[List[虚线],] = []  # 扩展线段<线段>, 扩展线段<线段<线段>>, 扩展线段<线段<线段<线段>>>...
        self.混合扩展中枢序列组: List[List[中枢],] = []
        for i in range(self.混合扩展线段分析层次):
            self.混合扩展线段序列组.append(list())
            self.混合扩展中枢序列组.append(list())

    @property
    def 观察员(self):
        """观察员（自引用）"""
        return self  # 用于兼容 chanlun.c99

    @property
    def 标识(self) -> str:
        """
        :return: "{符号}:{周期}"
        """
        return f"{self.符号}:{self.周期}"

    @property
    def 当前K线(self) -> Optional[K线]:
        """
        :return: 最后一根原始K线
        """
        return self.普通K线序列[-1] if self.普通K线序列 else None

    @property
    def 当前缠K(self) -> Optional[缠论K线]:
        """
        :return: 最后一根缠论K线
        """
        return self.缠论K线序列[-1] if self.缠论K线序列 else None

    @property
    def 线段序列(self) -> List[虚线]:
        return self.线段序列组[0]

    @property
    def 中枢序列(self) -> List[中枢]:
        return self.中枢序列组[0]

    @property
    def 扩展线段序列(self) -> List[虚线]:
        return self.扩展线段序列组[0]

    @property
    def 扩展中枢序列(self) -> List[中枢]:
        return self.扩展中枢序列组[0]

    @property
    def 扩展线段序列_线段(self) -> List[虚线]:
        return self.混合扩展线段序列组[0]

    @property
    def 扩展中枢序列_线段(self) -> List[中枢]:
        return self.混合扩展中枢序列组[0]

    @property
    def 线段_线段序列(self) -> List[虚线]:
        return self.线段序列组[1]

    @property
    def 线段_中枢序列(self) -> List[中枢]:
        return self.中枢序列组[1]

    @property
    def 扩展线段序列_扩展线段(self) -> List[虚线]:
        return self.扩展线段序列组[1]

    @property
    def 扩展中枢序列_扩展线段(self) -> List[中枢]:
        return self.扩展中枢序列组[1]

    def 投喂原始数据(self, 时间戳: datetime, 开: float, 高: float, 低: float, 收: float, 量: float):
        """便捷入口，直接从 OHLCV 创建 K线 并投喂
        :param 时间戳: 时间戳
        :param 开: 开盘价
        :param 高: 最高价
        :param 低: 最低价
        :param 收: 收盘价
        :param 量: 成交量
        """
        self.增加原始K线(K线.创建普K(self.符号, 时间戳, 开, 高, 低, 收, 量, 0, self.周期))

    @final
    def 增加原始K线(self, 普K: K线):
        """核心入口 — 投喂一根原始K线，增量更新所有层级

        :param 普K: 新到的原始K线

        处理流程: 原始K线→缠论K线（包含处理+合并）→分型→笔→线段→中枢→买卖点
        """
        if self.__终止时间戳 and 普K.时间戳 > self.__终止时间戳:
            return
        self.__处理数据(普K)

    def __处理数据(self, 普K: K线):
        状态, 当前分型 = 缠论K线.分析(普K, self.缠论K线序列, self.普通K线序列, self.配置)
        if 当前分型 is None:
            return

        self.配置.分析笔 and 笔.分析(当前分型, self.分型序列, self.笔序列, self.缠论K线序列, self.普通K线序列, 0, self.配置)
        if not self.分型序列:
            return

        self.配置.分析笔中枢 and 中枢.分析(self.笔序列, self.笔_中枢序列, True, "", 0)
        if not self.笔序列:
            return

        for i in range(self.线段分析层次):
            if i == 0:
                self.配置.分析线段 and 线段.分析(self.笔序列, self.线段序列组[i], self.配置)
                self.配置.分析线段中枢 and 中枢.分析(self.线段序列组[i], self.中枢序列组[i], True, "", 0)
                continue
            self.配置.分析线段 and 线段.分析(self.线段序列组[i - 1], self.线段序列组[i], self.配置)
            self.配置.分析线段中枢 and 中枢.分析(self.线段序列组[i], self.中枢序列组[i], True, "", 0)

        for i in range(self.扩展线段分析层次):
            if i == 0:
                self.配置.分析扩展线段 and 线段.扩展分析(self.笔序列, self.扩展线段序列组[i], self.配置)
                self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列组[i], self.扩展中枢序列组[i], True, "", 0)
                continue
            self.配置.分析扩展线段 and 线段.扩展分析(self.扩展线段序列组[i - 1], self.扩展线段序列组[i], self.配置)
            self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列组[i], self.扩展中枢序列组[i], True, "", 0)

        for i in range(min(self.混合扩展线段分析层次, len(self.线段序列组))):
            self.配置.分析扩展线段 and 线段.扩展分析(self.线段序列组[i], self.混合扩展线段序列组[i], self.配置)
            self.配置.分析线段中枢 and 中枢.分析(self.混合扩展线段序列组[i], self.混合扩展中枢序列组[i], True, "", 0)

    def 测试_保存数据(self, root: str = None) -> str:
        """拆分各序列数据，单独存文件，文件名为对应变量名

        :param root: 保存根目录（可选）
        :return: 保存目录
        """

        if root is not None:
            # 使用用户指定的根目录
            根目录 = Path(root)
        else:
            # 默认：系统临时目录
            根目录 = tempfile.gettempdir()

        # 生成子目录名称
        起始时间 = int(self.普通K线序列[0].时间戳.timestamp())
        结束时间 = int(self.普通K线序列[-1].时间戳.timestamp())
        目录标识 = f"Py_{self.标识}_{起始时间}_{结束时间}"

        # 最终保存路径 = 根目录 / 自动生成的子文件夹
        保存路径 = 根目录 / 目录标识
        保存路径.mkdir(exist_ok=True, parents=True)  # parents=True 支持多级目录自动创建

        def 保存序列(序列):
            if len(序列) == 0:
                return
            数据列表 = [对象.获取数据文本() for 对象 in 序列]
            文件名 = 序列[0].标识
            文件全路径 = 保存路径 / f"{文件名}.txt"
            # 逐个写入独立文件
            with open(文件全路径, "w", encoding="utf-8") as f:
                f.write("\n".join(数据列表))
                f.write("\n")  # 向 C99 对齐

        保存序列(self.笔序列)
        保存序列(self.笔_中枢序列)
        for i in range(self.线段分析层次):
            保存序列(self.线段序列组[i])
            保存序列(self.中枢序列组[i])
        for i in range(self.扩展线段分析层次):
            保存序列(self.扩展线段序列组[i])
            保存序列(self.扩展中枢序列组[i])
        for i in range(self.混合扩展线段分析层次):
            保存序列(self.混合扩展线段序列组[i])
            保存序列(self.混合扩展中枢序列组[i])

        logger.warning(f"全部数据拆分保存完成，目录：{保存路径.resolve()}")
        return str(保存路径.resolve())

    def 识别买卖点(self):
        """识别买卖点（占位方法，具体逻辑在子类或Rust核心中实现）"""
        pass

    def 静态重新分析(self):
        """静态重新分析"""
        self.分型序列: List[分型] = []

        self.笔序列: List[虚线] = []
        self.笔_中枢序列: List[中枢] = []

        self.线段序列组: List[List[虚线],] = []  # 线段, 线段<线段>，线段<线段<线段>>...
        self.中枢序列组: List[List[中枢],] = []
        for i in range(self.线段分析层次):
            self.线段序列组.append(list())
            self.中枢序列组.append(list())

        self.扩展线段序列组: List[List[虚线],] = []  # 扩展线段, 扩展线段<扩展线段>, 扩展线段<扩展线段<扩展线段>>...
        self.扩展中枢序列组: List[List[中枢],] = []
        for i in range(self.扩展线段分析层次):
            self.扩展线段序列组.append(list())
            self.扩展中枢序列组.append(list())

        self.混合扩展线段序列组: List[List[虚线],] = []  # 扩展线段<线段>, 扩展线段<线段<线段>>, 扩展线段<线段<线段<线段>>>...
        self.混合扩展中枢序列组: List[List[中枢],] = []
        for i in range(self.混合扩展线段分析层次):
            self.混合扩展线段序列组.append(list())
            self.混合扩展中枢序列组.append(list())

        for i in range(1, len(self.缠论K线序列) - 1):
            当前分型 = 分型(self.缠论K线序列[i - 1], self.缠论K线序列[i], self.缠论K线序列[i + 1])
            self.配置.分析笔 and 笔.分析(当前分型, self.分型序列, self.笔序列, self.缠论K线序列, self.普通K线序列, 0, self.配置)

        if not self.笔序列:
            return
        self.配置.分析笔中枢 and 中枢.分析(self.笔序列, self.笔_中枢序列, True, "", 0)

        for i in range(self.线段分析层次):
            if i == 0:
                self.配置.分析线段 and 线段.分析(self.笔序列, self.线段序列组[i], self.配置)
                self.配置.分析线段中枢 and 中枢.分析(self.线段序列组[i], self.中枢序列组[i], True, "", 0)
                continue
            self.配置.分析线段 and 线段.分析(self.线段序列组[i - 1], self.线段序列组[i], self.配置)
            self.配置.分析线段中枢 and 中枢.分析(self.线段序列组[i], self.中枢序列组[i], True, "", 0)

        for i in range(self.扩展线段分析层次):
            if i == 0:
                self.配置.分析扩展线段 and 线段.扩展分析(self.笔序列, self.扩展线段序列组[i], self.配置)
                self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列组[i], self.扩展中枢序列组[i], True, "", 0)
                continue
            self.配置.分析扩展线段 and 线段.扩展分析(self.扩展线段序列组[i - 1], self.扩展线段序列组[i], self.配置)
            self.配置.分析线段中枢 and 中枢.分析(self.扩展线段序列组[i], self.扩展中枢序列组[i], True, "", 0)

        for i in range(min(self.混合扩展线段分析层次, len(self.线段序列组))):
            self.配置.分析扩展线段 and 线段.扩展分析(self.线段序列组[i], self.混合扩展线段序列组[i], self.配置)
            self.配置.分析线段中枢 and 中枢.分析(self.混合扩展线段序列组[i], self.混合扩展中枢序列组[i], True, "", 0)

    def 加载本地数据(self, 文件路径: str):
        """重置基础序列后加载数据文件
        :param 文件路径: 数据文件路径 格式如: btcusd-300-1631772074-1632222374.nb
        """
        self.重置基础序列()
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量 = struct.unpack(">6d", buffer[i * size : i * size + size])
                self.投喂原始数据(转化为时间戳(int(时间戳)), 开盘价, 最高价, 最低价, 收盘价, 成交量)

    @classmethod
    def 读取数据文件(cls, 文件路径: str, 配置=缠论配置(), *, 观察员: Optional[观察者] = None) -> Self:
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
            logger.info(f"加载异常配置+传入差异: {传入差异}")

        name = Path(文件路径).name.split(".")[0]
        符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
        if 观察员 is None:
            观察员 = cls(符号, int(周期), 配置)
        else:
            观察员.符号 = 符号
            观察员.周期 = int(周期)
            观察员.配置 = 配置
        观察员.加载本地数据(文件路径)
        return 观察员


class K线合成器:
    """将小周期K线合成为大周期K线，支持多周期级联合成。

    :ivar 标识: 合成器标识
    :ivar 周期组: 从小到大排列的周期组
    :ivar 当前K线: 各周期当前K线
    :ivar 合成K线列表: 各周期已合成的K线列表

    数据输入:
      :meth:`投喂` — 投喂原始OHLCV数据
      :meth:`投喂K线` — 投喂原始K线，触发多周期合成（主入口）

    事件:
      :meth:`设置事件回调` — 设置K线合成完成时的回调函数

    查询:
      :meth:`获取当前K线` — 获取指定周期的当前K线
    """

    def __init__(self, 标识: str, 周期组: List[int], 事件回调: Optional[Callable] = None):
        """初始化K线合成器

        :param 标识: 合成器标识
        :param 周期组: 从小到大排列的周期列表
        :param 事件回调: 可选，K线合成完成时的回调函数(信号类型, 标识, 周期, 完成K线)
        """
        self.标识 = 标识
        self.周期组 = sorted(周期组)  # 按周期从小到大排序
        self.当前K线: Dict[int, Optional[K线]] = {周期: None for 周期 in 周期组}
        self.合成K线列表: Dict[int, List[K线]] = {周期: [] for 周期 in 周期组}
        self.事件回调 = 事件回调  # 新增：事件回调函数

    def 设置事件回调(self, 回调函数: Callable):
        """设置事件回调函数

        :param 回调函数: 回调函数
        """
        self.事件回调 = 回调函数

    def 投喂(self, 时间戳: datetime, 开: float, 高: float, 低: float, 收: float, 量: float):
        """投喂原始tick数据

        :param 时间戳: 时间戳
        :param 开: 开盘价
        :param 高: 最高价
        :param 低: 最低价
        :param 收: 收盘价
        :param 量: 成交量
        """
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
        """统一入口 — 投喂最小周期K线，自动合成大周期并分发给各周期观察者

        :param 普K: 最小周期原始K线
        """
        for 周期 in self.周期组:
            self._处理单个周期(周期, 普K)

    def _处理单个周期(self, 周期: int, 普K: K线):
        """处理单个周期的K线合成

        :param 周期: 目标周期
        :param 普K: 原始K线
        """
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
        """将时间戳对齐到周期边界

        :param 时间戳: 原始时间戳
        :param 周期: 周期（秒）
        :return: 对齐后的时间戳
        """
        total_seconds = int(时间戳.timestamp())
        aligned_seconds = (total_seconds // 周期) * 周期
        return datetime.fromtimestamp(aligned_seconds)

    def _创建新K线(self, 周期: int, 时间戳: datetime, 普K: K线) -> K线:
        """创建新的合成K线

        :param 周期: 目标周期
        :param 时间戳: 对齐后的时间戳
        :param 普K: 原始K线
        :return: 新合成K线
        """
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
        """更新当前K线数据

        :param 当前K线: 当前K线对象
        :param 新数据: 新到来的K线
        """
        当前K线.高 = max(当前K线.高, 新数据.高)
        当前K线.低 = min(当前K线.低, 新数据.低)
        当前K线.收盘价 = 新数据.收盘价
        当前K线.成交量 += 新数据.成交量
        # 当前K线.原始结束序号 = 新数据.序号

    def _完成K线(self, 周期: int):
        """完成当前K线并添加到列表

        :param 周期: 目标周期
        """
        当前K线 = self.当前K线[周期]
        if 当前K线 is None:
            return

        # 这里可以添加最终的处理逻辑，比如计算MACD等
        if self.合成K线列表[周期]:
            当前K线.序号 = self.合成K线列表[周期][-1].序号 + 1

        self.合成K线列表[周期].append(当前K线)

        self.当前K线[周期] = None
        # 新增：产生完成K线信号
        self._产生完成K线信号(周期, 当前K线)

    def _产生完成K线信号(self, 周期: int, 完成K线: K线):
        """产生K线完成信号

        :param 周期: 周期
        :param 完成K线: 完成的K线对象
        """
        if self.事件回调:
            try:
                self.事件回调(信号类型="K线完成", 标识=self.标识, 周期=周期, 完成K线=完成K线)
            except Exception as e:
                logger.warning(f"K线合成器信号回调错误: {e}")

    def 获取当前K线(self, 周期: int) -> Optional[K线]:
        """获取指定周期当前正在合成的K线

        :param 周期: 目标周期
        :return: 当前K线或None
        """
        return self.当前K线[周期]


@注册
class 立体分析器:
    """多周期缠论分析器，内部包含 :class:`K线合成器` + 每周期一个 :class:`观察者`。

    通过最小周期合成大周期K线，各周期观察者独立分析，实现多周期联立。

    :ivar 周期组: 所有分析周期
    :ivar 观察员: 各周期对应的观察者
    :ivar K线合成器: 内部K线合成器

    数据输入:
      :meth:`投喂K线` — 投入最小周期K线，自动合成大周期并驱动各周期分析（主入口）
    """

    def __init__(self, 符号: str, 周期组: List[int], 配置: 缠论配置 = 缠论配置(), 配置组: Dict[int, 缠论配置] = dict()):
        """初始化多周期立体分析器

        :param 符号: 交易对符号
        :param 周期组: 所有分析周期列表（第一个为最小输入周期）
        :param 配置: 默认配置
        :param 配置组: 各周期独立配置 {周期: 缠论配置}
        """
        self.周期组 = 周期组

        self.__输入周期 = self.周期组[0]  # 最小输入K线周期
        self.__显示周期 = self.周期组[1]
        self._K线合成器 = K线合成器(符号, self.周期组, self.__K线回调)

        self._单体分析器 = dict()
        for 周期 in self.周期组:
            临时配置 = 配置组.get(周期, 配置)
            当前配置 = 临时配置.model_copy(
                update={"图表展示标签": []},
                deep=True,
            )
            self._单体分析器[周期] = 观察者(符号=符号, 周期=周期, 配置=当前配置)

        self._单体分析器[self.__显示周期].配置.图表展示 = True
        self._单体分析器[self.__显示周期].配置.图表展示标签 = None  # None = 全部展示
        self._单体分析器[self.__显示周期].重置基础序列()

        for 周期 in self.周期组:  # 将不同周期对其至显示周期
            if 周期 != self.__显示周期:
                self._单体分析器[周期].基础缠K序列 = self._单体分析器[self.__显示周期].缠论K线序列

    def 投喂K线(self, 普K: K线):
        """统一入口 — 投喂最小周期K线，自动合成大周期并分发给各周期观察者

        :param 普K: 最小周期原始K线
        :raises RuntimeError: 当投喂的K线周期与输入周期不匹配时
        """
        if 普K.周期 != self.__输入周期:
            raise RuntimeError("立体分析器.投喂K线", 普K.周期, self.__输入周期)
        self._K线合成器.投喂K线(普K)

    def __K线回调(self, 信号类型: str, 标识: str, 周期: int, 完成K线: K线):
        """内部回调：K线完成时触发

        :param 信号类型: 信号类型
        :param 标识: 标识
        :param 周期: 周期
        :param 完成K线: 完成的K线对象
        """
        self._单体分析器[周期].增加原始K线(完成K线)
        if 当前K线 := self._K线合成器.获取当前K线(周期):
            self._单体分析器[周期].增加原始K线(当前K线)

    def 测试_保存数据(self, root: str = None):
        """拆分各序列数据，单独存文件。

        :param root: 保存根目录，默认系统临时目录
        :return: 数据保存目录路径
        """
        # 生成存储根目录
        脚本目录 = tempfile.gettempdir() if not root else root  # 默认系统临时目录
        起始时间 = int(self._单体分析器[self.__输入周期].普通K线序列[0].时间戳.timestamp())
        结束时间 = int(self._单体分析器[self.__输入周期].普通K线序列[-1].时间戳.timestamp())
        目录标识 = f"PyM_{self._单体分析器[self.__输入周期].标识}_{起始时间}_{结束时间}"

        # 最终保存路径 = 脚本目录 / 自动生成的文件夹
        保存路径 = Path(os.path.join(脚本目录, 目录标识))
        保存路径.mkdir(exist_ok=True)

        for 周期 in self.周期组:
            self._单体分析器[周期].测试_保存数据(保存路径)

        logger.warning(f"多级别数据拆分保存完成，目录：{保存路径.resolve()}")


# ═══════════════════════════════════════════════════════════════════════════════
# 以下信号匹配框架（import_by_name, Signal, Factor, Event, SignalsParser,
# Position 等类）摘录自 czsc 项目（https://github.com/zengbin93/czsc），
# Apache License 2.0 授权。 详见本文件头部 第三方代码声明。
# ═══════════════════════════════════════════════════════════════════════════════


def import_by_name(name: str):
    """通过字符串导入模块、类、函数

    函数执行逻辑：

    1. 检查 name 中是否包含点号（'.'）。如果没有，则直接使用内置的 import 函数来导入整个模块，并返回该模块对象。
    2. 如果 name 包含点号，先处理一个相对路径。将 name 拆分为两部分：module_name 和 function_name。
        使用 Python 内置的 rsplit 方法从右边开始分割，只取一次，这样可以确保我们将最后的一个点号前的部分作为 module_name，点号后面的部分作为 function_name。
    3. 使用import函数导入指定的 module_name。
        这里传入三个参数：globals() 和 locals() 分别代表当前全局和局部命名空间；
        [function_name] 是一个列表，用于指定要导入的子模块或属性名。
        这样做是为了避免一次性导入整个模块的所有内容，提高效率。
    4.  使用 vars 函数获取模块的字典表示形式（即模块内所有的变量和函数），取出 function_name 对应的值，然后返回这个值。

    :param name: 模块名，如：'czsc.objects.Factor'
    :return: 模块对象
    """
    if "." not in name:
        return __import__(name)

    # 从右边开始分割，分割成模块名和函数名
    module_name, function_name = name.rsplit(".", 1)
    module = __import__(module_name, globals(), locals(), [function_name])
    注入依赖(module)

    return vars(module)[function_name]


class Operate(Enum):
    # 持有状态
    HL = "持多"  # Hold Long
    HS = "持空"  # Hold Short
    HO = "持币"  # Hold Other

    # 多头操作
    LO = "开多"  # Long Open
    LE = "平多"  # Long Exit

    # 空头操作
    SO = "开空"  # Short Open
    SE = "平空"  # Short Exit

    def __str__(self):
        return self.value


@dataclass
class Signal:
    signal: str = ""

    # score 取值在 0~100 之间，得分越高，信号越强
    score: int = 0

    # k1, k2, k3 是信号名称
    k1: str = "任意"  # k1 一般是指明信号计算的K线周期，如 60分钟，日线，周线等
    k2: str = "任意"  # k2 一般是记录信号计算的参数
    k3: str = "任意"  # k3 用于区分信号，必须具有唯一性，推荐使用信号分类和开发日期进行标记

    # v1, v2, v3 是信号取值
    v1: str = "任意"
    v2: str = "任意"
    v3: str = "任意"

    # 任意 出现在模板信号中可以指代任何值

    def __post_init__(self):
        if not self.signal:
            self.signal = f"{self.k1}_{self.k2}_{self.k3}_{self.v1}_{self.v2}_{self.v3}_{self.score}"
        else:
            if not isinstance(self.signal, str):
                raise TypeError(f"Signal 初始化需要字符串，收到了 {type(self.signal).__name__}: {self.signal!r}")
            (
                self.k1,
                self.k2,
                self.k3,
                self.v1,
                self.v2,
                self.v3,
                score,
            ) = self.signal.split("_")
            self.score = int(score)

        if self.score > 100 or self.score < 0:
            raise ValueError("score 必须在0~100之间")

    def __repr__(self):
        return f"Signal('{self.signal}')"

    @property
    def key(self) -> str:
        """获取信号名称"""
        key = ""
        for k in [self.k1, self.k2, self.k3]:
            if k != "任意":
                key += k + "_"
        return key.strip("_")

    @property
    def value(self) -> str:
        """获取信号值"""
        return f"{self.v1}_{self.v2}_{self.v3}_{self.score}"

    def is_match(self, s: dict) -> bool:
        """判断信号是否与信号列表中的值匹配

        代码的执行逻辑如下：

        接收一个字典 s 作为参数，该字典包含了所有信号的信息。从字典 s 中获取名称为 key 的信号的值 v。
        如果 v 不存在，则抛出异常。从信号的值 v 中解析出 v1、v2、v3 和 score 四个变量。

        如果当前信号的得分 score 大于等于目标信号的得分 self.score，则继续执行，否则返回 False。
        如果当前信号的第一个值 v1 等于目标信号的第一个值 self.v1 或者目标信号的第一个值为 "任意"，则继续执行，否则返回 False。
        如果当前信号的第二个值 v2 等于目标信号的第二个值 self.v2 或者目标信号的第二个值为 "任意"，则继续执行，否则返回 False。
        如果当前信号的第三个值 v3 等于目标信号的第三个值 self.v3 或者目标信号的第三个值为 "任意"，则返回 True，否则返回 False。

        :param s: 所有信号字典
        :return: bool
        """
        key = self.key
        v = s.get(key, None)
        if not v:
            raise ValueError(f"{key} 不在信号列表中")

        if not isinstance(v, str):
            logger.warning(f"信号 {key} 的值类型异常: {type(v).__name__} = {v!r}，跳过匹配")
            return False

        v1, v2, v3, score = v.split("_")
        if int(score) >= self.score:
            if v1 == self.v1 or self.v1 == "任意":
                if v2 == self.v2 or self.v2 == "任意":
                    if v3 == self.v3 or self.v3 == "任意":
                        return True
        return False


@dataclass
class Factor:
    # signals_all 必须全部满足的信号，至少需要设定一个信号
    signals_all: List[Signal]

    # signals_any 满足其中任一信号，允许为空
    signals_any: List[Signal] = field(default_factory=list)

    # signals_not 不能满足其中任一信号，允许为空
    signals_not: List[Signal] = field(default_factory=list)

    name: str = ""

    def __post_init__(self):
        if not self.signals_all:
            raise ValueError("signals_all 不能为空")
        _fatcor = self.dump()
        _fatcor.pop("name")
        sha256 = hashlib.sha256(str(_fatcor).encode("utf-8")).hexdigest().upper()[:4]

        if self.name:
            self.name = self.name.split("#")[0] + f"#{sha256}"
        else:
            self.name = f"#{sha256}"
        # self.name = f"{self.name}#{sha256}" if self.name else sha256

    @property
    def unique_signals(self) -> List[str]:
        """获取 Factor 的唯一信号列表"""
        signals = []
        signals.extend(self.signals_all)
        if self.signals_any:
            signals.extend(self.signals_any)
        if self.signals_not:
            signals.extend(self.signals_not)
        signals = {x.signal if isinstance(x, Signal) else x for x in signals}
        return list(signals)

    def is_match(self, s: dict) -> bool:
        """判断 factor 是否满足"""
        if self.signals_not:
            for signal in self.signals_not:
                if signal.is_match(s):
                    return False

        for signal in self.signals_all:
            if not signal.is_match(s):
                return False

        if not self.signals_any:
            return True

        for signal in self.signals_any:
            if signal.is_match(s):
                return True
        return False

    def dump(self) -> dict:
        """将 Factor 对象转存为 dict"""
        signals_all = [x.signal for x in self.signals_all]
        signals_any = [x.signal for x in self.signals_any] if self.signals_any else []
        signals_not = [x.signal for x in self.signals_not] if self.signals_not else []

        raw = {
            "name": self.name,
            "signals_all": signals_all,
            "signals_any": signals_any,
            "signals_not": signals_not,
        }
        return raw

    @classmethod
    def load(cls, raw: dict):
        """从 dict 中创建 Factor

        :param raw: 样例如下
            {'name': '单测',
            'signals_all': ['15分钟_倒0笔_方向_向上_其他_其他_0', '15分钟_倒0笔_长度_大于5_其他_其他_0'],
            'signals_any': [],
            'signals_not': []}

        :return:
        """
        signals_any = [Signal(x) for x in raw.get("signals_any", [])]
        signals_not = [Signal(x) for x in raw.get("signals_not", [])]

        fa = Factor(
            name=raw.get("name", ""),
            signals_all=[Signal(x) for x in raw["signals_all"]],
            signals_any=signals_any,
            signals_not=signals_not,
        )
        return fa


@dataclass
class Event:
    operate: Operate

    # 多个信号组成一个因子，多个因子组成一个事件。
    # 单个事件是一系列同类型因子的集合，事件中的任一因子满足，则事件为真。
    factors: List[Factor]

    # signals_all 必须全部满足的信号，允许为空
    signals_all: List[Signal] = field(default_factory=list)

    # signals_any 满足其中任一信号，允许为空
    signals_any: List[Signal] = field(default_factory=list)

    # signals_not 不能满足其中任一信号，允许为空
    signals_not: List[Signal] = field(default_factory=list)

    name: str = ""

    def __post_init__(self):
        if not self.factors:
            raise ValueError("factors 不能为空")
        _event = self.dump()
        _event.pop("name")

        sha256 = hashlib.sha256(str(_event).encode("utf-8")).hexdigest().upper()[:4]
        if self.name:
            self.name = self.name.split("#")[0] + f"#{sha256}"
            # self.name = f"{self.name}#{sha256}"
        else:
            self.name = f"{self.operate.value}#{sha256}"
        self.sha256 = sha256

    @property
    def unique_signals(self) -> List[str]:
        """获取 Event 的唯一信号列表"""
        signals = []
        if self.signals_all:
            signals.extend(self.signals_all)
        if self.signals_any:
            signals.extend(self.signals_any)
        if self.signals_not:
            signals.extend(self.signals_not)

        for factor in self.factors:
            signals.extend(factor.unique_signals)

        signals = {x.signal if isinstance(x, Signal) else x for x in signals}
        return list(signals)

    def get_signals_config(self, signals_module: str = "chanlun.signals") -> List[Dict]:
        """获取事件的信号配置"""

        return get_signals_config(self.unique_signals, signals_module)

    def is_match(self, s: dict):
        """判断 event 是否满足

        代码的执行逻辑如下：

        1. 首先判断 signals_not 中的信号是否得到满足，如果满足任意一个信号，则直接返回 False，表示事件不满足。
        2. 接着判断 signals_all 中的信号是否全部得到满足，如果有任意一个信号不满足，则直接返回 False，表示事件不满足。
        3. 然后判断 signals_any 中的信号是否有一个得到满足，如果一个都不满足，则直接返回 False，表示事件不满足。
        4. 最后判断因子是否满足，顺序遍历因子列表，找到第一个满足的因子就退出，并返回 True 和该因子的名称，表示事件满足。
        5. 如果遍历完所有因子都没有找到满足的因子，则返回 False，表示事件不满足。
        """
        if self.signals_not and any(signal.is_match(s) for signal in self.signals_not):
            return False, None

        if self.signals_all and not all(signal.is_match(s) for signal in self.signals_all):
            return False, None

        if self.signals_any and not any(signal.is_match(s) for signal in self.signals_any):
            return False, None

        for factor in self.factors:
            if factor.is_match(s):
                return True, factor.name

        return False, None

    def dump(self) -> dict:
        """将 Event 对象转存为 dict"""
        signals_all = [x.signal for x in self.signals_all] if self.signals_all else []
        signals_any = [x.signal for x in self.signals_any] if self.signals_any else []
        signals_not = [x.signal for x in self.signals_not] if self.signals_not else []
        factors = [x.dump() for x in self.factors]

        raw = {
            "name": self.name,
            "operate": self.operate.value,
            "signals_all": signals_all,
            "signals_any": signals_any,
            "signals_not": signals_not,
            "factors": factors,
        }
        return raw

    @classmethod
    def load(cls, raw: dict):
        """从 dict 中创建 Event

        :param raw: 样例如下
                        {'name': '单测',
                         'operate': '开多',
                         'factors': [{'name': '测试',
                             'signals_all': ['15分钟_倒0笔_长度_大于5_其他_其他_0'],
                             'signals_any': [],
                             'signals_not': []}],
                         'signals_all': ['15分钟_倒0笔_方向_向上_其他_其他_0'],
                         'signals_any': [],
                         'signals_not': []}
        :return:
        """
        # 检查输入参数是否合法
        assert raw["operate"] in Operate.__dict__["_value2member_map_"], f"operate {raw['operate']} not in Operate"
        assert raw["factors"], "factors can not be empty"

        e = Event(
            name=raw.get("name", ""),
            operate=Operate.__dict__["_value2member_map_"][raw["operate"]],
            factors=[Factor.load(x) for x in raw["factors"]],
            signals_all=[Signal(x) for x in raw.get("signals_all", [])],
            signals_any=[Signal(x) for x in raw.get("signals_any", [])],
            signals_not=[Signal(x) for x in raw.get("signals_not", [])],
        )
        return e


class SignalsParser:
    """解析一串信号，生成信号函数配置"""

    def __init__(self, signals_module: str = "chanlun.signals"):
        """

        函数执行逻辑：

        1. 将传入的 signals_module 参数赋给实例变量 self.signals_module，代表信号函数所在的模块，默认模块是czsc库的signals模块。
        2. 使用 import_by_name 函数导入了指定名称的模块 signals_module。
        3. 对于导入的模块中的每个属性名进行遍历：
            - 魔法函数和私有函数不进行处理。
            - 获取函数的注解信息，并通过正则表达式获取注解中的参数模板和信号列表。
            - 如果解析到了参数模板，则将其存储在 sig_pats_map 中，key是函数名称。
            - 如果解析到了信号列表，则将其存储在 sig_name_map 中，并且为每个信号创建了 Signal 对象并存储在列表中，key是函数名称。
        4. 最后将得到的 sig_name_map 和 sig_pats_map 存储在实例变量中，以便其他方法使用。

        :param signals_module: 指定信号函数所在模块
        """
        self.signals_module = signals_module
        sig_name_map = {}
        sig_pats_map = {}
        sig_trigger_map = {}

        signals_module = import_by_name(signals_module)
        for name in dir(signals_module):
            if "_" not in name or name.startswith("__"):
                continue

            try:
                doc = getattr(signals_module, name).__doc__
                # 解析信号函数参数
                pats = re.findall(r"参数模板：\"(.*)\"", doc)
                if pats:
                    sig_pats_map[name] = pats[0]

                # 解析信号列表
                sigs = re.findall(r"Signal\('(.*)'\)", doc)
                if sigs:
                    sig_name_map[name] = [Signal(x) for x in sigs]

                # 解析触发条件
                触发匹配 = re.findall(r"触发条件：(.*)", doc)
                if 触发匹配:
                    sig_trigger_map[name] = [x.strip() for x in 触发匹配[0].split(",")]

            except (OSError, ImportError, TypeError, ValueError, AttributeError) as e:
                logger.error(f"解析信号函数 {name} 出错：{e}")

        self.sig_name_map = sig_name_map
        self.sig_pats_map = sig_pats_map
        self.sig_trigger_map = sig_trigger_map

    def parse_params(self, name, signal):
        """获取信号函数参数

        函数执行逻辑：

        1. 首先根据传入的 name 和 signal 参数，通过 Signal(signal).key 获取一个键值。
        2. 然后从实例变量 sig_pats_map 中获取与指定名称对应的参数模板，并将其存储在 pats 中。
        3. 如果没有找到参数模板，则返回 None。
        4. 最后将信号函数的完整名称存储在参数字典中，并返回参数字典。

        :param name: 信号函数名称, 如：cxt_bi_end_V230222
        :param signal: 需要解析的信号, 如：15分钟_D1K_量柱V221218_低量柱_6K_任意_0
        :return:
        """
        key = Signal(signal).key
        pats = self.sig_pats_map.get(name, None)
        if not pats:
            return None

        try:
            params = parse(pats, key).named  # type: ignore
            if "di" in params:
                params["di"] = int(params["di"])

            params["name"] = f"{self.signals_module}.{name}"

            # 附加上下文：触发条件与函数短名（供 信号计算器 优化用）
            触发条件 = self.sig_trigger_map.get(name)
            if 触发条件:
                params["触发条件"] = 触发条件
            params["_func_short_name"] = name

            return params
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            logger.error(f"解析信号 {signal} - {name} - {pats} 出错：{e}")
            return None

    def get_function_name(self, signal: str):
        """获取信号对应的信号函数名称

        函数执行逻辑：

        1. 创建一个 _signal 对象，通过传入的信号字符串进行初始化。
        2. 通过遍历 sig_name_map 中的项目，找出那些与 _signal.k3 相匹配的键，并将它们存储在 _k3_match 列表中。
        3. 如果只有一个匹配项，则返回该项；否则记录错误日志并返回 None。

        :param signal: 信号，数据样例：15分钟_D1K_量柱V221218_低量柱_6K_任意_0
        :return: 信号函数名称
        """
        sig_name_map = self.sig_name_map
        _signal = Signal(signal)
        _k3_match = list({k for k, v in sig_name_map.items() if v[0].k3 == _signal.k3})

        # 多匹配时排除模板函数（以 "模板_" 开头）
        if len(_k3_match) > 1:
            non_template = [k for k in _k3_match if not k.startswith("模板_")]
            if len(non_template) == 1:
                return non_template[0]

        if len(_k3_match) == 1:
            return _k3_match[0]
        else:
            logger.error(f"信号 {signal} 有多个匹配函数：{_k3_match}，请手动解析信号")
            return None

    def config_to_keys(self, config: List[Dict]):
        """将信号函数配置转换为信号key列表

        函数执行逻辑：

        1. 首先创建了一个空列表 keys 用于存储信号key。
        2. 对于传入的 config 列表中的每个配置字典 conf 进行以下操作：
            - 获取信号函数的名称。
            - 如果该信号函数的名称在 self.sig_pats_map 中存在对应的模板，使用参数填充模板，并将结果添加到 keys 列表中。

        :param config: 信号函数配置

            config = [{'freq': '日线', 'max_overlap': '3', 'name': 'czsc.signals.cxt_bi_end_V230222'},
                     {'freq1': '日线', 'freq2': '60分钟', 'name': 'czsc.signals.cxt_zhong_shu_gong_zhen_V221221'}]

        :return: 信号key列表
        """
        keys = []
        for conf in config:
            name = conf["name"].split(".")[-1]
            if name in self.sig_pats_map:
                keys.append(self.sig_pats_map[name].format(**conf))
        return keys

    def parse(self, signal_seq: List[str]):
        """解析信号序列

        函数执行逻辑：

        1. 接受一个signal_seq 参数。
        2. 定义一个空列表res ，用于存储解析结果。
        3. 遍历信号序列signal_seq 中的每一个信号：

            - 调用get_function_name 方法，以信号为参数，获取该信号对应的函数名。
            - 进行函数名存在性判断，name 在sig_pats_map 中存在，
              调用parse_params 方法，以函数名和信号为参数，解析参数并返回结果。

        :param signal_seq: 信号序列, 样例：
            ['15分钟_D1K_量柱V221218_低量柱_6K_任意_0', '日线_D1K_量柱V221218_低量柱_6K_任意_0']
        :return: 信号函数配置
        """
        res = []
        for signal in signal_seq:
            name = self.get_function_name(signal)
            if name in self.sig_pats_map:
                row = self.parse_params(name, signal)
                if row and row not in res:
                    res.append(row)
            else:
                logger.warning(f"未找到解析函数：{name}，请手动解析信号：{signal}")
        return res


def get_signals_config(signals_seq: List[str], signals_module: str = "") -> List[Dict]:
    """获取信号列表对应的信号函数配置

    函数执行逻辑：

    1. 首先创建了一个 SignalsParser 类的实例对象 sp，传入了参数 signals_module进行初始化，
        初始化工作主要是解析signals_module下的信号函数，生成了sig_pats_map信号参数模板字典和sig_name_map信号列表字典。
    2. 然后使用 sp 实例调用 parse 方法，该方法解析 signals_seq 中的信号，并返回信号函数的配置信息。

    :param signals_seq: 信号列表
    :param signals_module: 信号函数所在模块
    :return: 信号函数配置
    """
    sp = SignalsParser(signals_module=signals_module)
    conf = sp.parse(signals_seq)
    return conf


@注册
def create_single_signal(**kwargs) -> OrderedDict:
    """创建单个信号"""
    s = OrderedDict()
    k1, k2, k3 = kwargs.get("k1", "任意"), kwargs.get("k2", "任意"), kwargs.get("k3", "任意")
    v1, v2, v3 = kwargs.get("v1", "任意"), kwargs.get("v2", "任意"), kwargs.get("v3", "任意")
    v = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=kwargs.get("score", 0))
    s[v.key] = v.value
    return s


# ==============================================================================
# Position — 持仓管理
# ==============================================================================


class Position:
    def __init__(
        self,
        symbol: str,
        opens: List[Event],
        exits: List[Event] = [],
        interval: int = 0,
        timeout: int = 1000,
        stop_loss=1000,
        T0: bool = False,
        name=None,
    ):
        """简单持仓对象，仓位表达：1 持有多头，-1 持有空头，0 空仓

        :param symbol: 标的代码
        :param opens: 开仓交易事件列表
        :param exits: 平仓交易事件列表，允许为空
        :param interval: 同类型开仓间隔时间，单位：秒；默认值为 0，表示同类型开仓间隔没有约束
                假设上次开仓为多头，那么下一次多头开仓时间必须大于 上次开仓时间 + interval；空头也是如此。
        :param timeout: 最大允许持仓K线数量限制为最近一个开仓事件触发后的 timeout 根基础周期K线
        :param stop_loss: 最大允许亏损比例，单位：BP， 1BP = 0.01%；成本的计算以最近一个开仓事件触发价格为准
        :param T0: 是否允许T0交易，默认为 False 表示不允许T0交易
        :param name: 仓位名称，默认值为第一个开仓事件的名称
        """
        assert name, "name 是必须的参数"
        self.symbol = symbol
        self.opens = opens
        self.name = name
        self.exits = exits if exits else []
        self.events = self.opens + self.exits
        for event in self.events:
            assert event.operate in [Operate.LO, Operate.LE, Operate.SO, Operate.SE]

        self.interval = interval
        self.timeout = timeout
        self.stop_loss = stop_loss
        self.T0 = T0

        self.pos_changed = False  # 仓位是否发生变化
        self.operates = []  # 事件触发的操作列表
        self.holds = []  # 持仓状态列表
        self.pos = 0

        # 辅助判断的缓存数据
        self.last_event = {
            "dt": None,
            "bid": None,
            "price": None,
            "op": None,
            "op_desc": None,
        }
        self.last_lo_dt = None  # 最近一次开多交易的时间
        self.last_so_dt = None  # 最近一次开空交易的时间
        self.end_dt = None  # 最近一次信号传入的时间

    def __repr__(self):
        return f"Position(name={self.name}, symbol={self.symbol}, opens={[x.name for x in self.opens]}, timeout={self.timeout}, stop_loss={self.stop_loss}BP, T0={self.T0}, interval={self.interval}s)"

    @property
    def unique_signals(self) -> List[str]:
        """获取所有事件的唯一信号列表"""
        signals = []
        for e in self.events:
            signals.extend(e.unique_signals)
        return list(set(signals))

    def get_signals_config(self, signals_module: str = "") -> List[Dict]:
        """获取事件的信号配置"""
        return get_signals_config(self.unique_signals, signals_module)

    def dump(self, with_data: bool = False) -> dict:
        """将对象转换为 dict"""
        raw = {
            "symbol": self.symbol,
            "name": self.name,
            "opens": [x.dump() for x in self.opens],
            "exits": [x.dump() for x in self.exits],
            "interval": self.interval,
            "timeout": self.timeout,
            "stop_loss": self.stop_loss,
            "T0": self.T0,
        }
        if with_data:
            raw.update({"pairs": self.pairs, "holds": self.holds})
        return raw

    @classmethod
    def load(cls, raw: dict) -> "Position":
        """从 dict 中创建 Position
        :param raw: 样例如下
        :return:
        """
        pos = Position(
            name=raw["name"],
            symbol=raw["symbol"],
            opens=[Event.load(x) for x in raw["opens"] if raw.get("opens")],
            exits=[Event.load(x) for x in raw["exits"] if raw.get("exits")],
            interval=raw["interval"],
            timeout=raw["timeout"],
            stop_loss=raw["stop_loss"],
            T0=raw["T0"],
        )
        return pos

    @property
    def pairs(self) -> List[Dict]:
        """开平交易列表

        返回样例：

        [{'标的代码': '000001.SH',
          '交易方向': '多头',
          '开仓时间': Timestamp('2020-04-17 00:00:00'),
          '平仓时间': Timestamp('2020-04-20 00:00:00'),
          '开仓价格': 2838.49,
          '平仓价格': 2852.55,
          '持仓K线数': 1,
          '事件序列': '开多@站上SMA5 -> 开多@站上SMA5',
          '持仓天数': 3.0,
          '盈亏比例': 49.53},
         {'标的代码': '000001.SH',
          '交易方向': '多头',
          '开仓时间': Timestamp('2020-04-20 00:00:00'),
          '平仓时间': Timestamp('2020-04-24 00:00:00'),
          '开仓价格': 2852.55,
          '平仓价格': 2808.53,
          '持仓K线数': 4,
          '事件序列': '开多@站上SMA5 -> 平多@100BP止损',
          '持仓天数': 4.0,
          '盈亏比例': -154.32}]

        数据说明：

        1. 盈亏比例，单位是 BP
        2. 持仓天数，单位是 自然日
        3. 持仓K线数，指基础周期K线数量
        """
        pairs = []

        for op1, op2 in zip(self.operates, self.operates[1:]):
            if op1["op"] not in [Operate.LO, Operate.SO]:
                continue

            ykr = op2["price"] / op1["price"] - 1 if op1["op"] == Operate.LO else 1 - op2["price"] / op1["price"]
            pair = {
                "标的代码": self.symbol,
                "策略标记": self.name,
                "交易方向": "多头" if op1["op"] == Operate.LO else "空头",
                "开仓时间": op1["dt"],
                "平仓时间": op2["dt"],
                "开仓价格": op1["price"],
                "平仓价格": op2["price"],
                "持仓K线数": op2["bid"] - op1["bid"],
                "事件序列": f"{op1['op_desc']} -> {op2['op_desc']}",
                "持仓天数": (op2["dt"] - op1["dt"]).total_seconds() / (24 * 3600),
                "盈亏比例": round(ykr * 10000, 2),  # 盈亏比例 转换成以 BP 为单位的收益，1BP = 0.0001
            }
            pairs.append(pair)

        return pairs

    def update(self, s: dict):
        """更新持仓状态

        函数执行逻辑：

        - 首先，检查最新信号的时间是否在上次信号之前，如果是则打印警告信息并返回。
        - 初始化一些变量，包括操作类型（op）和操作描述（op_desc）。
        - 遍历所有的事件，检查是否与最新信号匹配。如果匹配，则记录操作类型和操作描述，并跳出循环。
        - 提取最新信号的相关信息，包括交易对符号、时间、价格和成交量。
        - 更新持仓状态的结束时间为最新信号的时间。
        - 如果操作类型是开仓（LO或SO），更新最后一个事件的信息。
        - 定义一个内部函数__create_operate，用于创建操作记录。
        - 根据操作类型更新仓位和操作记录。

            - 如果操作类型是LO（开多），检查是否满足开仓条件，如果满足则开多仓，否则只平空仓。
            - 如果操作类型是SO（开空），检查是否满足开仓条件，如果满足则开空仓，否则只平多仓。
            - 如果当前持仓为多仓，进行多头出场的判断：
                - 如果操作类型是LE（平多），平多仓。
                - 如果当前价格相对于最后一个事件的价格的收益率小于止损阈值，平多仓。
                - 如果当前成交量相对于最后一个事件的成交量的增加量大于超时阈值，平多仓。

            - 如果当前持仓为空仓，进行空头出场的判断：
                - 如果操作类型是SE（平空），平空仓。
                - 如果当前价格相对于最后一个事件的价格的收益率小于止损阈值，平空仓。
                - 如果当前成交量相对于最后一个事件的成交量的增加量大于超时阈值，平空仓。

        - 将当前持仓状态和价格记录到持仓列表中。

        :param s: 最新信号字典
        :return:
        """
        if self.end_dt and s["dt"] <= self.end_dt:
            logger.warning(f"请检查信号传入：最新信号时间{s['dt']}在上次信号时间{self.end_dt}之前")
            return

        self.pos_changed = False
        op = Operate.HO
        op_desc = ""
        for event in self.events:
            m, f = event.is_match(s)
            if m:
                op = event.operate
                op_desc = f"{event.name}@{f}"
                break

        symbol = s["symbol"]
        dt = s["dt"]
        price = s["close"]
        bid = s.get("id", s.get("bid", 0))
        self.end_dt = dt

        # 当有新的开仓 event 发生，更新 last_event
        if op in [Operate.LO, Operate.SO]:
            self.last_event = {
                "dt": dt,
                "bid": bid,
                "price": price,
                "op": op,
                "op_desc": op_desc,
            }

        def __create_operate(_op, _op_desc):
            self.pos_changed = True
            return {
                "symbol": symbol,
                "dt": dt,
                "bid": bid,
                "price": price,
                "op": _op,
                "op_desc": _op_desc,
                "pos": self.pos,
            }

        # 更新仓位
        if op == Operate.LO:
            if self.pos != 1 and (not self.last_lo_dt or (dt - self.last_lo_dt).total_seconds() > self.interval):
                # 与前一次开多间隔时间大于 interval，直接开多
                self.pos = 1
                self.operates.append(__create_operate(Operate.LO, op_desc))
                self.last_lo_dt = dt
            else:
                # 与前一次开多间隔时间小于 interval，仅对空头平仓
                if self.pos == -1 and (self.T0 or dt.date() != self.last_so_dt.date()):
                    self.pos = 0
                    self.operates.append(__create_operate(Operate.SE, op_desc))

        if op == Operate.SO:
            if self.pos != -1 and (not self.last_so_dt or (dt - self.last_so_dt).total_seconds() > self.interval):
                # 与前一次开空间隔时间大于 interval，直接开空
                self.pos = -1
                self.operates.append(__create_operate(Operate.SO, op_desc))
                self.last_so_dt = dt
            else:
                # 与前一次开空间隔时间小于 interval，仅对多头平仓
                if self.pos == 1 and (self.T0 or dt.date() != self.last_lo_dt.date()):
                    self.pos = 0
                    self.operates.append(__create_operate(Operate.LE, op_desc))

        # 多头出场
        if self.pos == 1 and (self.T0 or dt.date() != self.last_lo_dt.date()):
            assert self.last_event["dt"] >= self.last_lo_dt

            # 多头平仓
            if op == Operate.LE:
                self.pos = 0
                self.operates.append(__create_operate(Operate.LE, op_desc))

            # 多头止损
            if price / self.last_event["price"] - 1 < -self.stop_loss / 10000:
                self.pos = 0
                self.operates.append(__create_operate(Operate.LE, f"平多@{self.stop_loss}BP止损"))

            # 多头超时
            if bid - self.last_event["bid"] > self.timeout:
                self.pos = 0
                self.operates.append(__create_operate(Operate.LE, f"平多@{self.timeout}K超时"))

        # 空头出场
        if self.pos == -1 and (self.T0 or dt.date() != self.last_so_dt.date()):
            assert self.last_event["dt"] >= self.last_so_dt

            # 空头平仓
            if op == Operate.SE:
                self.pos = 0
                self.operates.append(__create_operate(Operate.SE, op_desc))

            # 空头止损
            if 1 - price / self.last_event["price"] < -self.stop_loss / 10000:
                self.pos = 0
                self.operates.append(__create_operate(Operate.SE, f"平空@{self.stop_loss}BP止损"))

            # 空头超时
            if bid - self.last_event["bid"] > self.timeout:
                self.pos = 0
                self.operates.append(__create_operate(Operate.SE, f"平空@{self.timeout}K超时"))

        self.holds.append({"dt": self.end_dt, "pos": self.pos, "price": price})


class 信号计算器:
    """多周期信号计算引擎 — 基于观察者字典。

    不再依赖 立体分析器，直接接收 ``{周期秒: 观察者}`` 字典。

    使用方式::

        分析器 = 立体分析器("btcusd", [300, 900, 3600], 配置)
        观察者字典 = {p: 分析器._单体分析器[p] for p in 分析器.周期组}
        计算器 = 信号计算器(观察者字典, 基础周期=300, 信号配置=[...])

        for k in k线列表:
            分析器.投喂K线(k)
            计算器.更新()
            print(计算器.信号字典)
    """

    def __init__(
        self,
        分析器: 立体分析器,
        信号配置: Optional[List[Dict]] = None,
        信号模块: str = "",
    ):
        self._分析器 = 分析器
        self._观察者字典 = {p: 分析器._单体分析器[p] for p in 分析器.周期组}
        self._基础周期 = 分析器.周期组[0]
        self._信号模块 = 信号模块
        self._信号函数缓存: Dict[str, Callable] = {}
        self.信号: dict = {}
        self.行情: dict = {}
        self.信号配置 = 信号配置 or []
        self._自动挂载指标()

    @property
    def 信号字典(self) -> dict:  # 向后兼容：合并返回
        return {**self.信号, **self.行情}

    @property
    def 信号配置(self) -> List[Dict]:
        return self._信号配置

    @信号配置.setter
    def 信号配置(self, value: List[Dict]):
        可用周期 = set(self._分析器.周期组)
        for c in value:
            freq = c.get("freq")
            if freq is not None:
                周期秒 = int(freq)
                if 周期秒 not in 可用周期:
                    raise ValueError(f"信号配置 freq={freq}({周期秒}s) 不在分析器周期组 {sorted(可用周期)} 中\n  信号: {c.get('name', '?')}")
        self._信号配置 = self._去重配置(value)
        self._预加载信号函数()

    def _去重配置(self, configs: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for c in configs:
            key = (c.get("name"), frozenset((k, str(v)) for k, v in c.items() if k != "name"))
            if key not in seen:
                seen.add(key)
                unique.append(c)
            else:
                logger.warning(f"信号计算器: 重复信号配置已跳过 — {c.get('name', '?')} { {k: v for k, v in c.items() if k != 'name'} }")
        return unique

    def _预加载信号函数(self):
        for config in self._信号配置:
            name = config.get("name")
            if name and name not in self._信号函数缓存:
                try:
                    self._信号函数缓存[name] = self._解析信号函数(name)
                except (ImportError, ModuleNotFoundError, AttributeError, KeyError) as e:
                    logger.warning(f"信号计算器: 无法导入 {name} ({e})，跳过")

    @staticmethod
    def _解析信号函数(name: str):
        """解析信号函数名，返回可调用对象。

        当运行在 __main__ 上下文中且目标模块为 chan 时，优先使用 __main__
        命名空间中的函数，避免 import_by_name 触发 chan 模块的重复导入。
        """
        if "." in name:
            module_name, func_name = name.rsplit(".", 1)
            main_mod = sys.modules.get("__main__")
            if main_mod is not None and hasattr(main_mod, func_name):
                # 验证 __main__ 确实是目标模块（通过文件名判断）
                main_file = getattr(main_mod, "__file__", "")
                expected_path = module_name.replace(".", os.sep) + ".py"
                if main_file.endswith(expected_path):
                    return getattr(main_mod, func_name)

        return import_by_name(name)

    def _自动挂载指标(self):
        """根据信号配置参数，在对应周期的观察者上自动补全缺失的指标。"""

        待补MACD: Dict[int, List[tuple]] = defaultdict(list)
        待补均线: Dict[int, List[tuple]] = defaultdict(list)

        for config in self._信号配置:
            name = config.get("name", "")
            freq = config.get("freq")
            if not freq:
                continue
            周期秒 = int(freq)
            if 周期秒 not in self._观察者字典:
                continue

            # MACD 类信号：从 config 解析 fast/slow/signal 参数
            if "macd" in name.lower() or "中枢" in name or "背驰" in name or "金叉" in name:
                fast = int(config.get("fast", config.get("快线周期", 13)))
                slow = int(config.get("slow", config.get("慢线周期", 31)))
                sig = int(config.get("signal", config.get("信号周期", 11)))
                key = f"macd_{fast}_{slow}_{sig}"
                if not any(t[0] == key for t in 待补MACD[周期秒]):
                    待补MACD[周期秒].append((key, "收", fast, slow, sig))

            # MA 类信号：从 config 解析 ma_type/timeperiod
            if "ma_" in name or "tas_ma" in name or "均线" in name:
                ma_type = config.get("ma_type", "SMA").upper()
                period = int(config.get("timeperiod", config.get("周期", 5)))
                key = f"{ma_type}_{period}"
                if not any(t[0] == key for t in 待补均线[周期秒]):
                    待补均线[周期秒].append((key, "收", ma_type, period))

        for 周期秒, macd_list in 待补MACD.items():
            cfg = self._观察者字典[周期秒].配置
            if not cfg.计算指标:
                cfg.计算指标 = True
            已有键 = {t[0] for t in cfg.MACD_参数列表}
            # 同时检查 (快线, 慢线, 信号) 参数避免只键名不同但参数相同的重复
            已有参数 = {(t[2], t[3], t[4]) for t in cfg.MACD_参数列表 if len(t) >= 5}
            新增 = [t for t in macd_list if t[0] not in 已有键 and (t[2], t[3], t[4]) not in 已有参数]
            if 新增:
                cfg.MACD_参数列表.extend(新增)
                if "macd" not in 已有键:
                    cfg.MACD_参数列表.insert(0, ("macd", "收", 新增[0][2], 新增[0][3], 新增[0][4]))
                logger.warning(f"信号计算器: 周期{周期秒}s 自动补全 MACD — {[t[0] for t in 新增]}")

        for 周期秒, ma_list in 待补均线.items():
            cfg = self._观察者字典[周期秒].配置
            if not cfg.计算指标:
                cfg.计算指标 = True
            已有 = {t[0] for t in cfg.均线参数列表}
            新增 = [t for t in ma_list if t[0] not in 已有]
            if 新增:
                cfg.均线参数列表.extend(新增)
                logger.warning(f"信号计算器: 周期{周期秒}s 自动补全 均线 — {[t[0] for t in 新增]}")

    def 从信号列表提取配置(self, 信号序列: List[str]):
        """从信号序列自动生成信号配置"""
        self.信号配置 = get_signals_config(list(set(信号序列)), self._信号模块)

    def 更新(self):
        """遍历信号配置，调用信号函数。结果写入 self.信号 和 self.行情。"""
        self.信号.clear()
        self.行情.clear()

        for config in self._信号配置:
            try:
                result = self._执行信号函数(config)
                if result:
                    for k, v in result.items():
                        if v != "任意_任意_任意_0":
                            self.信号[k] = v
            except (TypeError, ValueError, KeyError, AttributeError, IndexError) as e:
                logger.error(f"信号计算器: {config.get('name', '?')} 出错 — {e}")
                traceback.print_exc()

        # OHLCV 行情
        基础观察者 = self._观察者字典.get(self._基础周期)
        if 基础观察者 and 基础观察者.普通K线序列:
            最后K线 = 基础观察者.普通K线序列[-1]
            时间戳 = 最后K线.时间戳
            if isinstance(时间戳, (int, float)):
                时间戳 = datetime.fromtimestamp(int(时间戳))
            self.行情.update(
                symbol=基础观察者.符号,
                dt=时间戳,
                id=最后K线.序号,
                open=最后K线.开盘价,
                close=最后K线.收盘价,
                high=最后K线.高,
                low=最后K线.低,
                vol=最后K线.成交量,
            )

    def _执行信号函数(self, config: Dict) -> Optional[OrderedDict]:
        param = dict(config)
        sig_name = param.pop("name")
        sig_func = self._信号函数缓存.get(sig_name) or self._解析信号函数(sig_name)

        freq = param.get("freq")
        if freq is not None:
            周期秒 = int(freq)
            obs = self._观察者字典.get(周期秒)
            if obs is not None:
                return sig_func(obs, **param)
            else:
                raise KeyError(f"信号计算器: 未找到周期 {周期秒}s 的观察者，可用周期: {sorted(self._观察者字典.keys())}")
        else:
            return sig_func(self, **param)

    def 获取周期观察者(self, freq: str) -> Optional[观察者]:
        return self._观察者字典.get(int(freq))


def 测试_读取数据(观察员: 观察者, 配置: 缠论配置) -> Callable[[], 观察者]:
    """测试_读取数据
    :param 观察员: 观察者
    :param 配置: 缠论配置
    :return: 测试函数
    """

    def 魔法():
        启动时间 = datetime.now()
        观察者.读取数据文件(配置.加载文件路径, 配置, 观察员=观察员)
        消耗用时 = datetime.now() - 启动时间
        logger.info(f"测试_读取数据 耗时 {消耗用时} 普K数量 {len(观察员.普通K线序列)}")
        return 观察员

    return 魔法


def 测试_周期合成(配置: 缠论配置, 配置组: Dict[int, 缠论配置] = dict()):
    """测试_周期合成

    :param 配置: 默认配置
    :param 配置组: 各周期独立配置
    :return: 测试函数
    """
    文件路径 = 配置.加载文件路径
    name = Path(文件路径).name.split(".")[0]
    符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
    周期 = int(周期)
    周期组 = [周期, 周期 * 5, 周期 * 5 * 6]

    def 魔法():
        启动时间 = datetime.now()
        多级别分析 = 立体分析器(符号, 周期组, 配置, 配置组)
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], 周期, 符号)
                多级别分析.投喂K线(k线)
        消耗用时 = datetime.now() - 启动时间
        logger.info(f"测试_周期合成 {消耗用时} 普K数量 {len(多级别分析._单体分析器[周期].普通K线序列)}")
        return 多级别分析

    return 魔法


def 测试_指标挂载(配置: 缠论配置):
    文件路径 = 配置.加载文件路径
    name = Path(文件路径).name.split(".")[0]
    符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
    周期 = int(周期)
    观察员 = 观察者(符号, 周期, 配置)
    观察员.线段分析层次 = 0
    观察员.重置基础序列()

    def 魔法():
        启动时间 = datetime.now()
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                if i == 500:
                    配置.MACD_参数列表 = [("macd", "收", 13, 31, 11)]
                    配置.MACD_参数列表.append(("macd_12_26_9", 12, 26, 9))
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], 周期, 符号)
                观察员.增加原始K线(k线)
                if i == 500:
                    assert 观察员.普通K线序列[0].指标.macd_12_26_9 is not None, "指标挂载失败"
                    print(观察员.普通K线序列[-1].指标["macd_12_26_9"])
                    print(观察员.普通K线序列[-1].macd)

                    break

        消耗用时 = datetime.now() - 启动时间
        logger.info(f"测试_指标挂载 耗时 {消耗用时} 普K数量 {len(观察员.普通K线序列)}")
        return 观察员

    return 魔法


def 测试_信号识别(配置: 缠论配置):
    文件路径 = 配置.加载文件路径
    name = Path(文件路径).name.split(".")[0]
    符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
    周期 = int(周期)
    分析器 = 立体分析器(符号, [周期, 周期 * 5, 周期 * 5 * 6], 配置)
    信号配置 = []
    for p in [周期, 周期 * 5, 周期 * 5 * 6]:
        信号配置.extend(
            get_signals_config(
                [
                    f"{str(p)}_D1#MACD#13#33#11_MACD交叉V260601_金叉_任意_任意_0",
                ],
                "signals",
            )
        )
    计算器 = 信号计算器(分析器, 信号配置, "signals")

    def 魔法():
        启动时间 = datetime.now()
        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], 周期, 符号)
                分析器.投喂K线(k线)

                计算器.更新()

                # 输出信号内容
                if 计算器.信号:
                    dt = k线.时间戳
                    if isinstance(dt, (int, float)):
                        dt = datetime.fromtimestamp(dt)
                    信号摘要 = "  ".join(f"{k}→{v}" for k, v in 计算器.信号.items())
                    信号类型 = ",".join(sorted(set(v.split("_")[0] for v in 计算器.信号.values())))
                    logger.info(f"[{dt}] [{信号类型}] 📡 {信号摘要}")
                    print(f"[{dt}] [{信号类型}] 📡 {信号摘要}, {计算器.信号}")
                    print()

        消耗用时 = datetime.now() - 启动时间
        logger.info(f"测试_信号识别 {消耗用时} 普K数量 {len(分析器._单体分析器[周期].普通K线序列)}")
        return 分析器

    return 魔法


if __name__ == "__main__":
    当前配置 = 缠论配置.不推送()
    当前配置.加载文件路径 = str(Path(__file__).parent / "templates/btcusd-300-1761327300-1776327900.nb")
    with tempfile.TemporaryDirectory() as tmpdir:
        # 测试_读取数据(观察者("", 0, 当前配置), 当前配置)().测试_保存数据(tmpdir)
        # 测试_周期合成(当前配置)().测试_保存数据(tmpdir)
        # 测试_指标挂载(当前配置)().测试_保存数据(tmpdir)
        测试_信号识别(当前配置)()
