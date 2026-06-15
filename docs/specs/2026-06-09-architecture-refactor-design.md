# 架构重构设计稿 — 适配 OCR-IPMS 分层模式

日期：2026-06-09 ｜ 分支：`fix/logic` ｜ 参考：[wttc-nonelove/OCR-IPMS](https://github.com/wttc-nonelove/OCR-IPMS)

## 目标

把"核心应用逻辑层"按参考仓库的分层架构重构：**瘦路由 → 服务层**、**集中式枚举**、
**统一响应信封 `{code,message,data}`**、**前端逻辑分层**。严格的关注点分离用于
**保证 UI 不变**（cosmic/glassmorphism 风格、组件布局、视觉主题）。

## 关注点分离 = 安全机制

- 视觉层只在 **`index.html`（标记）+ `style.css`（主题）**。模板绑定的是 Vue `setup()`
  返回的键名（`@click="submitProjectRegistration"`、`stats.contractSum`…）。
- 只要 `setup()` 仍返回相同键名，**`index.html` 与 `style.css` 一字不改**。重构搬运的是
  *逻辑*，不是*表现*。
- W1–W5 的 `_verify_*.py`（Playwright 真机脚本）作为 **特征化测试**：重构前后行为一致 = 通过。

## 关键事实（决定设计）

- 我们的错误响应**已经**是 `{code, message}`（全局异常处理器），`code` 为**字符串**
  （`VALIDATION_ERROR` 等）。成功信封用 `code: 200`（int）。→ 前端以 **HTTP 状态码**判定
  成败（`api()` 已如此），信封仅用于**成功时解包 `data`**，规避 int/str 不一致；`exceptions.py` 不动。
- 我们已有 `require_role(*roles)`（`dependencies.py`）≈ 参考的 `require_roles`，RBAC 巩固主要是接线。
- 后端为**异步** SQLAlchemy（参考是同步）→ 适配*模式*而非照搬代码（服务函数 `async def ... AsyncSession`）。
- 唯一非 JSON 响应：`/api/uploads` 的 `FileResponse`（信封需按 content-type 排除）。
- 前端读响应共 **3 处**：`api()`、`tryRefresh()`、`handleLogin()`，仅这 3 处需解包。
- 前端无构建步骤（CDN Vue 全局版 + Vite 静态托管），`app.js` 以经典 `<script src>` 加载。

## 决策（已与用户确认）

1. **广度**：核心域优先（projects/approval、finance、close、contract-diff、ocr）；瘦 CRUD（dict/config/uploads/users/expenses）保留逻辑但仍走信封。
2. **响应信封**：采用 `{code,message,data}`（全局）。
3. **前端分层**：拆 `app.js` 为逻辑层，**命名空间经典脚本**（`window.PM.*`，多 `<script src>`），不改加载机制（最低风险）。
4. **验证**：复用 `_verify_*.py` 特征化测试，每阶段真机回归。
5. **节奏**：**先做后端批次**（枚举/信封/服务 + 前端解包），回归通过后 **checkpoint**；再做前端模块化作为第二批。

## 后端目标结构（核心域）

```
app/models/enums.py     # 新增：集中我们现有的状态值（draft/pending_audit/approved/
                        #       rejected/closed）与角色常量（采纳"集中枚举"模式，沿用现值）
app/schemas/common.py   # 新增：ok(data,msg)/paginated() 信封助手（code:200）
app/services/
  finance.py            # calc_receivable / validate_invoice / validate_payment
  approval.py           # 立项 submit + audit 状态流转（抽自 projects.py）
  close.py              # 结项申请 + 结项终审流转（抽自 close.py 路由）
  contract_diff.py      # 合同双版本 OCR 差异（抽自 contract_verifier）
  ocr.py                # OCR 识别编排
```
路由变瘦：解析 → 调服务 → `return ok(...)`。

## 信封机制（全局、安全）

- **成功**：响应包装机制对所有 `/api/*` 的 JSON 输出包成 `{code:200, message, data:<body>}`；
  **排除** `FileResponse`（content-type 守卫）。实现优先用轻量中间件，避免逐路由改 `response_model`。
- **错误**：扩展现有异常处理器，补 `data:null`（已有 `code`/`message`）。
- **前端解包**：仅 `api()`/`tryRefresh()`/`handleLogin()` 三处；成功且检测到信封形状则返回 `data.data`，
  否则原样返回（防御式，兼容迁移期）；其余调用方（`mapProject(p)`、`data.items`…）**不变**。

## 前端目标结构（命名空间经典脚本）

```
js/services/http.js   # api() 客户端、token/refresh、信封解包（window.PM.http）
js/services/*.js      # projects/finance/dashboard/dict API 封装（window.PM.services）
js/domain/mappers.js  # mapProject/mapInvoice/mapPayment + STATUS_CN（window.PM.mappers）
js/domain/finance.js  # sumInPeriod/financeRows/应收计算（window.PM.finance）
js/store.js           # 响应式状态 + actions（loadProjects/loadDashboard…）
js/app.js             # createApp({ setup }) 组合以上，返回模板所需的相同键名
```
`index.html` 仅改 `<script>` 段（多脚本按依赖顺序加载）。`style.css` 不动。

## 分阶段实施（每阶段独立回归）

- **阶段 1（后端）**：`enums.py` + `schemas/common.py` + 全局成功信封中间件 + 错误信封补 `data`。
  排除 uploads 文件下载。回归：登录/列表/看板等接口返回信封；旧前端经解包后行为不变。
- **阶段 2（前端解包）**：`api()`/`tryRefresh()`/`handleLogin()` 解包信封。回归：登录、看板、
  财务筛选、全生命周期脚本全绿。
- **阶段 3（后端服务抽取）**：核心域逻辑从路由迁入 `services/`，路由变瘦 + 集中枚举替换魔法字符串 +
  巩固 `require_role`。**纯内部重构**，契约不变。回归：全生命周期脚本全绿。
- **==Checkpoint（后端批次评审）==**：汇总回归报告，等待批准。
- **阶段 4（前端模块化）**：按命名空间拆分 `app.js`，`index.html` 仅改脚本标签。回归：全脚本全绿 +
  视觉对比（截图）确认 UI 像素级不变。

## 风险与回滚

- 全程 `fix/logic` 分支；每阶段单独提交；任一回归门失败即 `git revert` 该阶段。
- 阶段 1+2 成对：信封是契约变更，必须两端同步上线并立即回归。
- 阶段 4 最大半径，置于 checkpoint 之后单独批准。
- Vite 陈拷贝坑：改前端后 `docker restart pm-frontend` 并 `curl` 校验标记串。

## 非目标（YAGNI）

- 不改 UI 标记/样式/主题；不引入构建步骤；不改数据库表结构/状态字符串值；
  不引入参考仓库的额外业务（active/terminated/framework 状态、export 落库等）。
