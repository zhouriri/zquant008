# ZQuant量化分析平台 - 完整项目分析

**更新时间**: 2025-01-05
**版本**: v1.0
**代码规模**: ~25,000行 (后端15,000行 + 前端10,000行)

---

## 📋 目录

- [项目概览](#项目概览)
- [技术栈](#技术栈)
- [架构设计](#架构设计)
- [后端架构](#后端架构)
- [回测引擎](#回测引擎)
- [因子系统](#因子系统)
- [前端架构](#前端架构)
- [数据存储](#数据存储)
- [部署方案](#部署方案)
- [开发指南](#开发指南)
- [API文档](#api文档)

---

## 项目概览

### 项目简介

**ZQuant** 是一个功能完整的股票量化分析系统,提供从数据采集、策略开发、回测分析到结果管理的一站式解决方案。

### 核心特性

- 🚀 **开箱即用**: 完整的量化分析系统,无需从零开始搭建
- 📊 **数据驱动**: 集成Tushare专业数据源,自动采集和清洗股票数据
- 🔬 **回测引擎**: 事件驱动的回测系统,支持多种策略类型和全面的绩效分析
- 🎯 **策略模板**: 内置8种常用策略模板,快速上手量化分析
- 🔐 **安全可靠**: 基于JWT的认证和RBAC权限控制,保障系统安全
- ⚡ **高性能**: 基于FastAPI构建,支持异步处理和分布式任务队列
- 📈 **因子系统**: 支持自定义因子计算和组合因子模型

### 文件统计

| 模块 | Python文件 | TypeScript文件 | 代码行数(估算) |
|------|-----------|---------------|----------------|
| 后端(zquant) | 82个 | - | ~15,000行 |
| 前端(web/src) | - | ~150个 | ~10,000行 |
| **总计** | **82** | **150** | **~25,000** |

---

## 技术栈

### 后端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web框架 | FastAPI | 0.104.1+ | 现代化高性能Web框架 |
| 数据库ORM | SQLAlchemy | 2.0.23+ | Python SQL工具包和ORM |
| 数据库 | MySQL | 8.4+ | 关系型数据库 |
| 缓存 | Redis | 7+ | 高性能内存数据库 |
| 异步任务 | Celery | 5.3.4+ | 分布式任务队列 |
| 定时任务 | APScheduler | 3.10.4+ | Python任务调度库 |
| 数据源 | Tushare | 1.2.89 | 金融数据服务 |
| 认证 | JWT | - | 无状态认证机制 |
| 密码加密 | bcrypt | 3.2.2+ | 密码哈希 |
| 数据处理 | Pandas | 2.1.3+ | 数据分析库 |
| 日志 | Loguru | 0.7.2+ | 结构化日志 |

### 前端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | React | 19 | UI库 |
| 路由 | UmiJS | 4+ | React路由框架 |
| 语言 | TypeScript | 5+ | 类型安全的JavaScript |
| UI组件库 | Ant Design | 5+ | 企业级UI设计语言 |
| 状态管理 | React Context | - | 轻量级状态管理 |
| HTTP客户端 | umi-request | - | 基于axios的请求库 |
| 国际化 | i18n | - | 支持8种语言 |
| 代码规范 | Biome | - | 替代ESLint + Prettier |

### 开发工具

| 工具 | 用途 |
|------|------|
| Ruff | 代码检查和格式化(兼容Black) |
| Black | 代码格式化 |
| isort | 导入排序 |
| pytest | 单元测试 |
| Alembic | 数据库迁移 |
| Docker | 容器化部署 |

---

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────┐
│                   前端层 (React)                  │
│  Pages → Components → Hooks → Services → API        │
└─────────────────────────────────────────────────────┘
                       ↓ HTTP/REST
┌─────────────────────────────────────────────────────┐
│                    API路由层 (FastAPI)              │
│  统一错误处理、请求验证、响应转换                  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                  业务逻辑层 (Services)              │
│  认证服务、数据服务、回测服务、调度服务...        │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              数据访问层 (Repositories)             │
│  批量查询优化、缓存管理、统一数据访问              │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│               数据存储层 (Models + DB)             │
│  MySQL + Redis + 分表存储 + 视图管理               │
└─────────────────────────────────────────────────────┘
```

### 设计模式应用

| 设计模式 | 应用场景 | 实现位置 |
|---------|---------|----------|
| **Repository模式** | 统一数据访问层 | `repositories/` |
| **Strategy模式** | 数据同步策略 | `services/sync_strategies/` |
| **Factory模式** | 策略/因子工厂 | `factor/calculators/factory.py` |
| **Decorator模式** | 缓存/重试装饰器 | `utils/cache_decorator.py` |
| **Singleton模式** | 全局配置 | `config.py` |

### 代码复用架构

```
工具函数层 (utils/)
  ├── cache.py           # 缓存管理
  ├── cache_decorator.py # 缓存装饰器
  ├── date_helper.py     # 日期工具
  ├── code_converter.py  # 代码转换
  └── query_builder.py  # 查询构建器
           ↓
基类层 (*/*/base.py)
  ├── BaseSyncJob       # 调度任务基类
  ├── BaseStrategy      # 策略基类
  ├── DataSyncStrategy  # 数据同步策略基类
  └── AuditMixin       # 审计字段混入
           ↓
业务层 (services/)
  ├── 具体的同步任务
  ├── 具体的策略实现
  └── 具体的业务逻辑
```

### 主要重构成果

- ✅ **数据存储层**: 代码重复度降低 > 50%
- ✅ **调度脚本**: 统一参数解析和错误处理
- ✅ **API层**: 统一错误处理和响应转换
- ✅ **前端**: 统一数据查询和表格展示逻辑
- ✅ **2025重构**: Repository模式、批量查询优化、Strategy模式

---

## 后端架构

### 目录结构

```
zquant/
├── api/                     # API路由层
│   ├── v1/                # API v1版本
│   │   ├── auth.py        # 认证接口
│   │   ├── backtest.py    # 回测接口
│   │   ├── data.py        # 数据服务接口
│   │   ├── factor.py      # 因子管理接口
│   │   ├── dashboard.py   # 系统大盘接口
│   │   ├── notifications.py # 通知中心接口
│   │   ├── permissions.py # 权限管理接口
│   │   ├── roles.py       # 角色管理接口
│   │   ├── scheduler.py   # 定时任务接口
│   │   ├── stock_filter.py # 量化选股接口
│   │   ├── users.py       # 用户管理接口
│   │   ├── favorites.py   # 我的自选接口
│   │   ├── positions.py   # 我的持仓接口
│   │   ├── hsl_choice.py  # ZQ精选数据接口
│   │   └── config.py     # 配置管理接口
│   ├── decorators.py      # API装饰器(统一错误处理)
│   └── deps.py           # 依赖注入(数据库会话、认证)
├── models/                 # 数据库模型层
│   ├── backtest.py       # 回测相关模型
│   ├── data.py          # 数据相关模型(含动态分表)
│   ├── factor.py        # 因子模型
│   ├── notification.py  # 通知模型
│   ├── scheduler.py     # 调度任务模型
│   └── user.py         # 用户、角色、权限、APIKey模型
├── schemas/              # Pydantic模型(请求/响应验证)
├── services/             # 业务逻辑层
│   ├── sync_strategies/ # 数据同步策略(Strategy模式)
│   ├── auth.py         # 认证服务
│   ├── backtest.py     # 回测服务
│   ├── data.py         # 数据服务
│   ├── factor.py       # 因子服务
│   ├── scheduler.py    # 调度服务
│   ├── stock_filter.py # 选股服务
│   └── ...
├── repositories/         # Repository层(数据访问优化)
│   ├── trading_date_repository.py
│   ├── stock_repository.py
│   ├── price_data_repository.py
│   ├── factor_repository.py
│   └── ...
├── backtest/            # 回测引擎核心
│   ├── engine.py        # 回测引擎主类
│   ├── context.py       # 回测上下文
│   ├── strategy.py      # 策略基类
│   ├── order.py         # 订单模型
│   ├── cost.py         # 成本计算器
│   └── performance.py   # 绩效分析器
├── data/                # 数据存储和处理
│   ├── storage.py       # 数据存储服务
│   ├── processor.py     # 数据清洗和处理
│   ├── view_manager.py  # 视图管理(分表联合)
│   └── etl/            # ETL流程
├── scheduler/           # 任务调度器
│   ├── manager.py       # 调度管理器
│   └── job/            # 调度任务
│       ├── base.py      # 调度脚本基类
│       └── sync_*.py   # 数据同步脚本
├── factor/              # 因子计算模块
│   ├── calculators/    # 因子计算器
│   └── ...
├── core/               # 核心功能
│   ├── security.py      # 安全相关
│   ├── permissions.py   # 权限管理
│   └── exceptions.py   # 异常定义
├── middleware/         # 中间件
│   ├── audit.py        # 审计日志
│   ├── logging.py     # 请求日志
│   ├── rate_limit.py  # 速率限制
│   └── security.py    # 安全防护
├── utils/              # 工具函数
│   ├── cache.py       # 缓存管理
│   ├── cache_decorator.py # 缓存装饰器
│   ├── date_helper.py # 日期工具
│   ├── code_converter.py # 代码转换
│   ├── query_builder.py # 查询构建器
│   └── ...
├── constants/          # 常量管理
│   ├── data_constants.py
│   ├── factor_constants.py
│   └── api_constants.py
├── strategy/           # 策略示例
│   └── examples/      # 8种内置策略
├── scripts/            # 初始化和管理脚本
├── tests/              # 测试
├── main.py            # 应用入口
├── config.py          # 配置管理
└── database.py        # 数据库连接
```

### API路由结构

#### 核心端点分类

**认证与用户管理**
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新Token
- `GET /api/v1/users/me` - 获取当前用户信息
- `GET /api/v1/users/{id}` - 获取用户详情
- `PUT /api/v1/users/{id}` - 更新用户信息

**数据服务**
- `GET /api/v1/data/stocks` - 获取股票列表
- `GET /api/v1/data/stocks/{ts_code}` - 获取股票详情
- `GET /api/v1/data/trading-calendar` - 获取交易日历
- `GET /api/v1/data/daily` - 获取日线数据
- `GET /api/v1/data/daily-basic` - 获取每日指标
- `GET /api/v1/data/fundamentals` - 获取财务数据
- `POST /api/v1/data/sync` - 手动触发数据同步

**回测**
- `POST /api/v1/backtest/create` - 创建回测任务
- `GET /api/v1/backtest/tasks` - 获取回测任务列表
- `GET /api/v1/backtest/tasks/{id}` - 获取回测详情
- `GET /api/v1/backtest/results/{id}` - 获取回测结果
- `GET /api/v1/backtest/strategies` - 获取策略列表
- `POST /api/v1/backtest/strategies` - 创建策略

**定时任务**
- `GET /api/v1/scheduler/tasks` - 获取定时任务列表
- `POST /api/v1/scheduler/tasks` - 创建定时任务
- `PUT /api/v1/scheduler/tasks/{id}` - 更新定时任务
- `DELETE /api/v1/scheduler/tasks/{id}` - 删除定时任务
- `POST /api/v1/scheduler/tasks/{id}/trigger` - 手动触发任务
- `POST /api/v1/scheduler/tasks/{id}/pause` - 暂停任务
- `POST /api/v1/scheduler/tasks/{id}/resume` - 恢复任务

**因子管理**
- `GET /api/v1/factor/definitions` - 获取因子定义
- `POST /api/v1/factor/models` - 创建因子模型
- `POST /api/v1/factor/configs` - 创建因子配置
- `POST /api/v1/factor/calculate` - 计算因子值

**系统管理**
- 用户管理、角色管理、权限管理
- 数据源配置、系统配置

### 数据库模型和表结构

#### 表命名规范

| 前缀 | 说明 | 示例 |
|------|------|------|
| `zq_data_*` | 数据表 | zq_data_tustock_stockbasic |
| `zq_app_*` | 应用表 | zq_app_users, zq_app_roles |
| `zq_backtest_*` | 回测表 | zq_backtest_strategies |
| `zq_task_*` | 任务表 | zq_task_scheduled_tasks |
| `zq_stats_*` | 统计表 | zq_stats_apisync |
| `zq_quant_factor_*` | 因子表 | zq_quant_factor_definitions |

#### 核心数据表

**1. 股票相关**

| 表名 | 说明 | 关键字段 |
|-----|-----|---------|
| `zq_data_tustock_stockbasic` | 股票基础信息 | ts_code(PK), symbol, name, industry, market |
| `zq_data_tustock_tradecal` | 交易日历 | exchange, cal_date, is_open, pretrade_date |
| `zq_data_tustock_daily_XXXXXX` | 日线分表 | ts_code, trade_date, open, high, low, close |
| `zq_data_tustock_daily_basic_XXXXXX` | 每日指标分表 | ts_code, trade_date, pe, pb, turnover_rate |
| `zq_data_fundamentals` | 财务数据 | symbol, report_date, statement_type, data_json |
| `zq_data_stock_filter_result` | 量化选股结果 | id, filter_id, ts_code, match_date, score |
| `zq_data_hsl_choice` | ZQ精选数据 | ts_code, choice_date, reason, tags |

**2. 用户和权限**

| 表名 | 说明 | 关键字段 |
|-----|-----|---------|
| `zq_app_users` | 用户表 | id(PK), username, email, hashed_password, role_id |
| `zq_app_roles` | 角色表 | id(PK), name, description |
| `zq_app_permissions` | 权限表 | id(PK), name, code, resource, action |
| `zq_app_role_permissions` | 角色权限关联 | role_id, permission_id |
| `zq_app_apikeys` | API密钥表 | id(PK), user_id, key_hash, name, is_active |

**3. 回测**

| 表名 | 说明 | 关键字段 |
|-----|-----|---------|
| `zq_backtest_strategies` | 策略表 | id, name, code, description, category |
| `zq_backtest_tasks` | 回测任务 | id, strategy_id, status, start_date, end_date |
| `zq_backtest_results` | 回测结果 | id, task_id, total_return, sharpe_ratio, max_drawdown |

**4. 定时任务**

| 表名 | 说明 | 关键字段 |
|-----|-----|---------|
| `zq_task_scheduled_tasks` | 定时任务配置 | id, name, task_type, cron_expr, task_action |
| `zq_task_task_executions` | 任务执行历史 | id, task_id, status, start_time, end_time |

**5. 因子**

| 表名 | 说明 | 关键字段 |
|-----|-----|---------|
| `zq_quant_factor_definitions` | 因子定义 | id, factor_name, cn_name, column_name, factor_type |
| `zq_quant_factor_models` | 因子模型 | id, definition_id, name, model_code, config |
| `zq_quant_factor_configs` | 因子配置 | id, model_id, start_date, end_date, params |

---

## 回测引擎

### 核心组件

#### BacktestEngine - 回测引擎主类

**文件**: `zquant/backtest/engine.py`

**主要功能**:
- 事件驱动的回测执行
- T+1交易机制模拟
- 订单撮合和成交
- 成本计算(佣金、印花税、滑点)
- 投资组合管理

**核心方法**:
```python
def __init__(db, strategy_class, config):
    """初始化回测引擎"""
    self.context = Context(initial_cash, config)
    self.cost_calculator = CostCalculator(config)
    self.pending_orders = {}  # 待成交订单(T+1)
    self.filled_orders = []   # 已成交订单

def run():
    """运行回测"""
    # 按交易日历循环
    # 撮合昨日订单
    # 更新持仓市值
    # 调用策略on_bar
    # 记录回测结果
```

#### BaseStrategy - 策略基类

**文件**: `zquant/backtest/strategy.py`

**接口定义**:

| 方法 | 参数 | 说明 | 是否必须 |
|-----|------|------|---------|
| `initialize()` | - | 策略初始化 | 是 |
| `on_bar(context, bar_data)` | context: 上下文, bar_data: K线 | K线回调 | 是 |
| `on_tick(context, tick_data)` | tick_data: Tick数据 | Tick回调 | 否 |
| `on_order_status(context, order)` | order: 订单信息 | 订单状态回调 | 否 |

#### Context - 回测上下文

**文件**: `zquant/backtest/context.py`

**Portfolio - 投资组合**:
```python
@dataclass
class Portfolio:
    cash: float  # 可用资金
    positions: dict[str, Position]  # 持仓字典
    
    @property
    def total_value(self) -> float:  # 总资产
        return self.cash + sum(pos.market_value for pos in self.positions.values())
```

**Position - 持仓信息**:
```python
@dataclass
class Position:
    symbol: str
    quantity: float      # 持仓数量
    avg_cost: float      # 平均成本
    current_price: float # 当前价格
    market_value: float # 市值
    
    @property
    def profit(self) -> float:  # 浮动盈亏
        return (self.current_price - self.avg_cost) * self.quantity
```

**Context对象方法**:
```python
context.order(symbol, quantity, price=None)              # 下单
context.order_target(symbol, quantity)                   # 调整到目标数量
context.order_target_value(symbol, value)                 # 调整到目标市值
context.portfolio                                        # 访问投资组合
context.current_date                                     # 当前日期
```

#### Order - 订单模型

**文件**: `zquant/backtest/order.py`

**订单类型**:
- `OrderSide.BUY` - 买入
- `OrderSide.SELL` - 卖出

**订单状态**:
- `OrderStatus.PENDING` - 待成交
- `OrderStatus.FILLED` - 已成交
- `OrderStatus.CANCELLED` - 已取消

#### CostCalculator - 成本计算器

**文件**: `zquant/backtest/cost.py`

**成本类型**:
- 佣金: 默认万分之三,最低5元
- 印花税: 卖出时收取千分之一
- 滑点: 默认千分之一

#### PerformanceAnalyzer - 绩效分析器

**文件**: `zquant/backtest/performance.py`

**绩效指标**:
```python
{
    "total_return": 总收益率,
    "annual_return": 年化收益率,
    "max_drawdown": 最大回撤,
    "sharpe_ratio": 夏普比率,
    "alpha": Alpha,
    "beta": Beta,
    "win_rate": 胜率,
    "profit_loss_ratio": 盈亏比
}
```

### 执行流程

```
初始化引擎
  ↓
加载交易日历
  ↓
加载价格数据
  ↓
创建策略实例
  ↓
策略初始化
  ↓
┌─────────────┐
│ 交易日历循环 │
└─────────────┘
  ↓
撮合T-1订单(T+1机制)
  ↓
更新持仓市值
  ↓
获取当前K线
  ↓
调用策略on_bar
  ↓
{还有交易日?}
  是 ↑
  否 ↓
计算绩效指标
  ↓
返回回测结果
```

### 内置策略示例

| 策略文件 | 策略类型 | 核心逻辑 |
|---------|----------|---------|
| `simple_ma.py` | 简单均线 | 金叉买入,死叉卖出 |
| `dual_ma.py` | 双均线 | 短期均线上穿长期均线买入 |
| `bollinger_bands.py` | 布林带 | 价格触碰下轨买入,上轨卖出 |
| `rsi_strategy.py` | RSI指标 | RSI超买超卖信号 |
| `momentum.py` | 动量策略 | 上涨趋势买入 |
| `mean_reversion.py` | 均值回归 | 价格偏离均值回归 |
| `grid_trading.py` | 网格交易 | 分档买卖 |
| `pe_pb_strategy.py` | PE/PB价值 | 低估值买入 |
| `turnover_rate_strategy.py` | 换手率策略 | 高换手率选股 |

---

## 因子系统

### 系统概述

因子系统是ZQuant的核心功能之一,支持:
- **因子定义**: 定义因子的名称、公式、描述
- **因子模型**: 将因子映射到具体的计算逻辑
- **因子配置**: 配置因子的时间范围、参数
- **因子计算**: 批量计算多只股票的因子值
- **因子数据存储**: 按股票分表存储因子数据

### 数据模型

#### FactorDefinition - 因子定义表

**表名**: `zq_quant_factor_definitions`

**关键字段**:
```python
id: int (主键)
factor_name: str (唯一,因子标识)  # 如: "turnover_rate"
cn_name: str (中文名称)           # 如: "换手率"
en_name: str (英文名称)           # 如: "Turnover Rate"
column_name: str (数据列名)       # 如: "turnover_rate"
description: str (描述)
factor_type: str (因子类型)       # "单因子" 或 "组合因子"
enabled: bool (是否启用)
```

**示例因子**:
- `turnover_rate` - 换手率
- `hyper_activity` - 超级活跃
- `momentum_20d` - 20日动量
- `volatility_20d` - 20日波动率

#### FactorModel - 因子模型表

**表名**: `zq_quant_factor_models`

**关键字段**:
```python
id: int (主键)
definition_id: int (外键,关联因子定义)
name: str (模型名称)
model_code: str (模型代码)      # 如: "turnover_rate", "hyper_activity"
config: JSON (模型配置)
```

**内置因子模型**:
- `turnover_rate` - 换手率计算器
- `hyper_activity` - 超级活跃因子计算器

#### FactorConfig - 因子配置表

**表名**: `zq_quant_factor_configs`

**关键字段**:
```python
id: int (主键)
model_id: int (外键,关联因子模型)
start_date: date (开始日期)
end_date: date (结束日期)
params: JSON (计算参数)
```

#### FactorData - 因子数据分表

**表名**: `zq_quant_factor_spacex_{ts_code}`

**动态创建**: 根据股票代码动态创建

**关键字段**:
```python
ts_code: str (股票代码)
trade_date: date (交易日期)
{factor_column}: float (因子值)  # 如: turnover_rate, hyper_activity
```

### 因子计算器

#### FactorCalculatorFactory - 因子计算器工厂

**文件**: `zquant/factor/calculators/factory.py`

**功能**: 根据model_code创建对应的因子计算器

```python
class FactorCalculatorFactory:
    _calculators = {
        "turnover_rate": TurnoverRateCalculator,
        "hyper_activity": HyperActivityCalculator,
    }
    
    def create_calculator(self, model_code: str):
        return self._calculators[model_code]()
```

#### 内置因子计算器

**1. TurnoverRateCalculator - 换手率计算器**

计算公式:
```
换手率 = 成交量 / 流通股本 × 100%
```

**2. HyperActivityCalculator - 超级活跃因子计算器**

计算逻辑:
- 结合换手率和价格波动
- 识别活跃度高且波动大的股票

### 因子服务

#### FactorService - 因子管理服务

**文件**: `zquant/services/factor.py`

**主要方法**:

| 方法 | 说明 |
|-----|------|
| `get_definitions()` | 获取因子定义列表 |
| `create_definition()` | 创建因子定义 |
| `update_definition()` | 更新因子定义 |
| `get_models()` | 获取因子模型列表 |
| `create_model()` | 创建因子模型 |
| `get_configs()` | 获取因子配置列表 |
| `create_config()` | 创建因子配置 |
| `calculate_factor()` | 计算因子值 |

#### FactorCalculationService - 因子计算服务

**文件**: `zquant/services/factor_calculation.py`

**主要方法**:

| 方法 | 说明 |
|-----|------|
| `calculate_single_factor()` | 计算单个因子 |
| `calculate_batch_factors()` | 批量计算多个因子 |
| `get_factor_data()` | 获取因子数据 |
| `get_factor_ranking()` | 获取因子排名 |

### 因子数据存储

#### 分表策略

**原则**: 按股票代码分表

**表名格式**: `zq_quant_factor_spacex_{ts_code}`

**示例**:
- `zq_quant_factor_spacex_000001` - 平安银行
- `zq_quant_factor_spacex_000002` - 万科A

#### 视图管理

**联合视图**: `zq_quant_factor_spacex_view`

**创建方式**:
```python
from zquant.data.view_manager import create_or_update_factor_view

# 创建因子数据联合视图
create_or_update_factor_view(db)
```

**视图用途**: 统一查询所有股票的因子数据

### 因子API

#### 端点列表

| 方法 | 端点 | 说明 |
|-----|------|------|
| GET | `/api/v1/factor/definitions` | 获取因子定义列表 |
| POST | `/api/v1/factor/definitions` | 创建因子定义 |
| PUT | `/api/v1/factor/definitions/{id}` | 更新因子定义 |
| DELETE | `/api/v1/factor/definitions/{id}` | 删除因子定义 |
| GET | `/api/v1/factor/models` | 获取因子模型列表 |
| POST | `/api/v1/factor/models` | 创建因子模型 |
| GET | `/api/v1/factor/configs` | 获取因子配置列表 |
| POST | `/api/v1/factor/configs` | 创建因子配置 |
| POST | `/api/v1/factor/calculate` | 计算因子值 |
| GET | `/api/v1/factor/data` | 获取因子数据 |

### 因子使用场景

1. **量化选股**: 根据因子值筛选股票
2. **多因子模型**: 组合多个因子构建选股策略
3. **因子分析**: 分析因子的有效性和稳定性
4. **因子回测**: 回测基于因子的策略

---

## 前端架构

### 技术栈

- **框架**: React 19 + TypeScript
- **UI组件库**: Ant Design 5 + Ant Design Pro Components 2.7
- **路由**: UmiJS 4
- **状态管理**: React Context + Hooks
- **HTTP客户端**: umi-request(基于axios)
- **国际化**: i18n(支持8种语言)
- **代码规范**: Biome(替代ESLint + Prettier)

### 目录结构

```
web/src/
├── pages/                  # 页面组件
│   ├── user/             # 用户相关页面
│   ├── account/          # 账户中心
│   ├── dashboard/        # 系统大盘
│   ├── backtest/         # 回测页面
│   ├── data/            # 数据管理页面
│   ├── factor/           # 因子管理页面
│   ├── admin/           # 系统管理页面
│   ├── watchlist/        # 我的关注
│   └── legal/           # 法律声明
├── components/           # 公共组件
│   ├── DataTable/        # 数据表格组件
│   ├── DataTablePage/    # 通用表格页面
│   ├── RightContent/     # 右侧工具栏
│   ├── MenuSearch/       # 菜单搜索
│   ├── GlobalTabs/       # 全局标签页
│   ├── Footer/          # 页脚
│   └── HeaderDropdown/   # 头部下拉菜单
├── services/             # API服务层
│   └── zquant/         # ZQuant API封装
├── hooks/               # 自定义Hooks
│   ├── useDataQuery.ts         # 数据查询
│   ├── useDataSync.ts         # 数据同步
│   ├── useDataValidation.ts   # 数据校验
│   ├── useErrorHandler.ts     # 错误处理
│   ├── useGlobalTabs.ts       # 全局标签页
│   └── usePageCache.ts       # 页面缓存
├── contexts/            # React Context
│   ├── PageCacheContext.tsx   # 页面缓存上下文
│   └── SettingDrawerContext.tsx # 设置抽屉上下文
├── locales/             # 国际化文件
│   ├── zh-CN/
│   ├── en-US/
│   └── ...
├── utils/               # 工具函数
├── constants/           # 常量定义
├── app.tsx             # 应用入口(运行时配置)
├── global.less         # 全局样式
└── requestErrorConfig.ts # 错误处理配置
```

### 页面和路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/user/login` | Login | 登录页 |
| `/welcome` | Welcome | 欢迎页 |
| `/dashboard` | Dashboard | 系统大盘 |
| `/backtest` | Backtest | 回测模块 |
| `/backtest/list` | BacktestList | 回测任务列表 |
| `/backtest/strategies` | StrategyList | 策略管理 |
| `/data` | Data | 数据管理 |
| `/data/tushare` | TushareData | Tushare数据 |
| `/data/scheduler` | Scheduler | 定时任务 |
| `/factor` | Factor | 因子管理 |
| `/watchlist` | Watchlist | 我的关注 |
| `/admin/users` | Users | 用户管理 |
| `/admin/roles` | Roles | 角色管理 |

### 自定义Hooks

#### useDataQuery - 统一数据查询

```typescript
const { data, loading, error, refetch } = useDataQuery({
  url: '/api/v1/data/stocks',
  params: { page: 1, pageSize: 10 },
  immediate: true,
});
```

#### useDataSync - 统一数据同步

```typescript
const { sync, syncing, progress } = useDataSync({
  endpoint: '/api/v1/data/sync',
  onComplete: () => message.success('同步完成'),
});
```

#### useDataValidation - 数据校验

```typescript
const { validate, errors } = useDataValidation({
  schema: validationSchema,
});
```

#### useGlobalTabs - 全局标签页管理

```typescript
const { addTab, closeTab, activeTab, tabs } = useGlobalTabs();
```

#### usePageCache - 页面缓存

```typescript
const { cachePage, getCachedPage, clearCache } = usePageCache();
```

### API服务层

| 服务文件 | 说明 | 主要方法 |
|---------|------|---------|
| `auth.ts` | 认证服务 | login(), register(), refresh() |
| `users.ts` | 用户服务 | getCurrentUser(), updateUser() |
| `backtest.ts` | 回测服务 | createTask(), getTasks(), getResults() |
| `data.ts` | 数据服务 | getStocks(), getDailyData(), syncData() |
| `factor.ts` | 因子服务 | getDefinitions(), calculateFactor() |
| `scheduler.ts` | 调度服务 | getTasks(), createTask(), triggerTask() |
| `stockFilter.ts` | 选股服务 | createFilter(), getResults() |

---

## 数据存储

### 数据库设计

#### 表分类

**数据表 (zq_data_*)**:
- `zq_data_tustock_stockbasic` - 股票基础信息(~5000条)
- `zq_data_tustock_tradecal` - 交易日历(~2000条)
- `zq_data_tustock_daily_*` - 日线分表(~5000个表)
- `zq_data_tustock_daily_basic_*` - 每日指标分表(~5000个表)
- `zq_data_fundamentals` - 财务数据
- `zq_data_hsl_choice` - ZQ精选数据

**应用表 (zq_app_*)**:
- `zq_app_users` - 用户
- `zq_app_roles` - 角色
- `zq_app_permissions` - 权限
- `zq_app_role_permissions` - 角色权限关联
- `zq_app_apikeys` - API密钥
- `zq_app_configs` - 系统配置

**回测表 (zq_backtest_*)**:
- `zq_backtest_strategies` - 策略
- `zq_backtest_tasks` - 回测任务
- `zq_backtest_results` - 回测结果

**任务表 (zq_task_*)**:
- `zq_task_scheduled_tasks` - 定时任务配置
- `zq_task_task_executions` - 任务执行历史

**因子表 (zq_quant_factor_*)**:
- `zq_quant_factor_definitions` - 因子定义
- `zq_quant_factor_models` - 因子模型
- `zq_quant_factor_configs` - 因子配置
- `zq_quant_factor_spacex_*` - 因子数据分表(~5000个表)

**统计表 (zq_stats_*)**:
- `zq_stats_apisync` - API同步日志

### 分表策略

#### 分表原则

**按股票代码分表** - 日线数据、每日指标、因子数据

**表名格式**:
- 日线: `zq_data_tustock_daily_{symbol}`
- 每日指标: `zq_data_tustock_daily_basic_{symbol}`
- 因子: `zq_quant_factor_spacex_{symbol}`

**示例**:
- `zq_data_tustock_daily_000001` - 平安银行日线
- `zq_data_tustock_daily_basic_000001` - 平安银行每日指标
- `zq_quant_factor_spacex_000001` - 平安银行因子

#### 动态表模型

```python
@lru_cache(maxsize=None)
def create_tustock_daily_class(ts_code: str):
    """动态创建日线表模型类"""
    table_name = get_daily_table_name(ts_code)
    class TustockDaily(Base, AuditMixin):
        __tablename__ = table_name
        ...
    return TustockDaily
```

#### 分表管理器

**文件**: `zquant/services/partition_manager.py`

```python
class PartitionManager:
    def create_partition(self, ts_code: str):
        """创建分表"""
    
    def drop_partition(self, ts_code: str):
        """删除分表"""
    
    def list_partitions(self) -> list[str]:
        """列出所有分表"""
```

#### 分表优势

- **查询性能提升**: 单表数据量减少90%+
- **索引效率提升**: 单表索引更小
- **维护灵活性**: 可单独备份/删除旧数据
- **水平扩展**: 支持未来分库分表

### 视图管理

#### 联合视图设计

**1. 日线数据视图**

```sql
CREATE VIEW zq_data_tustock_daily_view AS
SELECT * FROM zq_data_tustock_daily_000001
UNION ALL
SELECT * FROM zq_data_tustock_daily_000002
UNION ALL
...
```

**2. 每日指标视图**

```sql
CREATE VIEW zq_data_tustock_daily_basic_view AS
SELECT * FROM zq_data_tustock_daily_basic_000001
UNION ALL
...
```

**3. 因子视图**

```sql
CREATE VIEW zq_quant_factor_spacex_view AS
SELECT * FROM zq_quant_factor_spacex_000001
UNION ALL
...
```

#### 视图管理器

**文件**: `zquant/data/view_manager.py`

| 函数 | 说明 |
|-----|------|
| `create_or_update_daily_view()` | 创建/更新日线视图 |
| `create_or_update_daily_basic_view()` | 创建/更新每日指标视图 |
| `create_or_update_factor_view()` | 创建/更新因子视图 |
| `drop_daily_view()` | 删除日线视图 |
| `get_all_daily_tables()` | 获取所有日线分表 |

#### 视图创建策略

1. **优先使用存储过程** - 性能更高
   ```sql
   CALL sp_create_daily_view();
   ```

2. **回退到Python代码** - 兼容性更好
   ```python
   _create_or_update_daily_view_direct(db)
   ```

---

## 部署方案

### Docker部署(推荐)

#### docker-compose.yml 服务编排

```yaml
services:
  zquant-app:     # FastAPI应用
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
  
  mysql:          # MySQL 8.4
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: zquant
    volumes:
      - mysql_data:/var/lib/mysql
  
  redis:          # Redis
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  nginx:          # Nginx反向代理
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - zquant-app
```

#### 部署步骤

```bash
# 1. 配置环境变量
cp docker/.env.example docker/.env

# 2. 启动所有服务
docker-compose up -d

# 3. 初始化数据库(首次部署)
docker-compose exec zquant-app python3 -m zquant.scripts.init_db
docker-compose exec zquant-app python3 -m zquant.scripts.init_scheduler
docker-compose exec zquant-app python3 -m zquant.scripts.init_view
docker-compose exec zquant-app python3 -m zquant.scripts.init_strategies
docker-compose exec zquant-app python3 -m zquant.scripts.init_factor

# 4. 访问应用
# 前端: http://localhost
# API文档: http://localhost/docs
```

### 传统部署方式

#### 安装依赖

```bash
pip install -r zquant/requirements.txt
```

#### 配置环境变量

```bash
cp .env.example .env
# 编辑.env,修改SECRET_KEY、DB_PASSWORD、TUSHARE_TOKEN等配置
```

#### 初始化数据库

```bash
# 1. 初始化数据库和基础表
python zquant/scripts/init_db.py

# 2. 初始化定时任务系统
python zquant/scripts/init_scheduler.py

# 3. 创建数据视图
python zquant/scripts/init_view.py

# 4. 导入策略模板
python zquant/scripts/init_strategies.py

# 5. 初始化因子系统
python zquant/scripts/init_factor.py
```

#### 启动服务

```bash
uvicorn zquant.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 开发指南

### 代码规范

#### Python代码规范

**使用Ruff进行代码检查和格式化**:

```bash
# 检查代码
ruff check zquant/

# 自动修复可修复的问题
ruff check --fix zquant/

# 格式化代码
ruff format zquant/

# 同时检查和格式化
ruff check --fix zquant/ && ruff format zquant/
```

**配置文件**: `zquant/pyproject.toml`

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

#### TypeScript代码规范

**使用Biome**:

```bash
# 检查代码
biome check web/src/

# 格式化代码
biome format web/src/

# 同时检查和格式化
biome check --write web/src/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_backtest.py

# 查看覆盖率
pytest --cov=zquant --cov-report=html
```

### Pre-commit钩子

```bash
# 安装pre-commit
pip install pre-commit

# 安装Git hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 常用命令

```bash
# 启动开发服务器
uvicorn zquant.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端开发服务器
cd web && npm start

# 同步数据
python zquant/scheduler/job/sync_daily_data.py

# 检查数据库表
python check_tables.py

# 查看API文档
# 访问 http://localhost:8000/docs
```

---

## API文档

### 认证

#### 登录

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 数据服务

#### 获取股票列表

```http
GET /api/v1/data/stocks?page=1&pageSize=20
Authorization: Bearer {access_token}
```

#### 获取日线数据

```http
GET /api/v1/data/daily?ts_code=000001.SZ&start_date=20240101&end_date=20241231
Authorization: Bearer {access_token}
```

### 回测

#### 创建回测任务

```http
POST /api/v1/backtest/create
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "strategy_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000.0,
  "symbols": ["000001.SZ", "000002.SZ"]
}
```

### 因子

#### 获取因子定义

```http
GET /api/v1/factor/definitions
Authorization: Bearer {access_token}
```

#### 计算因子

```http
POST /api/v1/factor/calculate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model_id": 1,
  "ts_codes": ["000001.SZ", "000002.SZ"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### 完整API文档

访问 `http://localhost:8000/docs` 查看完整的Swagger UI文档。

---

## 附录

### 环境变量配置

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DB_HOST` | 数据库主机 | localhost | 否 |
| `DB_PORT` | 数据库端口 | 3306 | 否 |
| `DB_USER` | 数据库用户名 | root | 否 |
| `DB_PASSWORD` | 数据库密码 | - | 是 |
| `DB_NAME` | 数据库名称 | zquant | 否 |
| `REDIS_HOST` | Redis主机 | localhost | 否 |
| `REDIS_PORT` | Redis端口 | 6379 | 否 |
| `TUSHARE_TOKEN` | Tushare API Token | - | 是 |
| `SECRET_KEY` | JWT密钥 | - | 是 |

### 常见问题

**Q: 如何获取Tushare Token?**

A: 访问 [Tushare官网](https://tushare.pro/) 注册账号并获取Token。

**Q: 服务启动后无法访问?**

A: 请检查:
1. 是否使用了正确的访问地址(`http://localhost:8000`而不是`http://0.0.0.0:8000`)
2. 防火墙是否允许8000端口
3. 服务是否正常启动

**Q: 如何创建第一个策略?**

A: 系统提供了8种策略模板,可以直接使用或基于模板进行修改。详见[策略管理文档](docs/strategy_management.md)。

### 相关文档

- [Docker部署指南](docs/docker_deployment.md)
- [API访问指南](API_ACCESS.md)
- [数据库初始化指南](docs/database_init.md)
- [策略管理文档](docs/strategy_management.md)
- [调度器指南](docs/scheduler_guide.md)
- [重构总结](docs/refactoring_2025_summary.md)
- [贡献指南](CONTRIBUTING.md)

### 联系方式

- **邮箱**: kevin@vip.qq.com
- **微信**: zquant2025
- **GitHub Issues**: https://github.com/yoyoung/zquant/issues
- **GitHub Discussions**: https://github.com/yoyoung/zquant/discussions

---

**文档版本**: 1.0
**更新日期**: 2025-01-05
**维护者**: ZQuant Team
