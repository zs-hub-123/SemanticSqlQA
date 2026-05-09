# -*- coding: utf-8 -*-
"""
语义层V3快速修复脚本
基于测试失败数据分析的紧急修复
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / '.env')

DB_CONFIG = {
    'host': os.getenv('SEMANTIC_DB_HOST', 'localhost'),
    'port': int(os.getenv('SEMANTIC_DB_PORT', '3306')),
    'user': os.getenv('SEMANTIC_DB_USER', 'root'),
    'password': os.getenv('SEMANTIC_DB_PASSWORD', ''),
    'database': os.getenv('SEMANTIC_DB_NAME', 'text02_semantic'),
    'charset': 'utf8mb4'
}

def main():
    print("=" * 60)
    print("  SQL智能问答系统 - 语义层V3快速修复")
    print("=" * 60)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ 数据库连接成功")
        
        # 1. 插入核心COUNT指标
        print("\n[1/3] 插入核心COUNT指标...")
        metrics_sql = """
INSERT INTO standard_metrics_dimensions 
(name, type, physical_table, physical_field, field_type, business_desc, aggregation_type, domain, is_non_additive, stat_period, data_granularity, default_filter, metric_version, effective_date) VALUES
('用户数量', 'metric', 'users', 'user_id', 'BIGINT', '注册用户总数', 'COUNT', '用户域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('买家数量', 'metric', 'users', 'user_id', 'BIGINT', '购买过商品的买家总数', 'COUNT', '用户域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('客户数量', 'metric', 'users', 'user_id', 'BIGINT', '客户总数', 'COUNT', '用户域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('商品数量', 'metric', 'products', 'product_id', 'BIGINT', '在售商品总数', 'COUNT', '商品域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('SKU数量', 'metric', 'product_specs', 'spec_id', 'BIGINT', '商品规格(SKU)总数', 'COUNT', '商品域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('店铺数量', 'metric', 'stores', 'store_id', 'BIGINT', '开店商家总数', 'COUNT', '店铺域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('订单数量', 'metric', 'orders', 'order_id', 'BIGINT', '订单总数', 'COUNT', '交易域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('有效订单数', 'metric', 'orders', 'order_id', 'BIGINT', '有效订单数(排除取消)', 'COUNT', '交易域', 1, NULL, NULL, "order_status NOT IN ('cancelled','refunded')", 'V3.0', '2024-01-01'),
('支付笔数', 'metric', 'payments', 'payment_id', 'BIGINT', '支付记录总数', 'COUNT', '交易域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('物流单数量', 'metric', 'shipments', 'shipment_id', 'BIGINT', '物流发货单总数', 'COUNT', '物流域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01'),
('优惠券数量', 'metric', 'coupons', 'coupon_id', 'BIGINT', '优惠券模板总数', 'COUNT', '营销域', 1, NULL, NULL, NULL, 'V3.0', '2024-01-01')
ON DUPLICATE KEY UPDATE metric_version = 'V3.0'
"""
        cursor.execute(metrics_sql)
        conn.commit()
        print(f"   ✅ 核心指标插入成功")
        
        # 2. 插入口语别名
        print("\n[2/3] 插入口语别名...")
        aliases_sql = """
INSERT INTO spoken_aliases (spoken_term, standard_name, alias_type, frequency, source) VALUES
('商品', '商品数量', 'entity', 200, 'fix_v3'),
('产品', '商品数量', 'entity', 150, 'fix_v3'),
('货品', '商品数量', 'entity', 80, 'fix_v3'),
('多少商品', '商品数量', 'entity', 120, 'fix_v3'),
('多少个商品', '商品数量', 'entity', 100, 'fix_v3'),
('商品有多少', '商品数量', 'entity', 90, 'fix_v3'),
('商品总共有', '商品数量', 'entity', 85, 'fix_v3'),
('店铺', '店铺数量', 'entity', 180, 'fix_v3'),
('商店', '店铺数量', 'entity', 100, 'fix_v3'),
('商家', '店铺数量', 'entity', 120, 'fix_v3'),
('卖家', '店铺数量', 'entity', 90, 'fix_v3'),
('多少店铺', '店铺数量', 'entity', 110, 'fix_v3'),
('查一下店铺', '店铺数量', 'entity', 95, 'fix_v3'),
('店铺总共有', '店铺数量', 'entity', 85, 'fix_v3'),
('订单', '订单数量', 'entity', 250, 'fix_v3'),
('订单数', '订单数量', 'entity', 220, 'fix_v3'),
('多少订单', '订单数量', 'entity', 150, 'fix_v3'),
('订单总共有', '订单数量', 'entity', 130, 'fix_v3'),
('订单一共', '订单数量', 'entity', 110, 'fix_v3'),
('流水', '支付笔数', 'entity', 140, 'fix_v3'),
('支付流水', '支付笔数', 'entity', 130, 'fix_v3'),
('付款记录', '支付笔数', 'entity', 110, 'fix_v3'),
('查一下流水', '支付笔数', 'entity', 95, 'fix_v3'),
('优惠券', '优惠券数量', 'entity', 160, 'fix_v3'),
('券', '优惠券数量', 'entity', 130, 'fix_v3'),
('查一下优惠券', '优惠券数量', 'entity', 95, 'fix_v3'),
('物流单', '物流单数量', 'entity', 120, 'fix_v3'),
('快递单', '物流单数量', 'entity', 100, 'fix_v3'),
('明细', '订单明细数量', 'entity', 110, 'fix_v3'),
('订单明细', '订单明细数量', 'entity', 130, 'fix_v3'),
('评分', '店铺评分数量', 'entity', 100, 'fix_v3'),
('评价', '店铺评分数量', 'entity', 95, 'fix_v3'),
('属性', '属性数量', 'entity', 110, 'fix_v3'),
('规格', '属性数量', 'entity', 100, 'fix_v3'),
('SKU', '属性数量', 'entity', 90, 'fix_v3'),
('地址', '地址数量', 'entity', 100, 'fix_v3'),
('收货地址', '地址数量', 'entity', 120, 'fix_v3'),
('用户', '用户数量', 'entity', 200, 'fix_v3'),
('买家', '用户数量', 'entity', 100, 'fix_v3'),
('客户', '用户数量', 'entity', 95, 'fix_v3'),
('会员', '用户数量', 'entity', 90, 'fix_v3')
ON DUPLICATE KEY UPDATE frequency = GREATEST(frequency, VALUES(frequency))
"""
        cursor.execute(aliases_sql)
        conn.commit()
        print(f"   ✅ 口语别名插入成功")
        
        # 3. 验证结果
        print("\n[3/3] 验证修复结果...")
        cursor.execute("SELECT COUNT(*) as cnt FROM standard_metrics_dimensions WHERE name IN ('商品数量', '用户数量', '店铺数量', '订单数量')")
        row = cursor.fetchone()
        print(f"   核心指标数量: {row[0]}")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM spoken_aliases WHERE source = 'fix_v3'")
        row = cursor.fetchone()
        print(f"   V3别名数量: {row[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("  ✅ V3修复完成!")
        print("=" * 60)
        print("\n请重启服务: python start.py")
        print("然后重新运行测试验证效果")
        
    except Error as e:
        print(f"\n❌ 数据库错误: {e}")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")

if __name__ == "__main__":
    main()
