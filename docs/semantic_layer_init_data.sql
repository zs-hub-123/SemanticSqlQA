-- ============================================================
-- 语义层初始化数据 - V5.0版
-- 基于15张业务表 + 增强指标元数据 + 业务规则
-- ============================================================

USE text02_semantic;

-- ============================================================
-- 步骤1：标准指标维度字典表数据（增强版）
-- 新增字段数据：is_non_additive, stat_period, data_granularity, default_filter
-- ============================================================

INSERT INTO `standard_metrics_dimensions` (
    `name`, `type`, `physical_table`, `physical_field`, `field_type`,
    `business_desc`, `aggregation_type`, `domain`,
    `is_non_additive`, `stat_period`, `data_granularity`, `default_filter`,
    `metric_version`, `effective_date`
) VALUES

-- 用户域指标
('用户数量', 'metric', 'users', 'user_id', 'BIGINT',
 '注册用户总数', 'COUNT', '用户域',
 1, 'daily,weekly,monthly,quarter,year', '时间+地区', NULL,
 'V1.0', '2024-01-01'),

('账户余额总额', 'metric', 'users', 'balance', 'DECIMAL(12,2)',
 '所有用户余额合计', 'SUM', '用户域',
 0, 'daily,monthly', '时间', NULL,
 'V1.0', '2024-01-01'),

('平均积分', 'metric', 'users', 'points', 'INT',
 '用户平均积分', 'AVG', '用户域',
 0, 'daily,monthly', '时间', NULL,
 'V1.0', '2024-01-01'),

