-- ============================================================
-- 电商场景 Text2SQL 数据集 - DDL 定义
-- 数据库: MySQL 8.0+
-- 共 15 张表，按域分组
-- 注意：表的创建顺序按外键依赖关系排列，确保引用表先创建
-- ============================================================

-- ============ 用户域 ============

-- 1. 用户表（12列）
CREATE TABLE IF NOT EXISTS `users` (
    `user_id`        BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '用户ID',
    `username`       VARCHAR(64)     NOT NULL                 COMMENT '用户名（登录名）',
    `nickname`       VARCHAR(64)     DEFAULT NULL             COMMENT '用户昵称',
    `gender`         ENUM('M','F','U') DEFAULT 'U'            COMMENT '性别：M=男 F=女 U=未知',
    `birth_date`     DATE            DEFAULT NULL             COMMENT '出生日期',
    `phone`          VARCHAR(20)     DEFAULT NULL             COMMENT '手机号',
    `email`          VARCHAR(128)    DEFAULT NULL             COMMENT '邮箱',
    `register_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    `user_level`     ENUM('1','2','3','4','5') DEFAULT '1'    COMMENT '用户等级：1-5级',
    `balance`        DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '账户余额',
    `points`         INT             NOT NULL DEFAULT 0       COMMENT '积分',
    `status`         ENUM('active','inactive','banned') NOT NULL DEFAULT 'active' COMMENT '状态：active=正常 inactive=未激活 banned=封禁',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_phone` (`phone`),
    KEY `idx_email` (`email`),
    KEY `idx_user_level` (`user_level`),
    KEY `idx_status` (`status`),
    KEY `idx_register_time` (`register_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 用户地址表（10列）
CREATE TABLE IF NOT EXISTS `user_addresses` (
    `address_id`     BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '地址ID',
    `user_id`        BIGINT          NOT NULL                 COMMENT '用户ID',
    `province`       VARCHAR(32)     NOT NULL                 COMMENT '省份',
    `city`           VARCHAR(32)     NOT NULL                 COMMENT '城市',
    `district`       VARCHAR(32)     DEFAULT NULL             COMMENT '区/县',
    `detail_address` VARCHAR(255)    NOT NULL                 COMMENT '详细地址',
    `receiver_name`  VARCHAR(64)     NOT NULL                 COMMENT '收货人姓名',
    `receiver_phone` VARCHAR(20)     NOT NULL                 COMMENT '收货人手机号',
    `is_default`     TINYINT         NOT NULL DEFAULT 0       COMMENT '是否默认地址：0=否 1=是',
    `create_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`address_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_province_city` (`province`, `city`),
    CONSTRAINT `fk_user_addresses_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户地址表';

-- ============ 商品域（分类） ============

-- 3. 商品分类表（8列）
CREATE TABLE IF NOT EXISTS `categories` (
    `category_id`   BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '分类ID',
    `category_name` VARCHAR(64)     NOT NULL                 COMMENT '分类名称',
    `parent_id`     BIGINT          DEFAULT NULL             COMMENT '父分类ID（自关联，顶级为NULL）',
    `level`         TINYINT         NOT NULL DEFAULT 1       COMMENT '分类层级：1=一级 2=二级 3=三级',
    `sort_order`    INT             NOT NULL DEFAULT 0       COMMENT '排序序号',
    `is_visible`    TINYINT         NOT NULL DEFAULT 1       COMMENT '是否可见：0=否 1=是',
    `icon_url`      VARCHAR(255)    DEFAULT NULL             COMMENT '分类图标URL',
    `create_time`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`category_id`),
    KEY `idx_parent_id` (`parent_id`),
    KEY `idx_level` (`level`),
    KEY `idx_sort_order` (`sort_order`),
    CONSTRAINT `fk_categories_parent_id` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`category_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';

-- ============ 店铺域 ============

-- 6. 店铺表（13列）
CREATE TABLE IF NOT EXISTS `stores` (
    `store_id`          BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '店铺ID',
    `store_name`        VARCHAR(128)    NOT NULL                 COMMENT '店铺名称',
    `store_type`        ENUM('flagship','specialty','franchise','personal') NOT NULL DEFAULT 'specialty' COMMENT '店铺类型：flagship=旗舰店 specialty=专营店 franchise=加盟店 personal=个人店',
    `owner_id`          BIGINT          NOT NULL                 COMMENT '店主用户ID',
    `province`          VARCHAR(32)     DEFAULT NULL             COMMENT '省份',
    `city`              VARCHAR(32)     DEFAULT NULL             COMMENT '城市',
    `main_category_id`  BIGINT          DEFAULT NULL             COMMENT '主营分类ID',
    `description`       VARCHAR(512)    DEFAULT NULL             COMMENT '店铺描述',
    `total_sales`       INT             NOT NULL DEFAULT 0       COMMENT '总销量',
    `total_followers`   INT             NOT NULL DEFAULT 0       COMMENT '总粉丝数',
    `commission_rate`   DECIMAL(4,2)    NOT NULL DEFAULT 0.00    COMMENT '平台佣金比例（%）',
    `status`            ENUM('open','closed','frozen','reviewing') NOT NULL DEFAULT 'reviewing' COMMENT '状态：open=营业 closed=关闭 frozen=冻结 reviewing=审核中',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`store_id`),
    KEY `idx_owner_id` (`owner_id`),
    KEY `idx_main_category_id` (`main_category_id`),
    KEY `idx_status` (`status`),
    KEY `idx_province_city` (`province`, `city`),
    CONSTRAINT `fk_stores_owner_id` FOREIGN KEY (`owner_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_stores_main_category_id` FOREIGN KEY (`main_category_id`) REFERENCES `categories` (`category_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='店铺表';

-- ============ 商品域（商品、规格） ============

-- 4. 商品表（16列）
CREATE TABLE IF NOT EXISTS `products` (
    `product_id`   BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '商品ID',
    `product_name` VARCHAR(128)    NOT NULL                 COMMENT '商品名称',
    `category_id`  BIGINT          NOT NULL                 COMMENT '分类ID',
    `store_id`     BIGINT          NOT NULL                 COMMENT '店铺ID',
    `brand`        VARCHAR(64)     DEFAULT NULL             COMMENT '品牌',
    `main_image`   VARCHAR(255)    DEFAULT NULL             COMMENT '主图URL',
    `price`        DECIMAL(10,2)   NOT NULL                 COMMENT '售价',
    `cost_price`   DECIMAL(10,2)   DEFAULT NULL             COMMENT '成本价',
    `stock`        INT             NOT NULL DEFAULT 0       COMMENT '库存数量',
    `sales`        INT             NOT NULL DEFAULT 0       COMMENT '销量',
    `rating_score` DECIMAL(2,1)    DEFAULT NULL             COMMENT '评分（0.0-5.0）',
    `status`       ENUM('on_sale','off_sale','pre_sale') NOT NULL DEFAULT 'on_sale' COMMENT '状态：on_sale=在售 off_sale=下架 pre_sale=预售',
    `tags`         VARCHAR(255)    DEFAULT NULL             COMMENT '标签（逗号分隔）',
    `description`  TEXT            DEFAULT NULL             COMMENT '商品描述',
    `create_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`product_id`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_store_id` (`store_id`),
    KEY `idx_brand` (`brand`),
    KEY `idx_status` (`status`),
    KEY `idx_price` (`price`),
    KEY `idx_sales` (`sales`),
    KEY `idx_create_time` (`create_time`),
    CONSTRAINT `fk_products_category_id` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_products_store_id` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- 5. 商品规格表（7列）
CREATE TABLE IF NOT EXISTS `product_specs` (
    `spec_id`     BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '规格ID',
    `product_id`  BIGINT          NOT NULL                 COMMENT '商品ID',
    `spec_name`   VARCHAR(64)     NOT NULL                 COMMENT '规格名称（如颜色、尺码）',
    `spec_value`  VARCHAR(128)    NOT NULL                 COMMENT '规格值（如红色、XL）',
    `sku_code`    VARCHAR(64)     NOT NULL                 COMMENT 'SKU编码',
    `price`       DECIMAL(10,2)   NOT NULL                 COMMENT 'SKU售价',
    `stock`       INT             NOT NULL DEFAULT 0       COMMENT 'SKU库存',
    PRIMARY KEY (`spec_id`),
    UNIQUE KEY `uk_sku_code` (`sku_code`),
    KEY `idx_product_id` (`product_id`),
    CONSTRAINT `fk_product_specs_product_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品规格表';

-- ============ 交易域 ============

-- 8. 订单表（18列）
CREATE TABLE IF NOT EXISTS `orders` (
    `order_id`        BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '订单ID',
    `order_no`        VARCHAR(32)     NOT NULL                 COMMENT '订单编号',
    `user_id`         BIGINT          NOT NULL                 COMMENT '下单用户ID',
    `store_id`        BIGINT          NOT NULL                 COMMENT '店铺ID',
    `order_status`    ENUM('pending','paid','shipped','received','cancelled','refunding','refunded') NOT NULL DEFAULT 'pending' COMMENT '订单状态：pending=待付款 paid=已付款 shipped=已发货 received=已收货 cancelled=已取消 refunding=退款中 refunded=已退款',
    `total_amount`    DECIMAL(12,2)   NOT NULL                 COMMENT '订单总金额',
    `discount_amount` DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '优惠金额',
    `pay_amount`      DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '实付金额',
    `coupon_id`       BIGINT          DEFAULT NULL             COMMENT '使用的优惠券ID',
    `payment_method`  ENUM('alipay','wechat','bank_card','balance','installment') DEFAULT NULL COMMENT '支付方式：alipay=支付宝 wechat=微信 bank_card=银行卡 balance=余额 installment=分期',
    `shipping_fee`    DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '运费',
    `receiver_name`   VARCHAR(64)     NOT NULL                 COMMENT '收货人姓名',
    `receiver_phone`  VARCHAR(20)     NOT NULL                 COMMENT '收货人手机号',
    `receiver_address` VARCHAR(255)    NOT NULL                 COMMENT '收货地址',
    `remark`          VARCHAR(255)    DEFAULT NULL             COMMENT '订单备注',
    `create_time`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    `pay_time`        DATETIME        DEFAULT NULL             COMMENT '支付时间',
    `ship_time`       DATETIME        DEFAULT NULL             COMMENT '发货时间',
    `receive_time`    DATETIME        DEFAULT NULL             COMMENT '收货时间',
    PRIMARY KEY (`order_id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_store_id` (`store_id`),
    KEY `idx_order_status` (`order_status`),
    KEY `idx_create_time` (`create_time`),
    KEY `idx_pay_time` (`pay_time`),
    KEY `idx_coupon_id` (`coupon_id`),
    CONSTRAINT `fk_orders_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_orders_store_id` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- 9. 订单明细表（11列）
CREATE TABLE IF NOT EXISTS `order_items` (
    `item_id`       BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '明细ID',
    `order_id`      BIGINT          NOT NULL                 COMMENT '订单ID',
    `product_id`    BIGINT          NOT NULL                 COMMENT '商品ID',
    `sku_code`      VARCHAR(64)     DEFAULT NULL             COMMENT 'SKU编码',
    `product_name`  VARCHAR(128)    NOT NULL                 COMMENT '商品名称（快照）',
    `spec_info`     VARCHAR(255)    DEFAULT NULL             COMMENT '规格信息（快照）',
    `price`         DECIMAL(10,2)   NOT NULL                 COMMENT '购买单价（快照）',
    `quantity`      INT             NOT NULL DEFAULT 1       COMMENT '购买数量',
    `subtotal`      DECIMAL(12,2)   NOT NULL                 COMMENT '小计金额',
    `refund_status` ENUM('none','applied','approved','rejected') NOT NULL DEFAULT 'none' COMMENT '退款状态：none=无 applied=已申请 approved=已通过 rejected=已拒绝',
    `refund_amount` DECIMAL(10,2)   DEFAULT NULL             COMMENT '退款金额',
    PRIMARY KEY (`item_id`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_product_id` (`product_id`),
    KEY `idx_sku_code` (`sku_code`),
    KEY `idx_refund_status` (`refund_status`),
    CONSTRAINT `fk_order_items_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_order_items_product_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';

-- 10. 支付记录表（10列）
CREATE TABLE IF NOT EXISTS `payments` (
    `payment_id`     BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '支付ID',
    `payment_no`     VARCHAR(64)     NOT NULL                 COMMENT '支付流水号',
    `order_id`       BIGINT          NOT NULL                 COMMENT '订单ID',
    `user_id`        BIGINT          NOT NULL                 COMMENT '支付用户ID',
    `amount`         DECIMAL(12,2)   NOT NULL                 COMMENT '支付金额',
    `payment_method` ENUM('alipay','wechat','bank_card','balance','installment') NOT NULL COMMENT '支付方式：alipay=支付宝 wechat=微信 bank_card=银行卡 balance=余额 installment=分期',
    `payment_status` ENUM('success','failed','refunded') NOT NULL DEFAULT 'success' COMMENT '支付状态：success=成功 failed=失败 refunded=已退款',
    `pay_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '支付时间',
    `callback_time`  DATETIME        DEFAULT NULL             COMMENT '回调时间',
    `trade_type`     ENUM('payment','refund') NOT NULL DEFAULT 'payment' COMMENT '交易类型：payment=支付 refund=退款',
    PRIMARY KEY (`payment_id`),
    UNIQUE KEY `uk_payment_no` (`payment_no`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_payment_status` (`payment_status`),
    KEY `idx_pay_time` (`pay_time`),
    KEY `idx_trade_type` (`trade_type`),
    CONSTRAINT `fk_payments_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_payments_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付记录表';

-- ============ 店铺域（评分） ============

-- 7. 店铺评分表（10列）
CREATE TABLE IF NOT EXISTS `store_ratings` (
    `rating_id`         BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '评分ID',
    `store_id`          BIGINT          NOT NULL                 COMMENT '店铺ID',
    `user_id`           BIGINT          NOT NULL                 COMMENT '评分用户ID',
    `order_id`          BIGINT          NOT NULL                 COMMENT '关联订单ID',
    `description_score` DECIMAL(2,1)    NOT NULL                 COMMENT '描述相符评分（1.0-5.0）',
    `service_score`     DECIMAL(2,1)    NOT NULL                 COMMENT '服务态度评分（1.0-5.0）',
    `logistics_score`   DECIMAL(2,1)    NOT NULL                 COMMENT '物流服务评分（1.0-5.0）',
    `content`           VARCHAR(512)    DEFAULT NULL             COMMENT '评价内容',
    `has_image`         TINYINT         NOT NULL DEFAULT 0       COMMENT '是否有图：0=否 1=是',
    `rating_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评分时间',
    PRIMARY KEY (`rating_id`),
    KEY `idx_store_id` (`store_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_rating_time` (`rating_time`),
    CONSTRAINT `fk_store_ratings_store_id` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_store_ratings_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_store_ratings_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='店铺评分表';

-- ============ 营销域 ============

-- 11. 优惠券模板表（15列）
CREATE TABLE IF NOT EXISTS `coupons` (
    `coupon_id`      BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '优惠券ID',
    `coupon_name`    VARCHAR(128)    NOT NULL                 COMMENT '优惠券名称',
    `coupon_type`    ENUM('fixed','percent','shipping') NOT NULL COMMENT '优惠券类型：fixed=满减 percent=折扣 shipping=包邮',
    `discount_value` DECIMAL(10,2)   NOT NULL                 COMMENT '优惠额度（满减为金额，折扣为折扣率如8.5表示85折）',
    `min_amount`     DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '最低消费金额',
    `max_discount`   DECIMAL(10,2)   DEFAULT NULL             COMMENT '最大优惠金额（折扣券封顶）',
    `total_count`    INT             NOT NULL                 COMMENT '发放总量',
    `remain_count`   INT             NOT NULL                 COMMENT '剩余数量',
    `per_limit`      INT             NOT NULL DEFAULT 1       COMMENT '每人限领数量',
    `scope_type`     ENUM('all','category','product','store') NOT NULL DEFAULT 'all' COMMENT '适用范围：all=全场 category=品类 product=指定商品 store=指定店铺',
    `scope_id`       BIGINT          DEFAULT NULL             COMMENT '范围关联ID（品类ID/商品ID/店铺ID）',
    `start_time`     DATETIME        NOT NULL                 COMMENT '生效开始时间',
    `end_time`       DATETIME        NOT NULL                 COMMENT '生效结束时间',
    `status`         ENUM('draft','active','expired','disabled') NOT NULL DEFAULT 'draft' COMMENT '状态：draft=草稿 active=生效中 expired=已过期 disabled=已停用',
    `create_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`coupon_id`),
    KEY `idx_coupon_type` (`coupon_type`),
    KEY `idx_scope_type` (`scope_type`),
    KEY `idx_status` (`status`),
    KEY `idx_start_end_time` (`start_time`, `end_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='优惠券模板表';

-- 12. 促销活动表（13列）
CREATE TABLE IF NOT EXISTS `campaigns` (
    `campaign_id`   BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '活动ID',
    `campaign_name` VARCHAR(128)    NOT NULL                 COMMENT '活动名称',
    `campaign_type` ENUM('flash_sale','group_buy','full_reduction','gift','lottery') NOT NULL COMMENT '活动类型：flash_sale=秒杀 group_buy=拼团 full_reduction=满减 gift=赠品 lottery=抽奖',
    `store_id`      BIGINT          DEFAULT NULL             COMMENT '店铺ID（NULL表示平台级活动）',
    `start_time`    DATETIME        NOT NULL                 COMMENT '活动开始时间',
    `end_time`      DATETIME        NOT NULL                 COMMENT '活动结束时间',
    `budget`        DECIMAL(12,2)   DEFAULT NULL             COMMENT '活动预算',
    `cost`          DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '已花费金额',
    `target_gmv`    DECIMAL(12,2)   DEFAULT NULL             COMMENT '目标GMV',
    `actual_gmv`    DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '实际GMV',
    `visit_count`   INT             NOT NULL DEFAULT 0       COMMENT '访问次数',
    `order_count`   INT             NOT NULL DEFAULT 0       COMMENT '下单数量',
    `status`        ENUM('planned','active','ended','cancelled') NOT NULL DEFAULT 'planned' COMMENT '状态：planned=计划中 active=进行中 ended=已结束 cancelled=已取消',
    PRIMARY KEY (`campaign_id`),
    KEY `idx_store_id` (`store_id`),
    KEY `idx_campaign_type` (`campaign_type`),
    KEY `idx_status` (`status`),
    KEY `idx_start_end_time` (`start_time`, `end_time`),
    CONSTRAINT `fk_campaigns_store_id` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='促销活动表';

-- 13. 用户优惠券表（8列）
CREATE TABLE IF NOT EXISTS `user_coupons` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '记录ID',
    `coupon_id`     BIGINT          NOT NULL                 COMMENT '优惠券ID',
    `user_id`       BIGINT          NOT NULL                 COMMENT '用户ID',
    `order_id`      BIGINT          DEFAULT NULL             COMMENT '使用时的订单ID（未使用为NULL）',
    `status`        ENUM('unused','used','expired') NOT NULL DEFAULT 'unused' COMMENT '状态：unused=未使用 used=已使用 expired=已过期',
    `receive_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '领取时间',
    `use_time`      DATETIME        DEFAULT NULL             COMMENT '使用时间',
    `expire_time`   DATETIME        NOT NULL                 COMMENT '过期时间',
    PRIMARY KEY (`id`),
    KEY `idx_coupon_id` (`coupon_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_status` (`status`),
    KEY `idx_expire_time` (`expire_time`),
    CONSTRAINT `fk_user_coupons_coupon_id` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`coupon_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_user_coupons_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_user_coupons_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户优惠券表';

-- ============ 物流域 ============

-- 14. 物流单表（17列）
CREATE TABLE IF NOT EXISTS `shipments` (
    `shipment_id`       BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '物流单ID',
    `order_id`          BIGINT          NOT NULL                 COMMENT '订单ID',
    `store_id`          BIGINT          NOT NULL                 COMMENT '发货店铺ID',
    `carrier`           ENUM('sf','yd','zt','sto','yt','ems','jd') NOT NULL COMMENT '快递公司：sf=顺丰 yd=韵达 zt=中通 sto=申通 yt=圆通 ems=EMS jd=京东',
    `shipment_no`       VARCHAR(64)     NOT NULL                 COMMENT '快递单号',
    `sender_name`       VARCHAR(64)     NOT NULL                 COMMENT '发件人姓名',
    `sender_phone`      VARCHAR(20)     NOT NULL                 COMMENT '发件人手机号',
    `sender_address`    VARCHAR(255)    NOT NULL                 COMMENT '发件人地址',
    `receiver_name`     VARCHAR(64)     NOT NULL                 COMMENT '收件人姓名',
    `receiver_phone`    VARCHAR(20)     NOT NULL                 COMMENT '收件人手机号',
    `receiver_address`  VARCHAR(255)    NOT NULL                 COMMENT '收件人地址',
    `weight`            DECIMAL(8,2)    DEFAULT NULL             COMMENT '包裹重量（kg）',
    `shipping_fee`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '运费',
    `status`            ENUM('pending','picked_up','in_transit','delivered','failed','returned') NOT NULL DEFAULT 'pending' COMMENT '物流状态：pending=待取件 picked_up=已取件 in_transit=运输中 delivered=已签收 failed=投递失败 returned=已退回',
    `ship_time`         DATETIME        DEFAULT NULL             COMMENT '发货时间',
    `deliver_time`      DATETIME        DEFAULT NULL             COMMENT '签收时间',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`shipment_id`),
    UNIQUE KEY `uk_shipment_no` (`shipment_no`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_store_id` (`store_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_status` (`status`),
    KEY `idx_ship_time` (`ship_time`),
    CONSTRAINT `fk_shipments_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_shipments_store_id` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物流单表';

-- 15. 物流轨迹表（7列）
CREATE TABLE IF NOT EXISTS `shipment_tracks` (
    `track_id`    BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '轨迹ID',
    `shipment_id` BIGINT          NOT NULL                 COMMENT '物流单ID',
    `location`    VARCHAR(128)    DEFAULT NULL             COMMENT '所在地点',
    `description` VARCHAR(255)    NOT NULL                 COMMENT '轨迹描述',
    `operator`    VARCHAR(64)     DEFAULT NULL             COMMENT '操作人/站点',
    `track_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '轨迹时间',
    `track_type`  ENUM('pickup','transit','transfer','delivering','signed','exception') NOT NULL COMMENT '轨迹类型：pickup=揽件 transit=运输中 transfer=中转 delivering=派送中 signed=已签收 exception=异常',
    PRIMARY KEY (`track_id`),
    KEY `idx_shipment_id` (`shipment_id`),
    KEY `idx_track_time` (`track_time`),
    KEY `idx_track_type` (`track_type`),
    CONSTRAINT `fk_shipment_tracks_shipment_id` FOREIGN KEY (`shipment_id`) REFERENCES `shipments` (`shipment_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物流轨迹表';
