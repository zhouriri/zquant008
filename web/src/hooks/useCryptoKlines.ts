/**
 * 加密货币K线数据Hook
 */

import { useState, useCallback } from "react";
import { cryptoService } from "@/services/cryptoService";
import type { CryptoKline } from "@/types/crypto";

export function useCryptoKlines() {
  const [klines, setKlines] = useState<CryptoKline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchKlines = useCallback(
    async (symbol: string, params?: {
      interval?: string;
      limit?: number;
      start_time?: string;
      end_time?: string;
    }) => {
      setLoading(true);
      setError(null);

      try {
        const data = await cryptoService.getKlines(symbol, params);
        setKlines(data);
      } catch (err: any) {
        setError(err.response?.data?.message || err.message || "获取K线失败");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return {
    klines,
    loading,
    error,
    fetchKlines,
  };
}