-- 用户域维度
('注册时间', 'dimension', 'users', 'register_time', 'DATETIME',
 '用户注册时间', NULL, '用户域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('用户等级', 'dimension', 'users', 'user_level', 'ENUM',
 '会员等级(1-5级)', NULL, '用户域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('用户状态', 'dimension', 'users', 'status', 'ENUM',
 '账户状态(active/inactive/banned)', NULL, '用户域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('性别', 'dimension', 'users', 'gender', 'ENUM',
 '性别(M/F/U)', NULL, '用户域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

-- 商品域指标
('商品数量', 'metric', 'products', 'product_id', 'BIGINT',
 '商品总数', 'COUNT', '商品域',
 1, 'daily,weekly,monthly', '分类+品牌', NULL,
 'V1.0', '2024-01-01'),

('平均价格', 'metric', 'products', 'price', 'DECIMAL(10,2)',
 '商品平均售价', 'AVG', '商品域',
 0, 'daily', '分类+品牌', NULL,
 'V1.0', '2024-01-01'),

('总库存', 'metric', 'products', 'stock', 'INT',
 '所有商品库存总量', 'SUM', '商品域',
 0, 'daily', '分类', NULL,
 'V1.0', '2024-01-01'),

('平均评分', 'metric', 'products', 'rating_score', 'DECIMAL(2,1)',
 '商品平均评分', 'AVG', '商品域',
 0, 'daily', '分类+品牌', NULL,
 'V1.0', '2024-01-01'),

('总销量', 'metric', 'products', 'sales', 'INT',
 '累计销量总计', 'SUM', '商品域',
 0, 'daily,weekly,monthly', '分类+品牌+时间', NULL,
 'V1.0', '2024-01-01'),

-- 商品域维度
('商品分类', 'dimension', 'categories', 'category_name', 'VARCHAR',
 '商品所属分类', NULL, '商品域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('商品状态', 'dimension', 'products', 'status', 'ENUM',
 '上架状态(on_sale/off_sale/pre_sale)', NULL, '商品域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('品牌', 'dimension', 'products', 'brand', 'VARCHAR',
 '商品品牌', NULL, '商品域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('价格区间', 'dimension', 'products', 'price', 'DECIMAL(10,2)',
 '商品售价', NULL, '商品域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

-- 店铺域指标
('店铺数量', 'metric', 'stores', 'store_id', 'BIGINT',
 '店铺总数', 'COUNT', '店铺域',
 1, 'daily,monthly', '城市+类型', NULL,
 'V1.0', '2024-01-01'),

('店铺总销售额', 'metric', 'orders', 'pay_amount', 'DECIMAL(12,2)',
 '店铺累计销售额（已支付订单）', 'SUM', '店铺域',
 0, 'daily,monthly', '时间+店铺', "order_status='paid'",
 'V1.0', '2024-01-01'),

('平均粉丝数', 'metric', 'stores', 'total_followers', 'INT',
 '店铺平均粉丝数', 'AVG', '店铺域',
 0, 'daily', '类型', NULL,
 'V1.0', '2024-01-01'),

-- 店铺域维度
('店铺类型', 'dimension', 'stores', 'store_type', 'ENUM',
 '店铺类型(flagship/specialty/franchise/personal)', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('店铺状态', 'dimension', 'stores', 'status', 'ENUM',
 '营业状态(open/closed/frozen/reviewing)', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('所在城市', 'dimension', 'stores', 'city', 'VARCHAR',
 '店铺所在城市', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('DSR描述分', 'dimension', 'store_ratings', 'description_score', 'DECIMAL(2,1)',
 '描述相符评分', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('DSR服务分', 'dimension', 'store_ratings', 'service_score', 'DECIMAL(2,1)',
 '服务态度评分', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('DSR物流分', 'dimension', 'store_ratings', 'logistics_score', 'DECIMAL(2,1)',
 '物流服务评分', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('有图评价', 'dimension', 'store_ratings', 'has_image', 'TINYINT',
 '是否有图评价(0=否 1=是)', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('是否有图评价', 'dimension', 'store_ratings', 'has_image', 'TINYINT',
 '是否有图评价(0=否 1=是)', NULL, '店铺域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

-- 交易域指标（核心）
('订单数量', 'metric', 'orders', 'order_id', 'BIGINT',
 '订单总数', 'COUNT', '交易域',
 1, 'daily,weekly,monthly,quarter,year', '时间+店铺+用户', NULL,
 'V1.0', '2024-01-01'),

('GMV成交总额', 'metric', 'orders', 'total_amount', 'DECIMAL(12,2)',
 '订单总金额(GMV)', 'SUM', '交易域',
 0, 'daily,weekly,monthly,quarter,year', '时间+地区+渠道+店铺', "order_status='paid'",
 'V1.0', '2024-01-01'),

('实付金额总额', 'metric', 'orders', 'pay_amount', 'DECIMAL(12,2)',
 '实际支付金额合计', 'SUM', '交易域',
 0, 'daily,weekly,monthly', '时间+店铺', "order_status='paid'",
 'V1.0', '2024-01-01'),

('优惠金额总额', 'metric', 'orders', 'discount_amount', 'DECIMAL(12,2)',
 '优惠减免金额合计', 'SUM', '交易域',
 0, 'daily,monthly', '时间', NULL,
 'V1.0', '2024-01-01'),

('客单价', 'metric', 'orders', 'pay_amount', 'DECIMAL(12,2)',
 '人均消费金额', 'AVG', '交易域',
 0, 'daily,weekly,monthly', '时间+店铺', "order_status='paid'",
 'V1.0', '2024-01-01'),

('运费总额', 'metric', 'orders', 'shipping_fee', 'DECIMAL(10,2)',
 '运费合计', 'SUM', '物流域',
 0, 'daily,monthly', '时间', NULL,
 'V1.0', '2024-01-01'),

-- 交易域维度
('订单状态', 'dimension', 'orders', 'order_status', 'ENUM',
 '订单状态(pending/paid/shipped/received/cancelled/refunding/refunded)', NULL, '交易域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('支付方式', 'dimension', 'orders', 'payment_method', 'ENUM',
 '支付方式(alipay/wechat/bank_card/balance/installment)', NULL, '交易域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('下单时间', 'dimension', 'orders', 'create_time', 'DATETIME',
 '下单时间', NULL, '交易域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('支付时间', 'dimension', 'orders', 'pay_time', 'DATETIME',
 '支付时间', NULL, '交易域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('发货时间', 'dimension', 'orders', 'ship_time', 'DATETIME',
 '发货时间', NULL, '交易域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('收货时间', 'dimension', 'orders', 'receive_time', 'DATETIME',
 '收货时间', NULL, '交易域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

-- 营销域指标
('优惠券发放量', 'metric', 'coupons', 'total_count', 'INT',
 '优惠券发放总数', 'SUM', '营销域',
 0, 'daily,monthly', '类型+状态', NULL,
 'V1.0', '2024-01-01'),

('核销率', 'metric', 'user_coupons', 'status', 'ENUM',
 '已使用占比', NULL, '营销域',
 1, 'daily,monthly', '时间+类型', "status='used'",
 'V1.0', '2024-01-01'),

('活动预算总额', 'metric', 'campaigns', 'budget', 'DECIMAL(12,2)',
 '活动预算合计', 'SUM', '营销域',
 0, 'daily', '类型+状态', NULL,
 'V1.0', '2024-01-01'),

('活动实际GMV', 'metric', 'campaigns', 'actual_gmv', 'DECIMAL(12,2)',
 '活动实际成交额（营销活动）', 'SUM', '营销域',
 0, 'daily', '类型+状态', NULL,
 'V1.0', '2024-01-01'),

('ROI投资回报率', 'metric', 'campaigns', 'actual_gmv', 'DECIMAL(12,2)',
 '投资回报率(actual_gmv/cost)', NULL, '营销域',
 0, 'daily', '类型', NULL,
 'V1.0', '2024-01-01'),

-- 营销域维度
('优惠券类型', 'dimension', 'coupons', 'coupon_type', 'ENUM',
 '券类型(fixed/percent/shipping)', NULL, '营销域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('优惠券状态', 'dimension', 'coupons', 'status', 'ENUM',
 '券状态(draft/active/expired/disabled)', NULL, '营销域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('活动类型', 'dimension', 'campaigns', 'campaign_type', 'ENUM',
 '活动类型(flash_sale/group_buy/full_reduction/gift/lottery)', NULL, '营销域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('活动状态', 'dimension', 'campaigns', 'status', 'ENUM',
 '活动状态(planned/active/ended/cancelled)', NULL, '营销域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

-- 物流域指标
('物流单数量', 'metric', 'shipments', 'shipment_id', 'BIGINT',
 '物流单总数', 'COUNT', '物流域',
 1, 'daily', '时间+快递公司', NULL,
 'V1.0', '2024-01-01'),

('签收率', 'metric', 'shipments', 'status', 'ENUM',
 '投递成功占比', NULL, '物流域',
 1, 'daily', '时间+快递公司', "status='delivered'",
 'V1.0', '2024-01-01'),

('平均送达时长', 'metric', 'shipments', 'deliver_time', 'DATETIME',
 '平均送达时间(小时)', NULL, '物流域',
 0, 'daily', '快递公司', NULL,
 'V1.0', '2024-01-01'),

('包裹重量均值', 'metric', 'shipments', 'weight', 'DECIMAL(8,2)',
 '包裹平均重量', 'AVG', '物流域',
 0, 'daily', NULL, NULL,
 'V1.0', '2024-01-01'),

-- 物流域维度
('快递公司', 'dimension', 'shipments', 'carrier', 'ENUM',
 '快递公司(sf/yd/zt/sto/yt/ems/jd)', NULL, '物流域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01'),

('物流状态', 'dimension', 'shipments', 'status', 'ENUM',
 '物流状态(pending/picked_up/in_transit/delivered/failed/returned)', NULL, '物流域',
 0, NULL, NULL, NULL, 'V1.0', '2024-01-01')

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- 步骤2：口语别名映射表数据
-- ============================================================

INSERT INTO `spoken_aliases` (`spoken_term`, `standard_name`, `alias_type`, `frequency`, `source`) VALUES
('买家', '用户数量', 'entity', 45, 'dataset'),
('客户', '用户数量', 'entity', 32, 'dataset'),
('顾客', '用户数量', 'entity', 18, 'dataset'),
('会员', '用户数量', 'entity', 28, 'dataset'),
('货品', '商品数量', 'entity', 35, 'dataset'),
('物品', '商品数量', 'entity', 22, 'dataset'),
('商家', '店铺数量', 'entity', 40, 'dataset'),
('卖家', '店铺数量', 'entity', 30, 'dataset'),
('商户', '店铺数量', 'entity', 15, 'dataset'),
('快递', '物流单数量', 'entity', 38, 'dataset'),
('包裹', '物流单数量', 'entity', 25, 'dataset'),
('券', '优惠券发放量', 'entity', 20, 'dataset'),
('折扣券', '优惠券发放量', 'entity', 18, 'dataset'),
('价格', '平均价格', 'field', 65, 'dataset'),
('售价', '平均价格', 'field', 48, 'dataset'),
('单价', '平均价格', 'field', 32, 'dataset'),
('定价', '平均价格', 'field', 15, 'dataset'),
('销量', '总销量', 'field', 78, 'dataset'),
('累计销量', '总销量', 'field', 42, 'dataset'),
('总销量', '总销量', 'field', 55, 'dataset'),
('会员等级', '用户等级', 'field', 35, 'dataset'),
('VIP等级', '用户等级', 'field', 28, 'dataset'),
('收到了', '已签收', 'value', 42, 'dataset'),
('已收货', '已签收', 'value', 58, 'dataset'),
('还没付', '待付款', 'value', 28, 'dataset'),
('未付款', '待付款', 'value', 35, 'dataset'),
('发出去了', '已发货', 'value', 22, 'dataset'),
('免邮', '包邮', 'value', 18, 'dataset'),
('免运费', '包邮', 'value', 25, 'dataset'),
('限时抢购', '秒杀', 'value', 15, 'dataset'),
('团购', '拼团', 'value', 12, 'dataset'),
('成交总额', 'GMV成交总额', 'term', 200, 'dataset'),
('成交额', 'GMV成交总额', 'term', 180, 'dataset'),
('月GMV', 'GMV成交总额', 'term', 150, 'dataset'),
('每月GMV', 'GMV成交总额', 'term', 150, 'dataset'),
('销售额', 'GMV成交总额', 'term', 170, 'dataset'),
('月度GMV', 'GMV成交总额', 'term', 140, 'dataset'),
('总销售额', 'GMV成交总额', 'term', 160, 'dataset'),
('店铺销售额', '店铺总销售额', 'term', 200, 'dataset'),
('店铺GMV', '店铺总销售额', 'term', 180, 'dataset'),
('店铺成交额', '店铺总销售额', 'term', 180, 'dataset'),
('商家销售额', 'GMV成交总额', 'term', 155, 'dataset'),
('人均消费', '客单价', 'term', 48, 'dataset'),
('人均金额', '客单价', 'term', 32, 'dataset'),
('使用率', '核销率', 'term', 28, 'dataset'),
('使用占比', '核销率', 'term', 18, 'dataset'),
('投递成功', '签收率', 'term', 35, 'dataset'),
('送达成功率', '签收率', 'term', 22, 'dataset'),
('DSR评分', 'DSR描述分', 'term', 40, 'dataset'),
('有图评价占比', '有图评价', 'term', 35, 'dataset'),
('有图率', '有图评价', 'term', 30, 'dataset'),
('带图评价', '有图评价', 'term', 25, 'dataset'),
('动态评分', 'DSR服务分', 'term', 25, 'dataset'),
ON DUPLICATE KEY UPDATE `frequency` = `frequency` + 1;


-- ============================================================
-- 步骤3：业务数据表元信息表数据
-- ============================================================

INSERT INTO `table_metadata` (`table_name`, `table_cn_name`, `description`, `domain`, `core_scenarios`) VALUES
('users', '用户表', '存储用户基本信息、等级、积分、余额等', '用户域', '["用户统计", "会员分析", "用户画像"]'),
('user_addresses', '用户地址表', '用户收货地址信息', '用户域', '["地址管理", "配送分析"]'),
('categories', '商品分类表', '商品分类层级结构（支持多级）', '商品域', '["品类分析", "分类统计"]'),
('products', '商品表', '商品主信息、价格、库存、销量、评分', '商品域', '["商品分析", "价格分析", "销量排行"]'),
('product_specs', '商品规格表', 'SKU规格信息', '商品域', '["SKU管理", "规格查询"]'),
('stores', '店铺表', '店铺基础信息、类型、销量、粉丝数', '店铺域', '["店铺分析", "商家排名"]'),
('store_ratings', '店铺评分表', '店铺DSR评分详情', '店铺域', '["服务质量", "好评率分析"]'),
('orders', '订单表', '订单主信息、状态流转、金额', '交易域', '["订单分析", "GMV统计", "转化率"]'),
('order_items', '订单明细表', '订单商品明细、退款信息', '交易域', '["商品销售", "退款分析"]'),
('payments', '支付记录表', '支付流水、支付方式', '交易域', '["支付分析", "渠道统计"]'),
('coupons', '优惠券模板表', '优惠券定义、规则', '营销域', '["优惠券分析", "营销效果"]'),
('campaigns', '促销活动表', '营销活动信息、ROI', '营销域', '["活动效果", "ROI分析"]'),
('user_coupons', '用户优惠券表', '用户领券用券记录', '营销域', '["核销率", "领券分析"]'),
('shipments', '物流单表', '物流发货信息、状态', '物流域', '["物流时效", "签收率"]'),
('shipment_tracks', '物流轨迹表', '物流跟踪节点', '物流域', '["轨迹查询", "时效分析"]')
ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- 步骤4：表直接关联关系表数据
-- ============================================================

INSERT INTO `table_relations` (`main_table`, `related_table`, `join_condition`, `join_type`, `description`) VALUES
('users', 'user_addresses', 'users.user_id = user_addresses.user_id', 'INNER', '用户-地址 一对多'),
('users', 'orders', 'users.user_id = orders.user_id', 'INNER', '用户-订单 一对多'),
('users', 'user_coupons', 'users.user_id = user_coupons.user_id', 'INNER', '用户-领券 一对多'),
('users', 'store_ratings', 'users.user_id = store_ratings.user_id', 'INNER', '用户-评分 一对多'),
('categories', 'products', 'categories.category_id = products.category_id', 'INNER', '分类-商品 一对多'),
('products', 'product_specs', 'products.product_id = product_specs.product_id', 'INNER', '商品-SKZ 一对多'),
('products', 'order_items', 'products.product_id = order_items.product_id', 'INNER', '商品-订单明细 一对多'),
('products', 'stores', 'products.store_id = stores.store_id', 'INNER', '商品-店铺 多对一'),
('stores', 'orders', 'stores.store_id = orders.store_id', 'INNER', '店铺-订单 一对多'),
('stores', 'store_ratings', 'stores.store_id = store_ratings.store_id', 'INNER', '店铺-评分 一对多'),
('stores', 'shipments', 'stores.store_id = shipments.store_id', 'INNER', '店铺-物流 一对多'),
('orders', 'order_items', 'orders.order_id = order_items.order_id', 'INNER', '订单-明细 一对多'),
('orders', 'payments', 'orders.order_id = payments.order_id', 'INNER', '订单-支付 一对一'),
('orders', 'shipments', 'orders.order_id = shipments.order_id', 'INNER', '订单-物流 一对一'),
('orders', 'user_coupons', 'orders.order_id = user_coupons.order_id', 'LEFT', '订单-用券 一对一'),
('orders', 'store_ratings', 'orders.order_id = store_ratings.order_id', 'LEFT', '订单-评分 一对多'),
('coupons', 'user_coupons', 'coupons.coupon_id = user_coupons.coupon_id', 'INNER', '优惠券模板-领取 一对多'),
('campaigns', 'stores', 'campaigns.store_id = stores.store_id', 'LEFT', '活动-店铺 多对一'),
('shipments', 'shipment_tracks', 'shipments.shipment_id = shipment_tracks.shipment_id', 'INNER', '物流单-轨迹 一对多')
ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- 步骤5：业务规则表数据 (V5.0新增)
-- ============================================================

INSERT INTO `business_rules` (
    `rule_name`, `rule_type`, `target_metric`, `target_dimension`,
    `rule_content`, `rule_desc`, `priority`, `error_message`
) VALUES
-- 过滤规则
('GMV仅统计已支付订单', 'filter', 'GMV成交总额', NULL,
 "order_status='paid'",
 'GMV只统计已支付的订单，排除未付款订单',
 100, '⚠️ GMV仅统计已支付订单'),

('客单价仅统计已支付', 'filter', '客单价', NULL,
 "order_status='paid'",
 '客单价只统计已支付订单',
 100, '⚠️ 客单价仅统计已支付订单'),

('签收率仅统计已签收', 'filter', '签收率', NULL,
 "status='delivered'",
 '签收率只统计已签收的物流单',
 100, '⚠️ 签收率仅统计已签收'),

-- 校验规则
('去重类指标跨粒度警告', 'validation', '用户数量', NULL,
 "granularity NOT IN ('daily','weekly')",
 '用户数量是去重类指标，跨粒度聚合可能导致数据失真',
 50, '⚠️ 去重类指标不建议跨粒度汇总'),

('去重类指标跨粒度警告', 'validation', '订单数量', NULL,
 "granularity NOT IN ('daily','weekly')",
 '订单数量是去重类指标，跨粒度聚合可能导致数据失真',
 50, '⚠️ 去重类指标不建议跨粒度汇总'),

('去重类指标跨粒度警告', 'validation', '商品数量', NULL,
 "granularity NOT IN ('daily','weekly')",
 '商品数量是去重类指标，跨粒度聚合可能导致数据失真',
 50, '⚠️ 去重类指标不建议跨粒度汇总'),

-- 计算规则
('客单价计算公式', 'calc', '客单价', NULL,
 'SUM(pay_amount) / COUNT(DISTINCT user_id)',
 '客单价 = 实付金额 / 下单用户数',
 30, NULL),

('ROI计算公式', 'calc', 'ROI投资回报率', NULL,
 'actual_gmv / cost',
 'ROI = 活动GMV / 活动成本',
 30, NULL)

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- 步骤6：维度层级表数据 (V5.0新增)
-- ============================================================

INSERT INTO `dimension_hierarchies` (
    `dimension_name`, `level_name`, `level_order`,
    `physical_table`, `physical_field`, `field_format`, `description`
) VALUES
-- 时间维度层级
('下单时间', '年', 1, 'orders', 'create_time', '%Y', '年度'),
('下单时间', '季度', 2, 'orders', 'create_time', '%Y-Q', '季度'),
('下单时间', '月', 3, 'orders', 'create_time', '%Y-%m', '月度'),
('下单时间', '周', 4, 'orders', 'create_time', '%Y-%W', '周度'),
('下单时间', '日', 5, 'orders', 'create_time', '%Y-%m-%d', '日度'),

-- 地区维度层级
('所在城市', '省份', 1, 'stores', 'province', NULL, '省份'),
('所在城市', '城市', 2, 'stores', 'city', NULL, '城市'),

('用户地址-省份', '省份', 1, 'user_addresses', 'province', NULL, '省份'),
('用户地址-城市', '城市', 2, 'user_addresses', 'city', NULL, '城市'),

-- 商品分类层级
('商品分类', '一级分类', 1, 'categories', 'category_name', NULL, '一级分类'),
('商品分类', '二级分类', 2, 'categories', 'category_name', NULL, '二级分类'),

-- 用户等级层级
('用户等级', 'VIP等级', 1, 'users', 'user_level', NULL, 'VIP等级')

ON DUPLICATE KEY UPDATE `description` = `description`;
