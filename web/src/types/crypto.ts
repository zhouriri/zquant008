/**
 * 加密货币相关类型定义
 */

// 加密货币交易对
export interface CryptoPair {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  exchange: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

// K线数据
export interface CryptoKline {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  quote_volume?: number;
}

// 实时行情
export interface CryptoTicker {
  symbol: string;
  exchange: string;
  price: number;
  price_change?: number;
  price_change_percent?: number;
  high_24h?: number;
  low_24h?: number;
  volume_24h?: number;
  timestamp?: string;
}

// 交易所配置
export interface ExchangeConfig {
  exchange: string;
  api_key: string;
  api_secret: string;
  passphrase?: string;
}

// 同步请求
export interface SyncPairsRequest {
  quote_asset?: string;
  status?: string;
}

export interface SyncKlinesRequest {
  symbol: string;
  interval?: string;
  days_back?: number;
  start_time?: string;
  end_time?: string;
}

// 同步结果
export interface SyncResult {
  synced_count: number;
}

// 支持的K线周期
export interface KlineInterval {
  value: string;
  label: string;
}

// 回测配置
export interface CryptoBacktestConfig {
  initial_capital: number;
  exchange: string;
  symbols: string[];
  interval: string;
  start_time: string;
  end_time: string;
  maker_fee: number;
  taker_fee: number;
  slippage_rate: number;
}

// 回测结果
export interface CryptoBacktestResult {
  initial_capital: number;
  final_value: number;
  total_return: number;
  total_return_pct: number;
  total_trades: number;
  start_time: string;
  end_time: string;
}
