# -*- coding: utf-8 -*-
"""缠论分析 MCP 服务器 — 混合方案。

- 纯函数 Tool：不依赖浏览器会话，AI 可独立拉数据/分析。
- 状态 Tool：复用 main.py 的全局连接管理器，查询浏览器会话的观察者。

挂载到 main.py::

    from chanlun_mcp import mcp
    app.mount("/mcp", mcp.streamable_http_app())
"""

from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP

from chan import (
    观察者,
    缠论配置,
    K线,
    走势,
    Bitstamp数据源,
    立体分析器,
    get_signals_config,
    信号计算器,
    相对方向,
)

mcp = FastMCP(
    "缠论分析",
    instructions="缠中说禅技术分析引擎。提供K线获取、走势结构分析、买卖点识别、日内分类等能力。",
    streamable_http_path="/",  # 挂载到 FastAPI 时内部路径从根开始
)


# ═══════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════


def _解析OHLCV文本(文本: str, 符号: str, 周期: int) -> List[K线]:
    """将 '时间戳|开|高|低|收|量' 文本解析为 K线 列表。"""
    K线序列 = []
    for i, 行 in enumerate(文本.strip().splitlines()):
        if not 行.strip():
            continue
        parts = 行.strip().split("|")
        if len(parts) < 5:
            raise ValueError(f"行 {i + 1} 格式错误，需要 时间戳|开|高|低|收 至少5列: {行}")
        时间戳 = int(float(parts[0]))
        开, 高, 低, 收 = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        量 = float(parts[5]) if len(parts) > 5 else 0
        from datetime import datetime

        K线序列.append(
            K线.创建普K(
                标识=符号,
                时间戳=datetime.fromtimestamp(时间戳),
                开盘价=开,
                最高价=高,
                最低价=低,
                收盘价=收,
                成交量=量,
                序号=i,
                周期=周期,
            )
        )
    return K线序列


def _喂入观察者(K线序列: List[K线], 周期: int, 符号: str) -> 观察者:
    """创建观察者并增量喂入K线，返回分析完成的分析器。"""
    obs = 观察者(符号, 周期, 缠论配置())
    for k in K线序列:
        obs.增加原始K线(k)
    return obs


def _获取会话观察者(用户标识: str):
    """延迟导入 main，避免循环依赖，返回会话观察者。"""
    from main import 全局连接管理器

    return 全局连接管理器.获取图表观察员(用户标识)


def _判定走势类型(中枢们) -> str:
    """按中枢数量和重叠关系判定走势类型（MCP 独立实现，不依赖 chan.走势）。"""
    if not 中枢们:
        return "无中枢"
    if len(中枢们) == 1:
        return "盘整"
    方向 = None
    for i in range(len(中枢们) - 1):
        a, b = 中枢们[i], 中枢们[i + 1]
        if max(a.低, b.低) <= min(a.高, b.高):
            return "盘整"  # 中枢重叠 → 扩展
        cur = "向上" if b.低 > a.高 else "向下"
        if 方向 is None:
            方向 = cur
        elif 方向 != cur:
            return "盘整"
    return 方向


# ═══════════════════════════════════════════════
# 纯函数 Tool — 不依赖会话
# ═══════════════════════════════════════════════


