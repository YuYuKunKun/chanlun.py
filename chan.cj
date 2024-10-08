/*
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
 */

package chanlun

import std.binary.BigEndianOrder
import std.convert.Parsable
import std.collection.{HashSet, ArrayList, enumerate, HashMap, any, contains}
import std.fs.{Path, File, FSException}
import std.math.{abs, MathExtension, sqrt}
import std.random.Random
import std.time.{DateTime, MonoTime}
import encoding.json.{JsonObject, JsonArray, JsonBool, JsonFloat, JsonString, JsonValue, JsonInt}
import net.http.*

public func dp(s: String): Unit {
    if (1 == 0) {
        println(s)
    }
}

public func str<T>(obj: T): String where T <: ToString {
    obj.toString()
}

public func sum(array: Array<Float64>): Float64 {
    var result = 0.0f64
    for (i in array) {
        result += i
    }
    return result
}

extend DateTime {
    public static func ts2int(ts!: String = "2008-08-08 08:08:08", format!: String = "yyyy-MM-dd HH:mm:ss"): Int64 {
        let dt = DateTime.parse(ts, format)
        dt.toUnixTimeStamp().toSeconds()
    }

    public static func int2ts(ts: Int64): DateTime {
        DateTime.UnixEpoch.addSeconds(ts)
    }

    public static func dt2int(dt: DateTime): Int64 {
        dt.toUnixTimeStamp().toSeconds()
    }
}

type News = ArrayList<NewBar>

type Raws = ArrayList<RawBar>

type Lines = ArrayList<Line>

type Bis = ArrayList<Bi>

type Duans = ArrayList<Duan>

extend<T> ArrayList<T> where T <: ToString {
    public func toLines(): Lines {
        let lines = Lines()
        for (bi in this) {
            lines.append((bi as Line).getOrThrow())
        }
        return lines
    }

    public func index(obj: NewBar): Int64 {
        if (this.isEmpty()) {
            throw ChanException("列表为空")
        }

        for ((i, o) in enumerate(this.iterator())) {
            if (refEq(obj, (o as NewBar).getOrThrow())) {
                return i
            }
        }
        throw ChanException("元素不在列表中")
    }

    public func index(obj: RawBar): Int64 {
        if (this.isEmpty()) {
            throw ChanException("列表为空")
        }

        for ((i, o) in enumerate(this.iterator())) {
            if (refEq(obj, (o as RawBar).getOrThrow())) {
                return i
            }
        }
        throw ChanException("元素不在列表中")
    }

    public func index2(obj: Bi): Int64 {
        if (this.isEmpty()) {
            throw ChanException("列表为空")
        }

        for ((i, o) in enumerate(this.iterator())) {
            if (refEq(obj, (o as Bi).getOrThrow())) {
                return i
            }
        }
        throw ChanException("元素不在列表中")
    }

    public func index2(obj: Duan): Int64 {
        if (this.isEmpty()) {
            throw ChanException("列表为空")
        }

        for ((i, o) in enumerate(this.iterator())) {
            if (refEq(obj, (o as Duan).getOrThrow())) {
                return i
            }
        }
        throw ChanException("元素不在列表中")
    }
}

public func colored(text: String, color!: ?String = Option<String>.None, on_color!: ?String = Option<String>.None,
    attrs!: ?String = Option<String>.None): String {
    let COLORS = HashMap<String, Byte>(
        [('black', 30), ('grey', 30), ('red', 31), ('green', 32), ('yellow', 33), ('blue', 34), ('magenta', 35),
        ('cyan', 36), ('light_grey', 37), ('dark_grey', 90), ('light_red', 91), ('light_green', 92),
        ('light_yellow', 93), ('light_blue', 94), ('light_magenta', 95), ('light_cyan', 96), ('white', 97)])
    let HIGHLIGHTS = HashMap<String, Byte>(
        [('on_black', 40), ('on_grey', 40), ('on_red', 41), ('on_green', 42), ('on_yellow', 43), ('on_blue', 44),
        ('on_magenta', 45), ('on_cyan', 46), ('on_light_grey', 47), ('on_dark_grey', 100), ('on_light_red', 101),
        ('on_light_green', 102), ('on_light_yellow', 103), ('on_light_blue', 104), ('on_light_magenta', 105),
        ('on_light_cyan', 106), ('on_white', 107)])
    let ATTRIBUTES = HashMap<String, Byte>(
        [('bold', 1), ('dark', 2), ('underline', 4), ('blink', 5), ('reverse', 7), ('concealed', 8)])

    let RESET = "\u{1B}[0m"
    var result = text

    if (let Some(code) <- color) {
        result = "\u{1B}[${COLORS[code]}m${result}"
    }
    if (let Some(code) <- on_color) {
        result = "\u{1B}[${HIGHLIGHTS[code]}m${result}"
    }
    if (let Some(code) <- attrs) {
        result = "\u{1B}[${ATTRIBUTES[code]}m${result}"
    }

    result += RESET
    return result
}

class ChanException <: Exception {
    private var messages: String = ""
    init() {
        super()
    }
    init(messages: String) {
        super(messages)
        this.messages = messages
    }
    public func getMessage(): String {
        return messages
    }
    public override func toString(): String {
        return "ChanException: ${messages}"
    }
}

public enum Shape <: ToString & Equatable<Shape> {
    D | G | S | X | T | Unknow

    public func toString(): String {
        match (this) {
            case D => "底分型"
            case G => "顶分型"
            case S => "上升分型"
            case X => "下降分型"
            case T => "喇叭口型"
            case Unknow => "未知分型"
        }
    }

    public operator override func ==(other: Shape): Bool {
        if (this.toString() == other.toString()) {
            return true
        }
        return false
    }

    public operator override func !=(other: Shape): Bool {
        return !(this == other)
    }

    public operator func !(): Shape {
        match (this) {
            case D => G
            case G => D
            case S => X
            case X => S
            case T => T
            case Unknow => Unknow
        }
    }

    public static func fromString(shapeString: String): Shape {
        match (shapeString) {
            case "底分型" => Shape.D
            case "顶分型" => Shape.G
            case "上升分型" => Shape.S
            case "下降分型" => Shape.X
            case "喇叭口型" => Shape.T
            case _ => Shape.Unknow
        }
    }
}

public enum Direction <: ToString & Equatable<Direction> {
    Up | Down | JumpUp | JumpDown | Left | Right | Unknow

    public func toString(): String {
        match (this) {
            case Up => "Up"
            case Down => "Down"
            case JumpDown => "JumpDown"
            case JumpUp => "JumpUp"
            case Left => "Left"
            case Right => "Right"
            case Unknow => "Unknow"
        }
    }

    public operator override func ==(other: Direction): Bool {
        if (this.toString() == other.toString()) {
            return true
        }
        return false
    }

    public operator override func !=(other: Direction): Bool {
        return !(this == other)
    }

    public operator func !(): Direction {
        match (this) {
            case Up => Down
            case Down => Up
            case JumpDown => JumpUp
            case JumpUp => JumpDown
            case Left => Right
            case Right => Left
            case Unknow => Unknow
        }
    }

    public static func fromString(dirString: String): Direction {
        match (dirString) {
            case "Up" => Direction.Up
            case "Down" => Direction.Down
            case "JumpDown" => Direction.JumpDown
            case "JumpUp" => Direction.JumpUp
            case "Left" => Direction.Left
            case "Right" => Direction.Right
            case _ => Direction.Unknow
        }
    }
}

public enum BSPoint <: ToString & Equatable<BSPoint> & Hashable {
    BUY(String, String, DateTime, Float64, Bool, Int64, Int64) | SELL(String, String, DateTime, Float64, Bool, Int64,
        Int64)
    // info: String, type: String, dt:DateTime, price: Float, valid: Bool, creation_offset:Int64 首次创建偏移, fix_offset:Int64 失效偏移

    public static func calc_zs_third_bsp(zs: ZhongShu, third: Line, observer: Observer): ?BSPoint {
        let relation = double_relation(zs, third)
        let tp: String = third.stamp
        if (relation == Direction.JumpDown) {
            return BSPoint.SELL("Third", "${tp}", third.end.mid.dt, third.end.mid.speck, true,
                observer.news[observer.news.size - 1].index - third.end.mid.index, 0)
        } else if (relation == Direction.JumpUp) {
            return BSPoint.BUY("Third", "${tp}", third.end.mid.dt, third.end.mid.speck, true,
                observer.news[observer.news.size - 1].index - third.end.mid.index, 0)
        }
        return None
    }

    public func toString(): String {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => "BUY(${info}, ${tp}, ${dt}, ${price}, ${valid}, ${creation_offset})"
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => "SELL(${info}, ${tp}, ${dt}, ${price}, ${valid}, ${creation_offset})"
        }
    }

    public func isBuy(): Bool {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => true
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => false
        }
    }

    public func isSell(): Bool {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => false
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => true
        }
    }

    public func setValid(valid: Bool): BSPoint {
        match (this) {
            case BUY(info, tp, dt, price, _, creation_offset, fix_offset) => BUY(info, tp, dt, price, valid,
                creation_offset, fix_offset)
            case SELL(info, tp, dt, price, _, creation_offset, fix_offset) => SELL(info, tp, dt, price, valid,
                creation_offset, fix_offset)
        }
    }

    public func getValid(): Bool {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => valid
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => valid
        }
    }

    public func getPrice(): Float64 {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => price
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => price
        }
    }

    public func setPrice(price: Float64): BSPoint {
        match (this) {
            case BUY(info, tp, dt, _, valid, creation_offset, fix_offset) => BUY(info, tp, dt, price, valid,
                creation_offset, fix_offset)
            case SELL(info, tp, dt, _, valid, creation_offset, fix_offset) => SELL(info, tp, dt, price, valid,
                creation_offset, fix_offset)
        }
    }

    public func getDt(): DateTime {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => dt
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => dt
        }
    }

    public func setDt(dt: DateTime): BSPoint {
        match (this) {
            case BUY(info, tp, _, price, valid, creation_offset, fix_offset) => BUY(info, tp, dt, price, valid,
                creation_offset, fix_offset)
            case SELL(info, tp, _, price, valid, creation_offset, fix_offset) => SELL(info, tp, dt, price, valid,
                creation_offset, fix_offset)
        }
    }

    public func getType(): String {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => tp
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => tp
        }
    }

    public func setType(tp: String): BSPoint {
        match (this) {
            case BUY(info, _, dt, price, valid, creation_offset, fix_offset) => BUY(info, tp, dt, price, valid,
                creation_offset, fix_offset)
            case SELL(info, _, dt, price, valid, creation_offset, fix_offset) => SELL(info, tp, dt, price, valid,
                creation_offset, fix_offset)
        }
    }

    public func getInfo(): String {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => info
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => info
        }
    }

    public func setInfo(info: String): BSPoint {
        match (this) {
            case BUY(_, tp, dt, price, valid, creation_offset, fix_offset) => BUY(info, tp, dt, price, valid,
                creation_offset, fix_offset)
            case SELL(_, tp, dt, price, valid, creation_offset, fix_offset) => SELL(info, tp, dt, price, valid,
                creation_offset, fix_offset)
        }
    }

    public func getOffset(): Int64 {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => creation_offset
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => creation_offset
        }
    }

    public func setOffset(fix_offset: Int64): BSPoint {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, _) => BUY(info, tp, dt, price, valid, creation_offset,
                fix_offset)
            case SELL(info, tp, dt, price, valid, creation_offset, _) => SELL(info, tp, dt, price, valid,
                creation_offset, fix_offset)
        }
    }

    public operator override func ==(other: BSPoint): Bool {
        if (this.toString() == other.toString()) {
            return true
        }
        return false
    }

    public operator override func !=(other: BSPoint): Bool {
        return !(this == other)
    }

    public func hashCode(): Int64 {
        match (this) {
            case BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => "BUY(${info}, ${tp}, ${dt}, ${price})".
                hashCode()
            case SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => "SELL(${info}, ${tp}, ${dt}, ${price})".
                hashCode()
        }
    }
}

public enum CMD <: ToString {
    APPEND(String) | REMOVE(String) | MODIFY(String)

    public func toString(): String {
        match (this) {
            case APPEND(s) => "APPEND(${s})"
            case REMOVE(s) => "REMOVE(${s})"
            case MODIFY(s) => "MODIFY(${s})"
        }
    }
}

public enum Freq <: ToString {
    YEAR(Int64) | MONTH(Int64) | WEEK(Int64) | DAY(Int64) | HOUR(Int64) | MINUTE(Int64) | SECOND(Int64) | TICKET(
        DateTime)

    public func toString(): String {
        match (this) {
            case YEAR(s) => "YEAR(${s})"
            case MONTH(s) => "MONTH(${s})"
            case WEEK(s) => "WEEK(${s})"
            case DAY(s) => "DAY(${s})"
            case HOUR(s) => "HOUR(${s})"
            case MINUTE(s) => "MINUTE(${s})"
            case SECOND(s) => "SECOND(${s})"
            case TICKET(s) => "TICKET(${s})"
        }
    }

    public func toDuration(): Duration {
        match (this) {
            case YEAR(s) => Duration.day * s * 360
            case MONTH(s) => Duration.day * s * 30
            case WEEK(s) => Duration.day * s * 7
            case DAY(s) => Duration.day * s
            case HOUR(s) => Duration.hour * s
            case MINUTE(s) => Duration.minute * s
            case SECOND(s) => Duration.second * s
            case TICKET(dt) => dt.toUnixTimeStamp()
        }
    }
}

public enum Indicators <: ToString {
    MACD(UInt32, UInt32, UInt32, String, Indicators, Indicators)
    | // fast: UInt32, slow: UInt32, signl: UInt32, from: String = {open, high, low, close, ...}, Oscillator MA Type,  Signal Line MA Type
        MA(UInt32, String)
    | // len: UInt, from: String = {open, high, low, close, ...} # N日移动平均线=N日收盘价之和 / N
        SMA(UInt32, String, UInt32)
    | // len: UInt32, from: String = {open, high, low, close, ...}, offset: UInt32=0
        EMA(UInt32, String, UInt32)
    | //

        BOLL(UInt32, String, UInt32, Indicators, UInt32) // len, from, dif, base ma type, offset

    public func toString(): String {
        ""
    }

    public static func calc_MA(ma: Indicators, array: Array<Float64>): Float64 {
        match (ma) {
            case Indicators.MA(n, _) =>
                if (array.size != (n as Int64).getOrThrow()) {
                    throw ChanException()
                }
                return sum(array) / (n as Float64).getOrThrow()
            case _ => throw ChanException()
        }
    }

    public static func calc_EMA(ema: Indicators, today: Float64, yesterday_ema: Float64): Float64 {
        match (ema) {
            case Indicators.EMA(n, _, offset) => (2.0 * today + yesterday_ema * ((n - 1) as Float64).getOrThrow()) /
                ((n + 1) as Float64).getOrThrow()
            case _ => throw ChanException()
        }
    }

