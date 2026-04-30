import random
from random import seed, randint, uniform, choice, choices
import os
import math
import traceback
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    List,
    Optional,
    Tuple,
    SupportsInt,
    Generator,
)

from fastapi import WebSocket
from pydantic import BaseModel


from chan import *


def 随机配置(随机源: Optional[random.Random] = None):
    """生成随机缠论配置，可传入独立的 Random 实例以保证线程安全"""
    rng = 随机源 if 随机源 is not None else random.Random()
    return 缠论配置.from_dict(
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
            "扩展线段_当下分析": rng.choice((True, False)),
            "买卖点激进识别": rng.choice((True, False)),
            "买卖点与MACD柱强相关": rng.choice((True, False)),
        }
    )


class 笔K线生成配置(BaseModel):
    """笔的K线生成配置"""

    最小K线数量: int = 5  # 一笔至少需要的K线数量
    最大K线数量: int = 20  # 一笔最多K线数量
    波动比例: float = 0.1  # 内部波动比例（相对于笔长度）
    包含K线比例: float = 0.3  # 包含关系K线比例
    缺口概率: float = 0.1  # 出现缺口的概率
    随机种子: Optional[int] = None  # 随机种子（可重复）


class 笔结构类型(Enum):
    标准上涨笔 = "标准上涨笔"  # 低->高，内部有回调
    标准下跌笔 = "标准下跌笔"  # 高->低，内部有反弹
    单边上扬笔 = "单边上扬笔"  # 几乎直线上升
    单边下跌笔 = "单边下跌笔"  # 几乎直线下降
    震荡上涨笔 = "震荡上涨笔"  # 大幅波动上升
    震荡下跌笔 = "震荡下跌笔"  # 大幅波动下降


