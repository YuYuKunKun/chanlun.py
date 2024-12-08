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

import json
import mmap
import time
import struct
import asyncio
import datetime
import traceback

from enum import Enum
from random import randint, choice
from pathlib import Path
from threading import Thread
from functools import wraps
from typing import List, Self, Optional, Tuple, final, Dict, Any, Set, Final, SupportsInt, Union
from abc import ABCMeta, abstractmethod

import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from termcolor import colored

"""
2	3	5	7	11	13	17	19	23	29	31	37	41	43	47	53	59	61	67	71
73	79	83	89	97	101	103	107	109	113	127	131	137	139	149	151	157	163	167	173
179	181	191	193	197	199	211	223	227	229	233	239	241	251	257	263	269	271	277	281
283	293	307	311	313	317	331	337	347	349	353	359	367	373	379	383	389	397	401	409
419	421	431	433	439	443	449	457	461	463	467	479	487	491	499	503	509	521	523	541
547	557	563	569	571	577	587	593	599	601	607	613	617	619	631	641	643	647	653	659
661	673	677	683	691	701	709	719	727	733	739	743	751	757	761	769	773	787	797	809
811	821	823	827	829	839	853	857	859	863	877	881	883	887	907	911	919	929	937	941
947	953	967	971	977	983	991	997	1009	1013	1019	1021	1031	1033	1039	1049	1051	1061	1063	1069
1087	1091	1093	1097	1103	1109	1117	1123	1129	1151	1153	1163	1171	1181	1187	1193	1201	1213	1217	1223
1229	1231	1237	1249	1259	1277	1279	1283	1289	1291	1297	1301	1303	1307	1319	1321	1327	1361	1367	1373
1381	1399	1409	1423	1427	1429	1433	1439	1447	1451	1453	1459	1471	1481	1483	1487	1489	1493	1499	1511
1523	1531	1543	1549	1553	1559	1567	1571	1579	1583	1597	1601	1607	1609	1613	1619	1621	1627	1637	1657
1663	1667	1669	1693	1697	1699	1709	1721	1723	1733	1741	1747	1753	1759	1777	1783	1787	1789	1801	1811
1823	1831	1847	1861	1867	1871	1873	1877	1879	1889	1901	1907	1913	1931	1933	1949	1951	1973	1979	1987
1993	1997	1999	2003	2011	2017	2027	2029	2039	2053	2063	2069	2081	2083	2087	2089	2099	2111	2113	2129
2131	2137	2141	2143	2153	2161	2179	2203	2207	2213	2221	2237	2239	2243	2251	2267	2269	2273	2281	2287
2293	2297	2309	2311	2333	2339	2341	2347	2351	2357	2371	2377	2381	2383	2389	2393	2399	2411	2417	2423
2437	2441	2447	2459	2467	2473	2477	2503	2521	2531	2539	2543	2549	2551	2557	2579	2591	2593	2609	2617
2621	2633	2647	2657	2659	2663	2671	2677	2683	2687	2689	2693	2699	2707	2711	2713	2719	2729	2731	2741
2749	2753	2767	2777	2789	2791	2797	2801	2803	2819	2833	2837	2843	2851	2857	2861	2879	2887	2897	2903
2909	2917	2927	2939	2953	2957	2963	2969	2971	2999	3001	3011	3019	3023	3037	3041	3049	3061	3067	3079
3083	3089	3109	3119	3121	3137	3163	3167	3169	3181	3187	3191	3203	3209	3217	3221	3229	3251	3253	3257
3259	3271	3299	3301	3307	3313	3319	3323	3329	3331	3343	3347	3359	3361	3371	3373	3389	3391	3407	3413
3433	3449	3457	3461	3463	3467	3469	3491	3499	3511	3517	3527	3529	3533	3539	3541	3547	3557	3559	3571
"""

"""
一、为引申出基本定义的引子概念与定义
1、飞吻：短期均线略略走平后继续按原来趋势进行下去。（14课）

2、唇吻：短期均线靠近长期均线但不跌破或升破，然后按原来趋势继续下去。（14课）

3、湿吻：短期均线跌破或升破长期均线甚至出现反复缠绕，如胶似漆。（14课）

4、女上位：短期均线在长期均线之上。（14课）

5、男上位：短期均线在长期均线之下。（14课）

6、第一类买点：用比较形象的语言描述就是由男上位最后一吻后出现的背驰式下跌构成。（14课）

7、第二类买点：女上位第一吻后出现的下跌构成。（14课）

8、上涨：最近一个高点比前一高点高，且最近一个低点比前一低点高。（15课）

9、下跌：最近一个高点比前一高点低，且最近一个低点比前一低点低。（15课）

10、盘整：最近一个高点比前一高点高，且最近一个低点比前一低点低；或者最近一个高点比前一高点低，且最近一个低点比前一低点高。（15课）

11、缠中说禅趋势力度：前一"吻"的结束与后一"吻"开始由短线均线与长期均线相交所形成的面积。在前后两个同向趋势中,当缠中说禅趋势力度比上一次缠中说禅趋势力度要弱，就形成"背驰"。 （15课）

12、缠中说禅趋势平均力度：当下与前一"吻"的结束时短线均线与长期均线形成的面积除以时间。（15课）

二、基本定义
1、走势：打开走势图看到的就是走势。走势分不同级别。（17课回复、18课）

2、走势类型：上涨、下跌、盘整。（17课回复、18课）

3、趋势：上涨、下跌。（17课回复、18课）

4、缠中说禅走势中枢：某级别走势类型中，被至少三个连续次级别走势类型所重叠的部分，称为缠中说禅走势中枢。换言之，缠中说禅走势中枢就是至少三个连续次级别走势类型重叠部分所构成。（18课）

在实际之中，对最后不能分解的级别，其缠中说禅走势中枢就不能用"至少三个连续次级别走势类型所重叠"定义，而定义为至少三个该级别单位K线重叠部分。（17课）

5、缠中说禅盘整：在任何级别的任何走势中，某完成的走势类型只包含一个缠中说禅走势中枢，就称为该级别的缠中说禅盘整。（17课）

6、缠中说禅趋势：在任何级别的任何走势中，某完成的走势类型至少包含两个以上依次同向的缠中说禅走势中枢，就称为该级别的缠中说禅趋势。该方向向上就称为上涨，向下就称为下跌。（17课）

在趋势里，同级别的前后缠中说禅走势中枢是不能有任何重叠的，这包括任何围绕走势中枢产生的任何瞬间波动之间的重叠。（20课）

三、技术分析基本原理
1、缠中说禅技术分析基本原理一：任何级别的任何走势类型终要完成。（17课）

2、缠中说禅技术分析基本原理二：任何级别任何完成的走势类型，必然包含一个以上的缠中说禅走势中枢。（17课）

四、走势分解定理、原则
1、缠中说禅走势分解定理一：任何级别的任何走势，都可以分解成同级别"盘整"、"下跌"与"上涨"三种走势类型的连接。（17课）

2、缠中说禅走势分解定理二：任何级别的任何走势类型，都至少由三段以上次级别走势类型构成。（17课）

3、缠中说禅走势类型分解原则：一个某级别的走势类型中，不可能出现比该级别更大的中枢，一旦出现，就证明这不是一个某级别的走势类型，而是更大级别走势类型的一部分或几个该级别走势类型的连接。（43课）

4、缠中说禅线段分解定理：线段被破坏，当且仅当至少被有重叠部分的连续三笔的其中一笔破坏。而只要构成有重叠部分的前三笔，那么必然会形成一线段，换言之，线段破坏的充要条件，就是被另一个线段破坏。（65课）

5、缠中说禅笔定理：任何的当下，在任何时间周期的K线图中，走势必然落在一确定的具有明确方向的笔当中（向上笔或向下笔），而在笔当中的位置，必然只有两种情况：一、在分型构造中。二、分型构造确认后延伸为笔的过程中。（91课）

五、走势中枢、走势中枢中心相关定理
1、缠中说禅走势中枢定理一：在趋势中，连接两个同级别"缠中说禅走势中枢"的必然是次级别以下级别的走势类型。（18课）

2、缠中说禅走势中枢定理二：在盘整中，无论是离开还是返回"缠中说禅走势中枢"的走势类型必然是次级别以下的。（18课）

3、缠中说禅走势中枢定理三：某级别"缠中说禅走势中枢"的破坏，当且仅当一个次级别走势离开该"缠中说禅走势中枢"后，其后的次级别回抽走势不重新回到该"缠中说禅走势中枢"内。（18课）

4、缠中说禅走势中枢中心定理一：走势中枢的延伸等价于任意区间[dn，gn]与[ZD，ZG]有重叠。换言之，若有Zn，使得dn>ZG或gn<ZD，则必然产生高级别的走势中枢或趋势及延续。其中GG=max(gn)，G=min(gn)，D=max(dn)，DD=min(dn)，ZG=min(g1，g2)，ZD=max(d1，d2)。（20课）

5、缠中说禅走势中枢中心定理二：前后同级别的两个缠中说禅走势中枢，后GG<前DD等价于下跌及其延续；后DD>前GG等价于上涨及其延续。后ZG<前ZD且后GG≥前DD，或后ZD>前ZG且后DD≤前GG，则等价于形成高级别的走势中枢。（20课）

六、走势级别延续定理
1、缠中说禅走势级别延续定理一：在更大级别缠中说禅走势中枢产生前，该级别走势类型将延续。也就是说，只能是只具有该级别缠中说禅走势中枢的盘整或趋势的延续。（20课）

2、缠中说禅走势级别延续定理二：更大级别缠中说禅走势中枢产生，当且仅当围绕连续两个同级别缠中说禅走势中枢产生的波动区间产生重叠。（20课）

七、买卖点相关定理、定律和程序
1、缠中说禅短差程序：大级别买点介入的，在次级别第一类卖点出现时，可以先减仓，其后在次级别第一类买点出现时回补。（14课）

2、缠中说禅买卖点定律一：任何级别的第二类买卖点都由次级别相应走势的第一类买卖点构成。（17课）

3、第三类买卖点定理：一个次级别走势类型向上离开缠中说禅走势中枢，然后以一个次级别走势类型回试，其低点不跌破ZG，则构成了第三类买点；

一个次级别走势类型向下离开缠中说禅走势中枢，然后以一个次级别走势类型回抽，其高点不升破ZD，则构成第三类卖点。（20课）

（而对于第三类买卖点，其意义就是对付中枢结束的，一个级别的中枢结束，无非面对两种情况，转成更大的中枢或上涨下跌直到形成新的该级别中枢。第三类买卖点就是告诉什么时候发生这种事情的，而在第二、三买卖点之间，都是中枢震荡，这时候，是不会有该级别的买卖点的，因此，如果参与其中的买卖，用的都是低级别的买卖点。）（53课）

4、缠中说禅买卖点的完备性定理：市场必然产生赢利的买卖点，只有第一、二、三类。（21课）

5、缠中说禅升跌完备性定理：市场中的任何向上与下跌，都必然从三类缠中说禅买卖点中的某一类开始以及结束。换言之，市场走势完全由这样的线段构成，线段的端点是某级别三类缠中说禅买卖点中的某一类。（21课）

6、缠中说禅买卖点级别定理：大级别的买卖点必然是次级别以下某一级别的买卖点。（35课）

7、缠中说禅背驰-买卖点定理：任一背驰都必然制造某级别的买卖点，任一级别的买卖点都必然源自某级别走势的背驰。（24课）

8、缠中说禅精确大转折点寻找程序定理：某大级别的转折点，可以通过不同级别背驰段的逐级收缩范围而确定。（27课）

9、缠中说禅趋势转折定律：任何级别的上涨转折都是由某级别的第一类卖点构成的；任何级别的下跌转折都是由某级别的第一类买点构成的。（17课）

10、缠中说禅背驰-转折定理：某级别趋势的背驰将导致该趋势最后一个中枢的级别扩展、该级别更大级别的盘整或该级别以上级别的反趋势。（29课）

11、缠中说禅小背驰-大转折定理：小级别顶背驰引发大级别向下的必要条件是该级别走势的最后一个次级别中枢出现第三类卖点；小级别底背驰引发大级别向上的必要条件是该级别走势的最后一个次级别中枢出现第三类买点。（44课）

12、缠中说禅第一利润最大定理：对于任何固定交易品种，在确定的操作级别下，以上缠中说禅操作模式的利润率最大。

（该模式的关键只参与确定操作级别的盘整与上涨，对盘整用中枢震荡方法处理，保证成本降低以及筹码不丢失（成本为0后是筹码增加，当然，对于小级别的操作，不会出现成本为0的情况），在中枢第三类买点后持股直到新中枢出现继续中枢震荡操作，中途不参与短差。最后，在中枢完成的向上移动出现背驰后抛出所有筹码，完成一次该级别的买卖操作，等待下一个买点出现。）（49课）

13、缠中说禅第二利润最大定理：对于不同交易品种交易中，在确定的操作级别下，以上激进的缠中说禅操作模式的利润率最大。

（还有一种更激进的操作方法，就是不断换股，也就是不参与中枢震荡，只在第三类买点买入，一旦形成新中枢就退出。例如操作级别是30分钟，那么中枢完成向上时一旦出现一个5分钟向下级别后下一个向上的5分钟级别走势不能创新高或出现背驰或盘整背驰，那么一定要抛出，为什么？因为后面一定会出现一个新的30分钟中枢，用这种方法，往往会抛在该级别向上走势的最高点区间。当然，实际上能否达到，那是技术精度的问题，是需要干多了才能干好的。）（49课）

八、补充回复中的定律
1、缠中说禅定律：任何非盘整性的转折性上涨，都是在某一级别的"下跌+盘整+下跌"后形成的。下跌反之。（16课��复）

2、缠中说缠的MACD定律：第一类买点都是在0轴之下背驰形成的，第二类买点都是第一次上0轴后回抽确认形成的。卖点的情况就反过来。

3、上升趋势形成的最精确定义，就是在第一中枢后出现第三类买点并形成非背驰类向上。（107课）

 版权归属： v林羽
 本文链接： https://blog.vlinyu.com/archives/chanlunjiexi-gainian-dingyi-yuanli-dingli
 许可协议： 本文使用《署名-非商业性使用-相同方式共享 4.0 国际 (CC BY-NC-SA 4.0)》协议授权

"""

