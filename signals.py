from collections import OrderedDict


def macd_金叉(观察员: 观察者, **kwargs) -> OrderedDict:
    """MACD 金叉死叉信号 — DIF 与 DEA 的交叉判断

    参数模板："{freq}_D{di}#MACD#{fast}#{slow}#{signal}_MACD交叉V260601"

    **信号逻辑：**

    1. DIF 上穿 DEA（前一根 DIF <= DEA，当前 DIF > DEA）→ 金叉
    2. DIF 下穿 DEA（前一根 DIF >= DEA，当前 DIF < DEA）→ 死叉

    **信号列表：**

    - Signal('15分钟_D1#MACD#13#31#11_MACD交叉V260601_金叉_任意_任意_0')
    - Signal('15分钟_D1#MACD#13#31#11_MACD交叉V260601_死叉_任意_任意_0')

    :param 观察员: 观察者对象
    :param kwargs: 其他参数
        - fast: 快线周期（默认 13）
        - slow: 慢线周期（默认 31）
        - signal: 信号周期（默认 11）
        - di: 信号计算截止倒数第i根K线
    :return: 信号识别结果
    """
    fast = int(kwargs.get("fast", 13))
    slow = int(kwargs.get("slow", 31))
    signal = int(kwargs.get("signal", 11))
    di = int(kwargs.get("di", 1))
    freq = kwargs.get("freq", "15分钟")

    k1, k2, k3 = f"{freq}_D{di}#MACD#{fast}#{slow}#{signal}_MACD交叉V260601".split("_", 2)

    普K序列 = 观察员.普通K线序列
    if len(普K序列) < di + 2:
        return create_single_signal(k1=k1, k2=k2, k3=k3)

    当前K线 = 普K序列[-di]
    前K线 = 普K序列[-di - 1]

    macd_key = f"macd_{fast}_{slow}_{signal}"
    cur_macd = getattr(当前K线.指标, macd_key, None) if 当前K线.指标 else None
    prev_macd = getattr(前K线.指标, macd_key, None) if 前K线.指标 else None

    if cur_macd is None or prev_macd is None:
        return create_single_signal(k1=k1, k2=k2, k3=k3)
    if cur_macd.DIF is None or cur_macd.DEA is None:
        return create_single_signal(k1=k1, k2=k2, k3=k3)
    if prev_macd.DIF is None or prev_macd.DEA is None:
        return create_single_signal(k1=k1, k2=k2, k3=k3)

    if prev_macd.DIF <= prev_macd.DEA and cur_macd.DIF > cur_macd.DEA:
        v1 = "金叉"
    elif prev_macd.DIF >= prev_macd.DEA and cur_macd.DIF < cur_macd.DEA:
        v1 = "死叉"
    else:
        v1 = "任意"

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
