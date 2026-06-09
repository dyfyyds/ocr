# 智能项目管理系统 — 真实端到端集成 & PPT 功能补全 设计稿

日期: 2026-06-09 · 分支: `fix/logic` · 验证方式: 真机浏览器 + 网络请求取证

## 1. 背景与诊断结论

用户反馈"页面仍是预写死的假数据"。经在运行中的 docker 栈上实测（真实登录 + 抓取网络
请求），结论是 **集成大部分已存在且可用**，但三类真实缺陷让 UI *表现为* 假数据：

| # | 缺陷 | 证据 | 影响 |
|---|------|------|------|
| D1 | **后端启动竞态** — `init_db()` 无重试；MySQL 未就绪时 `Application startup failed. Exiting.` | `docker logs pm-backend`: `Can't connect to MySQL server on 'mysql'` | 后端静默宕机 → 前端所有 `api()` 调用失败 → 回退到 mock 块。**这是"全是假数据"的根因。** |
| D2 | **合同校验区写死 mock + 残缺 HTML** | `index.html:660` `</div>"diff-cell match">…`（畸形标签）；`660-708` 写死 `¥580,000 / ¥420,000 / 智能大屏 / HT-2026-088`，绑定到死 ref `verifyAccept1/2`；真实动态版（`verifyDiffs`）就在其上方被重复遮蔽 | 立项"合同校验"屏字面显示预写死差异 |
| D3 | **真实后端接口被孤立 + 零散写死** | 后端 `/api/dashboard/stats\|trend\|status-distribution\|recent-logs` 真实可用但前端从不调用（改为客户端按已加载分页计算）；`index.html:538-539` 写死 `王五/李四` 下拉；`app.js:801` 离线回退注入假差异 | 规模化后统计口径错误；最近活动日志未用 |

附加逻辑漏洞：财务查询汇总的 `queryYear` 年度筛选未真正作用于 `financeRows`/图表/导出。

PPT（智能项目管理系统，slides 29–45）要求的功能**大多已存在**：register/projects/pm_projects/
finance_ledger/close_audit/finance_query/audit/users/dict 标签齐全，finance_query 已含
柱/饼图 + Excel/PDF 导出。所以"补全 PPT"主要是**让既有功能跑在真实数据上并补缺口**，而非重写。

## 2. 目标 / 非目标

**目标**
- 后端永不因 MySQL 瞬时不可用而崩溃（带退避重试）。
- 删除所有写死/回退 mock；后端失败时**显式报错**而非伪造成功。
- 前端工作台改用真实后端聚合接口；合同校验绑定真实 OCR 比对结果。
- 修复列出的逻辑漏洞（年度筛选、写死下拉/角色判断等）。
- 按 PPT 全流程逐角色真机走通并补齐发现的缺口。
- 全程保持 "cosmic-tech / glassmorphism" 视觉语言不变。

**非目标**
- 不重写 app.js 数据层（既有集成大部分有效，重写高风险且冗余）。
- 不改 SPA（`src/`）那套未部署的前端。
- 不引入新的设计风格 / 组件库。

## 3. 工作分解（按依赖排序）

### W1 — 后端启动竞态修复（根因，最高优先）
- `app/db/mysql.py:init_db()` 加入重试退避循环（如 ~30 次 ×1s），仅在多次失败后才放弃。
- 验证：停 mysql→起 backend 不崩溃，等待；mysql 起来后自动连上、`/api/health` 200。
- 验收：`docker logs` 无 `Application startup failed`；容器 `healthy`。

### W2 — 清除合同校验写死 mock + 修复残缺 HTML（D2）
- 删除 `index.html` 中 660–708 的写死差异表 / 第二个写死"人工确认表单"/畸形标签；
  统一保留绑定 `comparisonRows` + `verifyDiffs` 的真实动态版。
- 删除 `app.js:801-812` 的离线回退假差异、`mockUploadSealPDF` / `mockReportFileName` 残留命名；
  失败时走统一错误提示（toast/日志），不再注入假数据。
- 验收：上传真实 Word→PDF，校验屏只显示后端 `/verify` 返回的真实差异；后端故意返回错误时 UI 显示报错而非假差异。

### W3 — 工作台接入真实聚合接口（D3）
- `app.js` 新增 `loadDashboard()`：调用 `/api/dashboard/stats|trend|status-distribution|recent-logs`，
  驱动统计卡 / 趋势图 / 状态分布图 / 最近活动；保留客户端计算作为兜底但以后端为准。
- 验收：网络面板显示 4 个 dashboard 请求 200；卡片/图表数值与后端聚合一致（与 DB 20 条项目对得上）。

### W4 — 逻辑漏洞修复
- 财务查询汇总 `queryYear`（含可选月度）真正过滤 `financeRows`/图表/导出数据源。
- `index.html:538-539` 写死下拉 → 取真实用户（按角色过滤的 pm 列表）。
- 移除 `currentUser.name === '王五（项目经理）'` 等写死姓名判断 → 改用 `role` 判定。
- 验收：切换年度后表格/图表/导出随之变化；下拉来自 `/api/users`。

### W5 — PPT 全流程真机走通 + 补缺
逐角色用真机浏览器执行并抓网络，缺口随发现随补：
1. 商务：Word 合同上传→OCR/NLP 自动提取填表→补充信息→PDF 盖章上传→真实校验差异→提交立项。
2. 管理员：立项审核通过/驳回（驳回填原因）→ 状态 `已立项`。
3. 财务：选已立项→开票（上传发票 OCR 识别）→多次回款→自动算应收款；查询汇总+导出。
4. 项目经理：上传验收报告→提交结项；财务结项审核→ `已结项` 只读不可再开票。
- 验收：每个角色流程的关键步骤都有"网络请求 200 + 真实数据渲染"截图；已结项项目开票入口禁用。

## 4. 验证策略（真机浏览器 + 网络取证）
- 启动栈：`docker compose up -d`，确认 4 容器 healthy。
- 用 `mcp__Claude_in_Chrome` / Playwright 驱动 `:18088/`（nginx 入口）。
- 每个角色登录（admin/business/finance/pm，密码均 `123456`）。
- 每步用 `read_network_requests` 确认走的是 `/api/*` 且响应为真实 DB 数据；截图留证。
- **完成判定铁律**：任一关键屏若数据来自 mock/回退即视为未完成（遵守"先证据后断言"）。

## 5. 风险
- Vite 在 Windows/Docker 卷挂载下常漏 `app.js`/`index.html` 改动 → 改后 `docker restart pm-frontend` 并
  `curl :18088/app.js | grep <marker>` 确认非缓存旧版（见 two-frontends-gotcha 记忆）。
- 真实 OCR/LLM 依赖外部 key；若 `LLM_API_KEY` 缺失，提取走正则兜底——这是真实降级，不是 mock，需如实呈现。
- 编辑的是部署版 `index.html + app.js`（非 `src/` SPA）。

## 6. 提交策略
分支 `fix/logic`，按 W1→W5 分组小步提交；每组附验证证据要点。
