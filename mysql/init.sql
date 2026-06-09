-- ============================================================
--  智能项目管理系统 - MySQL 初始化脚本
--  创建时间: 2026-06
--  参照: RAG/docker-em/mysql/init.sql
-- ============================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================================
--  建库
-- ============================================================
CREATE DATABASE IF NOT EXISTS project_management
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE project_management;

-- ============================================================
--  1. 用户表
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT,
    `username`      VARCHAR(50)  NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `real_name`     VARCHAR(50)  DEFAULT NULL,
    `email`         VARCHAR(100) DEFAULT NULL,
    `phone`         VARCHAR(20)  DEFAULT NULL,
    `role`          ENUM('admin','business','finance','pm') NOT NULL,
    `avatar`        VARCHAR(255) DEFAULT NULL,
    `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '1=启用, 0=禁用',
    `last_login`    DATETIME     DEFAULT NULL COMMENT '最后登录时间',
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_role` (`role`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  2. 项目表
-- ============================================================
CREATE TABLE IF NOT EXISTS `projects` (
    `id`                 BIGINT       NOT NULL AUTO_INCREMENT,
    `project_name`       VARCHAR(200) NOT NULL,
    `contract_no`        VARCHAR(100) DEFAULT NULL,
    `contract_amount`    DECIMAL(15,2) DEFAULT NULL,
    `customer_name`      VARCHAR(200) DEFAULT NULL,
    `project_type`       VARCHAR(50)  DEFAULT NULL,
    `pm_id`              BIGINT       DEFAULT NULL,
    `sign_date`          DATE         DEFAULT NULL,
    `expected_start_date` DATE        DEFAULT NULL,
    `expected_end_date`  DATE         DEFAULT NULL,
    `description`        TEXT         DEFAULT NULL,
    `status`             ENUM('draft','pending_audit','approved','rejected','closed')
                         NOT NULL DEFAULT 'draft',
    `created_by`         BIGINT       NOT NULL,
    `audit_by`           BIGINT       DEFAULT NULL,
    `audit_time`         DATETIME     DEFAULT NULL,
    `audit_reason`       TEXT         DEFAULT NULL,
    `created_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_by` (`created_by`),
    KEY `idx_pm_id` (`pm_id`),
    KEY `idx_customer` (`customer_name`),
    KEY `idx_created_at` (`created_at` DESC),
    CONSTRAINT `fk_projects_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_projects_pm` FOREIGN KEY (`pm_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  3. 合同文件表
-- ============================================================
CREATE TABLE IF NOT EXISTS `contracts` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT,
    `project_id`  BIGINT       NOT NULL,
    `file_type`   ENUM('word','pdf') NOT NULL,
    `file_name`   VARCHAR(255) NOT NULL,
    `file_path`   VARCHAR(500) NOT NULL,
    `file_size`   BIGINT       NOT NULL DEFAULT 0,
    `version`     INT          NOT NULL DEFAULT 1,
    `ocr_result`  JSON         DEFAULT NULL,
    `uploaded_by` BIGINT       NOT NULL,
    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_project_id` (`project_id`),
    CONSTRAINT `fk_contracts_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_contracts_uploaded_by` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  4. 合同校验差异表
-- ============================================================
CREATE TABLE IF NOT EXISTS `contract_diff` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT,
    `project_id`    BIGINT       NOT NULL,
    `field_name`    VARCHAR(50)  NOT NULL,
    `ocr_value`     VARCHAR(500) DEFAULT NULL,
    `input_value`   VARCHAR(500) DEFAULT NULL,
    `diff_type`     ENUM('mismatch','format','missing') DEFAULT NULL,
    `confirmed`     TINYINT      NOT NULL DEFAULT 0 COMMENT '0=未确认, 1=已确认',
    `confirm_reason` TEXT        DEFAULT NULL,
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_project_id` (`project_id`),
    CONSTRAINT `fk_diff_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  5. 开票记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `invoices` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT,
    `project_id`      BIGINT       NOT NULL,
    `invoice_no`      VARCHAR(50)  DEFAULT NULL,
    `invoice_code`    VARCHAR(50)  DEFAULT NULL,
    `amount`          DECIMAL(15,2) NOT NULL,
    `tax_rate`        DECIMAL(5,2) DEFAULT NULL,
    `tax_amount`      DECIMAL(15,2) DEFAULT NULL,
    `invoice_unit`    VARCHAR(200) DEFAULT NULL,
    `invoice_date`    DATE         NOT NULL,
    `buyer_name`      VARCHAR(200) DEFAULT NULL,
    `seller_name`     VARCHAR(200) DEFAULT NULL,
    `file_path`       VARCHAR(500) DEFAULT NULL,
    `delivery_voucher` VARCHAR(500) DEFAULT NULL COMMENT '交付凭证路径',
    `ocr_result`      JSON         DEFAULT NULL,
    `created_by`      BIGINT       NOT NULL,
    `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_project_id` (`project_id`),
    KEY `idx_invoice_no` (`invoice_no`),
    KEY `idx_invoice_date` (`invoice_date`),
    CONSTRAINT `fk_invoices_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_invoices_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  6. 回款记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `payments` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT,
    `project_id`     BIGINT       NOT NULL,
    `invoice_id`     BIGINT       DEFAULT NULL,
    `amount`         DECIMAL(15,2) NOT NULL,
    `payment_date`   DATE         NOT NULL,
    `payment_method` VARCHAR(50)  DEFAULT NULL,
    `payer_unit`     VARCHAR(200) DEFAULT NULL COMMENT '汇款单位（图2 表单）',
    `bank_serial_no` VARCHAR(100) DEFAULT NULL COMMENT '银行流水号（图2 表单）',
    `remark`         VARCHAR(500) DEFAULT NULL,
    `file_path`      VARCHAR(500) DEFAULT NULL,
    `created_by`     BIGINT       NOT NULL,
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_project_id` (`project_id`),
    KEY `idx_invoice_id` (`invoice_id`),
    CONSTRAINT `fk_payments_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payments_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`),
    CONSTRAINT `fk_payments_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  7. 项目支出表
-- ============================================================
CREATE TABLE IF NOT EXISTS `project_expenses` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '支出ID',
    `project_id`  BIGINT       NOT NULL                COMMENT '所属项目ID',
    `description` VARCHAR(200) NOT NULL                COMMENT '支出说明',
    `amount`      DECIMAL(15,2) NOT NULL               COMMENT '支出金额(元)',
    `expense_date` DATE        NOT NULL                COMMENT '支出日期',
    `created_by`  BIGINT       NOT NULL                COMMENT '创建人ID',
    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_project_id` (`project_id`),
    CONSTRAINT `fk_expenses_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_expenses_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目支出表';

-- ============================================================
--  8. 结项记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `project_close` (
    `id`                     BIGINT NOT NULL AUTO_INCREMENT,
    `project_id`             BIGINT NOT NULL,
    `close_date`             DATE   NOT NULL,
    `close_reason`           TEXT   DEFAULT NULL,
    `acceptance_report_path` VARCHAR(500) DEFAULT NULL,
    `status`                 ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    `reviewer_id`            BIGINT DEFAULT NULL,
    `review_time`            DATETIME DEFAULT NULL,
    `review_reason`          TEXT   DEFAULT NULL,
    `created_by`             BIGINT NOT NULL,
    `created_at`             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_project_id` (`project_id`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_close_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_close_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_close_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  9. 审核记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `audit_log` (
    `id`          BIGINT   NOT NULL AUTO_INCREMENT,
    `project_id`  BIGINT   NOT NULL,
    `action`      ENUM('project_audit','close_audit') NOT NULL,
    `result`      ENUM('approved','rejected') NOT NULL,
    `reason`      TEXT     DEFAULT NULL,
    `reviewer_id` BIGINT   NOT NULL,
    `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_project_id` (`project_id`),
    KEY `idx_action` (`action`),
    CONSTRAINT `fk_audit_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_audit_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  10. 活动日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS `activity_logs` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `action`       VARCHAR(50)  NOT NULL                COMMENT '操作类型',
    `detail`       VARCHAR(500) NOT NULL                COMMENT '操作描述',
    `user_id`      BIGINT       NOT NULL                COMMENT '操作人ID',
    `project_id`   BIGINT       DEFAULT NULL            COMMENT '关联项目ID',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (`id`),
    KEY `idx_action` (`action`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_project_id` (`project_id`),
    KEY `idx_created_at` (`created_at` DESC),
    CONSTRAINT `fk_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_logs_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动日志表';

-- ============================================================
--  11. 字典类型表
-- ============================================================
CREATE TABLE IF NOT EXISTS `dict_type` (
    `id`         BIGINT      NOT NULL AUTO_INCREMENT,
    `type_code`  VARCHAR(50) NOT NULL,
    `type_name`  VARCHAR(100) NOT NULL,
    `status`     TINYINT     NOT NULL DEFAULT 1 COMMENT '1=启用, 0=禁用',
    `remark`     VARCHAR(500) DEFAULT NULL,
    `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_type_code` (`type_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  12. 字典项表
-- ============================================================
CREATE TABLE IF NOT EXISTS `dict_item` (
    `id`         BIGINT      NOT NULL AUTO_INCREMENT,
    `type_id`    BIGINT      NOT NULL,
    `item_label` VARCHAR(100) NOT NULL,
    `item_value` VARCHAR(100) NOT NULL,
    `sort_order` INT         NOT NULL DEFAULT 0,
    `status`     TINYINT     NOT NULL DEFAULT 1 COMMENT '1=启用, 0=禁用',
    `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_type_id` (`type_id`),
    CONSTRAINT `fk_dict_item_type` FOREIGN KEY (`type_id`) REFERENCES `dict_type` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  13. 系统配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS `system_config` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT,
    `config_key`   VARCHAR(100) NOT NULL,
    `config_value` TEXT         NOT NULL,
    `description`  VARCHAR(255) DEFAULT NULL,
    `updated_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  初始数据：默认用户（原型页面演示账号）
--  所有账号密码均为: 123456 (bcrypt 哈希)
-- ============================================================
INSERT INTO `users` (`username`, `password_hash`, `real_name`, `role`, `status`) VALUES
('admin',    '$2b$12$K8eTu5n.ywZzV5Q5UEMqNesubj5pw8CNSxtGWs405wmq10Zp.Acji', '系统管理员',    'admin',    1),
('business', '$2b$12$K8eTu5n.ywZzV5Q5UEMqNesubj5pw8CNSxtGWs405wmq10Zp.Acji', '张三（商务经理）', 'business', 1),
('finance',  '$2b$12$K8eTu5n.ywZzV5Q5UEMqNesubj5pw8CNSxtGWs405wmq10Zp.Acji', '李四（财务总监）', 'finance',  1),
('pm',       '$2b$12$K8eTu5n.ywZzV5Q5UEMqNesubj5pw8CNSxtGWs405wmq10Zp.Acji', '王五（项目经理）', 'pm',       1)
ON DUPLICATE KEY UPDATE `password_hash` = VALUES(`password_hash`);

-- ============================================================
--  初始数据：系统默认配置
-- ============================================================
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('ocr_engine',          'paddleocr',                'OCR 引擎选择'),
('max_file_size_mb',    '20',                       '单文件大小上限(MB)'),
('allowed_file_types',  '["docx","pdf","jpg","png"]','允许上传的文件类型'),
('jwt_expire_hours',    '2',                        'Token 有效期(小时)'),
('refresh_expire_days', '7',                        'Refresh Token 有效期(天)'),
('llm_enabled',         'false',                    '合同识别是否启用 LLM 提取（true/false）'),
('llm_api_url',         'https://token-plan-cn.xiaomimimo.com/v1/chat/completions', 'LLM 接口地址'),
('llm_api_key',         '',                         'LLM API Key'),
('llm_model',           'mimo-v2.5-pro',            'LLM 模型名称')
ON DUPLICATE KEY UPDATE `config_value` = VALUES(`config_value`);

-- ============================================================
--  初始数据：数据字典
-- ============================================================
INSERT INTO `dict_type` (`type_code`, `type_name`) VALUES
('project_type', '项目类型'),
('invoice_type', '发票类型'),
('payment_method', '回款方式'),
('contract_type', '合同类型')
ON DUPLICATE KEY UPDATE `type_name` = VALUES(`type_name`);

INSERT INTO `dict_item` (`type_id`, `item_label`, `item_value`, `sort_order`) VALUES
(1, '软件开发', 'software', 1),
(1, '系统集成', 'integration', 2),
(1, '技术咨询', 'consulting', 3),
(1, '运维服务', 'maintenance', 4),
(3, '银行转账', 'bank_transfer', 1),
(3, '支票', 'check', 2),
(3, '现金', 'cash', 3)
ON DUPLICATE KEY UPDATE `item_label` = VALUES(`item_label`);