@mcp.tool(name="get_kline_data", description="从 Bitstamp 获取K线数据，支持任意周期（非原生周期自动聚合，时间戳按周期边界对齐）。")
def 获取K线数据(符号: str = "btcusd", 周期: int = 300, 数量: int = 500) -> List[Dict[str, Any]]:
    """从 Bitstamp 获取K线数据，支持任意周期（非原生周期自动聚合）。

    Args:
        符号: 交易品种，如 btcusd / ethusd
        周期: K线周期（秒），如 300=5分钟 3600=1小时 10800=3小时
        数量: 请求K线条数
    Returns:
        [{时间, 开, 高, 低, 收, 量}, ...] 按时间升序，时间戳对齐到周期边界
    """
    # 直接走 ohlc()：一次调用即返回升序数据（内部自动对齐到 UTC 零点且周期整除、
    # 时间戳对齐聚合、自动分页）。注意不能循环调用 _load()，
    # 那需要挂到 Cerebro 上（lines 未分配空间会报 array assignment index out of range）。
    数据 = Bitstamp数据源.ohlc(符号, 周期, 数量)["data"]["ohlc"]
    结果 = []
    for bar in 数据:
        if isinstance(bar, dict):
            结果.append(
                {
                    "时间": str(bar["timestamp"]),
                    "开": float(bar["open"]),
                    "高": float(bar["high"]),
                    "低": float(bar["low"]),
                    "收": float(bar["close"]),
                    "量": float(bar["volume"]),
                }
            )
        else:  # 列表形式 [timestamp, open, high, low, close, volume]
            结果.append(
                {
                    "时间": str(bar[0]),
                    "开": float(bar[1]),
                    "高": float(bar[2]),
                    "低": float(bar[3]),
                    "收": float(bar[4]),
                    "量": float(bar[5]),
                }
            )
    return 结果


@mcp.tool(name="analyze_structure", description="分析K线走势结构，返回笔/线段/中枢统计和走势分类。")
def 分析走势(数据: str, 符号: str = "btcusd", 周期: int = 300) -> Dict[str, Any]:
    """分析K线走势结构，返回笔/线段/中枢统计和走势分类。

    Args:
        数据: OHLCV 文本，每行 '时间戳|开|高|低|收|量'（时间戳为秒）
        符号: 交易品种
        周期: K线周期（秒）
    Returns:
        {笔数, 线段数, 中枢数, 走势类型, 最近笔列表}
    """
    K线序列 = _解析OHLCV文本(数据, 符号, 周期)
    if not K线序列:
        return {"错误": "无有效K线数据"}
    obs = _喂入观察者(K线序列, 周期, 符号)
    中枢们 = obs.中枢序列
    return {
        "K线数": len(K线序列),
        "笔数": len(obs.笔序列),
        "线段数": len(obs.线段序列),
        "中枢数": len(中枢们),
        "走势类型": _判定走势类型(中枢们),
        "最近笔": [{"方向": b.方向.value, "起点": b.文.分型特征值, "终点": b.武.分型特征值} for b in obs.笔序列[-5:]],
    }


@mcp.tool(name="classify_intraday", description="第46课日内走势分类：按前3根K线与日内高低点关系分三类。")
def 日内分类(数据: str, 当前价: float = None) -> Dict[str, Any]:
    """第46课日内走势分类：按前3根K线与日内高低点关系分三类。

    Args:
        数据: 8根同周期K线，每行 '时间戳|开|高|低|收|量'
        当前价: 可选，收盘价
    Returns:
        {类型, 强度, 中枢数, 描述}
    """
    K线序列 = _解析OHLCV文本(数据, "btcusd", 1800)
    if len(K线序列) < 3:
        return {"错误": "至少需要3根K线"}
    r = 走势.日内分类(K线序列, 当前价)
    return r


# ═══════════════════════════════════════════════
# 状态 Tool — 复用 main.py 全局连接管理器
# ═══════════════════════════════════════════════


@mcp.tool(name="list_active_sessions", description="列出所有活跃的浏览器会话及其分析状态。")
def 列出活跃会话() -> List[Dict[str, Any]]:
    """列出所有活跃的浏览器 WebSocket 会话。

    浏览器打开页面并发送 ready 消息后，服务端会创建观察者并登记。
    返回每个会话的 user_id 和当前分析状态，供状态类工具使用。

    Returns:
        [{用户标识, 符号, 周期, K线数, 笔数, 中枢数, 走势类型}, ...]
    """
    from main import 全局连接管理器

    结果 = []
    for 用户标识, obs in 全局连接管理器.图表观察员字典.items():
        if obs is None:
            结果.append({"用户标识": 用户标识, "状态": "无观察者"})
            continue
        中枢们 = obs.中枢序列
        结果.append(
            {
                "用户标识": 用户标识,
                "符号": obs.符号,
                "周期": obs.周期,
                "K线数": len(obs.普通K线序列),
                "笔数": len(obs.笔序列),
                "中枢数": len(中枢们),
                "走势类型": _判定走势类型(中枢们),
            }
        )
    return 结果


