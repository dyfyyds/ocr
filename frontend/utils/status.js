// ============================================================
//  状态值集中映射（后端英文 ↔ 模板沿用的中文标签）
//  与 backend/app/models/enums.py 一一对应。挂在 window.PmStatus。
//  注意：模板渲染的是「中文标签」，故 mapProject 把后端 status 转中文后下发，
//  这是 R1/R2 之前就有的约定，本次重构保持不变（不动模板/视觉）。
// ============================================================
(function () {
  const STATUS_CN = {
    draft: '草稿',
    pending_audit: '待审核',
    approved: '已立项',
    rejected: '已驳回',
    closed: '已结项',
  };
  const cnFromBackend = (en) => STATUS_CN[en] || en;

  // 反向查找：模板中文 → 后端英文（用于按状态过滤已加载列表）
  const EN_FROM_CN = Object.fromEntries(
    Object.entries(STATUS_CN).map(([en, cn]) => [cn, en]),
  );
  const enFromCn = (cn) => EN_FROM_CN[cn] || cn;

  window.PmStatus = { STATUS_CN, cnFromBackend, enFromCn };
})();
