// ============================================================
//  纯函数：金额 / 百分比 / 文件名 等格式化助手
//  挂在 window.PmFormat。app.js 通过 const { fmtMoney } = window.PmFormat 消费。
//  采纳 OCR-IPMS utils 分层；不引入构建步骤，保留 CDN-Vue 部署形态。
// ============================================================
(function () {
  const fmtMoney = (n) =>
    Number(n || 0).toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  const pct = (num, denom, digits = 1) => {
    const d = Number(denom || 0);
    if (d <= 0) return '0.0';
    return ((Number(num || 0) / d) * 100).toFixed(digits);
  };

  window.PmFormat = { fmtMoney, pct };
})();