class 笔K线生成器:
    """
    根据笔的顶底数值生成K线序列
    """

    def __init__(self, 配置: 笔K线生成配置 = 笔K线生成配置(), 分析器: Optional["观察者"] = None):
        self.配置 = 配置
        self.分析器 = 分析器
        if 配置.随机种子:
            seed(配置.随机种子)

    def _验证顶底交替(self, 顶底序列: List[float]) -> None:
        """
        验证顶底序列是否交替（高点-低点-高点 或 低点-高点-低点）
        这是缠论笔的基本要求
        """
        if len(顶底序列) < 3:
            return  # 至少3个点才能验证交替

        for i in range(1, len(顶底序列) - 1):
            左 = 顶底序列[i - 1]
            中 = 顶底序列[i]
            右 = 顶底序列[i + 1]

            # 检查是否形成分型
            # 如果中是高点，左右应该是低点
            if 中 > 左 and 中 > 右:
                # 中点是高点，左右应该是低点
                if not (左 < 中 and 右 < 中):
                    print(f"警告：位置{i}可能不是有效高点，左:{左}, 中:{中}, 右:{右}")
            elif 中 < 左 and 中 < 右:
                # 中点是低点，左右应该是高点
                if not (左 > 中 and 右 > 中):
                    print(f"警告：位置{i}可能不是有效低点，左:{左}, 中:{中}, 右:{右}")
            else:
                # 既不是高点也不是低点，不符合顶底交替
                raise ValueError(f"顶底序列不交替，位置{i}: 左={左}, 中={中}, 右={右}\n序列应该交替出现高点和低点")

    def 生成K线序列(self, 顶底序列: List[float], 起始时间: datetime, 周期: int = 60) -> List[K线]:
        """
        根据顶底序列生成完整的K线序列
        """
        if len(顶底序列) < 2:
            raise ValueError("顶底序列至少需要2个点")

        # 确保顶底交替（可选，如果确定序列是标准的可以跳过）
        try:
            self._验证顶底交替(顶底序列)
        except ValueError as e:
            print(f"顶底序列验证失败，但仍继续生成: {e}")
            # 可以选择继续，或者处理成更标准的序列

        K线序列 = []
        当前时间 = 起始时间

        # 生成每段笔的K线
        for i in range(len(顶底序列) - 1):
            起点价格 = 顶底序列[i]
            终点价格 = 顶底序列[i + 1]

            # 判断笔方向
            if 起点价格 < 终点价格:
                笔类型 = 笔结构类型.标准上涨笔
            else:
                笔类型 = 笔结构类型.标准下跌笔

            # 生成这笔的K线
            笔K线 = self._生成单笔K线(起点价格, 终点价格, 笔类型, 当前时间, 周期)

            # 添加到总序列
            K线序列.extend(笔K线)

            # 更新时间（最后一个K线的时间 + 周期）
            if 笔K线:
                当前时间 = 笔K线[-1].时间戳 + timedelta(seconds=周期)

            if self.分析器:
                for k线 in 笔K线:
                    self.分析器.增加原始K线(k线)

        return K线序列

    def _生成单笔K线(self, 起点: float, 终点: float, 笔类型: 笔结构类型, 起始时间: datetime, 周期: int) -> List[K线]:
        """
        生成单笔的内部K线结构
        """
        # 确定K线数量
        K线数量 = randint(self.配置.最小K线数量, self.配置.最大K线数量)

        # 计算笔的总幅度
        总幅度 = abs(终点 - 起点)

        # 根据笔类型选择生成策略
        if 笔类型 in [笔结构类型.标准上涨笔, 笔结构类型.标准下跌笔]:
            return self._生成标准笔K线(起点, 终点, K线数量, 起始时间, 周期, 笔类型)
        elif 笔类型 in [笔结构类型.单边上扬笔, 笔结构类型.单边下跌笔]:
            return self._生成单边笔K线(起点, 终点, K线数量, 起始时间, 周期, 笔类型)
        else:  # 震荡笔
            return self._生成震荡笔K线(起点, 终点, K线数量, 起始时间, 周期, 笔类型)

    def _生成标准笔K线(self, 起点: float, 终点: float, K线数量: int, 起始时间: datetime, 周期: int, 笔类型: 笔结构类型) -> List[K线]:
        """
        生成标准笔的K线（有回调/反弹）
        """
        K线列表 = []
        当前价格 = 起点
        当前时间 = 起始时间

        # 计算每步的基础变动
        总变动 = 终点 - 起点
        基础步长 = 总变动 / (K线数量 - 1) if K线数量 > 1 else 总变动

        # 确定主要方向
        是上涨笔 = 笔类型 == 笔结构类型.标准上涨笔

        # 生成每根K线
        for i in range(K线数量):
            # 基础目标价格（线性）
            基础目标 = 起点 + 基础步长 * i

            # 添加波动
            if i == 0 or i == K线数量 - 1:
                # 起点和终点波动小
                波动范围 = abs(总变动) * 0.02
            else:
                # 中间波动大
                波动范围 = abs(总变动) * self.配置.波动比例

            # 生成K线的四个价格
            if 是上涨笔:
                开, 高, 低, 收 = self._生成上涨K线价格(基础目标, 波动范围, i, K线数量)
            else:
                开, 高, 低, 收 = self._生成下跌K线价格(基础目标, 波动范围, i, K线数量)

            # 确保起点和终点准确
            if i == 0:
                if 是上涨笔:
                    低 = min(低, 起点)
                    开 = 起点  # 上涨笔起点是低点
                    收 = max(开, 收)  # 确保上涨
                else:
                    高 = max(高, 起点)
                    开 = 起点  # 下跌笔起点是高点
                    收 = min(开, 收)  # 确保下跌

            elif i == K线数量 - 1:
                if 是上涨笔:
                    高 = max(高, 终点)
                    收 = 终点  # 上涨笔终点是高点
                else:
                    低 = min(低, 终点)
                    收 = 终点  # 下跌笔终点是低点

            # 创建K线
            k线 = K线.创建普K(
                标识="随机",
                序号=len(K线列表),
                时间戳=当前时间,
                开盘价=开,
                最高价=高,
                最低价=低,
                收盘价=收,
                成交量=uniform(100, 1000),
                周期=周期,
            )

            K线列表.append(k线)
            当前时间 += timedelta(seconds=周期)
            当前价格 = 收

        # 后处理：确保笔的起点和终点准确
        if K线列表:
            self._修正笔端点(K线列表, 起点, 终点, 是上涨笔)

        return K线列表

    def _生成单边笔K线(self, 起点: float, 终点: float, K线数量: int, 起始时间: datetime, 周期: int, 笔类型: 笔结构类型) -> List[K线]:
        """
        生成单边笔的K线（几乎直线上升/下降，回调很小）
        """
        K线列表 = []
        当前时间 = 起始时间

        # 确定方向
        是上涨笔 = 笔类型 == 笔结构类型.单边上扬笔

        # 计算总变动和每步变动
        总变动 = 终点 - 起点

        for i in range(K线数量):
            # 线性进展
            进度 = i / max(K线数量 - 1, 1)
            基础价格 = 起点 + 总变动 * 进度

            # 单边笔的波动很小
            波动范围 = abs(总变动) * 0.01  # 只有1%的波动

            # 生成K线价格
            if 是上涨笔:
                # 上涨笔：大部分是阳线
                if random.random() < 0.8:  # 80%阳线
                    开 = 基础价格 - 波动范围 * 0.2
                    收 = 基础价格 + 波动范围 * 0.3
                else:
                    开 = 基础价格 + 波动范围 * 0.2
                    收 = 基础价格 - 波动范围 * 0.1
            else:
                # 下跌笔：大部分是阴线
                if random.random() < 0.8:  # 80%阴线
                    开 = 基础价格 + 波动范围 * 0.2
                    收 = 基础价格 - 波动范围 * 0.3
                else:
                    开 = 基础价格 - 波动范围 * 0.2
                    收 = 基础价格 + 波动范围 * 0.1

            # 计算高低点
            高 = max(开, 收) + 波动范围 * 0.1
            低 = min(开, 收) - 波动范围 * 0.1

            # 修正第一根和最后一根
            if i == 0:
                if 是上涨笔:
                    低 = min(低, 起点)
                    开 = 起点
                else:
                    高 = max(高, 起点)
                    开 = 起点
            elif i == K线数量 - 1:
                if 是上涨笔:
                    高 = max(高, 终点)
                    收 = 终点
                else:
                    低 = min(低, 终点)
                    收 = 终点

            # 创建K线
            k线 = K线.创建普K(
                标识="随机",
                序号=len(K线列表),
                时间戳=当前时间,
                开盘价=开,
                最高价=高,
                最低价=低,
                收盘价=收,
                成交量=uniform(80, 600),
                周期=周期,
            )

            K线列表.append(k线)
            当前时间 += timedelta(seconds=周期)

        return K线列表

    def _生成震荡笔K线(self, 起点: float, 终点: float, K线数量: int, 起始时间: datetime, 周期: int, 笔类型: 笔结构类型) -> List[K线]:
        """
        生成震荡笔的K线（大幅波动上升/下降）
        """
        K线列表 = []
        当前时间 = 起始时间

        # 确定方向
        是上涨笔 = 笔类型 == 笔结构类型.震荡上涨笔

        # 计算总变动
        总变动 = 终点 - 起点

        # 震荡笔有较大的回调
        回调深度 = abs(总变动) * 0.3  # 回调30%

        for i in range(K线数量):
            # 基础线性进展
            基础进度 = i / max(K线数量 - 1, 1)
            基础价格 = 起点 + 总变动 * 基础进度

            # 添加较大的震荡
            震荡幅度 = abs(总变动) * 0.15  # 15%的震荡

            # 正弦波模拟震荡
            if K线数量 > 1:
                震荡 = math.sin(i * 2 * math.pi / K线数量) * 震荡幅度
            else:
                震荡 = 0

            震荡价格 = 基础价格 + 震荡

            # 生成K线价格
            波动范围 = abs(总变动) * 0.1
            if 是上涨笔:
                # 震荡上涨：随机阴阳线
                if random.random() < 0.5:
                    开 = 震荡价格 - 波动范围 * 0.4
                    收 = 震荡价格 + 波动范围 * 0.3
                else:
                    开 = 震荡价格 + 波动范围 * 0.3
                    收 = 震荡价格 - 波动范围 * 0.2
            else:
                # 震荡下跌：随机阴阳线
                if random.random() < 0.5:
                    开 = 震荡价格 + 波动范围 * 0.4
                    收 = 震荡价格 - 波动范围 * 0.3
                else:
                    开 = 震荡价格 - 波动范围 * 0.3
                    收 = 震荡价格 + 波动范围 * 0.2

            # 计算高低点（震荡笔的高低点差异大）
            高 = max(开, 收) + 波动范围 * 0.3
            低 = min(开, 收) - 波动范围 * 0.3

            # 修正端点
            if i == 0:
                if 是上涨笔:
                    低 = min(低, 起点)
                    开 = 起点
                else:
                    高 = max(高, 起点)
                    开 = 起点
            elif i == K线数量 - 1:
                if 是上涨笔:
                    高 = max(高, 终点)
                    收 = 终点
                else:
                    低 = min(低, 终点)
                    收 = 终点

            # 创建K线
            k线 = K线.创建普K(
                标识="随机",
                序号=len(K线列表),
                时间戳=当前时间,
                开盘价=开,
                最高价=高,
                最低价=低,
                收盘价=收,
                成交量=uniform(150, 1200),
                周期=周期,
            )

            K线列表.append(k线)
            当前时间 += timedelta(seconds=周期)

        return K线列表

    def _生成上涨K线价格(self, 基础价: float, 波动范围: float, 索引: int, 总数: int) -> Tuple[float, float, float, float]:
        """
        生成上涨笔中的单根K线价格
        """
        # 确定K线类型
        if 索引 == 0:
            # 第一根：通常是阳线
            K线类型 = "阳线"
        elif 索引 == 总数 - 1:
            # 最后一根：可能是阴线（形成顶分型）
            K线类型 = choice(["阳线", "阴线"])
        else:
            # 中间：随机，但偏阳线
            K线类型 = choices(["阳线", "阴线", "十字星"], weights=[0.6, 0.3, 0.1])[0]

        # 生成价格
        波动 = uniform(-波动范围, 波动范围)
        中心价 = 基础价 + 波动

        if K线类型 == "阳线":
            # 低开高收
            开 = 中心价 - 波动范围 * 0.3
            收 = 中心价 + 波动范围 * 0.3
        elif K线类型 == "阴线":
            # 高开低收
            开 = 中心价 + 波动范围 * 0.3
            收 = 中心价 - 波动范围 * 0.3
        else:  # 十字星
            开 = 中心价 - 波动范围 * 0.1
            收 = 中心价 + 波动范围 * 0.1

        # 计算高低点
        低 = min(开, 收) - 波动范围 * 0.2
        高 = max(开, 收) + 波动范围 * 0.2

        # 确保高低点合理
        if 高 <= 低:
            高, 低 = 低 + 波动范围 * 0.1, 高 - 波动范围 * 0.1

        return 开, 高, 低, 收

    def _生成下跌K线价格(self, 基础价: float, 波动范围: float, 索引: int, 总数: int) -> Tuple[float, float, float, float]:
        """
        生成下跌笔中的单根K线价格
        """
        if 索引 == 0:
            K线类型 = "阴线"  # 第一根通常是阴线
        elif 索引 == 总数 - 1:
            K线类型 = choice(["阴线", "阳线"])  # 最后一根可能阳线
        else:
            K线类型 = choices(["阴线", "阳线", "十字星"], weights=[0.6, 0.3, 0.1])[0]

        波动 = uniform(-波动范围, 波动范围)
        中心价 = 基础价 + 波动

        if K线类型 == "阴线":
            开 = 中心价 + 波动范围 * 0.3
            收 = 中心价 - 波动范围 * 0.3
        elif K线类型 == "阳线":
            开 = 中心价 - 波动范围 * 0.3
            收 = 中心价 + 波动范围 * 0.3
        else:  # 十字星
            开 = 中心价 - 波动范围 * 0.1
            收 = 中心价 + 波动范围 * 0.1

        低 = min(开, 收) - 波动范围 * 0.2
        高 = max(开, 收) + 波动范围 * 0.2

        if 高 <= 低:
            高, 低 = 低 + 波动范围 * 0.1, 高 - 波动范围 * 0.1

        return 开, 高, 低, 收

    def _修正笔端点(self, K线列表: List[K线], 起点: float, 终点: float, 是上涨笔: bool):
        """
        修正笔的起点和终点，确保准确
        """
        if not K线列表:
            return

        # 修正起点
        第一根 = K线列表[0]
        if 是上涨笔:
            第一根.低 = min(第一根.低, 起点)
            第一根.开盘价 = 起点
            第一根.收盘价 = max(第一根.收盘价, 第一根.开盘价)
        else:
            第一根.高 = max(第一根.高, 起点)
            第一根.开盘价 = 起点
            第一根.收盘价 = min(第一根.收盘价, 第一根.开盘价)

        # 修正终点
        最后一根 = K线列表[-1]
        if 是上涨笔:
            最后一根.高 = max(最后一根.高, 终点)
            最后一根.收盘价 = 终点
        else:
            最后一根.低 = min(最后一根.低, 终点)
            最后一根.收盘价 = 终点