# __all__ = ["Line", "Bar", "NewBar", "RawBar", "Bi", "Duan", "ZhongShu", "FenXing", "BaseAnalyzer"]
SupportsHL = Union["Line", "NewBar", "RawBar", "Bi", "Duan", "ZhongShu", "FenXing", "Interval", "Pillar"]


def timer(func):
    @wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
        return value

    return wrapper_timer


def ts2int(timestamp: str):
    return int(time.mktime(datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timetuple()))


def int2ts(timestamp: int):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timestamp)))


class Freq(Enum):
    # 60 180 300 900 1800 3600 7200 14400 21600 43200 86400 259200
    S1: int = 1
    S3: int = 3
    S5: int = 5
    S12: int = 12
    m1: int = 60 * 1
    m3: int = 60 * 3  # 180
    m5: int = 60 * 5  # 300
    m15: int = 60 * 15  # 900
    m30: int = 60 * 30  # 1800
    H1: int = 60 * 60 * 1  # 3600
    H2: int = 60 * 60 * 2  # 7200
    H4: int = 60 * 60 * 4  # 14400
    H6: int = 60 * 60 * 6  # 21600
    H12: int = 60 * 60 * 12  # 43200
    D1: int = 60 * 60 * 24  # 86400
    D3: int = 60 * 60 * 24 * 3  # 259200

    def __int__(self):
        return self.value


class Pillar:
    def __init__(self, high: float, low: float):
        assert high > low
        self.high = high
        self.low = low


class Shape(Enum):
    D = "底分型"
    G = "顶分型"
    S = "上升分型"
    X = "下降分型"
    T = "喇叭口型"

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Direction(Enum):
    Up = "向上"
    Down = "向下"
    JumpUp = "缺口向上"
    JumpDown = "缺口向下"
    NextUp = "连接向上"  # 高点与后一 低点相同
    NextDown = "连接向下"  # 低点与后一 高点相同

    Left = "左包右"  # 顺序包含
    Right = "右包左"  # 逆序包含

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __int__(self):
        match self:
            case Direction.Up:
                return 1
            case Direction.Down:
                return -1
            case Direction.JumpUp:
                return 2
            case Direction.JumpDown:
                return -2
            case Direction.NextUp:
                return 3
            case Direction.NextDown:
                return -3
            case Direction.Left:
                return 7
            case Direction.Right:
                return 9

    def reversal(self) -> Self:
        match self:
            case Direction.Up:
                return Direction.Down
            case Direction.Down:
                return Direction.Up
            case Direction.JumpUp:
                return Direction.JumpDown
            case Direction.JumpDown:
                return Direction.JumpUp
            case Direction.NextUp:
                return Direction.NextDown
            case Direction.NextDown:
                return Direction.NextUp
            case Direction.Left:
                return Direction.Right
            case Direction.Right:
                return Direction.Left

    def is_down(self) -> bool:
        match self:
            case Direction.Down | Direction.JumpDown | Direction.NextDown:
                return True
            case _:
                return False

    def is_up(self) -> bool:
        match self:
            case Direction.Up | Direction.JumpUp | Direction.NextUp:
                return True
            case _:
                return False

    def is_jump(self) -> bool:
        match self:
            case Direction.JumpDown | Direction.JumpUp:
                return True
            case _:
                return False

    def is_include(self) -> bool:
        match self:
            case Direction.Left | Direction.Right:
                return True
            case _:
                return False

    def is_nexts(self):
        match self:
            case Direction.NextUp | Direction.NextDown:
                return True
            case _:
                return False

    @staticmethod
    def generator(obj: int | list, directions):
        if type(obj) is int:
            print(obj)
            i: int = obj
            while i >= 0:
                yield choice(directions)
                i -= 1
        else:
            for direction in obj:
                yield direction


class ChanException(Exception):
    """exception"""

    ...


def _print(*args, **kwords):
    result = []
    for i in args:
        if i in ("小阳", True, Shape.D, "底分型") or "小阳" in str(i):
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
    if not 1:
        _print(*args, **kwords)


def bdp(*args, **kwargs):
    if not 1:
        dp(*args, **kwargs)


def ddp(*args, **kwargs):
    if not 0:
        dp(*args, **kwargs)


def zsdp(*args, **kwargs):
    if not 1:
        dp(*args, **kwargs)


def double_relation(left: SupportsHL, right: SupportsHL) -> Direction:
    """
    两个带有[low, high]对象的所有关系
    """
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

        if left.high == right.low:
            relation = Direction.NextUp

    elif (left.low > right.low) and (left.high > right.high):
        relation = Direction.Down  # "下跌"
        if left.low > right.high:
            relation = Direction.JumpDown  # "跳跌"
        if left.low == right.high:
            relation = Direction.NextDown

    return relation


def triple_relation(left: SupportsHL, mid: SupportsHL, right: SupportsHL, use_right: bool = False, ignore: bool = False) -> tuple[Optional[Shape], tuple[Direction, Direction], Optional[Pillar]]:
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

    zg = min(left.high, mid.high, right.high)
    zd = max(left.low, mid.low, right.low)
    if zg > zd:
        pillar = Pillar(high=zg, low=zd)
    else:
        pillar = None

    shape = None
    lm = double_relation(left, mid)
    mr = double_relation(mid, right)
    # lr = double_relation(left, right)
    match (lm, mr):
        case (Direction.Left, _):
            if ignore:
                ...  # print("顺序包含 lm", left, mid)
            else:
                raise ChanException("顺序包含 lm", left, mid)
        case (_, Direction.Left):
            if ignore:
                ...  # print("顺序包含 mr", mid, right)
            else:
                raise ChanException("顺序包含 mr", mid, right)

        case (Direction.Up | Direction.JumpUp | Direction.NextUp, Direction.Up | Direction.JumpUp | Direction.NextUp):
            shape = Shape.S
        case (Direction.Up | Direction.JumpUp | Direction.NextUp, Direction.Down | Direction.JumpDown | Direction.NextDown):
            shape = Shape.G
        case (Direction.Up | Direction.JumpUp | Direction.NextUp, Direction.Right) if use_right:
            shape = Shape.S

        case (Direction.Down | Direction.JumpDown | Direction.NextDown, Direction.Up | Direction.JumpUp | Direction.NextUp):
            shape = Shape.D
        case (Direction.Down | Direction.JumpDown | Direction.NextDown, Direction.Down | Direction.JumpDown | Direction.NextDown):
            shape = Shape.X
        case (Direction.Down | Direction.JumpDown | Direction.NextDown, Direction.Right) if use_right:
            shape = Shape.X

        case (Direction.Right, Direction.Up | Direction.JumpUp | Direction.NextUp) if use_right:
            shape = Shape.D
        case (Direction.Right, Direction.Down | Direction.JumpDown | Direction.NextDown) if use_right:
            shape = Shape.G
        case (Direction.Right, Direction.Right) if use_right:
            shape = Shape.T
        case _:
            print("未匹配的关系", use_right, lm, mr)

    if shape is None:
        ...  # print(colored("triple_relation: ", "red"), shape, (lm, mr), left, mid, right)

    return shape, (lm, mr), pillar


class Command:
    APPEND: Final[str] = "APPEND"
    MODIFY: Final[str] = "MODIFY"
    REMOVE: Final[str] = "REMOVE"

    def __init__(self, cmd: str, info: str) -> None:
        self.cmd = cmd
        self.info = info

    def __str__(self):
        # return f"{self.cmd.upper()}({self.info})"
        return f"{self.cmd.upper()}"

    @classmethod
    def Append(cls, stamp: str) -> Self:
        return Command(cls.APPEND, stamp)

    @classmethod
    def Modify(cls, stamp: str) -> Self:
        return Command(cls.MODIFY, stamp)

    @classmethod
    def Remove(cls, stamp: str) -> Self:
        return Command(cls.REMOVE, stamp)


@final
class BSPoint:
    __slots__ = "info", "tp", "dt", "price", "valid", "creation_offset", "fix_offset", "stamp"

    def __init__(self, info: str, tp: str, dt: datetime, price: float, valid: bool, creation_offset: int, fix_offset: int, stamp: str) -> None:
        self.info = info
        self.tp = tp
        self.dt = dt
        self.price = price
        self.valid = valid
        self.creation_offset = creation_offset
        self.fix_offset = fix_offset
        self.stamp = stamp


