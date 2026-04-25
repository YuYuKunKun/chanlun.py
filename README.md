# chanlun.py - 缠中说禅结构分析工具

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 📖 简介

`chanlun.py` 是一个基于缠中说禅理论的股票/数字货币技术分析工具。实现了**笔**、**段**、**中枢**的自动识别，并集成了 **TradingView 风格的前端可视化** 以及 **Backtrader 实时数据回测** 功能。通过简单的 Web API 即可获取任意交易品种的结构化分析结果。

## ✨ 特性

- 🧠 缠论核心算法：自动识别笔、线段、中枢
- 📈 交互式前端：基于 TradingView 风格的图表展示
- 🔄 实时回测：支持 Backtrader 引擎，可同步回测策略
- 🌐 Web API：通过 HTTP 请求获取分析数据，支持多种数据源
- ~~🎲 数据生成器：内置随机生成、周期合成、笔生成器等多种测试数据源~~

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn chan:app --reload --port 8080 --host localhost
```

服务启动后，访问 `http://127.0.0.1:8080` 即可看到前端可视化界面。

## 🎯 API 使用示例

通过 URL 参数可以灵活控制分析行为和输入数据：

```
http://127.0.0.1:8080/?debug=1&symbol=ethusd&generator=False&limit=1500&step=86400
```

| 参数          | 说明                            |
|-------------|-------------------------------|
| `debug`     | 开启网页调试模式（如 `true`）            |
| `symbol`    | 交易品种代码（如 `ethusd`、`btcusd`）   |
| `limit`     | 数据数量（如 `1500` 根 K 线）          |
| `step`      | K 线时间间隔（秒），如 `86400` 代表日线     |
| `generator` | 数据生成器/分析器类型，详见下方表格            |
| `**配置参数`    | 全量缠论配置相关参数 （如 `分析笔=False` 等等） |

### `generator` 参数详解

| 值        | 说明                                |
|----------|-----------------------------------|
| `True`   | ~~随机生成测试数据~~                      |
| `zqhc`   | 周期合成数据                            |
| `bi`     | ~~笔生成器，可通过 `points` 参数传入自定义顶底序列~~ |
| `hc`     | 邮局数据同步回测                          |
| `ex`     | 从文件读取数据（测试用）                      |
| `last`   | 读取上一次保存的分析数据                      |
| `lasthc` | 读取上一次保存的回测数据                      |
| (默认)     | 从邮局数据接口获取真实数据                     |

## 📸 预览

![运行效果预览](output.gif)

## 🤝 支持作者

如果这个项目对你有帮助，欢迎通过以下方式支持作者：

- ⭐ Star 本项目
- 📢 分享给更多缠论爱好者
- 💰 赞助（联系方式详见项目主页）

## 📄 开源协议

本项目采用 [MIT 协议](LICENSE)