    public static func calc_MACD(macd: Indicators, today: Float64, yesterday_ema_slow: Float64,
        yesterday_ema_fast: Float64, yesterday_dif: Float64): (Float64, Float64, Float64) {
        // https://baike.baidu.com/item/MACD%E6%8C%87%E6%A0%87/6271283
        match (macd) {
            case Indicators.MACD(slow, fast, signal, s, ma, signal_ma) =>
                let ma_slow = match (ma) {
                    case Indicators.EMA(_, _, offset) => calc_EMA(Indicators.EMA(slow, s, offset), today,
                        yesterday_ema_slow)
                    case _ => throw ChanException()
                }

                let ma_fast = match (ma) {
                    case Indicators.EMA(_, _, offset) => calc_EMA(Indicators.EMA(fast, s, offset), today,
                        yesterday_ema_fast)
                    case _ => throw ChanException()
                }

                let dif = ma_fast - ma_slow

                let dea = match (signal_ma) {
                    case Indicators.EMA(_, _, offset) => calc_EMA(Indicators.EMA(signal, s, offset), dif, yesterday_dif)
                    case _ => throw ChanException()
                }

                let macd = (dif - dea) * 2.0
                return (dif, dea, macd)

            case _ => throw ChanException()
        }
    }

    public static func calc_BOLL(boll: Indicators, array: Array<Float64>) {
        match (boll) {
            case Indicators.BOLL(n, _, K, ma, offset) =>
                if (array.size != (n as Int64).getOrThrow()) {
                    throw ChanException()
                }

                let average = match (ma) {
                    case Indicators.MA(_, s) => calc_MA(Indicators.MA(n, s), array)
                    case _ => throw ChanException()
                }
                var a = 0.0f64
                for (i in array) {
                    a += (i - average) ** 2
                }

                let sd = sqrt(a / (array.size as Float64).getOrThrow())
                return (average + (K as Float64).getOrThrow() * sd, average, average - (K as Float64).getOrThrow() * sd)

            case _ => throw ChanException()
        }
    }
}

public interface Continuously {
    mut prop index: Int64
}

public interface Interval {
    prop high: Float64
    prop low: Float64
}

public func double_relation<T>(left: T, right: T): Direction where T <: Interval {
    var relation: Direction = Direction.Unknow
    if (left.low <= right.low && left.high >= right.high) {
        relation = Direction.Left // "左包右" # 顺序
    } else if (left.low >= right.low && left.high <= right.high) {
        relation = Direction.Right // "右包左" # 逆序
    } else if (left.low < right.low && left.high < right.high) {
        relation = Direction.Up // "上涨"
        if (left.high < right.low) {
            relation = Direction.JumpUp // "跳涨"
        }
    } else if (left.low > right.low && left.high > right.high) {
        relation = Direction.Down // "下跌"
        if (left.low > right.high) {
            relation = Direction.JumpDown // "跳跌"
        }
    } else {
        throw ChanException()
    }

    return relation
}

public func triple_relation<T>(left: T, mid: T, right: T, use_right!: Bool = false): (Shape, (Direction, Direction)) where T <: Interval {
    let lm: Direction = double_relation(left, mid)
    let mr: Direction = double_relation(mid, right)
    var shape: Shape = match ((lm, mr)) {
        case (_, Direction.Left) => throw ChanException()

        case (Direction.Up, Direction.Up) => Shape.S
        case (Direction.Up, Direction.JumpUp) => Shape.S
        case (Direction.JumpUp, Direction.Up) => Shape.S
        case (Direction.JumpUp, Direction.JumpUp) => Shape.S
        case (Direction.Up, Direction.Right) => if (use_right) {
            Shape.S
        } else {
            Shape.Unknow // None
        }
        case (Direction.JumpUp, Direction.Right) => if (use_right) {
            Shape.S
        } else {
            Shape.Unknow // None
        }

        case (Direction.Down, Direction.Down) => Shape.X
        case (Direction.Down, Direction.JumpDown) => Shape.X
        case (Direction.JumpDown, Direction.Down) => Shape.X
        case (Direction.JumpDown, Direction.JumpDown) => Shape.X
        case (Direction.Down, Direction.Right) => if (use_right) {
            Shape.X
        } else {
            Shape.Unknow // None
        }
        case (Direction.JumpDown, Direction.Right) => if (use_right) {
            Shape.X
        } else {
            Shape.Unknow // None
        }

        case (Direction.Up, Direction.Down) => Shape.G
        case (Direction.Up, Direction.JumpDown) => Shape.G
        case (Direction.JumpUp, Direction.Down) => Shape.G
        case (Direction.JumpUp, Direction.JumpDown) => Shape.G

        case (Direction.Down, Direction.Up) => Shape.D
        case (Direction.Down, Direction.JumpUp) => Shape.D
        case (Direction.JumpDown, Direction.Up) => Shape.D
        case (Direction.JumpDown, Direction.JumpUp) => Shape.D

        case (Direction.Right, _) => if (use_right) {
            match (mr) {
                case Direction.Up => Shape.D
                case Direction.Down => Shape.G
                case Direction.JumpUp => Shape.D
                case Direction.JumpDown => Shape.G
                case Direction.Left => throw ChanException()
                case Direction.Right => Shape.T
                case Direction.Unknow => Shape.Unknow // None
            }
        } else {
            Shape.Unknow // None
        }

        case _ => Shape.Unknow // None
    }
    return (shape, (lm, mr))
}

public interface HashableEquatable<T> <: Hashable & Equatable<T> {}

public interface Observer {
    prop symbol: String
    prop freq: UInt32
    prop raws: Raws
    prop news: News
    prop fxs: ArrayList<FenXing>

    prop bis: Bis // level=0
    prop duans: Duans // level=0
    prop bi_zss: ArrayList<ZhongShu> // level=0
    prop duan_zss: ArrayList<ZhongShu> // level=0

    prop duan_bis: Bis // level=1
    prop duan_duans: Duans // level=2
    prop duan_bi_zss: ArrayList<ZhongShu> // level=1
    prop duan_duan_zss: ArrayList<ZhongShu> // level=2

    func update(obj: ToString, cmd: CMD): Unit
}

public interface Bar <: ToString & Interval {
    mut prop index: Int64
    prop open: Float64
    prop close: Float64
    prop high: Float64
    prop low: Float64
    prop volume: Float64
    prop direction: Direction
}

public interface BarExtensions {
    prop macd: Float64
}

public class RawBar <: Bar & HashableEquatable<RawBar> & BigEndianOrder<RawBar> & BarExtensions {
    public let dt: DateTime
    private var _index: Int64 = 0
    private var _open: Float64 = 0.0
    private var _close: Float64 = 0.0
    private var _high: Float64 = 0.0
    private var _low: Float64 = 0.0
    private var _volume: Float64 = 0.0
    private var _direction: Direction = Direction.Unknow

    private var dts: HashSet<DateTime> = HashSet<DateTime>()
    private var last_volume: Float64

    private let _extensions: HashMap<String, Float64> = HashMap<String, Float64>()

    RawBar(dt: DateTime, open: Float64, high: Float64, low: Float64, close: Float64, volume: Float64, index: Int64) {
        this.dt = dt
        this._open = open
        this._high = high
        this._low = low
        this._close = close
        this._volume = volume
        this._index = index
        this.dts.put(dt)
        this.last_volume = volume
    }

    public mut prop index: Int64 {
        get() {
            this._index
        }
        set(index) {
            this._index = index
        }
    }

    public prop open: Float64 {
        get() {
            this._open
        }
    }

    public prop close: Float64 {
        get() {
            this._close
        }
    }

    public prop high: Float64 {
        get() {
            this._high
        }
    }

    public prop low: Float64 {
        get() {
            this._low
        }
    }

    public prop volume: Float64 {
        get() {
            this._volume
        }
    }

    public prop direction: Direction {
        get() {
            if (this.open > this.close) {
                Direction.Down
            } else {
                Direction.Up
            }
        }
    }

    public prop macd: Float64 {
        get() {
            if (let Some(v) <- this._extensions.get("macd")) {
                return v
            }
            return 0.0f64
        }
    }

    public func hashCode(): Int64 {
        "RawBar(${this.dt}, ${this.open}, ${this.high}, ${this.low}, ${this.close}, ${this.volume}, ${this.index}, ${this.dts}, ${this.last_volume}, ${this.direction})".
            hashCode()
    }

    public operator override func ==(other: RawBar): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: RawBar): Bool {
        return !(this == other)
    }

    public func toString(): String {
        return "RawBar(${this.dt}, ${this.open}, ${this.high}, ${this.low}, ${this.close}, ${this.volume}, ${this.index})"
    }

    public func toNewBar(pre: ?NewBar): NewBar {
        return NewBar(
            dt: this.dt,
            high: this.high,
            low: this.low,
            elements: [this],
            pre: pre
        )
    }

    public static func readBigEndian(buffer: Array<Byte>): RawBar {
        if (buffer.size < 48) {
            throw IllegalArgumentException("RawBar.readBigEndian ")
        }
        let tmp = Float64.readBigEndian(buffer[0..8])
        let dt: DateTime = DateTime.int2ts(Int64(tmp))
        let open: Float64 = Float64.readBigEndian(buffer[8..16])
        let high: Float64 = Float64.readBigEndian(buffer[16..24])
        let low: Float64 = Float64.readBigEndian(buffer[24..32])
        let close: Float64 = Float64.readBigEndian(buffer[32..40])
        let volume: Float64 = Float64.readBigEndian(buffer[40..48])
        return RawBar(dt, open, high, low, close, volume, 0)
    }

    public func writeBigEndian(buffer: Array<Byte>): Int64 {
        DateTime.dt2int(this.dt).writeBigEndian(buffer[0..8])
        this.open.writeBigEndian(buffer[8..16])
        this.high.writeBigEndian(buffer[16..24])
        this.low.writeBigEndian(buffer[24..32])
        this.close.writeBigEndian(buffer[32..40])
        this.volume.writeBigEndian(buffer[40..48])
        return 48
    }
}

public class NewBar <: Bar & HashableEquatable<NewBar> & BarExtensions {
    public let dt: DateTime
    private var _index: Int64 = 0
    //private var _open: Float64 = 0.0
    //private var _close: Float64 = 0.0
    private var _high: Float64 = 0.0
    private var _low: Float64 = 0.0
    //private var _volume: Float64 = 0.0
    private var _direction: Direction = Direction.Unknow

    private var _shape: Shape = Shape.Unknow
    public var elements: Raws

    public var jump: Bool = false
    public var speck: Float64 = 0.0
    public var relation: Direction = Direction.Up // 与前一个NewBar 实际关系

    private let _extensions: HashMap<String, Float64> = HashMap<String, Float64>()

    NewBar(dt!: DateTime, high!: Float64, low!: Float64, elements!: Array<RawBar>, pre!: ?NewBar) {
        this.dt = dt
        //this._open = open
        this._high = high
        this._low = low
        //this._close = close
        //this._volume = volume
        //this._index = index
        this._direction = Direction.Up

        this.elements = Raws(elements)
        //this.doInit(pre)

        if (let Some(last) <- pre) {
            this._index = last.index + 1
            this.relation = double_relation(last, this)
            match (this.relation) {
                case Direction.JumpUp =>
                    this.jump = true
                    this._direction = Direction.Up
                    this.speck = this.high
                case Direction.JumpDown =>
                    this.jump = true
                    this._direction = Direction.Down
                    this.speck = this.low
                case Direction.Up =>
                    this.jump = false
                    this._direction = Direction.Up
                    this.speck = this.high

                case Direction.Down =>
                    this.jump = false
                    this._direction = Direction.Down
                    this.speck = this.low
                case Direction.Left | Direction.Right => throw ChanException("与前一个存在包含关系")
                case _ =>
                    this.jump = false
                    this._direction = Direction.Up
                    this.speck = this.high
            }
        }
    }

    public func hashCode(): Int64 {
        "NewBar(${this.dt}, ${this.open}, ${this.high}, ${this.low}, ${this.close}, ${this.volume}, ${this.index}, ${this.shape}, ${this.jump}, ${this.speck}, ${this.relation}, ${this.elements})".
            hashCode()
    }

    public operator override func ==(other: NewBar): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: NewBar): Bool {
        return !(this == other)
    }

    public func toString(): String {
        return "NewBar(${this.dt}, ${this.open}, ${this.high}, ${this.low}, ${this.close}, ${this.volume}, ${this.index})"
    }

    public mut prop index: Int64 {
        get() {
            this._index
        }
        set(index) {
            this._index = index
        }
    }

    public prop open: Float64 {
        get() {
            match (this.direction) {
                case Direction.Up => this.low
                case Direction.Down => this.high
                case _ => throw ChanException()
            }
        }
    }

    public prop close: Float64 {
        get() {
            match (this.direction) {
                case Direction.Up => this.high
                case Direction.Down => this.low
                case _ => throw ChanException()
            }
        }
    }

    public prop high: Float64 {
        get() {
            this._high
        }
    }

    public prop low: Float64 {
        get() {
            this._low
        }
    }

    public prop volume: Float64 {
        get() {
            var sum = 0.0f64
            for (bar in this.elements) {
                sum += bar.volume
            }
            sum
        }
    }

    public prop direction: Direction {
        get() {
            this._direction
        }
    }

    public mut prop shape: Shape {
        get() {
            this._shape
        }
        set(shape) {
            this._shape = shape
            match (shape) {
                case Shape.G => this.speck = this.high
                case Shape.D => this.speck = this.low
                case Shape.S => this.speck = this.high
                case Shape.X => this.speck = this.low
                case _ => throw ChanException()
            }
        }
    }

    public prop macd: Float64 {
        get() {
            if (let Some(v) <- this._extensions.get("macd")) {
                return v
            }
            return 0.0f64
        }
    }

    public func isPoint(dt: DateTime, price: Float64): Bool {
        if (this.dt == dt && this.speck == price) {
            return true
        }
        return false
    }

    public func merge(next_raw_bar: RawBar): ?NewBar {
        let last: RawBar = this.elements[this.elements.size - 1]
        if (next_raw_bar.index - 1 != last.index) {
            throw ChanException("数据不连续: ${next_raw_bar}, ${last}")
        }

        let relation = double_relation(this, next_raw_bar)

        match (relation) {
            case Direction.Left | Direction.Right =>
                match (this.relation) {
                    case Direction.Up | Direction.JumpUp =>
                        this._high = max(this._high, next_raw_bar.high)
                        this._low = max(this._low, next_raw_bar.low)

                    case Direction.Down | Direction.JumpDown =>
                        this._high = min(this._high, next_raw_bar.high)
                        this._low = min(this._low, next_raw_bar.low)

                    case _ => throw ChanException("NewBar merge direction: ${this.relation}")
                }
                this.elements.append(next_raw_bar)
                return None
            case Direction.Down | Direction.Up | Direction.JumpDown | Direction.JumpUp => return next_raw_bar.toNewBar(
                Some(this))
            case _ => throw ChanException("NewBar.merge unknow direction: ${relation}")
        }
    }
}

public interface FenXingInterface<T> <: Interval where T <: Interval {
    mut prop left: T
    mut prop mid: T
    mut prop right: T
    prop speck: Float64
    prop shape: Shape
}

public class FenXing <: ToString & FenXingInterface<NewBar> & HashableEquatable<FenXing> {
    private var _index: Int64 = 0
    private var _left: ?NewBar = None
    private var _mid: ?NewBar = None
    private var _right: ?NewBar = None
    private var _high: Float64 = 0.0
    private var _low: Float64 = 0.0

    FenXing(left: NewBar, mid: NewBar, right: NewBar) {
        this._low = min(left.low, mid.low)
        this._high = max(left.high, mid.high)
        this._left = Some(left)
        this._mid = Some(mid)
        this._right = Some(right)
    }

