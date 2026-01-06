/**
 * 加密货币实时行情Hook
 */

import { useState, useEffect, useCallback } from "react";
import { cryptoService } from "@/services/cryptoService";
import type { CryptoTicker } from "@/types/crypto";

export function useCryptoTicker(
  symbol: string,
  exchange?: string,
  autoRefresh?: boolean,
  interval?: number,
) {
  const [ticker, setTicker] = useState<CryptoTicker | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTicker = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await cryptoService.getTicker(symbol, exchange);
      setTicker(data);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || "获取行情失败");
    } finally {
      setLoading(false);
    }
  }, [symbol, exchange]);

  useEffect(() => {
    fetchTicker();

    if (autoRefresh) {
      const refreshInterval = setInterval(
        fetchTicker,
        interval || 5000, // 默认5秒刷新
      );

      return () => clearInterval(refreshInterval);
    }
  }, [fetchTicker, autoRefresh, interval]);

  return {
    ticker,
    loading,
    error,
    refetch: fetchTicker,
  };
}
