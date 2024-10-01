package chanlun

import std.unittest.testmacro.*
import std.binary.*
import std.math.{abs}
import std.math.MathExtension
import std.collection
import std.collection.{HashSet, ArrayList, enumerate, HashMap, any}
import std.time.*
import std.math
import std.fs.*
import net.http.*
import std.log.*
import std.convert.*
import std.ast.*
import std.collection.concurrent.*
import encoding.json.*
import std.random.Random
import std.console.*

public func dp(s: String): Unit {
    if (1 == 0) {
        println(s)
    }
}

public func str<T>(obj: T): String where T <: ToString {
    obj.toString()
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

extend<T> ArrayList<T> where T <: ToString {
    public func pop(index!: Int64 = -1): T {
        var i = index
        if (index < 0) {
            i = this.size - abs(index)
        }
        let obj = this.get(i)
        this.remove(i)
        return obj.getOrThrow()
    }

    public func appendObj(element: T): Unit {
        println("${element}")
        this.append(element)
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

    public func index(obj: Bi): Int64 {
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

    public func index(obj: Duan): Int64 {
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

    public func index(obj: Int64): Int64 {
        if (this.isEmpty()) {
            throw ChanException("列表为空")
        }

        for ((i, o) in enumerate(this.iterator())) {
            if (obj == (o as Int64).getOrThrow()) {
                return i
            }
        }
        throw ChanException("元素不在列表中")
    }
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

public enum BSPoint <: ToString & Equatable<BSPoint> {
    BUY(String) | SELL(String)

    public func toString(): String {
        match (this) {
            case BUY(s) => "BUY(${s})"
            case SELL(s) => "SELL(${s})"
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

public interface Pillar <: ToString {
    mut prop index: Int64
    prop high: Float64
    prop low: Float64
    prop volume: Float64
    prop direction: Direction
}

public func double_relation<T>(left: T, right: T): Direction where T <: Pillar {
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

public func triple_relation<T>(left: T, mid: T, right: T, use_right!: Bool = false): (Shape, (Direction, Direction)) where T <: Pillar {
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
    prop raws: ArrayList<RawBar>
    prop news: ArrayList<NewBar>
    prop fxs: ArrayList<FenXing>
    prop bis: ArrayList<Bi>
    prop duans: ArrayList<Duan>
    prop bi_zss: ArrayList<ZhongShu<Bi>>
    prop duan_zss: ArrayList<ZhongShu<Duan>>
    func update(obj: Any, cmd: CMD): Unit
}

public interface BaseInterface<T> <: ToString & HashableEquatable<T> {}

public interface BaseChanInterface<T> <: Pillar & BaseInterface<T> {
    func getFields(): HashMap<String, JsonValue>
}

public interface Bar <: ToString & Pillar {
    mut prop index: Int64
    prop open: Float64
    prop close: Float64
    prop high: Float64
    prop low: Float64
    prop volume: Float64
    prop direction: Direction
}

public class RawBar <: Bar & HashableEquatable<RawBar> & BigEndianOrder<RawBar> {
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

    public func toNewBar(pre: Option<NewBar>): NewBar {
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

public class NewBar <: Bar & HashableEquatable<NewBar> {
    public let dt: DateTime
    private var _index: Int64 = 0
    //private var _open: Float64 = 0.0
    //private var _close: Float64 = 0.0
    private var _high: Float64 = 0.0
    private var _low: Float64 = 0.0
    //private var _volume: Float64 = 0.0
    private var _direction: Direction = Direction.Unknow

    private var _shape: Shape = Shape.Unknow
    public var elements: ArrayList<RawBar>

    public var jump: Bool = false
    public var speck: Float64 = 0.0
    public var relation: Direction = Direction.Up // 与前一个NewBar 实际关系

    NewBar(dt!: DateTime, high!: Float64, low!: Float64, elements!: Array<RawBar>, pre!: Option<NewBar>) {
        this.dt = dt
        //this._open = open
        this._high = high
        this._low = low
        //this._close = close
        //this._volume = volume
        //this._index = index
        this._direction = Direction.Up

        this.elements = ArrayList<RawBar>(elements)
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

    public func merge(next_raw_bar: RawBar): Option<NewBar> {
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

public interface FenXingInterface<T> <: Pillar where T <: Bar {
    mut prop left: T
    mut prop mid: T
    mut prop right: T
    prop speck: Float64
    prop shape: Shape
}

public class FenXing <: ToString & FenXingInterface<NewBar> & HashableEquatable<FenXing> {
    private var _index: Int64 = 0
    private var _left: Option<NewBar> = None
    private var _mid: Option<NewBar> = None
    private var _right: Option<NewBar> = None
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
        "FenXing(${this.left.hashCode()}, ${this.mid.hashCode()}, ${this.right.hashCode()})".hashCode()
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

public interface Line {
    prop start: FenXing
    mut prop end: FenXing
}

public class Bi <: Pillar & HashableEquatable<Bi> & Line {
    public static let BI_JUMP: Bool = true
    public static let BI_LENGTH: Int64 = 5
    public static var BI_EQUAL: Bool = true
    public static let BI_FENGXING: Bool = false

    private var _index: Int64 = 0
    private var _direction: Direction = Direction.Unknow

    private let _start: FenXing
    private var _end: FenXing
    public var pre: Option<Bi>

    public var elements: ArrayList<NewBar>
    public var fake: Bool = false
    private let _id: Int64

    Bi(pre!: Option<Bi>, start!: FenXing, end!: FenXing, elements!: Array<NewBar>, fake!: Bool = false) {
        this._id = TradingView.getID()
        this.pre = pre
        this._start = start
        this._end = end
        this.elements = ArrayList(elements)
        this.fake = fake

        match ((start.shape, end.shape)) {
            case (Shape.G, Shape.D) => this._direction = Direction.Down

            case (Shape.D, Shape.G) => this._direction = Direction.Up

            case _ => throw ChanException("Bi.start.shape: ${start.shape}, ${end.shape}")
        }

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

    public prop high: Float64 {
        get() {
            //this._high
            if (this.direction == Direction.Down) {
                this.start.speck
            } else {
                this.end.speck
            }
        }
    }

    public prop low: Float64 {
        get() {
            //this._low
            if (this.direction == Direction.Up) {
                this.start.speck
            } else {
                this.end.speck
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

    public prop direction: Direction {
        get() {
            this._direction
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
            var flag = false
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

    public prop real_low: NewBar {
        get() {
            if (this.elements.isEmpty()) {
                throw ChanException("Bi.real_low: 列表为空")
            }
            if (Bi.BI_EQUAL) {
                var lows: ArrayList<NewBar> = ArrayList([this.elements[0]])
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
                var highs: ArrayList<NewBar> = ArrayList([this.elements[0]])
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
            var start = this.start.mid
            if (Bi.BI_FENGXING) {
                var start = this.start
            }
            let end = this.end
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

    public static func calc_length(elements: ArrayList<NewBar>): Int64 {
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

    public static func analyzer(fx: FenXing, fxs: ArrayList<FenXing>, bis: ArrayList<Bi>, cklines: ArrayList<NewBar>,
        _from: String, level: UInt16, observer: Observer): Unit {
        if (fxs.isEmpty()) {
            if (fx.shape == Shape.G || fx.shape == Shape.D) {
                fxs.append(fx)
            }
            return
        }

        func __pop(bis: ArrayList<Bi>, fx: FenXing, _from: String): Option<Bi> {
            let size = bis.size
            var bi: Option<Bi> = Option<Bi>.None
            if (size > 0) {
                if (bis[size - 1].end == fx) {
                    bi = Some(bis.pop())
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

        func __append(bis: ArrayList<Bi>, bi: Bi, _from: String): Unit {
            let size = bis.size
            if (size > 0 && !refEq(bis[size - 1].end, bi.start)) {
                throw ChanException("笔连续性错误!!!")
            }
            var index: Int64 = 0
            var pre: Option<Bi> = None
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
                        var tmp: Option<NewBar> = None
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
                        var tmp: Option<NewBar> = None
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
                        var tmp: Option<NewBar> = None
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
                        var tmp: Option<NewBar> = None
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

    public static func analysis_one(cklines: ArrayList<NewBar>, observer: Observer): (Option<FenXing>, Option<Bi>) {
        if (cklines.size > 2) {
            var bis: ArrayList<Bi> = ArrayList<Bi>()
            var fxs: ArrayList<FenXing> = ArrayList<FenXing>()
            var fx: Option<FenXing> = None
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

public class FeatureSequence<T> <: HashableEquatable<FeatureSequence<T>> & Line & Pillar where T <: ToString & HashableEquatable<T> & Line & Pillar {
    public var elements: HashSet<T>
    private let _id: Int64
    private var _direction: Direction = Direction.Unknow

    //public var direction: Direction // 特征序列方向为线段方向， 处理时需要注意！！！

    FeatureSequence(elements: Array<T>, direction: Direction) {
        this._id = TradingView.getID()
        this.elements = HashSet<T>(elements)
        this._direction = direction
        for (obj in elements) {
            if (direction == obj.direction) {
                throw ChanException("FeatureSequence, 方向相同")
            }
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

    public func hashCode(): Int64 {
        //"FeatureSequence(${this.direction}, ${this.elements})".hashCode()
        this._id
    }

    public operator override func ==(other: FeatureSequence<T>): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: FeatureSequence<T>): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "FeatureSequence(${this.direction}, ${this.elements})"
    }

    public func update(): Unit {
    }

    public func add(obj: T, _from: String): Bool {
        if (obj.direction == this._direction) {
            throw ChanException("方向不匹配 ${this.direction} ${obj.direction} ")
        }
        return this.elements.put(obj)
    }

    public func romove(obj: T, _from: String): Bool {
        if (obj.direction == this._direction) {
            throw ChanException("方向不匹配")
        }
        return this.elements.remove(obj)
    }

    public func copy(other: FeatureSequence<T>): FeatureSequence<T> {
        if (this._direction != other.direction) {
            throw ChanException()
        }
        this.elements = other.elements
        // self.notify_observer(cmd=FeatureSequence.CMD_MODIFY, obj=self)
        return this
    }

    public static func analyzer<T>(objs: ArrayList<T>, direction: Direction, _from: String): ArrayList<FeatureSequence<T>> where T <: ToString & HashableEquatable<T> & Line & Pillar {
        var result = ArrayList<FeatureSequence<T>>()
        for (obj in objs) {
            if (obj.direction == direction) {
                continue
            }

            if (result.size == 0) {
                result.append(FeatureSequence<T>([obj], direction))
            } else {
                let last = result[result.size - 1]
                if (double_relation(last, obj) == Direction.Left) {
                    last.add(obj, _from)
                } else {
                    result.append(FeatureSequence<T>([obj], direction))
                }
            }
        }
        return result
    }
}

public class Duan <: ToString & Pillar & HashableEquatable<Duan> & Line {
    public var pre: Option<Duan>
    private var _start: FenXing
    private var _end: FenXing
    public var elements: ArrayList<Bi>

    private var _index: Int64 = 0
    private var _direction: Direction

    public var done: Bool = false
    public var jump: Bool = false

    private var features: Array<Option<FeatureSequence<Bi>>> = [None, None, None]
    private let _id: Int64

    Duan(pre: Option<Duan>, start: FenXing, end: FenXing, elements: ArrayList<Bi>) {
        this._id = TradingView.getID()
        this.pre = pre
        this._start = start
        this._end = end
        this.elements = elements
        if (start.shape == Shape.G) {
            this._direction = Direction.Down
        } else {
            this._direction = Direction.Up
        }

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
            //this._high
            if (this.direction == Direction.Down) {
                this.start.speck
            } else {
                this.end.speck
            }
        }
    }

    public prop low: Float64 {
        get() {
            //this._low
            if (this.direction == Direction.Up) {
                this.start.speck
            } else {
                this.end.speck
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

    public prop direction: Direction {
        get() {
            this._direction
        }
    }

    public prop lmr: (Bool, Bool, Bool) {
        get() {
            (this.features[0].isSome(), this.features[1].isSome(), this.features[2].isSome())
        }
    }

    public prop state: String {
        get() {
            if (let Some(pre) <- this.pre) {
                if (let Some(mid) <- pre.mid) {
                } else {
                    return "None"
                }
                let relation = double_relation(pre.left.getOrThrow(), pre.mid.getOrThrow())
                if (relation == Direction.JumpUp && this.direction == Direction.Up) {
                    return "老阳"
                } else if (relation == Direction.JumpDown && this.direction == Direction.Down) {
                    return "老阴"
                } else {
                    if (this.direction == Direction.Up) {
                        return "小阳"
                    } else {
                        return "少阴"
                    }
                }
            } else {
                if (this.direction == Direction.Up) {
                    return "小阳"
                } else {
                    return "少阴"
                }
            }
        }
    }

    private func __feature_setter(offset: Int64, feature: Option<FeatureSequence<Bi>>): Unit {
        if (feature.isNone()) {
            if (let Some(obj) <- feature) {
                // notify
            }
            this.features[offset] = feature
            return
        }
        if (feature.getOrThrow().direction != this.direction) {
            throw ChanException("特征序列方向不匹配")
        }
        if (this.features[offset].isNone()) {
            //feature.notify_observer(cmd=FeatureSequence.CMD_APPEND, obj=feature)
            this.features[offset] = feature
        } else {
            this.features[offset].getOrThrow().copy(feature.getOrThrow())
            //self._features[offset].notify_observer(cmd=FeatureSequence.CMD_MODIFY, obj=self._features[offset])
        }
    }

    public mut prop left: Option<FeatureSequence<Bi>> {
        get() {
            return this.features[0]
        }
        set(feature) {
            this.__feature_setter(0, feature)
        }
    }

    public mut prop mid: Option<FeatureSequence<Bi>> {
        get() {
            return this.features[1]
        }
        set(feature) {
            this.__feature_setter(1, feature)
        }
    }

    public mut prop right: Option<FeatureSequence<Bi>> {
        get() {
            return this.features[2]
        }
        set(feature) {
            this.__feature_setter(2, feature)
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
            if (fx == this._end) {
                return
            }
            this._end = fx
        }
        // this.notify_observer(cmd=Duan.CMD_MODIFY, obj=self)

    }

    public func get_elements(): ArrayList<Bi> {
        var elements = ArrayList<Bi>([])
        for (obj in this.elements) {
            elements.append(obj)
            if (obj.end == this.end) {
                break
            }
        }
        return elements
    }

    public func append_element(bi: Bi, observer: Observer): Option<ArrayList<Bi>> {
        if (this.elements[this.elements.size - 1].end == bi.start) {
            this.elements.append(bi)
            if (this.direction == bi.direction) {
                if (let Some(mid) <- this.mid) {
                    if (this.direction == Direction.Up) {
                        if (this.high < bi.high) {
                            this.end = bi.end
                        } else {
                            this.end = mid.start
                        }
                    } else {
                        if (this.low > bi.low) {
                            this.end = bi.end
                        } else {
                            this.end = mid.start
                        }
                    }
                } else {
                    this.end = bi.end
                }
                if (observer.duan_zss.size > 0) {
                    observer.update(observer.duan_zss[observer.duan_zss.size - 1], CMD.MODIFY("ZhongShu<Duan>"))
                }
            } else {
                (this.left, this.mid, this.right) = this.get_features()
                if (this.right.isSome()) {
                    return Some(this.set_done(this.mid.getOrThrow().start))
                }
            }
            return None
        } else {
            throw ChanException("线段添加元素时，元素不连续, ${this.elements[this.elements.size-1]}, ${bi}")
        }
    }

    public func pop_element(bi: Bi): Bool {
        if (this.elements[this.elements.size - 1] == bi) {
            this.elements.pop()
            return true
        }
        throw ChanException("线段弹出元素时，元素不匹配")
    }

    public func get_features(): (Option<FeatureSequence<Bi>>, Option<FeatureSequence<Bi>>, Option<FeatureSequence<Bi>>) {
        let features = FeatureSequence<Bi>.analyzer<Bi>(this.elements, this.direction, "tmp")
        if (features.size == 0) {
            return (None, None, None)
        }

        if (features.size == 1) {
            return (Some(features[0]), None, None)
        }

        if (features.size == 2) {
            return (Some(features[0]), Some(features[1]), None)
        }

        if (features.size >= 3) {
            let relation = double_relation(features[features.size - 2], features[features.size - 1])
            if (this.direction == Direction.Up) {
                if (relation == Direction.JumpDown || relation == Direction.Down) {
                    return (Some(features[features.size - 3]), Some(features[features.size - 2]), Some(
                            features[features.size - 1]))
                } else {
                    return (Some(features[features.size - 2]), Some(features[features.size - 1]), None)
                }
            } else {
                if (relation == Direction.JumpUp || relation == Direction.Up) {
                    return (Some(features[features.size - 3]), Some(features[features.size - 2]), Some(
                            features[features.size - 1]))
                } else {
                    return (Some(features[features.size - 2]), Some(features[features.size - 1]), None)
                }
            }
        }

        return (None, None, None)
    }

    public func set_done(fx: FenXing): ArrayList<Bi> {
        (this.left, this.mid, this.right) = this.get_features()
        if (fx != this.mid.getOrThrow().start) {
            throw ChanException()
        }

        let elements = ArrayList<Bi>([])
        for (obj in this.elements) {
            if (elements.size > 0) {
                elements.append(obj)
            }

            if (obj.start == fx) {
                elements.append(obj)
            }
        }

        this.end = fx
        this.done = true
        let relation = double_relation(this.left.getOrThrow(), this.mid.getOrThrow())
        this.jump = relation == Direction.JumpDown || relation == Direction.JumpUp
        return elements
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

    public static func analyzer_pop(bi: Bi, xds: ArrayList<Duan>, level: UInt16, _from: String, observer: Observer): Unit {
        let cmd = "Duan.POP"

        func __pop(xds: ArrayList<Duan>, duan: Duan, _from: String): Unit {
            if (xds.size == 0) {
                return
            }
            if (xds[xds.size - 1] != duan) {
                throw ChanException()
            }

            //let tmp = xds[xds.size - 1]
            xds.remove(xds.size - 1)

            if (_from == "analyzer") {
                //dp("Duan.pop, level: ${level}, pop ${duan}")
                observer.update(duan, CMD.REMOVE("Duan"))
            }

            //this._zs_analyzer_pop<Duan>(duan, this.duan_zss, level, _from)
        }

        let duan: Duan = xds[xds.size - 1]
        let state: String = duan.state
        var pre: Option<Duan> = duan.pre
        if (pre.isNone() && xds.size > 1) {
            if (xds[xds.size - 2].index + 1 != duan.index) {
                throw ChanException()
            }
            pre = Some(xds[xds.size - 2])
        }
        let lmr = duan.lmr
        dp("${cmd}, ${level}, ${state}, (${lmr[0]} ${lmr[1]} ${lmr[2]}), ${duan} ${bi}")

        duan.pop_element(bi)
        if (let Some(last) <- pre) {
            if ((last.right.isSome() && (last.right.getOrThrow().elements |> any {line: Bi => line == bi})) || (last.
                right.isNone() && (last.left.getOrThrow().elements |> any {line: Bi => line == bi}))) {
                __pop(xds, duan, _from)
                last.pop_element(bi)
                // last.features = [last.left, last.mid, None]
                last.right = None
                return
            }
        }

        if (duan.elements.size > 0) {
            (duan.left, duan.mid, duan.right) = duan.get_features()
        } else {
            __pop(xds, duan, _from)
        }
    }

    public static func analyzer_push(bi: Bi, xds: ArrayList<Duan>, level: UInt16, _from: String, observer: Observer): Unit {
        let cmd = "Duan.PUSH"
        func __append(xds: ArrayList<Duan>, duan: Duan, _from: String): Unit {
            if (xds.size > 0 && xds[xds.size - 1].end != duan.start) {
                throw ChanException("线段连续性错误")
            }

            var index = 0
            var pre: Option<Duan> = None
            if (xds.size > 0) {
                index = xds[xds.size - 1].index + 1
                pre = Some(xds[xds.size - 1])
            }

            duan.index = index
            duan.pre = pre
            xds.append(duan)

            if (_from == "analyzer") {
                //dp("Duan.append, level: ${level}, pop ${duan}")
                observer.update(duan, CMD.APPEND("Duan"))
            }

            //this._zs_analyzer_push<Duan>(duan, this.duan_zss, xds, level, _from)
        }

        func __pop(xds: ArrayList<Duan>, duan: Duan, _from: String): Unit {
            if (xds.size == 0) {
                return
            }
            if (xds[xds.size - 1] != duan) {
                throw ChanException()
            }
            //let tmp = xds[xds.size - 1]
            xds.remove(xds.size - 1)

            if (_from == "analyzer") {
                observer.update(duan, CMD.REMOVE("Duan"))
            }

            //this._zs_analyzer_pop<Duan>(duan, this.duan_zss, level, _from)
        }

        var new = Duan(None, bi.start, bi.end, ArrayList<Bi>([bi]))
        if (xds.isEmpty()) {
            __append(xds, new, _from)
            return
        }

        var duan = xds[xds.size - 1]
        var state = duan.state
        let lmr = duan.lmr
        dp("${cmd}, ${level}, ${state}, (${lmr[0]} ${lmr[1]} ${lmr[2]}), ${duan} ${bi}")

        if (duan.direction == bi.direction) {
            // 与线段方向相同时修改线段终点
            duan.append_element(bi, observer)
            observer.update(duan, CMD.MODIFY("Duan"))
            return
        }

        if (xds.size == 1) {
            if ((duan.direction == Direction.Up && bi.low < duan.start.speck && duan.elements.size == 1) || (duan.
                direction == Direction.Down && bi.high > duan.start.speck && duan.elements.size == 1)) {
                new = Duan(None, bi.start, bi.end, ArrayList<Bi>([bi]))
                __pop(xds, duan, _from)
                __append(xds, new, _from)
                return
            }
        }

        let elements = duan.append_element(bi, observer)

        if (let Some(elements) <- elements) {
            // 分型成型
            observer.update(duan, CMD.MODIFY("Duan"))
            new = Duan(duan, elements[0].start, elements[elements.size - 1].end, elements)
            (new.left, new.mid, new.right) = new.get_features()
            __append(xds, new, _from)
            if (duan.jump) {
                new.pre = Some(duan)
            }
            if (duan.direction == Direction.Up) {
                dp("${cmd}, ${level}, 顶分型终结，缺口: ${duan.jump}")
            } else {
                dp("${cmd}, ${level}, 底分型终结，缺口: ${duan.jump}")
            }
        }
    }
}

public class ZhongShu<T> <: ToString & Pillar & HashableEquatable<ZhongShu<T>> & Line where T <: ToString & Pillar & HashableEquatable<T> & Line {
    private var _index: Int64 = 0
    private let _direction: Direction

    public var elements: ArrayList<T> = ArrayList<T>()
    public var third: Option<T> = Option<T>.None
    private let _id: Int64

    init(element: T) {
        this._id = TradingView.getID()
        this.elements = ArrayList<T>([element])
        this._direction = !element.direction
    }

    init(elements: Array<T>) {
        this._id = TradingView.getID()
        if (elements.size < 3) {
            throw ChanException("ZhongShu init elements size < 3")
        }
        //let relation = double_relation(elements[0], elements[2])

        this.elements = ArrayList<T>(elements)
        this._direction = elements[1].direction
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

    public prop left: Option<T> {
        get() {
            this.elements.get(0)
        }
    }

    public prop mid: Option<T> {
        get() {
            this.elements.get(1)
        }
    }

    public prop right: Option<T> {
        get() {
            this.elements.get(2)
        }
    }

    public prop last_element: Option<T> {
        get() {
            if (this.elements.size > 0) {
                return Some(this.elements[this.elements.size - 1])
            } else {
                return None
            }
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

    public func hashCode(): Int64 {
        //"ZhongShu(${this.index}, ${this.third}, ${this.direction}, ${this.elements})".hashCode()
        this._id
    }

    public operator override func ==(other: ZhongShu<T>): Bool {
        return refEq(this, other)
    }

    public operator override func !=(other: ZhongShu<T>): Bool {
        return !(this == other)
    }

    public func toString(): String {
        "ZhongShu(index:${this.index}, third:${this.third.isSome()}, ${this.direction}, zg:${this.zg}, zd:${this.zd}, elements.size=${this.elements.size})"
    }

    public func check(): Bool {
        let relation = double_relation(this.left.getOrThrow(), this.right.getOrThrow())
        relation == Direction.Down || relation == Direction.Up || relation == Direction.Left || relation == Direction.
            Right
    }

    public func isEmpty(): Bool {
        this.elements.isEmpty()
    }

    public func pop_element(obj: T, _from: String): Unit {
        if (let Some(third) <- this.third) {
            if (third == obj) {
                this.third = None
                return
            }
            throw ChanException()
        }

        let last = this.elements[this.elements.size - 1]
        if (last != obj) {
            println("不同 ${last} ${obj}")
            return
        }
        let size = this.elements.size
        this.elements.remove(this.elements.size - 1)
    }

    public func append_element(obj: T, _from: String): Unit {
        let size = this.elements.size
        if (size == 0) {
            this.elements.append(obj)
            return
        }

        if (this.elements[size - 1].index + 1 != obj.index) {
            throw ChanException("ZhongShu append_element index 不连贯")
        }

        if (size == 1) {
            this.elements.append(obj)
        } else if (size == 2) {
            let relation = double_relation(this.elements[0], obj)
            if (relation == Direction.Up || relation == Direction.Down || relation == Direction.Left || relation ==
                Direction.Right) {
                this.elements.append(obj)
            } else if (relation == Direction.Unknow) {
                throw ChanException()
            } else {
                this.elements.remove(0)
                this.elements.append(obj)
            }
        } else {
            let relation = double_relation(this, obj)
            if (relation == Direction.Up || relation == Direction.Down || relation == Direction.Left || relation ==
                Direction.Right) {
                let last = this.last_element.getOrThrow()
                if (last.end == obj.start) {
                    this.elements.append(obj)
                } else {
                    throw ChanException("中枢无法添加元素")
                }
            } else if (relation == Direction.JumpUp || relation == Direction.JumpDown) {
                if (this.third.isSome()) {
                    throw ChanException("ZhongShu third is not None ${this.third}")
                } else {
                    this.third = Some(obj)
                }
            } else {
                throw ChanException("ZhongShu relation")
            }
        }
    }

    public static func analyzer_pop<T>(obj: T, zss: ArrayList<ZhongShu<T>>, level: UInt16, _from: String,
        observer: Observer): Unit where T <: ToString & Pillar & HashableEquatable<T> & Line & Pillar {
        let cmd = "ZhongShu.POP"

        func _pop(zss: ArrayList<ZhongShu<T>>, zs: ZhongShu<T>, _from: String): Unit {
            if (zss.size > 0) {
                if (zss[zss.size - 1] == zs) {
                    zss.remove(zss.size - 1)
                    if (_from == "analyzer") {
                        if (obj is Bi) {
                            observer.update(zs, CMD.REMOVE("ZhongShu<Bi>"))
                        }
                        if (obj is Duan) {
                            observer.update(zs, CMD.REMOVE("ZhongShu<Duan>"))
                        }
                    }
                } else {
                    throw ChanException()
                }
                println("${cmd}, ${obj}")
            }
        }

        if (zss.size > 0) {
            println("${cmd}, zss.size=${zss.size}, ${obj}")
            let last = zss[zss.size - 1]
            if (last.third.isSome()) {
                if (last.third.getOrThrow() == obj) {
                    last.third = None
                    return
                }
            }
            last.pop_element(obj, _from)

            if (last.elements.size == 0) {
                _pop(zss, last, _from)
                if (zss.size > 0) {
                    let last = zss[zss.size - 1]
                    if (last.third.getOrThrow() == obj) {
                        last.third = None
                        if (obj is Bi) {
                            observer.update(last, CMD.MODIFY("ZhongShu<Bi>"))
                        }
                        if (obj is Duan) {
                            observer.update(last, CMD.MODIFY("ZhongShu<Duan>"))
                        }
                    }
                }
            } else {
                if (obj is Bi) {
                    observer.update(last, CMD.MODIFY("ZhongShu<Bi>"))
                }
                if (obj is Duan) {
                    observer.update(last, CMD.MODIFY("ZhongShu<Duan>"))
                }
            }
        }
    }

    public static func analyzer_push<T>(obj: T, zss: ArrayList<ZhongShu<T>>, objs: ArrayList<T>, level: UInt16,
        _from: String, observer: Observer): Unit where T <: ToString & Pillar & HashableEquatable<T> & Line {
        let cmd = "ZhongShu.PUSH"

        func _append(zss: ArrayList<ZhongShu<T>>, zs: ZhongShu<T>, _from: String): Unit {
            var index: Int64 = 0
            if (zss.size > 0) {
                index = zss[zss.size - 1].index + 1
            }
            zs.index = index
            zss.append(zs)
            if (obj is Bi) {
                observer.update(zs, CMD.APPEND("ZhongShu<Bi>"))
            }
            if (obj is Duan) {
                observer.update(zs, CMD.APPEND("ZhongShu<Duan>"))
            }

            println("${cmd}, append")
        }
        println("${cmd}, zss.size=${zss.size}, ${obj}")

        if (zss.isEmpty()) {
            let new = ZhongShu<T>(obj)
            _append(zss, new, _from)
        } else {
            let last = zss[zss.size - 1]
            if (last.third.isSome()) {
                let new = ZhongShu<T>(obj)
                _append(zss, new, _from)
                return
            } else {
                last.append_element(obj, _from)
                if (obj is Bi) {
                    observer.update(last, CMD.MODIFY("ZhongShu<Bi>"))
                }
                if (obj is Duan) {
                    observer.update(last, CMD.MODIFY("ZhongShu<Duan>"))
                }
                if (last.third.isSome()) {
                    let new = ZhongShu<T>(obj)
                    _append(zss, new, _from)
                    return
                }
            }
        }
    }

    public static func analyzer<T>(elements: ArrayList<T>, observer: Observer): (Bool, ArrayList<ZhongShu<T>>) where T <: ToString & Pillar & HashableEquatable<T> & Line & Pillar {
        let zss = ArrayList<ZhongShu<T>>()
        if (elements.size < 3) {
            return (false, zss)
        }

        for (obj in elements) {
            ZhongShu<T>.analyzer_push(obj, zss, elements, 0, "tmp", observer)
        }
        return (zss.size > 0, zss)
    }
}

class BaseAnalyzer <: Observer {
    public var _symbol: String
    public var _freq: UInt32
    public var _raws: ArrayList<RawBar> = ArrayList<RawBar>()
    public var _news: ArrayList<NewBar> = ArrayList<NewBar>()
    public var _fxs: ArrayList<FenXing> = ArrayList<FenXing>()
    public var _bis: ArrayList<Bi> = ArrayList<Bi>()
    public var _duans: ArrayList<Duan> = ArrayList<Duan>()
    public var _bi_zss: ArrayList<ZhongShu<Bi>> = ArrayList<ZhongShu<Bi>>()
    public var _duan_zss: ArrayList<ZhongShu<Duan>> = ArrayList<ZhongShu<Duan>>()
    public var ws: Option<WebSocket> = None

    public static func fromData(symbol: String, freq: UInt32, buffer: Array<Byte>, ws!: Option<WebSocket> = None): BaseAnalyzer {
        var obj = BaseAnalyzer(symbol, freq, ws: ws)
        let size = 48 // struct.calcsize(">6d")

        for (i in 0..buffer.size / size) {
            //for (i in 200..500) {
            let bar = RawBar.readBigEndian(buffer[i * size..(i + 1) * size])
            obj.push(bar)
        }
        return obj
    }

    public static func readFromDatFile(path: String, ws!: Option<WebSocket> = None): BaseAnalyzer {
        let filename = Path(path).fileName.getOrThrow()
        let tmp = filename.split("-", 3)
        let symbol = tmp[0]
        let freq: UInt32 = UInt32.parse(tmp[1])
        let buffer = File.readFrom(path)
        return BaseAnalyzer.fromData(symbol, freq, buffer, ws: ws)
    }

    BaseAnalyzer(symbol: String, freq: UInt32, ws!: Option<WebSocket> = None) {
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
    public prop raws: ArrayList<RawBar> {
        get() {
            this._raws
        }
    }
    public prop news: ArrayList<NewBar> {
        get() {
            this._news
        }
    }
    public prop fxs: ArrayList<FenXing> {
        get() {
            this._fxs
        }
    }
    public prop bis: ArrayList<Bi> {
        get() {
            this._bis
        }
    }
    public prop duans: ArrayList<Duan> {
        get() {
            this._duans
        }
    }
    public prop bi_zss: ArrayList<ZhongShu<Bi>> {
        get() {
            this._bi_zss
        }
    }
    public prop duan_zss: ArrayList<ZhongShu<Duan>> {
        get() {
            this._duan_zss
        }
    }

    public func update(o: Any, cmd: CMD): Unit {
        let _from = "analyzer"
        match (cmd) {
            case CMD.APPEND(name) => if (name == "RawBar") {
                let obj = (o as RawBar).getOrThrow()
            //TradingView.push(obj, this.ws)
            } else if (name == "NewBar") {
                let obj = (o as NewBar).getOrThrow()
                TradingView.push(obj, this.ws)
            } else if (name == "Bi") {
                let obj = (o as Bi).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                ZhongShu<Bi>.analyzer_push(obj, this.bi_zss, this.bis, 0, _from, this)
                Duan.analyzer_push(obj, this.duans, 0, _from, this)
            } else if (name == "Duan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                ZhongShu<Duan>.analyzer_push(obj, this.duan_zss, this.duans, 0, _from, this)
            } else if (name == "ZhongShu<Bi>") {
                let obj = (o as ZhongShu<Bi>).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Duan>") {
                let obj = (o as ZhongShu<Duan>).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else {
                println("unknow : ${cmd}")
            }

            case CMD.REMOVE(name) => if (name == "RawBar") {
                let obj = (o as RawBar).getOrThrow()
            } else if (name == "NewBar") {
                let obj = (o as NewBar).getOrThrow()
            } else if (name == "Bi") {
                let obj = (o as Bi).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                ZhongShu<Bi>.analyzer_pop(obj, this.bi_zss, 0, _from, this)
                Duan.analyzer_pop(obj, this.duans, 0, _from, this)
            } else if (name == "Duan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
                ZhongShu<Duan>.analyzer_pop(obj, this.duan_zss, 0, _from, this)
            } else if (name == "ZhongShu<Bi>") {
                let obj = (o as ZhongShu<Bi>).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Duan>") {
                let obj = (o as ZhongShu<Duan>).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else {
                println("unknow : ${cmd}")
            }

            case CMD.MODIFY(name) => if (name == "RawBar") {
                let obj = (o as RawBar).getOrThrow()
            } else if (name == "NewBar") {
                let obj = (o as NewBar).getOrThrow()
                TradingView.push(obj, this.ws)
            } else if (name == "Bi") {
                let obj = (o as Bi).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "Duan") {
                let obj = (o as Duan).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Bi>") {
                let obj = (o as ZhongShu<Bi>).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
            } else if (name == "ZhongShu<Duan>") {
                let obj = (o as ZhongShu<Duan>).getOrThrow()
                TradingView.push(obj, this.ws, cmd)
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
                sleep(Duration.millisecond * 30)
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
}

///

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
                                "./btcusd-300-1713295800-1715695500.dat",
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

public class TradingView {
    public static let IDS = HashSet<Int64>()
    public static var seed: UInt64 = 40320

    public static func getID(): Int64 {
        let m: Random = Random(TradingView.seed)

        while (true) {
            let i: Int64 = m.nextInt64()
            if (IDS.put(i)) {
                return i
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
            println("TradingView.seed=${TradingView.seed}")
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

    public static func push(bar: RawBar, ws: Option<WebSocket>): Unit {
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

    public static func push(bar: NewBar, ws: Option<WebSocket>): Unit {
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

    public static func push(bi: Bi, ws: Option<WebSocket>, command: CMD): Unit {
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

    public static func push(duan: Duan, ws: Option<WebSocket>, command: CMD): Unit {
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

        let options = CreateMultipointShapeOptions(shape: "trend_line", text: "")
        let properties = TrendLine.getDuan("Duan-${duan.index}")

        obj.put("name", JsonString("trend_line"))
        obj.put("id", JsonString(duan.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())

        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(feature: FeatureSequence<Bi>, ws: Option<WebSocket>, command: CMD): Unit {
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
        let properties = TrendLine.getFeature("特征序列", feature.direction)

        obj.put("name", JsonString("trend_line"))
        obj.put("id", JsonString(feature.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())

        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(zs: ZhongShu<Bi>, ws: Option<WebSocket>, command: CMD): Unit {
        let obj = JsonObject()
        let cmd = command.toString()
        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))

        let points = ArrayList<JsonValue>()
        if (cmd != "REMOVE(ZhongShu<Bi>)") {
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
        let properties = Rectangle.getBi("Bi中枢-${zs.index}", zs.direction)

        obj.put("name", JsonString("rectangle"))
        obj.put("id", JsonString(zs.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())
        if (let Some(ss) <- ws) {
            TradingView.send(ss, obj.toString().toArray())
        }
    }

    public static func push(zs: ZhongShu<Duan>, ws: Option<WebSocket>, command: CMD): Unit {
        let obj = JsonObject()
        let cmd = command.toString()
        obj.put("type", JsonString("shape"))
        obj.put("cmd", JsonString(cmd))

        let points = ArrayList<JsonValue>()
        if (cmd != "REMOVE(ZhongShu<Duan>)") {
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
        let properties = Rectangle.getDuan("Duan中枢-${zs.index}", zs.direction)

        obj.put("name", JsonString("rectangle"))
        obj.put("id", JsonString(zs.hashCode().toString()))
        obj.put("points", JsonArray(points))
        obj.put("options", options)
        obj.put("properties", properties.toJson())
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

public func CreateMultipointShapeOptions(
    shape!: String = "trend_line",
    lock!: Bool = true,
    disableSelection!: Bool = true,
    disableSave!: Bool = true,
    disableUndo!: Bool = true,
    text!: String = "text",
    filled!: Bool = false,
    icon!: Int64 = 0,
    showInObjectsTree!: Bool = false,
    zOrder!: Option<String> = None // ​"top" | "bottom"
): JsonObject {
    /*
            https://www.tradingview.com/charting-library-docs/v27/api/interfaces/Charting_Library.CreateMultipointShapeOptions
            "emoji" | "triangle" | "curve" | "circle" | "ellipse" | "path" | "polyline" | "text" | "icon" | "extended" | "anchored_text" | "anchored_note" | "note" | "signpost" | "double_curve" | "arc" | "sticker" | "arrow_up" | "arrow_down" | "arrow_left" | "arrow_right" | "price_label" | "price_note" | "arrow_marker" | "flag" | "vertical_line" | "horizontal_line" | "cross_line" | "horizontal_ray" | "trend_line" | "info_line" | "trend_angle" | "arrow" | "ray" | "parallel_channel" | "disjoint_angle" | "flat_bottom" | "anchored_vwap" | "pitchfork" | "schiff_pitchfork_modified" | "schiff_pitchfork" | "balloon" | "comment" | "inside_pitchfork" | "pitchfan" | "gannbox" | "gannbox_square" | "gannbox_fixed" | "gannbox_fan" | "fib_retracement" | "fib_trend_ext" | "fib_speed_resist_fan" | "fib_timezone" | "fib_trend_time" | "fib_circles" | "fib_spiral" | "fib_speed_resist_arcs" | "fib_channel" | "xabcd_pattern" | "cypher_pattern" | "abcd_pattern" | "callout" | "triangle_pattern" | "3divers_pattern" | "head_and_shoulders" | "fib_wedge" | "elliott_impulse_wave" | "elliott_triangle_wave" | "elliott_triple_combo" | "elliott_correction" | "elliott_double_combo" | "cyclic_lines" | "time_cycles" | "sine_line" | "long_position" | "short_position" | "forecast" | "date_range" | "price_range" | "date_and_price_range" | "bars_pattern" | "ghost_feed" | "projection" | "rectangle" | "rotated_rectangle" | "brush" | "highlighter" | "regression_trend" | "fixed_range_volume_profile"
     */
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
        return JsonObject(this.getFields())
    }

    public func getFields(): HashMap<String, JsonValue> {
        let obj = HashMap<String, JsonValue>()
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
        return JsonObject(this.getFields())
    }

    public func getFields(): HashMap<String, JsonValue> {
        let obj = HashMap<String, JsonValue>()
        obj.put("showLine", JsonBool(this.showLine))
        obj.put("lineWidth", JsonInt(this.lineWidth))
        obj.put("lineColor", JsonString(this.lineColor))
        obj.put("lineStyle", JsonInt(this.lineStyle))
        return obj
    }
}

public class Rectangle {
    public static func getBi(title: String, direction: Direction): Rectangle {
        let linewidth: Int64 = 1
        var linecolor: String = "rgba(76, 175, 80, 1)"
        var backgroundColor: String = "rgba(76, 175, 80, 0.2)"
        if (direction == Direction.Down) {
            linecolor = "rgba(178, 40, 51, 1)"
            backgroundColor = "rgba(178, 40, 51, 0.2)"
        }
        let middleline = MiddleLine(lineColor: linecolor, lineWidth: linewidth)
        let obj = Rectangle(text: "Bizs", title: title, color: linecolor, linewidth: linewidth,
            backgroundColor: backgroundColor, middleLine: middleline)
        return obj
    }

    public static func getDuan(title: String, direction: Direction): Rectangle {
        let linewidth: Int64 = 2
        var linecolor: String = "rgba(76, 175, 80, 1)"
        var backgroundColor: String = "rgba(76, 175, 80, 0.2)"
        if (direction == Direction.Down) {
            linecolor = "rgba(178, 40, 51, 1)"
            backgroundColor = "rgba(178, 40, 51, 0.2)"
        }
        let middleline = MiddleLine(lineColor: linecolor, lineWidth: linewidth)
        let obj = Rectangle(text: "Duanzs", title: title, color: linecolor, linewidth: linewidth,
            backgroundColor: backgroundColor, middleLine: middleline)
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
        obj.put("intervalsVisibilities", JsonObject(this.intervalsVisibilities.getFields()))
        return obj
    }
}

public class TrendLine {
    public static func getBi(title: String): TrendLine {
        let obj = TrendLine(text: "bi", title: title, linecolor: "#CC62FF", linewidth: 2, linestyle: 0)
        return obj
    }

    public static func getDuan(title: String): TrendLine {
        let obj = TrendLine(text: "duan", title: title, linecolor: "#F1C40F", linewidth: 3, linestyle: 0)
        return obj
    }

    public static func getFeature(title: String, direction: Direction): TrendLine {
        var obj = TrendLine(text: "feature", title: title, linecolor: "#22FF22", linewidth: 2, linestyle: 2)
        if (direction == Direction.Up) {
            obj = TrendLine(text: "feature", title: title, linecolor: "#FF2222", linewidth: 2, linestyle: 2)
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
    ) {
    }
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
