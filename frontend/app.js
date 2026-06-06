/* ── app.js: Cosmos Void 逻辑控制中心 ── */

const { createApp, ref, computed, onMounted, nextTick, watch } = Vue;

createApp({
  setup() {
    // ── 用户认证、权限隔离与路由状态 ──
    const currentUser = ref(null);
    const activeTab = ref('dashboard');
    const terminalLogs = ref([]);

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
      pm: '王五',
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
    const dictTypes = ref([
      { code: 'PROJECT_TYPE', name: '项目类型' },
      { code: 'PAYMENT_METHOD', name: '回款方式' }
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

      // 3. 初始化项目档案数据
      const storedProjects = localStorage.getItem('pm_projects');
      if (storedProjects) {
        projects.value = JSON.parse(storedProjects);
      } else {
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
        nextTick(() => renderCharts());
      }
    };

    const handleLogin = () => {
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

      nextTick(() => renderCharts());
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
      localStorage.removeItem('pm_current_user');
      animateLogin();
    };

    // ── 权限强分离控制 ──
    const enforceTabAccess = () => {
      if (!currentUser.value) return;
      const role = currentUser.value.role;
      if (role === 'pm' && activeTab.value !== 'pm_projects' && activeTab.value !== 'dashboard') {
        activeTab.value = 'pm_projects';
      } else if (role === 'finance' && !['finance_ledger', 'close_audit', 'dashboard'].includes(activeTab.value)) {
        activeTab.value = 'finance_ledger';
      } else if (role === 'business' && !['register', 'projects', 'dashboard'].includes(activeTab.value)) {
        activeTab.value = 'projects';
      } else if (role === 'admin' && !['audit', 'users', 'dict', 'dashboard'].includes(activeTab.value)) {
        activeTab.value = 'dashboard';
      }
    };

    // ── 全局统计指标 ──
    const stats = computed(() => {
      const list = projects.value;
      const total = list.length;
      const initiated = list.filter(p => p.status === '已立项').length;
      const pendingAudit = list.filter(p => p.status === '待审核').length;
      const closed = list.filter(p => p.status === '已结项').length;

      let contractSum = 0;
      let invoicedSum = 0;
      let paymentSum = 0;

      list.forEach(p => {
        if (['已立项', '已结项'].includes(p.status)) {
          contractSum += parseFloat(p.amount || 0);
          p.invoices?.forEach(i => invoicedSum += parseFloat(i.amount || 0));
          p.payments?.forEach(py => paymentSum += parseFloat(py.amount || 0));
        }
      });

      const receivables = Math.max(0, invoicedSum - paymentSum);
      const invoiceRate = contractSum > 0 ? ((invoicedSum / contractSum) * 100).toFixed(1) : '0.0';
      const collectionRate = invoicedSum > 0 ? ((paymentSum / invoicedSum) * 100).toFixed(1) : '0.0';

      return {
        total,
        initiated,
        pendingAudit,
        closed,
        contractSum: contractSum.toLocaleString('zh-CN', { minimumFractionDigits: 2 }),
        invoicedSum: invoicedSum.toLocaleString('zh-CN', { minimumFractionDigits: 2 }),
        paymentSum: paymentSum.toLocaleString('zh-CN', { minimumFractionDigits: 2 }),
        receivables: receivables.toLocaleString('zh-CN', { minimumFractionDigits: 2 }),
        invoiceRate,
        collectionRate
      };
    });

    const pendingAuditProjects = computed(() => {
      return projects.value.filter(p => p.status === '待审核');
    });

    const pendingCloseProjects = computed(() => {
      return projects.value.filter(p => p.status === '已立项' && p.acceptanceReport !== '');
    });

    // ── 商务端 OCR 模拟 ──
    const simulateWordOCR = () => {
      isScanning.value = true;
      ocrSuccess.value = false;
      addLog('OCR扫描', '正在解析 Word 合同文本... 抓取参数: [项目名称]、[项目金额]、[合同编号]、[签订日期]');
      
      setTimeout(() => {
        isScanning.value = false;
        ocrSuccess.value = true;
        
        // 自动提取信息回填
        formProject.value.name = '智能大屏数据可视化系统';
        formProject.value.code = 'HT-2026-088';
        formProject.value.amount = 420000.00;
        formProject.value.date = '2026-06-05';
        formProject.value.client = '网信政务科技集团';
        formProject.value.type = '软件开发';
        formProject.value.pm = '王五';
        formProject.value.description = '政务大屏可视化项目研发合作协议。';
        formProject.value.expenses = [];
        
        addLog('OCR扫描', 'Word 原件文本扫描成功。置信度 100%。已自动映射至表单。');
        currentStep.value = 2;
      }, 3000);
    };

    const nextToSeal = () => {
      currentStep.value = 3;
      addLog('系统', 'Word 合同基本信息已保存。请继续上传盖章的 PDF 扫描件进行印章与金额校验。');
    };

    const mockUploadSealPDF = () => {
      formProject.value.contractFile = '智能大屏数据可视化系统-合同-已盖章.pdf';
      addLog('OCR扫描', '成功导入盖章版 PDF 合同扫描文件：' + formProject.value.contractFile);
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

    const nextToVerify = () => {
      if (!formProject.value.contractFile) {
        alert('请先上传盖章的 PDF 合同文件！');
        return;
      }
      currentStep.value = 4;
      addLog('OCR比对', '正在执行双版本合同结构文本校验（Word 录入值对比 PDF 扫描解析结果）...');
    };

    // 印章校验与差异比对确认
    const verifyAccept1 = ref(true);
    const verifyAccept2 = ref(true);
    const verifyRemark = ref('大写金额字符转换与日期书写差异属于格式原因，正本含义实际无出入，确认确认。');

    const startEditProject = (proj) => {
      activeEditProject.value = proj;
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
      verifyAccept1.value = false;
      verifyAccept2.value = false;
      
      activeTab.value = 'register';
      addLog('系统', `开始修改并重新发起立项，项目: ${proj.name} (${proj.code})`);
    };

    const saveAsDraft = () => {
      if (!formProject.value.name) {
        alert('请至少填写项目名称，方可暂存为草稿！');
        return;
      }
      
      if (activeEditProject.value) {
        const idx = projects.value.findIndex(p => p.id === activeEditProject.value.id);
        if (idx !== -1) {
          projects.value[idx] = {
            ...projects.value[idx],
            ...formProject.value,
            status: '草稿'
          };
          saveProjects();
          addLog('数据库', `项目草稿“${formProject.value.name}”修改已保存。`);
        }
      } else {
        const newProj = {
          ...formProject.value,
          id: Date.now(),
          status: '草稿',
          created_by: currentUser.value.username,
          invoices: [],
          payments: []
        };
        projects.value.push(newProj);
        saveProjects();
        addLog('数据库', `新项目“${newProj.name}”已成功暂存为草稿。`);
      }
      
      resetForm();
      activeTab.value = 'projects';
    };

    const submitProjectRegistration = () => {
      if (!verifyAccept1.value || !verifyAccept2.value) {
        alert('必须人工核对并勾选所有提取差异项后，方可提起立项！');
        return;
      }
      
      if (activeEditProject.value) {
        // 编辑重新提交模式
        const idx = projects.value.findIndex(p => p.id === activeEditProject.value.id);
        if (idx !== -1) {
          projects.value[idx] = {
            ...projects.value[idx],
            ...formProject.value,
            status: '待审核',
            rejectReason: '' // 清除被驳回的原委
          };
          saveProjects();
          addLog('数据库', `项目“${formProject.value.name}”修改已保存并重新提起立项审核流程。`);
        }
      } else {
        // 新增项目模式
        const newProj = {
          ...formProject.value,
          id: Date.now(),
          status: '待审核',
          created_by: currentUser.value.username,
          invoices: [],
          payments: []
        };
        projects.value.push(newProj);
        saveProjects();
        addLog('数据库', `项目“${newProj.name}”立项已发起，提交审核流。当前等待管理员终审。`);
      }
      
      resetForm();
      activeTab.value = 'projects';
    };

    const resetForm = () => {
      formProject.value = {
        name: '',
        code: '',
        amount: 0,
        date: '',
        client: '',
        type: '软件开发',
        pm: '王五',
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
      activeEditProject.value = null; // 确保清空编辑态
      verifyAccept1.value = true;
      verifyAccept2.value = true;
      verifyRemark.value = '大写金额字符转换与日期书写差异属于格式原因，正本含义实际无出入，确认确认。';
    };

    // ── 审批流程 ──
    const reviewProject = ref(null);
    const adminRejectReason = ref('');

    const openAuditDetails = (proj) => {
      reviewProject.value = proj;
      adminRejectReason.value = '';
    };

    const auditProject = (status) => {
      const idx = projects.value.findIndex(p => p.id === reviewProject.value.id);
      if (idx !== -1) {
        if (status === '已驳回' && !adminRejectReason.value) {
          alert('驳回时必须填写原因反馈给商务经理！');
          return;
        }
        projects.value[idx].status = status;
        projects.value[idx].rejectReason = status === '已驳回' ? adminRejectReason.value : '';
        saveProjects();
        addLog('数据库', `立项审核决策执行成功。项目: ${projects.value[idx].code} 决议结果: ${status}`);
        reviewProject.value = null;
      }
    };

    // ── 项目经理端（PM 执行） ──
    const showAcceptanceReportModal = ref(null);
    const mockReportFileName = ref('阶段完工验收报告_王五PM.pdf');

    const submitClosingRequest = (proj) => {
      const idx = projects.value.findIndex(p => p.id === proj.id);
      if (idx !== -1) {
        projects.value[idx].acceptanceReport = mockReportFileName.value;
        saveProjects();
        addLog('系统', `项目经理成功上传验收报告 [${mockReportFileName.value}] 并向财务提起结项申请。`);
        showAcceptanceReportModal.value = null;
      }
    };

    // ── 财务总监端（开票与回款） ──
    const triggerRecordFinance = (proj) => {
      selectedProjectForFinance.value = proj;
      tempInvoice.value = { amount: proj.amount - totalInvoiced(proj), code: 'INV-' + Math.floor(Math.random()*90000 + 10000), date: new Date().toISOString().split('T')[0] };
      tempPayment.value = { amount: proj.amount - totalPaid(proj), method: '银行转账', date: new Date().toISOString().split('T')[0] };
    };

    const totalInvoiced = (proj) => {
      return proj.invoices?.reduce((sum, item) => sum + item.amount, 0) || 0;
    };

    const totalPaid = (proj) => {
      return proj.payments?.reduce((sum, item) => sum + item.amount, 0) || 0;
    };

    const recordInvoice = () => {
      if (!tempInvoice.value.amount || !tempInvoice.value.code) return;
      const idx = projects.value.findIndex(p => p.id === selectedProjectForFinance.value.id);
      if (idx !== -1) {
        projects.value[idx].invoices.push({
          id: Date.now(),
          amount: parseFloat(tempInvoice.value.amount),
          code: tempInvoice.value.code,
          date: tempInvoice.value.date
        });
        saveProjects();
        addLog('财务记账', `成功记录发票开具。发票编号: ${tempInvoice.value.code}，金额: ¥${parseFloat(tempInvoice.value.amount).toLocaleString()}，隶属项目: ${selectedProjectForFinance.value.code}`);
        triggerRecordFinance(projects.value[idx]); // 重新加载
        nextTick(() => renderCharts());
      }
    };

    const recordPayment = () => {
      if (!tempPayment.value.amount) return;
      const idx = projects.value.findIndex(p => p.id === selectedProjectForFinance.value.id);
      if (idx !== -1) {
        projects.value[idx].payments.push({
          id: Date.now(),
          amount: parseFloat(tempPayment.value.amount),
          method: tempPayment.value.method,
          date: tempPayment.value.date
        });
        saveProjects();
        addLog('财务记账', `成功登记回款到账。回款金额: ¥${parseFloat(tempPayment.value.amount).toLocaleString()}，入账方式: ${tempPayment.value.method}，隶属项目: ${selectedProjectForFinance.value.code}`);
        triggerRecordFinance(projects.value[idx]); // 重新加载
        nextTick(() => renderCharts());
      }
    };

    const auditProjectClosing = (proj, approve) => {
      const idx = projects.value.findIndex(p => p.id === proj.id);
      if (idx !== -1) {
        if (approve) {
          projects.value[idx].status = '已结项';
          addLog('财务审计', `财务终审通过。项目结项决议生效，编码: ${proj.code}`);
        } else {
          projects.value[idx].acceptanceReport = '';
          addLog('财务审计', `财务终审退回结项申请。项目: ${proj.code} 重置回项目执行中状态。`);
        }
        saveProjects();
        nextTick(() => renderCharts());
      }
    };

    // ── 数据字典 ──
    const newDictCode = ref('');
    const newDictName = ref('');
    const newDictType = ref('PROJECT_TYPE');

    const addDictItem = () => {
      if (!newDictCode.value || !newDictName.value) return;
      const newItem = {
        id: Date.now(),
        typeCode: newDictType.value,
        code: newDictCode.value,
        name: newDictName.value,
        order: dictItems.value.filter(d => d.typeCode === newDictType.value).length + 1
      };
      dictItems.value.push(newItem);
      localStorage.setItem('pm_dict', JSON.stringify(dictItems.value));
      newDictCode.value = '';
      newDictName.value = '';
      addLog('系统配置', `已新增数据字典项: ${newItem.name} (${newItem.code})`);
    };

    const deleteDictItem = (id) => {
      dictItems.value = dictItems.value.filter(d => d.id !== id);
      localStorage.setItem('pm_dict', JSON.stringify(dictItems.value));
      addLog('系统配置', '已成功物理删除选中的数据字典条目。');
    };

    // ── 用户控制 ──
    const newUserForm = ref({ username: '', name: '', role: 'pm' });
    const addUser = () => {
      if (!newUserForm.value.username || !newUserForm.value.name) return;
      const u = {
        id: Date.now(),
        username: newUserForm.value.username,
        password: '123456', // 默认密码
        name: newUserForm.value.name,
        role: newUserForm.value.role,
        active: true
      };
      users.value.push(u);
      localStorage.setItem('pm_users', JSON.stringify(users.value));
      addLog('系统配置', `新用户注册成功。姓名: ${u.name}，默认密码已设为 123456`);
      newUserForm.value = { username: '', name: '', role: 'pm' };
    };

    const toggleUserActive = (user) => {
      user.active = !user.active;
      localStorage.setItem('pm_users', JSON.stringify(users.value));
      addLog('系统配置', `已修改用户 "${user.name}" 的系统激活状态为：${user.active ? '启用' : '挂起冻结'}`);
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

        // 动态计算近 6 个月开票/回款金额走势
        const months = [];
        const invoiceData = [];
        const paymentData = [];
        
        const now = new Date();
        for (let i = 5; i >= 0; i--) {
          const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
          const monthStr = (d.getMonth() + 1) + '月';
          months.push(monthStr);
          
          let monthInvoiceSum = 0;
          let monthPaymentSum = 0;
          
          projects.value.forEach(p => {
            if (['已立项', '已结项'].includes(p.status)) {
              p.invoices?.forEach(inv => {
                const invDate = new Date(inv.date);
                if (invDate.getFullYear() === d.getFullYear() && invDate.getMonth() === d.getMonth()) {
                  monthInvoiceSum += parseFloat(inv.amount || 0);
                }
              });
              p.payments?.forEach(pay => {
                const payDate = new Date(pay.date);
                if (payDate.getFullYear() === d.getFullYear() && payDate.getMonth() === d.getMonth()) {
                  monthPaymentSum += parseFloat(pay.amount || 0);
                }
              });
            }
          });
          
          invoiceData.push(monthInvoiceSum);
          paymentData.push(monthPaymentSum);
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

        const draft = projects.value.filter(p => p.status === '草稿').length;
        const pending = projects.value.filter(p => p.status === '待审核').length;
        const approved = projects.value.filter(p => p.status === '已立项').length;
        const closed = projects.value.filter(p => p.status === '已结项').length;
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
      logout,
      enforceTabAccess,

      // OCR 解析与分步
      isScanning,
      ocrSuccess,
      currentStep,
      formProject,
      newExpense,
      activeEditProject,
      startEditProject,
      simulateWordOCR,
      nextToSeal,
      mockUploadSealPDF,
      addExpenseItem,
      removeExpenseItem,
      totalFormExpenses,
      nextToVerify,
      verifyAccept1,
      verifyAccept2,
      verifyRemark,
      submitProjectRegistration,
      saveAsDraft,
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
      mockReportFileName,
      submitClosingRequest,

      // 财务台账账本
      selectedProjectForFinance,
      tempInvoice,
      tempPayment,
      triggerRecordFinance,
      totalInvoiced,
      totalPaid,
      recordInvoice,
      recordPayment,
      auditProjectClosing,

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
