// ============================================================
//  日期 / 期间过滤工具
//  挂在 window.PmDate。createPeriodSummer 是工厂：返回一个根据 year/month
//  refs 实时取值的 sum 函数，用于财务查询汇总按年度/月度过滤明细金额。
// ============================================================
(function () {
  // refs: { yearRef, monthRef } —— 传入响应式 ref；返回一个 (arr) => number 的 summer
  // monthRef.value 为 0 时表示「全年」
  const createPeriodSummer = ({ yearRef, monthRef }) => (arr) =>
    (arr || []).reduce((s, x) => {
      if (!x || !x.date) return s;
      const d = new Date(x.date);
      if (isNaN(d.getTime())) return s;
      if (d.getFullYear() !== Number(yearRef.value)) return s;
      if (monthRef.value && d.getMonth() + 1 !== Number(monthRef.value)) return s;
      return s + parseFloat(x.amount || 0);
    }, 0);

  // 稳定的近 N 年候选（默认 4 年），用于年度下拉选项
  const recentYears = (n = 4) => {
    const cy = new Date().getFullYear();
    return Array.from({ length: n }, (_, i) => cy - i);
  };

  window.PmDate = { createPeriodSummer, recentYears };
})();
