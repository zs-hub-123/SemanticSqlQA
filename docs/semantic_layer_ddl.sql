-- ============================================================
-- SQL智能问答系统 - 语义层核心表 DDL (V5.0)
-- 数据库: text02_semantic
-- 作用：屏蔽底层物理表差异，统一业务人话 ↔ 数据库字段映射
-- 更新内容 V5.0:
--   1. 增强指标元数据：非累加标识、统计周期、数据粒度、版本管理
--   2. 新增业务规则表
-- ============================================================

CREATE DATABASE IF NOT EXISTS text02_semantic DEFAULT CHARSET utf8mb4;
USE text02_semantic;

-- ============================================================
-- 表1：标准指标维度字典表 (增强版)
-- 作用：定义所有可查询的业务指标和维度
-- 新增字段：is_non_additive, stat_period, data_granularity, metric_version, effective_date
-- ============================================================
DROP TABLE IF EXISTS `standard_metrics_dimensions`;
CREATE TABLE `standard_metrics_dimensions` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL COMMENT '标准名称（唯一）',
    `type` ENUM('metric', 'dimension') NOT NULL COMMENT '类型：metric=指标(可聚合) dimension=维度(分组/筛选)',
    `physical_table` VARCHAR(50) NOT NULL COMMENT '所属物理表名',
    `physical_field` VARCHAR(50) NOT NULL COMMENT '物理字段名',
    `field_type` VARCHAR(50) NOT NULL COMMENT '字段类型：DECIMAL/INT/VARCHAR/DATETIME等',
    `business_desc` VARCHAR(500) NOT NULL COMMENT '业务含义说明',
    `aggregation_type` VARCHAR(20) DEFAULT NULL COMMENT '聚合方式：SUM/COUNT/AVG/MIN/MAX（仅指标类）',

    -- === V5.0 新增字段 ===
    `is_non_additive` TINYINT(1) DEFAULT 0 COMMENT '是否不可二次聚合：0=可聚合 1=去重类不可聚合(如UV、支付用户数)',
    `stat_period` VARCHAR(20) DEFAULT NULL COMMENT '支持统计周期：daily=日/week=周/month=月/quarter=季/year=年/real_time=实时',
    `data_granularity` VARCHAR(200) DEFAULT NULL COMMENT '数据粒度：可用维度的组合，如"时间+地区+渠道"',
    `default_filter` VARCHAR(500) DEFAULT NULL COMMENT '默认过滤条件：SQL WHERE子句，如 order_status=''paid'' ',
    `metric_version` VARCHAR(20) DEFAULT 'V1.0' COMMENT '口径版本：如V1.0、V2.0',
    `effective_date` DATE DEFAULT NULL COMMENT '生效日期：从该日期起启用此版本',
    `deprecate_date` DATE DEFAULT NULL COMMENT '废弃日期：到该日期后停止使用',
    `calculation_formula` TEXT COMMENT '计算公式：衍生/复合指标的SQL表达式',
    `related_metrics` VARCHAR(200) DEFAULT NULL COMMENT '关联指标：复合指标依赖的原子指标ID',
    `domain` VARCHAR(50) NOT NULL COMMENT '业务域：用户域/商品域/店铺域/交易域/营销域/物流域',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY `uk_name` (`name`),
    KEY `idx_type` (`type`),
    KEY `idx_domain` (`domain`),
    KEY `idx_physical_table` (`physical_table`),
    KEY `idx_version` (`metric_version`),
    KEY `idx_effective` (`effective_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标准指标维度字典表(增强版)';

-- ============================================================
-- 表2：口语别名映射表
-- 作用：用户口语 → 标准词映射（解决同义词问题）
-- ============================================================
DROP TABLE IF EXISTS `spoken_aliases`;
CREATE TABLE `spoken_aliases` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `spoken_term` VARCHAR(200) NOT NULL COMMENT '用户口语表达',
    `standard_name` VARCHAR(100) NOT NULL COMMENT '对应的标准指标/维度名称',
    `alias_type` ENUM('entity', 'field', 'value', 'term') NOT NULL COMMENT '别名类型：实体/字段/枚举值/术语',
    `frequency` INT DEFAULT 1 COMMENT '出现频次（用于排序）',
    `source` VARCHAR(50) DEFAULT 'manual' COMMENT '来源：manual=人工标注 dataset=数据集提取',
    `is_active` TINYINT DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_spoken` (`spoken_term`),
    KEY `idx_standard` (`standard_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='口语别名映射表';

-- ============================================================
-- 表3：业务数据表元信息表
-- 作用：记录15张业务表的基础信息
-- ============================================================
DROP TABLE IF EXISTS `table_metadata`;
CREATE TABLE `table_metadata` (
    `table_name` VARCHAR(50) PRIMARY KEY COMMENT '物理表名',
    `table_cn_name` VARCHAR(100) NOT NULL COMMENT '中文表名',
    `description` VARCHAR(500) NOT NULL COMMENT '表用途说明',
    `domain` VARCHAR(50) NOT NULL COMMENT '所属业务域',
    `row_count_estimate` BIGINT DEFAULT 0 COMMENT '预估行数',
    `core_scenarios` TEXT COMMENT '核心业务场景（JSON数组）',
    `is_active` TINYINT DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY `idx_domain` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务数据表元信息表';

-- ============================================================
-- 表4：表直接关联关系表
-- 作用：仅存储直接相邻的表关联（不存间接跨层）
-- ============================================================
DROP TABLE IF EXISTS `table_relations`;
CREATE TABLE `table_relations` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `main_table` VARCHAR(50) NOT NULL COMMENT '主表',
    `related_table` VARCHAR(50) NOT NULL COMMENT '关联表',
    `join_condition` VARCHAR(500) NOT NULL COMMENT 'JOIN条件：如 user_id = user_id',
    `join_type` ENUM('INNER', 'LEFT') DEFAULT 'INNER' COMMENT '连接类型',
    `relation_strength` ENUM('strong', 'weak') DEFAULT 'strong' COMMENT '关联强度',
    `description` VARCHAR(255) DEFAULT NULL COMMENT '关联说明',
    `is_active` TINYINT DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_tables` (`main_table`, `related_table`),
    KEY `idx_main` (`main_table`),
    KEY `idx_related` (`related_table`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表直接关联关系表';

-- ============================================================
-- 表5：业务规则表 (V5.0新增)
-- 作用：定义口径规则、计算规则、冲突规则
-- ============================================================
DROP TABLE IF EXISTS `business_rules`;
CREATE TABLE `business_rules` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `rule_name` VARCHAR(100) NOT NULL COMMENT '规则名称',
    `rule_type` ENUM('filter', 'calc', 'conflict', 'validation') NOT NULL COMMENT '规则类型：filter=过滤规则 calc=计算规则 conflict=冲突规则 validation=校验规则',
    `target_metric` VARCHAR(100) DEFAULT NULL COMMENT '目标指标：应用此规则的指标名',
    `target_dimension` VARCHAR(100) DEFAULT NULL COMMENT '目标维度：应用此规则的维度名',
    `rule_content` TEXT NOT NULL COMMENT '规则内容：SQL WHERE子句或公式',
    `rule_desc` VARCHAR(500) DEFAULT NULL COMMENT '规则描述：业务含义说明',
    `priority` INT DEFAULT 0 COMMENT '优先级：数字越大越优先',
    `error_message` VARCHAR(200) DEFAULT NULL COMMENT '违反规则时的错误提示',
    `is_active` TINYINT DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY `idx_rule_type` (`rule_type`),
    KEY `idx_target_metric` (`target_metric`),
    KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务规则表';

-- ============================================================
-- 表6：维度层级表 (V5.0新增)
-- 作用：定义维度的钻取路径，如 时间:年→季→月→日
-- ============================================================
DROP TABLE IF EXISTS `dimension_hierarchies`;
CREATE TABLE `dimension_hierarchies` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `dimension_name` VARCHAR(100) NOT NULL COMMENT '维度名称',
    `level_name` VARCHAR(50) NOT NULL COMMENT '层级名称',
    `level_order` INT NOT NULL COMMENT '层级顺序：1=最高级',
    `physical_table` VARCHAR(50) NOT NULL COMMENT '物理表',
    `physical_field` VARCHAR(50) NOT NULL COMMENT '物理字段',
    `field_format` VARCHAR(50) DEFAULT NULL COMMENT '字段格式：如 %Y、%Y-%m',
    `description` VARCHAR(200) DEFAULT NULL COMMENT '层级说明',
    `is_active` TINYINT DEFAULT 1,
    KEY `idx_dimension` (`dimension_name`),
    KEY `idx_order` (`level_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维度层级表';