@mcp.tool(name="query_current_structure", description="查询浏览器会话当前分析的走势结构（复用全局连接管理器）。")
def 查询当前走势(用户标识: str) -> Dict[str, Any]:
    """查询浏览器会话当前分析的走势结构（复用全局连接管理器）。

    Args:
        用户标识: 浏览器 WebSocket 会话的用户ID
    Returns:
        {符号, 周期, K线数, 笔数, 线段数, 中枢数, 走势类型} 或 错误
    """
    obs = _获取会话观察者(用户标识)
    if obs is None:
        return {"错误": f"用户 {用户标识} 没有活跃的浏览器会话，请先在浏览器打开页面"}
    中枢们 = obs.中枢序列
    return {
        "符号": obs.符号,
        "周期": obs.周期,
        "K线数": len(obs.普通K线序列),
        "笔数": len(obs.笔序列),
        "线段数": len(obs.线段序列),
        "中枢数": len(中枢们),
        "走势类型": _判定走势类型(中枢们),
        "当前缠K": str(obs.当前缠K) if obs.当前缠K else None,
    }


@mcp.tool(name="check_segment_divergence", description="检查浏览器会话中指定「线段<线段>」位置的 MACD 背离，可递归检查内部子级别。")
def 检查线段背离(用户标识: str, 索引: int = -1, 内部: bool = False) -> Dict[str, Any]:
    """检查「线段<线段>」序列中指定位置的 MACD 背离。

    取索引处的线段为后段，向前找同向的隔一段作为前段，
    用 背驰分析.MACD背离 判断价格与 DIF 是否背离。

    Args:
        用户标识: 浏览器 WebSocket 会话的用户ID
        索引: 「线段<线段>」序列下标，-1 表示最后一条
    Returns:
        背离检测结果（类型/价格/DIF极值）或 错误
    """
    from chan import 背驰分析

    obs = _获取会话观察者(用户标识)
    if obs is None:
        return {"错误": f"用户 {用户标识} 没有活跃的浏览器会话"}

    线段_线段 = obs.线段_线段序列
    if not 线段_线段:
        return {"错误": "没有 线段<线段> 结构"}

    # 解析索引
    if 索引 < 0:
        索引 = len(线段_线段) - 1
    if 索引 >= len(线段_线段):
        return {"错误": f"索引 {索引} 超出范围，共 {len(线段_线段)} 条"}

    后段 = 线段_线段[索引]
    结果 = {
        "索引": 索引,
        "总数": len(线段_线段),
        "后段方向": 后段.方向.value if 后段.方向 else str(后段.方向),
        "后段区间": [后段.文.分型特征值, 后段.武.分型特征值],
    }

    # ── 内部检查：该「线段<线段>」的基础序列（构成它的线段）内部背离 ──
    if 内部:
        内部段们 = list(后段.基础序列 or [])
        if not 内部段们:
            结果["内部"] = {"错误": "该 线段<线段> 没有基础序列"}
            return 结果
        内部结果 = {"段数": len(内部段们), "背离列表": []}
        for j in range(len(内部段们) - 2):
            前段, 后段2 = 内部段们[j], 内部段们[j + 2]
            if 前段.方向 == 后段2.方向:
                背离结果 = 背驰分析.MACD背离(前段, 后段2, obs.普通K线序列)
                内部结果["背离列表"].append(
                    {
                        "内部索引": j,
                        "前段方向": 前段.方向.value if 前段.方向 else str(前段.方向),
                        "前段区间": [前段.文.分型特征值, 前段.武.分型特征值],
                        "后段区间": [后段2.文.分型特征值, 后段2.武.分型特征值],
                        "类型": 背离结果["类型"],
                        "背离": 背离结果["背离"],
                    }
                )
        内部结果["背离数"] = sum(1 for x in 内部结果["背离列表"] if x["背离"])
        结果["内部"] = 内部结果
        return 结果

    # 向前找同向的隔一段作前段
    for i in range(索引 - 2, -1, -1):
        if 线段_线段[i].方向 == 后段.方向:
            前段 = 线段_线段[i]
            结果["前段索引"] = i
            结果["前段方向"] = 前段.方向.value if 前段.方向 else str(前段.方向)
            结果["前段区间"] = [前段.文.分型特征值, 前段.武.分型特征值]
            背离结果 = 背驰分析.MACD背离(前段, 后段, obs.普通K线序列)
            结果.update(背离结果)
            break
    else:
        结果["错误"] = f"索引 {索引} 之前没有同向的 线段<线段> 可对比"

    return 结果


