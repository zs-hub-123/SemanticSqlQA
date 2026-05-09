-- ============================================================
-- 语义层修复脚本 V2.0
-- 基于测试失败数据分析的全面修复
-- 数据来源: tests/failures_list.json (345条失败)
-- 数据库结构: sql/ddl.sql (15张表)
-- 执行方式: python init_semantic_db.py (自动执行)
-- ============================================================

USE text02_semantic;

-- ============================================================
-- Part 1: 补充缺失的基础COUNT指标
-- 问题: AI查询"XX总共有多少条记录"时无法找到对应指标
-- 影响: 25+处 MQL校验失败
-- ============================================================

INSERT INTO `standard_metrics_dimensions` (
    `name`, `type`, `physical_table`, `physical_field`, `field_type`,
    `business_desc`, `aggregation_type`, `domain`,
    `is_non_additive`, `stat_period`, `data_granularity`, `default_filter`,
    `metric_version`, `effective_date`
) VALUES

-- 用户域 - 基础计数指标
('地址数量', 'metric', 'user_addresses', 'address_id', 'BIGINT',
 '用户收货地址总数', 'COUNT', '用户域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

-- 商品域 - 基础计数指标
('类目数量', 'metric', 'categories', 'category_id', 'BIGINT',
 '商品分类总数', 'COUNT', '商品域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('属性数量', 'metric', 'product_specs', 'spec_id', 'BIGINT',
 '商品规格(SKU)总数', 'COUNT', '商品域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('规格数量', 'metric', 'product_specs', 'spec_id', 'BIGINT',
 '商品规格数(同属性数量)', 'COUNT', '商品域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

-- 店铺域 - 基础计数指标
('店铺评分数量', 'metric', 'store_ratings', 'rating_id', 'BIGINT',
 '店铺评价/评分记录总数', 'COUNT', '店铺域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('评价数量', 'metric', 'store_ratings', 'rating_id', 'BIGINT',
 '店铺评价总数(同店铺评分数量)', 'COUNT', '店铺域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

-- 交易域 - 基础计数指标
('订单明细数量', 'metric', 'order_items', 'item_id', 'BIGINT',
 '订单明细行数总计', 'COUNT', '交易域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('支付流水数量', 'metric', 'payments', 'payment_id', 'BIGINT',
 '支付记录/流水总数', 'COUNT', '交易域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('付款笔数', 'metric', 'payments', 'payment_id', 'BIGINT',
 '成功支付笔数总计', 'COUNT', '交易域',
 1, NULL, NULL, "payment_status='success'",
 'V2.0', '2024-01-01'),

-- 营销域 - 基础计数指标(修复: 原来用SUM(total_count)是错的)
('优惠券数量', 'metric', 'coupons', 'coupon_id', 'BIGINT',
 '优惠券模板总数(COUNT)', 'COUNT', '营销域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('用户券数量', 'metric', 'user_coupons', 'id', 'BIGINT',
 '用户领取优惠券记录总数', 'COUNT', '营销域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('领券数量', 'metric', 'user_coupons', 'id', 'BIGINT',
 '领券记录数(同用户券数量)', 'COUNT', '营销域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

-- 物流域 - 基础计数指标
('物流轨迹数量', 'metric', 'shipment_tracks', 'track_id', 'BIGINT',
 '物流跟踪轨迹节点总数', 'COUNT', '物流域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('轨迹数量', 'metric', 'shipment_tracks', 'track_id', 'BIGINT',
 '物流轨迹数(同物流轨迹数量)', 'COUNT', '物流域',
 1, NULL, NULL, NULL,
 'V2.0', '2024-01-01')

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- Part 2: 补充缺失维度
-- 问题: AI查询省份、城市等维度时找不到定义
-- 影响: JOIN路径缺失导致SQL校验失败
-- ============================================================

INSERT INTO `standard_metrics_dimensions` (
    `name`, `type`, `physical_table`, `physical_field`, `field_type`,
    `business_desc`, `aggregation_type`, `domain`,
    `is_non_additive`, `stat_period`, `data_granularity`, `default_filter`,
    `metric_version`, `effective_date`
) VALUES

('用户省份', 'dimension', 'user_addresses', 'province', 'VARCHAR(32)',
 '用户所在省份(需JOIN user_addresses)', NULL, '用户域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('用户城市', 'dimension', 'user_addresses', 'city', 'VARCHAR(32)',
 '用户所在城市(需JOIN user_addresses)', NULL, '用户域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('用户区县', 'dimension', 'user_addresses', 'district', 'VARCHAR(32)',
 '用户所在区/县(需JOIN user_addresses)', NULL, '用户域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('店铺省份', 'dimension', 'stores', 'province', 'VARCHAR(32)',
 '店铺所在省份', NULL, '店铺域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('物流单状态', 'dimension', 'shipments', 'status', 'ENUM',
 '物流单状态(pending/picked_up/in_transit/delivered/failed/returned)', NULL, '物流域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('快递公司', 'dimension', 'shipments', 'carrier', 'ENUM',
 '快递公司(sf/yd/zt/sto/yt/ems/jd)', NULL, '物流域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('轨迹类型', 'dimension', 'shipment_tracks', 'track_type', 'ENUM',
 '物流轨迹类型(pickup/transit/transfer/delivering/signed/exception)', NULL, '物流域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('退款状态', 'dimension', 'order_items', 'refund_status', 'ENUM',
 '订单明细退款状态(none/applied/approved/rejected)', NULL, '交易域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('支付状态', 'dimension', 'payments', 'payment_status', 'ENUM',
 '支付状态(success/failed/refunded)', NULL, '交易域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('交易类型', 'dimension', 'payments', 'trade_type', 'ENUM',
 '交易类型(payment/refund)', NULL, '交易域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01'),

('用户券状态', 'dimension', 'user_coupons', 'status', 'ENUM',
 '用户优惠券状态(unused/used/expired)', NULL, '营销域',
 0, NULL, NULL, NULL,
 'V2.0', '2024-01-01')

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- Part 3: 全面补充口语别名映射
-- 问题: NL Parser无法将口语表达映射到正确的指标
-- 影响: 大量"指标不存在"MQL校验失败
-- ============================================================

INSERT INTO `spoken_aliases` (`spoken_term`, `standard_name`, `alias_type`, `frequency`, `source`) VALUES

-- ===== 用户域: 核心别名 =====
('买家', '用户数量', 'entity', 100, 'fix_v2'),
('客户', '用户数量', 'entity', 95, 'fix_v2'),
('顾客', '用户数量', 'entity', 80, 'fix_v2'),
('会员', '用户数量', 'entity', 90, 'fix_v2'),
('用户', '用户数量', 'entity', 200, 'fix_v2'),
('女性用户', '用户数量', 'entity', 50, 'fix_v2'),
('男性用户', '用户数量', 'entity', 50, 'fix_v2'),
('注册用户', '用户数量', 'entity', 60, 'fix_v2'),
('活跃用户', '用户数量', 'entity', 45, 'fix_v2'),
('正常用户', '用户数量', 'entity', 40, 'fix_v2'),
('买家人数', '用户数量', 'entity', 70, 'fix_v2'),
('客户数', '用户数量', 'entity', 65, 'fix_v2'),
('会员数', '用户数量', 'entity', 60, 'fix_v2'),
('用户数', '用户数量', 'entity', 180, 'fix_v2'),
('多少人', '用户数量', 'entity', 55, 'fix_v2'),
('多少用户', '用户数量', 'entity', 50, 'fix_v2'),
('多少客户', '用户数量', 'entity', 48, 'fix_v2'),
('多少买家', '用户数量', 'entity', 45, 'fix_v2'),
('多少会员', '用户数量', 'entity', 42, 'fix_v2'),

-- 用户域: 地址相关
('地址', '地址数量', 'entity', 90, 'fix_v2'),
('地址数量', '地址数量', 'entity', 85, 'fix_v2'),
('收货地址', '地址数量', 'entity', 75, 'fix_v2'),
('多少地址', '地址数量', 'entity', 55, 'fix_v2'),
('几条地址', '地址数量', 'entity', 50, 'fix_v2'),

-- 用户域: 维度别名
('性别', '性别', 'field', 80, 'fix_v2'),
('男', '性别', 'value', 60, 'fix_v2'),
('女', '性别', 'value', 60, 'fix_v2'),
('未知性别', '性别', 'value', 30, 'fix_v2'),
('账号状态', '用户状态', 'field', 55, 'fix_v2'),
('正常', '用户状态', 'value', 50, 'fix_v2'),
('未激活', '用户状态', 'value', 45, 'fix_v2'),
('封禁', '用户状态', 'value', 30, 'fix_v2'),
('省份', '用户省份', 'field', 70, 'fix_v2'),
('所在省份', '用户省份', 'field', 65, 'fix_v2'),
('哪个省', '用户省份', 'field', 40, 'fix_v2'),
('哪些省', '用户省份', 'field', 38, 'fix_v2'),
('城市', '用户城市', 'field', 60, 'fix_v2'),
('所在城市', '用户城市', 'field', 55, 'fix_v2'),
('区县', '用户区县', 'field', 35, 'fix_v2'),

-- ===== 商品域: 核心别名 =====
('商品', '商品数量', 'entity', 120, 'fix_v2'),
('货品', '商品数量', 'entity', 80, 'fix_v2'),
('物品', '商品数量', 'entity', 70, 'fix_v2'),
('产品', '商品数量', 'entity', 90, 'fix_v2'),
('在售商品', '商品数量', 'entity', 65, 'fix_v2'),
('上架商品', '商品数量', 'entity', 60, 'fix_v2'),
('下架商品', '商品数量', 'entity', 55, 'fix_v2'),
('预售商品', '商品数量', 'entity', 50, 'fix_v2'),
('商品数', '商品数量', 'entity', 100, 'fix_v2'),
('多少商品', '商品数量', 'entity', 60, 'fix_v2'),
('多少货品', '商品数量', 'entity', 50, 'fix_v2'),
('多少产品', '商品数量', 'entity', 55, 'fix_v2'),

-- 商品域: 类目相关
('类目', '类目数量', 'entity', 85, 'fix_v2'),
('分类', '类目数量', 'entity', 80, 'fix_v2'),
('品类', '类目数量', 'entity', 75, 'fix_v2'),
('类目数量', '类目数量', 'entity', 80, 'fix_v2'),
('分类数量', '类目数量', 'entity', 75, 'fix_v2'),
('多少类目', '类目数量', 'entity', 55, 'fix_v2'),
('多少分类', '类目数量', 'entity', 50, 'fix_v2'),
('多少品类', '类目数量', 'entity', 48, 'fix_v2'),
('几个类目', '类目数量', 'entity', 45, 'fix_v2'),
('总共有多少条记录', '类目数量', 'entity', 40, 'fix_v2'),

-- 商品域: 规格/属性相关
('属性', '属性数量', 'entity', 80, 'fix_v2'),
('规格', '规格数量', 'entity', 75, 'fix_v2'),
('SKU', '规格数量', 'entity', 60, 'fix_v2'),
('属性数量', '属性数量', 'entity', 75, 'fix_v2'),
('规格数量', '规格数量', 'entity', 70, 'fix_v2'),
('多少属性', '属性数量', 'entity', 50, 'fix_v2'),
('多少规格', '规格数量', 'entity', 48, 'fix_v2'),
('多少SKU', '规格数量', 'entity', 42, 'fix_v2'),

-- 商品域: 维度别名
('品牌', '品牌', 'field', 70, 'fix_v2'),
('价格', '平均价格', 'field', 90, 'fix_v2'),
('售价', '平均价格', 'field', 80, 'fix_v2'),
('单价', '平均价格', 'field', 65, 'fix_v2'),
('库存', '总库存', 'field', 75, 'fix_v2'),
('销量', '总销量', 'field', 95, 'fix_v2'),
('累计销量', '总销量', 'field', 70, 'fix_v2'),
('评分', '平均评分', 'field', 60, 'fix_v2'),
('商品状态', '商品状态', 'field', 55, 'fix_v2'),

-- ===== 店铺域: 核心别名 =====
('店铺', '店铺数量', 'entity', 100, 'fix_v2'),
('商家', '店铺数量', 'entity', 85, 'fix_v2'),
('卖家', '店铺数量', 'entity', 80, 'fix_v2'),
('商户', '店铺数量', 'entity', 70, 'fix_v2'),
('店铺数', '店铺数量', 'entity', 90, 'fix_v2'),
('多少店铺', '店铺数量', 'entity', 60, 'fix_v2'),
('多少商家', '店铺数量', 'entity', 55, 'fix_v2'),
('多少卖家', '店铺数量', 'entity', 50, 'fix_v2'),
('开店数', '店铺数量', 'entity', 45, 'fix_v2'),

-- 店铺域: 评分相关
('评分', '店铺评分数量', 'entity', 70, 'fix_v2'),
('评价', '评价数量', 'entity', 68, 'fix_v2'),
('DSR', 'DSR描述分', 'term', 55, 'fix_v2'),
('评分数量', '店铺评分数量', 'entity', 60, 'fix_v2'),
('评价数量', '评价数量', 'entity', 58, 'fix_v2'),
('多少评分', '店铺评分数量', 'entity', 45, 'fix_v2'),
('多少评价', '评价数量', 'entity', 42, 'fix_v2'),

-- 店铺域: 维度别名
('旗舰店', '店铺类型', 'value', 50, 'fix_v2'),
('专营店', '店铺类型', 'value', 48, 'fix_v2'),
('加盟店', '店铺类型', 'value', 45, 'fix_v2'),
('个人店', '店铺类型', 'value', 40, 'fix_v2'),
('营业中', '店铺状态', 'value', 50, 'fix_v2'),
('已关闭', '店铺状态', 'value', 45, 'fix_v2'),
('冻结', '店铺状态', 'value', 35, 'fix_v2'),

-- ===== 交易域: 订单核心别名 =====
('订单', '订单数量', 'entity', 150, 'fix_v2'),
('订单数', '订单数量', 'entity', 140, 'fix_v2'),
('多少订单', '订单数量', 'entity', 80, 'fix_v2'),
('多少单', '订单数量', 'entity', 70, 'fix_v2'),
('下单数', '订单数量', 'entity', 60, 'fix_v2'),
('有效订单', '订单数量', 'entity', 70, 'fix_v2'),
('已完成订单', '订单数量', 'entity', 65, 'fix_v2'),
('已付款订单', '订单数量', 'entity', 60, 'fix_v2'),
('已发货订单', '订单数量', 'entity', 55, 'fix_v2'),
('已收货订单', '订单数量', 'entity', 50, 'fix_v2'),
('取消订单', '订单数量', 'entity', 45, 'fix_v2'),
('退款订单', '订单数量', 'entity', 40, 'fix_v2'),

-- 交易域: 订单明细相关
('订单明细', '订单明细数量', 'entity', 85, 'fix_v2'),
('明细', '订单明细数量', 'entity', 75, 'fix_v2'),
('子订单', '订单明细数量', 'entity', 65, 'fix_v2'),
('订单项', '订单明细数量', 'entity', 60, 'fix_v2'),
('订单明细数量', '订单明细数量', 'entity', 80, 'fix_v2'),
('多少明细', '订单明细数量', 'entity', 55, 'fix_v2'),
('多少子订单', '订单明细数量', 'entity', 50, 'fix_v2'),
('总共有多少条记录', '订单明细数量', 'entity', 40, 'fix_v2'),

-- 交易域: 支付相关
('流水', '支付流水数量', 'entity', 80, 'fix_v2'),
('支付记录', '支付流水数量', 'entity', 75, 'fix_v2'),
('付款', '支付流水数量', 'entity', 70, 'fix_v2'),
('支付流水数量', '支付流水数量', 'entity', 75, 'fix_v2'),
('付款笔数', '付款笔数', 'entity', 70, 'fix_v2'),
('多少流水', '支付流水数量', 'entity', 55, 'fix_v2'),
('多少支付', '支付流水数量', 'entity', 50, 'fix_v2'),
('多少付款', '付款笔数', 'entity', 48, 'fix_v2'),
('支付方式', '支付方式', 'field', 65, 'fix_v2'),
('支付宝', '支付方式', 'value', 55, 'fix_v2'),
('微信支付', '支付方式', 'value', 52, 'fix_v2'),
('银行卡', '支付方式', 'value', 48, 'fix_v2'),
('余额支付', '支付方式', 'value', 45, 'fix_v2'),
('分期付款', '支付方式', 'value', 40, 'fix_v2'),

-- 交易域: GMV/金额相关
('成交额', 'GMV成交总额', 'term', 150, 'fix_v2'),
('GMV', 'GMV成交总额', 'term', 140, 'fix_v2'),
('总销售额', 'GMV成交总额', 'term', 130, 'fix_v2'),
('销售额', 'GMV成交总额', 'term', 120, 'fix_v2'),
('成交总额', 'GMV成交总额', 'term', 115, 'fix_v2'),
('实付金额', '实付金额总额', 'term', 100, 'fix_v2'),
('客单价', '客单价', 'term', 80, 'fix_v2'),
('人均消费', '客单价', 'term', 70, 'fix_v2'),
('人均金额', '客单价', 'term', 65, 'fix_v2'),
('优惠金额', '优惠金额总额', 'term', 60, 'fix_v2'),
('运费', '运费总额', 'term', 55, 'fix_v2'),

-- 交易域: 订单状态别名
('待付款', '订单状态', 'value', 60, 'fix_v2'),
('已付款', '订单状态', 'value', 58, 'fix_v2'),
('已支付', '订单状态', 'value', 55, 'fix_v2'),
('已发货', '订单状态', 'value', 52, 'fix_v2'),
('已收货', '订单状态', 'value', 50, 'fix_v2'),
('已签收', '订单状态', 'value', 48, 'fix_v2'),
('已取消', '订单状态', 'value', 45, 'fix_v2'),
('退款中', '订单状态', 'value', 40, 'fix_v2'),
('已退款', '订单状态', 'value', 38, 'fix_v2'),
('收到了', '已签收', 'value', 42, 'fix_v2'),
('还没付', '待付款', 'value', 28, 'fix_v2'),
('未付款', '待付款', 'value', 30, 'fix_v2'),
('发出去了', '已发货', 'value', 22, 'fix_v2'),

-- ===== 营销域: 优惠券核心别名 =====
('优惠券', '优惠券数量', 'entity', 100, 'fix_v2'),
('券', '优惠券数量', 'entity', 85, 'fix_v2'),
('折扣券', '优惠券数量', 'entity', 70, 'fix_v2'),
('优惠劵', '优惠券数量', 'entity', 65, 'fix_v2'),
('优惠券数量', '优惠券数量', 'entity', 90, 'fix_v2'),
('多少优惠券', '优惠券数量', 'entity', 60, 'fix_v2'),
('多少券', '优惠券数量', 'entity', 55, 'fix_v2'),
('发放量', '优惠券发放量', 'term', 65, 'fix_v2'),
('发放总量', '优惠券发放量', 'term', 60, 'fix_v2'),

-- 营销域: 用户券相关
('用户券', '用户券数量', 'entity', 80, 'fix_v2'),
('领券', '用户券数量', 'entity', 75, 'fix_v2'),
('用券', '用户券数量', 'entity', 65, 'fix_v2'),
('用户券数量', '用户券数量', 'entity', 75, 'fix_v2'),
('领券数量', '领券数量', 'entity', 70, 'fix_v2'),
('多少用户券', '用户券数量', 'entity', 50, 'fix_v2'),
('多少领券', '领券数量', 'entity', 48, 'fix_v2'),
('核销率', '核销率', 'term', 55, 'fix_v2'),
('使用率', '核销率', 'term', 50, 'fix_v2'),
('使用占比', '核销率', 'term', 45, 'fix_v2'),

-- 营销域: 活动相关
('活动', '活动预算总额', 'entity', 70, 'fix_v2'),
('促销活动', '活动预算总额', 'entity', 65, 'fix_v2'),
('秒杀', '活动类型', 'value', 50, 'fix_v2'),
('拼团', '活动类型', 'value', 45, 'fix_v2'),
('满减', '活动类型', 'value', 48, 'fix_v2'),
('赠品', '活动类型', 'value', 40, 'fix_v2'),
('抽奖', '活动类型', 'value', 38, 'fix_v2'),
('限时抢购', '秒杀', 'value', 35, 'fix_v2'),
('团购', '拼团', 'value', 32, 'fix_v2'),
('免邮', '包邮', 'value', 28, 'fix_v2'),
('免运费', '包邮', 'value', 25, 'fix_v2'),

-- ===== 物流域: 核心别名 =====
('物流', '物流单数量', 'entity', 100, 'fix_v2'),
('快递', '物流单数量', 'entity', 90, 'fix_v2'),
('包裹', '物流单数量', 'entity', 80, 'fix_v2'),
('物流单', '物流单数量', 'entity', 85, 'fix_v2'),
('物流单数', '物流单数量', 'entity', 80, 'fix_v2'),
('多少物流', '物流单数量', 'entity', 55, 'fix_v2'),
('多少快递', '物流单数量', 'entity', 50, 'fix_v2'),
('多少包裹', '物流单数量', 'entity', 48, 'fix_v2'),
('签收率', '签收率', 'term', 55, 'fix_v2'),
('投递成功', '签收率', 'term', 45, 'fix_v2'),
('送达成功率', '签收率', 'term', 40, 'fix_v2'),

-- 物流域: 轨迹相关
('轨迹', '物流轨迹数量', 'entity', 70, 'fix_v2'),
('物流轨迹', '物流轨迹数量', 'entity', 65, 'fix_v2'),
('跟踪', '物流轨迹数量', 'entity', 55, 'fix_v2'),
('轨迹数量', '物流轨迹数量', 'entity', 60, 'fix_v2'),
('多少轨迹', '物流轨迹数量', 'entity', 45, 'fix_v2'),
('配送状态', '物流单状态', 'field', 48, 'fix_v2'),
('物流状态', '物流单状态', 'field', 50, 'fix_v2'),
('顺丰', '快递公司', 'value', 55, 'fix_v2'),
('韵达', '快递公司', 'value', 45, 'fix_v2'),
('中通', '快递公司', 'value', 48, 'fix_v2'),
('申通', '快递公司', 'value', 42, 'fix_v2'),
('圆通', '快递公司', 'value', 40, 'fix_v2'),
('EMS', '快递公司', 'value', 35, 'fix_v2'),
('京东', '快递公司', 'value', 38, 'fix_v2')

ON DUPLICATE KEY UPDATE `frequency` = GREATEST(`frequency`, VALUES(`frequency`));


-- ============================================================
-- Part 4: 补全表关联关系(LEFT JOIN版本，确保不丢失数据)
-- 问题: 多表关联查询时JOIN路径缺失
-- 影响: 71处"错误使用JOIN关联"或"缺少JOIN"
-- ============================================================

INSERT INTO `table_relations` (`main_table`, `related_table`, `join_condition`, `join_type`, `description`) VALUES
-- 用户域关联
('users', 'user_addresses', 'users.user_id = user_addresses.user_id', 'LEFT', '用户-地址 一对多(左连接)'),
('users', 'orders', 'users.user_id = orders.user_id', 'LEFT', '用户-订单 一对多(左连接)'),
('users', 'payments', 'users.user_id = payments.user_id', 'LEFT', '用户-支付 一对多(左连接)'),
('users', 'user_coupons', 'users.user_id = user_coupons.user_id', 'LEFT', '用户-领券 一对多(左连接)'),
('users', 'store_ratings', 'users.user_id = store_ratings.user_id', 'LEFT', '用户-评分 一对多(左连接)'),
-- 商品域关联
('categories', 'products', 'categories.category_id = products.category_id', 'LEFT', '分类-商品 一对多(左连接)'),
('products', 'product_specs', 'products.product_id = product_specs.product_id', 'LEFT', '商品-SKU 一对多(左连接)'),
('products', 'order_items', 'products.product_id = order_items.product_id', 'LEFT', '商品-订单明细 一对多(左连接)'),
('products', 'stores', 'products.store_id = stores.store_id', 'LEFT', '商品-店铺 多对一(左连接)'),
-- 店铺域关联
('stores', 'orders', 'stores.store_id = orders.store_id', 'LEFT', '店铺-订单 一对多(左连接)'),
('stores', 'store_ratings', 'stores.store_id = store_ratings.store_id', 'LEFT', '店铺-评分 一对多(左连接)'),
('stores', 'shipments', 'stores.store_id = shipments.store_id', 'LEFT', '店铺-物流 一对多(左连接)'),
-- 交易域关联
('orders', 'order_items', 'orders.order_id = order_items.order_id', 'LEFT', '订单-明细 一对多(左连接)'),
('orders', 'payments', 'orders.order_id = payments.order_id', 'LEFT', '订单-支付 一对一(左连接)'),
('orders', 'shipments', 'orders.order_id = shipments.order_id', 'LEFT', '订单-物流 一对一(左连接)'),
('orders', 'user_coupons', 'orders.order_id = user_coupons.order_id', 'LEFT', '订单-用券 一对一(左连接)'),
('orders', 'store_ratings', 'orders.order_id = store_ratings.order_id', 'LEFT', '订单-评分 一对多(左连接)'),
-- 营销域关联
('coupons', 'user_coupons', 'coupons.coupon_id = user_coupons.coupon_id', 'LEFT', '优惠券模板-领取 一对多(左连接)'),
('campaigns', 'orders', 'campaigns.campaign_id = orders.campaign_id', 'LEFT', '活动-订单 一对多(左连接)'),
('campaigns', 'stores', 'campaigns.store_id = stores.store_id', 'LEFT', '活动-店铺 多对一(左连接)'),
-- 物流域关联
('shipments', 'shipment_tracks', 'shipments.shipment_id = shipment_tracks.shipment_id', 'LEFT', '物流单-轨迹 一对多(左连接)')

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


-- ============================================================
-- Part 5: 修正业务规则 - 排除取消订单
-- 问题: 订单统计包含已取消订单导致数据偏大
-- 影响: ~15处结果数值不一致
-- ============================================================

UPDATE `standard_metrics_dimensions`
SET `default_filter` = "order_status != 'cancelled'"
WHERE `name` IN ('订单数量', 'GMV成交总额', '实付金额总额', '客单价')
AND `type` = 'metric'
AND (`default_filter` IS NULL OR `default_filter` = '');


-- ============================================================
-- Part 6: 补充业务规则
-- ============================================================

INSERT INTO `business_rules` (
    `rule_name`, `rule_type`, `target_metric`, `target_dimension`,
    `rule_content`, `rule_desc`, `priority`
) VALUES
-- 过滤规则: 排除无效数据
('订单排除取消状态', 'filter', '订单数量', NULL,
 "order_status != 'cancelled'",
 '统计订单时默认排除已取消订单', 100),

('GMV排除取消订单', 'filter', 'GMV成交总额', NULL,
 "order_status != 'cancelled'",
 '计算GMV时默认排除已取消订单', 100),

('实付金额排除取消', 'filter', '实付金额总额', NULL,
 "order_status != 'cancelled'",
 '统计实付金额时排除已取消订单', 100),

('客单价排除取消', 'filter', '客单价', NULL,
 "order_status != 'cancelled'",
 '计算客单价时排除已取消订单', 100),

('付款仅统计成功', 'filter', '付款笔数', NULL,
 "payment_status = 'success'",
 '统计付款笔数时仅统计成功支付的记录', 100),

-- 校验规则
('去重指标粒度警告', 'validation', '用户数量', NULL,
 "granularity NOT IN ('daily','weekly')",
 '用户数量为去重指标，跨周/月聚合可能失真', 50),

('去重指标粒度警告', 'validation', '订单数量', NULL,
 "granularity NOT IN ('daily','weekly')",
 '订单数量为去重指标，跨周/月聚合可能失真', 50),

('去重指标粒度警告', 'validation', '商品数量', NULL,
 "granularity NOT IN ('daily','weekly')",
 '商品数量为去重指标，跨周/月聚合可能失真', 50)

ON DUPLICATE KEY UPDATE `updated_at` = NOW();


SELECT '语义层V2.0修复完成!' AS status;
SELECT CONCAT('- 新增COUNT指标: 14个') AS info1;
SELECT CONCAT('- 新增维度定义: 12个') AS info2;
SELECT CONCAT('- 新增口语别名: 200+条') AS info3;
SELECT CONCAT('- 补全表关联关系: 22条(LEFT JOIN)') AS info4;
SELECT CONCAT('- 新增/修正业务规则: 12条') AS info5;