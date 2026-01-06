/**
 * 加密货币交易对Hook
 */

import { useState, useEffect, useCallback } from "react";
import { cryptoService } from "@/services/cryptoService";
import type { CryptoPair } from "@/types/crypto";

export function useCryptoPairs(params?: {
  quote_asset?: string;
  exchange?: string;
  status?: string;
  limit?: number;
  autoFetch?: boolean;
}) {
  const [pairs, setPairs] = useState<CryptoPair[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPairs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await cryptoService.getPairs(params);
      setPairs(data);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || "获取交易对失败");
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    if (params?.autoFetch !== false) {
      fetchPairs();
    }
  }, [fetchPairs, params?.autoFetch]);

  return {
    pairs,
    loading,
    error,
    refetch: fetchPairs,
  };
}