@mcp.tool(name="execute_session_code", description="在浏览器会话中执行受限 Python 代码访问观察者（复用代码执行器）。")
def 执行会话代码(用户标识: str, 代码: str) -> Dict[str, Any]:
    """在浏览器会话对应的受限环境中执行 Python 代码。

    复用 main.py 的 代码执行器：AST 安全检查 + 超时 + 观察员注入。
    代码内可直接使用 ``观察员`` 变量访问该会话的缠论分析器。

    示例::

        观察员 = 观察员  # 已注入
        print(len(观察员.笔序列), len(观察员.中枢序列))

    Args:
        用户标识: 浏览器 WebSocket 会话的用户ID
        代码: 要执行的 Python 代码
    Returns:
        代码执行器返回结果（stdout/stderr/异常信息）
    """
    from main import 全局连接管理器

    环境 = 全局连接管理器.获取执行环境(用户标识)
    obs = 全局连接管理器.获取图表观察员(用户标识)
    if obs is None:
        return {"错误": f"用户 {用户标识} 没有活跃的浏览器会话"}
    环境.设置图表观察员(obs)  # 确保观察员注入命名空间
    return 环境.执行(代码)


@mcp.tool(name="detect_session_signals", description="识别浏览器会话当前K线上的买卖点信号（复用会话观察者）。")
def 识别会话买卖点(用户标识: str, 信号集: str = "中枢第三买卖点") -> Dict[str, Any]:
    """识别浏览器会话当前K线上的买卖点信号（复用会话观察者）。

    Args:
        用户标识: 浏览器 WebSocket 会话的用户ID
        信号集: 信号集名称，支持 中枢第三买卖点 / 第二买卖点 / 第一买卖点
    Returns:
        {信号: {key: value}} 或 错误
    """
    obs = _获取会话观察者(用户标识)
    if obs is None:
        return {"错误": f"用户 {用户标识} 没有活跃的浏览器会话，请先在浏览器打开页面"}

    freq = str(obs.周期)
    信号映射 = {
        "中枢第三买卖点": f"{freq}_D1MO3_中枢第三买卖点V230602_中枢段DEA穿越2_三买_任意_0",
        "第二买卖点": f"{freq}_D1MO5_第二买卖点V260701_DEA穿越0_二买_任意_0",
        "第一买卖点": f"{freq}_D1M_第一买卖点V260703_MACD背驰_一买_任意_0",
    }
    if 信号集 not in 信号映射:
        return {"错误": f"未知信号集 {信号集}，可选: {list(信号映射.keys())}"}

    分析器 = 立体分析器(obs.符号, [obs.周期, obs.周期 * 5, obs.周期 * 5 * 6], obs.配置)
    信号配置 = get_signals_config([信号映射[信号集]], "signals")
    计算器 = 信号计算器(分析器=分析器, 信号配置=信号配置, 信号模块="signals")

    # 增量喂入已有K线
    for k in obs.普通K线序列:
        分析器.投喂K线(k)
        计算器.更新()

    return {"信号": {k: v for k, v in 计算器.信号.items() if v != "任意_任意_任意_0"}}


if __name__ == "__main__":
    import sys

    传输 = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if 传输 == "stdio":
        mcp.run()
    elif 传输 == "sse":
        mcp.run(transport="sse")
    else:
        print("用法: python chanlun_mcp.py [stdio|sse]")