class ZShuCondition(Enum):
    """中枢的三种情况"""

    New: str = "新生"
    Continue: str = "延续"
    Expand: str = "扩张"


@final
class ChanConfig:
    __slots__ = "ANALYZER_CALC_BI", "ANALYZER_CALC_BI_ZS", "ANALYZER_CALC_XD", "ANALYZER_CALC_XD_ZS", "ANALYZER_SHON_TV", "BI_EQUAL", "BI_FENGXING", "BI_JUMP", "BI_LENGTH", "MACD_FAST_PERIOD", "MACD_SIGNAL_PERIOD", "MACD_SLOW_PERIOD", "ANALYZER_CALC_MACD"

    def __init__(self):
        self.BI_LENGTH = 5  # 成BI最低长度
        self.BI_JUMP = True  # 跳空是否判定为 NewBar
        self.BI_EQUAL = True  # True: 一笔终点存在多个终点时，取最后一个, False: 用max/min时只会取第一个值，会有这个情况 当首个出现时 小于[BI_LENGTH]而后个则大于[BI_LENGTH]但max/min函数不会取后一个. 例子: bitstamp btcusd 30m [2024-06-03 17:00]至[2024-06-05 01:00] 中 [NewBar(63, 2024-06-03 22:30:00, 69318.0, 68553.0, D, 2), NewBar(94, 2024-06-04 17:30:00, 68768.0, 68553.0, D, 1)]
        self.BI_FENGXING = False  # True: 一笔起始分型高低包含整支笔对象则不成笔, False: 只判断分型中间数据是否包含

        self.ANALYZER_CALC_BI = True  # 是否计算BI
        self.ANALYZER_CALC_XD = True  # 是否计算XD
        self.ANALYZER_CALC_BI_ZS = True  # 是否计算BI中枢
        self.ANALYZER_CALC_XD_ZS = True  # 是否计算XD中枢
        self.ANALYZER_CALC_MACD = True  # 是否计算MACD
        self.ANALYZER_SHON_TV = True
        self.MACD_FAST_PERIOD = 12.0
        self.MACD_SLOW_PERIOD = 26.0
        self.MACD_SIGNAL_PERIOD = 9.0


@final
class MACD:
    __slots__ = "fast_ema", "slow_ema", "DIF", "DEA", "fastperiod", "slowperiod", "signalperiod"

    def __init__(self, fast_ema: float, slow_ema: float, dif: float, dea: float, fastperiod: float = 12.0, slowperiod: float = 26.0, signalperiod: float = 9.0):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.DIF = dif
        self.DEA = dea
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

    @classmethod
    def calc(cls, pre: "RawBar", bar: "RawBar") -> Self:
        value = bar.close
        _fast_ema = (2.0 * value + (pre.macd.fastperiod - 1.0) * pre.macd.fast_ema) / (pre.macd.fastperiod + 1.0)
        _slow_ema = (2.0 * value + (pre.macd.slowperiod - 1.0) * pre.macd.slow_ema) / (pre.macd.slowperiod + 1.0)
        _dif = _fast_ema - _slow_ema
        _dea = (2.0 * _dif + (pre.macd.signalperiod - 1.0) * pre.macd.DEA) / (pre.macd.signalperiod + 1.0)
        macd = MACD(_fast_ema, _slow_ema, _dif, _dea, fastperiod=pre.macd.fastperiod, slowperiod=pre.macd.slowperiod, signalperiod=pre.macd.signalperiod)
        bar.macd = macd
        return macd


class Observer(metaclass=ABCMeta):
    thread = None
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    TIME = 0.01

    @abstractmethod
    def notify(self, obj: Any, cmd: Command): ...


class Interval:
    __slots__ = "index", "elements", "__high", "__low"

    def __init__(self, elements: List, high: float, low: float):
        self.elements = elements
        self.__high = high
        self.__low = low
        self.index = 0

    def __str__(self):
        return f"Interval({self.index}, {len(self)}, {self.__high}, {self.__low})"

    def __len__(self):
        return len(self.elements)

    def __iter__(self):
        return iter(self.elements)

    @property
    def high(self) -> int | float:
        return self.__high

    @property
    def low(self) -> int | float:
        return self.__low

    def check(self) -> Optional[bool]:
        tmp = Interval.new(self.elements)
        if tmp:
            for i in range(3, len(self.elements) - 1):
                hl = self.elements[i]
                if double_relation(self, hl).is_jump():
                    if i != len(self.elements) - 1:
                        self.elements = self.elements[:i]
                    return None
            return True
        return False

    @classmethod
    def new(cls, elements) -> Optional["Interval"]:
        if len(elements) < 3:
            return

        lr = double_relation(elements[0], elements[2])
        if lr.is_jump():
            return

        lm = double_relation(elements[0], elements[1])
        if lm.is_jump():
            return

        mr = double_relation(elements[1], elements[2])
        if mr.is_jump():
            return

        high = min([hl.high for hl in elements[:3]])
        low = max([hl.low for hl in elements[:3]])
        return cls(elements, high, low)

    @classmethod
    def analyzer(cls, hls: List, intervals: List["Interval"], observer: Observer):
        if not intervals:
            for i in range(1, len(hls) - 1):
                new = cls.new([hls[i - 1], hls[i], hls[i + 1]])
                if new is not None:
                    intervals.append(new)
                    observer.notify(new, Command.Append("nb"))
                    return cls.analyzer(hls, intervals, observer)

        else:
            last = intervals[-1]
            flag: Optional[bool] = last.check()
            if flag is None:
                index = hls.index(last.elements[2]) + 1
            elif flag is True:
                index = hls.index(last.elements[-1]) + 1
            else:
                intervals.pop()
                observer.notify(last, Command.Remove("nb"))
                return cls.analyzer(hls, intervals, observer)

            observer.notify(last, Command.Modify("nb"))

            while index == -1:
                try:
                    index = hls.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    if len(last) > 3:
                        last.elements.pop()
                    else:
                        drop = intervals.pop()
                        observer.notify(drop, Command.Remove("nb"))
                        return cls.analyzer(hls, intervals, observer)

            elements = []
            for hl in hls[index:]:
                if double_relation(last, hl).is_jump():
                    if not elements:
                        elements.append(last.elements[-1])
                    elements.append(hl)
                else:
                    if not elements:
                        if hl not in last.elements:
                            last.elements.append(hl)
                        observer.notify(last, Command.Modify("nb"))
                    else:
                        elements.append(hl)

                if len(elements) >= 3:
                    new = cls.new(elements[:])
                    if new is None:
                        elements.pop(0)
                    else:
                        intervals.append(new)
                        new.index = last.index + 1
                        observer.notify(new, Command.Append("nb"))
                        last = new
                        elements.clear()


class RawBar:
    __slots__ = "__open", "high", "low", "__close", "volume", "dt", "index", "macd"

    def __init__(self, dt: datetime, o: float, h: float, low: float, c: float, v: float, i: int):
        self.dt: datetime = dt
        self.__open: float = o
        self.high: float = h
        self.low: float = low
        self.__close: float = c
        self.volume: float = v
        self.index: int = i
        self.macd = MACD(c, c, 0.0, 0.0)

    @property
    def open(self) -> float:
        return self.__open

    @property
    def close(self) -> float:
        return self.__close

    @open.setter
    def open(self, v: float):
        self.__open = v

    @close.setter
    def close(self, v: float):
        self.__close = v

    @property
    def direction(self):
        if self.open > self.close:
            return Direction.Down
        else:
            return Direction.Up

    def __str__(self):
        return f"{self.__class__.__name__}({self.dt}, {self.high}, {self.low}, index={self.index})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.dt}, {self.high}, {self.low}, index={self.index})"

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

    def to_new_bar(self, pre) -> "NewBar":
        return NewBar(
            dt=self.dt,
            high=self.high,
            low=self.low,
            direction=self.direction,
            volume=self.volume,
            raw_index=self.index,
            pre=pre,
        )

    @classmethod
    def bars_save_as_dat(cls, path: str, bars: List):
        with open(path, "wb") as f:
            for bar in bars:
                f.write(bytes(bar))
        print(f"Saved {len(bars)} bars to {path}")

    @classmethod
    def from_be_bytes(cls, buf: bytes) -> "RawBar":
        timestamp, open_, high, low, close, vol = struct.unpack(">6d", buf[: struct.calcsize(">6d")])
        return cls(
            dt=datetime.datetime.fromtimestamp(timestamp),
            o=open_,
            h=high,
            low=low,
            c=close,
            v=vol,
            i=0,
        )

    @classmethod
    def from_csv_file(cls, path: str) -> List["RawBar"]:
        raws: List["RawBar"] = []
        with open(path, "r") as f:
            stamps = f.readline().split(",")
            ts = stamps.index("timestamp")
            o = stamps.index("open")
            h = stamps.index("high")
            low = stamps.index("low")
            c = stamps.index("close")
            v = stamps.index("volume")
            i = 0
            for line in f.readlines():
                info = line.split(",")
                rb = RawBar(datetime.datetime.strptime(info[ts], "%Y-%m-%d %H:%M:%S"), float(info[o]), float(info[h]), float(info[low]), float(info[c]), float(info[v]), i)
                raws.append(rb)
                i += 1

        return raws


