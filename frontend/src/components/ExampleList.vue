<template>
  <div class="examples">
    <h3>💡 示例问题</h3>
    <div class="example-grid">
      <button
        v-for="(example, index) in EXAMPLES"
        :key="index"
        class="example-btn"
        @click="$emit('select', example)"
      >
        ▶️ {{ truncateText(example, 15) }}
      </button>
    </div>
  </div>
</template>

<script setup>
const EXAMPLES = [
  '查询所有状态为正常的用户数量',
  '找出商品价格最高的前5个商品',
  '统计每个分类下的商品数量',
  '查询近一个月内的订单总数和总金额',
  '找出下单量最多的用户',
  '查询评分最高的店铺',
  '统计每个店铺的总销售额',
  '查询使用优惠券最多的用户'
]

function truncateText(text, maxLength) {
  return text.length <= maxLength ? text : text.substring(0, maxLength) + '...'
}

defineEmits(['select'])
</script>

<style scoped>
.examples {
  padding: 16px 0;
}

.examples h3 {
  margin-bottom: 12px;
  font-size: 16px;
  color: #333;
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.example-btn {
  padding: 10px 15px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 20px;
  cursor: pointer;
  text-align: center;
  font-size: 13px;
  color: #333;
  transition: all 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.example-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}
</style>
