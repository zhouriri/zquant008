# 加密货币版本 0.4.0 增强计划

## 📅 计划日期
2025-01-06

## 🎯 目标

基于ZQuant 0.3.0的核心架构优化,将其精华部分应用到加密货币模块,提升代码质量、性能和可维护性。

---

## ✅ 从0.3.0挑选的精华功能

### 1. 🏗️ Repository模式 (高优先级) ⭐⭐⭐⭐⭐

#### 原版实现
```python
# zquant/repositories/stock_repository.py
class StockRepository:
    """股票信息Repository"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = get_cache()
        self._cache_prefix = "stock:"
```

#### 加密货币版本实现
```python
# zquant/repositories/crypto_repository.py
class CryptoRepository:
    """加密货币数据Repository
    
    统一加密货币数据访问,提供批量查询和缓存优化
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = get_cache()
        self._cache_prefix = "crypto:"
```

#### 优势
- **查询性能提升90%+**: 批量查询替代N+1查询
- **缓存集中管理**: 统一的缓存策略
- **代码复用**: 减少重复代码50%+
- **易于测试**: Repository层独立测试

#### 需要实现的Repository
- CryptoPairRepository - 交易对数据
- CryptoKlineRepository - K线数据
- CryptoTickerRepository - 实时行情
- CryptoOrderRepository - 订单数据
- CryptoPositionRepository - 持仓数据

---

### 2. 🔄 Scheduler执行器模式 (高优先级) ⭐⭐⭐⭐⭐

#### 原版实现
```python
# zquant/scheduler/base.py
class TaskExecutor(ABC):
    """任务执行器基类"""
    
    @abstractmethod
    def execute(self, db: Session, config: dict, execution: TaskExecution | None = None) -> dict:
        """执行任务"""
        pass
```

#### 加密货币版本应用
现有加密货币调度任务应该继承统一的Executor基类:
```python
# zquant/scheduler/executors/crypto_sync_executor.py
class CryptoSyncExecutor(TaskExecutor):
    """加密货币同步任务执行器"""
    
    def execute(self, db: Session, config: dict, execution: TaskExecution | None = None) -> dict:
        """执行同步任务"""
        update_execution_progress(execution, 10, "开始同步交易对")
        
        # 同步逻辑...
        
        update_execution_progress(execution, 100, "同步完成")
        return {"success": True, "count": count}
```

#### 优势
- **统一的执行流程**: 所有调度任务使用相同模式
- **进度追踪**: 统一的进度更新机制
- **错误处理**: 标准化的错误处理和重试
- **易于扩展**: 新增调度任务只需继承基类

#### 需要重构的文件
- zquant/scheduler/job/sync_crypto_klines.py
- zquant/scheduler/job/sync_crypto_klines_v2.py

---

### 3. 🎨 前端组件抽象 (中优先级) ⭐⭐⭐⭐

#### 原版实现
```typescript
// web/src/components/DataTablePage/index.tsx
export interface DataTablePageConfig<TItem = any> {
  queryFn: (params: any) => Promise<any>;
  getItems: (response: any) => TItem[];
  columns: ProColumns<TItem>[];
  // ...更多配置
}
```

#### 加密货币版本应用
使用DataTablePage组件重构加密货币页面:
```typescript
// web/src/pages/CryptoMarket.tsx
import { DataTablePage } from '@/components/DataTablePage';

const CryptoMarket = () => {
  const config: DataTablePageConfig<CryptoPair> = {
    queryFn: cryptoService.getPairs,
    getItems: (res) => res.data,
    columns: [
      { title: '交易对', dataIndex: 'symbol', key: 'symbol' },
      { title: '价格', dataIndex: 'price', key: 'price' },
      // ...
    ],
    tableTitle: '加密货币行情'
  };
  
  return <DataTablePage {...config} />;
};
```

#### 优势
- **代码量减少**: 每个页面减少100+行代码
- **统一体验**: 所有页面一致的交互体验
- **易于维护**: 修改一处,所有页面受益
- **配置驱动**: 通过配置生成页面

#### 需要重构的页面
- web/src/pages/CryptoMarket.tsx
- web/src/pages/CryptoSync.tsx
- web/src/pages/CryptoBacktest.tsx

---

### 4. 🔧 前端Hook统一 (中优先级) ⭐⭐⭐⭐

#### 原版实现
```typescript
// web/src/hooks/useDataQuery.ts
export const useDataQuery = <T>(queryFn: (params: any) => Promise<T>) => {
  // 统一的数据查询Hook
};

// web/src/hooks/useDataValidation.ts
export const useDataValidation = (validateFn: (values: any) => Promise<void>) => {
  // 统一的数据验证Hook
};
```

#### 加密货币版本应用
统一现有的加密货币Hook:
```typescript
// web/src/hooks/useCryptoData.ts (新建)
export const useCryptoData = <T>(
  type: 'pairs' | 'klines' | 'ticker',
  params?: any
) => {
  // 统一的加密货币数据Hook
  // 复用useDataQuery的统一逻辑
};
```