class NewBar(RawBar):
    __slots__ = "__shape", "__raw_start_index", "raw_end_index", "__direction"

    def __init__(
        self,
        dt: datetime,
        high: float,
        low: float,
        direction: Direction,
        volume: float,
        raw_index: int,
        pre: Optional["NewBar"] = None,
    ):
        assert high >= low
        if direction == Direction.Down:
            close = low
            _open = high
        else:
            close = high
            _open = low
        super().__init__(dt, _open, high, low, close, volume, 0)
        self.__shape: Shape = Shape.S

        if direction is Direction.Up:
            self.__shape = Shape.S
        else:
            self.__shape = Shape.X

        self.__raw_start_index: int = raw_index
        self.raw_end_index: int = raw_index
        self.__direction: Direction = direction

        if pre is not None:
            self.index = pre.index + 1

            if double_relation(pre, self).is_include():
                raise ChanException(f"\n    {double_relation(pre, self)}\n    {pre},\n    {self}")

    def __str__(self):
        return f"{self.__class__.__name__}({self.index}, {self.dt}, {self.high}, {self.low}, {self.shape})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index}, {self.dt}, {self.high}, {self.low}, {self.shape})"

    @property
    def raw_start_index(self) -> int:
        return self.__raw_start_index

    @property
    def timestamp(self) -> int:
        return int(self.dt.timestamp())

    @property
    def direction(self) -> Direction:
        return self.__direction

    @property
    def speck(self) -> float:
        if self.shape is Shape.G:
            return self.high
        elif self.shape is Shape.S:
            return self.high
        elif self.shape is Shape.D:
            return self.low
        elif self.shape is Shape.X:
            return self.low
        else:
            print("NewBar.speck: shape is None")
            return self.high

    @property
    def shape(self) -> Optional[Shape]:
        return self.__shape

    @shape.setter
    def shape(self, shape: Shape):
        self.__shape = shape

    @property
    def open(self) -> float:
        return self.high if self.direction == Direction.Down else self.low

    @property
    def close(self) -> float:
        return self.low if self.direction == Direction.Down else self.high

    @classmethod
    def generate(cls, bar: "NewBar", direction: Direction, seconds: int, half: bool = False) -> Self:
        offset = datetime.timedelta(seconds=seconds)
        dt: datetime = bar.dt + offset
        volume: float = 998
        raw_index: int = bar.raw_start_index + 1
        high: float = 0
        low: float = 0
        d = bar.high - bar.low
        match direction:
            case Direction.Up:
                i = d * 0.5 if half else randint(int(d * 0.1279), int(d * 0.883))
                low: float = bar.low + i
                high: float = bar.high + i
            case Direction.Down:
                i = d * 0.5 if half else randint(int(d * 0.1279), int(d * 0.883))
                low: float = bar.low - i
                high: float = bar.high - i
            case Direction.JumpUp:
                i = d * 1.5 if half else randint(int(d * 1.1279), int(d * 1.883))
                low: float = bar.low + i
                high: float = bar.high + i
            case Direction.JumpDown:
                i = d * 1.5 if half else randint(int(d * 1.1279), int(d * 1.883))
                low: float = bar.low - i
                high: float = bar.high - i
            case Direction.NextUp:
                i = bar.high - bar.low
                high: float = bar.high + i
                low: float = bar.high
            case Direction.NextDown:
                i = bar.high - bar.low
                high: float = bar.low
                low: float = bar.low - i
        nb = NewBar(dt, high, low, Direction.Up if direction.is_up() else Direction.Down, volume, raw_index, bar)
        nb.index = bar.index + 1
        assert double_relation(bar, nb) is direction, (direction, double_relation(bar, nb))
        return nb

    @classmethod
    def get_fx(cls, bars: List["NewBar"], bar: "NewBar") -> "FenXing":
        i = bars.index(bar)
        return FenXing(bars[i - 1], bars[i], bars[i + 1])

    @classmethod
    def merger(cls, pre: Optional["NewBar"], bar: "NewBar", next_bar: RawBar) -> Optional["NewBar"]:
        if not double_relation(bar, next_bar).is_include():
            nb = next_bar.to_new_bar(bar)
            nb.index = bar.index + 1
            return nb

        if next_bar.index - 1 != bar.raw_end_index:
            raise ChanException(f"NewBar.merger: 不可追加不连续元素 bar.raw_end_index: {bar.raw_end_index}, next_bar.index: {next_bar.index}.")

        direction = Direction.Up
        if pre is not None:
            if double_relation(pre, bar).is_down():
                direction = Direction.Down

        func = max
        if direction is Direction.Down:
            func = min
        bar.high = func(bar.high, next_bar.high)
        bar.low = func(bar.low, next_bar.low)
        bar.raw_end_index = next_bar.index

        if pre is not None:
            bar.index = pre.index + 1
        return None


class FenXing:
    __slots__ = "index", "left", "mid", "right"

    def __init__(self, left: NewBar, mid: NewBar, right: NewBar, index: int = 0):
        self.left = left
        self.mid = mid
        self.right = right
        self.index = index

    @property
    def dt(self) -> datetime.datetime:
        return self.mid.dt

    @property
    def shape(self) -> Shape:
        return self.mid.shape

    @property
    def speck(self) -> float:
        return self.mid.speck

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

    def get_shape(self) -> Shape:
        shape, (_, _), _ = triple_relation(self.left, self.mid, self.right)
        return shape

    def get_relations(self) -> (Direction, Direction):
        _, (lm, mr), _ = triple_relation(self.left, self.mid, self.right)
        return lm, mr

    @staticmethod
    def get_fenxing(bars: List[NewBar], mid: NewBar) -> "FenXing":
        index = bars.index(mid)
        return FenXing(bars[index - 1], mid, bars[index + 1])

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


class Line(metaclass=ABCMeta):
    __slots__ = "pre", "next", "index", "__start", "__end", "__stamp", "__elements"

    def __init__(self, start: FenXing, end: FenXing, index: int, elements: List | Set, stamp: str = "Line"):
        self.index: int = index
        self.pre: Optional[Self] = None
        self.next: Optional[Self] = None
        self.__start = start
        self.__end = end
        self.__stamp = stamp
        self.__elements = elements

    def __len__(self):
        return len(self.elements)

    def __iter__(self):
        return iter(self.elements)

    def __hash__(self):
        return hash(f"{self.stamp} {self.start.mid}")

    def __eq__(self, other):
        return type(other) is self and self.stamp == other.stamp and self.start == other.start and self.end == other.end and self.elements == other.elements and self.index == other.index

    @property
    @final
    def stamp(self) -> str:
        return self.__stamp

    @property
    @final
    def elements(self) -> List:
        return self.__elements

    @elements.setter
    def elements(self, elements: List):
        self.__elements = elements

    @property
    def start(self) -> FenXing:
        return self.__start

    @property
    def end(self) -> FenXing:
        return self.__end

    @end.setter
    @final
    def end(self, end: FenXing):
        self.__end = end

    @property
    @final
    def direction(self) -> Direction:
        if self.start.shape is Shape.G and self.end.shape is Shape.D:
            return Direction.Down
        elif self.start.shape is Shape.D and self.end.shape is Shape.G:
            return Direction.Up
        else:
            raise ChanException(f"{self.stamp}.direction: {self.start.shape}, {self.end.shape}, {self.stamp}")

    @property
    def high(self) -> float:
        if self.direction == Direction.Down:
            return self.start.speck
        else:
            return self.end.speck

    @property
    def low(self) -> float:
        if self.direction == Direction.Up:
            return self.start.speck
        else:
            return self.end.speck

    @property
    def open(self) -> float:
        if self.direction == Direction.Down:
            return self.high
        else:
            return self.low

    @property
    def close(self) -> float:
        if self.direction == Direction.Up:
            return self.high
        else:
            return self.low

    def is_previous(self, line: "Line") -> bool:
        return line.end is self.start

    def is_next(self, line: "Line") -> bool:
        return self.end is line.start

    def get_line(self) -> "Line":
        return Line(self.start, self.end, self.index, self.elements, self.stamp)

    def get_bars(self, bars: list) -> List[NewBar]:
        return bars[bars.index(self.start.mid) : bars.index(self.end.mid) + 1]

    @classmethod
    def append(cls, lines: List["Line"], line: "Line"):
        if lines and not lines[-1].is_next(line):
            raise ChanException("Line.append 不连续", lines[-1], line)

        if lines:
            line.index = lines[-1].index + 1
            line.pre = lines[-1]
            if len(lines) > 1:
                lines[-2].next = lines[-1]

        lines.append(line)

    @classmethod
    def pop(cls, lines: List["Line"], line: "Line") -> Optional["Line"]:
        if not lines:
            return

        if lines[-1] is line:
            drop = lines.pop()
            return drop
        raise ChanException("Line.pop 弹出数据不在列表中")

    @classmethod
    @final
    def create(cls, obj: List | "Line", stamp: str) -> "Line":
        if type(obj) is list:
            lines: List["Line"] = obj[:]
            return Line(lines[0].start, lines[-1].end, 0, lines, stamp)
        line: "Line" = obj
        return Line(line.start, line.end, 0, [line], stamp)


class Lines:
    def __init__(self, elements: List[Line]):
        self.__elements = elements

    def __len__(self):
        return len(self.__elements)

    def __iter__(self):
        return iter(self.__elements)

    def __next__(self):
        return next(self)

    def __getitem__(self, index):
        return self.__elements[index]

    def __setitem__(self, index, value):
        self.__elements[index] = value

    def __delitem__(self, index):
        del self.__elements[index]

    def append(self, element: Line):
        length = len(self.__elements)
        if length > 0:
            last = self.__elements[-1]
            assert last.end is element.start
            if last.index + 1 != element.index:
                element.index = last.index + 1
                element.pre = last
                if length > 1:
                    pre = self.__elements[-2]
                    pre.next = last

        self.__elements.append(element)

    def pop(self, index=-1):
        return self.__elements.pop(index)

    def index(self, element: Line):
        return self.__elements.index(element)

    def clear(self):
        self.__elements.clear()

    def reset_line_index(self):
        """reset line index"""
        for index, element in enumerate(self.__elements):
            element.index = index
        print("Lines reset line index done!", len(self.__elements))

    def reset_line_next_and_pre(self):
        for i in range(1, len(self.__elements)):
            if hasattr(self.__elements[i - 1], "next"):
                self.__elements[i - 1].next = self.__elements[i]
            if hasattr(self.__elements[i - 1], "pre"):
                self.__elements[i].pre = self.__elements[i - 1]


@final
class FeatureSequence(Line):
    def __init__(self, elements: Set[Line]):
        start: FenXing = tuple(elements)[0].start
        end: FenXing = tuple(elements)[0].end
        super().__init__(start, end, 0, elements, f"FeatureSequence<{tuple(elements)[0].stamp if len(elements) > 0 else None}>")

    def __str__(self):
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)}, {self.stamp})"

    def __repr__(self):
        return f"特征序列({self.direction}, {self.start.dt}, {self.end.dt}, {len(self.elements)}, {self.stamp})"

    @property
    def start(self) -> FenXing:
        direction = tuple(self.elements)[0].direction
        if direction is Direction.Down:  # Down特征序列 为 Up线段, 取高高
            func = max
        else:
            func = min
        fx = func([line.start for line in self.elements], key=lambda o: o.speck)
        assert fx.shape in (Shape.G, Shape.D)
        return fx

    @property
    def end(self) -> FenXing:
        direction = tuple(self.elements)[0].direction
        if direction is Direction.Down:  # Down特征序列 为 Up线段, 取高高
            func = max
        else:
            func = min
        fx = func([line.end for line in self.elements], key=lambda o: o.speck)
        assert fx.shape in (Shape.G, Shape.D)
        return fx

    @property
    def high(self) -> float:
        return max([self.end, self.start], key=lambda fx: fx.speck).speck

    @property
    def low(self) -> float:
        return min([self.end, self.start], key=lambda fx: fx.speck).speck

    def add(self, line: Line):
        direction = tuple(self.elements)[0].direction
        if line.direction != direction:
            raise ChanException("方向不匹配", direction, line, self)
        self.elements.add(line)

    def remove(self, line: Line):
        direction = tuple(self.elements)[0].direction
        if line.direction != direction:
            raise ChanException("方向不匹配", direction, line, self)

        try:
            self.elements.remove(line)
        except Exception as e:
            print(self)
            raise e

    @classmethod
    def analyzer(cls, lines: List[Line], direction: Direction, combines: Tuple[Direction] = (Direction.Left,)) -> Tuple[Optional["FeatureSequence"], Optional["FeatureSequence"], Optional["FeatureSequence"]]:
        if combines is None:
            combines = (Direction.Left,)
        features: List[FeatureSequence] = []
        for obj in lines:
            if obj.direction is direction:
                if len(features) >= 3:
                    left, mid, right = features[-3], features[-2], features[-1]
                    shape, (_, _), _ = triple_relation(left, mid, right, use_right=True, ignore=True)
                    if (direction is Direction.Up and shape is Shape.G and obj.high > mid.high) or (direction is Direction.Down and shape is Shape.D and obj.low < mid.low):
                        start = min(mid.elements, key=lambda o: o.index)
                        end = max(right.elements, key=lambda o: o.index)
                        elements = lines[lines.index(start) : lines.index(end) + 1]
                        fake = Line(start.start, end.end, 0, elements, f"Fake-{start.stamp}")
                        feature = FeatureSequence({fake})
                        features.pop()
                        features[-1] = feature

                continue
            if features:
                last = features[-1]

                if double_relation(last, obj) in combines:
                    last.add(obj)
                else:
                    features.append(FeatureSequence({obj}))
            else:
                features.append(FeatureSequence({obj}))

        length = len(features)
        if length == 1:
            return features[0], None, None
        if length == 2:
            return features[0], features[1], None
        if length >= 3:
            relation = double_relation(features[-2], features[-1])
            if direction is Direction.Up:
                if relation.is_down():
                    return features[-3], features[-2], features[-1]
                else:
                    return features[-2], features[-1], None
            else:
                if relation.is_up():
                    return features[-3], features[-2], features[-1]
                else:
                    return features[-2], features[-1], None

        return None, None, None


