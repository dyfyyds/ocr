/* ── app.js: Cosmos Void 逻辑控制中心 ── */

const { createApp, ref, computed, onMounted, nextTick, watch } = Vue;

createApp({
  setup() {
    // ── 用户认证、权限隔离与路由状态 ──
    const currentUser = ref(null);
    const activeTab = ref(localStorage.getItem('pm_active_tab') || 'dashboard');
    const terminalLogs = ref([]);
    // 移动端侧边栏抽屉开关
    const sidebarOpen = ref(false);

    // 登录表单模型
    const loginForm = ref({
      username: '',
      password: '',
      error: ''
    });

    // ── 本地存储数据库表 ──
    const projects = ref([]);
    const users = ref([]);
    const dictItems = ref([]);
    const auditLogs = ref([]);

    // ── OCR 状态与分步逻辑 ──
    const isScanning = ref(false);
    const ocrSuccess = ref(false);
    const currentStep = ref(1); // 1: 上传Word, 2: 自动填充表单, 3: 预算支出与PDF, 4: OCR差异比对
    
    // 立项登记表单模型
    const formProject = ref({
      name: '',
      code: '',
      amount: 0,
      date: '',
      client: '',
      type: '软件开发',
      pm: '—',
      description: '',
      expenses: [],
      invoices: [],
      payments: [],
      contractVersion: 1,
      contractFile: '',
      acceptanceReport: '',
      status: '草稿',
      created_by: '',
      rejectReason: ''
    });

    const newExpense = ref({ desc: '', amount: '', date: '' });
    const activeEditProject = ref(null);
    const selectedProjectDetails = ref(null);
    
    // 财务开票与回款临时表单
    const selectedProjectForFinance = ref(null);
    const tempInvoice = ref({ amount: '', code: '', date: '' });
    const tempPayment = ref({ amount: '', method: '银行转账', date: '' });

    // 数据字典类型定义
    // 字典类型（登录后由 loadDict() 从后端覆盖，code 与后端一致为小写）
    const dictTypes = ref([
      { code: 'project_type', name: '项目类型' },
      { code: 'payment_method', name: '回款方式' }
    ]);

    // ── 数据库初始化与种子数据注入 ──
    const initDatabase = () => {
      // 1. 初始化系统用户表（包含默认明文密码 '123456'）
      const storedUsers = localStorage.getItem('pm_users');
      if (storedUsers) {
        users.value = JSON.parse(storedUsers);
      } else {
        const initialUsers = [
          { id: 1, username: 'admin', password: '123456', name: '系统管理员', role: 'admin', active: true },
          { id: 2, username: 'business', password: '123456', name: '张三（商务经理）', role: 'business', active: true },
          { id: 3, username: 'finance', password: '123456', name: '李四（财务总监）', role: 'finance', active: true },
          { id: 4, username: 'pm', password: '123456', name: '王五（项目经理）', role: 'pm', active: true }
        ];
        localStorage.setItem('pm_users', JSON.stringify(initialUsers));
        users.value = initialUsers;
      }

      // 2. 初始化数据字典项
      const storedDict = localStorage.getItem('pm_dict');
      if (storedDict) {
        dictItems.value = JSON.parse(storedDict);
      } else {
        const initialDict = [
          { id: 1, typeCode: 'PROJECT_TYPE', code: 'DEV', name: '软件开发', order: 1 },
          { id: 2, typeCode: 'PROJECT_TYPE', code: 'INTEGRATION', name: '系统集成', order: 2 },
          { id: 3, typeCode: 'PROJECT_TYPE', code: 'CONSULTING', name: '技术咨询', order: 3 },
          { id: 4, typeCode: 'PROJECT_TYPE', code: 'MAINTENANCE', name: '运维服务', order: 4 },
          { id: 5, typeCode: 'PAYMENT_METHOD', code: 'BANK', name: '银行转账', order: 1 },
          { id: 6, typeCode: 'PAYMENT_METHOD', code: 'ALIPAY', name: '支付宝商户', order: 2 }
        ];
        localStorage.setItem('pm_dict', JSON.stringify(initialDict));
        dictItems.value = initialDict;
      }

      // 3. 项目档案改由后端 loadProjects() 加载，不再注入本地假数据。
      //    旧的本地种子数据已停用（封存在 if(false) 死分支内，避免大段删除带来风险）。
      projects.value = [];
      localStorage.removeItem('pm_projects');
      if (false) {
        const initialProjects = [
          {
            id: 1,
            name: '智慧园区管理系统',
            code: 'HT-2026-001',
            amount: 580000.00,
            date: '2026-06-01',
            client: '科蓝软件科技有限公司',
            type: '软件开发',
            pm: '王五',
            description: '为智慧园区提供物联感知、设备集成与资产管理平台。',
            expenses: [
              { desc: '服务器采购', amount: 25000, date: '2026-06-05' },
              { desc: '第三方接口授权费', amount: 8000, date: '2026-06-05' }
            ],
            invoices: [],
            payments: [],
            contractVersion: 1,
            contractFile: '智慧园区管理系统-合同-盖章版.pdf',
            acceptanceReport: '',
            status: '待审核',
            created_by: 'business',
            rejectReason: ''
          },
          {
            id: 2,
            name: '企业级数据中台项目',
            code: 'HT-2026-002',
            amount: 1200000.00,
            date: '2026-05-15',
            client: '华盛集团股份有限公司',
            type: '系统集成',
            pm: '王五',
            description: '整合企业数据孤岛，构建分析主仓与实时报表看板。',
            expenses: [
              { desc: '专线宽带采购', amount: 45000, date: '2026-05-20' }
            ],
            invoices: [
              { id: 1, amount: 600000.00, code: 'INV-2026-001', date: '2026-05-28' }
            ],
            payments: [
              { id: 1, amount: 500000.00, method: '银行转账', date: '2026-06-02' }
            ],
            contractVersion: 1,
            contractFile: '企业级数据中台项目-盖章合同.pdf',
            acceptanceReport: '',
            status: '已立项',
            created_by: 'business',
            rejectReason: ''
          },
          {
            id: 3,
            name: '智能质检系统维护项目',
            code: 'HT-2026-003',
            amount: 240000.00,
            date: '2026-04-10',
            client: '万顺制造有限公司',
            type: '运维服务',
            pm: '王五',
            description: '智能机器视觉模块维保与定期更新算法服务。',
            expenses: [],
            invoices: [
              { id: 2, amount: 240000.00, code: 'INV-2026-002', date: '2026-04-15' }
            ],
            payments: [
              { id: 2, amount: 240000.00, method: '银行转账', date: '2026-04-30' }
            ],
            contractVersion: 1,
            contractFile: '智能质检系统维护项目-盖章.pdf',
            acceptanceReport: '质检系统完工报告-盖章.pdf',
            status: '已结项',
            created_by: 'business',
            rejectReason: ''
          },
          {
            id: 4,
            name: '政务云平台升级工程',
            code: 'HT-2026-004',
            amount: 1800000.00,
            date: '2026-05-01',
            client: '市大数据管理局',
            type: '软件开发',
            pm: '王五',
            description: '云主机架构升级扩容，适配全栈国产系统开发。',
            expenses: [],
            invoices: [],
            payments: [],
            contractVersion: 1,
            contractFile: '政务云合同-盖章.pdf',
            acceptanceReport: '',
            status: '已驳回',
            created_by: 'business',
            rejectReason: '提交的合同签订人印章不清晰，且与立项金额不一致。请核对后重新提交盖章合同扫描件。'
          },
          {
            id: 5,
            name: '智能排产规划咨询',
            code: 'HT-2026-005',
            amount: 150000.00,
            date: '2026-06-03',
            client: '远东重工集团',
            type: '技术咨询',
            pm: '李四',
            description: '车间精益排产建模服务，提供规划方案。',
            expenses: [],
            invoices: [],
            payments: [],
            contractVersion: 1,
            contractFile: '',
            acceptanceReport: '',
            status: '草稿',
            created_by: 'business',
            rejectReason: ''
          }
        ];
        localStorage.setItem('pm_projects', JSON.stringify(initialProjects));
        projects.value = initialProjects;
      }
      
      // 写入初始连接日志
      addLog('数据库', '本地数据库存储引擎连接成功。项目数据状态就绪。');
      addLog('OCR内核', 'PaddleOCR 识别服务就绪。智能解析解析通道就绪。');
    };

    const saveProjects = () => {
      localStorage.setItem('pm_projects', JSON.stringify(projects.value));
    };

    const addLog = (type, message) => {
      const timeStr = new Date().toLocaleTimeString();
      terminalLogs.value.unshift({ time: timeStr, type, text: message });
      if (terminalLogs.value.length > 50) {
        terminalLogs.value.pop();
      }
    };

    // ── 用户认证与会话控制 ──
    const checkLoginSession = () => {
      const savedUser = localStorage.getItem('pm_current_user');
      if (savedUser) {
        currentUser.value = JSON.parse(savedUser);
        addLog('系统', `用户会话成功恢复：${currentUser.value.name} （角色：${currentUser.value.role.toUpperCase()}）`);
        // 导航至合法页
        enforceTabAccess();
        // 会话恢复后从后端重新加载真实数据
        if (localStorage.getItem('pm_token')) {
          loadAllData();
        } else {
          nextTick(() => renderCharts());
        }
      }
    };

    const handleLogin = async () => {
      loginForm.value.error = '';
      if (!loginForm.value.username || !loginForm.value.password) {
        loginForm.value.error = '请输入用户名和密码！';
        return;
      }

      // 数据库匹配用户
      const found = users.value.find(u => u.username === loginForm.value.username);
      if (!found) {
        loginForm.value.error = '账号不存在，请检查输入！';
        addLog('安全', `尝试登录非法账号: "${loginForm.value.username}"`);
        return;
      }

      if (!found.active) {
        loginForm.value.error = '此账号已被管理员冻结，无法登录系统！';
        addLog('安全', `已被冻结的用户尝试登录: ${found.name}`);
        return;
      }

      // 验证密码（默认 '123456'）
      const expectedPassword = found.password || '123456';
      if (loginForm.value.password !== expectedPassword) {
        loginForm.value.error = '密码输入错误！';
        addLog('安全', `用户 "${found.name}" 登录密码验证失败。`);
        return;
      }

      // 成功登录
      currentUser.value = found;
      localStorage.setItem('pm_current_user', JSON.stringify(found));

      // 同步认证后端 API，获取并缓存 JWT（access + refresh），供需要鉴权的接口使用
      try {
        const tokenData = await api('/auth/login', {
          method: 'POST',
          body: { username: found.username, password: loginForm.value.password },
        });
        localStorage.setItem('pm_token', tokenData.access_token);
        if (tokenData.refresh_token) localStorage.setItem('pm_refresh_token', tokenData.refresh_token);
        addLog('系统', `后端 API 认证成功，Token 已缓存。`);
      } catch (e) {
        // 后端认证失败（如账号不同步）：清除旧 Token，明确提示而非静默吞掉
        localStorage.removeItem('pm_token');
        localStorage.removeItem('pm_refresh_token');
        addLog('安全', `后端 API 认证未通过（${e.message}）：文件上传等需鉴权功能将不可用，请核对账号密码与后端是否一致。`);
      }

      addLog('系统', `登录成功。工作舱已绑定用户：${found.name}（角色：${found.role.toUpperCase()}）`);
      
      // 根据角色分发默认工作台
      if (found.role === 'pm') {
        activeTab.value = 'pm_projects';
      } else if (found.role === 'finance') {
        activeTab.value = 'finance_ledger';
      } else if (found.role === 'business') {
        activeTab.value = 'projects';
      } else {
        activeTab.value = 'dashboard';
      }

      // 清除表单
      loginForm.value.username = '';
      loginForm.value.password = '';
      loginForm.value.error = '';

      // 拉取后端真实数据（项目/用户/字典）并渲染图表
      if (localStorage.getItem('pm_token')) {
        await loadAllData();
      } else {
        nextTick(() => renderCharts());
      }
    };

    // 一键演示填充并登录
    const quickAutofillAndLogin = (username) => {
      const found = users.value.find(u => u.username === username);
      if (found) {
        loginForm.value.username = username;
        loginForm.value.password = found.password || '123456';
        loginForm.value.error = '';
        handleLogin();
      }
    };

    const logout = () => {
      addLog('系统', `用户 "${currentUser.value?.name}" 已安全断开会话连接。`);
      currentUser.value = null;
      // 清理整个会话：包括后端 JWT，避免登出后残留可用 Token
      ['pm_current_user', 'pm_active_tab', 'pm_token', 'pm_refresh_token']
        .forEach((k) => localStorage.removeItem(k));
      sidebarOpen.value = false;
      activeTab.value = 'dashboard';
      // 等 Vue 渲染完登录表单后再执行动画
      nextTick(() => {
        // 清除可能残留的 GSAP 样式
        gsap.set('.space-grid-bg, .inline-flex, h1, p, .glass-panel.max-w-md', { clearProps: 'all' });
        animateLogin();
      });
    };

    // ── 权限强分离控制 ──
    const enforceTabAccess = () => {
      if (!currentUser.value) return;
      const role = currentUser.value.role;
      if (role === 'pm' && activeTab.value !== 'pm_projects' && activeTab.value !== 'dashboard') {
        activeTab.value = 'pm_projects';
      } else if (role === 'finance' && !['finance_ledger', 'close_audit', 'finance_query', 'dashboard'].includes(activeTab.value)) {
        activeTab.value = 'finance_ledger';
      } else if (role === 'business' && !['register', 'projects', 'dashboard'].includes(activeTab.value)) {
        activeTab.value = 'projects';
      } else if (role === 'admin' && !['audit', 'users', 'dict', 'dashboard'].includes(activeTab.value)) {
        activeTab.value = 'dashboard';
      }
    };

    // ── 工作台后端聚合数据（取代客户端按已加载分页估算） ──
    // 由 loadDashboard() 调真实接口填充；失败回退客户端计算，绝不伪造。
    const dashboard = ref({ loaded: false, stats: null, trend: [], statusDist: {}, logs: [] });
    const fmtMoney = (n) => Number(n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    // ── 全局统计指标 ──
    const stats = computed(() => {
      // 优先后端聚合（跨全部项目/发票/回款，规模化口径准确）
      const d = dashboard.value;
      if (d.loaded && d.stats) {
        const s = d.stats;
        const contractSum = +s.contract_total || 0;
        const invoicedSum = +s.invoice_total || 0;
        const paymentSum = +s.payment_total || 0;
        const receivables = Math.max(0, +s.receivable || 0);
        return {
          total: s.project_total || 0,
          initiated: s.approved_total || 0,
          pendingAudit: s.pending_audit || 0,
          closed: s.closed_total || 0,
          contractSum: fmtMoney(contractSum),
          invoicedSum: fmtMoney(invoicedSum),
          paymentSum: fmtMoney(paymentSum),
          receivables: fmtMoney(receivables),
          invoiceRate: contractSum > 0 ? ((invoicedSum / contractSum) * 100).toFixed(1) : '0.0',
          collectionRate: invoicedSum > 0 ? ((paymentSum / invoicedSum) * 100).toFixed(1) : '0.0',
        };
      }

      // 回退：后端不可用时按已加载项目估算
      const list = projects.value;
      let contractSum = 0, invoicedSum = 0, paymentSum = 0;
      list.forEach(p => {
        if (['已立项', '已结项'].includes(p.status)) {
          contractSum += parseFloat(p.amount || 0);
          p.invoices?.forEach(i => invoicedSum += parseFloat(i.amount || 0));
          p.payments?.forEach(py => paymentSum += parseFloat(py.amount || 0));
        }
      });
      const receivables = Math.max(0, invoicedSum - paymentSum);
      return {
        total: list.length,
        initiated: list.filter(p => p.status === '已立项').length,
        pendingAudit: list.filter(p => p.status === '待审核').length,
        closed: list.filter(p => p.status === '已结项').length,
        contractSum: fmtMoney(contractSum),
        invoicedSum: fmtMoney(invoicedSum),
        paymentSum: fmtMoney(paymentSum),
        receivables: fmtMoney(receivables),
        invoiceRate: contractSum > 0 ? ((invoicedSum / contractSum) * 100).toFixed(1) : '0.0',
        collectionRate: invoicedSum > 0 ? ((paymentSum / invoicedSum) * 100).toFixed(1) : '0.0',
      };
    });

    const pendingAuditProjects = computed(() => {
      return projects.value.filter(p => p.status === '待审核');
    });

    const pendingCloseProjects = computed(() => {
      // 已提交结项申请、等待财务终审的项目（close_status === pending）
      return projects.value.filter(p => p.closeStatus === 'pending');
    });

    // ── 后端 API 基础地址 ──
    const API_BASE = '/api';

    // 获取认证头
    const getAuthHeaders = () => {
      const token = localStorage.getItem('pm_token');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };

    // 用 refresh_token 静默续期 access_token，成功返回 true
    const tryRefresh = async () => {
      const refresh = localStorage.getItem('pm_refresh_token');
      if (!refresh) return false;
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        localStorage.setItem('pm_token', data.access_token);
        if (data.refresh_token) localStorage.setItem('pm_refresh_token', data.refresh_token);
        return true;
      } catch {
        return false;
      }
    };

    // ── 统一后端请求层 ──
    // 自动注入鉴权头；遇 401 用 refresh_token 续期并重试一次；
    // 规范化错误为 Error(message)（读取后端真实的 message 字段）。
    const api = async (path, { method = 'GET', body, isForm = false, _retried = false } = {}) => {
      const headers = { ...getAuthHeaders() };
      if (body != null && !isForm) headers['Content-Type'] = 'application/json';
      const payload = isForm ? body : (body != null ? JSON.stringify(body) : undefined);

      let res;
      try {
        res = await fetch(`${API_BASE}${path}`, { method, headers, body: payload });
      } catch (e) {
        throw Object.assign(new Error('网络连接失败，请检查后端服务是否可用'), { status: 0 });
      }

      // access_token 失效：尝试续期后重试一次；失败则登出
      if (res.status === 401 && !_retried && !path.includes('/auth/')) {
        if (await tryRefresh()) {
          return api(path, { method, body, isForm, _retried: true });
        }
        logout();
        throw Object.assign(new Error('登录状态已过期，请重新登录'), { status: 401 });
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw Object.assign(
          new Error(data.message || data.detail || `请求失败 (${res.status})`),
          { status: res.status, code: data.code },
        );
      }
      return res.status === 204 ? null : res.json().catch(() => null);
    };

    // ── 后端数据加载层（取代 localStorage 假数据） ──
    // 状态映射：后端英文 → 控制舱模板沿用的中文标签（保持现有视觉语言不动）
    const STATUS_CN = {
      draft: '草稿', pending_audit: '待审核', approved: '已立项',
      rejected: '已驳回', closed: '已结项',
    };

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
      created_by: p.created_by_name || ('用户#' + p.created_by),
      rejectReason: p.audit_reason || '',
      contractFile: '合同盖章扫描件.pdf',
      // 结项：close_status 决定验收报告/复核状态
      closeStatus: p.close_status || '',
      acceptanceReport: p.acceptance_report
        ? '验收报告.pdf'
        : (p.close_status ? '结项申请已提交' : ''),
      contractVersion: 1,
      expenses: [],
      invoices: [],
      payments: [],
    });

    const mapInvoice = (inv) => ({
      id: inv.id,
      code: inv.invoice_no || inv.invoice_code || ('INV-' + inv.id),
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

    // 拉取单个项目的开票/回款明细并挂载（财务台账、结项复核、看板统计依赖）
    const refreshProjectFinance = async (proj) => {
      try {
        const [invRes, payRes] = await Promise.all([
          api(`/projects/${proj.id}/invoices`),
          api(`/projects/${proj.id}/payments`),
        ]);
        proj.invoices = (invRes?.items || []).map(mapInvoice);
        proj.payments = (payRes?.items || []).map(mapPayment);
      } catch (e) {
        // 明细拉取失败不阻断列表展示
      }
      return proj;
    };

    // 从后端加载项目列表（唯一数据源），并为已立项/已结项补充开票回款明细
    const loadProjects = async () => {
      try {
        const data = await api('/projects?size=100');
        const list = (data?.items || []).map(mapProject);
        await Promise.all(
          list
            .filter((p) => ['已立项', '已结项'].includes(p.status))
            .map((p) => refreshProjectFinance(p))
        );
        projects.value = list;
      } catch (e) {
        addLog('系统', `项目列表加载失败：${e.message}`);
      }
    };

    // 从后端加载用户列表（管理员用户管理页）
    const loadUsers = async () => {
      try {
        const data = await api('/users?size=100');
        users.value = (data?.items || []).map((u) => ({
          id: u.id,
          username: u.username,
          name: u.real_name || u.username,
          role: u.role,
          active: u.status === 1,
        }));
      } catch (e) {
        addLog('系统', `用户列表加载失败：${e.message}`);
      }
    };

    // 从后端加载数据字典（类型 + 字典项）
    const loadDict = async () => {
      try {
        const tdata = await api('/dict/types');
        dictTypes.value = (tdata?.items || []).map((t) => ({
          id: t.id, code: t.type_code, name: t.type_name,
        }));
        const all = [];
        for (const t of dictTypes.value) {
          const idata = await api(`/dict/types/${t.code}/items`);
          (idata?.items || []).forEach((it) => all.push({
            id: it.id, typeId: t.id, typeCode: t.code,
            code: it.item_value, name: it.item_label, order: it.sort_order,
          }));
        }
        dictItems.value = all;
      } catch (e) {
        addLog('系统', `数据字典加载失败：${e.message}`);
      }
    };

    // 工作台真实聚合：统计 / 趋势 / 状态分布 / 最近活动 四个后端接口
    const loadDashboard = async () => {
      try {
        const [s, t, sd, lg] = await Promise.all([
          api('/dashboard/stats'),
          api('/dashboard/trend'),
          api('/dashboard/status-distribution'),
          api('/dashboard/recent-logs?limit=30'),
        ]);
        const statusDist = {};
        (sd.items || []).forEach((i) => { statusDist[i.status] = i.count; });
        dashboard.value = {
          loaded: true,
          stats: s,
          trend: t.items || [],
          statusDist,
          logs: lg.items || [],
        };
        // 面板为空时用后端真实活动日志填充（不覆盖会话实时事件）
        if (terminalLogs.value.length === 0 && dashboard.value.logs.length) {
          dashboard.value.logs.forEach((l) => {
            terminalLogs.value.push({
              time: (l.created_at || '').replace('T', ' ').slice(11, 19) || '--:--:--',
              type: l.action || '系统',
              text: l.detail || '',
            });
          });
        }
        nextTick(() => renderCharts());  // 数据到位后用真实聚合重绘图表
      } catch (e) {
        dashboard.value = { ...dashboard.value, loaded: false };
        addLog('系统', `工作台统计加载失败（回退本地估算）：${e.message}`);
      }
    };

    // 登录后按角色加载后端数据
    const loadAllData = async () => {
      await loadProjects();
      const role = currentUser.value?.role;
      const tasks = [loadDict(), loadDashboard()];
      if (role === 'admin') tasks.push(loadUsers());
      await Promise.all(tasks.map((p) => p.catch(() => {})));
      nextTick(() => renderCharts());
    };

    // 当前项目ID（用于上传文件）
    const currentProjectId = ref(null);

    // ── 文件选择器工具函数 ──
    const pickFile = (accept) => {
      return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = accept;
        input.onchange = (e) => {
          resolve(e.target.files[0] || null);
        };
        input.click();
      });
    };

    // ── Word 合同上传（真实调用后端 API） ──
    const simulateWordOCR = async () => {
      const file = await pickFile('.docx');
      if (!file) return;

      isScanning.value = true;
      ocrSuccess.value = false;
      addLog('OCR扫描', `正在上传 Word 合同: ${file.name} (${(file.size / 1024).toFixed(1)}KB)...`);

      try {
        // 先创建项目草稿
        const projData = await api('/projects/register', {
          method: 'POST',
          body: {
            project_name: '待识别项目',
            contract_no: null,
            contract_amount: null,
            customer_name: null,
            project_type: null,
            sign_date: null,
            description: null,
          },
        });
        currentProjectId.value = projData.id;
        addLog('数据库', `项目草稿已创建，ID: ${projData.id}`);

        // 上传 Word 文件
        const formData = new FormData();
        formData.append('file', file);

        addLog('OCR扫描', '正在解析 Word 合同文本... 抓取参数: [项目名称]、[项目金额]、[合同编号]、[签订日期]');

        const uploadData = await api(`/projects/${projData.id}/upload-word`, {
          method: 'POST',
          body: formData,
          isForm: true,
        });
        const extracted = uploadData.ocr_result?.extracted || {};

        // 自动提取信息回填表单
        formProject.value.name = extracted.project_name || '待识别项目';
        formProject.value.code = extracted.contract_no || '';
        formProject.value.amount = extracted.contract_amount ? parseFloat(extracted.contract_amount) : 0;
        formProject.value.date = extracted.sign_date || '';
        formProject.value.client = extracted.customer_name || '';
        formProject.value.type = '软件开发';
        formProject.value.pm = '—';
        formProject.value.description = '';
        formProject.value.expenses = [];

        // 更新项目名称（回填后同步到后端）
        if (extracted.project_name) {
          await api(`/projects/${projData.id}`, {
            method: 'PUT',
            body: {
              project_name: extracted.project_name,
              contract_no: extracted.contract_no || null,
              contract_amount: extracted.contract_amount ? parseFloat(extracted.contract_amount) : null,
              customer_name: extracted.customer_name || null,
              sign_date: extracted.sign_date || null,
            },
          }).catch(() => {});
        }

        isScanning.value = false;
        ocrSuccess.value = true;

        const fields = [];
        if (extracted.project_name) fields.push('项目名称');
        if (extracted.contract_amount) fields.push('合同金额');
        if (extracted.contract_no) fields.push('合同编号');
        if (extracted.sign_date) fields.push('签订日期');
        if (extracted.customer_name) fields.push('客户名称');

        addLog('OCR扫描', `Word 合同解析成功。识别到字段: [${fields.join('、') || '无'}]。已自动映射至表单。`);
        currentStep.value = 2;

      } catch (err) {
        isScanning.value = false;
        addLog('系统', `上传失败: ${err.message}`);
        alert('Word 合同上传失败: ' + err.message);
      }
    };

    const nextToSeal = () => {
      currentStep.value = 3;
      addLog('系统', 'Word 合同基本信息已保存。请继续上传盖章的 PDF 扫描件进行印章与金额校验。');
    };

    // ── PDF 盖章件上传（真实调用后端 API） ──
    const uploadSealPDF = async () => {
      const file = await pickFile('.pdf');
      if (!file) return;

      if (!currentProjectId.value) {
        alert('请先上传 Word 合同或保存项目草稿！');
        return;
      }

      addLog('OCR扫描', `正在上传盖章 PDF: ${file.name} (${(file.size / 1024).toFixed(1)}KB)...`);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const uploadData = await api(`/projects/${currentProjectId.value}/upload-pdf`, {
          method: 'POST',
          body: formData,
          isForm: true,
        });
        formProject.value.contractFile = file.name;
        formProject.value.contractVersion = uploadData.version || 1;

        // 保存 OCR 结果用于后续校验
        window._pdfOcrResult = uploadData.ocr_result;

        addLog('OCR扫描', `PDF 盖章件上传成功 (版本 v${uploadData.version || 1})。OCR 识别完成，已归档锁定。`);

      } catch (err) {
        addLog('系统', `PDF 上传失败: ${err.message}`);
        alert('PDF 合同上传失败: ' + err.message);
      }
    };

    // 支出预算流水管理
    const addExpenseItem = () => {
      if (!newExpense.value.desc || !newExpense.value.amount || !newExpense.value.date) return;
      formProject.value.expenses.push({
        desc: newExpense.value.desc,
        amount: parseFloat(newExpense.value.amount),
        date: newExpense.value.date
      });
      newExpense.value = { desc: '', amount: '', date: '' };
      addLog('数据库', '已记录新增的项目前期支出预算流水。');
    };

    const removeExpenseItem = (idx) => {
      formProject.value.expenses.splice(idx, 1);
    };

    const totalFormExpenses = computed(() => {
      return formProject.value.expenses.reduce((sum, item) => sum + item.amount, 0);
    });

    const nextToVerify = async () => {
      if (!formProject.value.contractFile) {
        alert('请先上传盖章的 PDF 合同文件！');
        return;
      }
      if (!currentProjectId.value) {
        alert('项目未创建，请先上传 Word 合同！');
        return;
      }

      currentStep.value = 4;
      addLog('OCR比对', '正在执行双版本合同结构文本校验（Word 录入值对比 PDF 扫描解析结果）...');

      // 调用后端校验接口
      try {
        const data = await api(`/projects/${currentProjectId.value}/verify`, { method: 'POST' });
        verifyDiffs.value = (data.diffs || []).map(d => ({ ...d, accepted: false }));
        verifyOcrRaw.value = data.ocr_raw || {};

        if (verifyDiffs.value.length === 0) {
          addLog('OCR比对', '校验通过！OCR 识别结果与录入信息完全一致，无差异项。');
        } else {
          addLog('OCR比对', `检测到 ${verifyDiffs.value.length} 处差异，请人工确认。`);
        }
      } catch (err) {
        // 不再注入任何假数据：校验失败如实报错并退回上一步，由用户重试。
        addLog('OCR比对', `校验请求失败：${err.message}`);
        verifyDiffs.value = [];
        verifyOcrRaw.value = {};
        currentStep.value = 3;
        alert('合同校验失败：' + err.message + '\n请确认已上传盖章 PDF 合同且后端服务正常后重试。');
      }
    };

    // 印章校验与差异比对确认
    const verifyRemark = ref('');
    const verifyDiffs = ref([]);
    const verifyOcrRaw = ref({});

    const comparisonRows = computed(() => {
      const fields = [
        { key: 'contract_amount', label: '合同金额' },
        { key: 'sign_date', label: '签订日期' },
        { key: 'project_name', label: '项目名称' },
        { key: 'contract_no', label: '合同编号' },
        { key: 'customer_name', label: '客户名称' }
      ];

      return fields.map(f => {
        const diff = verifyDiffs.value.find(d => d.field_name === f.key);
        
        let wordVal = '';
        if (f.key === 'contract_amount') {
          wordVal = formProject.value.amount !== undefined && formProject.value.amount !== null
            ? parseFloat(formProject.value.amount).toFixed(2) + ' 元'
            : '';
        } else if (f.key === 'sign_date') {
          wordVal = formProject.value.date || '';
        } else if (f.key === 'project_name') {
          wordVal = formProject.value.name || '';
        } else if (f.key === 'contract_no') {
          wordVal = formProject.value.code || '';
        } else if (f.key === 'customer_name') {
          wordVal = formProject.value.client || '';
        }

        let ocrVal = '';
        if (diff) {
          ocrVal = diff.ocr_value || '';
        } else {
          const rawOcr = verifyOcrRaw.value[f.key];
          if (rawOcr !== undefined && rawOcr !== null && rawOcr !== '') {
            ocrVal = rawOcr;
          } else {
            ocrVal = wordVal;
          }
        }

        if (f.key === 'contract_amount' && ocrVal && !ocrVal.endsWith('元') && !isNaN(parseFloat(ocrVal.replace(/[,，¥￥\s]/g, '')))) {
          ocrVal = ocrVal + ' 元';
        }

        let statusText = '一致';
        let statusClass = 'match';

        if (diff) {
          if (diff.diff_type === 'format') {
            statusText = '格式差异';
            statusClass = 'format-diff';
          } else if (diff.diff_type === 'missing') {
            statusText = '缺失';
            statusClass = 'mismatch';
          } else {
            statusText = '不匹配';
            statusClass = 'mismatch';
          }
        }

        return {
          key: f.key,
          label: f.label,
          ocrVal,
          wordVal,
          statusText,
          statusClass,
          isDiff: !!diff,
          diffItem: diff
        };
      });
    });

    const startEditProject = (proj) => {
      activeEditProject.value = proj;
      // 关联后端项目 ID，使「暂存草稿/重新提交」作用于真实记录
      currentProjectId.value = proj.id;
      formProject.value = {
        name: proj.name,
        code: proj.code,
        amount: proj.amount,
        date: proj.date,
        client: proj.client,
        type: proj.type,
        pm: proj.pm,
        description: proj.description,
        expenses: [...(proj.expenses || [])],
        invoices: proj.invoices || [],
        payments: proj.payments || [],
        contractVersion: (proj.contractVersion || 1) + 1,
        contractFile: proj.contractFile || '',
        acceptanceReport: proj.acceptanceReport || '',
        status: proj.status,
        created_by: proj.created_by,
        rejectReason: proj.rejectReason || ''
      };
      
      currentStep.value = 2; // 直接跳过上传Word，进入比对和要素确认阶段
      ocrSuccess.value = true;

      activeTab.value = 'register';
      addLog('系统', `开始修改并重新发起立项，项目: ${proj.name} (${proj.code})`);
    };

    const saveAsDraft = async () => {
      if (!formProject.value.name) {
        alert('请至少填写项目名称，方可暂存为草稿！');
        return;
      }

      const payload = {
        project_name: formProject.value.name,
        contract_no: formProject.value.code || null,
        contract_amount: formProject.value.amount || null,
        customer_name: formProject.value.client || null,
        project_type: formProject.value.type || null,
        sign_date: formProject.value.date || null,
        description: formProject.value.description || null,
      };

      try {
        if (currentProjectId.value) {
          // 已存在后端记录（Word 上传创建 / 编辑已驳回项目）→ 更新字段，状态保持草稿
          await api(`/projects/${currentProjectId.value}`, { method: 'PUT', body: payload });
        } else {
          // 手工填写、未走 Word 上传 → 直接登记一条草稿
          const created = await api('/projects/register', { method: 'POST', body: payload });
          currentProjectId.value = created.id;
        }
        addLog('数据库', `项目"${formProject.value.name}"已暂存为草稿。`);
        await loadProjects();
        resetForm();
        activeTab.value = 'projects';
      } catch (err) {
        addLog('系统', `暂存草稿失败：${err.message}`);
        alert('暂存草稿失败：' + err.message);
      }
    };

    const submitProjectRegistration = async () => {
      if (verifyDiffs.value.some(d => !d.accepted)) {
        alert('必须人工核对并勾选所有提取差异项后，方可提起立项！');
        return;
      }

      if (!currentProjectId.value) {
        alert('项目未创建，请先完成合同上传流程！');
        return;
      }

      try {
        // 更新项目信息到后端（把差异核对说明并入描述，供审核人真实查看）
        const remarkLine = verifyRemark.value ? ('差异核对说明：' + verifyRemark.value) : '';
        const mergedDesc = [formProject.value.description, remarkLine].filter(Boolean).join('\n') || null;
        await api(`/projects/${currentProjectId.value}`, {
          method: 'PUT',
          body: {
            project_name: formProject.value.name,
            contract_no: formProject.value.code || null,
            contract_amount: formProject.value.amount || null,
            customer_name: formProject.value.client || null,
            sign_date: formProject.value.date || null,
            description: mergedDesc,
          },
        }).catch(() => {});

        // 提交立项申请
        await api(`/projects/${currentProjectId.value}/submit`, { method: 'POST' });

        addLog('数据库', `项目"${formProject.value.name}"立项已发起，提交审核流。当前等待管理员终审。`);

        // 从后端重新加载项目列表（真实状态）
        await loadProjects();

        resetForm();
        activeTab.value = 'projects';

      } catch (err) {
        addLog('系统', `提交失败: ${err.message}`);
        alert('提交立项失败: ' + err.message);
      }
    };

    const resetForm = () => {
      formProject.value = {
        name: '',
        code: '',
        amount: 0,
        date: '',
        client: '',
        type: '软件开发',
        pm: '—',
        description: '',
        expenses: [],
        invoices: [],
        payments: [],
        contractVersion: 1,
        contractFile: '',
        acceptanceReport: '',
        status: '草稿',
        created_by: '',
        rejectReason: ''
      };
      currentStep.value = 1;
      ocrSuccess.value = false;
      activeEditProject.value = null;
      currentProjectId.value = null;
      verifyDiffs.value = [];
      verifyOcrRaw.value = {};
      verifyRemark.value = '';
    };

    // 字段中文名映射
    const fieldLabelCN = (field) => {
      const map = {
        project_name: '项目名称',
        contract_amount: '合同金额',
        contract_no: '合同编号',
        sign_date: '签订日期',
        customer_name: '客户名称',
      };
      return map[field] || field;
    };

    // ── 审批流程 ──
    const reviewProject = ref(null);
    const adminRejectReason = ref('');

    const openAuditDetails = (proj) => {
      reviewProject.value = proj;
      adminRejectReason.value = '';
    };

    const auditProject = async (status) => {
      if (!reviewProject.value) return;
      if (status === '已驳回' && !adminRejectReason.value) {
        alert('驳回时必须填写原因反馈给商务经理！');
        return;
      }
      const result = status === '已立项' ? 'approved' : 'rejected';
      const proj = reviewProject.value;
      try {
        await api(`/projects/${proj.id}/audit`, {
          method: 'POST',
          body: { result, reason: result === 'rejected' ? adminRejectReason.value : null },
        });
        addLog('数据库', `立项审核决策执行成功。项目: ${proj.code} 决议结果: ${status}`);
        reviewProject.value = null;
        adminRejectReason.value = '';
        await loadProjects();
        nextTick(() => renderCharts());
      } catch (err) {
        addLog('系统', `审核提交失败：${err.message}`);
        alert('审核提交失败：' + err.message);
      }
    };

    // ── 项目经理端（PM 执行） ──
    const showAcceptanceReportModal = ref(null);
    const pickedReportFile = ref(null);   // 已选择的验收报告文件

    const pickReportFile = async () => {
      const f = await pickFile('.pdf,.docx,.jpg,.jpeg,.png');
      if (f) {
        pickedReportFile.value = f;
        addLog('系统', `已选择验收报告文件：${f.name}`);
      }
    };

    const submitClosingRequest = async (proj) => {
      try {
        const fd = new FormData();
        fd.append('close_date', new Date().toISOString().split('T')[0]);
        fd.append('close_reason', '项目已完工，提交验收结项申请');
        if (pickedReportFile.value) fd.append('file', pickedReportFile.value);

        await api(`/projects/${proj.id}/close`, { method: 'POST', body: fd, isForm: true });
        addLog('系统', `项目经理已向财务提起结项申请${pickedReportFile.value ? '（验收报告: ' + pickedReportFile.value.name + '）' : ''}。`);
        showAcceptanceReportModal.value = null;
        pickedReportFile.value = null;
        await loadProjects();
      } catch (err) {
        addLog('系统', `结项申请提交失败：${err.message}`);
        alert('结项申请提交失败：' + err.message);
      }
    };

    // ── 财务总监端（开票与回款） ──
    const pickedInvoiceFile = ref(null);   // 待上传的发票图片/PDF
    const invoiceScanning = ref(false);    // 发票 OCR 识别中标志
    const pickedPaymentFile = ref(null);   // 待上传的回款凭证

    const triggerRecordFinance = (proj) => {
      selectedProjectForFinance.value = proj;
      pickedInvoiceFile.value = null;
      pickedPaymentFile.value = null;
      const remainInvoice = Math.max(0, proj.amount - totalInvoiced(proj));
      const remainPayment = Math.max(0, totalInvoiced(proj) - totalPaid(proj));
      tempInvoice.value = {
        amount: remainInvoice || '', code: '', date: new Date().toISOString().split('T')[0],
        unit: proj.client || '', buyer: proj.client || '', seller: '',
      };
      tempPayment.value = {
        amount: remainPayment || '', method: '银行转账', date: new Date().toISOString().split('T')[0],
      };
    };

    // 选择发票文件 → 调用后端独立 OCR 识别并自动回填开票表单
    const scanInvoice = async () => {
      const f = await pickFile('.jpg,.jpeg,.png,.pdf');
      if (!f) return;
      pickedInvoiceFile.value = f;
      invoiceScanning.value = true;
      isScanning.value = true;
      addLog('OCR扫描', `正在识别发票文件：${f.name} (${(f.size / 1024).toFixed(1)}KB)...`);
      try {
        const fd = new FormData();
        fd.append('file', f);
        const res = await api('/ocr/recognize', { method: 'POST', body: fd, isForm: true });
        const ex = res?.extracted || {};
        if (ex.amount) {
          const amt = parseFloat(String(ex.amount).replace(/,/g, ''));
          if (!isNaN(amt)) tempInvoice.value.amount = amt;
        }
        if (ex.invoice_no) tempInvoice.value.code = ex.invoice_no;
        if (ex.invoice_date) tempInvoice.value.date = ex.invoice_date;
        if (ex.buyer_name) tempInvoice.value.buyer = ex.buyer_name;
        if (ex.seller_name) tempInvoice.value.seller = ex.seller_name;
        const got = [
          ex.invoice_no && '发票号码', ex.amount && '金额',
          ex.invoice_date && '开票日期', ex.buyer_name && '购买方',
        ].filter(Boolean);
        addLog('OCR扫描', `发票识别完成，提取字段：${got.length ? got.join('、') : '无（请手动填写）'}。`);
      } catch (err) {
        addLog('系统', `发票 OCR 识别失败：${err.message}`);
        alert('发票识别失败：' + err.message);
      } finally {
        invoiceScanning.value = false;
        isScanning.value = false;
      }
    };

    // 选择回款凭证文件
    const pickPaymentVoucher = async () => {
      const f = await pickFile('.jpg,.jpeg,.png,.pdf');
      if (f) {
        pickedPaymentFile.value = f;
        addLog('系统', `已选择回款凭证：${f.name}`);
      }
    };

    const totalInvoiced = (proj) => {
      return proj.invoices?.reduce((sum, item) => sum + item.amount, 0) || 0;
    };

    const totalPaid = (proj) => {
      return proj.payments?.reduce((sum, item) => sum + item.amount, 0) || 0;
    };

    const recordInvoice = async () => {
      const proj = selectedProjectForFinance.value;
      if (!proj) return;
      if (!tempInvoice.value.amount) { alert('请填写开票金额'); return; }
      try {
        const fd = new FormData();
        fd.append('amount', tempInvoice.value.amount);
        fd.append('invoice_date', tempInvoice.value.date || new Date().toISOString().split('T')[0]);
        if (tempInvoice.value.code) fd.append('invoice_no', tempInvoice.value.code);
        if (tempInvoice.value.unit) fd.append('invoice_unit', tempInvoice.value.unit);
        if (tempInvoice.value.buyer) fd.append('buyer_name', tempInvoice.value.buyer);
        if (tempInvoice.value.seller) fd.append('seller_name', tempInvoice.value.seller);
        if (pickedInvoiceFile.value) fd.append('file', pickedInvoiceFile.value);

        await api(`/projects/${proj.id}/invoices`, { method: 'POST', body: fd, isForm: true });
        addLog('财务记账', `开票登记成功。发票号: ${tempInvoice.value.code || '—'}，金额: ¥${parseFloat(tempInvoice.value.amount).toLocaleString()}，项目: ${proj.code}`);
        pickedInvoiceFile.value = null;
        await refreshProjectFinance(proj);
        tempInvoice.value = { amount: '', code: '', date: new Date().toISOString().split('T')[0], unit: proj.client || '', buyer: proj.client || '', seller: '' };
        nextTick(() => renderCharts());
      } catch (err) {
        addLog('系统', `开票失败：${err.message}`);
        alert('开票失败：' + err.message);
      }
    };

    const recordPayment = async () => {
      const proj = selectedProjectForFinance.value;
      if (!proj) return;
      if (!tempPayment.value.amount) { alert('请填写回款金额'); return; }
      try {
        const fd = new FormData();
        fd.append('amount', tempPayment.value.amount);
        fd.append('payment_date', tempPayment.value.date || new Date().toISOString().split('T')[0]);
        if (tempPayment.value.method) fd.append('payment_method', tempPayment.value.method);
        if (pickedPaymentFile.value) fd.append('file', pickedPaymentFile.value);

        await api(`/projects/${proj.id}/payments`, { method: 'POST', body: fd, isForm: true });
        addLog('财务记账', `回款登记成功。金额: ¥${parseFloat(tempPayment.value.amount).toLocaleString()}，方式: ${tempPayment.value.method}，项目: ${proj.code}`);
        pickedPaymentFile.value = null;
        await refreshProjectFinance(proj);
        tempPayment.value = { amount: '', method: tempPayment.value.method || '银行转账', date: new Date().toISOString().split('T')[0] };
        nextTick(() => renderCharts());
      } catch (err) {
        addLog('系统', `回款登记失败：${err.message}`);
        alert('回款登记失败：' + err.message);
      }
    };

    const auditProjectClosing = async (proj, approve) => {
      try {
        await api(`/projects/${proj.id}/close/audit`, {
          method: 'POST',
          body: {
            result: approve ? 'approved' : 'rejected',
            reason: approve ? null : '财务复核退回，请核对验收材料后重新提交',
          },
        });
        addLog('财务审计', approve
          ? `财务终审通过。项目结项决议生效，编码: ${proj.code}`
          : `财务终审退回结项申请。项目: ${proj.code} 维持执行中状态。`);
        await loadProjects();
        nextTick(() => renderCharts());
      } catch (err) {
        addLog('系统', `结项审核失败：${err.message}`);
        alert('结项审核失败：' + err.message);
      }
    };

    // ── 财务查询汇总 + 报表导出（PPT slide 35） ──
    const queryYear = ref(new Date().getFullYear());
    const queryMonth = ref(0); // 0 = 全年，1-12 = 指定月度
    // 稳定的年度候选（以当前自然年为基准，避免选项随 queryYear 漂移）
    const yearOptions = computed(() => {
      const cy = new Date().getFullYear();
      return [cy, cy - 1, cy - 2, cy - 3];
    });
    let financeBarChart = null;
    let financePieChart = null;

    // 按所选年度/月度过滤的开票或回款金额合计（依据每条明细的真实日期）
    const sumInPeriod = (arr) => (arr || []).reduce((s, x) => {
      if (!x.date) return s;
      const d = new Date(x.date);
      if (isNaN(d.getTime())) return s;
      if (d.getFullYear() !== Number(queryYear.value)) return s;
      if (queryMonth.value && (d.getMonth() + 1) !== Number(queryMonth.value)) return s;
      return s + parseFloat(x.amount || 0);
    }, 0);

    // 回款方式选项（取自数据字典 PAYMENT_METHOD，缺省给常用项）
    const paymentMethods = computed(() => {
      const fromDict = dictItems.value
        .filter(d => d.typeCode === 'payment_method')
        .map(d => d.name);
      return fromDict.length ? fromDict : ['银行转账', '支付宝商户', '现金', '支票'];
    });

    // 已立项/已结项项目在所选年度/月度内的开票回款汇总行
    const financeRows = computed(() => {
      return projects.value
        .filter(p => ['已立项', '已结项'].includes(p.status))
        .map(p => {
          const invoiced = sumInPeriod(p.invoices);
          const paid = sumInPeriod(p.payments);
          return {
            code: p.code, name: p.name, amount: p.amount,
            invoiced, paid, receivable: Math.max(0, invoiced - paid),
          };
        });
    });

    const financeTotals = computed(() => {
      const rows = financeRows.value;
      return {
        contract: rows.reduce((s, r) => s + r.amount, 0),
        invoiced: rows.reduce((s, r) => s + r.invoiced, 0),
        paid: rows.reduce((s, r) => s + r.paid, 0),
        receivable: rows.reduce((s, r) => s + r.receivable, 0),
      };
    });

    const renderFinanceCharts = () => {
      const rows = financeRows.value;
      const barDom = document.getElementById('financeQueryBarChart');
      const pieDom = document.getElementById('financeQueryPieChart');
      if (barDom) {
        if (financeBarChart) financeBarChart.dispose();
        financeBarChart = echarts.init(barDom, 'dark');
        financeBarChart.setOption({
          backgroundColor: 'transparent',
          tooltip: { trigger: 'axis' },
          legend: { data: ['合同额', '累计开票', '累计回款'], textStyle: { color: '#94a3b8' } },
          grid: { left: 60, right: 20, top: 40, bottom: 80 },
          xAxis: { type: 'category', data: rows.map(r => r.name),
                   axisLabel: { color: '#64748b', interval: 0, rotate: 28, fontSize: 10 } },
          yAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e293b' } } },
          series: [
            { name: '合同额', type: 'bar', data: rows.map(r => r.amount), itemStyle: { color: '#06b6d4' } },
            { name: '累计开票', type: 'bar', data: rows.map(r => r.invoiced), itemStyle: { color: '#a855f7' } },
            { name: '累计回款', type: 'bar', data: rows.map(r => r.paid), itemStyle: { color: '#10b981' } },
          ],
        });
      }
      if (pieDom) {
        if (financePieChart) financePieChart.dispose();
        financePieChart = echarts.init(pieDom, 'dark');
        const t = financeTotals.value;
        financePieChart.setOption({
          backgroundColor: 'transparent',
          tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
          legend: { bottom: 0, textStyle: { color: '#94a3b8' } },
          series: [{
            type: 'pie', radius: ['40%', '70%'], center: ['50%', '44%'],
            data: [
              { value: +t.paid.toFixed(2), name: '已回款', itemStyle: { color: '#10b981' } },
              { value: +Math.max(0, t.invoiced - t.paid).toFixed(2), name: '已开票未回款', itemStyle: { color: '#f59e0b' } },
              { value: +Math.max(0, t.contract - t.invoiced).toFixed(2), name: '未开票额度', itemStyle: { color: '#475569' } },
            ],
            label: { color: '#cbd5e1' },
          }],
        });
      }
    };

    const exportFinanceExcel = () => {
      if (typeof XLSX === 'undefined') { alert('Excel 导出组件未加载，请检查网络'); return; }
      const rows = financeRows.value.map(r => ({
        立项编号: r.code, 项目名称: r.name, 合同金额: r.amount,
        累计开票: r.invoiced, 累计回款: r.paid, 应收余额: r.receivable,
      }));
      const t = financeTotals.value;
      rows.push({ 立项编号: '合计', 项目名称: '', 合同金额: t.contract, 累计开票: t.invoiced, 累计回款: t.paid, 应收余额: t.receivable });
      const ws = XLSX.utils.json_to_sheet(rows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '开票回款汇总');
      XLSX.writeFile(wb, `财务开票回款汇总_${queryYear.value}.xlsx`);
      addLog('系统', '已导出开票回款汇总 Excel 报表。');
    };

    const exportFinancePDF = () => {
      const JsPDF = (window.jspdf || {}).jsPDF;
      if (!JsPDF) { alert('PDF 导出组件未加载，请检查网络'); return; }
      const doc = new JsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
      doc.setFontSize(16);
      doc.text(`Finance Billing & Collection Report  ${queryYear.value}`, 40, 40);
      let y = 56;
      // ECharts 图（canvas 渲染，含中文，作为图片嵌入不受字体限制）
      try {
        if (financeBarChart) doc.addImage(financeBarChart.getDataURL({ pixelRatio: 2, backgroundColor: '#0f172a' }), 'PNG', 40, y, 470, 210);
        if (financePieChart) doc.addImage(financePieChart.getDataURL({ pixelRatio: 2, backgroundColor: '#0f172a' }), 'PNG', 530, y, 270, 210);
      } catch (e) { /* 图表未就绪则跳过 */ }
      y += 230;
      doc.setFontSize(10);
      doc.text('Code           Contract        Invoiced        Paid            Receivable', 40, y);
      y += 14;
      const t = financeTotals.value;
      financeRows.value.forEach(r => {
        if (y > 540) { doc.addPage(); y = 40; }
        doc.text(
          `${(r.code || '').padEnd(14)} ${String(r.amount).padEnd(14)} ${String(r.invoiced).padEnd(14)} ${String(r.paid).padEnd(14)} ${r.receivable}`,
          40, y,
        );
        y += 14;
      });
      if (y > 540) { doc.addPage(); y = 40; }
      doc.text(`TOTAL          ${t.contract}        ${t.invoiced}        ${t.paid}        ${t.receivable}`, 40, y + 6);
      doc.save(`Finance_Report_${queryYear.value}.pdf`);
      addLog('系统', '已导出开票回款汇总 PDF 报表。');
    };

    // ── 数据字典 ──
    const newDictCode = ref('');
    const newDictName = ref('');
    const newDictType = ref('project_type');

    const addDictItem = async () => {
      if (!newDictCode.value || !newDictName.value) { alert('请填写唯一代号与显示名称'); return; }
      const type = dictTypes.value.find(t => t.code === newDictType.value);
      if (!type) { alert(`字典类型 ${newDictType.value} 不存在，请先在后端初始化该类型`); return; }
      try {
        await api(`/dict/types/${type.id}/items`, {
          method: 'POST',
          body: {
            item_label: newDictName.value,
            item_value: newDictCode.value,
            sort_order: dictItems.value.filter(d => d.typeCode === newDictType.value).length + 1,
          },
        });
        addLog('系统配置', `已新增数据字典项: ${newDictName.value} (${newDictCode.value})`);
        newDictCode.value = '';
        newDictName.value = '';
        await loadDict();
      } catch (err) {
        addLog('系统', `新增字典项失败：${err.message}`);
        alert('新增字典项失败：' + err.message);
      }
    };

    const deleteDictItem = async (id) => {
      try {
        await api(`/dict/items/${id}`, { method: 'DELETE' });
        addLog('系统配置', '已删除选中的数据字典条目。');
        await loadDict();
      } catch (err) {
        addLog('系统', `删除字典项失败：${err.message}`);
        alert('删除字典项失败：' + err.message);
      }
    };

    // ── 用户控制 ──
    const newUserForm = ref({ username: '', name: '', role: 'pm' });
    const addUser = async () => {
      if (!newUserForm.value.username || !newUserForm.value.name) { alert('请填写登录账号与真实姓名'); return; }
      try {
        await api('/users', {
          method: 'POST',
          body: {
            username: newUserForm.value.username,
            password: '123456',
            real_name: newUserForm.value.name,
            role: newUserForm.value.role,
          },
        });
        addLog('系统配置', `新用户注册成功。姓名: ${newUserForm.value.name}，默认密码已设为 123456`);
        newUserForm.value = { username: '', name: '', role: 'pm' };
        await loadUsers();
      } catch (err) {
        addLog('系统', `新增用户失败：${err.message}`);
        alert('新增用户失败：' + err.message);
      }
    };

    const toggleUserActive = async (user) => {
      try {
        const res = await api(`/users/${user.id}/status`, { method: 'PUT' });
        user.active = res?.status === 1;
        addLog('系统配置', `已修改用户 "${user.name}" 的系统激活状态为：${user.active ? '启用' : '挂起冻结'}`);
      } catch (err) {
        addLog('系统', `修改用户状态失败：${err.message}`);
        alert('修改用户状态失败：' + err.message);
      }
    };

    // ── 3D 旋转及倾斜效果监听 ──
    const init3DCardTilt = () => {
      document.addEventListener('mousemove', (e) => {
        const cards = document.querySelectorAll('.tilt-card');
        cards.forEach(card => {
          const rect = card.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          
          if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const angleX = -((y - centerY) / centerY) * 10;
            const angleY = ((x - centerX) / centerX) * 10;
            card.style.transform = `rotateX(${angleX}deg) rotateY(${angleY}deg) translateZ(10px)`;
          } else {
            card.style.transform = 'rotateX(0deg) rotateY(0deg) translateZ(0px)';
          }
        });
      });
    };

    // ── ECharts 霓虹主题数据渲染 ──
    let chartInstanceTrend = null;
    let chartInstanceStatus = null;

    const renderCharts = () => {
      const trendDom = document.getElementById('billingCollectionTrendChart');
      const statusDom = document.getElementById('projectStatusChart');

      if (trendDom) {
        if (chartInstanceTrend) chartInstanceTrend.dispose();
        chartInstanceTrend = echarts.init(trendDom, 'dark');

        // 近 6 个月开票/回款走势：优先后端 /dashboard/trend，回退客户端
        const months = [];
        const invoiceData = [];
        const paymentData = [];
        const bt = dashboard.value.loaded ? dashboard.value.trend : null;
        if (bt && bt.length) {
          bt.forEach(it => {
            months.push((parseInt((it.month || '').split('-')[1], 10) || '') + '月');
            invoiceData.push(+it.invoice_amount || 0);
            paymentData.push(+it.payment_amount || 0);
          });
        } else {
          const now = new Date();
          for (let i = 5; i >= 0; i--) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            months.push((d.getMonth() + 1) + '月');
            let mi = 0, mp = 0;
            projects.value.forEach(p => {
              if (['已立项', '已结项'].includes(p.status)) {
                p.invoices?.forEach(inv => {
                  const dt = new Date(inv.date);
                  if (dt.getFullYear() === d.getFullYear() && dt.getMonth() === d.getMonth()) mi += parseFloat(inv.amount || 0);
                });
                p.payments?.forEach(pay => {
                  const dt = new Date(pay.date);
                  if (dt.getFullYear() === d.getFullYear() && dt.getMonth() === d.getMonth()) mp += parseFloat(pay.amount || 0);
                });
              }
            });
            invoiceData.push(mi); paymentData.push(mp);
          }
        }

        const option = {
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(11, 14, 22, 0.95)',
            borderColor: 'rgba(0, 242, 254, 0.3)',
            borderWidth: 1,
            textStyle: { color: '#f5f7fa', fontFamily: 'Outfit, sans-serif', fontSize: 12 },
            axisPointer: {
              type: 'line',
              lineStyle: { color: 'rgba(0, 242, 254, 0.4)', type: 'dashed' }
            },
            formatter: function(params) {
              let html = `<div style="padding: 4px 8px;">
                <div style="font-weight: bold; margin-bottom: 8px; color: #8c9ba5; font-size: 13px;">${params[0].name} 财务走势</div>`;
              params.forEach(p => {
                const color = p.seriesName === '开票额' ? '#00f2fe' : '#7f00ff';
                html += `<div style="display: flex; justify-content: space-between; gap: 24px; align-items: center; margin-top: 6px;">
                  <span style="display: flex; align-items: center; gap: 6px; color: #f5f7fa;">
                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: ${color}; box-shadow: 0 0 6px ${color};"></span>
                    ${p.seriesName}
                  </span>
                  <span style="font-weight: 700; color: ${color}; font-family: 'Fira Code', monospace;">¥ ${p.value.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</span>
                </div>`;
              });
              html += '</div>';
              return html;
            }
          },
          legend: {
            data: ['开票额', '回款额'],
            textStyle: { color: '#8c9ba5', fontFamily: 'Outfit, sans-serif' },
            right: '5%',
            top: '0%'
          },
          grid: { top: '15%', left: '3%', right: '3%', bottom: '5%', containLabel: true },
          xAxis: {
            type: 'category',
            data: months,
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
            axisLabel: { color: '#8c9ba5', fontFamily: 'Outfit, sans-serif', fontSize: 11 },
            axisTick: { show: false }
          },
          yAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.02)' } },
            axisLabel: { color: '#8c9ba5', fontFamily: 'Outfit, sans-serif', fontSize: 11 },
            axisLine: { show: false }
          },
          series: [
            {
              name: '开票额',
              type: 'bar',
              barWidth: '16',
              data: invoiceData,
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(0, 242, 254, 0.85)' },
                  { offset: 1, color: 'rgba(0, 180, 219, 0.15)' }
                ]),
                borderRadius: [6, 6, 0, 0],
                shadowColor: 'rgba(0, 242, 254, 0.3)',
                shadowBlur: 10
              },
              emphasis: {
                itemStyle: {
                  color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#00f2fe' },
                    { offset: 1, color: 'rgba(0, 242, 254, 0.4)' }
                  ]),
                  shadowBlur: 15,
                  shadowColor: 'rgba(0, 242, 254, 0.6)'
                }
              }
            },
            {
              name: '回款额',
              type: 'line',
              smooth: true,
              showSymbol: false,
              data: paymentData,
              lineStyle: { 
                width: 4, 
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                  { offset: 0, color: '#7f00ff' },
                  { offset: 1, color: '#b92b27' }
                ]),
                shadowColor: 'rgba(127, 0, 255, 0.4)', 
                shadowBlur: 12,
                shadowOffsetY: 4
              },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(127, 0, 255, 0.2)' },
                  { offset: 1, color: 'rgba(127, 0, 255, 0)' }
                ])
              },
              symbol: 'circle',
              symbolSize: 8,
              itemStyle: {
                color: '#7f00ff',
                borderColor: '#fff',
                borderWidth: 2,
                shadowColor: 'rgba(127, 0, 255, 0.8)',
                shadowBlur: 8
              },
              emphasis: {
                scale: true,
                lineStyle: { width: 5 }
              }
            }
          ]
        };
        chartInstanceTrend.setOption(option);
      }

      if (statusDom) {
        if (chartInstanceStatus) chartInstanceStatus.dispose();
        chartInstanceStatus = echarts.init(statusDom, 'dark');

        const sdb = dashboard.value.loaded ? dashboard.value.statusDist : null;
        const draft    = sdb ? (sdb.draft || 0)         : projects.value.filter(p => p.status === '草稿').length;
        const pending  = sdb ? (sdb.pending_audit || 0) : projects.value.filter(p => p.status === '待审核').length;
        const approved = sdb ? (sdb.approved || 0)      : projects.value.filter(p => p.status === '已立项').length;
        const closed   = sdb ? (sdb.closed || 0)        : projects.value.filter(p => p.status === '已结项').length;
        const total = draft + pending + approved + closed;

        const option = {
          backgroundColor: 'transparent',
          title: {
            text: total,
            subtext: '立项总数',
            left: 'center',
            top: '40%',
            textStyle: {
              color: '#f5f7fa',
              fontSize: 28,
              fontWeight: '800',
              fontFamily: 'Outfit, sans-serif'
            },
            subtextStyle: {
              color: '#8c9ba5',
              fontSize: 12,
              fontFamily: 'Outfit, sans-serif',
              fontWeight: 'normal',
              align: 'center'
            }
          },
          tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(11, 14, 22, 0.95)',
            borderColor: 'rgba(0, 242, 254, 0.3)',
            borderWidth: 1,
            textStyle: { color: '#f5f7fa', fontFamily: 'Outfit, sans-serif', fontSize: 12 },
            formatter: function(params) {
              const startColor = params.color.colorStops ? params.color.colorStops[0].color : params.color;
              return `<div style="padding: 6px 10px; text-align: center;">
                <div style="font-weight: 700; color: ${startColor}; font-size: 14px; margin-bottom: 4px;">
                  <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: ${startColor}; margin-right: 6px; box-shadow: 0 0 6px ${startColor};"></span>
                  ${params.name}
                </div>
                <div style="font-size: 16px; font-weight: bold; color: #f5f7fa; margin: 4px 0;">${params.value} <span style="font-size: 11px; color: #8c9ba5;">个项目</span></div>
                <div style="font-size: 11px; color: #8c9ba5;">占比: ${params.percent}%</div>
              </div>`;
            }
          },
          legend: {
            orient: 'horizontal',
            bottom: '0%',
            left: 'center',
            itemWidth: 10,
            itemHeight: 10,
            itemGap: 16,
            textStyle: { color: '#8c9ba5', fontFamily: 'Outfit, sans-serif', fontSize: 11 }
          },
          series: [
            {
              name: '状态分布',
              type: 'pie',
              radius: ['52%', '72%'],
              center: ['50%', '48%'],
              avoidLabelOverlap: false,
              itemStyle: { 
                borderRadius: 8, 
                borderColor: '#08090c', 
                borderWidth: 3 
              },
              label: { show: false },
              emphasis: {
                scale: true,
                itemStyle: {
                  shadowBlur: 15,
                  shadowColor: 'rgba(0, 242, 254, 0.3)'
                }
              },
              data: [
                { 
                  value: draft, 
                  name: '草稿', 
                  itemStyle: { 
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: '#8c9ba5' },
                      { offset: 1, color: '#5c6b75' }
                    ]),
                    shadowColor: 'rgba(140, 155, 165, 0.3)',
                    shadowBlur: 8
                  } 
                },
                { 
                  value: pending, 
                  name: '待审核', 
                  itemStyle: { 
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: '#ffd54f' },
                      { offset: 1, color: '#ff8f00' }
                    ]),
                    shadowColor: 'rgba(255, 193, 7, 0.4)',
                    shadowBlur: 8
                  } 
                },
                { 
                  value: approved, 
                  name: '已立项', 
                  itemStyle: { 
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: '#00e676' },
                      { offset: 1, color: '#00b0ff' }
                    ]),
                    shadowColor: 'rgba(0, 230, 118, 0.4)',
                    shadowBlur: 8
                  } 
                },
                { 
                  value: closed, 
                  name: '已结项', 
                  itemStyle: { 
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: '#00f2fe' },
                      { offset: 1, color: '#7f00ff' }
                    ]),
                    shadowColor: 'rgba(0, 242, 254, 0.4)',
                    shadowBlur: 8
                  } 
                }
              ]
            }
          ]
        };
        chartInstanceStatus.setOption(option);
      }
    };

    // ── GSAP 动画控制系统 ──
    const animateLogin = () => {
      nextTick(() => {
        if (currentUser.value) return;
        gsap.killTweensOf('.space-grid-bg, .inline-flex, h1, p, .glass-panel.max-w-md');
        
        gsap.from('.space-grid-bg', {
          duration: 1.5,
          opacity: 0,
          ease: 'power1.out'
        });
        
        gsap.from('.inline-flex', {
          duration: 0.8,
          y: -40,
          scale: 0.6,
          opacity: 0,
          ease: 'back.out(1.5)'
        });
        
        gsap.from('h1, p', {
          duration: 0.6,
          y: 20,
          opacity: 0,
          stagger: 0.15,
          ease: 'power2.out'
        });
        
        gsap.from('.glass-panel.max-w-md', {
          duration: 0.8,
          y: 40,
          opacity: 0,
          delay: 0.25,
          ease: 'power3.out',
          clearProps: 'all'
        });
      });
    };

    const animateDashboard = () => {
      // 已登出时不执行仪表盘动画：其 killTweensOf('.glass-panel') 会误杀登录卡片
      // (.glass-panel.max-w-md) 的入场动画，导致登录表单停在 opacity:0 而消失。
      if (!currentUser.value) return;
      nextTick(() => {
        gsap.killTweensOf('.tilt-card, .glass-panel');
        
        gsap.from('.tilt-card', {
          duration: 0.6,
          y: 30,
          opacity: 0,
          stagger: 0.08,
          ease: 'power3.out',
          clearProps: 'all'
        });
        
        gsap.from('.glass-panel:has(#billingCollectionTrendChart), .glass-panel:has(#projectStatusChart)', {
          duration: 0.8,
          y: 30,
          opacity: 0,
          delay: 0.2,
          stagger: 0.1,
          ease: 'power2.out',
          clearProps: 'all'
        });
        
        gsap.from('.glass-panel:has(.terminal-panel)', {
          duration: 0.6,
          y: 20,
          opacity: 0,
          delay: 0.4,
          ease: 'power2.out',
          clearProps: 'all'
        });
        
        renderCharts();
      });
    };

    // 监听导航菜单切换动效
    watch(activeTab, (newTab) => {
      // 登出会把 activeTab 重置为 'dashboard'，此时无登录用户：
      // 跳过持久化与一切动画，避免 .glass-panel 系列动画/killTweens 干扰登录卡片入场。
      if (!currentUser.value) return;
      localStorage.setItem('pm_active_tab', newTab);
      sidebarOpen.value = false; // 移动端：切换菜单后自动收起抽屉
      if (newTab === 'dashboard') {
        animateDashboard();
      } else {
        nextTick(() => {
          gsap.from('.glass-panel', {
            duration: 0.6,
            y: 20,
            opacity: 0,
            stagger: 0.08,
            ease: 'power2.out',
            clearProps: 'all'
          });
        });
      }
    });

    // 监听扫描仪动画触发
    watch(isScanning, (scanning) => {
      if (scanning) {
        nextTick(() => {
          gsap.from('.scanner-container', {
            duration: 0.8,
            rotateX: 45,
            rotateY: -45,
            scale: 0.6,
            opacity: 0,
            ease: 'back.out(1.5)',
            clearProps: 'all'
          });
          gsap.from('.document-line', {
            duration: 0.5,
            width: 0,
            stagger: 0.08,
            ease: 'power2.out',
            delay: 0.3
          });
        });
      }
    });

    // ── 星空背景 Canvas 引擎 ──
    const initStarfield = () => {
      const canvas = document.getElementById('starfield');
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      let stars = [];
      let width = window.innerWidth;
      let height = window.innerHeight;
      
      canvas.width = width;
      canvas.height = height;
      
      class Star {
        constructor() {
          this.reset();
        }
        reset() {
          this.x = Math.random() * width;
          this.y = Math.random() * height;
          this.size = Math.random() * 1.5 + 0.4;
          this.speedX = (Math.random() - 0.5) * 0.08;
          this.speedY = (Math.random() - 0.5) * 0.08;
          this.opacity = Math.random() * 0.8 + 0.2;
          this.opacitySpeed = Math.random() * 0.01 + 0.003;
          this.twinkleFactor = Math.random() > 0.5 ? 1 : -1;
          this.currentCoords = { x: this.x, y: this.y, opacity: this.opacity };
        }
        update(mouseX, mouseY) {
          this.x += this.speedX;
          this.y += this.speedY;
          
          const dx = mouseX - width / 2;
          const dy = mouseY - height / 2;
          const targetX = this.x - dx * (this.size * 0.005);
          const targetY = this.y - dy * (this.size * 0.005);
          
          this.opacity += this.opacitySpeed * this.twinkleFactor;
          if (this.opacity > 1 || this.opacity < 0.2) {
            this.twinkleFactor *= -1;
          }
          
          if (this.x < 0) this.x = width;
          if (this.x > width) this.x = 0;
          if (this.y < 0) this.y = height;
          if (this.y > height) this.y = 0;
          
          this.currentCoords = { x: targetX, y: targetY, opacity: this.opacity };
          return this.currentCoords;
        }
      }
      
      const createStars = () => {
        stars = [];
        const numStars = Math.floor((width * height) / 8000);
        for (let i = 0; i < Math.min(numStars, 200); i++) {
          stars.push(new Star());
        }
      };
      
      createStars();
      
      window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        createStars();
      });
      
      let mouseX = width / 2;
      let mouseY = height / 2;
      
      window.addEventListener('mousemove', (e) => {
        // 1. Parallax shift for the background image (space_bg.png)
        const px = (e.clientX - width / 2) * 0.04;
        const py = (e.clientY - height / 2) * 0.04;
        gsap.to('#cosmic-backdrop', {
          x: -px,
          y: -py,
          duration: 2.0,
          ease: 'power1.out'
        });
        
        // 2. Parallax shift for the canvas stars
        gsap.to({x: mouseX, y: mouseY}, {
          x: e.clientX,
          y: e.clientY,
          duration: 1.5,
          ease: 'power1.out',
          onUpdate: function() {
            mouseX = this.targets()[0].x;
            mouseY = this.targets()[0].y;
          }
        });
      });
      
      let shootingStars = [];
      class ShootingStar {
        constructor() {
          this.reset();
        }
        reset() {
          this.x = Math.random() * width;
          this.y = Math.random() * (height * 0.5);
          this.length = Math.random() * 80 + 40;
          this.speed = Math.random() * 10 + 10;
          this.angle = Math.PI / 6 + (Math.random() * Math.PI / 12);
          this.dx = Math.cos(this.angle) * this.speed;
          this.dy = Math.sin(this.angle) * this.speed;
          this.opacity = 1;
          this.fadeSpeed = Math.random() * 0.02 + 0.01;
        }
        update() {
          this.x += this.dx;
          this.y += this.dy;
          this.opacity -= this.fadeSpeed;
        }
        draw() {
          if (this.opacity <= 0) return;
          ctx.save();
          ctx.strokeStyle = `rgba(0, 242, 254, ${this.opacity})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(this.x, this.y);
          ctx.lineTo(this.x - Math.cos(this.angle) * this.length, this.y - Math.sin(this.angle) * this.length);
          ctx.stroke();
          ctx.restore();
        }
      }
      
      const animate = () => {
        ctx.clearRect(0, 0, width, height);
        
        // 1. Draw Mouse Interactive Spotlight Glow
        const mouseGrad = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 250);
        mouseGrad.addColorStop(0, "rgba(0, 242, 254, 0.025)");
        mouseGrad.addColorStop(0.5, "rgba(127, 0, 255, 0.008)");
        mouseGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
        ctx.save();
        ctx.fillStyle = mouseGrad;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 250, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
        
        // 2. Draw Twinkling Stars
        stars.forEach(star => {
          const s = star.update(mouseX, mouseY);
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
          
          let color = `rgba(255, 255, 255, ${s.opacity})`;
          if (star.size > 1.4) {
            color = `rgba(0, 242, 254, ${s.opacity})`;
          } else if (star.size < 0.7) {
            color = `rgba(127, 0, 255, ${s.opacity})`;
          }
          
          ctx.fillStyle = color;
          
          if (s.size > 1.5) {
            ctx.shadowColor = '#00f2fe';
            ctx.shadowBlur = 6;
          } else {
            ctx.shadowBlur = 0;
          }
          
          ctx.fill();
        });
        
        // 3. Draw Connecting Lines (Star Web)
        for (let i = 0; i < stars.length; i++) {
          const s1 = stars[i].currentCoords;
          for (let j = i + 1; j < stars.length; j++) {
            const s2 = stars[j].currentCoords;
            const dx = s1.x - s2.x;
            const dy = s1.y - s2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < 85) {
              const opacity = (1 - dist / 85) * 0.08 * ((s1.opacity + s2.opacity) / 2);
              ctx.beginPath();
              ctx.moveTo(s1.x, s1.y);
              ctx.lineTo(s2.x, s2.y);
              ctx.strokeStyle = `rgba(0, 242, 254, ${opacity})`;
              ctx.lineWidth = 0.5;
              ctx.stroke();
            }
          }
        }
        
        // 4. Draw Shooting Stars
        if (Math.random() < 0.002 && shootingStars.length < 2) {
          shootingStars.push(new ShootingStar());
        }
        
        shootingStars.forEach((ss, idx) => {
          ss.update();
          ss.draw();
          if (ss.opacity <= 0) {
            shootingStars.splice(idx, 1);
          }
        });
        
        requestAnimationFrame(animate);
      };
      
      animate();
    };

    // ── 生命周期挂载 ──
    onMounted(() => {
      initDatabase();
      checkLoginSession();
      init3DCardTilt();
      initStarfield();
      
      window.addEventListener('resize', () => {
        chartInstanceTrend?.resize();
        chartInstanceStatus?.resize();
      });

      // 初始化入场动画
      if (!currentUser.value) {
        animateLogin();
      } else {
        animateDashboard();
      }
    });

    return {
      currentUser,
      activeTab,
      sidebarOpen,
      terminalLogs,
      projects,
      users,
      dictItems,
      dictTypes,
      auditLogs,
      
      // 登录系统
      loginForm,
      handleLogin,
      quickAutofillAndLogin,
      login: quickAutofillAndLogin,   // 模板侧边栏「快捷切换」调用 login()
      nextTick,                        // 模板中 nextTick(() => renderCharts())
      logout,
      enforceTabAccess,

      // OCR 解析与分步
      currentProjectId,
      isScanning,
      ocrSuccess,
      currentStep,
      formProject,
      newExpense,
      activeEditProject,
      startEditProject,
      simulateWordOCR,
      loadDashboard,
      nextToSeal,
      uploadSealPDF,
      addExpenseItem,
      removeExpenseItem,
      totalFormExpenses,
      nextToVerify,
      verifyRemark,
      verifyDiffs,
      verifyOcrRaw,
      comparisonRows,
      submitProjectRegistration,
      saveAsDraft,
      fieldLabelCN,
      resetForm,

      // 业务计算项
      stats,
      pendingAuditProjects,
      pendingCloseProjects,

      // 管理员审核
      reviewProject,
      adminRejectReason,
      openAuditDetails,
      auditProject,

      // PM 工程
      showAcceptanceReportModal,
      pickedReportFile,
      pickReportFile,
      submitClosingRequest,

      // 财务台账账本
      selectedProjectForFinance,
      tempInvoice,
      tempPayment,
      triggerRecordFinance,
      totalInvoiced,
      totalPaid,
      scanInvoice,
      invoiceScanning,
      pickedInvoiceFile,
      recordInvoice,
      pickPaymentVoucher,
      pickedPaymentFile,
      recordPayment,
      auditProjectClosing,

      // 财务查询汇总 + 导出
      queryYear,
      queryMonth,
      yearOptions,
      paymentMethods,
      financeRows,
      financeTotals,
      renderFinanceCharts,
      exportFinanceExcel,
      exportFinancePDF,

      // 字典控制
      newDictCode,
      newDictName,
      newDictType,
      addDictItem,
      deleteDictItem,

      // 用户管理
      newUserForm,
      addUser,
      toggleUserActive,

      renderCharts
    };
  }
}).mount('#app');