#### 优势
- **统一加载状态**: 所有Hook使用相同的loading/error状态
- **统一错误处理**: 标准化的错误提示
- **减少重复**: 避免每个Hook重复实现相同逻辑

---

### 5. 🎯 工具类创建 (中优先级) ⭐⭐⭐

#### 原版实现
```python
# zquant/utils/date_helper.py
class DateHelper:
    """日期工具类"""
    
    @staticmethod
    def get_trading_days(start: str, end: str) -> List[str]:
        """获取交易日"""
        pass

# zquant/utils/code_converter.py
class CodeConverter:
    """代码转换工具类"""
    
    @staticmethod
    def symbol_to_ts_code(symbol: str) -> str:
        """股票代码转换"""
        pass
```

#### 加密货币版本实现
```python
# zquant/utils/crypto_helper.py
class CryptoHelper:
    """加密货币工具类"""
    
    @staticmethod
    def symbol_to_base_quote(symbol: str) -> tuple:
        """将BTCUSDT拆分为(BTC, USDT)"""
        # ...
    
    @staticmethod
    def get_interval_seconds(interval: str) -> int:
        """获取周期对应的秒数"""
        mapping = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        return mapping.get(interval, 86400)
    
    @staticmethod
    def normalize_interval(interval: str) -> str:
        """标准化周期格式"""
        # ...
```

---

### 6. 🚀 中间件增强 (低优先级) ⭐⭐⭐

#### 原版实现
```python
# zquant/middleware/audit.py
# zquant/middleware/logging.py
# zquant/middleware/rate_limit.py
# zquant/middleware/security.py
```

#### 加密货币版本应用
为加密货币API添加中间件支持:
```python
# 在zquant/api/v1/crypto.py中添加
from zquant.api.decorators import (
    handle_errors,
    validate_request,
    log_request
)

@router.get("/pairs")
@handle_errors
@log_request
async def get_pairs():
    # API端点
    pass
```

#### 优势
- **统一错误处理**: 自动捕获和记录错误
- **请求日志**: 统一的请求日志格式
- **性能监控**: API响应时间统计
- **安全增强**: 限流、XSS防护等

---

## 📊 实施计划

### 阶段1: Repository模式 (1-2天)
- [ ] 创建CryptoRepository基类
- [ ] 实现CryptoPairRepository
- [ ] 实现CryptoKlineRepository
- [ ] 实现CryptoTickerRepository
- [ ] 重构现有代码使用Repository
- [ ] 编写单元测试

### 阶段2: Scheduler优化 (1天)
- [ ] 创建CryptoSyncExecutor
- [ ] 重构sync_crypto_klines.py
- [ ] 重构sync_crypto_klines_v2.py
- [ ] 测试调度任务

### 阶段3: 前端优化 (2-3天)
- [ ] 使用DataTablePage重构CryptoMarket
- [ ] 使用DataTablePage重构CryptoSync
- [ ] 使用DataTablePage重构CryptoBacktest
- [ ] 统一useCrypto* Hooks
- [ ] 测试前端页面

### 阶段4: 工具类和中间件 (1天)
- [ ] 创建CryptoHelper工具类
- [ ] 添加中间件装饰器
- [ ] 性能测试

---

## 🎯 预期收益

### 性能提升
| 指标 | 提升 | 说明 |
|------|------|------|
| 数据库查询 | 90%+ | 批量查询替代N+1查询 |
| 缓存命中率 | 50%+ | 统一缓存策略 |
| 前端代码量 | 40%+ | 组件抽象复用 |
| API响应时间 | 30%+ | 优化查询逻辑 |

### 代码质量
| 指标 | 提升 | 说明 |
|------|------|------|
| 代码重复度 | -50%+ | Repository和组件复用 |
| 可测试性 | +100% | Repository层独立测试 |
| 可维护性 | +80% | 统一的代码模式 |
| 扩展性 | +100% | 易于添加新功能 |

---

## 📝 注意事项

### 不需要迁移的功能

以下0.3.0功能**不适合**加密货币版本:

1. **用户资产管理功能**
   - 加密货币模块已经包含自选和持仓功能
   - 可以保留现有实现

2. **量化筛选功能**
   - 加密货币选股逻辑与股票差异较大
   - 后续可单独开发

3. **组合因子功能**
   - 加密货币因子计算逻辑不同
   - 后续可单独开发

4. **特定股票数据同步**
   - Tushare、HSL等数据源仅用于股票
   - 加密货币已有独立的数据源

---

## 🚀 版本号

建议将当前版本从0.1.0升级到0.4.0:

```
当前: ZQuant Crypto Module v0.1.0
目标: ZQuant Crypto Module v0.4.0
原因: 对齐主版本的架构优化
```

---

## 📞 总结

通过本次增强,加密货币模块将获得:

✅ **Repository模式** - 统一数据访问,性能提升90%+
✅ **Scheduler优化** - 统一调度执行,更好的进度追踪
✅ **前端组件化** - 代码量减少40%+,统一交互体验
✅ **工具类增强** - 更好的代码组织和复用
✅ **中间件支持** - 统一的错误处理和日志

**预期工作量**: 5-6天
**预期收益**: 代码质量和性能显著提升