class ZhongShu:
    __slots__ = "index", "elements", "third", "__stamp", "__direction"

    def __init__(self, direction: Direction, lines: List[Line]):
        self.index: int = 0
        self.__direction = direction
        self.elements: List[Line] = list(lines)
        self.third: Optional[Line] = None
        self.__stamp = lines[0].stamp

    def __str__(self):
        return f"{self.stamp}中枢({self.index}, {self.direction}, {self.third is not None}, {self.zg}, {self.zd}, elements size={len(self.elements)})"

    def __repr__(self):
        return f"{self.stamp}中枢({self.index}, {self.direction}, {self.third is not None}, {self.zg}, {self.zd}, elements size={len(self.elements)})"

    @property
    def stamp(self) -> str:
        return f"ZhongShu<{self.__stamp}>"

    @property
    def left(self) -> Optional[Line]:
        return self.elements[0] if self.elements else None

    @property
    def mid(self) -> Optional[Line]:
        return self.elements[1] if len(self.elements) > 1 else None

    @property
    def right(self) -> Optional[Line]:
        return self.elements[2] if len(self.elements) > 2 else None

    @property
    def direction(self) -> Direction:
        return self.__direction
        # return Direction.Down if self.start.shape is Shape.D else Direction.Up

    @property
    def zg(self) -> float:
        return min(self.elements[:3], key=lambda o: o.high).high

    @property
    def zd(self) -> float:
        return max(self.elements[:3], key=lambda o: o.low).low

    @property
    def g(self) -> float:
        return min(self.elements, key=lambda o: o.high).high

    @property
    def d(self) -> float:
        return max(self.elements, key=lambda o: o.low).low

    @property
    def gg(self) -> float:
        return max(self.elements, key=lambda o: o.high).high

    @property
    def dd(self) -> float:
        return min(self.elements, key=lambda o: o.low).low

    @property
    def high(self) -> float:
        return self.zg

    @property
    def low(self) -> float:
        return self.zd

    @property
    def start(self) -> FenXing:
        return self.elements[0].start

    @property
    def end(self) -> FenXing:
        return self.elements[-1].end

    @property
    def last(self) -> Line:
        return self.elements[-1]

    def update(self, lines: List[Line]) -> bool:
        i = self.elements[-1].index

        while 1:
            try:
                lines.index(self.elements[-1])
                break
            except ValueError:
                _ = Line.pop(self.elements, self.elements[-1])

        fixed = False
        for line in lines:
            if self.elements[-1].is_next(line):
                self.elements.append(line)
                fixed = True
                if line.index == i:
                    break
        return fixed

    def check(self) -> bool:
        return double_relation(self.left, self.right) in (
            Direction.Down,
            Direction.Up,
            Direction.Left,
            Direction.Right,
        )

    def get_elements(self) -> List[Line]:
        elements: List[Line] = self.elements[:]
        if self.third is not None:
            elements.append(self.third)
        return elements

    @classmethod
    def append(cls, zss: List["ZhongShu"], zs: "ZhongShu", observer: Observer):
        if zss:
            zs.index = zss[-1].index + 1
            if zss[-1].get_elements()[-1].index > zs.get_elements()[-1].index:
                raise ChanException()
        zss.append(zs)
        zsdp(f"ZhongShu.append: {zs}")
        observer and observer.notify(zs, Command.Append(zs.stamp + "_zs"))

    @classmethod
    def pop(cls, zss: List["ZhongShu"], zs: "ZhongShu", observer: Observer) -> Optional["ZhongShu"]:
        if not zss:
            return
        if zss[-1] is zs:
            zsdp(f"ZhongShu.pop: {zs}")
            observer and observer.notify(zs, Command.Remove(zs.stamp + "_zs"))
            return zss.pop()

    @classmethod
    def new(cls, elements: List[Line]) -> Optional["ZhongShu"]:
        if Interval.new(elements) is not None:
            return ZhongShu(elements[1].direction, elements)

    @classmethod
    def analyzer(cls, lines: List[Line], zss: List["ZhongShu"], observer: Optional[Observer]):
        if not lines:
            return

        if not zss:
            for i in range(1, len(lines) - 1):
                left, mid, right = lines[i - 1], lines[i], lines[i + 1]
                new = cls.new([left, mid, right])
                if new is not None:
                    if left.index == 0:
                        continue  # 方便计算走势

                    cls.append(zss, new, observer)
                    return cls.analyzer(lines, zss, observer)

        else:
            last = zss[-1]
            tmp = Interval.new(last.elements)
            if tmp is None:
                cls.pop(zss, last, observer)
                return cls.analyzer(lines, zss, observer)
            else:
                if last.high == tmp.high and last.low == tmp.low:
                    ...
                else:
                    cls.pop(zss, last, observer)
                    return cls.analyzer(lines, zss, observer)

            if last.third is not None:
                if not double_relation(last, last.third).is_jump():
                    last.elements.append(last.third)
                    last.third = None
                    observer and observer.notify(last, Command.Modify(last.stamp))

            while 1:
                try:
                    index = lines.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    if len(last.elements) > 3:
                        last.elements.pop()
                        observer and observer.notify(last, Command.Modify(last.stamp))
                    else:
                        cls.pop(zss, last, observer)
                        return cls.analyzer(lines, zss, observer)

            elements = []
            for hl in lines[index:]:
                if double_relation(last, hl).is_jump():
                    elements.append(hl)
                    if last.elements[-1].is_next(hl):
                        last.third = hl
                else:
                    if not elements:
                        last.elements.append(hl)
                        observer and observer.notify(last, Command.Modify(last.stamp))
                    else:
                        elements.append(hl)

                if len(elements) >= 3:
                    new = cls.new(elements[:])
                    if new is None:
                        elements.pop(0)
                    else:
                        relation = double_relation(last, new)
                        if relation.is_up():
                            if elements[0].direction == Direction.Up:
                                elements.pop(0)
                                continue
                        elif relation.is_down():
                            if elements[0].direction == Direction.Down:
                                elements.pop(0)
                                continue
                        else:
                            print(colored(f"{relation}", "red"))

                        cls.append(zss, new, observer)
                        last = new
                        elements = []