    public mut prop index: Int64 {
        get() {
            this._index
        }
        set(index) {
            this._index = index
        }
    }
    public prop high: Float64 {
        get() {
            this._high
        }
    }

    public prop low: Float64 {
        get() {
            this._low
        }
    }

    public prop volume: Float64 {
        get() {
            throw ChanException()
        }
    }

    public prop direction: Direction {
        get() {
            throw ChanException()
        }
    }

    public prop shape: Shape {
        get() {
            this.mid.shape
        }
    }

    public prop speck: Float64 {
        get() {
            match (this.shape) {
                case Shape.G | Shape.D => this.mid.speck
                case Shape.X | Shape.S => this.right.speck
                case _ => throw ChanException()
            }
        }
    }

    public mut prop left: NewBar {
        get() {
            this._left.getOrThrow()
        }
        set(obj) {
            this._left = Some(obj)
        }
    }

    public mut prop mid: NewBar {
        get() {
            this._mid.getOrThrow()
        }
        set(obj) {
            this._mid = Some(obj)
        }
    }

    public mut prop right: NewBar {
        get() {
            this._right.getOrThrow()
        }
        set(obj) {
            this._right = Some(obj)
        }
    }

    public prop dt: DateTime {
        get() {
            this.mid.dt
        }
    }

    public func hashCode(): Int64 {
        //"FenXing(${this.left.hashCode()}, ${this.mid.hashCode()}, ${this.right.hashCode()})".hashCode()
        this.mid.hashCode()
    }

    public operator override func ==(other: FenXing): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: FenXing): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "FenXing(${this.dt}, ${this.shape}, ${this.speck})"
    }

    public static func append(fxs: ArrayList<FenXing>, fx: FenXing): Unit {
        if (!fxs.isEmpty()) {
            if (fxs[fxs.size - 1].shape == fx.shape) {
                throw ChanException("分型相同无法添加")
            }
            //fx.index = fxs[fxs.size - 1].index + 1
        }
        fxs.append(fx)
    }

    public static func pop(fxs: ArrayList<FenXing>, fx: FenXing): FenXing {
        if (!fxs.isEmpty()) {
            if (refEq(fxs[fxs.size - 1], fx)) {
                throw ChanException("分型不相同无法删除")
            }
            let fx = fxs[fxs.size - 1]
            fxs.remove(fxs.size - 1)
            return fx
        } else {
            throw ChanException("")
        }
    }
}

public interface LineExtensions {
    mut prop level: Byte
    prop elements: Lines
}

public interface Line <: ToString & HashableEquatable<Line> & Interval & Continuously & BarExtensions {
    prop start: FenXing
    mut prop end: FenXing

    prop bars: News

    prop stamp: String {
        get() {
            "Line"
        }
    }
    prop direction: Direction {
        get() {
            match ((this.start.shape, this.end.shape)) {
                case (Shape.G, Shape.D) => Direction.Down

                case (Shape.D, Shape.G) => Direction.Up

                case _ => throw ChanException("Line.direction: ${this.start.shape}, ${this.end.shape}")
            }
        }
    }

    prop high: Float64 {
        get() {
            if (this.direction == Direction.Down) {
                this.start.speck
            } else {
                this.end.speck
            }
        }
    }

    prop low: Float64 {
        get() {
            if (this.direction == Direction.Up) {
                this.start.speck
            } else {
                this.end.speck
            }
        }
    }

    prop volume: Float64 {
        get() {
            var sum = 0.0f64
            for (bar in this.getBars()) {
                sum += bar.volume
            }
            sum
        }
    }

    prop macd: Float64 {
        get() {
            var sum = 0.0f64
            for (bar in this.getBars()) {
                sum += bar.macd
            }
            sum
        }
    }

    func toString(): String {
        "${this.stamp}(${this.index}, ${this.start}, ${this.end})"
    }

    func hashCode(): Int64 {
        "Line(${this.start.hashCode()}, ${this.end.hashCode()})".hashCode()
    }

    operator override func ==(other: Line): Bool {
        return refEq(this.start, other.start) && refEq(this.end, other.end)
    }

    operator override func !=(other: Line): Bool {
        return !(this == other)
    }

    func getBars(): Array<NewBar> {
        return this.bars[this.start.mid.index..this.end.mid.index + 1].toArray()
    }
}

public class Bi <: HashableEquatable<Bi> & Line {
    public static let BI_JUMP: Bool = true
    public static let BI_LENGTH: Int64 = 5
    public static var BI_EQUAL: Bool = true
    public static let BI_FENGXING: Bool = false

    private var _index: Int64 = 0

    private let _start: FenXing
    private var _end: FenXing
    public var pre: ?Bi

    public var elements: News
    public var fake: Bool = false
    private let _id: Int64

    Bi(pre!: ?Bi, start!: FenXing, end!: FenXing, elements!: Array<NewBar>, fake!: Bool = false) {
        this._id = TradingView.getID()
        this.pre = pre
        this._start = start
        this._end = end
        this.elements = News(elements)
        this.fake = fake

        if (let Some(last) <- pre) {
            if (last.end != start) {
                throw ChanException()
            }
            this.index = pre.getOrThrow().index + 1
        }
    }

    public mut prop index: Int64 {
        get() {
            this._index
        }
        set(index) {
            this._index = index
        }
    }

    public prop stamp: String {
        get() {
            "Bi"
        }
    }

    public prop bars: News {
        get() {
            this.elements
        }
    }

    public prop start: FenXing {
        get() {
            this._start
        }
    }

    public mut prop end: FenXing {
        get() {
            this._end
        }
        set(fx) {
            //let old = this._end
            this._end = fx
            match (this.direction) {
                case Direction.Up => if (fx.shape != Shape.G || fx.shape != Shape.S) {
                    throw ChanException("Bi.end: UP.shape not in (G, S)")
                }

                case Direction.Down => if (this.low > fx.low) {
                    if (fx.shape != Shape.D || fx.shape != Shape.X) {
                        throw ChanException("Bi.end: UP.shape not in (D, X)")
                    }
                }

                case _ => throw ChanException("Bi.direction: 无效")
            }
        }
    }

    public prop volume: Float64 {
        get() {
            var sum = 0.0f64
            for (bar in this.elements) {
                sum += bar.volume
            }
            sum
        }
    }

    public prop macd: Float64 {
        get() {
            var result = 0.0f64
            for (bar in elements) {
                result += bar.macd
            }
            return result
        }
    }

    public func getBars(): Array<NewBar> {
        this.elements.toArray()
    }

    public prop real_low: NewBar {
        get() {
            if (this.elements.isEmpty()) {
                throw ChanException("Bi.real_low: 列表为空")
            }
            if (Bi.BI_EQUAL) {
                var lows: News = ArrayList([this.elements[0]])
                let length = this.elements.size
                for (bar in this.elements[1..length]) {
                    if (bar.low <= lows[lows.size - 1].low) {
                        if (bar.low == min(bar.low, lows[lows.size - 1].low)) { // bar.low < lows[lows.size - 1].low
                            lows.clear()
                        }
                        lows.append(bar)
                    }
                }
                if (lows.size > 1) {
                }
                return lows[lows.size - 1]
            } else {
                var low: NewBar = this.elements[0]
                for (bar in this.elements[1..this.elements.size]) {
                    if (bar.low < low.low) {
                        low = bar
                    }
                }
                return low
            }
        }
    }

    public prop real_high: NewBar {
        get() {
            if (this.elements.isEmpty()) {
                throw ChanException("Bi.real_high: 列表为空")
            }
            if (Bi.BI_EQUAL) {
                var highs: News = ArrayList([this.elements[0]])
                for (bar in this.elements[1..this.elements.size]) {
                    if (bar.high >= highs[highs.size - 1].high) {
                        if (bar.high == max(bar.high, highs[highs.size - 1].high)) { // bar.high > highs[highs.size - 1].high
                            highs.clear()
                        }
                        highs.append(bar)
                    }
                }
                if (highs.size > 1) {
                }
                return highs[highs.size - 1]
            } else {
                var high: NewBar = this.elements[0]
                let length = this.elements.size
                for (bar in this.elements[1..length]) {
                    if (bar.high > high.high) {
                        high = bar
                    }
                }
                return high
            }
        }
    }

    public prop length: Int64 {
        get() {
            return Bi.calc_length(this.elements)
        }
    }

    public prop relation: Bool {
        get() {
            var start: Interval = this.start.mid
            if (Bi.BI_FENGXING) {
                start = this.start
            }
            let end: Interval = this.end.mid
            let relation = double_relation(start, end)
            if (this.direction == Direction.Down) {
                if (relation == Direction.Down || relation == Direction.JumpDown) {
                    return true
                }
            } else {
                if (relation == Direction.Up || relation == Direction.JumpUp) {
                    return true
                }
            }

            return false
        }
    }

    public func hashCode(): Int64 {
        //"Bi(${this.pre}, ${this.start}, ${this.end}, ${this.elements})".hashCode()
        this._id
    }

