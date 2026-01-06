/**
 * 加密货币API服务
 */

import axios, { AxiosInstance } from "axios";
import type {
  CryptoPair,
  CryptoKline,
  CryptoTicker,
  ExchangeConfig,
  SyncPairsRequest,
  SyncKlinesRequest,
  SyncResult,
} from "@/types/crypto";

class CryptoService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: "/api/v1",
      timeout: 30000,
    });
  }

  // ==================== 交易对 ====================

  /**
   * 获取交易对列表
   */
  async getPairs(params?: {
    quote_asset?: string;
    exchange?: string;
    status?: string;
    limit?: number;
  }): Promise<CryptoPair[]> {
    const response = await this.api.get("/crypto/pairs", { params });
    return response.data.data;
  }

  /**
   * 同步交易对列表
   */
  async syncPairs(
    request: SyncPairsRequest,
    config: ExchangeConfig,
  ): Promise<SyncResult> {
    const response = await this.api.post("/crypto/sync/pairs", request, {
      params: config,
    });
    return response.data.data;
  }

  // ==================== K线数据 ====================

  /**
   * 获取K线数据
   */
  async getKlines(
    symbol: string,
    params?: {
      interval?: string;
      limit?: number;
      start_time?: string;
      end_time?: string;
    },
  ): Promise<CryptoKline[]> {
    const response = await this.api.get(`/crypto/klines/${symbol}`, { params });
    return response.data.data;
  }

  /**
   * 同步K线数据
   */
  async syncKlines(
    request: SyncKlinesRequest,
    config: ExchangeConfig,
  ): Promise<SyncResult> {
    const response = await this.api.post("/crypto/sync/klines", request, {
      params: config,
    });
    return response.data.data;
  }

  // ==================== 实时行情 ====================

  /**
   * 获取实时行情
   */
  async getTicker(symbol: string, exchange?: string): Promise<CryptoTicker> {
    const response = await this.api.get(`/crypto/ticker/${symbol}`, {
      params: { exchange },
    });
    return response.data.data;
  }

  /**
   * 批量获取实时行情
   */
  async getTickers(symbols: string[]): Promise<CryptoTicker[]> {
    const promises = symbols.map((symbol) => this.getTicker(symbol));
    return Promise.all(promises);
  }

  // ==================== 其他 ====================

  /**
   * 获取支持的K线周期
   */
  async getIntervals(): Promise<{ intervals: string[]; description: Record<string, string> }> {
    const response = await this.api.get("/crypto/intervals");
    return response.data.data;
  }
}

export const cryptoService = new CryptoService();