@final
class Bi(Line):
    __slots__ = "fake", "config"

    def __init__(
        self,
        pre: Optional["Self"],
        start: FenXing,
        end: FenXing,
        elements: List[NewBar],
        fake: bool,
        config: ChanConfig,
    ):
        super().__init__(start, end, 0, elements, "Bi")
        self.pre = pre
        self.fake = fake
        self.config = config

        if pre is not None:
            assert pre.end is start, (pre.end, start)
            self.index = pre.index + 1

    def __str__(self):
        return f"Bi({self.index}, {self.direction}, {colored(self.start.dt, 'green')}, {self.start.speck}, {colored(self.end.dt, 'green')}, {self.end.speck}, {self.elements[-1]}, fake: {self.fake})"

    def __repr__(self):
        return f"Bi({self.index}, {self.direction}, {colored(self.start.dt, 'green')}, {self.start.speck}, {colored(self.end.dt, 'green')}, {self.end.speck}, {self.elements[-1]}, fake: {self.fake})"

    @property
    def length(self) -> int:
        size = 1
        elements = self.elements
        for i in range(1, len(elements)):
            left = elements[i - 1]
            right = elements[i]
            assert left.index + 1 == right.index, (
                left.index,
                right.index,
            )
            relation = double_relation(left, right)
            if self.config.BI_JUMP and relation.is_jump():
                size += 1
            size += 1
        if not self.config.BI_JUMP:
            assert size == len(elements)
        if self.config.BI_JUMP:
            return size
        return len(elements)

    @property
    def real_high(self) -> Optional[NewBar]:
        if not self.elements:
            return None
        if self.config.BI_EQUAL:
            high = [self.elements[0]]
            for bar in self.elements[1:]:
                if bar.high >= high[-1].high:
                    if bar.high > high[-1].high:
                        high.clear()
                    high.append(bar)
            if len(high) > 1:
                dp("", high)
            return high[-1]

        return max(self.elements, key=lambda x: x.high)

    @property
    def real_low(self) -> Optional[NewBar]:
        if not self.elements:
            return None
        if self.config.BI_EQUAL:
            low = [self.elements[0]]
            for bar in self.elements[1:]:
                if bar.low <= low[-1].low:
                    if bar.low < low[-1].low:
                        low.clear()
                    low.append(bar)
            if len(low) > 1:
                dp("", low)
            return low[-1]
        return min(self.elements, key=lambda x: x.low)

    @property
    def relation(self) -> bool:
        if self.config.BI_FENGXING:
            start = self.start
            relation = double_relation(start, self.end)
        else:
            start = self.start.mid
            relation = double_relation(start, self.end)

        if self.direction is Direction.Down:
            return relation.is_down()
        return relation.is_jump()

    def check(self) -> bool:
        if len(self.elements) >= self.config.BI_FENGXING:
            # assert self.start.mid is self.elements[0]
            # assert self.end.mid is self.elements[-1]
            if self.direction is Direction.Down and self.start.mid is self.real_high and self.end.mid is self.real_low:
                return True
            if self.direction is Direction.Up and self.start.mid is self.real_low and self.end.mid is self.real_high:
                return True
        return False

    @staticmethod
    def get_elements(bars: List[NewBar], start: FenXing, end: FenXing) -> List[NewBar]:
        return bars[bars.index(start.mid) : bars.index(end.mid) + 1]

    @classmethod
    def analyzer(
        cls,
        fx: FenXing,
        fxs: List[FenXing],
        bis: List["Bi"],
        bars: List[NewBar],
        _from: str,
        level: int,
        config: ChanConfig,
        observer: Observer,
    ):
        if not fxs:
            if fx.shape in (Shape.G, Shape.D):
                fxs.append(fx)
            return

        def pop():
            tmp_ = fxs.pop()
            if bis:
                bi_ = bis.pop()
                assert bi_.end is tmp_, "最后一笔终点错误"
                if _from == "analyzer":
                    bdp(f"Bi. pop: {bi_}")
                    observer and observer.notify(bi_, Command.Remove("Bi"))

        last = fxs[-1]

        if last.mid.dt > fx.mid.dt:
            raise ChanException("时序错误")

        if (last.shape is Shape.G and fx.shape is Shape.D) or (last.shape is Shape.D and fx.shape is Shape.G):
            bi = Bi(None, last, fx, Bi.get_elements(bars, last, fx), False, config)
            if bi.length > 4:
                eq = config.BI_EQUAL
                config.BI_EQUAL = False  # 起始点检测时不考虑相同起始点情况，避免递归

                if last.shape is Shape.G and fx.shape is Shape.D:
                    start = bi.real_high
                else:
                    start = bi.real_low
                if start is not last.mid:
                    # print("不是真底")
                    new = FenXing.get_fenxing(bars, start)
                    if last.shape is Shape.G and fx.shape is Shape.D:
                        assert new.shape is Shape.G, new
                    else:
                        assert new.shape is Shape.D, new
                    Bi.analyzer(new, fxs, bis, bars, _from, level + 1, config, observer)  # 处理新顶
                    Bi.analyzer(fx, fxs, bis, bars, _from, level + 1, config, observer)  # 再处理当前底
                    config.BI_EQUAL = eq
                    return
                config.BI_EQUAL = eq

                if last.shape is Shape.G and fx.shape is Shape.D:
                    end = bi.real_low
                else:
                    end = bi.real_high

                if bi.relation and fx.mid is end:
                    FenXing.append(fxs, fx)
                    Line.append(bis, bi)
                    if _from == "analyzer":
                        bdp(f"Bi. append: {bi}")
                        observer and observer.notify(bi, Command.Append("Bi"))
                else:
                    # 2024 05 21 修正
                    if len(fxs) < 3:
                        return
                    _bars = bars[bars.index(last.mid) :]
                    _fx, _bi = Bi.analysis_one(_bars, level, config, observer)
                    if _bi is None:
                        return

                    start = fxs[-3]
                    end = _bi.start
                    nb = Bi(None, start, end, Bi.get_elements(bars, start, end), False, config)
                    if not nb.check():
                        return
                    # print(_bi)
                    pop()
                    Bi.analyzer(_bi.start, fxs, bis, bars, _from, level + 1, config, observer)

            else:
                ...
                # GD or DG
                if (last.shape is Shape.G and fx.shape is Shape.D and fx.right.high > last.speck) or (last.shape is Shape.D and fx.shape is Shape.G and fx.right.low < last.speck):
                    pop()

        elif (last.shape is Shape.G and (fx.shape is Shape.S or fx.shape is Shape.G)) or (last.shape is Shape.D and (fx.shape is Shape.X or fx.shape is Shape.D)):
            if last.shape is Shape.G:
                func = min

                def okey(o):
                    return o.low
            else:
                func = max

                def okey(o):
                    return o.high

            if fx.shape is Shape.S:
                speck = fx.right.high
            elif fx.shape is Shape.X:
                speck = fx.right.low
            else:
                speck = fx.speck

            if (last.shape is Shape.G and last.speck < speck) or (last.shape is Shape.D and last.speck > speck):
                pop()
                if fxs:
                    last = fxs[-1]
                    if fx.shape is Shape.S or fx.shape is Shape.G:
                        assert last.shape is Shape.D, last.shape
                    else:
                        assert last.shape is Shape.G, last.shape

                    new = FenXing.get_fenxing(
                        bars,
                        func(
                            Bi.get_elements(bars, last, fx),
                            key=okey,
                        ),
                    )

                    if fx.shape is Shape.S or fx.shape is Shape.G:
                        assert new.shape is Shape.D
                    else:
                        assert new.shape is Shape.G

                    if (last.shape is Shape.G and last.speck > new.mid.low) or (last.shape is Shape.D and last.speck < new.mid.high):
                        pop()
                        Bi.analyzer(new, fxs, bis, bars, _from, level + 1, config, observer)  # 处理新底
                        # print("GS修正") or print("DX修正")
                        if fx.shape in (Shape.S, Shape.X):
                            return
                        Bi.analyzer(fx, fxs, bis, bars, _from, level + 1, config, observer)  # 再处理当前顶
                        # print("GG修正") or print("DD修正")
                        return

                if fx.shape in (Shape.S, Shape.X):
                    return

                if not fxs:
                    FenXing.append(fxs, fx)
                    return

                bi = Bi(None, last, fx, Bi.get_elements(bars, last, fx), False, config)

                FenXing.append(fxs, fx)
                Line.append(bis, bi)
                if _from == "analyzer":
                    bdp(f"Bi. append: {bi}")
                    observer and observer.notify(bi, Command.Append("Bi"))

        elif (last.shape is Shape.G and fx.shape is Shape.X) or (last.shape is Shape.D and fx.shape is Shape.S):
            ...

        else:
            raise ChanException(last.shape, fx.shape)

    @staticmethod
    def analysis_one(bars: List[NewBar], level: int, config: ChanConfig, observer: Observer) -> tuple[Optional[FenXing], Optional["Bi"]]:
        try:
            bars[2]
        except IndexError:
            return None, None
        bis = []
        fxs = []
        fx = None
        size = len(bars)
        for i in range(1, size - 2):
            left, mid, right = bars[i - 1], bars[i], bars[i + 1]
            fx = FenXing(left, mid, right)
            Bi.analyzer(fx, fxs, bis, bars, "tmp", level + 1, config, observer)
            if bis:
                return fx, bis[0]
        if bis:
            return fx, bis[0]
        return None, None


@final
class Duan(Line):
    __slots__ = "features", "observer"

    def __init__(
        self,
        start: FenXing,
        end: FenXing,
        elements: List[Line],
        stamp: str = "Duan",
        *,
        observer: Optional[Observer] = None,
    ):
        super().__init__(start, end, 0, elements, stamp)
        self.observer: Optional[Observer] = observer
        self.features: list[Optional[FeatureSequence]] = [None, None, None]

    def __str__(self):
        return f"{self.stamp}({self.index}, {self.direction}, has pre: {self.pre is not None}, done: {self.done}, {self.state}, {self.start}, {self.end}, size={len(self.elements)})"

    def __repr__(self):
        return str(self)

    @property
    def gap(self) -> Optional[Pillar]:
        if not self.mid:
            return
        if double_relation(self.left, self.mid).is_jump():
            hl = [self.left.start.speck, self.mid.start.speck]
            return Pillar(max(*hl), min(*hl))

    @property
    def done(self) -> bool:
        return self.right is not None

    @property
    def lmr(self) -> tuple[bool, bool, bool]:
        return self.left is not None, self.mid is not None, self.right is not None

    @property
    def state(self) -> Optional[str]:
        if self.pre is not None and self.pre.gap:
            return "老阳" if self.direction is Direction.Up else "老阴"
        return "小阳" if self.direction is Direction.Up else "少阴"

    @property
    def left(self) -> FeatureSequence:
        return self.features[0]

    @left.setter
    def left(self, feature: FeatureSequence):
        self.__feature_setter(0, feature)

    @property
    def mid(self) -> FeatureSequence:
        return self.features[1]

    @mid.setter
    def mid(self, feature: FeatureSequence):
        self.__feature_setter(1, feature)

    @property
    def right(self) -> FeatureSequence:
        return self.features[2]

    @right.setter
    def right(self, feature: FeatureSequence):
        self.__feature_setter(2, feature)

    def __feature_setter(self, offset: int, feature: Optional[FeatureSequence]):
        if feature and feature.direction == self.direction:
            raise ChanException("特征序列方向不匹配")
        features: List = self.features
        observer: Optional[Observer] = self.observer
        old = features[offset]
        features[offset] = feature

        old and observer and observer.notify(old, Command.Remove(old.stamp))
        feature and observer and observer.notify(feature, Command.Append(feature.stamp))

    def clear_features(self):
        for feature in self.features:
            if feature is not None:
                self.observer and self.observer.notify(feature, Command.Remove(feature.stamp))

    def update(self, lines: List[Line]) -> bool:
        assert self.done is True, (self, self.features)
        i = self.elements[-1].index
        while 1:
            try:
                lines.index(self.elements[-1])
                break
            except ValueError:
                self.pop_element(self.elements[-1])

        for line in lines:
            if self.elements[-1].is_next(line):
                self.add_element(line)
                if line.index == i:
                    break
        # assert size == len(self.elements)
        return self.done

    def get_next_elements(self) -> List[Line]:
        assert self.elements[0].start is self.start, (self.elements[0].start, self.start)
        elements = []
        for line in self.elements:
            if elements:
                elements.append(line)
            if line.start is self.end:
                elements.append(line)
        return elements

    def set_elements(self, elements: List[Line]):
        assert elements[0].start is self.start, (elements[0].start, self.start)
        self.clear_features()
        self.elements.clear()
        last = None
        for i in range(1, len(elements) - 1):
            pre = elements[i - 1]
            last = elements[i]
            assert last.is_previous(pre) is True
            self.add_element(pre)
            if self.done:
                print("set_elements done", i, len(elements))
        if last:
            self.add_element(last)

    def get_elements(self) -> List[Line]:
        assert self.elements[0].start is self.start, (self.elements[0].start, self.start)
        elements = []
        for obj in self.elements:
            elements.append(obj)
            if obj.end is self.end:
                break
        return elements

    def pop_element(self, line: Line) -> Line:
        duan = self
        drop = Line.pop(duan.elements, line)
        duan.left, duan.mid, duan.right = FeatureSequence.analyzer(duan.elements, duan.direction)
        return drop

    def add_element(self, line: Line):
        duan = self
        Line.append(duan.elements, line)
        if self.done:
            ...

        duan.left, duan.mid, duan.right = FeatureSequence.analyzer(duan.elements, duan.direction)
        if duan.mid is not None:
            duan.end = duan.mid.start

        if duan.direction == line.direction:
            if duan.mid is not None:
                if duan.direction == Direction.Up:
                    if duan.high < line.high:
                        duan.end = line.end
                    else:
                        duan.end = duan.mid.start
                else:
                    if duan.low > line.low:
                        duan.end = line.end
                    else:
                        duan.end = duan.mid.start
            else:
                duan.end = line.end

    @classmethod
    def new(cls, line: Line | List[Line], observer: Optional[Observer]) -> "Duan":
        if type(line) is list:
            lines = line[:]
            return Duan(line[0].start, line[2].end, lines, "Duan" if lines[0].stamp == "Bi" else lines[0].stamp + "Duan", observer=observer)
        return Duan(line.start, line.end, [line], "Duan" if line.stamp == "Bi" else line.stamp + "Duan", observer=observer)

    @classmethod
    def analyzer(cls, lines: List[Line], xds: List["Duan"], observer: Observer):
        if not lines:
            return
        try:
            lines[5]
        except IndexError:
            return

        if not xds:
            for i in range(1, len(lines) - 1):
                left, mid, right = lines[i - 1], lines[i], lines[i + 1]
                if double_relation(left, right).is_jump():
                    continue
                duan = Duan.new([left, mid, right], observer)
                Line.append(xds, duan)
                observer and observer.notify(duan, Command.Append(duan.stamp))
                return Duan.analyzer(lines, xds, observer)

        else:
            last = xds[-1]
            while 1:
                try:
                    index = lines.index(last.elements[-1]) + 1
                    break
                except ValueError:
                    line = last.pop_element(last.elements[-1])
                    ddp("Duan.analyzer 弹出", line)

                    if not last.elements:
                        print("Duan.analyzer 无法找到", last)
                        if Line.pop(xds, last) is not None:
                            observer and observer.notify(last, Command.Remove(last.stamp))
                            last.clear_features()
                        return Duan.analyzer(lines, xds, observer)
            duan = last

            # for line in lines[index:]:
            for i in range(index, len(lines)):
                line = lines[i]
                last = duan.pre
                if last and last.elements[-1] not in lines:
                    if not last.update(lines):
                        # print("异常", last)
                        Line.pop(xds, duan)
                        observer and observer.notify(duan, Command.Remove(duan.stamp))
                        duan.clear_features()
                        return Duan.analyzer(lines, xds, observer)

                if last and last.gap and len(duan.elements) == 3:
                    if (last.direction is Direction.Up and line.high > last.high) or (last.direction is Direction.Down and line.low < last.low):
                        Line.pop(xds, duan)
                        observer and observer.notify(duan, Command.Remove(duan.stamp))
                        duan.clear_features()
                        last.add_element(line)
                        observer and observer.notify(last, Command.Modify(last.stamp))
                        # print("修正")
                        duan = last
                        continue

                duan.add_element(line)
                observer and observer.notify(duan, Command.Modify(duan.stamp))
                if duan.done:
                    elements = duan.get_next_elements()
                    duan.clear_features()
                    for feature in duan.features:
                        if feature is not None:
                            observer and observer.notify(feature, Command.Append(feature.stamp))

                    if duan.direction is Direction.Up:
                        fx = "顶分型"
                    else:
                        fx = "底分型"

                    ddp("    ", f"{fx}终结, 缺口: {duan.gap}")
                    size = len(elements)
                    if size >= 3:
                        duan = Duan.new(elements[:3], observer)
                        Line.append(xds, duan)
                        observer and observer.notify(duan, Command.Append(duan.stamp))
                        for feature in duan.features:
                            if feature is not None:
                                observer and observer.notify(feature, Command.Append(feature.stamp))

                        return Duan.analyzer(lines, xds, observer)

                    duan = Duan.new(elements, observer)
                    Line.append(xds, duan)
                    observer and observer.notify(duan, Command.Append(duan.stamp))
                    for feature in duan.features:
                        if feature is not None:
                            observer and observer.notify(feature, Command.Append(feature.stamp))


