// ============================================================
//  项目 / 发票 / 回款 的领域映射 + 数据装配
//  挂在 window.PmApiProjects。纯转换，不持有 Vue ref。
// ============================================================
(function () {
  const { STATUS_CN } = window.PmStatus;

  // 后端 ProjectOut → 模板沿用的项目结构
  const mapProject = (p) => ({
    id: p.id,
    name: p.project_name || '未命名项目',
    code: p.contract_no || '—',
    amount: parseFloat(p.contract_amount || 0),
    date: p.sign_date || '',
    client: p.customer_name || '',
    type: p.project_type || '软件开发',
    pm: '—',
    description: p.description || '',
    status: STATUS_CN[p.status] || p.status,
    created_by: p.created_by_name || '用户#' + p.created_by,
    rejectReason: p.audit_reason || '',
    contractFile: '合同盖章扫描件.pdf',
    // 结项：close_status 决定验收报告/复核状态
    closeStatus: p.close_status || '',
    acceptanceReport: p.acceptance_report
      ? '验收报告.pdf'
      : p.close_status
        ? '结项申请已提交'
        : '',
    contractVersion: 1,
    expenses: [],
    invoices: [],
    payments: [],
  });

  const mapInvoice = (inv) => ({
    id: inv.id,
    code: inv.invoice_no || inv.invoice_code || 'INV-' + inv.id,
    amount: parseFloat(inv.amount || 0),
    date: inv.invoice_date || '',
    unit: inv.invoice_unit || '',
    buyer: inv.buyer_name || '',
  });

  const mapPayment = (pay) => ({
    id: pay.id,
    method: pay.payment_method || '银行转账',
    amount: parseFloat(pay.amount || 0),
    date: pay.payment_date || '',
  });

  // 注册项目 payload 构造（PUT/POST 共用）；description 把 verifyRemark 并入
  const buildProjectPayload = (form, { verifyRemark } = {}) => {
    const remarkLine = verifyRemark ? '差异核对说明：' + verifyRemark : '';
    const mergedDesc =
      [form.description, remarkLine].filter(Boolean).join('\n') || null;
    return {
      project_name: form.name,
      contract_no: form.code || null,
      contract_amount: form.amount || null,
      customer_name: form.client || null,
      project_type: form.type || null,
      sign_date: form.date || null,
      description: mergedDesc,
    };
  };

  // 拉取项目列表 + 为已立项/已结项补充开票/回款明细（财务台账/看板/结项依赖）
  const fetchProjectsWithFinance = async (api) => {
    const data = await api('/projects?size=100');
    const list = (data?.items || []).map(mapProject);
    await Promise.all(
      list
        .filter((p) => ['已立项', '已结项'].includes(p.status))
        .map(async (p) => {
          try {
            const [invRes, payRes] = await Promise.all([
              api('/projects/' + p.id + '/invoices'),
              api('/projects/' + p.id + '/payments'),
            ]);
            p.invoices = (invRes?.items || []).map(mapInvoice);
            p.payments = (payRes?.items || []).map(mapPayment);
          } catch (e) {
            // 单项明细失败不阻断列表
          }
        }),
    );
    return list;
  };

  window.PmApiProjects = {
    mapProject,
    mapInvoice,
    mapPayment,
    buildProjectPayload,
    fetchProjectsWithFinance,
  };
})();
