/**
 * 根据TS代码判断交易所
 * 
 * @param tsCode TS代码或代码列表
 * @returns 交易所代码 (SSE 或 SZSE)
 */
export const getExchangeFromTsCode = (tsCode: string | string[] | undefined): string => {
  if (!tsCode) return 'SSE'; // 默认上交所
  
  const codes = Array.isArray(tsCode) ? tsCode : [tsCode];
  // 检查是否包含深交所代码（.SZ结尾）
  const hasSZSE = codes.some(code => code.endsWith('.SZ'));
  // 检查是否包含上交所代码（.SH结尾）
  const hasSSE = codes.some(code => code.endsWith('.SH'));
  
  // 如果只有深交所，返回SZSE；如果只有上交所或混合，返回SSE（默认）
  if (hasSZSE && !hasSSE) {
    return 'SZSE';
  }
  return 'SSE';
};