class BaseAnalyzer(Observer):
    __slots__ = "symbol", "freq", "ws", "last_raw_bar", "raws", "news", "fxs", "bis", "xds", "bzss", "dzss", "cache", "config"

    def __init__(self, symbol: str, freq: SupportsInt, ws: WebSocket = None):
        self.symbol: str = symbol
        self.freq: int = int(freq)
        self.ws = ws
        self.last_raw_bar: Optional[RawBar] = None
        self.raws: list[RawBar] = []
        self.news: list[NewBar] = []
        self.fxs: list[FenXing] = []
        self.bis: list[Bi] = []
        self.xds: list[Duan] = []
        self.bzss: list[ZhongShu] = []
        self.dzss: list[ZhongShu] = []
        self.cache = dict()
        self.config = ChanConfig()

        self.zs = []

    def notify(self, obj: Any, cmd: Command):
        if not self.config.ANALYZER_SHON_TV:
            return
        message = dict()
        message["stamp"] = obj.stamp if hasattr(obj, "stamp") else obj.__class__.__name__

        if type(obj) is NewBar:
            message["type"] = "realtime"
            message["timestamp"] = str(obj.dt)
            message["open"] = obj.open
            message["high"] = obj.high
            message["low"] = obj.low
            message["close"] = obj.close
            message["volume"] = obj.volume

        if type(obj) is Bi:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(hash(obj))
            message["name"] = "trend_line"
            message["points"] = [{"time": int(obj.start.dt.timestamp()), "price": obj.start.speck}, {"time": int(obj.end.dt.timestamp()), "price": obj.end.speck}]
            message["options"] = {"shape": "trend_line", "text": obj.stamp}
            message["properties"] = {"linecolor": "#CC62FF", "linewidth": 2, "title": f"{obj.stamp}-{obj.index}"}

            if cmd.cmd == Command.APPEND:
                ...
            elif cmd.cmd == Command.MODIFY:
                ...
            elif cmd.cmd == Command.REMOVE:
                ...

        if type(obj) is Duan:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(id(obj))
            message["name"] = "trend_line"
            message["points"] = [{"time": int(obj.start.dt.timestamp()), "price": obj.start.speck}, {"time": int(obj.end.dt.timestamp()), "price": obj.end.speck}]
            message["options"] = {"shape": "trend_line", "text": obj.stamp}
            message["properties"] = {"linecolor": "#F1C40F" if obj.stamp == "Duan" else "#00C40F", "linewidth": 3, "title": f"{obj.stamp}-{obj.index}", "text": obj.stamp}

        if type(obj) is Interval:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(id(obj))
            message["name"] = "rectangle"
            message["points"] = [{"time": int(obj.elements[0].dt.timestamp()), "price": obj.high}, {"time": int(obj.elements[-1].dt.timestamp()), "price": obj.low}]
            message["options"] = {"shape": "rectangle", "text": "nb"}
            message["properties"] = {"color": "#00C40F", "backgroundColor": "#00C40F"}

        if type(obj) is ZhongShu:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(hash(obj))
            message["name"] = "rectangle"
            if cmd.cmd == Command.APPEND or cmd.cmd == Command.MODIFY:
                points = (
                    [
                        {"time": int(obj.start.dt.timestamp()), "price": obj.zg},
                        {
                            "time": int(obj.elements[-1].end.mid.dt.timestamp()),
                            "price": obj.zd,
                        },
                    ]
                    if len(obj.elements) <= 3
                    else [
                        {"time": int(obj.start.dt.timestamp()), "price": obj.zg},
                        {
                            "time": int(obj.elements[-1].start.mid.dt.timestamp()),
                            "price": obj.zd,
                        },
                    ]
                )

            elif cmd.cmd == Command.REMOVE:
                points = []
            else:
                points = []

            message["points"] = points
            message["options"] = {"shape": "rectangle", "text": obj.stamp}
            message["properties"] = {
                "color": "#993333" if obj.direction is Direction.Down else "#99CC99",  # 上下上 为 红色，反之为 绿色
                "linewidth": 1 if obj.elements[0].stamp == "Bi" else 2,
                "title": f"{obj.stamp}-{obj.index}",
                "text": obj.stamp,
            }

        if type(obj) is FeatureSequence:
            message["type"] = "shape"
            message["cmd"] = str(cmd)
            message["id"] = str(id(obj))
            message["name"] = "trend_line"
            start = obj.start.dt
            end = obj.end.dt
            if start > end:
                start, end = end, start
            message["points"] = [{"time": int(start.timestamp()), "price": obj.start.speck}, {"time": int(end.timestamp()), "price": obj.end.speck}]
            message["options"] = {"shape": "trend_line", "text": obj.stamp}
            message["properties"] = {
                "linecolor": "#FFFFFF" if obj.direction.reversal() is Direction.Down else "#fbc02d",
                "linewidth": 4,
                "linestyle": 1,
                # "showLabel": True,
                "title": obj.stamp,
            }

        if cmd.cmd == Command.APPEND:
            ...
        elif cmd.cmd == Command.MODIFY:
            ...
        elif cmd.cmd == Command.REMOVE:
            ...

        # future = asyncio.ensure_future(self.ws.send_text('{"type": "websocket.send", "text": data}'))
        # self.loop.run_until_complete(future)
        if self.ws is not None and self.config.ANALYZER_SHON_TV:
            asyncio.set_event_loop(self.loop)
            asyncio.ensure_future(self.ws.send_text(json.dumps(message)))
        # print(message)
        return

    @final
    def step(
        self,
        dt: datetime.datetime | int | str,
        open_: float | str,
        high: float | str,
        low: float | str,
        close: float | str,
        volume: float | str,
    ):
        if type(dt) is datetime.datetime:
            ...
        elif isinstance(dt, str):
            dt: datetime.datetime = datetime.datetime.fromtimestamp(int(dt))
        elif isinstance(dt, int):
            dt: datetime.datetime = datetime.datetime.fromtimestamp(dt)
        else:
            raise ChanException("类型不支持", type(dt))
        open_ = float(open_)
        high = float(high)
        low = float(low)
        close = float(close)
        volume = float(volume)

        index = 0

        last = RawBar(
            dt=dt,
            o=open_,
            h=high,
            low=low,
            c=close,
            v=volume,
            i=index,
        )
        self.push(last)

    @final
    def push(self, bar: RawBar):
        if self.last_raw_bar is not None:
            bar.index = self.last_raw_bar.index + 1
        self.last_raw_bar = bar
        # self.raws.append(bar)
        pre = None
        if self.news:
            try:
                pre = self.news[-2]
            except IndexError:
                pass
            nb = NewBar.merger(pre, self.news[-1], bar)
            if nb is not None:
                if self.config.ANALYZER_CALC_MACD:
                    MACD.calc(self.news[-1], nb)
                self.news.append(nb)
            else:
                if self.config.ANALYZER_CALC_MACD and pre:
                    MACD.calc(pre, self.news[-1])
        else:
            nb = bar.to_new_bar(None)
            nb.macd = MACD(fast_ema=nb.close, slow_ema=nb.close, dif=0.0, dea=0.0, fastperiod=self.config.MACD_FAST_PERIOD, slowperiod=self.config.MACD_SLOW_PERIOD, signalperiod=self.config.MACD_SIGNAL_PERIOD)
            self.news.append(nb)

        # Interval.analyzer(self.news, self.zs, self)

        self.notify(self.news[-1], Command.Append("NewBar"))

        # left, mid, right = None, None, None
        try:
            left, mid, right = self.news[-3:]
        except ValueError:
            return

        (shape, _, _) = triple_relation(left, mid, right)
        mid.shape = shape
        fx = FenXing(left, mid, right)
        if self.ws is not None and self.config.ANALYZER_SHON_TV:
            time.sleep(self.TIME)

        if not self.config.ANALYZER_CALC_BI:
            return

        Bi.analyzer(fx, self.fxs, self.bis, self.news, "analyzer", 0, self.config, self)
        # return
        if self.bis and self.cache.get("bi", None) is self.bis[-1]:
            return
        if self.bis:
            self.cache["bi"] = self.bis[-1]
        if self.config.ANALYZER_CALC_BI_ZS:
            ZhongShu.analyzer(self.bis, self.bzss, self)

        if self.config.ANALYZER_CALC_XD:
            try:
                Duan.analyzer(self.bis, self.xds, self)
            except Exception as e:
                traceback.print_exc()
                xds = self.xds[-3:]
                news = self.news[xds[0].start.left.index :]
                RawBar.bars_save_as_dat(f"./templates/{self.symbol}_duan_exception-{self.freq}-{int(news[0].dt.timestamp())}-{int(news[-1].dt.timestamp())}.nb", news)
                raise e
            if self.xds and self.cache.get("xd", None) is self.xds[-1]:
                return
            if self.xds:
                self.cache["xd"] = self.xds[-1]
            if self.config.ANALYZER_CALC_XD_ZS:
                ZhongShu.analyzer(self.xds, self.dzss, self)

    @classmethod
    def read_from_dat_file(cls, path: str) -> "BaseAnalyzer":
        name = Path(path).name.split(".")[0]
        symbol, freq, s, e = name.split("-")
        size = struct.calcsize(">6d")
        obj = cls(symbol, int(freq))
        with open(path, "rb") as f:
            # if not f.seek(size * 1000000):
            #    return obj
            start = time.time()
            half = start
            length = 0
            with mmap.mmap(f.fileno(), size * 6000000, access=mmap.ACCESS_READ) as mm:
                # for buffer in chunked_file_reader(f):

                while buffer := mm.read(size * 10000):
                    try:
                        for i in range(len(buffer) // size):
                            bar = RawBar.from_be_bytes(buffer[i * size : i * size + size])
                            obj.push(bar)
                            length += 1
                            if length % 100000 == 0:
                                print(length, f" read in {time.time() - start}s")
                                print(f"news:{len(obj.news)}")
                                print(f"bis: {len(obj.bis)}")
                                print(f"xds: {len(obj.xds)}")
                                print(f"bzss:{len(obj.bzss)}")
                                print(f"dzss:{len(obj.dzss)}")
                                print(f"{time.time() - half}s")
                                print(f"{time.time() - start}s")
                                half = time.time()
                    except KeyboardInterrupt:
                        print(traceback.format_exc())
                        break
            print(f"\nnews:{len(obj.news)} read in {time.time() - start}s")
            print(f"bis: {len(obj.bis)}")
            print(f"xds: {len(obj.xds)}")
            print(f"bzss:{len(obj.bzss)}")
            print(f"dzss:{len(obj.dzss)}")
            print(dir(obj.config))

        return obj


class Generator(BaseAnalyzer):
    def __init__(self, symbol: str, freq: int, ws: WebSocket):
        super().__init__(symbol, freq, ws)

    def save_nb_file(self):
        RawBar.bars_save_as_dat(f"./templates/{self.symbol}-{self.freq}-{int(self.news[0].dt.timestamp())}-{int(self.news[-1].dt.timestamp())}.nb", self.news)

    def load_nb_file(self, path: str):
        with open(path, "rb") as f:
            buffer = f.read()
            size = struct.calcsize(">6d")
            for i in range(len(buffer) // size):
                bar = RawBar.from_be_bytes(buffer[i * size : i * size + size])
                self.push(bar)

    def push_new_bar(self, nb: NewBar):
        self.news.append(nb)
        # Interval.analyzer(self.news, self.zs, self)
        self.notify(self.news[-1], Command.Append("NewBar"))
        # return
        # left, mid, right = None, None, None
        try:
            left, mid, right = self.news[-3:]
        except ValueError:
            return

        (shape, _, _) = triple_relation(left, mid, right)
        mid.shape = shape
        fx = FenXing(left, mid, right)
        if self.ws is not None and self.config.ANALYZER_SHON_TV:
            time.sleep(self.TIME)

        if not self.config.ANALYZER_CALC_BI:
            return

        Bi.analyzer(fx, self.fxs, self.bis, self.news, "analyzer", 0, self.config, self)
        # return
        if self.bis and self.cache.get("bi", None) is self.bis[-1]:
            return
        if self.bis:
            self.cache["bi"] = self.bis[-1]
        if self.config.ANALYZER_CALC_BI_ZS:
            ZhongShu.analyzer(self.bis, self.bzss, self)

        if self.config.ANALYZER_CALC_XD:
            try:
                Duan.analyzer(self.bis, self.xds, self)
            except Exception as e:
                traceback.print_exc()
                xds = self.xds[-3:]
                news = self.news[xds[0].start.left.index :]
                RawBar.bars_save_as_dat(f"./templates/{self.symbol}_duan_exception_byGenerator-{self.freq}-{int(news[0].dt.timestamp())}-{int(news[-1].dt.timestamp())}.nb", news)
                raise e
            if self.xds and self.cache.get("xd", None) is self.xds[-1]:
                return
            if self.xds:
                self.cache["xd"] = self.xds[-1]
            if self.config.ANALYZER_CALC_XD_ZS:
                ZhongShu.analyzer(self.xds, self.dzss, self)

    @classmethod
    def generator(cls, points: List[int | dict], seconds=300):
        news = []

        def append(array, new):
            if not array:
                array.append(new)
                return
            if double_relation(array[-1], new) is Direction.Left:
                array[-1] = new
            elif double_relation(array[-1], new) is Direction.Right:
                print(array[-1], new)
            else:
                print(double_relation(array[-1], new))
                array.append(new)

        dt = datetime.datetime(2008, 8, 8)
        offset = datetime.timedelta(seconds=seconds)
        index = 0
        for i in range(1, len(points)):
            if type(points[i]) is dict:
                o = int(points[i - 1]["price"])
                c = int(points[i]["price"])
            else:
                o = int(points[i - 1])
                c = int(points[i])
            direction = Direction.Up if o < c else Direction.Down
            h = max(o, c)
            l = min(o, c)
            d = h - l
            m = d / 5
            if direction == Direction.Up:
                nb = NewBar(dt, l + m, l, direction, 8, index, None)
                append(news, nb)
                dt = dt + offset
                for dd in [Direction.NextUp] * 4:
                    nb = NewBar.generate(nb, dd, seconds, True)
                    append(news, nb)
                    dt = dt + offset
            else:
                nb = NewBar(dt, h, l + m * 4, direction, 8, index, None)
                append(news, nb)
                dt = dt + offset
                for dd in [Direction.NextDown] * 4:
                    nb = NewBar.generate(nb, dd, seconds, True)
                    append(news, nb)
                    dt = dt + offset

        lines = Lines(news)
        lines.reset_line_index()
        return news


class Bitstamp(BaseAnalyzer):
    def __init__(self, symbol: str, freq: SupportsInt, ws: WebSocket = None):
        super().__init__(symbol, freq, ws)

    def init(self, size):
        self.left_date_timestamp: int = int(datetime.datetime.now().timestamp() * 1000)
        left = int(self.left_date_timestamp / 1000) - self.freq * size
        if left < 0:
            raise ChanException
        _next = left
        while 1:
            data = self.ohlc(self.symbol, self.freq, _next, _next := _next + self.freq * 1000)
            if not data.get("data"):
                print(data)
                raise ChanException
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
                    # self.save_file()
                    raise e

            # start = int(data["data"]["ohlc"][0]["timestamp"])
            end = int(data["data"]["ohlc"][-1]["timestamp"])

            _next = end
            if len(data["data"]["ohlc"]) < 100:
                break

    @staticmethod
    def ohlc(pair: str, step: int, start: int, end: int, length: int = 1000) -> Dict:
        proxies = {
            "http": "http://127.0.0.1:11809",
            "https": "http://127.0.0.1:11809",
        }
        s = requests.Session()

        s.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "content-type": "application/json",
        }
        url = f"https://www.bitstamp.net/api/v2/ohlc/{pair}/?step={step}&limit={length}&start={start}&end={end}"
        resp = s.get(url, timeout=5, proxies=proxies)
        js = resp.json()
        # print(json)
        return js


def main_bitstamp(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = Freq.m5, ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Bitstamp(symbol, freq=int(freq), ws=ws)
        bitstamp.init(int(limit))

    return func


def gen(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = Freq.m5, ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Generator(symbol, freq=int(freq), ws=ws)
        bitstamp.config.BI_JUMP = False
        dt = datetime.datetime(2008, 8, 8)
        nb = NewBar(dt, 10000, 9900, Direction.Up, 8.8, 0)
        bitstamp.push_new_bar(nb)
        for direction in Direction.generator(int(limit), [Direction.Up, Direction.JumpUp, Direction.NextUp, Direction.Down, Direction.JumpDown, Direction.NextDown]):
            nb = NewBar.generate(nb, direction, int(freq))
            # print(direction, nb)
            bitstamp.push_new_bar(nb)

        for duan in bitstamp.xds:
            if duan.gap:
                bitstamp.save_nb_file()
                break

    return func


def gen2(symbol: str = "btcusd", limit: int = 500, freq: SupportsInt = Freq.m5, ws: Optional[WebSocket] = None):
    def func():
        bitstamp = Generator(symbol, freq=int(freq), ws=ws)
        bitstamp.config.BI_JUMP = False
        a = [
            {"price": 11070.490547079706, "time": 1218098700},
            {"price": 11477.076230434637, "time": 1218100200},
            {"price": 10311.530604817166, "time": 1218102000},
            {"price": 10728.958573061562, "time": 1218103200},
            {"price": 9856.15463945964, "time": 1218104700},
            {"price": 10132.632904140995, "time": 1218105900},
            {"price": 9969.998630799022, "time": 1218107700},
            {"price": 10224.792325701446, "time": 1218109200},
            {"price": 9682.168101337797, "time": 1218111900},
            {"price": 9891.448028901257, "time": 1218114000},
        ]
        for nb in Generator.generator(a, int(freq)):
            bitstamp.push_new_bar(nb)

        for duan in bitstamp.xds:
            if duan.gap:
                bitstamp.save_nb_file()
                break

    return func


app = FastAPI()
# priority_queue = asyncio.PriorityQueue()
# queue = Observer.queue  # asyncio.Queue()
app.mount(
    "/charting_library",
    StaticFiles(directory="charting_library"),
    name="charting_library",
)
templates = Jinja2Templates(directory="templates")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            message = json.loads(data)
            if message["type"] == "ready":
                # exchange = message["exchange"]
                symbol = message["symbol"]
                freq = message["freq"]
                limit = message["limit"]
                if Observer.thread is not None:
                    tmp = Observer.thread
                    Observer.thread = None

                    tmp.join(1)
                    time.sleep(1)

                if message["generator"] == "True":
                    Observer.thread = Thread(target=gen(symbol=symbol, freq=freq, limit=limit, ws=websocket))  # 使用线程来运行main函数
                else:
                    Observer.thread = Thread(target=main_bitstamp(symbol=symbol, freq=freq, limit=limit, ws=websocket))  # 使用线程来运行main函数
                Observer.thread.start()
    except WebSocketDisconnect:
        ...


@app.get("/")
async def main_page(
    request: Request,
    nol: str = "network",
    exchange: str = "bitstamp",
    symbol: str = "btcusd",
    step: int = 300,
    limit: int = 500,
    generator: bool = False,
):
    resolutions = {
        60: "1",
        180: "3",
        300: "5",
        900: "15",
        1800: "30",
        3600: "1H",
        7200: "2H",
        14400: "4H",
        21600: "6H",
        43200: "12H",
        86400: "1D",
        259200: "3D",
    }
    if resolutions.get(step) is None:
        return resolutions

    # Observer.CAN = True
    return templates.TemplateResponse("index.html", {"request": request, "exchange": exchange, "symbol": symbol, "interval": resolutions.get(step), "limit": str(limit), "step": str(step), "generator": generator})


if __name__ == "__main__":
    BaseAnalyzer.read_from_dat_file("btcusd-60-0-0.dat")
