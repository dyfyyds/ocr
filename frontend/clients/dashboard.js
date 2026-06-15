// ============================================================
//  工作台聚合数据（4 路并发：stats / trend / status-distribution / recent-logs）
//  挂在 window.PmApiDashboard。返回普通对象，不持有 Vue ref；
//  app.js 拿到结果后塞进 dashboard.value 即可。
// ============================================================
(function () {
  // 把 status-distribution 的 [{status,count}] 拍平成 { status: count } 便于环图取值
  const flattenStatusDist = (items) => {
    const out = {};
    (items || []).forEach((it) => {
      out[it.status] = it.count;
    });
    return out;
  };

  // 真实活动日志 → 终端面板行（time + type + text）
  const mapRecentLog = (l) => ({
    time: (l.created_at || '').replace('T', ' ').slice(11, 19) || '--:--:--',
    type: l.action || '系统',
    text: l.detail || '',
  });

  const fetchDashboard = async (api) => {
    const [s, t, sd, lg] = await Promise.all([
      api('/dashboard/stats'),
      api('/dashboard/trend'),
      api('/dashboard/status-distribution'),
      api('/dashboard/recent-logs?limit=30'),
    ]);
    return {
      stats: s,
      trend: t.items || [],
      statusDist: flattenStatusDist(sd.items),
      logs: (lg.items || []).map(mapRecentLog),
    };
  };

  window.PmApiDashboard = { fetchDashboard, mapRecentLog, flattenStatusDist };
})();
