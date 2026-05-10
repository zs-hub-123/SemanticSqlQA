-- ============================================================
-- 语义层修复脚本 V4.0
-- 基于五大数据集849题测试结果(0.12%准确率)的数据驱动分析
--
-- 失败分布:
--   SQL_MISMATCH:     528 (62.3%) ← COUNT(*) vs COUNT(DISTINCT)
--   NL_PARSE_FAIL:    163 (19.2%) ← 口语别名缺失
--   METRIC_NOT_FOUND:  98 (11.6%) ← 指标名不匹配/缺失
--   RETRY_EXHAUSTED:    20 (2.4%)
--   TABLE_WHITELIST:    18 (2.1%)
--   NO_CANDIDATE_TABLE:  6 (0.7%)
-- ============================================================

USE text02_semantic;

-- ============================================================
-- Part 1: 新增缺失的核心指标（解决METRIC_NOT_FOUND, 98个）
-- ============================================================

INSERT INTO standard_metrics_dimensions
(name, type, physical_table, physical_field, field_type,
 business_desc, aggregation_type, domain,
 is_non_additive, stat_period, data_granularity, default_filter,
 metric_version, effective_date) VALUES

-- A. 实体计数指标
('地址数量', 'metric', 'user_addresses', 'address_id', 'BIGINT',
 '收货地址总数', 'COUNT', '用户域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

('类目数量', 'metric', 'categories', 'category_id', 'BIGINT',
 '商品分类总数', 'COUNT', '商品域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

('店铺评分数量', 'metric', 'store_ratings', 'rating_id', 'BIGINT',
 '店铺评价记录总数', 'COUNT', '店铺域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

('订单明细数量', 'metric', 'order_items', 'item_id', 'BIGINT',
 '订单明细记录总数', 'COUNT', '交易域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

('活动数量', 'metric', 'campaigns', 'campaign_id', 'BIGINT',
 '营销活动总数', 'COUNT', '营销域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

('用户优惠券数量', 'metric', 'user_coupons', 'id', 'BIGINT',
 '用户领券记录总数', 'COUNT', '营销域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

('物流轨迹数量', 'metric', 'shipment_tracks', 'track_id', 'BIGINT',
 '物流跟踪节点总数', 'COUNT', '物流域',
 1, NULL, NULL, NULL, 'V4.0', '2024-01-01'),

-- B. 业务聚合指标
('复购率', 'metric', 'orders', 'user_id', 'BIGINT',
 '重复购买用户占比', NULL, '交易域',
 1, 'monthly,quarter', '时间+地区+渠道', "order_status='paid'", 'V4.0', '2024-01-01'),

('回头率', 'metric', 'orders', 'user_id', 'BIGINT',
 '同复购率', NULL, '交易域',
 1, 'monthly,quarter', '时间+地区+渠道', "order_status='paid'", 'V4.0', '2024-01-01'),

('退款金额', 'metric', 'order_items', 'refund_amount', 'DECIMAL(10,2)',
 '退款金额合计', 'SUM', '交易域',
 0, 'daily,weekly,monthly', '时间+商品+店铺', "refund_status IN ('approved','refunded')", 'V4.0', '2024-01-01'),

('退款总额', 'metric', 'order_items', 'refund_amount', 'DECIMAL(10,2)',
 '同退款金额', 'SUM', '交易域',
 0, 'daily,weekly,monthly', '时间+商品+店铺', "refund_status IN ('approved','refunded')", 'V4.0', '2024-01-01'),

('访问量', 'metric', 'users', 'user_id', 'BIGINT',
 '独立访客数(UV)', 'COUNT(DISTINCT)', '用户域',
 1, 'daily,weekly,monthly', '时间+地区+渠道', NULL, 'V4.0', '2024-01-01'),

('UV', 'metric', 'users', 'user_id', 'BIGINT',
 '独立访客数(同访问量)', 'COUNT(DISTINCT)', '用户域',
 1, 'daily,weekly,monthly', '时间+地区+渠道', NULL, 'V4.0', '2024-01-01'),

('PV', 'metric', 'orders', 'order_id', 'BIGINT',
 '页面浏览量(以订单数近似)', 'COUNT', '交易域',
 1, 'daily,weekly,monthly', '时间+地区+渠道', NULL, 'V4.0', '2024-01-01'),

('账户余额均值', 'metric', 'users', 'balance', 'DECIMAL(12,2)',
 '用户平均账户余额', 'AVG', '用户域',
 0, 'daily,monthly', '等级+地区', NULL, 'V4.0', '2024-01-01'),

-- C. 维度级指标（用于维度-only查询的候选表查找）
('一级类目', 'dimension', 'categories', 'category_name', 'VARCHAR',
 '一级分类', NULL, '商品域', 0, NULL, NULL, "level=1", 'V4.0', '2024-01-01'),
('二级类目', 'dimension', 'categories', 'category_name', 'VARCHAR',
 '二级分类', NULL, '商品域', 0, NULL, NULL, "level=2", 'V4.0', '2024-01-01'),
('类目名称', 'dimension', 'categories', 'category_name', 'VARCHAR',
 '分类名称', NULL, '商品域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('省份', 'dimension', 'user_addresses', 'province', 'VARCHAR',
 '收货地址所在省份', NULL, '用户域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('城市', 'dimension', 'user_addresses', 'city', 'VARCHAR',
 '收货地址所在城市', NULL, '用户域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('区县', 'dimension', 'user_addresses', 'detail_address', 'VARCHAR',
 '详细地址(含区县)', NULL, '用户域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('商品名称', 'dimension', 'products', 'product_name', 'VARCHAR',
 '商品名称', NULL, '商品域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('店名', 'dimension', 'stores', 'store_name', 'VARCHAR',
 '店铺名称', NULL, '店铺域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('昵称', 'dimension', 'users', 'nickname', 'VARCHAR',
 '用户昵称', NULL, '用户域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('品牌', 'dimension', 'products', 'brand', 'VARCHAR',
 '品牌名称', NULL, '商品域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('规格名称', 'dimension', 'product_specs', 'spec_name', 'VARCHAR',
 'SKU规格名称', NULL, '商品域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('物流单号', 'dimension', 'shipments', 'shipment_no', 'VARCHAR',
 '快递运单号', NULL, '物流域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('支付流水号', 'dimension', 'payments', 'payment_no', 'VARCHAR',
 '支付流水编号', NULL, '交易域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('订单编号', 'dimension', 'orders', 'order_no', 'VARCHAR',
 '订单编号', NULL, '交易域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('券名', 'dimension', 'coupons', 'coupon_name', 'VARCHAR',
 '优惠券名称', NULL, '营销域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('活动名', 'dimension', 'campaigns', 'campaign_name', 'VARCHAR',
 '营销活动名称', NULL, '营销域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01'),
('位置', 'dimension', 'shipment_tracks', 'location', 'VARCHAR',
 '物流当前位置', NULL, '物流域', 0, NULL, NULL, NULL, 'V4.0', '2024-01-01')

ON DUPLICATE KEY UPDATE metric_version = 'V4.0';


-- ============================================================
-- Part 2: 补充口语别名映射（解决NL_PARSE_FAIL, 163个）
-- 核心策略：高频词→实体指标 + 指标变体→标准名 + 维度查询词
-- ============================================================

INSERT INTO spoken_aliases (spoken_term, standard_name, alias_type, frequency, source) VALUES

-- A. 高频口语 → 实体计数
('商户', '店铺数量', 'entity', 200, 'v4_fix'),
('商户数量', '店铺数量', 'entity', 150, 'v4_fix'),
('多少商户', '店铺数量', 'entity', 120, 'v4_fix'),
('商家', '店铺数量', 'entity', 250, 'v4_fix'),
('商家数量', '店铺数量', 'entity', 180, 'v4_fix'),
('卖家', '店铺数量', 'entity', 200, 'v4_fix'),
('客户', '用户数量', 'entity', 200, 'v4_fix'),
('客户数', '用户数量', 'entity', 180, 'v4_fix'),
('货品', '商品数量', 'entity', 200, 'v4_fix'),
('物品', '商品数量', 'entity', 180, 'v4_fix'),
('产品', '商品数量', 'entity', 200, 'v4_fix'),
('券', '优惠券数量', 'entity', 300, 'v4_fix'),
('活动', '活动数量', 'entity', 280, 'v4_fix'),
('快递', '物流单数量', 'entity', 220, 'v4_fix'),
('地址', '地址数量', 'entity', 200, 'v4_fix'),
('类目', '类目名称', 'entity', 200, 'v4_fix'),
('品类', '类目名称', 'entity', 180, 'v4_fix'),
('评价', '店铺评分数量', 'entity', 200, 'v4_fix'),
('DSR', 'DSR描述分', 'term', 200, 'v4_fix'),
('轨迹', '物流轨迹数量', 'entity', 150, 'v4_fix'),
('明细', '订单明细数量', 'entity', 180, 'v4_fix'),
('流水', '支付笔数', 'entity', 200, 'v4_fix'),
('属性', 'SKU数量', 'entity', 200, 'v4_fix'),
('规格', 'SKU数量', 'entity', 180, 'v4_fix'),
('SKU', 'SKU数量', 'entity', 160, 'v4_fix'),

-- B. 指标名变体 → 已有标准指标
('GMV', 'GMV成交总额', 'term', 300, 'v4_fix'),
('成交额', 'GMV成交总额', 'term', 260, 'v4_fix'),
('销售总额', 'GMV成交总额', 'term', 220, 'v4_fix'),
('实付金额', '实付金额总额', 'term', 240, 'v4_fix'),
('优惠金额', '优惠金额总额', 'term', 200, 'v4_fix'),
('人均消费', '客单价', 'term', 220, 'v4_fix'),
('运费', '运费总额', 'term', 180, 'v4_fix'),
('销量', '总销量', 'term', 300, 'v4_fix'),
('库存', '总库存', 'term', 220, 'v4_fix'),
('价格', '平均价格', 'term', 260, 'v4_fix'),
('均价', '平均价格', 'term', 180, 'v4_fix'),
('评分', '平均评分', 'term', 200, 'v4_fix'),
('退款', '退款金额', 'term', 220, 'v4_fix'),
('预算', '活动预算总额', 'term', 180, 'v4_fix'),
('ROI', 'ROI投资回报率', 'term', 200, 'v4_fix'),
('余额', '账户余额均值', 'term', 160, 'v4_fix'),
('回头率', '复购率', 'term', 200, 'v4_fix'),
('UV', '访问量', 'term', 200, 'v4_fix'),
('签收率', '签收率', 'term', 180, 'v4_fix'),
('核销率', '核销率', 'term', 160, 'v4_fix'),

-- C. 状态/条件词
('下架', '商品数量', 'status_filter', 100, 'v4_fix'),
('营业中', '店铺数量', 'status_filter', 100, 'v4_fix'),
('已发货', '订单数量', 'status_filter', 120, 'v4_fix'),
('已取消', '订单数量', 'status_filter', 120, 'v4_fix'),
('已支付', '订单数量', 'status_filter', 120, 'v4_fix'),
('退款中', '订单数量', 'status_filter', 100, 'v4_fix'),
('支付宝', '订单数量', 'payment_filter', 100, 'v4_fix'),
('签收', '物流单数量', 'status_filter', 80, 'v4_fix'),

-- D. 维度查询词
('一级分类', '一级类目', 'dimension', 200, 'v4_fix'),
('二级分类', '二级类目', 'dimension', 200, 'v4_fix'),
('子分类', '二级类目', 'dimension', 140, 'v4_fix'),
('店铺类型', '店铺类型', 'dimension', 200, 'v4_fix'),
('省份', '省份', 'dimension', 200, 'v4_fix'),
('城市', '城市', 'dimension', 200, 'v4_fix'),
('品牌', '商品品牌', 'dimension', 200, 'v4_fix'),
('店名', '店名', 'dimension', 200, 'v4_fix'),
('订单编号', '订单编号', 'dimension', 180, 'v4_fix')

ON DUPLICATE KEY UPDATE frequency = GREATEST(frequency, VALUES(frequency));


-- ============================================================
-- Part 3: 补充表关联关系（解决TABLE_WHITELIST_FAIL, 18个）
-- ============================================================

INSERT INTO table_relations (
    main_table, related_table, join_condition, join_type,
    relation_desc, cardinality
) VALUES
('categories', 'products', 'categories.category_id = products.category_id',
 'LEFT JOIN', '分类与商品(一对多)', '1:N'),
('categories', 'categories', 'categories.parent_id = categories.category_id',
 'LEFT JOIN', '分类自连接(父子层级)', 'N:1'),
('users', 'stores', 'users.user_id = stores.owner_id',
 'LEFT JOIN', '用户与店铺(店主)', '1:1'),
('shipments', 'stores', 'shipments.store_id = stores.store_id',
 'LEFT JOIN', '物流与店铺', 'N:1'),
('order_items', 'products', 'order_items.product_id = products.product_id',
 'INNER JOIN', '明细与商品', 'N:1'),
('order_items', 'orders', 'order_items.order_id = orders.order_id',
 'INNER JOIN', '明细与订单', 'N:1'),
('store_ratings', 'stores', 'store_ratings.store_id = stores.store_id',
 'LEFT JOIN', '评分与店铺', 'N:1'),
('store_ratings', 'users', 'store_ratings.user_id = users.user_id',
 'LEFT JOIN', '评分与用户', 'N:1'),
('user_coupons', 'coupons', 'user_coupons.coupon_id = coupons.coupon_id',
 'LEFT JOIN', '用户券与模板', 'N:1'),
('user_coupons', 'users', 'user_coupons.user_id = users.user_id',
 'LEFT JOIN', '用户券与用户', 'N:1'),
('user_coupons', 'orders', 'user_coupons.id = orders.order_id',
 'LEFT JOIN', '用户券与订单', 'N:1'),
('payments', 'orders', 'payments.order_id = orders.order_id',
 'LEFT JOIN', '支付与订单', '1:1'),
('campaigns', 'stores', 'campaigns.store_id = stores.store_id',
 'LEFT JOIN', '活动与店铺', 'N:1')

ON DUPLICATE KEY UPDATE updated_at = NOW();


-- ============================================================
-- Part 4: 补充业务规则（自动应用关键过滤条件）
-- ============================================================

INSERT INTO business_rules (
    rule_name, rule_type, target_metric, target_dimension,
    rule_content, rule_desc, priority, error_message
) VALUES
('排除取消订单_GMV', 'filter', 'GMV成交总额', NULL,
 "order_status NOT IN ('cancelled','refunded')",
 'GMV统计默认排除取消/退款订单', 95, NULL),
('排除取消订单_实付', 'filter', '实付金额总额', NULL,
 "order_status NOT IN ('cancelled','refunded')",
 '实付金额统计排除取消订单', 95, NULL),
('排除取消订单_运费', 'filter', '运费总额', NULL,
 "order_status NOT IN ('cancelled','refunded')",
 '运费统计排除取消订单', 90, NULL),
('仅有效订单_订单数', 'filter', '订单数量', NULL,
 "order_status NOT IN ('cancelled','refunded')",
 '订单数统计排除取消/退款', 90, NULL),
('仅已退款', 'filter', '退款金额', NULL,
 "refund_status IN ('approved','refunded')",
 '退款金额只统计已批准/已退款', 95, NULL),
('仅在售_商品数', 'filter', '商品数量', NULL,
 "status='on_sale'",
 '商品数只统计在售商品', 80, NULL),
('仅在售_均价', 'filter', '平均价格', NULL,
 "status='on_sale'",
 '均价只统计在售商品', 75, NULL),
('仅在售_销量', 'filter', '总销量', NULL,
 "status='on_sale'",
 '销量只统计在售商品', 75, NULL),
('仅在售_评分', 'filter', '平均评分', NULL,
 "status='on_sale'",
 '评分只统计在售商品', 75, NULL),
('仅营业中_店铺', 'filter', '店铺数量', NULL,
 "status='open'",
 '店铺数只统计营业中', 80, NULL),
('仅活跃用户', 'filter', '用户数量', NULL,
 "status='active'",
 '用户数只统计活跃用户', 80, NULL),
('仅有效券', 'filter', '优惠券数量', NULL,
 "status='active'",
 '券数只统计有效券', 75, NULL),
('仅已签收_物流', 'filter', '物流单数量', NULL,
 "status='delivered'",
 '物流单数只统计已签收', 80, NULL)

ON DUPLICATE KEY UPDATE updated_at = NOW();
