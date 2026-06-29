# -*- coding: utf-8 -*-
import backtrader as bt
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import math

import queue
import threading


__all__ = ["订单类型", "市场类型", "自适应市场仓位", "交易信号", "批次", "订单执行器", "高级策略基类_", "高级策略基类", "自定义实时数据源", "回测"]


# ---------- 订单类型枚举 ----------
class 订单类型(str, Enum):
    市价 = "Market"
    限价 = "Limit"
    止损 = "Stop"
    止损限价 = "StopLimit"


# ---------- 市场类型 ----------
class 市场类型(str, Enum):
    股票 = "stock"
    期货 = "futures"
    加密货币 = "crypto"


# ==================== 自适应市场仓位计算器 (Sizer) ====================
class 自适应市场仓位(bt.Sizer):
    """
    根据市场类型计算下单数量，支持：
    - 股票：100股整数倍
    - 加密货币：最小数量精度（如0.001）
    - 期货：整数手，支持合约乘数
    - 杠杆与保证金占用
    - 风险百分比/固定金额/固定数量模式
    修正：使用 self.strategy.broker 获取账户信息
    """

    params = (
        ("市场类型", 市场类型.加密货币),
        ("风险百分比", None),
        ("固定金额", None),
        ("固定数量", None),
        ("杠杆", 1.0),
        ("股票每手股数", 100),
        ("加密货币最小数量", 0.001),
        ("期货合约乘数", 1.0),
        ("期货最小手数", 1),
        ("允许部分开仓", False),
    )

    def _getsizing(self, 佣金信息, 可用现金, 数据, 是否买入):
        """返回最终下单数量（股/币/手）"""
        价格 = 数据.close[0]

        # 1. 确定名义目标价值（单位：基础货币）
        # 修正：通过 strategy 获取总资产
        总资产 = self.strategy.broker.getvalue()
        if self.p.固定金额 is not None:
            目标价值 = self.p.固定金额
        elif self.p.风险百分比 is not None:
            目标价值 = 总资产 * (self.p.风险百分比 / 100.0)
        elif self.p.固定数量 is not None:
            原始数量 = self.p.固定数量
            return self._应用市场规则(原始数量, 价格, 可用现金, 是否买入)
        else:
            raise ValueError("必须指定 固定金额、风险百分比 或 固定数量 之一")

        # 2. 根据市场类型将目标价值转换为理论数量
        市场 = self.p.市场类型
        if 市场 == 市场类型.期货:
            每手价值 = 价格 * self.p.期货合约乘数
            理论手数 = 目标价值 / 每手价值 / self.p.杠杆
            原始数量 = 理论手数
        else:
            理论数量 = 目标价值 / 价格 / self.p.杠杆
            原始数量 = 理论数量

        return self._应用市场规则(原始数量, 价格, 可用现金, 是否买入)

    def _应用市场规则(self, 原始数量, 价格, 可用现金, 是否买入):
        市场 = self.p.市场类型
        if 市场 == 市场类型.股票:
            手 = self.p.股票每手股数
            最终数量 = int(原始数量 // 手) * 手
        elif 市场 == 市场类型.加密货币:
            最小量 = self.p.加密货币最小数量
            最终数量 = math.floor(原始数量 / 最小量) * 最小量
        elif 市场 == 市场类型.期货:
            最小手 = self.p.期货最小手数
            最终数量 = int(原始数量 // 最小手) * 最小手
        else:
            最终数量 = 原始数量

        if 最终数量 <= 0:
            return 0

        # 验证资金是否足够
        if 市场 == 市场类型.期货:
            每手价值 = 价格 * self.p.期货合约乘数
            所需保证金 = 最终数量 * 每手价值 / self.p.杠杆
        else:
            所需保证金 = 最终数量 * 价格 / self.p.杠杆

        if 所需保证金 > 可用现金:
            if not self.p.允许部分开仓:
                return 0
            else:
                # 调整至最大可开数量
                if 市场 == 市场类型.期货:
                    最大手数 = int(可用现金 * self.p.杠杆 / (价格 * self.p.期货合约乘数))
                    最大手数 = max(最大手数 // self.p.期货最小手数 * self.p.期货最小手数, 0)
                    return 最大手数
                else:
                    最大数量 = int(可用现金 * self.p.杠杆 / 价格)
                    if 市场 == 市场类型.股票:
                        最大数量 = max(最大数量 // self.p.股票每手股数 * self.p.股票每手股数, 0)
                    elif 市场 == 市场类型.加密货币:
                        最大数量 = math.floor(最大数量 / self.p.加密货币最小数量) * self.p.加密货币最小数量
                    return 最大数量
        return 最终数量


# ==================== 交易信号对象 ====================
class 交易信号:
    """完整买卖点信息"""

    def __init__(
        self,
        方向: str,
        原始数量: int = 0,
        参考价格: float = None,
        时间戳: datetime = None,
        止损价: Optional[float] = None,
        止盈价: Optional[float] = None,
        移动回撤比例: Optional[float] = None,
        订单类型: 订单类型 = 订单类型.市价,
        限价: Optional[float] = None,
        止损触发价: Optional[float] = None,
        有效期: Optional[int] = None,
        交易编号: Optional[int] = None,
        市场类型: 市场类型 = 市场类型.加密货币,
        杠杆: float = 1.0,
        信号来源: str = "",
    ):
        self.方向 = 方向
        self.原始数量 = 原始数量
        self.参考价格 = 参考价格 or 0.0
        self.时间戳 = 时间戳 or datetime.now()
        self.止损价 = 止损价
        self.止盈价 = 止盈价
        self.移动回撤比例 = 移动回撤比例
        self.订单类型 = 订单类型
        self.限价 = 限价
        self.止损触发价 = 止损触发价
        self.有效期 = 有效期
        self.交易编号 = 交易编号
        self.市场类型 = 市场类型
        self.杠杆 = 杠杆
        self.信号来源 = 信号来源


# ==================== 批次对象 ====================
class 批次:
    """单个持仓批次，支持独立风控"""

    def __init__(self, 交易编号: int, 方向: str, 数量: int, 入场价: float, 止损价: float = None, 止盈价: float = None, 移动回撤比例: float = None, 状态: str = "待成交"):
        self.交易编号 = 交易编号
        self.方向 = 方向
        self.数量 = 数量
        self.入场价 = 入场价
        self.止损价 = 止损价
        self.止盈价 = 止盈价
        self.移动回撤比例 = 移动回撤比例
        self.状态 = 状态  # 待成交/持有/平仓中/已平仓
        # 移动止损追踪值
        self.最高价跟踪 = 入场价
        self.最低价跟踪 = 入场价
        self.当前移动止损价 = None
        if 移动回撤比例 is not None:
            if 方向 == "long":
                self.当前移动止损价 = 入场价 * (1 - 移动回撤比例)
            else:
                self.当前移动止损价 = 入场价 * (1 + 移动回撤比例)
        # 关联订单（用于OCO）
        self.止损订单 = None
        self.止盈订单 = None
        self.风控已挂 = False

    def 更新移动止损(self, 最高价: float, 最低价: float, 当前价: float) -> bool:
        """基于最高/最低价更新移动止损，返回是否触发"""
        if self.移动回撤比例 is None:
            return False
        if self.方向 == "long":
            if 最高价 > self.最高价跟踪:
                self.最高价跟踪 = 最高价
                新止损 = self.最高价跟踪 * (1 - self.移动回撤比例)
                if self.当前移动止损价 is None or 新止损 > self.当前移动止损价:
                    self.当前移动止损价 = 新止损
            # 使用最低价检查是否触发
            return 最低价 <= self.当前移动止损价 if self.当前移动止损价 is not None else False
        else:
            if 最低价 < self.最低价跟踪:
                self.最低价跟踪 = 最低价
                新止损 = self.最低价跟踪 * (1 + self.移动回撤比例)
                if self.当前移动止损价 is None or 新止损 < self.当前移动止损价:
                    self.当前移动止损价 = 新止损
            return 最高价 >= self.当前移动止损价 if self.当前移动止损价 is not None else False

    def 检查静态风控(self, 当前价: float) -> bool:
        if self.止损价 is not None:
            if self.方向 == "long" and 当前价 <= self.止损价:
                return True
            if self.方向 == "short" and 当前价 >= self.止损价:
                return True
        if self.止盈价 is not None:
            if self.方向 == "long" and 当前价 >= self.止盈价:
                return True
            if self.方向 == "short" and 当前价 <= self.止盈价:
                return True
        return False


# ==================== 订单执行器 ====================
class 订单执行器:
    """
    负责将交易信号转换为实际订单，集成Sizer、OCO风控单、部分成交处理
    """

    def __init__(self, 策略实例, 批次列表: List, 日志函数):
        self.策略 = 策略实例
        self.批次列表 = 批次列表
        self.日志 = 日志函数

    def 执行(self, 信号: 交易信号):
        """主入口：下单并部署风控"""
        # 1. 计算最终数量
        if 信号.原始数量 > 0:
            数量 = 信号.原始数量
        else:
            # 调用策略的 _getsize 方法，它会使用绑定的 Sizer
            数量 = self.策略.getsizing(self.策略.data, isbuy=(信号.方向 == "long"))
        if 数量 <= 0:
            self.日志(f"数量为0，忽略信号: {信号.信号来源}")
            return

        # 2. 处理有效期
        有效期日期 = None
        if 信号.有效期 is not None:
            有效期日期 = self.策略.data.datetime.date(0) + timedelta(days=信号.有效期)

        # 3. 先创建批次（状态=待成交），确保订单未成交时已预留位置
        批次对象 = 批次(交易编号=信号.交易编号 or self.策略.获取下一个交易编号(), 方向=信号.方向, 数量=数量, 入场价=信号.参考价格, 止损价=信号.止损价, 止盈价=信号.止盈价, 移动回撤比例=信号.移动回撤比例, 状态="待成交")
        self.批次列表.append(批次对象)
        信号.交易编号 = 批次对象.交易编号

        # 4. 提交主订单
        主订单 = self._提交主订单(信号, 数量, 有效期日期)
        if 主订单 is None:
            # 订单创建失败，删除批次
            self.批次列表.remove(批次对象)
            return

        # 5. 将订单与批次关联
        主订单.关联批次 = 批次对象
        批次对象.主订单引用 = 主订单

        self.日志(f"提交订单: {信号.方向} {数量}@{'市价' if 信号.订单类型 == 订单类型.市价 else 信号.限价} 止损={信号.止损价} 止盈={信号.止盈价} 移动={信号.移动回撤比例}")

    def _提交主订单(self, 信号: 交易信号, 数量: int, 有效期日期):
        """根据订单类型创建Backtrader订单"""
        if 信号.订单类型 == 订单类型.市价:
            if 信号.方向 == "long":
                return self.策略.buy(size=数量, exectype=bt.Order.Market)
            else:
                return self.策略.sell(size=数量, exectype=bt.Order.Market)
        elif 信号.订单类型 == 订单类型.限价:
            if 信号.限价 is None:
                self.日志("限价单缺少限价")
                return None
            if 信号.方向 == "long":
                return self.策略.buy(size=数量, price=信号.限价, exectype=bt.Order.Limit, valid=有效期日期)
            else:
                return self.策略.sell(size=数量, price=信号.限价, exectype=bt.Order.Limit, valid=有效期日期)
        elif 信号.订单类型 == 订单类型.止损:
            if 信号.止损触发价 is None:
                self.日志("止损单缺少触发价")
                return None
            if 信号.方向 == "long":
                return self.策略.sell(size=数量, price=信号.止损触发价, exectype=bt.Order.Stop, valid=有效期日期)
            else:
                return self.策略.buy(size=数量, price=信号.止损触发价, exectype=bt.Order.Stop, valid=有效期日期)
        else:
            self.日志("不支持止损限价单")
            return None


# ==================== 完整高级策略基类（全中文） ====================
class 高级策略基类_(bt.Strategy):
    """
    支持完整买卖点信号、多批次独立风控、自适应市场资金管理、OCO模拟、全局风控
    子类需实现 生成买卖点 方法
    """

    params = (
        # 资金与市场
        ("市场类型", 市场类型.加密货币),
        ("风险百分比", 2.0),
        ("杠杆", 1.0),
        ("允许部分开仓", False),
        # 股票
        ("股票每手股数", 100),
        # 加密货币
        ("加密货币最小数量", 0.001),
        # 期货
        ("期货合约乘数", 1.0),
        ("期货最小手数", 1),
        # 批次管理
        ("最大批次数", 5),
        ("允许加多", True),
        ("允许加空", True),
        # 风控
        ("默认止损比例", 0.02),
        ("默认止盈比例", 0.03),
        ("默认移动回撤比例", 0.01),
        ("启用移动止损", True),
        ("使用OCO订单", True),  # 是否使用真实OCO订单（依赖券商支持）
        ("全局最大回撤限制", 20.0),
        ("每日亏损限制", 5.0),
        ("回撤后全部平仓", True),
        # 其他
        ("数据预热周期", 30),  # 指标计算需要的最小K线数
    )

    def __init__(self):
        super().__init__()
        # 批次管理
        self.批次列表: List[批次] = []
        self.下一个交易编号 = 1
        # 全局风控
        self.每日起始净值 = None
        self.上次日期 = None
        self.峰值净值 = None
        self.全局风控触发 = False
        # 订单暂存与部分成交累计
        self.订单累计成交 = {}  # {order.ref: 已成交数量}
        # 自定义Sizer
        self.sizer = 自适应市场仓位(
            市场类型=self.p.市场类型,
            风险百分比=self.p.风险百分比,
            杠杆=self.p.杠杆,
            允许部分开仓=self.p.允许部分开仓,
            股票每手股数=self.p.股票每手股数,
            加密货币最小数量=self.p.加密货币最小数量,
            期货合约乘数=self.p.期货合约乘数,
            期货最小手数=self.p.期货最小手数,
        )
        # 注册Sizer（关键！）
        self.setsizer(self.sizer)

        # 执行器
        self.执行器 = 订单执行器(self, self.批次列表, self.日志)

    def 日志(self, 文本: str):
        dt = self.datas[0].datetime.datetime(0)
        print(f"[{dt}] {文本}")

    def 获取下一个交易编号(self) -> int:
        编号 = self.下一个交易编号
        self.下一个交易编号 += 1
        return 编号

    # ---------- 批次管理 ----------
    def 移除批次(self, 批次对象: 批次):
        if 批次对象 in self.批次列表:
            self.批次列表.remove(批次对象)
            self.日志(f"移除批次 {批次对象.交易编号}")

    def 平仓批次(self, 批次对象: 批次, 平仓数量: int = None):
        """发起市价平仓，将批次标记为平仓中"""
        if 平仓数量 is None:
            平仓数量 = 批次对象.数量
        if 平仓数量 <= 0 or 平仓数量 > 批次对象.数量:
            return
        if 批次对象.方向 == "long":
            订单 = self.sell(size=平仓数量, exectype=bt.Order.Market)
        else:
            订单 = self.buy(size=平仓数量, exectype=bt.Order.Market)

        订单.关联批次 = 批次对象
        订单.平仓数量 = 平仓数量
        批次对象.状态 = "平仓中"
        self.日志(f"提交平仓订单 批次{批次对象.交易编号} 数量{平仓数量}")

    def 全部平仓(self):
        """清空所有批次"""
        for 批次 in self.批次列表[:]:
            self.平仓批次(批次)

    # ---------- 风控管理（使用High/Low） ----------
    def 管理批次风控(self):
        最高价 = self.data.high[0]
        最低价 = self.data.low[0]
        收盘价 = self.data.close[0]
        for 批次 in self.批次列表[:]:
            if 批次.状态 != "持有":
                continue
            # 移动止损触发
            if self.p.启用移动止损 and 批次.移动回撤比例 is not None:
                if 批次.更新移动止损(最高价, 最低价, 收盘价):
                    self.日志(f"批次{批次.交易编号} 移动止损触发")
                    self.平仓批次(批次)
                    continue
            # 静态止损止盈触发
            if 批次.检查静态风控(收盘价):
                self.日志(f"批次{批次.交易编号} 静态止损/止盈触发")
                self.平仓批次(批次)

    # ---------- 挂载OCO风控单（仅在主订单成交后调用） ----------
    def _挂载风控单_OCO(self, 批次: 批次, 当前价格: float):
        """在主订单成交后，挂止损止盈单，使用真正的 OCO (oco 参数)"""
        if not self.p.使用OCO订单:
            return
        if 批次.风控已挂:
            return
        数量 = 批次.数量
        if 批次.方向 == "long":
            # 多头：止损单是卖出止损，止盈单是卖出限价
            stop_order = None
            limit_order = None
            if 批次.止损价 is not None:
                stop_order = self.sell(size=数量, price=批次.止损价, exectype=bt.Order.Stop, transmit=False)
            if 批次.止盈价 is not None:
                limit_order = self.sell(size=数量, price=批次.止盈价, exectype=bt.Order.Limit, transmit=False)
            # 建立 OCO 关系
            if stop_order and limit_order:
                stop_order.oco = limit_order
                limit_order.oco = stop_order
                # 最后一个订单必须 transmit=True 才会发送
                limit_order.transmit = True
                stop_order.transmit = False
            elif stop_order:
                stop_order.transmit = True
            elif limit_order:
                limit_order.transmit = True
            # 记录订单引用
            批次.止损订单 = stop_order
            批次.止盈订单 = limit_order
        else:
            # 空头：止损单是买入止损，止盈单是买入限价
            stop_order = None
            limit_order = None
            if 批次.止损价 is not None:
                stop_order = self.buy(size=数量, price=批次.止损价, exectype=bt.Order.Stop, transmit=False)
            if 批次.止盈价 is not None:
                limit_order = self.buy(size=数量, price=批次.止盈价, exectype=bt.Order.Limit, transmit=False)
            if stop_order and limit_order:
                stop_order.oco = limit_order
                limit_order.oco = stop_order
                limit_order.transmit = True
                stop_order.transmit = False
            elif stop_order:
                stop_order.transmit = True
            elif limit_order:
                limit_order.transmit = True
            批次.止损订单 = stop_order
            批次.止盈订单 = limit_order
        批次.风控已挂 = True
        if stop_order or limit_order:
            self.日志(f"批次{批次.交易编号} 已挂载OCO风控单")

    # ---------- 全局风控 ----------
    def 检查全局风控(self) -> bool:
        if self.全局风控触发:
            return False
        当前净值 = self.broker.getvalue()
        今日日期 = self.datas[0].datetime.date(0)
        if 今日日期 != self.上次日期:
            self.每日起始净值 = 当前净值
            self.上次日期 = 今日日期
        if self.峰值净值 is None or 当前净值 > self.峰值净值:
            self.峰值净值 = 当前净值
        回撤 = (当前净值 - self.峰值净值) / self.峰值净值
        if 回撤 < -self.p.全局最大回撤限制 / 100:
            self.日志(f"最大回撤超过 {self.p.全局最大回撤限制}%，触发全局风控")
            if self.p.回撤后全部平仓:
                self.全部平仓()
            self.全局风控触发 = True
            return False
        if self.每日起始净值:
            日亏损 = (当前净值 - self.每日起始净值) / self.每日起始净值
            if 日亏损 < -self.p.每日亏损限制 / 100:
                self.日志(f"每日亏损超过 {self.p.每日亏损限制}%，暂停开仓")
                return False
        return True

    # ---------- 订单回调（处理成交、部分成交、取消） ----------
    def notify_order(self, 订单):
        if 订单.status in [订单.Submitted, 订单.Accepted]:
            return

        # 处理平仓订单成交
        if 订单.status == 订单.Completed and hasattr(订单, "平仓数量"):
            if hasattr(订单, "关联批次"):
                批次 = 订单.关联批次
                平仓数量 = 订单.平仓数量
                批次.数量 -= 平仓数量
                self.日志(f"批次{批次.交易编号} 平仓成交 {平仓数量}，剩余 {批次.数量}")
                if 批次.数量 <= 0:
                    self.移除批次(批次)
                else:
                    批次.状态 = "持有"
            return

        # 处理开仓订单成交或部分成交
        if 订单.status in [订单.Completed, 订单.Partial]:
            if hasattr(订单, "关联批次"):
                批次 = 订单.关联批次
                # 累计成交数量处理（防止部分成交多次回调）
                累计 = self.订单累计成交.get(订单.ref, 0)
                本次新增 = 订单.executed.size - 累计
                if 本次新增 > 0:
                    # 更新批次数量（如果之前没有成交过，则设置数量为新增；否则累加）
                    if 累计 == 0:
                        批次.数量 = 本次新增
                    else:
                        批次.数量 += 本次新增
                    self.订单累计成交[订单.ref] = 订单.executed.size
                    self.日志(f"批次{批次.交易编号} 新增成交 {本次新增}，累计批次数量 {批次.数量}")
                    # 如果是首次成交，更新入场价并挂载OCO
                    if 累计 == 0:
                        批次.入场价 = 订单.executed.price
                        # 更新移动止损初始值
                        if 批次.移动回撤比例:
                            if 批次.方向 == "long":
                                批次.当前移动止损价 = 批次.入场价 * (1 - 批次.移动回撤比例)
                            else:
                                批次.当前移动止损价 = 批次.入场价 * (1 + 批次.移动回撤比例)
                        批次.状态 = "持有"
                        # 挂载OCO风控单（若使用）
                        self._挂载风控单_OCO(批次, 订单.executed.price)
                # 如果订单完全成交，清理累计记录
                if 订单.status == 订单.Completed and 订单.ref in self.订单累计成交:
                    del self.订单累计成交[订单.ref]
                return

        # 订单取消/拒绝/过期：删除关联的预创建批次
        if 订单.status in [订单.Canceled, 订单.Margin, 订单.Rejected, 订单.Expired]:
            if hasattr(订单, "关联批次"):
                批次 = 订单.关联批次
                if 批次 in self.批次列表:
                    self.批次列表.remove(批次)
                    self.日志(f"订单未成交，删除预创建批次{批次.交易编号}")
            # 清理累计成交记录
            if 订单.ref in self.订单累计成交:
                del self.订单累计成交[订单.ref]
            self.日志(f"订单状态: {订单.getstatusname()}")

    # ---------- 核心主循环 ----------
    def 生成买卖点(self) -> Optional[交易信号]:
        """子类必须实现，返回交易信号或None"""
        raise NotImplementedError("子类必须实现 生成买卖点 方法")

    def next(self):
        # 数据预热检查
        if len(self.data) < self.p.数据预热周期:
            return

        # 全局风控检查（决定是否允许开新仓）
        允许开仓 = self.检查全局风控()
        # 管理已有批次的风控（平仓）
        self.管理批次风控()
        # 生成信号并执行（仅在允许开仓且未达最大批次数时）
        if 允许开仓 and len(self.批次列表) < self.p.最大批次数:
            信号 = self.生成买卖点()
            if 信号:
                self.执行器.执行(信号)


# ==================== 示例：简单双均线策略（演示多批次加仓） ====================
class 示例双均线策略(高级策略基类_):
    """使用双均线金叉死叉产生买卖点，支持加仓"""

    params = (
        ("快线周期", 10),
        ("慢线周期", 30),
        ("止损比例", 0.02),
        ("止盈比例", 0.03),
        ("移动回撤比例", 0.01),
        ("加仓间隔K线数", 5),  # 距离上次开仓至少多少根K线才允许再次加仓
    )

    def __init__(self):
        super().__init__()
        self.快线 = bt.indicators.SMA(self.data.close, period=self.p.快线周期)
        self.慢线 = bt.indicators.SMA(self.data.close, period=self.p.慢线周期)
        self.交叉 = bt.indicators.CrossOver(self.快线, self.慢线)
        self.上次开仓K线 = {"long": -100, "short": -100}  # 记录最近开仓的K线索引

    def 生成买卖点(self):
        # 获取当前持有批次的方向统计（不限制唯一方向，允许双向锁仓，但加仓控制分开）
        多头批次数 = sum(1 for b in self.批次列表 if b.方向 == "long" and b.状态 == "持有")
        空头批次数 = sum(1 for b in self.批次列表 if b.方向 == "short" and b.状态 == "持有")
        当前K线索引 = len(self.data)

        # 金叉做多（允许加多）
        if self.交叉[0] == 1:
            if self.p.允许加多 and 多头批次数 < self.p.最大批次数:
                # 加仓间隔控制
                if 当前K线索引 - self.上次开仓K线["long"] >= self.p.加仓间隔K线数:
                    信号 = 交易信号(方向="long", 原始数量=0, 参考价格=self.data.close[0], 止损价=self.data.close[0] * (1 - self.p.止损比例), 止盈价=self.data.close[0] * (1 + self.p.止盈比例), 移动回撤比例=self.p.移动回撤比例 if self.p.启用移动止损 else None, 订单类型=订单类型.市价, 信号来源="双均线金叉")
                    self.上次开仓K线["long"] = 当前K线索引
                    return 信号

        # 死叉做空（允许加空）
        if self.交叉[0] == -1:
            if self.p.允许加空 and 空头批次数 < self.p.最大批次数:
                if 当前K线索引 - self.上次开仓K线["short"] >= self.p.加仓间隔K线数:
                    信号 = 交易信号(方向="short", 原始数量=0, 参考价格=self.data.close[0], 止损价=self.data.close[0] * (1 + self.p.止损比例), 止盈价=self.data.close[0] * (1 - self.p.止盈比例), 移动回撤比例=self.p.移动回撤比例 if self.p.启用移动止损 else None, 订单类型=订单类型.市价, 信号来源="双均线死叉")
                    self.上次开仓K线["short"] = 当前K线索引
                    return 信号
        return None


# ==================== 修正后的随机数据类（用于演示） ====================
class 随机数据(bt.feeds.DataBase):
    def __init__(self, start_date=datetime(2020, 1, 1), 最大条数=10000):
        super().__init__()
        self.关闭价 = 100.0
        self._date = start_date
        self._条数计数 = 0
        self.最大条数 = 最大条数

    def _load(self):
        # 达到最大条数后停止提供数据
        if self._条数计数 >= self.最大条数:
            return False

        # 递增日期
        self._date += timedelta(days=1)
        # 随机生成价格
        self.关闭价 += np.random.randn() * 2
        self.lines.open[0] = self.关闭价 + np.random.randn() * 0.5
        self.lines.high[0] = self.关闭价 + abs(np.random.randn() * 1)
        self.lines.low[0] = self.关闭价 - abs(np.random.randn() * 1)
        self.lines.close[0] = self.关闭价
        self.lines.volume[0] = 10000 + int(abs(np.random.randn() * 5000))
        self.lines.datetime[0] = bt.date2num(self._date)

        self._条数计数 += 1
        return True


class 自定义实时数据源(bt.feed.DataBase):
    """
    一个用于模拟实时数据推送的数据源，继承自Backtrader的DataBase。
    在实际应用中，你需要将“模拟生成数据”的部分，替换为接收WebSocket等推送数据的代码。
    """

    def __init__(self, 数据队列: queue.Queue, 观察员: "观察者", 魔法, **魔法参数):
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
        if self.p.观察员.当前缠K is None:
            return

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


class Bitstamp数据源(bt.feeds.DataBase):
    """Bitstamp 交易所 OHLC 数据源，包装为 Backtrader DataFeed。

    在 ``start()`` 中通过 Bitstamp REST API 分页预加载全部历史数据到内存，
    在 ``_load()`` 中逐条吐出 OHLC 柱。

    用法::

        data = Bitstamp数据源(符号="btcusd", 周期=300, 数量=500)
        cerebro.adddata(data)
    """

    params = (
        ("符号", "btcusd"),
        ("周期", 300),  # 秒
        ("数量", 500),  # 请求的 K 线条数
        ("重试次数", 3),
    )

    @staticmethod
    def ohlc(pair: str, step: int, start: int, end: int, length: int = 1000, retries: int = 3) -> Dict:
        """执行HTTP请求，带重试机制"""
        url = f"https://www.bitstamp.net/api/v2/ohlc/{pair}/"
        session = requests.Session()
        session.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
        }

        params = {"step": step, "limit": length, "start": start, "end": end}

        for attempt in range(retries):
            try:
                resp = session.get(url, params=params, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"请求失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2**attempt)

    def start(self):
        """分页拉取全部 OHLC 数据到内存。"""
        self._数据: List[dict] = []
        end_ts = int(datetime.now().timestamp())
        left = end_ts - self.p.周期 * self.p.数量
        if left < 0:
            raise RuntimeError(f"起始时间戳 {left} < 0")
        _next = left
        while True:
            page = self.ohlc(self.p.符号, self.p.周期, _next, _next := _next + self.p.周期 * 1000, retries=self.p.重试次数)
            if not page.get("data"):
                break
            self._数据.extend(page["data"]["ohlc"])
            _next = int(page["data"]["ohlc"][-1]["timestamp"])
            if len(page["data"]["ohlc"]) < 100:
                break
        self._索引 = 0

    def _load(self):
        """逐条吐出 OHLC 柱到 Backtrader 数据线。"""
        if self._索引 >= len(self._数据):
            return False
        bar = self._数据[self._索引]
        self._索引 += 1
        ts = int(bar["timestamp"])
        self.lines.datetime[0] = bt.date2num(datetime.fromtimestamp(ts))
        self.lines.open[0] = float(bar["open"])
        self.lines.high[0] = float(bar["high"])
        self.lines.low[0] = float(bar["low"])
        self.lines.close[0] = float(bar["close"])
        self.lines.volume[0] = float(bar["volume"])
        return True


class Nb数据源(bt.feeds.DataBase):
    """将 .nb 二进制 K 线文件包装为 Backtrader DataFeed。"""

    params = (("文件路径", ""),)

    def start(self):
        self._f = open(self.p.文件路径, "rb")
        self._size = struct.calcsize(">6d")

    def stop(self):
        if self._f:
            self._f.close()

    def _load(self):
        buffer = self._f.read(self._size)
        if not buffer or len(buffer) < self._size:
            return False
        ts, o, h, l, c, v = struct.unpack(">6d", buffer)
        self.lines.datetime[0] = bt.date2num(datetime.fromtimestamp(ts))
        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        return True


# ==================== 回测运行入口 ====================
if __name__ == "__main__":
    import numpy as np

    cerebro = bt.Cerebro()

    # 使用修正后的随机数据，生成 500 个交易日
    data = 随机数据(start_date=datetime(2022, 1, 1))
    cerebro.adddata(data)

    # 添加策略（使用示例双均线策略）
    cerebro.addstrategy(
        示例双均线策略,
        市场类型=市场类型.加密货币,
        风险百分比=2.0,  # 每笔使用2%资金
        杠杆=5.0,
        最大批次数=8,  # 最多同时持有3个批次
        允许加多=True,
        允许加空=True,
        启用移动止损=True,
        使用OCO订单=True,  # 尝试使用真实OCO（Backtrader模拟支持）
        全局最大回撤限制=20,
        每日亏损限制=5,
        数据预热周期=30,
        加仓间隔K线数=5,
    )

    # 配置 Broker
    cerebro.broker.setcash(100000.0)
    cerebro.broker.set_slippage_perc(perc=0.001)  # 滑点0.1%
    # 定义填充器，参数 perc 表示百分比，取值范围 0.0 到 100.0
    filler = bt.broker.fillers.FixedBarPerc(perc=30)

    # 将填充器应用到 Broker
    cerebro.broker.set_filler(filler)

    # 运行回测
    print("初始资金: {:.2f}".format(cerebro.broker.getvalue()))
    results = cerebro.run()
    print("最终资金: {:.2f}".format(cerebro.broker.getvalue()))

    # 可选：绘制图表（需要安装 matplotlib）
    # cerebro.plot()
