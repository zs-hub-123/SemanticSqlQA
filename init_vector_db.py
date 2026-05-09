# ============================================================
# 向量库初始化脚本
# 功能：将15张业务表的结构信息向量化入库
# 向量模型：远程API服务
# ============================================================

import sys
import os
import requests
import numpy as np
import base64
import pickle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, '.env'), override=True)

print(f"DEBUG: MILVUS_HOST = {os.getenv('MILVUS_HOST')}")
print(f"DEBUG: MILVUS_PORT = {os.getenv('MILVUS_PORT')}")
print(f"DEBUG: EMBEDDING_API = {os.getenv('EMBEDDING_API')}")

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
MILVUS_PORT = int(os.getenv('MILVUS_PORT', '19530'))
COLLECTION_NAME = os.getenv('MILVUS_COLLECTION_NAME', 'table_schemas_vector')
EMBEDDING_API = os.getenv('EMBEDDING_API', 'http://localhost:50183/api/embedding')

TABLE_SCHEMAS = {
    "users": {
        "cn_name": "用户表",
        "description": "存储用户基本信息、等级、积分、余额等",
        "fields": [
            ("user_id", "BIGINT", "用户ID"),
            ("username", "VARCHAR(64)", "用户名"),
            ("nickname", "VARCHAR(64)", "用户昵称"),
            ("gender", "ENUM('M','F','U')", "性别"),
            ("register_time", "DATETIME", "注册时间"),
            ("user_level", "ENUM('1','2','3','4','5')", "用户等级"),
            ("balance", "DECIMAL(12,2)", "账户余额"),
            ("points", "INT", "积分"),
            ("status", "ENUM('active','inactive','banned')", "账户状态")
        ]
    },
    "user_addresses": {
        "cn_name": "用户地址表",
        "description": "用户收货地址信息",
        "fields": [
            ("address_id", "BIGINT", "地址ID"),
            ("user_id", "BIGINT", "用户ID"),
            ("province", "VARCHAR(32)", "省份"),
            ("city", "VARCHAR(32)", "城市"),
            ("detail_address", "VARCHAR(255)", "详细地址"),
            ("receiver_name", "VARCHAR(64)", "收货人姓名"),
            ("receiver_phone", "VARCHAR(20)", "收货人手机号")
        ]
    },
    "categories": {
        "cn_name": "商品分类表",
        "description": "商品分类层级结构",
        "fields": [
            ("category_id", "BIGINT", "分类ID"),
            ("category_name", "VARCHAR(64)", "分类名称"),
            ("parent_id", "BIGINT", "父分类ID"),
            ("level", "TINYINT", "分类层级"),
            ("is_visible", "TINYINT", "是否可见")
        ]
    },
    "products": {
        "cn_name": "商品表",
        "description": "商品主信息、价格、库存、销量、评分",
        "fields": [
            ("product_id", "BIGINT", "商品ID"),
            ("product_name", "VARCHAR(128)", "商品名称"),
            ("category_id", "BIGINT", "分类ID"),
            ("store_id", "BIGINT", "店铺ID"),
            ("brand", "VARCHAR(64)", "品牌"),
            ("price", "DECIMAL(10,2)", "售价"),
            ("stock", "INT", "库存"),
            ("sales", "INT", "销量"),
            ("rating_score", "DECIMAL(2,1)", "商品评分"),
            ("status", "ENUM('on_sale','off_sale','pre_sale')", "商品状态")
        ]
    },
    "product_specs": {
        "cn_name": "商品规格表",
        "description": "SKU规格信息",
        "fields": [
            ("spec_id", "BIGINT", "规格ID"),
            ("product_id", "BIGINT", "商品ID"),
            ("spec_name", "VARCHAR(64)", "规格名称"),
            ("spec_value", "VARCHAR(128)", "规格值"),
            ("sku_code", "VARCHAR(64)", "SKU编码"),
            ("price", "DECIMAL(10,2)", "SKU售价"),
            ("stock", "INT", "SKU库存")
        ]
    },
    "stores": {
        "cn_name": "店铺表",
        "description": "店铺基础信息、类型、销量、粉丝数",
        "fields": [
            ("store_id", "BIGINT", "店铺ID"),
            ("store_name", "VARCHAR(128)", "店铺名称"),
            ("store_type", "ENUM('flagship','specialty','franchise','personal')", "店铺类型"),
            ("owner_id", "BIGINT", "店主ID"),
            ("province", "VARCHAR(32)", "省份"),
            ("city", "VARCHAR(32)", "城市"),
            ("total_sales", "INT", "总销量"),
            ("total_followers", "INT", "总粉丝数"),
            ("status", "ENUM('open','closed','frozen','reviewing')", "店铺状态")
        ]
    },
    "store_ratings": {
        "cn_name": "店铺评分表",
        "description": "店铺DSR评分详情",
        "fields": [
            ("rating_id", "BIGINT", "评分ID"),
            ("order_id", "BIGINT", "订单ID"),
            ("store_id", "BIGINT", "店铺ID"),
            ("description_score", "DECIMAL(2,1)", "描述相符评分"),
            ("service_score", "DECIMAL(2,1)", "服务态度评分"),
            ("logistics_score", "DECIMAL(2,1)", "物流服务评分")
        ]
    },
    "orders": {
        "cn_name": "订单表",
        "description": "订单主信息、状态流转、金额",
        "fields": [
            ("order_id", "BIGINT", "订单ID"),
            ("order_no", "VARCHAR(32)", "订单编号"),
            ("user_id", "BIGINT", "用户ID"),
            ("store_id", "BIGINT", "店铺ID"),
            ("total_amount", "DECIMAL(12,2)", "订单总金额"),
            ("discount_amount", "DECIMAL(12,2)", "优惠金额"),
            ("pay_amount", "DECIMAL(12,2)", "实付金额"),
            ("order_status", "ENUM('pending','paid','shipped','received','cancelled','refunding','refunded')", "订单状态"),
            ("payment_method", "ENUM('alipay','wechat','bank_card','balance','installment')", "支付方式"),
            ("shipping_fee", "DECIMAL(10,2)", "运费"),
            ("create_time", "DATETIME", "下单时间"),
            ("pay_time", "DATETIME", "支付时间"),
            ("ship_time", "DATETIME", "发货时间"),
            ("receive_time", "DATETIME", "收货时间")
        ]
    },
    "order_items": {
        "cn_name": "订单明细表",
        "description": "订单商品明细、退款信息",
        "fields": [
            ("item_id", "BIGINT", "明细ID"),
            ("order_id", "BIGINT", "订单ID"),
            ("product_id", "BIGINT", "商品ID"),
            ("product_name", "VARCHAR(128)", "商品名称"),
            ("price", "DECIMAL(10,2)", "单价"),
            ("quantity", "INT", "数量"),
            ("subtotal", "DECIMAL(12,2)", "小计"),
            ("refund_status", "ENUM('none','applied','approved','rejected')", "退款状态"),
            ("refund_amount", "DECIMAL(10,2)", "退款金额")
        ]
    },
    "payments": {
        "cn_name": "支付记录表",
        "description": "支付流水、支付方式",
        "fields": [
            ("payment_id", "BIGINT", "支付ID"),
            ("order_id", "BIGINT", "订单ID"),
            ("payment_no", "VARCHAR(64)", "支付流水号"),
            ("payment_method", "ENUM('alipay','wechat','bank_card','balance')", "支付方式"),
            ("amount", "DECIMAL(12,2)", "支付金额"),
            ("status", "ENUM('pending','success','failed')", "支付状态"),
            ("pay_time", "DATETIME", "支付时间")
        ]
    },
    "coupons": {
        "cn_name": "优惠券模板表",
        "description": "优惠券定义、规则",
        "fields": [
            ("coupon_id", "BIGINT", "优惠券ID"),
            ("coupon_name", "VARCHAR(128)", "优惠券名称"),
            ("coupon_type", "ENUM('fixed','percent','shipping')", "券类型"),
            ("coupon_value", "DECIMAL(10,2)", "优惠券值"),
            ("min_amount", "DECIMAL(10,2)", "最低消费金额"),
            ("total_count", "INT", "发放总量"),
            ("received_count", "INT", "已领取数量"),
            ("used_count", "INT", "已使用数量"),
            ("status", "ENUM('draft','active','expired','disabled')", "券状态")
        ]
    },
    "campaigns": {
        "cn_name": "促销活动表",
        "description": "营销活动信息、ROI",
        "fields": [
            ("campaign_id", "BIGINT", "活动ID"),
            ("campaign_name", "VARCHAR(128)", "活动名称"),
            ("campaign_type", "ENUM('flash_sale','group_buy','full_reduction','gift','lottery')", "活动类型"),
            ("store_id", "BIGINT", "店铺ID"),
            ("budget", "DECIMAL(12,2)", "活动预算"),
            ("actual_gmv", "DECIMAL(12,2)", "活动实际GMV"),
            ("cost", "DECIMAL(12,2)", "活动成本"),
            ("status", "ENUM('planned','active','ended','cancelled')", "活动状态")
        ]
    },
    "user_coupons": {
        "cn_name": "用户优惠券表",
        "description": "用户领券用券记录",
        "fields": [
            ("id", "BIGINT", "记录ID"),
            ("user_id", "BIGINT", "用户ID"),
            ("coupon_id", "BIGINT", "优惠券ID"),
            ("order_id", "BIGINT", "使用的订单ID"),
            ("status", "ENUM('unused','used','expired')", "状态"),
            ("receive_time", "DATETIME", "领取时间"),
            ("use_time", "DATETIME", "使用时间")
        ]
    },
    "shipments": {
        "cn_name": "物流单表",
        "description": "物流发货信息、状态",
        "fields": [
            ("shipment_id", "BIGINT", "物流单ID"),
            ("order_id", "BIGINT", "订单ID"),
            ("store_id", "BIGINT", "店铺ID"),
            ("shipment_no", "VARCHAR(64)", "物流单号"),
            ("carrier", "ENUM('sf','yd','zt','sto','yt','ems','jd')", "快递公司"),
            ("status", "ENUM('pending','picked_up','in_transit','delivered','failed','returned')", "物流状态"),
            ("ship_time", "DATETIME", "发货时间"),
            ("deliver_time", "DATETIME", "签收时间"),
            ("weight", "DECIMAL(8,2)", "包裹重量")
        ]
    },
    "shipment_tracks": {
        "cn_name": "物流轨迹表",
        "description": "物流跟踪节点",
        "fields": [
            ("track_id", "BIGINT", "轨迹ID"),
            ("shipment_id", "BIGINT", "物流单ID"),
            ("location", "VARCHAR(128)", "当前位置"),
            ("status", "VARCHAR(64)", "状态描述"),
            ("track_time", "DATETIME", "轨迹时间")
        ]
    }
}