    public operator override func ==(other: Bi): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: Bi): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "Bi(${this.direction}, ${this.start.dt}, ${this.start.speck}, ${this.end.dt}, ${this.end.speck}, index:${this.index})"
    }

    public func check(): Bool {
        if (this.elements.size >= 5) {
            if (this.start.mid != this.elements[0] || this.end.mid != this.elements[this.elements.size - 1]) {
                if (!this.fake) {
                    throw ChanException()
                }
            }
            if (this.direction == Direction.Down && this.start.mid == this.real_high && this.end.mid == this.real_low) {
                return true
            }
            if (this.direction == Direction.Up && this.start.mid == this.real_low && this.end.mid == this.real_high) {
                return true
            }
        }
        return false
    }

    public static func calc_length(elements: News): Int64 {
        var size: Int64 = 1
        for (i in 1..elements.size) {
            var left = elements[i - 1]
            var right = elements[i]
            //@Assert(left.index + 1 , right.index)
            if (left.index + 1 != right.index) {
                throw ChanException()
            }
            let relation = double_relation(left, right)
            if (Bi.BI_JUMP && (relation == Direction.JumpDown || relation == Direction.JumpUp)) {
                size += 1
            }
            size += 1
        }

        if ((!Bi.BI_JUMP) && (size != elements.size)) {
            throw ChanException()
        }

        if (Bi.BI_JUMP) {
            return size
        }
        return elements.size
    }

    public static func analyzer(fx: FenXing, fxs: ArrayList<FenXing>, bis: Bis, cklines: News, _from: String,
        level: UInt16, observer: Observer): Unit {
        if (fxs.isEmpty()) {
            if (fx.shape == Shape.G || fx.shape == Shape.D) {
                fxs.append(fx)
            }
            return
        }

        func __pop(bis: Bis, fx: FenXing, _from: String): ?Bi {
            let size = bis.size
            var bi: ?Bi = Option<Bi>.None
            if (size > 0) {
                if (bis[size - 1].end == fx) {
                    bi = bis[size - 1]
                    bis.remove(size - 1)
                    // bi.done = false
                    if (_from == "analyzer") {
                        //dp("Bi.analyzer, level: ${level}, pop ${bi}")
                        observer.update(bi.getOrThrow(), CMD.REMOVE("Bi"))
                    }
                } else {
                    throw ChanException("最后一笔终点错误")
                }
            }
            return bi
        }

        func __append(bis: Bis, bi: Bi, _from: String): Unit {
            let size = bis.size
            if (size > 0 && !refEq(bis[size - 1].end, bi.start)) {
                throw ChanException("笔连续性错误!!!")
            }
            var index: Int64 = 0
            var pre: ?Bi = None
            if (size > 0) {
                pre = Some(bis[size - 1])
                index = bis[size - 1].index + 1
            }
            bi.index = index
            bi.pre = pre
            // bi.done = true
            bis.append(bi)
            if (_from == "analyzer") {
                //dp("Bi.analyzer, level: ${level}, append ${bi}")
                observer.update(bi, CMD.APPEND("Bi"))
            }
        }

        var last: FenXing = fxs[fxs.size - 1]

        //let left: NewBar = fx.left
        let mid: NewBar = fx.mid
        let right: NewBar = fx.right

        if (last.mid.dt > fx.mid.dt) {
            throw ChanException("时序错误")
        }
        //dp("Bi.analyzer, level: ${level}, ${fx.mid}, ${_from}, ${last.shape}, ${fx.shape}")
        match ((last.shape, fx.shape)) {
            case (Shape.G, Shape.D) =>
                var bi = Bi(pre: None, start: last, end: fx,
                    elements: cklines[cklines.index(last.mid)..cklines.index(fx.mid) + 1].toArray())
                if (bi.length > 4) {
                    let eq = Bi.BI_EQUAL
                    Bi.BI_EQUAL = false
                    if (!refEq(bi.real_high, last.mid)) {
                        let top: NewBar = bi.real_high
                        let new: FenXing = FenXing(
                            cklines[cklines.index(top) - 1],
                            top,
                            cklines[cklines.index(top) + 1],
                        )
                        if (new.shape != Shape.G) {
                            throw ChanException()
                        }
                        Bi.analyzer(new, fxs, bis, cklines, _from, level + 1, observer)
                        Bi.analyzer(fx, fxs, bis, cklines, _from, level + 1, observer)
                        Bi.BI_EQUAL = eq
                        return
                    }
                    Bi.BI_EQUAL = eq
                    if (bi.relation && fx.mid == bi.real_low) {
                        FenXing.append(fxs, fx)
                        __append(bis, bi, _from)
                    } else {
                        // 2024 05 21 修正
                        let _cklines = cklines[cklines.index(last.mid)..]
                        let (_, _bi) = Bi.analysis_one(_cklines, observer)
                        if (let Some(b) <- _bi) {
                            if (fxs.size > 2) {
                                let start = fxs[fxs.size - 3]
                                let nb = Bi(pre: None, start: start, end: b.start,
                                    elements: cklines[cklines.index(start.mid)..cklines.index(b.start.mid) + 1].toArray(
                                ))
                                if (!nb.check()) {
                                    return
                                }

                                let tmp = fxs[fxs.size - 1]
                                fxs.remove(fxs.size - 1)
                                if (tmp != last) {
                                    throw ChanException()
                                }
                                __pop(bis, tmp, _from)
                                Bi.analyzer(b.start, fxs, bis, cklines, _from, level + 1, observer)
                            }
                        }
                    }
                } else {
                    // GD
                    if (right.high > last.speck) {
                        let tmp = fxs[fxs.size - 1]
                        fxs.remove(fxs.size - 1)
                        if (!refEq(tmp, last)) {
                            throw ChanException()
                        }

                        __pop(bis, tmp, _from)
                    }
                }
                return

            case (Shape.G, Shape.S) =>
                if (last.speck < right.high) {
                    let tmp = fxs[fxs.size - 1]
                    fxs.remove(fxs.size - 1)
                    __pop(bis, tmp, _from)

                    if (!fxs.isEmpty()) {
                        last = fxs[fxs.size - 1]
                        if (last.shape != Shape.D) {
                            throw ChanException()
                        }
                        var tmp: ?NewBar = None
                        for (bar in cklines[cklines.index(last.mid)..cklines.index(fx.mid) + 1]) {
                            if (tmp.isNone()) {
                                tmp = Some(bar)
                            } else {
                                if (let Some(obj) <- tmp) {
                                    if (obj.low > bar.low) {
                                        tmp = Some(bar)
                                    }
                                }
                            }
                        }
                        let bottom: NewBar = tmp.getOrThrow()
                        if (bottom.shape != Shape.D) {
                            throw ChanException()
                        }
                        if (last.speck > bottom.low) {
                            let tmp = fxs[fxs.size - 1]
                            fxs.remove(fxs.size - 1)
                            __pop(bis, tmp, _from)
                            let i = cklines.index(bottom)
                            let new: FenXing = FenXing(cklines[i - 1], bottom, cklines[i + 1])
                            if (new.shape != Shape.D) {
                                throw ChanException()
                            }
                            Bi.analyzer(new, fxs, bis, cklines, _from, level + 1, observer)
                        }
                    }
                }
                return

            case (Shape.G, Shape.G) =>
                if (last.speck < mid.high) {
                    let tmp = fxs[fxs.size - 1]
                    fxs.remove(fxs.size - 1)
                    __pop(bis, tmp, _from)

                    if (!fxs.isEmpty()) {
                        last = fxs[fxs.size - 1]
                        if (last.shape != Shape.D) {
                            throw ChanException()
                        }
                        var tmp: ?NewBar = None
                        for (bar in cklines[cklines.index(last.mid)..cklines.index(fx.mid) + 1]) {
                            if (tmp.isNone()) {
                                tmp = Some(bar)
                            } else {
                                if (let Some(obj) <- tmp) {
                                    if (obj.low > bar.low) {
                                        tmp = Some(bar)
                                    }
                                }
                            }
                        }
                        let bottom: NewBar = tmp.getOrThrow()
                        if (bottom.shape != Shape.D) {
                            throw ChanException()
                        }
                        if (last.speck > bottom.low) {
                            let tmp = fxs[fxs.size - 1]
                            fxs.remove(fxs.size - 1)
                            __pop(bis, tmp, _from)
                            let i = cklines.index(bottom)
                            let new: FenXing = FenXing(cklines[i - 1], bottom, cklines[i + 1])
                            if (new.shape != Shape.D) {
                                throw ChanException()
                            }
                            Bi.analyzer(new, fxs, bis, cklines, _from, level + 1, observer)
                            Bi.analyzer(fx, fxs, bis, cklines, _from, level + 1, observer)
                            return
                        }
                    }
                    if (fxs.isEmpty()) {
                        FenXing.append(fxs, fx)
                        return
                    }
                    let start: FenXing = fxs[fxs.size - 1]
                    var bi = Bi(pre: None, start: start, end: fx,
                        elements: cklines[cklines.index(start.mid)..cklines.index(fx.mid) + 1].toArray())
                    FenXing.append(fxs, fx)
                    __append(bis, bi, _from)
                }
                return

            case (Shape.G, Shape.X) => return

            case (Shape.D, Shape.G) =>
                var bi = Bi(pre: None, start: last, end: fx,
                    elements: cklines[cklines.index(last.mid)..cklines.index(fx.mid) + 1].toArray())
                if (bi.length > 4) {
                    let eq = Bi.BI_EQUAL
                    Bi.BI_EQUAL = false
                    if (!refEq(bi.real_low, last.mid)) {
                        let bottom: NewBar = bi.real_low
                        let new: FenXing = FenXing(
                            cklines[cklines.index(bottom) - 1],
                            bottom,
                            cklines[cklines.index(bottom) + 1],
                        )
                        if (new.shape != Shape.D) {
                            throw ChanException()
                        }
                        Bi.analyzer(new, fxs, bis, cklines, _from, level + 1, observer)
                        Bi.analyzer(fx, fxs, bis, cklines, _from, level + 1, observer)
                        Bi.BI_EQUAL = eq
                        return
                    }
                    Bi.BI_EQUAL = eq
                    if (bi.relation && fx.mid == bi.real_high) {
                        FenXing.append(fxs, fx)
                        __append(bis, bi, _from)
                    } else {
                        // 2024 05 21 修正
                        let _cklines = cklines[cklines.index(last.mid)..]
                        let (_, _bi) = Bi.analysis_one(_cklines, observer)
                        if (let Some(b) <- _bi) {
                            if (fxs.size > 2) {
                                let start = fxs[fxs.size - 3]
                                let nb = Bi(pre: None, start: start, end: b.start,
                                    elements: cklines[cklines.index(start.mid)..cklines.index(b.start.mid) + 1].toArray(
                                ))
                                if (!nb.check()) {
                                    return
                                }
                                let tmp = fxs[fxs.size - 1]
                                fxs.remove(fxs.size - 1)
                                if (tmp != last) {
                                    throw ChanException()
                                }
                                __pop(bis, tmp, _from)
                                Bi.analyzer(b.start, fxs, bis, cklines, _from, level + 1, observer)
                            }
                        }
                    }
                } else {
                    // DG
                    if (right.low < last.speck) {
                        let tmp = fxs[fxs.size - 1]
                        fxs.remove(fxs.size - 1)
                        if (!refEq(tmp, last)) {
                            throw ChanException()
                        }
                        __pop(bis, tmp, _from)
                    }
                }
                return

            case (Shape.D, Shape.X) =>
                if (last.speck > right.low) {
                    let tmp = fxs[fxs.size - 1]
                    fxs.remove(fxs.size - 1)
                    __pop(bis, tmp, _from)

                    if (!fxs.isEmpty()) {
                        last = fxs[fxs.size - 1]
                        if (last.shape != Shape.G) {
                            throw ChanException()
                        }
                        var tmp: ?NewBar = None
                        for (bar in cklines[cklines.index(last.mid)..cklines.index(fx.mid) + 1]) {
                            if (tmp.isNone()) {
                                tmp = Some(bar)
                            } else {
                                if (let Some(obj) <- tmp) {
                                    if (obj.high < bar.high) {
                                        tmp = Some(bar)
                                    }
                                }
                            }
                        }
                        let top: NewBar = tmp.getOrThrow()
                        if (top.shape != Shape.G) {
                            throw ChanException()
                        }
                        if (last.speck < top.high) {
                            let tmp = fxs[fxs.size - 1]
                            fxs.remove(fxs.size - 1)
                            __pop(bis, tmp, _from)
                            let i = cklines.index(top)
                            let new: FenXing = FenXing(cklines[i - 1], top, cklines[i + 1])
                            if (new.shape != Shape.G) {
                                throw ChanException()
                            }
                            Bi.analyzer(new, fxs, bis, cklines, _from, level + 1, observer)
                        }
                    }
                }
                return

            case (Shape.D, Shape.D) =>
                if (last.speck > mid.low) {
                    let tmp = fxs[fxs.size - 1]
                    fxs.remove(fxs.size - 1)
                    __pop(bis, tmp, _from)

                    if (!fxs.isEmpty()) {
                        last = fxs[fxs.size - 1]
                        if (last.shape != Shape.G) {
                            throw ChanException()
                        }
                        var tmp: ?NewBar = None
                        for (bar in cklines[cklines.index(last.mid)..cklines.index(fx.mid) + 1]) {
                            if (tmp.isNone()) {
                                tmp = Some(bar)
                            } else {
                                if (let Some(obj) <- tmp) {
                                    if (obj.high < bar.high) {
                                        tmp = Some(bar)
                                    }
                                }
                            }
                        }
                        let top: NewBar = tmp.getOrThrow()
                        if (top.shape != Shape.G) {
                            throw ChanException()
                        }
                        if (last.speck < top.high) {
                            let tmp = fxs[fxs.size - 1]
                            fxs.remove(fxs.size - 1)
                            __pop(bis, tmp, _from)

                            let i = cklines.index(top)
                            let new: FenXing = FenXing(cklines[i - 1], top, cklines[i + 1])
                            if (new.shape != Shape.G) {
                                throw ChanException()
                            }
                            Bi.analyzer(new, fxs, bis, cklines, _from, level + 1, observer)
                            Bi.analyzer(fx, fxs, bis, cklines, _from, level + 1, observer)
                            return
                        }
                    }

                    if (fxs.isEmpty()) {
                        FenXing.append(fxs, fx)
                        return
                    }

                    let start: FenXing = fxs[fxs.size - 1]
                    var bi = Bi(pre: None, start: start, end: fx,
                        elements: cklines[cklines.index(start.mid)..cklines.index(fx.mid) + 1].toArray())
                    FenXing.append(fxs, fx)
                    __append(bis, bi, _from)
                }
                return

            case (Shape.D, Shape.S) => return

            case (_, _) => throw ChanException()
        }
        return
    }

    public static func analysis_one(cklines: News, observer: Observer): (?FenXing, ?Bi) {
        if (cklines.size > 2) {
            var bis: Bis = Bis()
            var fxs: ArrayList<FenXing> = ArrayList<FenXing>()
            var fx: ?FenXing = None
            let size = cklines.size
            for (i in 1..size - 2) {
                let left = cklines[i - 1]
                let mid = cklines[i]
                let right = cklines[i + 1]
                Bi.analyzer(FenXing(left, mid, right), fxs, bis, cklines, "tmp", 0, observer)
                if (!bis.isEmpty()) {
                    fx = Some(FenXing(left, mid, right))
                    return (fx, Some(bis[0]))
                }
            }
            return (None, None)
        } else {
            return (None, None)
        }
    }
}

public class FeatureSequence <: HashableEquatable<FeatureSequence> & Line {
    public var elements: HashSet<Line>
    private let _id: Int64
    private var _direction: Direction = Direction.Unknow // 特征序列方向为线段方向

    FeatureSequence(elements: Array<Line>, direction: Direction) {
        this._id = TradingView.getID()
        this.elements = HashSet<Line>(elements)
        this._direction = direction
        for (obj in elements) {
            if (direction == obj.direction) {
                throw ChanException("FeatureSequence, 方向相同")
            }
        }
    }

    public prop bars: News {
        get() {
            throw ChanException()
        }
    }

    public mut prop index: Int64 {
        get() {
            throw ChanException()
        }
        set(_) {
            throw ChanException()
        }
    }

    public prop high: Float64 {
        get() {
            max(this.start.speck, this.end.speck)
        }
    }

    public prop low: Float64 {
        get() {
            min(this.start.speck, this.end.speck)
        }
    }

    public prop volume: Float64 {
        get() {
            throw ChanException()
        }
    }

    public prop direction: Direction {
        get() {
            this._direction
        }
    }

    public prop level: Byte {
        get() {
            let array = this.elements.toArray()
            if (array[0] is Duan) {
                return (array[0] as Duan).getOrThrow().level
            }
            return 0
        }
    }

    public prop start: FenXing {
        get() {
            var tmp: ?FenXing = None
            for (line in this.elements) {
                if (let Some(t) <- tmp) {
                    var f = {a: Float64, b: Float64 => max(a, b)}
                    if (this._direction == Direction.Down) {
                        f = {a: Float64, b: Float64 => min(a, b)}
                    } else if (this._direction == Direction.Up) {
                        f = {a: Float64, b: Float64 => max(a, b)}
                    } else {
                        throw ChanException()
                    }
                    if (f(t.speck, line.start.speck) == line.start.speck) {
                        tmp = Some(line.start)
                    }
                } else {
                    tmp = Some(line.start)
                }
            }
            return tmp.getOrThrow()
        }
    }

    public mut prop end: FenXing {
        get() {
            var tmp: ?FenXing = None
            for (line in this.elements) {
                if (let Some(t) <- tmp) {
                    var f = {a: Float64, b: Float64 => max(a, b)}
                    if (this._direction == Direction.Down) {
                        f = {a: Float64, b: Float64 => min(a, b)}
                    } else if (this._direction == Direction.Up) {
                        f = {a: Float64, b: Float64 => max(a, b)}
                    } else {
                        throw ChanException()
                    }
                    if (f(t.speck, line.end.speck) == line.end.speck) {
                        tmp = Some(line.end)
                    }
                } else {
                    tmp = Some(line.end)
                }
            }
            return tmp.getOrThrow()
        }
        set(_) {
            throw ChanException()
        }
    }

    public prop macd: Float64 {
        get() {
            var result = 0.0f64
            for (bar in elements) {
                result += bar.macd
            }
            return result
        }
    }

    public func hashCode(): Int64 {
        //"FeatureSequence(${this.direction}, ${this.elements})".hashCode()
        this._id
    }

    public operator override func ==(other: FeatureSequence): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: FeatureSequence): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "FeatureSequence(${this.direction}, ${this.elements})"
    }

    public func add(obj: Line, _from: String): Bool {
        if (obj.direction == this._direction) {
            throw ChanException("方向不匹配 ${this.direction} ${obj.direction} ${_from}")
        }
        return this.elements.put(obj)
    }

    public func romove(obj: Line, _from: String): Bool {
        if (obj.direction == this._direction) {
            throw ChanException("方向不匹配 ${_from}")
        }
        return this.elements.remove(obj)
    }

    public static func analyzer(objs: ArrayList<Line>, direction: Direction, _from: String): ArrayList<FeatureSequence> {
        var result = ArrayList<FeatureSequence>()
        for (obj in objs) {
            if (obj.direction == direction) {
                continue
            }

            if (result.size == 0) {
                result.append(FeatureSequence([obj], direction))
            } else {
                let last = result[result.size - 1]
                if (double_relation(last, obj) == Direction.Left) {
                    last.add(obj, _from)
                } else {
                    result.append(FeatureSequence([obj], direction))
                }
            }
        }
        return result
    }

    public static func analyzer(lines: Lines, direction: Direction): (?FeatureSequence, ?FeatureSequence, ?FeatureSequence) {
        if (!contains(direction)([Direction.Up, Direction.Down])) {
            throw ChanException("特征序列无法分辨方向 ${direction}")
        }
        let features = ArrayList<FeatureSequence>()
        for (line in lines) {
            if (line.direction == direction) {
                continue
            }

            if (features.size == 0) {
                features.append(FeatureSequence([line], direction))
            } else {
                let last = features[features.size - 1]
                if (double_relation(last, line) == Direction.Left) {
                    last.add(line, "")
                } else {
                    features.append(FeatureSequence([line], direction))
                }
            }
        }

        if (features.size == 0) {
            return (None, None, None)
        }

        if (features.size == 1) {
            return (Some(features[0]), Option<FeatureSequence>.None, Option<FeatureSequence>.None)
        }

        if (features.size == 2) {
            return (Some(features[0]), Some(features[1]), Option<FeatureSequence>.None)
        }

        if (features.size >= 3) {
            for (i in 0..features.size - 2) {
                let left = features[i]
                let mid = features[i + 1]
                let right = features[i + 2]

                try {
                    let (shape, (lm, mr)) = triple_relation(left, mid, right)
                    println("${features.size}, ${i}, ${shape}")
                    if (shape == Shape.G || shape == Shape.D) {
                    }
                } catch (a: ChanException) {
                    println("${a}")
                }
            }
            let relation = double_relation(features[features.size - 2], features[features.size - 1])
            if (direction == Direction.Up) {
                if (relation == Direction.JumpDown || relation == Direction.Down) {
                    return (Some(features[features.size - 3]), Some(features[features.size - 2]), Some(
                            features[features.size - 1]))
                } else {
                    return (Some(features[features.size - 2]), Some(features[features.size - 1]), Option<FeatureSequence>.
                            None)
                }
            } else {
                if (relation == Direction.JumpUp || relation == Direction.Up) {
                    return (Some(features[features.size - 3]), Some(features[features.size - 2]), Some(
                            features[features.size - 1]))
                } else {
                    return (Some(features[features.size - 2]), Some(features[features.size - 1]), Option<FeatureSequence>.
                            None)
                }
            }
        }

        return (None, None, None)
    }
}