def 测试_读取数据(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置(线段内部中枢图显=False), 文件路径: str = "./templates/btcusd_ex-1800-1685795400-1713488400.nb"):
    def 魔法():
        观察员 = 观察者.读取数据文件(文件路径, ws)
        观察员.图表刷新()
        return 观察员

    return 魔法


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
        yield from random.sample(可选方向, 数量)  # 使用random.sample


def 根据当前K线生成新K线(self, 方向: 相对方向, 居中: bool = False) -> "K线":
    时间偏移 = timedelta(seconds=self.周期)
    时间戳: datetime = self.时间戳 + 时间偏移
    成交量: float = 998
    高: float = 0
    低: float = 0
    高低差 = self.高 - self.低
    match 方向:
        case 相对方向.向上:
            偏移 = 高低差 * 0.5 if 居中 else randint(int(高低差 * 0.1279), int(高低差 * 0.883))
            低 = self.低 + 偏移
            高 = self.高 + 偏移
        case 相对方向.向下:
            偏移 = 高低差 * 0.5 if 居中 else randint(int(高低差 * 0.1279), int(高低差 * 0.883))
            低 = self.低 - 偏移
            高 = self.高 - 偏移
        case 相对方向.向上缺口:
            偏移 = 高低差 * 1.5 if 居中 else randint(int(高低差 * 1.1279), int(高低差 * 1.883))
            低 = self.低 + 偏移
            高 = self.高 + 偏移
        case 相对方向.向下缺口:
            偏移 = 高低差 * 1.5 if 居中 else randint(int(高低差 * 1.1279), int(高低差 * 1.883))
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
        开盘价=round(uniform(高, 低), max(小数点)),
        最高价=round(高, max(小数点)),
        最低价=round(低, max(小数点)),
        收盘价=round(uniform(高, 低), max(小数点)),
        成交量=成交量 * random.random(),
        序号=self.序号 + 1,
        周期=self.周期,
    )

    # assert 相对方向.分析(self, 新K线) is 方向, (方向, 相对方向.分析(self, 新K线))
    return 新K线


