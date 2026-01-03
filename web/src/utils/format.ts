/**
 * 格式化时长（秒 -> 时分秒）
 * @param seconds 时长（秒）
 * @returns 格式化后的字符串，如：1小时2分3秒
 */
export const formatDuration = (seconds: number | undefined | null): string => {
  if (seconds === null || seconds === undefined) return '-';
  
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const remainingSeconds = s % 60;
  
  const parts = [];
  if (h > 0) parts.push(`${h}小时`);
  if (m > 0 || h > 0) parts.push(`${m}分`);
  parts.push(`${remainingSeconds}秒`);
  
  return parts.length > 0 ? parts.join('') : '0秒';
};