public class Duan <: HashableEquatable<Duan> & Line & LineExtensions {
    public var pre: ?Duan
    private var _start: FenXing
    private var _end: FenXing
    private var _elements: Lines
    private var _index: Int64 = 0

    public var done: Bool = false
    public var jump: Bool = false

    public let features: Array<?FeatureSequence> = [None, None, None]
    private let _id: Int64
    private var _level: Byte = 1
    private let _stamp: String
    private let _bars: News = News()

    Duan(pre: ?Duan, start: FenXing, end: FenXing, elements: Lines, stamp!: String = "Duan") {
        this._id = TradingView.getID()
        this.pre = pre
        this._start = start
        this._end = end
        this._elements = elements
        this._stamp = stamp

        for (i in 1..elements.size) {
            if (elements[i - 1].index + 1 != elements[i].index) {
                throw ChanException()
            }
        }

        if (let Some(last) <- pre) {
            if (last.end != start) {
                throw ChanException()
            }
            this._index = last.index + 1
        }
    }

    public func hashCode(): Int64 {
        //"Duan(${this.pre}, ${this.start}, ${this.end}, ${this.direction}, ${this.elements})".hashCode()
        this._id
    }

    public operator override func ==(other: Duan): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: Duan): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "Duan(${this.pre.isSome()}, ${this.start}, ${this.end}, ${this.direction}, size=${this.elements.size})"
    }

    public prop elements: Lines {
        get() {
            this._elements
        }
    }

    public prop bars: News {
        get() {
            this._bars
        }
    }

    public mut prop index: Int64 {
        get() {
            this._index
        }
        set(index) {
            this._index = index
        }
    }

    public prop stamp: String {
        get() {
            this._stamp
        }
    }

    public prop start: FenXing {
        get() {
            return this._start
        }
    }

    public mut prop end: FenXing {
        get() {
            return this._end
        }
        set(fx) {
            this._end = fx
        }
    }

    public prop volume: Float64 {
        get() {
            var sum = 0.0f64
            for (bi in this.elements) {
                sum += bi.volume
            }
            sum
        }
    }

    public prop macd: Float64 {
        get() {
            var result = 0.0f64
            for (bar in elements) {
                result += bar.macd
            }
            return result
        }
    }

    public prop left: ?FeatureSequence {
        get() {
            return this.features[0]
        }
    }

    public prop mid: ?FeatureSequence {
        get() {
            return this.features[1]
        }
    }

    public prop right: ?FeatureSequence {
        get() {
            return this.features[2]
        }
    }

    public mut prop level: Byte {
        get() {
            this._level
        }
        set(level) {
            this._level = level
        }
    }

    public func get_elements(): ArrayList<Line> {
        var elements = ArrayList<Line>([])
        for (bi in this.elements) {
            elements.append(bi)
            if (bi.end == this.end) {
                break
            }
        }
        return elements
    }

    public static func feature_setter(offset: Int64, feature: ?FeatureSequence, features: Array<?FeatureSequence>,
        direction: Direction, line: Line, observer: Observer): Unit {
        if (feature.isSome()) {
            if (feature.getOrThrow().direction != direction) {
                throw ChanException("特征序列方向不匹配")
            }
        }
        if (feature.isNone()) {
            if (let Some(obj) <- features[offset]) {
                if (line is Duan) {
                    observer.update(obj, CMD.REMOVE("FeatureSequence"))
                }
            }
            features[offset] = feature
            return
        }

        if (features[offset].isNone()) {
            if (line is Duan) {
                observer.update(feature.getOrThrow(), CMD.APPEND("FeatureSequence"))
            }
            features[offset] = feature
        } else {
            features[offset].getOrThrow().elements = feature.getOrThrow().elements
            if (line is Duan) {
                observer.update(features[offset].getOrThrow(), CMD.MODIFY("FeatureSequence"))
            }
        }
    }

    public static func set_features(duan: Duan, bi: Line, observer: Observer): Unit {
        let (left, mid, right) = FeatureSequence.analyzer(duan.elements, duan.direction)
        Duan.feature_setter(0, left, duan.features, duan.direction, bi, observer)
        Duan.feature_setter(1, mid, duan.features, duan.direction, bi, observer)
        Duan.feature_setter(2, right, duan.features, duan.direction, bi, observer)
    }

    public static func set_done(duan: Duan, fx: FenXing, observer: Observer): ArrayList<Line> {
        if (fx != duan.mid.getOrThrow().start) {
            throw ChanException()
        }

        let elements = ArrayList<Line>([])
        for (obj in duan.elements) {
            if (elements.size > 0) {
                elements.append(obj)
            }

            if (obj.start == fx) {
                elements.append(obj)
            }
        }

        duan.end = fx
        let relation = double_relation(duan.left.getOrThrow(), duan.mid.getOrThrow())
        duan.jump = relation == Direction.JumpDown || relation == Direction.JumpUp
        observer.update(duan, CMD.MODIFY("ZhongShu<Duan>_checkThird"))
        observer.update(duan, CMD.MODIFY(duan.stamp))
        //println(colored("setDone, ${duan}", color: "red", attrs: "blink"))
        return elements
    }

    public static func __append(xds: Duans, duan: Duan, observer: Observer): Unit {
        if (xds.size > 0 && xds[xds.size - 1].end != duan.start) {
            throw ChanException("线段连续性错误")
        }

        var index = 0
        var pre: ?Duan = None
        if (xds.size > 0) {
            index = xds[xds.size - 1].index + 1
        }

        duan.index = index

        xds.append(duan)

        observer.update(duan, CMD.APPEND(duan.stamp))
    }

    public static func __pop(xds: Duans, duan: Duan, observer: Observer): Unit {
        if (xds.size == 0) {
            return
        }
        if (xds[xds.size - 1] != duan) {
            throw ChanException()
        }
        xds.remove(xds.size - 1)
        observer.update(duan, CMD.REMOVE(duan.stamp))
    }

    public static func pop(line: Line, xds: Duans, observer: Observer): Unit {
        if (xds.size == 0) {
            return
        }
        let cmd = "Duan.POP"
        let duan: Duan = xds[xds.size - 1]
        var pre: ?Duan = if (xds.size > 1) {
            xds[xds.size - 2]
        } else {
            None
        }

        dp("${cmd}, ${duan} ${line}")

        if (duan.elements[duan.elements.size - 1] == line) {
            duan.elements.remove(duan.elements.size - 1)
        }

        if (let Some(last) <- pre) {
            if ((last.right.isSome() && (last.right.getOrThrow().elements |> any {bi: Line => line == bi})) || (last.
                right.isNone() && (last.left.getOrThrow().elements |> any {bi: Line => line == bi}))) {
                Duan.__pop(xds, duan, observer)
                if (last.elements[last.elements.size - 1] == line) {
                    last.elements.remove(last.elements.size - 1)
                }
                Duan.set_features(last, line, observer)
                return
            }
        }
        if (duan.elements.size > 0) {
            Duan.set_features(duan, line, observer)
        } else {
            Duan.__pop(xds, duan, observer)
        }
    }

    public static func push(bi: Line, xds: Duans, observer: Observer): Unit {
        let cmd = "Duan.PUSH"

        let stamp = if (bi.stamp == "Bi") {
            "Duan"
        } else {
            "Duan${bi.stamp}"
        }

        let level: Byte = if (bi.stamp == "Bi") {
            1
        } else {
            (bi as Duan).getOrThrow().level + 1
        }

        var new = Duan(None, bi.start, bi.end, Lines([bi]), stamp: stamp)
        new.level = level
        if (xds.isEmpty()) {
            Duan.__append(xds, new, observer)
            return
        }

        var duan = xds[xds.size - 1]

        dp("${cmd}, ${duan} ${bi}")

        if (duan.elements[duan.elements.size - 1].end != bi.start) {
            throw ChanException("线段添加元素时，元素不连续${duan.elements[duan.elements.size - 1]}, ${bi}")
        }

        if (duan.elements[duan.elements.size - 1].index + 1 != bi.index) {
            throw ChanException("线段添加元素时，元素不连续${duan.elements[duan.elements.size - 1].index}, ${bi.index}")
        }

        duan.elements.append(bi)
        if (duan.direction == bi.direction) {
            // 与线段方向相同时修改线段终点
            if (let Some(mid) <- duan.mid) {
                if (duan.direction == Direction.Up) {
                    if (duan.high < bi.high) {
                        duan.end = bi.end
                    } else {
                        duan.end = mid.start
                    }
                } else {
                    if (duan.low > bi.low) {
                        duan.end = bi.end
                    } else {
                        duan.end = mid.start
                    }
                }
            } else {
                duan.end = bi.end
            }
            if (duan.stamp == "Duan" && observer.duan_zss.size > 0) {
                observer.update(observer.duan_zss[observer.duan_zss.size - 1], CMD.MODIFY("ZhongShu<Duan>"))
            }

            if (duan.stamp == "DuanDuan" && observer.duan_duan_zss.size > 0) {
                observer.update(observer.duan_zss[observer.duan_duan_zss.size - 1], CMD.MODIFY("ZhongShu<Duan>"))
            }
            observer.update(duan, CMD.MODIFY(duan.stamp))
            return
        }

        if (xds.size == 1) {
            if ((duan.direction == Direction.Up && bi.low < duan.start.speck && duan.elements.size == 1) || (duan.
                direction == Direction.Down && bi.high > duan.start.speck && duan.elements.size == 1)) {
                new = Duan(None, bi.start, bi.end, Lines([bi]), stamp: stamp)
                new.level = level
                Duan.__pop(xds, duan, observer)
                Duan.__append(xds, new, observer)
                return
            }
        }

        Duan.set_features(duan, bi, observer)
        if (duan.right.isSome()) {
            let elements = set_done(duan, duan.mid.getOrThrow().start, observer)

            new = Duan(duan, elements[0].start, elements[elements.size - 1].end, elements, stamp: stamp)
            new.level = level
            Duan.set_features(new, bi, observer)
            Duan.__append(xds, new, observer)
            if (duan.jump) {
                new.pre = Some(duan)
            }
            if (duan.direction == Direction.Up) {
                dp("${cmd}, 顶分型终结，缺口: ${duan.jump}")
            } else {
                dp("${cmd}, 底分型终结，缺口: ${duan.jump}")
            }
        }
    }

    public static func modify(line: Line, xds: Duans, observer: Observer): Unit {
        let cmd = "Duan.MODIFY"
        let duan = xds[xds.size - 1]

        Duan.set_features(duan, line, observer)
        if (duan.elements.size == 1) {
            duan.end = duan.elements[0].end
        }
        if (duan.left.isSome()) {
            duan.end = duan.left.getOrThrow().start
        }
        if (duan.mid.isSome()) {
            duan.end = duan.mid.getOrThrow().start
        }

        if (duan.elements.size >= 3) {
            let bi = if (duan.elements.size % 2 == 1) {
                duan.elements[duan.elements.size - 1]
            } else {
                duan.elements[duan.elements.size - 2]
            }
            if (let Some(mid) <- duan.mid) {
                if (duan.direction == Direction.Up) {
                    if (duan.high < bi.high) {
                        duan.end = bi.end
                    } else {
                        duan.end = mid.start
                    }
                } else {
                    if (duan.low > bi.low) {
                        duan.end = bi.end
                    } else {
                        duan.end = mid.start
                    }
                }
            } else {
                duan.end = bi.end
            }
        }

        observer.update(duan, CMD.MODIFY(duan.stamp))
        if (duan.right.isSome()) {
            let elements = set_done(duan, duan.mid.getOrThrow().start, observer)

            let new = Duan(duan, elements[0].start, elements[elements.size - 1].end, elements, stamp: duan.stamp)
            new.level = duan.level
            Duan.set_features(new, line, observer)
            Duan.__append(xds, new, observer)
            if (duan.jump) {
                new.pre = Some(duan)
            }
            if (duan.direction == Direction.Up) {
                dp("${cmd}, 顶分型终结，缺口: ${duan.jump}")
            } else {
                dp("${cmd}, 底分型终结，缺口: ${duan.jump}")
            }
        }
    }
}

public class ZhongShu <: ToString & Interval & HashableEquatable<ZhongShu> & Line {
    private var _index: Int64 = 0
    private let _direction: Direction
    public let bspoints = ArrayList<BSPoint>()

    public var elements: ArrayList<Line> = ArrayList<Line>()
    private var _third: ?Line = Option<Line>.None
    private let _id: Int64
    private var _level: Byte = 0

    init(elements: Array<Line>) {
        this._id = TradingView.getID()
        if (elements.size < 3) {
            throw ChanException("ZhongShu init elements size < 3")
        }
        //let relation = double_relation(elements[0], elements[2])

        this.elements = ArrayList<Line>(elements)
        this._direction = elements[1].direction
    }

    public func hashCode(): Int64 {
        //"ZhongShu(${this.index}, ${this.third}, ${this.direction}, ${this.elements})".hashCode()
        this._id
    }

