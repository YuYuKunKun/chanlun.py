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
"""
# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 16:45
# @Author  : YuYuKunKun
# @File    : chan.py

import json
import math
import struct
import sys
from dataclasses import dataclass, field
from datetime import datetime
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
)

from pydantic import BaseModel, Field, model_validator, ValidationError, field_validator
from termcolor import colored


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
]


class 买卖点类型(str, Enum):
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
        return self.name

    def __repr__(self) -> str:
        return self.name

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


class datetime_(datetime):  # 用于对齐C输出
    def __str__(self):
        return f"{int(self.timestamp())}"

    def __repr__(self):
        return f"{int(self.timestamp())}"


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
    笔内起始分型包含整笔_包括右: bool = False  # True: 将笔之武.右纳入
    笔内原始K线包含整笔: bool = False  # 在非 [笔内起始分型包含整笔] 时判断原始K线包含整笔的情况

    笔次级成笔: bool = False
    笔弱化: bool = False
    笔弱化_原始数量: int = 3
    # 笔_必须对齐:bool = False # 强迫症设为True, 将获得无与伦比满足。。。

    线段_非缺口下穿刺: bool = False  # True: 非缺口状态下[小阳, 少阴]时，存在贯穿伤与之后紧邻的三个元素有方向相同的线段时回退， 此举在当下是否有任何意义呢？
    线段_特征序列忽视老阴老阳: bool = False  # True 不用严格的特征序列包含，也就是忽视缺口全以无缺口对待
    线段_缺口后紧急修正: bool = True  # True: 当 线段_特征序列忽视老阴老阳=False 时生效，同样 线段_特征序列忽视老阴老阳=True时等同于修正武斗不异常，但只产出一个线段
    线段_修正: bool = False  # 短路修正，不建议使用，但此修正将走势显示的更加清晰

    线段内部中枢图显: bool = True
    扩展线段_当下分析: bool = False  # 以当下来看的分析规则，否则以事后来看

    分析笔: bool = True  # 是否计算BI
    分析线段: bool = True  # 是否计算XD
    分析扩展线段: bool = True  # 是否计算XD
    分析笔中枢: bool = True  # 是否计算BI中枢
    分析线段中枢: bool = True  # 是否计算XD中枢

    手动终止: str = ""  # 2099-12-31 00:00:00
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

    买卖点_指标模式: str = "配置"  # 【任意，配置，全量, 相对】 对应K线
    买卖点_指标匹配_MACD: bool = True  # 买在负，卖在正！
    买卖点_指标匹配_KDJ: bool = True  # 买在死叉之后，卖在金叉之后
    买卖点_指标匹配_RSI: bool = True  # 买在均线之下，卖在均线之上

    # --- 缠论六类买卖点识别参数 ---
    买卖点_背离率: float = float("inf")  # T1/T1P背离率，默认无限大（不筛选）
    买卖点_T2_回调阈值: float = 1.0  # T2回调幅度/突破振幅上限
    买卖点_T2S_最大层级: int = 3  # T2S最大搜索深度
    买卖点_峰值条件: bool = False  # T1是否要求突破中枢内所有元素的极值
    买卖点_计算方式: str = "峰"  # "峰"=最大MACD柱绝对值, "面"=MACD柱面积
    买卖点_计算线段BSP1: bool = True  # 是否启用T1/T1P识别
    买卖点_处理BSP2: bool = True  # 是否启用T2/T2S识别
    买卖点_计算线段BSP3: bool = True  # 是否启用T3A/T3B识别
    买卖点_依赖T1: bool = True  # T2是否必须依赖T1
    买卖点_中枢来源: str = "合"  # "实"/"虚"/"合" - 取线段的哪个内部中枢序列
    买卖点_调试输出: bool = False  # 是否打印调试信息

    线段内部背驰_MACD: bool = True
    线段内部背驰_斜率: bool = True
    线段内部背驰_测度: bool = True
    线段内部背驰_模式: str = "相对"  # 【任意，配置，全量，相对】

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

    @classmethod
    def 按序号重组字典(cls, 默认配置, 原始字典: dict) -> dict:
        """
        {
            "1_open": 10,
            "1_close": 11,
            "2_open": 20,
            "name": "BTC",    # 无法拆分
            "time": 123456    # 无法拆分
        }
        转化为
        {
            1: {"open": 10, "close": 11},
            2: {"open": 20},
            "无法拆分": {
                "name": "BTC",
                "time": 123456
            }
        }

        """

        结果 = {}
        无法拆分项 = {}

        for 复合键, 值 in 原始字典.items():
            # 尝试拆分
            if "_" in 复合键:
                序号部分, 键部分 = 复合键.split("_", 1)
                try:
                    序号 = int(序号部分)
                    # 能正常拆分 → 分组
                    if 序号 not in 结果:
                        结果[序号] = {}
                    结果[序号][键部分] = 值
                except:
                    # 格式异常 → 单独处理
                    无法拆分项[复合键] = 值
            else:
                # 无下划线 → 无法拆分 → 单独存放
                无法拆分项[复合键] = 值

        # 把无法拆分的也放进结果顶层（你要的结构）
        """if 无法拆分项:
            结果["无法拆分"] = 无法拆分项"""
        配置组 = dict()
        for k, v in 结果.items():
            配置组[k] = 默认配置.model_copy(
                update=v,
                deep=True,
            )

        return 配置组

    def 对比(self, other: "缠论配置") -> dict:
        """
        比较当前配置与另一个配置的差异
        返回: {
            "字段名": {
                "旧值": 当前配置的值,
                "新值": 另一个配置的值
            },
            ...
        }
        仅当值不同时才包含该字段
        """
        diff_dict = {}
        # 获取所有字段名
        for field_name in self.model_fields.keys():
            old_value = getattr(self, field_name)
            new_value = getattr(other, field_name)
            # 直接比较值（支持 None）
            if old_value != new_value:
                diff_dict[field_name] = new_value
        return diff_dict


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


@final
class 缺口:
    def __init__(self, 高: float, 低: float) -> None:
        assert 高 > 低
        self.高 = 高
        self.低 = 低

    def __str__(self) -> str:
        return f"缺口区间<{self.低:g} <=> {self.高:g}>"

    def __repr__(self) -> str:
        return f"缺口区间<{self.低:g} <=> {self.高:g}>"


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

    # 模型配置
    model_config = {
        "arbitrary_types_allowed": True,  # 允许特殊类型
        "json_encoders": {
            datetime: lambda v: v.isoformat(),  # 日期时间序列化
            Enum: lambda v: v.value,  # 枚举值序列化
        },
    }

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
        )

    @classmethod
    def 增量计算_K线(cls, 前一个MACD: "平滑异同移动平均线", 当前K线: "K线", 计算方式: "str") -> "平滑异同移动平均线":
        当前收盘价: float = 指标.K线取值(当前K线, 计算方式)
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个MACD, 当前收盘价, 当前时间)


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
            RSI_SMA周期=RSI_SMA周期,
            RSI_SMA=RSI_SMA,
            RSI历史队列=历史队列,
        )

    @classmethod
    def 增量计算_K线(cls, 前一个RSI: "相对强弱指数", 当前K线: "K线", 计算方式: "str") -> "相对强弱指数":
        当前收盘价: float = 指标.K线取值(当前K线, 计算方式)
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个RSI, 当前收盘价, 当前时间)


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
    def 增量计算_K线(cls, 前一个KDJ: "随机指标", 当前K线: "K线", 计算方式: "str") -> "随机指标":
        当前最高价: float = 当前K线.高
        当前最低价: float = 当前K线.低
        当前收盘价: float = 当前K线.收盘价
        当前时间: datetime = 当前K线.时间戳
        return cls.增量计算(前一个KDJ, 当前最高价, 当前最低价, 当前收盘价, 当前时间)


class 背驰分析:
    @staticmethod
    def MACD背驰(进入段: "虚线", 离开段: "虚线", K线序列: List["K线"], 方式: str = "总") -> bool:
        """MACD柱状线面积背驰"""
        进入MACD = K线.获取MACD(K线序列, 进入段.文.中.标的K线, 进入段.武.中.标的K线)
        离开MACD = K线.获取MACD(K线序列, 离开段.文.中.标的K线, 离开段.武.中.标的K线)

        # 计算面积（绝对值求和）
        进入面积 = abs(进入MACD["总"] if 方式 == "总" else (进入MACD["阳"] if 进入段.方向 is 相对方向.向上 else 进入MACD["阴"]))
        离开面积 = abs(离开MACD["总"] if 方式 == "总" else (离开MACD["阳"] if 进入段.方向 is 相对方向.向上 else 离开MACD["阴"]))

        return 离开面积 < 进入面积

    @staticmethod
    def 斜率背驰(进入段: "虚线", 离开段: "虚线") -> bool:
        """价格斜率背驰"""
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
    def 测度背驰(进入段: "虚线", 离开段: "虚线") -> bool:
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

    @staticmethod
    def 全量背驰(进入段: "虚线", 离开段: "虚线", 普K序列: List["K线"]) -> bool:
        return all([背驰分析.MACD背驰(进入段, 离开段, 普K序列), 背驰分析.测度背驰(进入段, 离开段), 背驰分析.斜率背驰(进入段, 离开段)])

    @staticmethod
    def 任意背驰(进入段: "虚线", 离开段: "虚线", 普K序列: List["K线"]) -> bool:
        return any([背驰分析.MACD背驰(进入段, 离开段, 普K序列), 背驰分析.测度背驰(进入段, 离开段), 背驰分析.斜率背驰(进入段, 离开段)])

    @staticmethod
    def 配置背驰(进入段: "虚线", 离开段: "虚线", 普K序列: List["K线"], 配置: 缠论配置) -> bool:
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
    def 任选背驰(进入段: "虚线", 离开段: "虚线", 普K序列: List["K线"]) -> bool:
        混沌槽 = [背驰分析.MACD背驰(进入段, 离开段, 普K序列), 背驰分析.测度背驰(进入段, 离开段), 背驰分析.斜率背驰(进入段, 离开段)]
        return len([背驰 for 背驰 in 混沌槽 if 背驰]) >= 2

    @staticmethod
    def 背驰模式(进入段: "虚线", 离开段: "虚线", 普K序列: List["K线"], 配置: 缠论配置, 模式: str) -> bool:
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
        return f"{self.标识}<{self.序号}, {self.周期}, {self.方向}, {self.时间戳}, {self.开盘价:g}, {self.高:g}, {self.低:g}, {self.收盘价:g}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.周期}, {self.方向}, {self.时间戳}, {self.开盘价:g}, {self.高:g}, {self.低:g}, {self.收盘价:g}>"

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

    @staticmethod
    def 截取(序列: List["K线"], 始: "K线", 终: "K线") -> List["K线"]:
        return 序列[序列.index(始) : 序列.index(终) + 1]


class 缠论K线(object):
    __slots__ = ["序号", "时间戳", "高", "低", "方向", "分型", "周期", "标识", "分型特征值", "原始起始序号", "原始结束序号", "标的K线", "买卖点信息"]

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
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.方向}, {self.时间戳}, {self.高:g}, {self.低:g}>"

    def __repr__(self):
        return f"{self.标识}<{self.序号}, {self.分型}, {self.周期}, {self.方向}, {self.时间戳}, {self.高:g}, {self.低:g}>"

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
            return False
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
            if 之前普K.时间戳 == 当前K线.时间戳:
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
    def 截取(序列: List["缠论K线"], 始: "缠论K线", 终: "缠论K线") -> List["缠论K线"]:
        return 序列[序列.index(始) : 序列.index(终) + 1]


class 分型(object):
    __slots__ = ["左", "中", "右", "结构", "时间戳", "分型特征值"]

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
        return f"{self.中.分型}<{self.时间戳}, {self.分型特征值:g}, None: {self.左 is None}, None: {self.右 is None}>"

    def __repr__(self):
        return f"{self.中.分型}<{self.时间戳}, {self.分型特征值:g}, None: {self.左 is None}, None: {self.右 is None}>"

    @property
    def 关系组(self) -> Optional[Tuple[相对方向, 相对方向, 相对方向]]:
        if self.左 and self.右:
            return 相对方向.分析(self.左.高, self.左.低, self.中.高, self.中.低), 相对方向.分析(self.中.高, self.中.低, self.右.高, self.右.低), 相对方向.分析(self.左.高, self.左.低, self.右.高, self.右.低)
        return None

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
        try:
            return 分型(左=K线序列[索引 - 1], 中=中, 右=K线序列[索引 + 1])
        except IndexError:
            return 分型(左=K线序列[索引 - 1], 中=中, 右=None)

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


class 虚线(object):
    __slots__ = ["标识", "序号", "级别", "文", "武", "有效性", "基础序列", "特征序列", "实_中枢序列", "虚_中枢序列", "合_中枢序列", "确认K线", "模式", "_特征序列_显示", "前一缺口", "前一结束位置", "短路修正"]

    def __init__(self, 序号: int, 标识: str, 文: 分型, 武: 分型, 级别: int, 有效性: bool = True):
        self.序号 = 序号
        self.标识 = 标识
        self.级别 = 级别

        self.文 = 文
        self.武 = 武

        self.有效性 = 有效性

        self.基础序列: List["虚线"] = []
        self.特征序列: List[Optional[线段特征]] = []

        self.实_中枢序列: List["中枢"] = []
        self.虚_中枢序列: List["中枢"] = []
        self.合_中枢序列: List["中枢"] = []
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
        return self.基础序列

    @property
    def 图表标题(self) -> str:
        return f"{self.文.中.标识}:{self.文.中.周期}:{self.标识}:{self.序号}"

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

    def 之前是(self, 之前: "虚线") -> bool:
        if self.标识 == 之前.标识:
            return 分型.判断分型(之前.武, self.文)
        return False

    def 之后是(self, 之后: "虚线") -> bool:
        if self.标识 == 之后.标识:
            return 分型.判断分型(self.武, 之后.文)
        return False

    def 获取普K序列(self, 观察员: "观察者") -> List[K线]:
        return K线.截取(观察员.普通K线序列, self.文.中.标的K线, self.武.中.标的K线)

    def 获取缠K序列(self, 观察员: "观察者") -> List[缠论K线]:
        return 缠论K线.截取(观察员.缠论K线序列, self.文.中, self.武.中)

    def 获取数据文本(self):
        if self.标识 == "笔":
            return f"{self.标识}, {self.序号}, {self.级别}, 文:({int(self.文.时间戳.timestamp())},{self.文.分型特征值:g}), 武:({int(self.武.时间戳.timestamp())},{self.武.分型特征值:g}), {self.有效性}"
        前, 后, 三, 贯穿伤 = 线段.分割序列(self)
        return f"{self.标识}, {self.序号}, {self.级别}, 文:({int(self.文.时间戳.timestamp())},{self.文.分型特征值:g}), 武:({int(self.武.时间戳.timestamp())},{self.武.分型特征值:g}), {self.有效性}, {len(self.基础序列)}, {线段.特征序列状态(self)}, (前: {str(前)}, 后: {str(后)}, 三: {str(三)}, 伤: {str(贯穿伤)}), 实: {str(self.实_中枢序列)}, 虚: {str(self.虚_中枢序列)}, 合: {str(self.合_中枢序列)}, {self.模式}, {str(self.前一缺口)}, {str(self.前一结束位置)}, {self.短路修正}"

    @classmethod
    def 创建笔(cls, 文: 分型, 武: 分型, 有效性: bool = True) -> "虚线":
        return 虚线(0, "笔", 文, 武, 1, 有效性)

    @classmethod
    def 创建线段(cls, 虚线序列: List["虚线"]) -> "虚线":
        文 = 虚线序列[0].文
        武 = 虚线序列[-1].武
        标识 = "线段" if 虚线序列[0].标识 == "笔" else f"线段<{虚线序列[0].标识}>"
        段 = 虚线(0, 标识, 文, 武, 虚线序列[0].级别 + 1)
        段.特征序列 = [None] * 3
        段.实_中枢序列 = []
        段.虚_中枢序列 = []
        段.合_中枢序列 = []
        段.基础序列 = 虚线序列
        return 段


class 笔(object):
    __slots__ = []

    @staticmethod
    def 获取缠K数量(缠K序列: List[缠论K线], 笔序列: List[虚线], 配置: 缠论配置) -> int:
        实际数量 = len(缠K序列)
        if 实际数量 >= 配置.笔内元素数量:
            return 实际数量

        if 配置.笔弱化 and 实际数量 >= 3:
            实际高点 = 笔.实际高点(缠K序列, 配置.笔内相同终点取舍)
            实际低点 = 笔.实际低点(缠K序列, 配置.笔内相同终点取舍)
            原始数量 = 1 + abs(实际低点.标的K线.序号 - 实际高点.标的K线.序号)
            if 原始数量 >= 配置.笔内元素数量:
                return 配置.笔内元素数量

            if 笔序列:
                筆 = 笔.根据缠K找笔(笔序列, 实际高点) or 笔.根据缠K找笔(笔序列, 实际低点)
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

    @staticmethod
    def 相对关系(筆: 虚线, 配置: 缠论配置) -> bool:
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
        旧分型 = 分型序列.pop()
        if 笔序列:
            旧笔 = 笔序列.pop()
            assert 旧笔.武 is 旧分型, f"最后一笔终点错误{行号}"
            旧笔.有效性 = False

    @classmethod
    def _添加新笔(cls, 分型序列: List[分型], 笔序列: List[虚线], 待添加分型: "分型", 待添加新笔: 虚线, 行号):
        if not 分型序列 and 待添加分型.结构 not in (分型结构.顶, 分型结构.底):
            raise ValueError("首次添加分型不为 顶底", 待添加分型)
        if 分型序列:
            if 分型序列[-1].结构 is 待添加分型.结构:
                raise ValueError("分型相同无法添加", 分型序列[-1], 待添加分型)
            if 分型序列[-1].右 is None:
                print("分型.向序列中添加, 分型异常", 分型序列[-1])

        分型序列.append(待添加分型)
        if 笔序列 and not 笔序列[-1].之后是(待添加新笔):
            raise ValueError("笔.向序列中添加 不连续", 笔序列[-1], 待添加新笔)

        if 笔序列:
            待添加新笔.序号 = 笔序列[-1].序号 + 1
            if 待添加新笔.武.左 is None and 待添加新笔.武.右 is None:
                待添加新笔.有效性 = False
            if 笔序列[-1].武.结构 in (分型结构.上, 分型结构.下):
                print(f"_添加新笔[{行号}] 出现无效分型", 笔序列[-1])

        笔序列.append(待添加新笔)

    @classmethod
    def 分析(cls, 当前分型: Optional[分型], 分型序列: List[分型], 笔序列: List[虚线], 缠K序列: List[缠论K线], 普K序列: List[K线], 递归层次: int, 配置: 缠论配置):
        if 当前分型 is None:
            return 递归层次

        if 递归层次 > 64:
            print(f"笔.分析 递归深度超出 64 < {递归层次}")
            # return 递归层次

        if 当前分型.结构 not in (分型结构.顶, 分型结构.底):
            return 递归层次

        if not 分型序列:
            if 当前分型.结构 in (分型结构.顶, 分型结构.底):
                分型序列.append(当前分型)
            return 递归层次

        笔递归分析 = 笔.分析

        之前分型 = 分型序列[-1]
        if (之前分型.中.时间戳 == 当前分型.中.时间戳) or (之前分型.结构 in (分型结构.上, 分型结构.下)):
            笔._弹出旧笔(分型序列, 笔序列, sys._getframe().f_lineno)
            if not 分型序列:
                if 当前分型.右 is not None:
                    分型.向序列中添加(分型序列, 当前分型)
                return 递归层次

        之前分型 = 分型序列[-1]
        if 之前分型.中.时间戳 > 当前分型.中.时间戳 and 之前分型.中.序号 - 当前分型.中.序号 > 1:
            # raise RuntimeError(f"时序错误-{递归层次}, {之前分型}, {当前分型}")
            print(colored(f"时序错误-{递归层次}, {之前分型}, {当前分型}", "red"))
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
            if 笔.获取缠K数量(基础序列, 笔序列, 配置) >= 配置.笔内元素数量:
                if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                    文官 = 笔.实际高点(基础序列, False)
                else:
                    文官 = 笔.实际低点(基础序列, False)

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
                    武将 = 笔.实际低点(基础序列, 配置.笔内相同终点取舍)
                else:
                    武将 = 笔.实际高点(基础序列, 配置.笔内相同终点取舍)

                if 笔.相对关系(当前笔, 配置) and 当前分型.中 is 武将:
                    笔._添加新笔(分型序列, 笔序列, 当前分型, 当前笔, sys._getframe().f_lineno)
                    return 递归层次

                if 配置.笔次级成笔:
                    if 之前分型.结构 is 分型结构.顶 and 当前分型.结构 is 分型结构.底:
                        武将 = 笔.次低(基础序列, 配置.笔内相同终点取舍)
                    else:
                        武将 = 笔.次高(基础序列, 配置.笔内相同终点取舍)
                    if 笔.相对关系(当前笔, 配置) and 当前分型.中 is 武将:
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
                    武将 = 笔.实际低点(k线序列, 配置.笔内相同终点取舍)
                else:
                    武将 = 笔.实际高点(k线序列, 配置.笔内相同终点取舍)
                临时分型 = 分型.从缠K序列中获取分型(缠K序列, 武将)

                if 分型序列:
                    递归层次 = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                    if 分型序列 and 分型序列[-1] is 临时分型:
                        # 进行修复错过的笔
                        for ck in 缠K序列[缠K序列.index(武将) :]:
                            if ck.分型 in (分型结构.底, 分型结构.顶):
                                临时分型 = 分型.从缠K序列中获取分型(缠K序列, ck)
                                递归层次 = 笔递归分析(临时分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                                if 分型序列 and 分型序列[-1] is 临时分型:
                                    """"""
                                    # print("笔.分析 事后修复错过的笔", 临时分型, "当前分型", 当前分型)

                    递归层次 = 笔递归分析(当前分型, 分型序列, 笔序列, 缠K序列, 普K序列, 递归层次 + 1, 配置)
                    return 递归层次
                else:
                    分型.向序列中添加(分型序列, 当前分型)

        return 递归层次

    @staticmethod
    def 以文会友(笔序列: List[虚线], 文: 分型) -> Optional[虚线]:
        for 筆 in 笔序列:
            if 筆.文 is 文:
                return 筆
        return None

    @staticmethod
    def 以武会友(笔序列: List[虚线], 武: 分型) -> Optional[虚线]:
        for 筆 in 笔序列[::-1]:
            if 筆.武 is 武:
                return 筆
        return None

    @staticmethod
    def 根据缠K找笔(笔序列: List[虚线], 缠K: "缠论K线", 偏移: int = 1):
        for 筆 in 笔序列[::-1]:
            if 筆.文.中.序号 - 偏移 <= 缠K.序号 <= 筆.武.中.序号:
                # if 缠K in 筆.缠K序列[偏移:]:
                return 筆

        return None


class 线段特征(list):
    __slots__ = ["序号", "标识", "线段方向"]

    def __init__(self, 标识: str, 基础序列: List[虚线], 线段方向: 相对方向):
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
            func = max
        else:
            func = min
        return func([线.文 for 线 in self], key=lambda o: o.中.分型特征值)

    @property
    def 武(self) -> 分型:
        if self.线段方向 is 相对方向.向上:
            func = max
        else:
            func = min
        return func([线.武 for 线 in self], key=lambda o: o.中.分型特征值)

    @property
    def 高(self) -> float:
        return max([self.文, self.武], key=lambda fx: fx.中.分型特征值).中.分型特征值

    @property
    def 低(self) -> float:
        return min([self.文, self.武], key=lambda fx: fx.中.分型特征值).中.分型特征值

    @property
    def 方向(self) -> 相对方向:
        return self.线段方向.翻转()

    def 添加(self, 待添加虚线: Union[虚线]):
        if 待添加虚线.方向 == self.线段方向:
            raise ValueError("方向不匹配", self.线段方向, 待添加虚线, self)
        self.append(待添加虚线)

    def 删除(self, 待删除虚线: Union[虚线]):
        if 待删除虚线.方向 == self.方向:
            raise ValueError("方向不匹配", self.线段方向, 待删除虚线, self)
        self.remove(待删除虚线)

    @classmethod
    def 新建(cls, 虚线序列: List[虚线], 线段方向: 相对方向) -> "线段特征":
        return 线段特征(标识=f"特征<{虚线序列[0].__class__.__name__}>", 基础序列=虚线序列, 线段方向=线段方向)

    @classmethod
    def 静态分析(cls, 虚线序列: List[虚线], 线段方向: 相对方向, 四象: str, 是否忽视: bool = False) -> List["线段特征"]:
        """
        :param 虚线序列:
        :param 线段方向:
        :param 四象: 老阴，老阳，少阴，小阳
            老阴 老阳 分别代表 缺口顶分型后的向下线段 与 缺口底分型后的向上线段
        :return: 特征序列元组
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
                    小号虚线 = min(中, key=lambda o: o.序号)
                    大号虚线 = max(右, key=lambda o: o.序号)
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
                之前线段特征.添加(当前虚线)
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
    __slots__ = ["左", "中", "右", "结构"]

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
    __slots__ = []

    @classmethod
    def 添加虚线(cls, 段: 虚线, 筆: 虚线):
        if len(段.基础序列) and not 分型.判断分型(段.基础序列[-1].武, 筆.文):
            raise ValueError(f"{段.标识}.添加虚线 不连续", 段.基础序列[-1], 筆)

        if len(段.基础序列) and 段.基础序列[-1].标识 != 筆.标识:
            raise ValueError(f"{段.标识}.添加虚线 标识不符", 段.基础序列[-1].标识, 筆.标识)
        段.基础序列.append(筆)

    @classmethod
    def 武斗(cls, 段: 虚线, 武: 分型, 行号: int):
        # print(f"{self.__class__.__name__}.武斗[{行号}], ", 武)
        if 段.武.分型特征值 == 武.分型特征值:
            段.武 = 武
            return
        assert 段.文.结构 is not 武.结构, (f"文武结构相同 {行号}", 段.文, 武)
        if 武.右 is not None and 分型结构.分析(武.左, 武.中, 武.右) is not 武.结构:
            raise RuntimeError(分型结构.分析(武.左, 武.中, 武.右), 武.结构)
        if 段.方向 is 相对方向.向上:
            if 武.分型特征值 < 段.文.分型特征值:
                raise RuntimeError(f"向上{段.标识}, 结束点 小于 起点", 段.标识, 段.文, 武)
            # if max([self._武, 武], key=lambda k: k.分型特征值) is not 武:
            #    pass  # print(colored(f"{self.__class__.__name__}.武斗[{行号}] 出现回退 从 {self._武} ==>>> {武}", "red", "on_green"))  # raise RuntimeError(self._武, 武)
        else:
            if 武.分型特征值 > 段.文.分型特征值:
                raise RuntimeError(f"向下{段.标识}, 结束点 大于 起点", 段.标识, 段.文, 武)
            # if min([self._武, 武], key=lambda k: k.分型特征值) is not 武:
            #    pass  # print(colored(f"{self.__class__.__name__}.武斗[{行号}] 出现回退 从 {self._武} ==>>> {武}", "red", "on_green"))  # raise RuntimeError(self._武, 武)
        段.武 = 武

    @classmethod
    def 特征分型终结(cls, 段: 虚线) -> bool:
        """
        是否符合特征序列 正常分型 终结
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
        return tuple(特征 is not None for 特征 in 段.特征序列)

    @classmethod
    def 获取缺口(cls, 段: 虚线) -> Optional[缺口]:
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
        """
        老阳: 向下线段第一二特征序列有缺口时，后一向上线段
        老阴: 向上线段第一二特征序列有缺口时，后一向下线段
        小阳: 向上线段
        少阴: 向下线段
        """
        if 段.前一缺口 is not None:
            return "老阳" if 段.方向 is 相对方向.向上 else "老阴"
        return "小阳" if 段.方向 is 相对方向.向上 else "少阴"

    @classmethod
    def 设置特征序列(cls, 段: 虚线, 序列, 行号):
        # print(f"线段.设置特征序列[{行号}]", self)
        if 段.模式 != "文武":
            return

        for 特征 in 序列:
            if 特征 and 特征.方向 == 段.方向:
                raise ValueError(f"特征序列方向不匹配[{行号}]")
        左, 中, 右 = 序列
        段.特征序列 = [左, 中, 右]
        if 右 is not None:
            基础序列 = []
            if 右[-1] not in 段.基础序列:
                raise ValueError()
            for 元素 in 段.基础序列:
                基础序列.append(元素)
                if 元素 is 右[-1]:
                    break

            if (len(基础序列) >= 6) and (len(基础序列) % 2 == 0):
                段.基础序列[:] = 基础序列[:]
            else:
                raise RuntimeError()
        else:
            pass

    @classmethod
    def 刷新特征序列(cls, 段: 虚线, 配置: 缠论配置):
        if 段.模式 != "文武":
            return
        基础序列 = 段.基础序列
        if 段.前一结束位置 and 段.前一结束位置 in 基础序列:
            基础序列 = 段.基础序列[段.基础序列.index(段.前一结束位置) - 1 :]

        特征序列 = 线段特征.静态分析(基础序列, 段.方向, 线段.四象(段), 配置.线段_特征序列忽视老阴老阳)
        if len(特征序列) >= 3:
            分型序列 = 线段特征.获取分型序列(特征序列)
            if (段.方向 is 相对方向.向上 and 分型序列[-1].结构 is 分型结构.顶) or (段.方向 is 相对方向.向下 and 分型序列[-1].结构 is 分型结构.底):
                线段.设置特征序列(段, [分型序列[-1].左, 分型序列[-1].中, 分型序列[-1].右], sys._getframe().f_lineno)

            else:
                线段.设置特征序列(段, [特征序列[-2], 特征序列[-1], None], sys._getframe().f_lineno)
        else:
            特征序列.extend([None] * (3 - len(特征序列)))
            线段.设置特征序列(段, 特征序列, sys._getframe().f_lineno)

    @classmethod
    def 分割序列(cls, 段: 虚线, 所属中枢: Optional["中枢"] = None) -> Tuple[List[虚线], List[虚线], List[虚线], Optional[虚线]]:
        if 段.模式 != "文武":
            return 段.基础序列[:], [], [], None
        if len(段.基础序列) == 0:
            print(段.标识, 段.序号)
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
    def 刷新(cls, 段: 虚线, 配置: 缠论配置):
        if 段.模式 != "文武":
            return
        if not len(段.基础序列):
            print("    线段.刷新 基础序列为空")
            return

        线段.刷新特征序列(段, 配置)
        有效特征序列 = [特征 for 特征 in 段.特征序列 if 特征 is not None]
        if len(有效特征序列) == 3:
            线段.武斗(段, 段.特征序列[1].文, sys._getframe().f_lineno)

        elif len(有效特征序列) >= 1:
            最近特征 = 有效特征序列[-1]

            if 最近特征[-1] not in 段.基础序列:
                特征后一笔 = 笔.以武会友(段.基础序列, 最近特征[-1].武)
            else:
                特征后一笔 = 最近特征[-1]

            if 特征后一笔 is not None:
                序号 = 段.基础序列.index(特征后一笔)
                if 序号 < len(段.基础序列) - 1:
                    下一笔 = 段.基础序列[序号 + 1]
                    if (段.方向 is 相对方向.向上 and 段.高 <= 下一笔.高) or (段.方向 is 相对方向.向下 and 段.低 >= 下一笔.低):
                        线段.武斗(段, 下一笔.武, sys._getframe().f_lineno)
            else:
                print("    线段.刷新 特征后一笔 = None, ", 段, 有效特征序列)
        else:
            raise RuntimeError(len(有效特征序列))
        线段.获取内部中枢序列(段, 配置)

    @classmethod
    def 序列重置(cls, 段: 虚线, 序列: Sequence):
        基础序列 = []
        for 元素 in 段.基础序列:
            if 元素 not in 序列:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    break
            基础序列.append(元素)

        段.基础序列[:] = 基础序列[:]
        段.特征序列[2] = None

    @classmethod
    def 查找贯穿伤(cls, 段: 虚线) -> Optional[虚线]:
        for 贯穿伤 in 段.基础序列[3:]:
            if 段.方向.是否向上():
                if 贯穿伤.武.分型特征值 < 段.文.分型特征值:
                    return 贯穿伤
            else:
                if 贯穿伤.武.分型特征值 > 段.文.分型特征值:
                    return 贯穿伤
        return None

    @classmethod
    def 获取内部中枢序列(cls, 段: 虚线, 配置: 缠论配置) -> Tuple[List["中枢"], List["中枢"], List["中枢"]]:
        # 线段内部如存在中枢则级别比无中枢要大
        if 段.模式 != "文武":
            return [], [], []
        实, 虚, _, _ = 线段.分割序列(段)

        中枢.分析(实, 段.实_中枢序列, 标识=f"{段.标识}_{段.序号}_实_")
        中枢.分析(虚, 段.虚_中枢序列, 标识=f"{段.标识}_{段.序号}_虚_")
        中枢.分析(段.基础序列, 段.合_中枢序列, 标识=f"{段.标识}_{段.序号}_合_")
        return 段.虚_中枢序列, 段.实_中枢序列, 段.合_中枢序列  # 阴 阳 合

    @classmethod
    def 基础判断(cls, 左: 虚线, 中: 虚线, 右: 虚线, 关系序列: List[相对方向]) -> bool:
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
    def _添加线段(cls, 线段序列: List[虚线], 待添加线段: 虚线, 配置: 缠论配置, 行号: str):
        if 线段序列 and not 线段序列[-1].之后是(待添加线段):
            raise ValueError(f"线段.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)
        待添加线段.模式 = "文武"

        if not 线段序列:
            线段序列.append(待添加线段)
            return

        之前线段 = 线段序列[-1]

        if not 之前线段.特征序列[2] and not 之前线段.短路修正:
            assert not 待添加线段.短路修正 and 之前线段.特征序列[2][-1] in 待添加线段.基础序列
            raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段.右 = None", 之前线段)

        if 之前线段.基础序列[-1] not in 待添加线段.基础序列 and not 之前线段.短路修正:
            raise RuntimeError(f"线段._向序列中添加[{行号}], 之前线段[-1] not in 待添加虚线!", 之前线段)

        待添加线段.序号 = 之前线段.序号 + 1
        待添加线段.前一缺口 = 线段.获取缺口(之前线段)
        待添加线段.前一结束位置 = 之前线段.基础序列[-1]

        if 线段.四象(之前线段) in ("老阴", "老阳"):
            待添加线段.前一缺口 = None

        线段序列.append(待添加线段)
        # print(f"线段._向序列中添加[{行号}]", 待添加虚线)

    @classmethod
    def _弹出线段(cls, 线段序列: List[虚线], 待弹出线段: 虚线, 配置: 缠论配置, 行号: str):
        if not 线段序列:
            return None

        if 线段序列[-1] is not 待弹出线段:
            raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

        左, 中, 右 = 待弹出线段.特征序列
        if 右 is not None:
            结构 = 分型结构.分析(左, 中, 右, True, True)
            if 结构 in (分型结构.顶, 分型结构.底) and not 相对方向.分析(左.高, 左.低, 中.高, 中.低).是否缺口():
                print(colored(f"[警告<{行号}>]:", "yellow"), colored("线段._从序列中删除 发现分型完毕, 且特征序列无缺口", "red"), 待弹出线段)

        线段序列.pop()
        待弹出线段.前一结束位置 = None
        待弹出线段.有效性 = False

        return 待弹出线段

    @classmethod
    def _缺口突破(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        当前线段 = 线段序列[-1]
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

        # 执行修正
        序列 = 当前线段.基础序列[:]
        线段._弹出线段(线段序列, 当前线段, 配置, f"{sys._getframe().f_lineno}, {层级}")
        当前线段 = 线段序列[-1]
        assert 当前线段.特征序列[2] is not None
        当前线段基础序列 = 线段.分割序列(当前线段)[0]
        当前线段基础序列.extend(序列)

        当前线段.基础序列[:] = 当前线段基础序列[:]
        线段.刷新(当前线段, 配置)
        return True

    @classmethod
    def _非缺口下穿刺(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        当前线段 = 线段序列[-1]
        四象 = 线段.四象(当前线段)

        # 外层条件
        if not (配置.线段_非缺口下穿刺 and 四象 in ("小阳", "少阴") and 当前线段.特征序列[2] is None):
            return False

        # 查找贯穿伤
        贯穿伤 = 线段.查找贯穿伤(当前线段)
        if not 贯穿伤:
            return False

        # 切割基础序列
        基础序列 = 当前线段.基础序列[当前线段.基础序列.index(贯穿伤) :]

        # 长度条件
        if not (len(基础序列) == 4 and len(线段序列) >= 2):
            return False

        左, 中, 右 = 基础序列[-3], 基础序列[-2], 基础序列[-1]

        # 方向条件
        if 相对方向.分析(左.高, 左.低, 右.高, 右.低) is not 当前线段.方向:
            return False

        # 执行修正
        print(colored(f"[警告<{sys._getframe().f_lineno}, {层级}>]:", "yellow"), colored("线段.修复贯穿伤", "red"), 贯穿伤, 基础序列)  # 异常弹出

        基础序列 = 当前线段.基础序列[:]
        线段._弹出线段(线段序列, 当前线段, 配置, f"{sys._getframe().f_lineno}, {层级}")
        当前线段 = 线段序列[-1]
        当前线段.特征序列[2] = None
        for 临时虚线 in 基础序列[基础序列.index(当前线段.基础序列[-1]) + 1 :]:
            线段.添加虚线(当前线段, 临时虚线)
        线段.刷新(当前线段, 配置)

        if 当前线段.特征序列[2]:
            段 = 虚线.创建线段([左, 中, 右])
            线段._添加线段(线段序列, 段, 配置, f"{sys._getframe().f_lineno}, {层级}")
            段.特征序列[0] = 线段特征.新建([中], 段.方向)

        return True

    @classmethod
    def _缺口后紧急修正(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
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
        线段._添加线段(线段序列, 新段, 配置, f"{sys._getframe().f_lineno}, {层级}")
        return True

    @classmethod
    def _修正(cls, 线段序列: List[虚线], 配置: 缠论配置, 层级: int) -> bool:
        当前线段 = 线段序列[-1]

        # 条件1：配置允许修正且当前线段基础序列长度足够
        if not (配置.线段_修正 and len(当前线段.基础序列) >= 9):
            return False

        # 分割序列
        当前基础序列, 之后基础序列, _, _ = 线段.分割序列(当前线段)

        # 条件2：之后基础序列长度至少为6
        if len(之后基础序列) < 6:
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
        线段._添加线段(线段序列, 新段, 配置, f"{sys._getframe().f_lineno}, {层级}")

        # 根据当前线段的四象决定是否清空前一个缺口
        if 线段.四象(当前线段) in ("老阴", "老阳"):
            新段.前一缺口 = None

        # 创建第二个新段（最后3个元素）
        新段 = 虚线.创建线段(之后基础序列[-3:])
        线段._添加线段(线段序列, 新段, 配置, f"{sys._getframe().f_lineno}, {层级}")

        return True

    @classmethod
    def 分析(cls, 笔序列: List[虚线], 线段序列: List[虚线], 配置: 缠论配置, 层级: int = 0, 关系序列=[相对方向.向上, 相对方向.向下]) -> None:
        """
        注意笔序列前三个元素必须符合线段基本要求
        四象: 老阴，老阳，少阴，小阳
            老阴 老阳 分别代表 缺口顶分型后的向下线段 与 缺口底分型后的向上线段
            当其分型完成时需要对 线段.前一缺口 设置为None，新线段不在考虑之前是否有缺口的问题
        无缺口: 即笔破坏
            笔破坏不去处理特征序列的逆序包含
        """
        # 递归深度守卫
        if 层级 > 256:
            print("线段.分析 递归深度超出 256")
            return None
            # raise RuntimeError("线段分析 层级过深")

        线段递归分析 = 线段.分析

        # -------------------- 1. 初始化第一个线段 --------------------
        if not 线段序列:
            for i in range(1, len(笔序列) - 1):
                左, 中, 右 = 笔序列[i - 1], 笔序列[i], 笔序列[i + 1]
                if not 线段.基础判断(左, 中, 右, 关系序列):  # FIXME 首个线段必须有明确方向
                    continue
                段 = 虚线.创建线段([左, 中, 右])
                线段._添加线段(线段序列, 段, 配置, f"{sys._getframe().f_lineno}, {层级}")
                段.特征序列[0] = 线段特征.新建([中], 段.方向)
                break
            if not 线段序列:
                return None

        # -------------------- 2. 清理无效的尾部引用 --------------------
        while 线段序列 and 线段序列[-1].前一结束位置:
            if 线段序列[-1].前一结束位置 not in 笔序列:
                线段._弹出线段(线段序列, 线段序列[-1], 配置, f"{sys._getframe().f_lineno}, {层级}")
            else:
                break

        if not 线段序列:
            return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

        # -------------------- 3. 确保当前线段有效 --------------------
        当前线段 = 线段序列[-1]
        线段.序列重置(当前线段, 笔序列)

        if len(当前线段.基础序列) < 3:
            线段._弹出线段(线段序列, 当前线段, 配置, f"{sys._getframe().f_lineno}, {层级}")
            if not 线段序列:
                return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)

        当前线段 = 线段序列[-1]

        # -------------------- 4. 特征序列已完整时的处理 --------------------
        if 当前线段.特征序列[2] is not None:
            基础序列 = 线段.分割序列(当前线段)[1]
            新段 = 虚线.创建线段(基础序列)
            线段._添加线段(线段序列, 新段, 配置, f"{sys._getframe().f_lineno}, {层级}")
            if 线段.四象(当前线段) in ("老阴", "老阳"):
                新段.前一缺口 = None

        当前线段 = 线段序列[-1]
        线段.刷新(当前线段, 配置)

        # -------------------- 5. 调用一次全局修正（不循环） --------------------
        线段._缺口突破(线段序列, 配置, 层级)
        线段._非缺口下穿刺(线段序列, 配置, 层级)
        线段._缺口后紧急修正(线段序列, 配置, 层级)
        线段._修正(线段序列, 配置, 层级)

        # -------------------- 6. 循环处理后续的笔 --------------------
        当前线段 = 线段序列[-1]
        if not 当前线段.基础序列:
            raise RuntimeError
        起始索引 = 笔序列.index(当前线段.基础序列[-1]) + 1

        for 当前虚线 in 笔序列[起始索引:]:
            当前线段 = 线段序列[-1]
            四象 = 线段.四象(当前线段)

            线段.添加虚线(当前线段, 当前虚线)
            线段.刷新(当前线段, 配置)

            # 依次尝试四种修正，任意一个成功则跳过后续处理
            if 线段._缺口突破(线段序列, 配置, 层级):
                continue
            if 线段._非缺口下穿刺(线段序列, 配置, 层级):
                continue
            if 线段._缺口后紧急修正(线段序列, 配置, 层级):
                continue
            if 线段._修正(线段序列, 配置, 层级):
                continue

            # 无修正触发，且特征序列[2]已存在 → 创建新段
            if 当前线段.特征序列[2] is None:
                continue

            基础序列 = 线段.分割序列(当前线段)[1]
            新段 = 虚线.创建线段(基础序列)
            线段._添加线段(线段序列, 新段, 配置, f"{sys._getframe().f_lineno}, {层级}")
            if 四象 in ("老阴", "老阳"):
                新段.前一缺口 = None

            # 检查新段与当前虚线的连续性
            if 新段.基础序列[-1] is not 当前虚线:
                if not 新段.基础序列[-1].之后是(当前虚线):
                    return 线段递归分析(笔序列, 线段序列, 配置, 层级 + 1, 关系序列)
                线段.添加虚线(新段, 当前虚线)

            线段.刷新(新段, 配置)

        return None

    @classmethod
    def 武终(cls, 段: 虚线, 行号: int):
        if 段.模式 != "文武":
            线段.武斗(段, 段.基础序列[-1].武, 行号)

    @classmethod
    def 验证序列(cls, 段: 虚线, 序列: Sequence):
        基础序列 = []
        for 元素 in 段.基础序列:
            if 元素 not in 序列:
                break
            if 基础序列:
                if not 基础序列[-1].之后是(元素):
                    print("    线段._验证序列 数据不连续")
                    break
            基础序列.append(元素)
        段.基础序列[:] = 基础序列[:]
        if len(段.基础序列) % 2 == 0:
            段.基础序列 and 段.基础序列.pop()

    @classmethod
    def _添加扩展线段(cls, 线段序列: List[虚线], 待添加线段: 虚线, 行号: int):
        待添加线段.模式 = "高低"
        待添加线段.标识 = f"扩展{待添加线段.标识}" if 待添加线段.基础序列[0].标识 != "笔" else "扩展线段"
        if 线段序列 and not 线段序列[-1].之后是(待添加线段):
            raise ValueError(f"{线段序列[-1].标识}.向序列中添加 不连续[{行号}]", 线段序列[-1].武, 待添加线段.文)
        if 线段序列:
            之前线段 = 线段序列[-1]
            待添加线段.序号 = 之前线段.序号 + 1

        线段序列.append(待添加线段)
        # print(f"线段._向序列中添加[{行号}]", 待添加线段)

    @classmethod
    def _弹出扩展线段(cls, 线段序列: List[虚线], 待弹出线段: 虚线, 行号: int):
        if not 线段序列:
            return None

        if 线段序列[-1] is 待弹出线段:
            drop = 线段序列.pop()
            待弹出线段.有效性 = False
            # print(f"线段._从序列中删除[{行号}]", 待弹出线段)
            return drop
        raise ValueError("线段._从序列中删除 弹出数据不在列表中", 待弹出线段)

    @classmethod
    def 扩展分析(cls, 虚线序列: List[虚线], 线段序列: List[虚线], 配置: 缠论配置) -> None:
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

        if not 线段序列:
            for i in range(1, len(虚线序列) - 1):
                左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
                关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
                if 关系 not in (相对方向.向下, 相对方向.向上, 相对方向.顺, 相对方向.逆, 相对方向.同):  # FIXME 此处为首个线段
                    continue

                段 = 虚线.创建线段([左, 中, 右])
                线段._添加扩展线段(线段序列, 段, sys._getframe().f_lineno)
                break

        # 检查线段元素
        if not 线段序列:
            return None

        当前线段 = 线段序列[-1]
        线段.验证序列(当前线段, 虚线序列)
        if len(当前线段.基础序列) < 3:
            线段._弹出扩展线段(线段序列, 当前线段, sys._getframe().f_lineno)
            return 线段递归扩展分析(虚线序列, 线段序列, 配置)

        if not 配置.扩展线段_当下分析:
            左, 中, 右 = 当前线段.基础序列[:3]
            if not 相对方向.分析(左.高, 左.低, 右.高, 右.低).是否缺口():
                当前线段.基础序列[:] = 当前线段.笔序列[:3]
                线段.武终(当前线段, sys._getframe().f_lineno)
            else:
                线段._弹出扩展线段(线段序列, 当前线段, sys._getframe().f_lineno)
                return 线段递归扩展分析(虚线序列, 线段序列, 配置)

        线段.武终(当前线段, sys._getframe().f_lineno)
        if 当前线段.基础序列[-1].序号 + 3 > 虚线序列[-1].序号:
            return None

        序号 = 虚线序列.index(当前线段.基础序列[-1]) + 1
        if 序号 >= len(虚线序列):
            return None

        for i in range(序号 + 1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            相对关系 = 相对方向.分析(左.高, 左.低, 右.高, 右.低)
            if 相对关系.是否缺口():
                线段.添加虚线(当前线段, 左)
                线段.添加虚线(当前线段, 中)
                线段.武终(当前线段, sys._getframe().f_lineno)
                continue

            if 左 in 当前线段.基础序列:
                continue

            段 = 虚线.创建线段([左, 中, 右])
            线段._添加扩展线段(线段序列, 段, sys._getframe().f_lineno)
            return 线段递归扩展分析(虚线序列, 线段序列, 配置)


class 中枢(object):
    __slots__ = ["序号", "标识", "级别", "基础序列", "第三买卖线", "本级_第三买卖线"]

    def __init__(self, 序号: int, 标识: str, 级别: int, 基础序列: List[虚线]):
        self.基础序列 = 基础序列[:3]
        self.序号: int = 序号
        self.标识: str = 标识
        self.级别: int = 级别
        self.第三买卖线: Optional[虚线] = None
        self.本级_第三买卖线: Optional[虚线] = None

    def 添加虚线(self, 实线: 虚线):
        self.基础序列.append(实线)
        self.本级_第三买卖线 = None
        self.第三买卖线 = None

    def __str__(self):
        return f"{self.标识}({self.高:g}, {self.低:g}, 元素数量: {len(self.基础序列)}, {str(self.基础序列)}, {self.基础序列[0].文} ===>>> {self.基础序列[-1].武})"

    def __repr__(self):
        return str(self)

    @property
    def 图表标题(self) -> str:
        return f"{self.文.中.标识}:{self.文.中.周期}:{self.标识}:{self.序号}"

    @property
    def 离开段(self) -> 虚线:
        return self.基础序列[-1]

    @property
    def 方向(self) -> 相对方向:
        return self.基础序列[0].方向.翻转()

    @property
    def 高(self) -> float:
        return min(self.基础序列[:3], key=lambda o: o.高).高

    @property
    def 低(self) -> float:
        return max(self.基础序列[:3], key=lambda o: o.低).低

    @property
    def 高高(self) -> float:
        if len(self.基础序列) > 3:
            return max(self.基础序列, key=lambda o: o.高).高
        return max(self.基础序列, key=lambda o: o.高).高

    @property
    def 低低(self) -> float:
        if len(self.基础序列) > 3:
            return min(self.基础序列, key=lambda o: o.低).低
        return min(self.基础序列, key=lambda o: o.低).低

    @property
    def 文(self) -> 分型:
        return self.基础序列[0].文

    @property
    def 武(self) -> 分型:
        return self.基础序列[-1].武

    def 获取数据文本(self):
        return f"{self.标识}, {self.序号}, {self.级别}, 文:({int(self.文.时间戳.timestamp())},{self.文.分型特征值:g}), 武:({int(self.武.时间戳.timestamp())},{self.武.分型特征值:g}), {self.第三买卖线}, {self.本级_第三买卖线}"

    def 完整性(self, 虚实: str = "合"):
        """

        详情见 教你炒股票 43：有关背驰的补习课(2007-04-06 15:31:28)
        不完整时 下一个中枢大概率会与当前中枢发生扩展！

        """
        if self.基础序列[0].标识 == "笔":
            # 笔中枢
            return self.第三买卖线 is not None

        else:
            # if self.本级_第三买卖线:
            #     return True
            线段内部中枢 = self.基础序列[-1].合_中枢序列 if 虚实 == "合" else self.基础序列[-1].实_中枢序列
            for 内部中枢 in 线段内部中枢:
                if 相对方向.分析(self.高, self.低, 内部中枢.高, 内部中枢.低).是否缺口():
                    return True
        return False

    def 获取序列(self) -> List[虚线]:
        序列: List = self.基础序列[:]
        if self.第三买卖线 is not None:
            序列.append(self.第三买卖线)
        return 序列

    def 获取扩展中枢(self, 扩展中枢: List, 配置: 缠论配置):
        if len(self.基础序列) >= 9:
            扩展线段 = []
            线段.扩展分析(self.基础序列, 扩展线段, 配置)
            中枢.分析(扩展线段, 扩展中枢, False, f"{self.标识}_扩展中枢_")

    def 校验合法性(self, 序列: Sequence[虚线], 中枢序列) -> bool:
        有效序列 = self.基础序列[:]
        无效序列 = []
        for 元素 in self.基础序列:
            if 元素 not in 序列:
                无效序列.append(元素)

        if 无效序列:
            无效 = 无效序列[0]
            序号 = self.基础序列.index(无效)
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
                        self.添加虚线(self.第三买卖线)
                        self.设置第三买卖线(None)

            else:
                self.设置第三买卖线(None)
        return True

    def 设置第三买卖线(self, 线: Union[虚线, None]):
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
        尾部 = self.基础序列[-1].武 if self.基础序列[-1].标识 == "笔" else self.基础序列[-1].基础序列[-1].武
        关系 = 相对方向.分析(self.高, self.低, 尾部.中.高, 尾部.中.低)
        if 关系 is 相对方向.向上缺口:
            状态 = "中枢之上"
        elif 关系 is 相对方向.向下缺口:
            状态 = "中枢之下"
        return 状态

    @classmethod
    def 基础检查(cls, 左: 虚线, 中: 虚线, 右: 虚线) -> bool:
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
    def 创建(cls, 左: 虚线, 中: 虚线, 右: 虚线, 级别: int, 标识: str = "") -> "中枢":
        assert 中枢.基础检查(左, 中, 右)
        return 中枢(
            序号=0,
            标识=f"{标识}中枢<{中.标识}>",
            基础序列=[左, 中, 右],
            级别=级别,
        )

    @classmethod
    def 从序列中获取中枢(cls, 虚线序列: Sequence[虚线], 起始方向: 相对方向, 标识: str) -> Optional["中枢"]:
        if len(虚线序列) < 3:
            return None

        for i in range(1, len(虚线序列) - 1):
            左, 中, 右 = 虚线序列[i - 1], 虚线序列[i], 虚线序列[i + 1]
            if 中枢.基础检查(左, 中, 右):
                if 左.方向 is 起始方向:
                    return 中枢.创建(左, 中, 右, 级别=0, 标识=标识)

        return None

    @classmethod
    def 向中枢序列尾部添加(cls, 中枢序列: List["中枢"], 待添加中枢: "中枢"):
        if 中枢序列:
            待添加中枢.序号 = 中枢序列[-1].序号 + 1
            if 中枢序列[-1].获取序列()[-1].序号 > 待添加中枢.获取序列()[-1].序号:
                raise ValueError()
        中枢序列.append(待添加中枢)

    @classmethod
    def 从中枢序列尾部弹出(cls, 中枢序列: List["中枢"], 待弹出中枢: "中枢") -> Optional["中枢"]:
        if not 中枢序列:
            return None
        if 中枢序列[-1] is 待弹出中枢:
            return 中枢序列.pop()
        return None

    @classmethod
    def 分析(cls, 虚线序列: Sequence[虚线], 中枢序列: List["中枢"], 跳过首部: bool = True, 标识: str = "", 层级: int = 0) -> None:
        if len(虚线序列) < 3:
            return None

        中枢递归分析 = 中枢.分析

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

                    中枢.向中枢序列尾部添加(中枢序列, 新中枢)
                    return 中枢递归分析(虚线序列, 中枢序列, 跳过首部, 标识, 层级 + 1)

            return None

        当前中枢 = 中枢序列[-1]

        if not 当前中枢.校验合法性(虚线序列, 中枢序列):
            中枢.从中枢序列尾部弹出(中枢序列, 当前中枢)
            return 中枢递归分析(虚线序列, 中枢序列, 跳过首部, 标识, 层级 + 1)

        序号 = 虚线序列.index(当前中枢.基础序列[-1]) + 1

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
                    当前中枢.添加虚线(当前虚线)
                else:
                    基础序列.append(当前虚线)

            while len(基础序列) >= 3:
                新中枢 = 中枢.从序列中获取中枢(基础序列, 当前中枢.基础序列[-1].方向.翻转(), 标识)
                if 新中枢 is None:
                    基础序列.pop(0)
                else:
                    中枢.向中枢序列尾部添加(中枢序列, 新中枢)
                    当前中枢 = 新中枢
                    基础序列 = []
        return None


class 观察者:
    def __init__(self, 符号: str, 周期: int, 配置: 缠论配置):
        配置.标识 = 符号
        self.符号: str = 符号
        self.周期: int = int(周期)
        self.配置: 缠论配置 = 配置
        self.__终止时间戳: Optional[datetime] = 转化为时间戳(self.配置.手动终止) if self.配置.手动终止 else None

        self.重置基础序列()

    @property
    def 观察员(self):
        return self  # 用于兼容 chanlun.c99

    @property
    def 标识(self) -> str:
        return f"{self.符号}:{self.周期}"

    @property
    def 当前K线(self) -> Optional["K线"]:
        return self.普通K线序列[-1] if self.普通K线序列 else None

    @property
    def 当前缠K(self) -> Optional["缠论K线"]:
        return self.缠论K线序列[-1] if self.缠论K线序列 else None

    def 重置基础序列(self):
        self.基础缠K序列: List[缠论K线] = []

        self.普通K线序列: List[K线] = []
        self.缠论K线序列: List[缠论K线] = []

        self.分型序列: List[分型] = []

        self.笔序列: List[虚线] = []
        self.笔_中枢序列: List[中枢] = []

        self.线段序列: List[虚线] = []
        self.中枢序列: List[中枢] = []

        self.扩展线段序列: List[虚线] = []
        self.扩展中枢序列: List[中枢] = []

        self.扩展线段序列_线段: List[虚线] = []
        self.扩展中枢序列_线段: List[中枢] = []

        self.线段_线段序列: List[虚线] = []
        self.线段_中枢序列: List[中枢] = []

        self.扩展线段序列_扩展线段: List[虚线] = []
        self.扩展中枢序列_扩展线段: List[中枢] = []

    @final
    def 增加原始K线(self, 普K: K线):
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

        self.配置.分析笔中枢 and 中枢.分析(self.笔序列, self.笔_中枢序列)
        if not self.笔序列:
            return

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

    def 测试_保存数据(self):
        """拆分各序列数据，单独存文件，文件名为对应变量名"""
        # 提取各类文本数据
        笔序列_文本数据 = [筆.获取数据文本() for 筆 in self.笔序列]
        线段序列_文本数据 = [实线.获取数据文本() for 实线 in self.线段序列]
        扩展线段序列_数据文本 = [实线.获取数据文本() for 实线 in self.扩展线段序列]
        扩展线段序列_线段_数据文本 = [实线.获取数据文本() for 实线 in self.扩展线段序列_线段]
        线段_线段序列_数据文本 = [实线.获取数据文本() for 实线 in self.线段_线段序列]
        扩展线段序列_扩展线段_数据文本 = [实线.获取数据文本() for 实线 in self.扩展线段序列_扩展线段]

        笔_中枢序列_数据文本 = [当前中枢.获取数据文本() for 当前中枢 in self.笔_中枢序列]
        中枢序列_数据文本 = [当前中枢.获取数据文本() for 当前中枢 in self.中枢序列]
        扩展中枢序列_数据文本 = [当前中枢.获取数据文本() for 当前中枢 in self.扩展中枢序列]
        扩展中枢序列_线段_数据文本 = [当前中枢.获取数据文本() for 当前中枢 in self.扩展中枢序列_线段]
        线段_中枢序列_数据文本 = [当前中枢.获取数据文本() for 当前中枢 in self.线段_中枢序列]
        扩展中枢序列_扩展线段_数据文本 = [当前中枢.获取数据文本() for 当前中枢 in self.扩展中枢序列_扩展线段]

        # 生成存储根目录
        脚本目录 = Path(__file__).parent  # 取当前脚本所在文件夹
        起始时间 = int(self.普通K线序列[0].时间戳.timestamp())
        结束时间 = int(self.普通K线序列[-1].时间戳.timestamp())
        目录标识 = f"Py_{self.标识}_{起始时间}_{结束时间}"

        # 最终保存路径 = 脚本目录 / 自动生成的文件夹
        保存路径 = 脚本目录 / 目录标识
        保存路径.mkdir(exist_ok=True)

        # 映射：变量名 -> 数据列表
        数据映射 = [
            ("笔序列_文本数据", 笔序列_文本数据),
            ("线段序列_文本数据", 线段序列_文本数据),
            ("扩展线段序列_数据文本", 扩展线段序列_数据文本),
            ("扩展线段序列_线段_数据文本", 扩展线段序列_线段_数据文本),
            ("线段_线段序列_数据文本", 线段_线段序列_数据文本),
            ("扩展线段序列_扩展线段_数据文本", 扩展线段序列_扩展线段_数据文本),
            ("笔_中枢序列_数据文本", 笔_中枢序列_数据文本),
            ("中枢序列_数据文本", 中枢序列_数据文本),
            ("扩展中枢序列_数据文本", 扩展中枢序列_数据文本),
            ("扩展中枢序列_线段_数据文本", 扩展中枢序列_线段_数据文本),
            ("线段_中枢序列_数据文本", 线段_中枢序列_数据文本),
            ("扩展中枢序列_扩展线段_数据文本", 扩展中枢序列_扩展线段_数据文本),
        ]

        # 逐个写入独立文件
        for 文件名, 数据列表 in 数据映射:
            文件全路径 = 保存路径 / f"{文件名}.txt"
            with open(文件全路径, "w", encoding="utf-8") as f:
                f.write("\n".join(数据列表))
                f.write("\n")  # 向 C99 对齐
        print(f"全部数据拆分保存完成，目录：{保存路径.resolve()}")

    def 识别买卖点(self):
        pass

    @classmethod
    def 读取数据文件(cls, 文件路径: str, 配置=缠论配置()) -> Self:
        # btcusd-300-1631772074-1632222374.nb
        name = Path(文件路径).name.split(".")[0]
        符号, 周期, 起始时间戳, 结束时间戳 = name.split("-")
        实例 = cls(符号=符号, 周期=int(周期), 配置=配置)

        with open(文件路径, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], int(周期))
                实例.增加原始K线(k线)

        return 实例


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
            当前K线.序号 = self.合成K线列表[周期][-1].序号 + 1

        self.合成K线列表[周期].append(当前K线)

        # 新增：产生完成K线信号
        self._产生完成K线信号(周期, 当前K线)

    def _产生完成K线信号(self, 周期: int, 完成K线: K线):
        """产生K线完成信号"""
        if self.事件回调:
            try:
                self.事件回调(信号类型="K线完成", 标识=self.标识, 周期=周期, 完成K线=完成K线)
            except Exception as e:
                print(f"K线合成器信号回调错误: {e}")

    def 获取当前K线(self, 周期: int) -> Optional[K线]:
        """获取指定周期当前正在合成的K线"""
        return self.当前K线[周期]


class 立体分析器:
    def __init__(self, 符号: str, 周期组: List[int], 配置: 缠论配置 = 缠论配置(), 配置组: Dict[int, 缠论配置] = dict()):
        self.周期组 = 周期组

        self.__输入周期 = self.周期组[0]  # 最小输入K线周期
        self.__显示周期 = self.周期组[1]
        self._K线合成器 = K线合成器(符号, self.周期组, self.__K线回调)

        self._单体分析器 = dict()
        for 周期 in self.周期组:
            临时配置 = 配置组.get(周期, 配置)
            当前配置 = 临时配置.model_copy(
                update={
                    "推送K线": False,
                    # "推送笔": False,
                    "推送线段": False,
                    # "图表展示": False,
                },
                deep=True,
            )
            self._单体分析器[周期] = 观察者(符号=符号, 周期=周期, 配置=当前配置)

        self._单体分析器[self.__显示周期].配置.推送K线 = True
        self._单体分析器[self.__显示周期].配置.推送笔 = True
        self._单体分析器[self.__显示周期].配置.推送线段 = True
        self._单体分析器[self.__显示周期].配置.图表展示 = True
        self._单体分析器[self.__显示周期].重置基础序列()

        for 周期 in self.周期组:  # 将不同周期对其至显示周期
            if 周期 != self.__显示周期:
                self._单体分析器[周期].基础缠K序列 = self._单体分析器[self.__显示周期].缠论K线序列

    def 投喂K线(self, 普K: K线):
        if 普K.周期 != self.__输入周期:
            raise RuntimeError("立体分析器.投喂K线", 普K.周期, self.__输入周期)
        self._K线合成器.投喂K线(普K)

    def __K线回调(self, 信号类型: str, 标识: str, 周期: int, 完成K线: K线):
        self._单体分析器[周期].增加原始K线(完成K线)
        if 当前K线 := self._K线合成器.获取当前K线(周期):
            self._单体分析器[周期].增加原始K线(当前K线)


def 测试_读取数据(配置: 缠论配置):
    def 魔法():
        启动时间 = datetime.now()
        观察员 = 观察者.读取数据文件(配置.加载文件路径, 配置)
        消耗用时 = datetime.now() - 启动时间
        print("测试_读取数据 耗时", 消耗用时, "普K数量", len(观察员.普通K线序列))
        return 观察员

    return 魔法


def 测试_周期合成(配置: 缠论配置, 配置组: Dict[int, 缠论配置] = dict()):
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
                k线 = K线.读取大端字节数组(buffer[i * size : i * size + size], 周期)
                多级别分析.投喂K线(k线)
        消耗用时 = datetime.now() - 启动时间
        print("测试_周期合成", 消耗用时, "普K数量", len(多级别分析._单体分析器[周期].普通K线序列))
        return 多级别分析

    return 魔法


if __name__ == "__main__":
    当前配置 = 缠论配置.不推送()
    当前配置.加载文件路径 = "./btcusd-300-1761327300-1776327900.nb"
    测试_读取数据(当前配置)().测试_保存数据()
    # 测试_周期合成(当前配置)()