def get_embeddings(texts):
    """调用远程API获取向量"""
    url = EMBEDDING_API
    all_embeddings = []
    
    for i, text in enumerate(texts):
        try:
            payload = {"content": text}
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'dense' in result['data']:
                    dense_str = result['data']['dense']
                    embedding = pickle.loads(base64.b64decode(dense_str))
                    embedding = np.array(embedding)
                    if embedding.ndim > 1:
                        embedding = embedding.squeeze()
                    all_embeddings.append(embedding.tolist())
                else:
                    print(f"  警告: 第 {i+1} 条文本返回格式异常")
                    all_embeddings.append(None)
            else:
                print(f"  警告: 第 {i+1} 条文本向量化失败: {response.status_code}")
                all_embeddings.append(None)
        except Exception as e:
            print(f"  警告: 第 {i+1} 条文本向量化异常: {e}")
            all_embeddings.append(None)
    
    valid_embeddings = [e for e in all_embeddings if e is not None]
    if not valid_embeddings:
        raise Exception("所有文本向量化失败")
    
    print(f"  成功向量化 {len(valid_embeddings)}/{len(texts)} 条文本")
    return np.array(valid_embeddings)


def create_collection():
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)
        print(f"删除旧集合: {COLLECTION_NAME}")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="table_name", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
    ]
    schema = CollectionSchema(fields, description="SQL表结构向量库")
    collection = Collection(COLLECTION_NAME, schema)

    collection.create_index(
        field_name="embedding",
        index_type="AUTOINDEX",
        metric_type="COSINE"
    )
    print(f"创建集合成功: {COLLECTION_NAME}")
    return collection