    public operator override func ==(other: ZhongShu): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: ZhongShu): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "ZhongShu(index:${this.index}, third:${this.third.isSome()}, ${this.direction}, zg:${this.zg}, zd:${this.zd}, elements.size=${this.elements.size})"
    }

    public prop bars: News {
        get() {
            throw ChanException()
        }
    }

    public mut prop third: ?Line {
        get() {
            this._third
        }
        set(third) {
            this._third = third
        }
    }

    public mut prop index: Int64 {
        get() {
            this._index
        }
        set(index) {
            this._index = index
        }
    }

    public prop stamp: String {
        get() {
            "ZhongShu<${this.elements[0].stamp}>"
        }
    }

    public prop high: Float64 {
        get() {
            this.zg
        }
    }

    public prop low: Float64 {
        get() {
            this.zd
        }
    }

    public prop volume: Float64 {
        get() {
            var sum = 0.0f64
            for (bar in this.elements) {
                sum += bar.volume
            }
            sum
        }
    }

    public prop direction: Direction {
        get() {
            if (this.elements.size == 0) {
                Direction.Unknow
            } else if (this.elements.size == 1) {
                !this.elements[0].direction
            } else {
                this.elements[1].direction
            }
        }
    }

    public prop macd: Float64 {
        get() {
            var result = 0.0f64
            for (line in elements) {
                result += line.macd
            }
            return result
        }
    }

    public prop left: ?Line {
        get() {
            this.elements.get(0)
        }
    }

    public prop mid: ?Line {
        get() {
            this.elements.get(1)
        }
    }

    public prop right: ?Line {
        get() {
            this.elements.get(2)
        }
    }

    public prop zg: Float64 {
        get() {
            var size = 0
            var high = Float64.Max
            for (obj in this.elements) {
                if (size == 3) {
                    break
                }
                high = min(high, obj.high)
                size += 1
            }
            return high
        }
    }

    public prop zd: Float64 {
        get() {
            var size = 0
            var low = Float64.Min
            for (obj in this.elements) {
                if (size == 3) {
                    break
                }
                low = max(low, obj.low)
                size += 1
            }
            return low
        }
    }

    public prop gg: Float64 {
        get() {
            var high = Float64.Min
            for (obj in this.elements) {
                high = max(high, obj.high)
            }
            return high
        }
    }

    public prop dd: Float64 {
        get() {
            var low = Float64.Max
            for (obj in this.elements) {
                low = min(low, obj.low)
            }
            return low
        }
    }

    public prop start: FenXing {
        get() {
            this.elements[0].start
        }
    }

    public mut prop end: FenXing {
        get() {
            this.elements[this.elements.size - 1].end
        }
        set(_) {
            throw ChanException()
        }
    }

    public mut prop level: Byte {
        get() {
            this._level
        }
        set(level) {
            this._level = level
        }
    }

    public func check(): Bool {
        let relation = double_relation(this.left.getOrThrow(), this.right.getOrThrow())
        return contains(relation)([Direction.Up, Direction.Down, Direction.Right, Direction.Left])
    }

    public func pop_element(obj: Line, observer: Observer, _from: String): Unit {
        if (let Some(third) <- this.third) {
            if (third == obj) {
                this.third = None
                dp("ZhongShu.pop_element ${_from}, 第三买卖点, ${this.bspoints.size}, ${obj}")
                var i = 0
                for (bsp in this.bspoints) {
                    if (bsp.getValid() == true && bsp.getInfo() == "Third") {
                        let new = bsp.setValid(false) //.setOffset(observer.news[observer.news.size-1].index- obj.end.mid.index)
                        this.bspoints.set(i, new)
                        observer.update(new, CMD.MODIFY("BSPoint"))
                    }
                    i += 1
                }
                return
            }
            if (third.index < obj.index) {
                return
            }
            throw ChanException("中枢结束标志不符 ${third} == ${obj}")
        }

        let last = this.elements[this.elements.size - 1]
        if (last != obj) {
            throw ChanException("不同 ${last} ${obj}")
        }
        this.elements.remove(this.elements.size - 1)
    }

    public func append_element(obj: Line, observer: Observer, _from: String): Unit {
        let size = this.elements.size
        if (size == 0) {
            throw ChanException()
        }

        if (this.elements[size - 1].index + 1 != obj.index) {
            throw ChanException("ZhongShu append_element index 不连贯")
        }

        if (size == 1) {
            this.elements.append(obj)
        } else if (size == 2) {
            let relation = double_relation(this.elements[0], obj)
            if (contains(relation)([Direction.Up, Direction.Down, Direction.Right, Direction.Left])) {
                this.elements.append(obj)
            } else if (relation == Direction.Unknow) {
                throw ChanException()
            } else {
                this.elements.remove(0)
                this.elements.remove(0)
                this.elements.append(obj)
            }
        } else {
            let relation = double_relation(this, obj)
            if (contains(relation)([Direction.Up, Direction.Down, Direction.Right, Direction.Left])) {
                let last = this.elements[this.elements.size - 1]
                if (last.end == obj.start) {
                    this.elements.append(obj)
                } else {
                    throw ChanException("中枢无法添加元素")
                }
            } else if (contains(relation)([Direction.JumpUp, Direction.JumpDown])) {
                if (this.third.isSome()) {
                    throw ChanException("ZhongShu third is not None ${this.third}")
                } else {
                    this.third = Some(obj)
                    for (p in this.bspoints) {
                        if (p.getValid() == true) {
                            throw ChanException()
                        }
                    }
                    if (let Some(bsp) <- BSPoint.calc_zs_third_bsp(this, obj, observer)) {
                        this.bspoints.append(bsp)
                        observer.update(bsp, CMD.APPEND("BSPoint"))
                    }
                    if (_from == "analyzer") {
                        observer.update(this, CMD.MODIFY(this.stamp))
                        /*
                        if (obj is Bi) {
                            observer.update(this, CMD.MODIFY("ZhongShu<Bi>"))
                        }
                        if (obj is Duan) {
                            observer.update(this, CMD.MODIFY("ZhongShu<Duan>"))
                        }
                         */
                    }
                }
            } else {
                throw ChanException("ZhongShu relation")
            }
        }
    }

    public static func analyzer_pop(obj: Line, zss: ArrayList<ZhongShu>, level: UInt16, _from: String,
        observer: Observer): Unit {
        let cmd = "ZhongShu.POP"

        func _pop(zss: ArrayList<ZhongShu>, zs: ZhongShu, _from: String): Unit {
            if (zss.size > 0) {
                if (zss[zss.size - 1] == zs) {
                    zss.remove(zss.size - 1)
                    observer.update(zs, CMD.REMOVE(zs.stamp))
                /*
                    if (_from == "analyzer") {
                        if (obj is Bi) {
                            observer.update(zs, CMD.REMOVE("ZhongShu<Bi>"))
                        }
                        if (obj is Duan) {
                            observer.update(zs, CMD.REMOVE("ZhongShu<Duan>"))
                        }
                    }
                 */
                } else {
                    throw ChanException()
                }
            }
        }

        if (zss.size > 0) {
            let last = zss[zss.size - 1]
            dp("${cmd}, z  ss.size=${zss.size}, ${last.third.isSome()}, ${obj}")
            last.pop_element(obj, observer, _from)
            if (last.elements.size == 0) {
                _pop(zss, last, _from)
            } else {
                if (_from == "analyzer") {
                    observer.update(last, CMD.MODIFY(last.stamp))
                    /*
                    if (obj is Bi) {
                        observer.update(last, CMD.MODIFY("ZhongShu<Bi>"))
                    }
                    if (obj is Duan) {
                        observer.update(last, CMD.MODIFY("ZhongShu<Duan>"))
                    }
                     */
                }
            }
        }
    }

    public static func analyzer_push(obj: Line, zss: ArrayList<ZhongShu>, objs: ArrayList<Line>, level: UInt16,
        _from: String, observer: Observer): Unit {
        let cmd = "ZhongShu.PUSH"

        func __append(zss: ArrayList<ZhongShu>, zs: ZhongShu, _from: String): Unit {
            var index: Int64 = 0
            if (zss.size > 0) {
                index = zss[zss.size - 1].index + 1
            }
            zs.index = index
            zss.append(zs)
            if (_from == "analyzer") {
                observer.update(zs, CMD.APPEND(zs.stamp))
                /*
                if (obj is Bi) {
                    observer.update(zs, CMD.APPEND("ZhongShu<Bi>"))
                }
                if (obj is Duan) {
                    observer.update(zs, CMD.APPEND("ZhongShu<Duan>"))
                }
                 */
            }

            dp("${cmd}, append")
        }
        dp("${cmd}, zss.size=${zss.size}, ${obj}")

        if (zss.isEmpty()) {
            if (obj.index >= 2) {
                let left = objs[objs.size - 3]
                let mid = objs[objs.size - 2]
                let right = objs[objs.size - 1]
                let relation = double_relation(left, right)
                if (contains(relation)([Direction.Up, Direction.Down, Direction.Right, Direction.Left])) {
                    let new = ZhongShu([left, mid, right])
                    __append(zss, new, _from)
                }
            }
        } else {
            let last = zss[zss.size - 1]
            if (let Some(third) <- last.third) {
                if (contains(double_relation(last, third))([Direction.Up, Direction.Down, Direction.Right,
                    Direction.Left])) {
                    throw ChanException("第三买卖点 无效！${third}")
                }
                if (obj.index - third.index >= 2) {
                    // 符合形成中枢条件
                    let left = objs[objs.size - 3]
                    let mid = objs[objs.size - 2]
                    let right = objs[objs.size - 1]

                    if (left.direction == third.direction) {
                        let relation = double_relation(left, right)
                        if (contains(relation)([Direction.Up, Direction.Down, Direction.Right, Direction.Left])) {
                            let new = ZhongShu([left, mid, right])
                            __append(zss, new, _from)
                            return
                        }
                    }
                }
            } else {
                last.append_element(obj, observer, _from)
                if (_from == "analyzer") {
                    observer.update(last, CMD.MODIFY(last.stamp))
                    /*
                    if (obj is Bi) {
                        observer.update(last, CMD.MODIFY("ZhongShu<Bi>"))
                    }
                    if (obj is Duan) {
                        observer.update(last, CMD.MODIFY("ZhongShu<Duan>"))
                    }
                     */
                }
                if (let Some(third) <- last.third) {
                    if (obj.index - third.index >= 2) {
                        // 符合形成中枢条件
                        let left = objs[objs.size - 3]
                        let mid = objs[objs.size - 2]
                        let right = objs[objs.size - 1]

                        if (left.direction == third.direction) {
                            let relation = double_relation(left, right)
                            if (contains(relation)([Direction.Up, Direction.Down, Direction.Right, Direction.Left])) {
                                let new = ZhongShu([left, mid, right])
                                __append(zss, new, _from)
                                return
                            }
                        }
                    }
                }
            }
        }
    }

    public static func analyzer(elements: ArrayList<Line>, observer: Observer): (Bool, ArrayList<ZhongShu>) {
        let zss = ArrayList<ZhongShu>()
        if (elements.size < 3) {
            return (false, zss)
        }

        for (obj in elements) {
            ZhongShu.analyzer_push(obj, zss, elements, 0, "tmp", observer)
        }
        return (zss.size > 0, zss)
    }
}

class BaseAnalyzer <: Observer {
    public var _symbol: String
    public var _freq: UInt32
    public var ws: ?WebSocket = None
    public var _raws: Raws = Raws()
    public var _news: News = News()
    public var _fxs: ArrayList<FenXing> = ArrayList<FenXing>()

    public let _bis: Bis = Bis()
    public let _duans: Duans = Duans()
    public let _bi_zss: ArrayList<ZhongShu> = ArrayList<ZhongShu>()
    public let _duan_zss: ArrayList<ZhongShu> = ArrayList<ZhongShu>()

    public var _duan_bis: Bis = Bis()
    public var _duan_duans: Duans = Duans()
    public var _duan_bi_zss: ArrayList<ZhongShu> = ArrayList<ZhongShu>()
    public var _duan_duan_zss: ArrayList<ZhongShu> = ArrayList<ZhongShu>()

    BaseAnalyzer(symbol: String, freq: UInt32, ws!: ?WebSocket = None) {
        this._symbol = symbol
        this._freq = freq
        this.ws = ws
    }

    public prop symbol: String {
        get() {
            this._symbol
        }
    }

    public prop freq: UInt32 {
        get() {
            this._freq
        }
    }

    public prop raws: Raws {
        get() {
            this._raws
        }
    }

    public prop news: News {
        get() {
            this._news
        }
    }

    public prop fxs: ArrayList<FenXing> {
        get() {
            this._fxs
        }
    }

    public prop bis: Bis {
        get() {
            this._bis
        }
    }

    public prop duans: Duans {
        get() {
            this._duans
        }
    }

    public prop bi_zss: ArrayList<ZhongShu> {
        get() {
            this._bi_zss
        }
    }

    public prop duan_zss: ArrayList<ZhongShu> {
        get() {
            this._duan_zss
        }
    }

    public prop duan_bis: Bis {
        get() {
            this._duan_bis
        }
    }

    public prop duan_duans: Duans {
        get() {
            this._duan_duans
        }
    }

    public prop duan_bi_zss: ArrayList<ZhongShu> {
        get() {
            this._duan_bi_zss
        }
    }

    public prop duan_duan_zss: ArrayList<ZhongShu> {
        get() {
            this._duan_duan_zss
        }
    }

    public func update(o: ToString, cmd: CMD): Unit {
        let _from = "analyzer"
        if (cmd.toString().indexOf("NewBar").isSome()) {
            let obj = (o as NewBar).getOrThrow()
            TradingView.push(obj, this.ws)
            return
        }
        //println("${cmd}, ${o}")
        match (cmd) {
            case CMD.APPEND(name) =>
                //println(name)
                if (name == "RawBar") {
                let obj = (o as RawBar).getOrThrow()
            //TradingView.push(obj, this.ws)
            } else if (name == "NewBar") {
                let obj = (o as NewBar).getOrThrow()
                TradingView.push(obj, this.ws)
            } else if (name == "BSPoint") {
                let obj = (o as BSPoint).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "Bi") {
                let obj = (o as Bi).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                let (zss, duans, bis) = (this.bi_zss, this.duans, this.bis)
                ZhongShu.analyzer_push(obj, zss, bis.toLines(), 0, _from, this)
                Duan.push(obj, duans, this)
            } else if (name == "Duan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                ZhongShu.analyzer_push(obj, this.duan_zss, this.duans.toLines(), 0, _from, this)
                Duan.push(obj, this.duan_duans, this)
            } else if (name == "FeatureSequence") {
                let obj = (o as FeatureSequence).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "DuanDuan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, CMD.APPEND("Duan"))
                ZhongShu.analyzer_push(obj, this.duan_duan_zss, this.duan_duans.toLines(), 0, _from, this)
            } else if (name == "ZhongShu<Bi>") {
                let obj = (o as ZhongShu).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Duan>" || name == "ZhongShu<DuanDuan>") {
                let obj = (o as ZhongShu).getOrThrow()
                TradingView.push(obj, this.ws, CMD.APPEND("ZhongShu<Duan>"))
            } else {
                println("unknow : ${cmd}")
            }

            case CMD.REMOVE(name) =>
                //println(name)
                if (name == "BSPoint") {
                let obj = (o as BSPoint).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "Bi") {
                let obj = (o as Bi).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                let (bi_zss, duans) = (this.bi_zss, this.duans)
                ZhongShu.analyzer_pop(obj, bi_zss, 0, _from, this)
                Duan.pop(obj, duans, this)
            } else if (name == "Duan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                ZhongShu.analyzer_pop(obj, this.duan_zss, 0, _from, this)
                Duan.pop(obj, this.duan_duans, this)
            } else if (name == "FeatureSequence") {
                let obj = (o as FeatureSequence).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "DuanDuan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, CMD.REMOVE("Duan"))
                ZhongShu.analyzer_pop(obj, this.duan_duan_zss, 0, _from, this)
            } else if (name == "ZhongShu<Bi>") {
                let obj = (o as ZhongShu).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Duan>" || name == "ZhongShu<DuanDuan>") {
                let obj = (o as ZhongShu).getOrThrow()
                TradingView.push(obj, this.ws, CMD.REMOVE("ZhongShu<Duan>"))
            } else {
                println("unknow : ${cmd}")
            }

            case CMD.MODIFY(name) =>
                //println(name)
                if (name == "BSPoint") {
                let obj = (o as BSPoint).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "Duan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                Duan.modify(obj, this.duan_duans, this)
            } else if (name == "FeatureSequence") {
                let obj = (o as FeatureSequence).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "DuanDuan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, CMD.MODIFY("Duan"))
            } else if (name == "ZhongShu<Bi>") {
                let obj = (o as ZhongShu).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Duan>" || name == "ZhongShu<DuanDuan>") {
                let obj = (o as ZhongShu).getOrThrow()
                TradingView.push(obj, this.ws, CMD.MODIFY("ZhongShu<Duan>"))
            } else if (name == "ZhongShu<Duan>_checkThird") {
                let duan = (o as Duan).getOrThrow()
                var zss = if (duan.level == 1) {
                    this.duan_zss
                } else if (duan.level == 2) {
                    this.duan_duan_zss
                } else {
                    throw ChanException()
                }

                var duans = if (duan.level == 1) {
                    this.duans
                } else if (duan.level == 2) {
                    this.duan_duans
                } else {
                    throw ChanException()
                }

                if (zss.isEmpty()) {
                    return
                }
                let zs = zss[zss.size - 1]
                if (let Some(third) <- zs.third) {
                    if (third == duan) {
                        if (contains(double_relation(zs, duan))(
                            [Direction.Up, Direction.Down, Direction.Right, Direction.Left])) {
                            ZhongShu.analyzer_pop(duan, zss, 0, _from, this)
                            ZhongShu.analyzer_push(duan, zss, duans.toLines(), 0, _from, this)
                        }
                    }
                }

            //TradingView.push(zs, this.ws, cmd)
            } else {
                println("unknow : ${cmd}")
            }
        }
    }

