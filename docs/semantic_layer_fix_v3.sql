-- ============================================================
-- 语义层修复脚本 V3.0
-- 基于测试失败数据分析的全面修复（V5.2优化版）
-- 数据来源: tests/failures_list.json (47条失败)
-- 数据库结构: sql/ddl.sql (15张表)
-- 执行方式: python init_semantic_db.py (自动执行)
-- 主要问题:
--   1. MQL校验失败: 缺少'商品数量'/'店铺数量'/'用户数量'等基础指标
--   2. SQL语义差异: COUNT(*) vs COUNT(field) 匹配问题
-- ============================================================

USE text02_semantic;

-- ============================================================
-- Part 1: 补充缺失的核心COUNT指标（最高优先级）
-- 问题: AI查询"XX总共有多少条记录"时无法找到对应指标
-- 影响: 30+处 MQL校验失败 "指标不存在"
-- ============================================================

INSERT INTO `standard_metrics_dimensions` (
    `name`, `type`, `physical_table`, `physical_field`, `field_type`,
    `business_desc`, `aggregation_type`, `domain`,
    `is_non_additive`, `stat_period`, `data_granularity`, `default_filter`,
    `metric_version`, `effective_date`
) VALUES

-- ===== 核心实体计数指标（必须添加） =====

('用户数量', 'metric', 'users', 'user_id', 'BIGINT',
 '注册用户总数', 'COUNT', '用户域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

('买家数量', 'metric', 'users', 'user_id', 'BIGINT',
 '购买过商品的买家总数(同用户数量)', 'COUNT', '用户域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

('客户数量', 'metric', 'users', 'user_id', 'BIGINT',
 '客户总数(同用户数量)', 'COUNT', '用户域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

('会员数量', 'metric', 'users', 'user_id', 'BIGINT',
 '会员总数(同用户数量)', 'COUNT', '用户域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

-- 商品域 - 核心计数指标
('商品数量', 'metric', 'products', 'product_id', 'BIGINT',
 '在售商品总数', 'COUNT', '商品域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

('SKU数量', 'metric', 'product_specs', 'spec_id', 'BIGINT',
 '商品规格(SKU)总数', 'COUNT', '商品域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

-- 店铺域 - 核心计数指标
('店铺数量', 'metric', 'stores', 'store_id', 'BIGINT',
 '开店商家总数', 'COUNT', '店铺域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

-- 交易域 - 核心计数指标
('订单数量', 'metric', 'orders', 'order_id', 'BIGINT',
 '订单总数', 'COUNT', '交易域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

('有效订单数', 'metric', 'orders', 'order_id', 'BIGINT',
 '有效订单数(排除取消/退款)', 'COUNT', '交易域',
 1, NULL, NULL, "order_status NOT IN ('cancelled','refunded')",
 'V3.0', '2024-01-01'),

('支付笔数', 'metric', 'payments', 'payment_id', 'BIGINT',
 '支付记录总数', 'COUNT', '交易域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

-- 物流域 - 核心计数指标
('物流单数量', 'metric', 'shipments', 'shipment_id', 'BIGINT',
 '物流发货单总数', 'COUNT', '物流域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01'),

-- 营销域 - 核心计数指标
('优惠券数量', 'metric', 'coupons', 'coupon_id', 'BIGINT',
 '优惠券模板总数', 'COUNT', '营销域',
 1, NULL, NULL, NULL,
 'V3.0', '2024-01-01')

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- Part 2: 补充口语别名映射（关键！）
-- 问题: NL Parser无法将口语表达映射到正确的指标
-- 影响: 大量"指标不存在"MQL校验失败
-- ============================================================

INSERT INTO `spoken_aliases` (`spoken_term`, `standard_name`, `alias_type`, `frequency`, `source`) VALUES

-- ===== 商品域别名 =====
('商品', '商品数量', 'entity', 200, 'fix_v3'),
('产品', '商品数量', 'entity', 150, 'fix_v3'),
('货品', '商品数量', 'entity', 80, 'fix_v3'),
('多少商品', '商品数量', 'entity', 120, 'fix_v3'),
('多少个商品', '商品数量', 'entity', 100, 'fix_v3'),
('商品有多少', '商品数量', 'entity', 90, 'fix_v3'),
('商品总共有', '商品数量', 'entity', 85, 'fix_v3'),
('商品一共', '商品数量', 'entity', 70, 'fix_v3'),

-- ===== 店铺域别名 =====
('店铺', '店铺数量', 'entity', 180, 'fix_v3'),
('商店', '店铺数量', 'entity', 100, 'fix_v3'),
('商家', '店铺数量', 'entity', 120, 'fix_v3'),
('卖家', '店铺数量', 'entity', 90, 'fix_v3'),
('多少店铺', '店铺数量', 'entity', 110, 'fix_v3'),
('查一下店铺', '店铺数量', 'entity', 95, 'fix_v3'),
('店铺总共有', '店铺数量', 'entity', 85, 'fix_v3'),

-- ===== 订单域别名 =====
('订单', '订单数量', 'entity', 250, 'fix_v3'),
('订单数', '订单数量', 'entity', 220, 'fix_v3'),
('多少订单', '订单数量', 'entity', 150, 'fix_v3'),
('订单总共有', '订单数量', 'entity', 130, 'fix_v3'),
('订单一共', '订单数量', 'entity', 110, 'fix_v3'),
('有效订单', '有效订单数', 'entity', 100, 'fix_v3'),
('已完成订单', '有效订单数', 'entity', 90, 'fix_v3'),
('成交订单', '有效订单数', 'entity', 85, 'fix_v3'),

-- ===== 支付/流水域别名 =====
('流水', '支付笔数', 'entity', 140, 'fix_v3'),
('支付流水', '支付笔数', 'entity', 130, 'fix_v3'),
('付款记录', '支付笔数', 'entity', 110, 'fix_v3'),
('查一下流水', '支付笔数', 'entity', 95, 'fix_v3'),
('流水总共有', '支付笔数', 'entity', 80, 'fix_v3'),
('付款笔数', '支付笔数', 'entity', 90, 'fix_v3'),

-- ===== 优惠券域别名 =====
('优惠券', '优惠券数量', 'entity', 160, 'fix_v3'),
('券', '优惠券数量', 'entity', 130, 'fix_v3'),
('优惠卷', '优惠券数量', 'entity', 60, 'fix_v3'),  -- 常见错别字
('查一下优惠券', '优惠券数量', 'entity', 95, 'fix_v3'),
('优惠券总共有', '优惠券数量', 'entity', 80, 'fix_v3'),

-- ===== 物流域别名 =====
('物流单', '物流单数量', 'entity', 120, 'fix_v3'),
('快递单', '物流单数量', 'entity', 100, 'fix_v3'),
('发货单', '物流单数量', 'entity', 90, 'fix_v3'),
('包裹', '物流单数量', 'entity', 80, 'fix_v3'),

-- ===== 订单明细域别名 =====
('明细', '订单明细数量', 'entity', 110, 'fix_v3'),
('订单明细', '订单明细数量', 'entity', 130, 'fix_v3'),
('明细总共有', '订单明细数量', 'entity', 85, 'fix_v3'),

-- ===== 评分域别名 =====
('评分', '店铺评分数量', 'entity', 100, 'fix_v3'),
('评价', '店铺评分数量', 'entity', 95, 'fix_v3'),
('评分总共有', '店铺评分数量', 'entity', 75, 'fix_v3'),

-- ===== 属性/SKU域别名 =====
('属性', '属性数量', 'entity', 110, 'fix_v3'),
('规格', '属性数量', 'entity', 100, 'fix_v3'),
('SKU', '属性数量', 'entity', 90, 'fix_v3'),
('属性总共有', '属性数量', 'entity', 80, 'fix_v3'),

-- ===== 地址域别名 =====
('地址', '地址数量', 'entity', 100, 'fix_v3'),
('收货地址', '地址数量', 'entity', 120, 'fix_v3'),
('配送地址', '地址数量', 'entity', 90, 'fix_v3'),
('地址总共有', '地址数量', 'entity', 75, 'fix_v3')

ON DUPLICATE KEY UPDATE `frequency` = GREATEST(`frequency`, VALUES(`frequency`));


-- ============================================================
-- Part 3: 补充表关联关系（解决JOIN路径缺失）
-- 问题: 多表关联查询时找不到关联关系
-- 影响: SQL校验失败或生成错误SQL
-- ============================================================

INSERT INTO `table_relations` (
    `main_table`, `related_table`, `join_type`,
    `join_condition`, `relation_desc`, `cardinality`
) VALUES

-- 用户相关JOIN
('users', 'user_addresses', 'LEFT JOIN',
 'users.user_id = user_addresses.user_id',
 '用户与收货地址(一对多)', '1:N'),

('users', 'orders', 'LEFT JOIN',
 'users.user_id = orders.user_id',
 '用户与订单(一对多)', '1:N'),

-- 订单相关JOIN
('orders', 'order_items', 'INNER JOIN',
 'orders.order_id = order_items.order_id',
 '订单与明细(一对多)', '1:N'),

('orders', 'payments', 'LEFT JOIN',
 'orders.order_id = payments.order_id',
 '订单与支付(一对一)', '1:1'),

('orders', 'shipments', 'LEFT JOIN',
 'orders.order_id = shipments.order_id',
 '订单与物流(一对多)', '1:N'),

('orders', 'store_ratings', 'LEFT JOIN',
 'orders.order_id = store_ratings.order_id',
 '订单与评价(一对一)', '1:1'),

-- 商品相关JOIN
('products', 'product_specs', 'INNER JOIN',
 'products.product_id = product_specs.product_id',
 '商品与规格(一对多)', '1:N'),

('products', 'order_items', 'INNER JOIN',
 'products.product_id = order_items.product_id',
 '商品与订单明细(多对多)', 'M:N'),

('products', 'categories', 'LEFT JOIN',
 'products.category_id = categories.category_id',
 '商品与分类(多对一)', 'N:1'),

-- 店铺相关JOIN
('stores', 'products', 'LEFT JOIN',
 'stores.store_id = products.store_id',
 '店铺与商品(一对多)', '1:N'),

('stores', 'store_ratings', 'LEFT JOIN',
 'stores.store_id = store_ratings.store_id',
 '店铺与评价(一对多)', '1:N'),

('stores', 'orders', 'LEFT JOIN',
 'stores.store_id = orders.store_id',
 '店铺与订单(一对多)', '1:N'),

-- 物流相关JOIN
('shipments', 'shipment_tracks', 'INNER JOIN',
 'shipments.shipment_id = shipment_tracks.shipment_id',
 '物流单与轨迹(一对多)', '1:N'),

-- 营销相关JOIN
('coupons', 'user_coupons', 'LEFT JOIN',
 'coupons.coupon_id = user_coupons.coupon_id',
 '优惠券与领券记录(一对多)', '1:N'),

('user_coupons', 'orders', 'LEFT JOIN',
 'user_coupons.id = orders.coupon_id',
 '用券记录与订单(多对一)', 'N:1')

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- Part 4: 补充业务规则（自动应用过滤条件）
-- 问题: 订单统计未排除已取消订单
-- 影响: 统计数据不准确
-- ============================================================

INSERT INTO `business_rules` (
    `rule_name`, `rule_type`, `target_metric`, `target_dimension`,
    `rule_content`, `rule_desc`, `priority`, `error_message`
) VALUES

-- 订单相关规则
('排除取消订单', 'filter', '订单数量', NULL,
 "order_status NOT IN ('cancelled','refunded')",
 '订单统计默认排除已取消和已退款订单', 100,
 '⚠️ 订单类指标应排除取消/退款订单'),

('排除取消订单_有效订单', 'filter', '有效订单数', NULL,
 "order_status NOT IN ('cancelled','refunded')",
 '有效订单只统计非取消状态', 100,
 NULL),

-- 支付相关规则
('仅成功支付', 'filter', 'GMV成交总额', NULL,
 "payment_status='success' OR pay_amount > 0",
 'GMV只统计实际支付的金额', 95,
 '⚠️ GMV应排除未支付订单'),

-- 用户相关规则
('仅活跃用户', 'filter', '用户数量', NULL,
 "status='active'",
 '用户统计默认只统计活跃用户', 80,
 NULL),

-- 商品相关规则
('仅在售商品', 'filter', '商品数量', NULL,
 "status='on_sale'",
 '商品统计默认只在售商品', 80,
 NULL)

ON DUPLICATE KEY UPDATE `updated_at` = NOW();

-- ============================================================
-- 完成!
-- 执行后请重启服务: python start.py
-- 然后重新运行测试验证效果
-- ============================================================
