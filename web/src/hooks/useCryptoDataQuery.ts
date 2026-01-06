/**
 * 加密货币数据查询统一Hook
 *
 * 基于useDataQuery封装，提供统一的加密货币数据查询逻辑
 */

import { useCallback } from 'react';
import { useDataQuery } from './useDataQuery';
import { cryptoService } from '@/services/cryptoService';
import type { CryptoPair, CryptoKline } from '@/types/crypto';

/**
 * 加密货币交易对数据查询Hook
 */
export function useCryptoPairsQuery(options?: {
  autoQuery?: boolean;
  successMessage?: string;
  errorMessage?: string;
}) {
  return useDataQuery<CryptoPair>(
    async (params) => {
      const { quote_asset, exchange, status, limit } = params;
      return await cryptoService.getPairs({
        quote_asset,
        exchange,
        status: status || 'trading',
        limit: limit || 100,
      });
    },
    (response) => response.data || [],
    (item, index) => item.symbol || index,
    {
      successMessage: options?.successMessage || `获取交易对成功`,
      errorMessage: options?.errorMessage || '获取交易对失败',
      autoQuery: options?.autoQuery || true,
    }
  );
}

/**
 * 加密货币K线数据查询Hook
 */
export function useCryptoKlinesQuery(options?: {
  autoQuery?: boolean;
  successMessage?: string;
  errorMessage?: string;
}) {
  return useDataQuery<CryptoKline>(
    async (params) => {
      const { symbol, interval, limit, start_time, end_time } = params;
      return await cryptoService.getKlines(
        symbol,
        {
          interval: interval || '1h',
          limit: limit || 100,
          start_time,
          end_time,
        }
      );
    },
    (response) => response.data || [],
    (item, index) => `${item.timestamp}_${index}`,
    {
      successMessage: options?.successMessage || `获取K线数据成功`,
      errorMessage: options?.errorMessage || '获取K线数据失败',
      autoQuery: options?.autoQuery || false,
    }
  );
}

/**
 * 加密货币实时行情Hook (保持自动刷新功能)
 */
export function useCryptoRealtime(
  symbol: string,
  exchange: string = 'binance',
  autoRefresh: boolean = true,
  interval: number = 5000
) {
  const { ticker, loading, error, refetch } = useCryptoTicker(
    symbol,
    exchange,
    autoRefresh,
    interval
  );

  const formatPrice = useCallback((price: number) => {
    return price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }, []);

  const formatPercent = useCallback((percent: number) => {
    const color = percent >= 0 ? 'text-green-500' : 'text-red-500';
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  }, []);

  return {
    ticker,
    loading,
    error,
    refetch,
    formatPrice,
    formatPercent,
  };
}

// 重新导出原有的Hook以保持兼容性
export { useCryptoTicker } from './useCryptoTicker';
export { useCryptoPairs } from './useCryptoPairs';
export { useCryptoKlines } from './useCryptoKlines';