    public func push(dt: Int64, open: Float64, high: Float64, low: Float64, close: Float64, volume: Float64,
        fast_period!: UInt32, slow_period!: UInt16, signal_periot!: UInt16) {
        let bar = RawBar(DateTime.int2ts(dt), open, high, low, close, volume, 0)
        this.push(bar, fast_period: fast_period, slow_period: slow_period, signal_periot: signal_periot)
    }

    public func push(dt: DateTime, open: Float64, high: Float64, low: Float64, close: Float64, volume: Float64,
        fast_period!: UInt32, slow_period!: UInt16, signal_periot!: UInt16) {
        let bar = RawBar(dt, open, high, low, close, volume, 0)
        this.push(bar, fast_period: fast_period, slow_period: slow_period, signal_periot: signal_periot)
    }

    public func push(bar: RawBar, fast_period!: UInt32 = 12, slow_period!: UInt16 = 26, signal_periot!: UInt16 = 9): Unit {
        if (this.raws.isEmpty()) {
            this.raws.append(bar)
        } else {
            let last = this.raws[this.raws.size - 1]
            if (last.dt == bar.dt) {
                throw ChanException()
            }
            bar.index = last.index + 1
            this.raws.append(bar)
            //this.update(bar, CMD.APPEND("RawBar"))
            //sleep(Duration.millisecond * 50)
        }

        if (this.news.size > 0) {
            if (let Some(nb) <- this.news[this.news.size - 1].merge(bar)) {
                this.news.append(nb)
                this.update(nb, CMD.APPEND("NewBar"))
                sleep(Duration.millisecond * 5)
            } else {
                this.update(this.news[this.news.size - 1], CMD.MODIFY("NewBar"))
            }
        } else {
            let nb = bar.toNewBar(None)
            this.news.append(nb)
            this.update(nb, CMD.APPEND("NewBar"))
            return
        }

        if (this.news.size >= 3) {
            let left = this.news[this.news.size - 3]
            let mid = this.news[this.news.size - 2]
            let right = this.news[this.news.size - 1]
            let (shape, _) = triple_relation(left, mid, right)

            mid.shape = shape
            if (shape == Shape.G) {
                mid.speck = mid.high
                right.speck = right.low
            } else if (shape == Shape.D) {
                mid.speck = mid.low
                right.speck = right.high
            } else if (shape == Shape.S) {
                mid.speck = mid.high
                right.speck = right.high
                right.shape = Shape.S
            } else if (shape == Shape.X) {
                mid.speck = mid.low
                right.speck = right.low
                right.shape = Shape.X
            }

            let fx = FenXing(left, mid, right)

            Bi.analyzer(fx, this.fxs, this.bis, this.news, "analyzer", 0, this)
        }
    }

    public func analyzer() {
    }

    public static func fromData(symbol: String, freq: UInt32, buffer: Array<Byte>, ws!: ?WebSocket = None): BaseAnalyzer {
        var obj = BaseAnalyzer(symbol, freq, ws: ws)
        let size = 48 // struct.calcsize(">6d")

        for (i in 0..buffer.size / size) {
            //for (i in 3050..buffer.size / size) {
            let bar = RawBar.readBigEndian(buffer[i * size..(i + 1) * size])
            obj.push(bar)
        }
        return obj
    }

    public static func readFromDatFile(path: String, ws!: ?WebSocket = None): BaseAnalyzer {
        let filename = Path(path).fileName.getOrThrow()
        let tmp = filename.split("-", 3)
        let symbol = tmp[0]
        let freq: UInt32 = UInt32.parse(tmp[1])
        let buffer = File.readFrom(path)
        return BaseAnalyzer.fromData(symbol, freq, buffer, ws: ws)
    }
}

class NaiveDistributor <: HttpRequestDistributor {
    let map = HashMap<String, HttpRequestHandler>()
    public func register(path: String, handler: HttpRequestHandler): Unit {
        println(path)
        map.put(path, handler)
    }

    public func distribute(path: String): HttpRequestHandler {
        println(path)
        if (path == "/ws") {
            return WSHandler()
        }

        return NotFoundHandler()
    }
}

class NotFoundHandler <: HttpRequestHandler {
    public func handle(httpContext: HttpContext): Unit {
        httpContext.responseBuilder.status(404).body("404 Not Found")
    }
}

class WSHandler <: HttpRequestHandler {
    public func handle(ctx: HttpContext): Unit {
        println("${ctx.request.url}")
        println("${ctx.request.remoteAddr}")
        // 2 完成 websocket 握手，获取 websocket 实例
        let websocketServer = WebSocket.upgradeFromServer(
            ctx,
            subProtocols: ArrayList<String>(["foo", "bar", "foo1"]),
            userFunc: {
                request: HttpRequest =>
                let value = request.headers.getFirst("sec-websocket-extensions") ?? ""
                println("${value}")
                request.headers.del("sec-websocket-extensions")
                let headers = HttpHeaders()
                headers
            }
        )
        // 3 消息收发
        // 收 hello
        var last_time = MonoTime.now()
        let data = ArrayList<UInt8>()
        var frame = websocketServer.read()
        while (true) {
            println("${DateTime.now()}   ${frame.frameType}")
            match (frame.frameType) {
                case ContinuationWebFrame =>
                    data.appendAll(frame.payload)
                    if (frame.fin) {
                        break
                    }
                case TextWebFrame | BinaryWebFrame =>
                    if (!data.isEmpty()) {
                        throw Exception("invalid frame")
                    }
                    //data.appendAll(frame.payload)

                    let message = String.fromUtf8(frame.payload.toArray())
                    println("data: ${message}")
                    if (message == "hello") {
                        spawn {
                            BaseAnalyzer.readFromDatFile(
                                "/home/moscow/PycharmProjects/chanlun.py/btcusd-300-1713295800-1715695500.dat",
                                ws: Some(websocketServer)
                            )
                        }
                    }
                    if (frame.fin) {
                        break
                    }
                case CloseWebFrame =>
                    websocketServer.write(CloseWebFrame, frame.payload)
                    break
                case PingWebFrame => websocketServer.writePongFrame(frame.payload)
                case _ => ()
            }
            frame = websocketServer.read()
            var now = MonoTime.now()
            if (last_time + Duration.second * 12 < now) {
                unsafe { websocketServer.write(TextWebFrame, DateTime.now().toString().rawData()) }
                last_time = now
            }
        }
        /*
            println("data: ${String.fromUtf8(data.toArray())}") // hello

            // 发 4097 个 a
            websocketServer.write(TextWebFrame, Array<UInt8>(4097, repeat: 97))

            // 4 关闭 websocket，
            // 收发 CloseFrame
            let websocketFrame = websocketServer.read()
            println("close frame type: ${websocketFrame.frameType}") // CloseWebFrame
            println("close frame payload: ${websocketFrame.payload}") // 3, 232
            websocketServer.write(CloseWebFrame, websocketFrame.payload)
            // 关闭底层连接
            websocketServer.closeConn()
         */
    }
}

public func CreateMultipointShapeOptions(
    shape!: String = "trend_line",
    lock!: Bool = true,
    disableSelection!: Bool = true,
    disableSave!: Bool = true,
    disableUndo!: Bool = true,
    text!: String = "text",
    filled!: Bool = false,
    icon!: Int64 = 0,
    showInObjectsTree!: Bool = true,
    zOrder!: ?String = None // ​"top" | "bottom"
): JsonObject {
    //https://www.tradingview.com/charting-library-docs/v27/api/interfaces/Charting_Library.CreateMultipointShapeOptions

    let obj = JsonObject()
    let shapes = "​emoji | triangle | curve | circle | ellipse | path | polyline | text | icon | extended | anchored_text | anchored_note | note | signpost | double_curve | arc | sticker | arrow_up | arrow_down | arrow_left | arrow_right | price_label | price_note | arrow_marker | flag | vertical_line | horizontal_line | cross_line | horizontal_ray | trend_line | info_line | trend_angle | arrow | ray | parallel_channel | disjoint_angle | flat_bottom | anchored_vwap | pitchfork | schiff_pitchfork_modified | schiff_pitchfork | balloon | comment | inside_pitchfork | pitchfan | gannbox | gannbox_square | gannbox_fixed | gannbox_fan | fib_retracement | fib_trend_ext | fib_speed_resist_fan | fib_timezone | fib_trend_time | fib_circles | fib_spiral | fib_speed_resist_arcs | fib_channel | xabcd_pattern | cypher_pattern | abcd_pattern | callout | triangle_pattern | 3divers_pattern | head_and_shoulders | fib_wedge | elliott_impulse_wave | elliott_triangle_wave | elliott_triple_combo | elliott_correction | elliott_double_combo | cyclic_lines | time_cycles | sine_line | long_position | short_position | forecast | date_range | price_range | date_and_price_range | bars_pattern | ghost_feed | projection | rectangle | rotated_rectangle | brush | highlighter | regression_trend | fixed_range_volume_profile"
    if (shapes.indexOf(shape).isNone()) {
        throw UnsupportedException("CreateMultipointShapeOptions: Unsupported shape (${shape})")
    }
    obj.put("shape", JsonString(shape))
    obj.put("lock", JsonBool(lock))
    obj.put("disableSelection", JsonBool(disableSelection))
    obj.put("disableSave", JsonBool(disableSave))
    obj.put("disableUndo", JsonBool(disableUndo))
    obj.put("text", JsonString(text))
    obj.put("filled", JsonBool(filled))
    if (shape == "icon") {
        obj.put("icon", JsonInt(icon))
    }
    obj.put("showInObjectsTree", JsonBool(showInObjectsTree))
    if (let Some(tmp) <- zOrder) {
        if (tmp == "top" || tmp == "bottom") {
            obj.put("zOrder", JsonString(tmp))
        } else {
            println("CreateMultipointShapeOptions: Unsupported zOrder (${zOrder})")
        }
    }
    return obj
}

public class IntervalsVisibilities {
    IntervalsVisibilities(
        let ticks!: Bool = true,
        let seconds!: Bool = true,
        let minutes!: Bool = true,
        let hours!: Bool = true,
        let days!: Bool = true,
        let weeks!: Bool = true,
        let months!: Bool = true,
        let ranges!: Bool = true,
        let secondsFrom!: Int64 = 1,
        let secondsTo!: Int64 = 59,
        let minutesFrom!: Int64 = 1,
        let minutesTo!: Int64 = 59,
        let hoursFrom!: Int64 = 1,
        let hoursTo!: Int64 = 24,
        let daysFrom!: Int64 = 1,
        let daysTo!: Int64 = 366,
        let weeksFrom!: Int64 = 1,
        let weeksTo!: Int64 = 52,
        let monthsFrom!: Int64 = 1,
        let monthsTo!: Int64 = 12
    ) {}

    public func toJson(): JsonValue {
        let obj = JsonObject()
        obj.put("ticks", JsonBool(this.ticks))
        obj.put("seconds", JsonBool(this.seconds))
        obj.put("secondsFrom", JsonInt(this.secondsFrom))
        obj.put("secondsTo", JsonInt(this.secondsTo))
        obj.put("minutes", JsonBool(this.minutes))
        obj.put("minutesFrom", JsonInt(this.minutesFrom))
        obj.put("minutesTo", JsonInt(this.minutesTo))
        obj.put("hours", JsonBool(this.hours))
        obj.put("hoursFrom", JsonInt(this.hoursFrom))
        obj.put("hoursTo", JsonInt(this.hoursTo))
        obj.put("days", JsonBool(this.days))
        obj.put("daysFrom", JsonInt(this.daysFrom))
        obj.put("daysTo", JsonInt(this.daysTo))
        obj.put("weeks", JsonBool(this.weeks))
        obj.put("weeksFrom", JsonInt(this.weeksFrom))
        obj.put("weeksTo", JsonInt(this.weeksTo))
        obj.put("months", JsonBool(this.months))
        obj.put("monthsFrom", JsonInt(this.monthsFrom))
        obj.put("monthsTo", JsonInt(this.monthsTo))
        obj.put("ranges", JsonBool(this.ranges))
        return obj
    }
}

public class MiddleLine {
    MiddleLine(
        let showLine!: Bool = false,
        let lineWidth!: Int64 = 1,
        let lineColor!: String = "#000066",
        let lineStyle!: Int64 = 2
    ) {}

    public func toJson(): JsonValue {
        let obj = JsonObject()
        obj.put("showLine", JsonBool(this.showLine))
        obj.put("lineWidth", JsonInt(this.lineWidth))
        obj.put("lineColor", JsonString(this.lineColor))
        obj.put("lineStyle", JsonInt(this.lineStyle))
        return obj
    }
}

public class Rectangle {
    public static func getBi(title: String, direction: Direction, extendRight: Bool): Rectangle {
        let linewidth: Int64 = 1
        var linecolor: String = "rgba(76, 175, 80, 1)"
        var backgroundColor: String = "rgba(76, 175, 80, 0.2)"
        if (direction == Direction.Down) {
            linecolor = "rgba(178, 40, 51, 1)"
            backgroundColor = "rgba(178, 40, 51, 0.2)"
        }
        let middleline = MiddleLine(lineColor: linecolor, lineWidth: linewidth)
        let obj = Rectangle(text: "Bizs", title: title, color: linecolor, linewidth: linewidth,
            backgroundColor: backgroundColor, middleLine: middleline, extendRight: extendRight)
        return obj
    }

    public static func getDuan(title: String, direction: Direction, extendRight: Bool): Rectangle {
        let linewidth: Int64 = 2
        var linecolor: String = "rgba(76, 175, 80, 1)"
        var backgroundColor: String = "rgba(76, 175, 80, 0.2)"
        if (direction == Direction.Down) {
            linecolor = "rgba(178, 40, 51, 1)"
            backgroundColor = "rgba(178, 40, 51, 0.2)"
        }
        let middleline = MiddleLine(lineColor: linecolor, lineWidth: linewidth)
        let obj = Rectangle(text: "Duanzs", title: title, color: linecolor, linewidth: linewidth,
            backgroundColor: backgroundColor, middleLine: middleline, extendRight: extendRight)
        return obj
    }

    Rectangle(
        let color!: String = "#99CC99",
        let fillBackground!: Bool = true,
        let backgroundColor!: String = "rgba(156, 39, 176, 0.2)",
        let linewidth!: Int64 = 1,
        let transparency!: Int64 = 50,
        let showLabel!: Bool = false,
        let horzLabelsAlign!: String = "left",
        let vertLabelsAlign!: String = "bottom",
        let textColor!: String = "#9c27b0",
        let fontSize!: Int64 = 14,
        let bold!: Bool = false,
        let italic!: Bool = false,
        let extendLeft!: Bool = false,
        let extendRight!: Bool = false,
        let middleLine!: MiddleLine = MiddleLine(),
        let visible!: Bool = true,
        let frozen!: Bool = true,
        let title!: String = "Bi中枢-10",
        let text!: String = "Bizs",
        let intervalsVisibilities!: IntervalsVisibilities = IntervalsVisibilities()
    ) {}

