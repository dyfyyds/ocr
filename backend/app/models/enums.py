# ============================================================
#  集中式状态 / 角色常量
#  采纳 OCR-IPMS 的「集中枚举」模式，但**沿用本系统现有的字符串值**
#  （与数据库存储值、前端 STATUS_CN 映射保持一致，不做任何值变更）。
# ============================================================

# ── 角色 ──
ROLE_ADMIN = "admin"
ROLE_BUSINESS = "business"
ROLE_FINANCE = "finance"
ROLE_PM = "pm"

# ── 项目状态（project.status）──
PROJECT_DRAFT = "draft"            # 草稿
PROJECT_PENDING_AUDIT = "pending_audit"  # 待审核
PROJECT_APPROVED = "approved"     # 已立项
PROJECT_REJECTED = "rejected"     # 已驳回
PROJECT_CLOSED = "closed"         # 已结项

# ── 结项申请状态（project_close.status / project.close_status）──
CLOSE_PENDING = "pending"
CLOSE_APPROVED = "approved"
CLOSE_REJECTED = "rejected"

# ── 业务规则用到的状态集合 ──
# 仅「已立项」可开票（与原 invoices.py 守卫一致）
INVOICEABLE_STATUSES = frozenset({PROJECT_APPROVED})
# 可发起结项的状态
CLOSEABLE_STATUSES = frozenset({PROJECT_APPROVED})