def generate_texts():
    texts = []
    table_names = []
    chunk_types = []

    for table_name, info in TABLE_SCHEMAS.items():
        table_text = f"表名：{table_name}，中文名称：{info['cn_name']}，业务用途：{info['description']}"
        texts.append(table_text)
        table_names.append(table_name)
        chunk_types.append("table")

        for field_name, field_type, field_desc in info['fields']:
            field_text = f"表名：{table_name}，字段名：{field_name}，字段类型：{field_type}，字段中文含义：{field_desc}"
            texts.append(field_text)
            table_names.append(table_name)
            chunk_types.append("field")

    return texts, table_names, chunk_types


def init_vector_db():
    print("=" * 60)
    print("  向量库初始化")
    print("=" * 60)

    print(f"\n连接Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    print("✅ Milvus连接成功")

    print("\n生成文本切片...")
    texts, table_names, chunk_types = generate_texts()
    print(f"  共 {len(texts)} 条文本")

    print("\n调用远程API生成向量...")
    embeddings = get_embeddings(texts)
    print(f"  向量维度: {embeddings.shape}")

    print("\n创建集合并插入数据...")
    collection = create_collection()

    data = [
        table_names,
        chunk_types,
        texts,
        embeddings.tolist()
    ]
    collection.insert(data)
    collection.flush()
    print(f"✅ 插入 {len(texts)} 条数据")

    print("\n加载集合...")
    collection.load()

    print("\n" + "=" * 60)
    print("  ✅ 向量库初始化完成!")
    print("=" * 60)
    print(f"  集合名: {COLLECTION_NAME}")
    print(f"  数据量: {collection.num_entities}")


if __name__ == "__main__":
    init_vector_db()