    public func toJson(): JsonObject {
        let obj = JsonObject()
        obj.put("color", JsonString(this.color))
        obj.put("fillBackground", JsonBool(this.fillBackground))
        obj.put("backgroundColor", JsonString(this.backgroundColor))
        obj.put("linewidth", JsonInt(this.linewidth))
        obj.put("transparency", JsonInt(this.transparency))
        obj.put("showLabel", JsonBool(this.showLabel))
        obj.put("horzLabelsAlign", JsonString(this.horzLabelsAlign))
        obj.put("vertLabelsAlign", JsonString(this.vertLabelsAlign))
        obj.put("textColor", JsonString(this.textColor))
        obj.put("fontSize", JsonInt(this.fontSize))
        obj.put("bold", JsonBool(this.bold))
        obj.put("italic", JsonBool(this.italic))
        obj.put("extendLeft", JsonBool(this.extendLeft))
        obj.put("extendRight", JsonBool(this.extendRight))
        obj.put("middleLine", this.middleLine.toJson())
        obj.put("visible", JsonBool(this.visible))
        obj.put("frozen", JsonBool(this.frozen))
        obj.put("title", JsonString(this.title))
        obj.put("text", JsonString(this.text))
        obj.put("intervalsVisibilities", this.intervalsVisibilities.toJson())
        return obj
    }
}

public class TrendLine {
    public static func getBi(title: String): TrendLine {
        let obj = TrendLine(text: "bi", title: title, linecolor: "#CC62FF", linewidth: 2, linestyle: 0)
        return obj
    }

    public static func getDuan(title: String, linecolor!: String = "#F1C40F"): TrendLine {
        let obj = TrendLine(text: "duan", title: title, linecolor: linecolor, linewidth: 3, linestyle: 0)
        return obj
    }

    public static func getFeature(title: String, direction: Direction, linestyle!: Int64 = 2, text!: String = "feature"): TrendLine {
        var obj = TrendLine(text: text, title: title, linecolor: "#22FF22", linewidth: 2, linestyle: linestyle)
        if (direction == Direction.Up) {
            obj = TrendLine(text: text, title: title, linecolor: "#FF2222", linewidth: 2, linestyle: linestyle)
        }
        return obj
    }

    TrendLine(
        let linecolor!: String = "#22FF22",
        let linewidth!: Int64 = 2,
        let linestyle!: Int64 = 0,
        let extendLeft!: Bool = false,
        let extendRight!: Bool = false,
        let leftEnd!: Int64 = 0,
        let rightEnd!: Int64 = 0,
        let showLabel!: Bool = false,
        let horzLabelsAlign!: String = "center",
        let vertLabelsAlign!: String = "bottom",
        let textcolor!: String = "#2962FF",
        let fontsize!: Int64 = 14,
        let bold!: Bool = false,
        let italic!: Bool = false,
        let showMiddlePoint!: Bool = false,
        let showPriceLabels!: Bool = false,
        let showPriceRange!: Bool = false,
        let showPercentPriceRange!: Bool = false,
        let showPipsPriceRange!: Bool = false,
        let showBarsRange!: Bool = false,
        let showDateTimeRange!: Bool = false,
        let showDistance!: Bool = false,
        let showAngle!: Bool = false,
        let statsPosition!: Int64 = 2,
        let visible!: Bool = true,
        let frozen!: Bool = true,
        let title!: String = "特征序列",
        let text!: String = "feature",
        let intervalsVisibilities!: IntervalsVisibilities = IntervalsVisibilities()
    ) {}
    public func toJson(): JsonValue {
        let obj = JsonObject()
        obj.put("linecolor", JsonString(this.linecolor))
        obj.put("linewidth", JsonInt(this.linewidth))
        obj.put("linestyle", JsonInt(this.linestyle))
        obj.put("title", JsonString(this.title))
        obj.put("text", JsonString(this.text))
        /*
            obj.put("extendLeft", JsonBool(this.extendLeft))
            obj.put("extendRight", JsonBool(this.extendRight))
            obj.put("leftEnd", JsonInt(this.leftEnd))
            obj.put("rightEnd", JsonInt(this.rightEnd))
            obj.put("showLabel", JsonBool(this.showLabel))
            obj.put("horzLabelsAlign", JsonString(this.horzLabelsAlign))
            obj.put("vertLabelsAlign", JsonString(this.vertLabelsAlign))
            obj.put("textcolor", JsonString(this.textcolor))
            obj.put("fontsize", JsonInt(this.fontsize))
            obj.put("bold", JsonBool(this.bold))
            obj.put("italic", JsonBool(this.italic))
            obj.put("showMiddlePoint", JsonBool(this.showMiddlePoint))
            obj.put("showPriceLabels", JsonBool(this.showPriceLabels))
            obj.put("showPriceRange", JsonBool(this.showPriceRange))
            obj.put("showPercentPriceRange", JsonBool(this.showPercentPriceRange))
            obj.put("showPipsPriceRange", JsonBool(this.showPipsPriceRange))
            obj.put("showBarsRange", JsonBool(this.showBarsRange))
            obj.put("showDateTimeRange", JsonBool(this.showDateTimeRange))
            obj.put("showDistance", JsonBool(this.showDistance))
            obj.put("showAngle", JsonBool(this.showAngle))
            obj.put("statsPosition", JsonInt(this.statsPosition))
            obj.put("visible", JsonBool(this.visible))
            obj.put("frozen", JsonBool(this.frozen))
            obj.put("intervalsVisibilities", JsonObject(this.intervalsVisibilities.getFields()))
         */
        return obj
    }
}

public class Arrow {
    Arrow(
        let color!: String = "#CC2F3C",
        let arrowColor!: String = "#CC2F3C",
        let fontsize!: Int64 = 14,
        let bold!: Bool = false,
        let italic!: Bool = false,
        let showLabel!: Bool = true,
        let visible!: Bool = true,
        let frozen!: Bool = true,
        let title!: String = "BiTS",
        let text!: String = "Bi三卖1",
        let intervalsVisibilities!: IntervalsVisibilities = IntervalsVisibilities()
    ) {}
    public func toJson(): JsonValue {
        let obj = JsonObject()
        obj.put("color", JsonString(this.color))
        obj.put("title", JsonString(this.title))
        obj.put("text", JsonString(this.text))
        /*
        obj.put("arrowColor", JsonString(this.arrowColor))
        obj.put("fontsize", JsonInt(this.fontsize))
        obj.put("bold", JsonBool(this.bold))
        obj.put("italic", JsonBool(this.italic))
        obj.put("showLabel", JsonBool(this.showLabel))
        obj.put("visible", JsonBool(this.visible))
        obj.put("frozen", JsonBool(this.frozen))
        obj.put("intervalsVisibilities", this.intervalsVisibilities.toJson())
         */
        return obj
    }
}

public class TradingView {
    public static let IDS = HashSet<Int64>()
    public static var seed: UInt64 = 40320
    public static var ID: Int64 = Int64.Max
    public static func getID(): Int64 {
        while (true) {
            ID -= 1
            let b = IDS.put(ID)
            if (b) {
                return ID
            }
        }

        throw IllegalArgumentException()
    }

    public static func setSeed(): Unit {
        let f = File.openRead("/dev/urandom")
        let buffer = Array<Byte>(8, repeat: 0)
        try {
            f.read(buffer)
            TradingView.seed = UInt64.readBigEndian(buffer)
            println(colored("TV.seed=${TradingView.seed}", color: "red", attrs: "blink"))
        } catch (E: IllegalArgumentException) {
            println(E.message)
        } catch (e: FSException) {
            println(e.message)
        } finally {
            f.close()
        }
    }

    public static func getOptions(
        shape!: String = "trend_line",
        lock!: Bool = true,
        disableSelection!: Bool = true,
        disableSave!: Bool = true,
        disableUndo!: Bool = true,
        text!: String = "text"
    ): JsonObject {
        let obj = JsonObject()
        obj.put("shape", JsonString(shape))
        //obj.put("lock", JsonBool(lock))
        //obj.put("disableSelection", JsonBool(disableSelection))
        //obj.put("disableSave", JsonBool(disableSave))
        //obj.put("disableUndo", JsonBool(disableUndo))
        obj.put("text", JsonString(text))
        return obj
    }

    public static func send(ws: WebSocket, message: Array<Byte>): Unit {
        ws.write(TextWebFrame, message)
        //dp(String.fromUtf8(message))
    }

    public static func push(bar: RawBar, ws: ?WebSocket): Unit {
        let obj = JsonObject()
        let cmd = CMD.APPEND("RawBar").toString()
        obj.put("type", JsonString("realtime"))
        obj.put("cmd", JsonString(cmd))
        obj.put("timestamp", JsonString(bar.dt.toString()))
        obj.put("open", JsonFloat(bar.open))
        obj.put("high", JsonFloat(bar.high))
        obj.put("low", JsonFloat(bar.low))
        obj.put("close", JsonFloat(bar.close))
        obj.put("volume", JsonFloat(bar.volume))
        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(bar: NewBar, ws: ?WebSocket): Unit {
        let obj = JsonObject()
        let cmd = CMD.APPEND("NewBar").toString()
        obj.put("type", JsonString("realtime"))
        obj.put("cmd", JsonString(cmd))
        obj.put("timestamp", JsonString(bar.dt.toString()))
        obj.put("open", JsonFloat(bar.open))
        obj.put("high", JsonFloat(bar.high))
        obj.put("low", JsonFloat(bar.low))
        obj.put("close", JsonFloat(bar.close))
        obj.put("volume", JsonFloat(bar.volume))
        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(bsp: BSPoint, ws: ?WebSocket, command: CMD): Unit {
        let obj = JsonObject()
        var cmd = command.toString()
        if (command.toString() == "MODIFY(BSPoint)") {
            cmd = "REMOVE(BSPoint)"
        }

        let points = ArrayList<JsonValue>()
        let s = JsonObject()
        s.put("time", JsonInt(DateTime.dt2int(bsp.getDt())))
        s.put("price", JsonFloat(bsp.getPrice()))
        points.append(s)

        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))
        var shape_name = "arrow_up"
        var color = "#089981"
        if (bsp.isSell()) {
            shape_name = "arrow_down"
            color = "#CC2F3C"
        }

        if (bsp.getValid() == false) {
            color = "#FFFA50"
        }
        let title: String = match (bsp) {
            case BSPoint.BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => "${tp}${info}Buy"
            case BSPoint.SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => "${tp}${info}Sell"
        }
        let text = match (bsp) {
            case BSPoint.BUY(info, tp, dt, price, valid, creation_offset, fix_offset) => "${tp}${info}Buy, ${creation_offset}, ${valid}"
            case BSPoint.SELL(info, tp, dt, price, valid, creation_offset, fix_offset) => "${tp}${info}Sell, ${creation_offset}, ${valid}"
        }
        let options = CreateMultipointShapeOptions(shape: shape_name, text: "${command}")
        let properties = Arrow(color: color, text: text, title: title)
        obj.put("name", JsonString(shape_name))
        obj.put("id", JsonString(bsp.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())
        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(bi: Bi, ws: ?WebSocket, command: CMD): Unit {
        let obj = JsonObject()
        let cmd = command.toString()
        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))

        let points = ArrayList<JsonValue>()
        let s = JsonObject()
        s.put("time", JsonInt(DateTime.dt2int(bi.start.dt)))
        s.put("price", JsonFloat(bi.start.speck))
        points.append(s)
        let e = JsonObject()
        e.put("time", JsonInt(DateTime.dt2int(bi.elements[bi.elements.size - 1].dt)))
        e.put("price", JsonFloat(bi.end.speck))
        points.append(e)

        let options = CreateMultipointShapeOptions(shape: "trend_line", text: "")
        let properties = TrendLine.getBi("Bi-${bi.index}")

        obj.put("name", JsonString("trend_line"))
        obj.put("id", JsonString(bi.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())

        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(duan: Duan, ws: ?WebSocket, command: CMD): Unit {
        let obj = JsonObject()
        let cmd = command.toString()
        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))

        let points = ArrayList<JsonValue>()
        let s = JsonObject()
        s.put("time", JsonInt(DateTime.dt2int(duan.start.dt)))
        s.put("price", JsonFloat(duan.start.speck))
        points.append(s)
        let e = JsonObject()
        e.put("time", JsonInt(DateTime.dt2int(duan.end.dt)))
        e.put("price", JsonFloat(duan.end.speck))
        points.append(e)
        let linecolor: String = if (duan.stamp != "Duan") {
            "#2962FF"
        } else {
            "#F1C40F"
        }

        let options = CreateMultipointShapeOptions(shape: "trend_line", text: "")
        let properties = TrendLine.getDuan("Duan-${duan.index}", linecolor: linecolor)

        obj.put("name", JsonString("trend_line"))
        obj.put("id", JsonString(duan.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())

        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(feature: FeatureSequence, ws: ?WebSocket, command: CMD): Unit {
        let obj = JsonObject()
        let cmd = command.toString()
        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))

        let points = ArrayList<JsonValue>()
        let s = JsonObject()
        s.put("time", JsonInt(DateTime.dt2int(feature.start.dt)))
        s.put("price", JsonFloat(feature.start.speck))
        points.append(s)
        let e = JsonObject()
        e.put("time", JsonInt(DateTime.dt2int(feature.end.dt)))
        e.put("price", JsonFloat(feature.end.speck))
        points.append(e)

        let options = CreateMultipointShapeOptions(shape: "trend_line", text: "")
        let level: Int64 = if (feature.level == 0) {
            1
        } else if (feature.level == 1) {
            1
        } else if (feature.level == 2) {
            2
        } else {
            0
        }
        let properties = TrendLine.getFeature("特征序列", feature.direction, linestyle: level)

        obj.put("name", JsonString("trend_line"))
        obj.put("id", JsonString(feature.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())

        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(zs: ZhongShu, ws: ?WebSocket, command: CMD): Unit {
        let obj = JsonObject()
        let cmd = command.toString()
        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))

        match (command) {
            case CMD.APPEND(s) => "APPEND(${s})"
            case CMD.REMOVE(s) => "REMOVE(${s})"
            case CMD.MODIFY(s) => "MODIFY(${s})"
        }

        let points = ArrayList<JsonValue>()
        if (cmd.indexOf("REMOVE").isNone()) {
            let s = JsonObject()
            s.put("time", JsonInt(DateTime.dt2int(zs.start.dt)))
            s.put("price", JsonFloat(zs.zg))
            points.append(s)
            let e = JsonObject()
            e.put("time", JsonInt(DateTime.dt2int(zs.end.dt)))
            e.put("price", JsonFloat(zs.zd))
            points.append(e)
        }

        let options = CreateMultipointShapeOptions(shape: "rectangle", text: "zs")
        let properties = obj.put("name", JsonString("rectangle"))
        obj.put("id", JsonString(zs.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        if (zs.left.getOrThrow().stamp == "Bi") {
            obj.put("properties", Rectangle.getBi("Bi中枢-${zs.index}", zs.direction, zs.third.isNone()).toJson())
        } else {
            obj.put("properties", Rectangle.getDuan("Duan中枢-${zs.index}", zs.direction, zs.third.isNone()).toJson())
        }
        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }
}

main() {
    //let obj = BaseAnalyzer.readFromDatFile("./btcusd-300-1713295800-1715695500.dat")

    TradingView.setSeed()

    // 1. 构建 Server 实例
    let server = ServerBuilder().addr("0.0.0.0").port(8080).distributor(NaiveDistributor()) // 自定义分发器
        .build()
    // 2. 启动服务
    //server.logger.level = DEBUG
    server.serve()
}