def 测试_随机生成(symbol: str = "btcusd", limit: int = 5000, freq: SupportsInt = 时间周期.分(5), ws: Optional[WebSocket] = None, 配置: 缠论配置 = 缠论配置()):
    def 魔法():
        随机生成实例 = 观察者(symbol + "_gen", 周期=int(freq), 数据通道=ws, 配置=配置)
        dt = datetime(2008, 8, 8)
        原始K线 = K线.创建普K("随机", dt, 8888.55, 10000.00, 9000.22, 9527.33, 888, 0, int(freq))
        随机生成实例.增加原始K线(原始K线)
        for 方向 in 从序列中机选(
            int(limit),
            [相对方向.向上, 相对方向.向上缺口, 相对方向.衔接向上, 相对方向.向下, 相对方向.向下缺口, 相对方向.衔接向下],
        ):
            原始K线 = 根据当前K线生成新K线(原始K线, 方向)
            随机生成实例.增加原始K线(原始K线)

        折线 = [元素.文.分型特征值 for 元素 in 随机生成实例.笔序列]
        折线.append(随机生成实例.笔序列[-1].武.分型特征值)
        print(折线)

        return 随机生成实例

    return 魔法


def 测试_笔生成器(
    symbol: str = "btcusd",
    limit: int = 500,
    freq: SupportsInt = 时间周期.分(5),
    ws: Optional[WebSocket] = None,
    顶底序列=[100, 200, 150, 250, 200, 300, 250, 350],
    配置: 缠论配置 = 缠论配置(),
):
    def 魔法():
        分析器 = 观察者(符号=symbol, 周期=int(freq), 数据通道=ws, 配置=配置)
        生成器 = 笔K线生成器(笔K线生成配置(最小K线数量=5, 最大K线数量=12, 波动比例=0.15, 随机种子=random.Random(os.urandom(64)).randint(0, 999999999)), 分析器)
        K线序列 = 生成器.生成K线序列(顶底序列, datetime(2024, 1, 1, 9, 30, 0), 周期=int(freq))
        return 分析器

    return 魔法


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
