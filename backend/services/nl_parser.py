# ============================================================
# 第二层：智能解析层
# 功能：调用大模型将口语问句转换为结构化标准词
# 大模型调用次数：第1次（共2次）
# ============================================================

import json
import logging
import requests
from typing import Dict, Any, List

from backend.core.config import config
from backend.core.exceptions import APIError

logger = logging.getLogger(__name__)


class NLParser:
    """
    自然语言解析器

    职责：
    1. 接收用户口语问句
    2. 注入标准指标/维度列表作为上下文
    3. 调用大模型输出结构化JSON（识别到的指标、维度、筛选条件）
    """

    SYSTEM_PROMPT = """你是一个专业的电商数据分析语义解析器。

## 任务
分析用户的自然语言问题，从中提取标准的业务指标和维度。

## 你拥有的标准词汇表
{metrics_and_dimensions}

## 口语别名映射表（重要！）
用户可能会用以下口语表达，请务必映射到对应的标准词：
{aliases_context}

## 解析示例（Few-shot）
以下是几个常见问题的解析示例，请参考：

示例1：
用户问：上个月GMV是多少？
输出：{{"metrics": ["GMV成交总额"], "dimensions": [], "filters": {{}}, "time_range": {{"start": "上月1日", "end": "上月最后一日"}}, "original_question": "上个月GMV是多少？"}}

示例2：
用户问：各个店铺类型的订单数
输出：{{"metrics": ["订单数"], "dimensions": ["店铺类型"], "filters": {{}}, "original_question": "各个店铺类型的订单数"}}

示例3：
用户问：今年每个月的下单金额和退款金额
输出：{{"metrics": ["下单金额", "退款金额"], "dimensions": ["下单时间"], "filters": {{}}, "time_range": {{"start": "2026-01-01", "end": "2026-12-31"}}, "original_question": "今年每个月的下单金额和退款金额"}}

示例4：
用户问：广东省的男性用户有多少
输出：{{"metrics": ["用户数"], "dimensions": [], "filters": {{"省份": "广东省", "性别": "M"}}, "original_question": "广东省的男性用户有多少"}}

示例5：
用户问：列出所有一级类目和它们的二级子分类
输出：{{"metrics": [], "dimensions": ["一级类目", "二级类目"], "filters": {{}}, "original_question": "列出所有一级类目和它们的二级子分类"}}

## 输出要求
严格返回JSON格式，不要输出其他内容：
{{
    "metrics": ["识别到的标准指标名称1", "标准指标名称2"],
    "dimensions": ["识别到的标准维度名称1", "标准维度名称2"],
    "filters": {{"维度名": "筛选值"}},
    "time_range": {{  // 如果有时间范围
        "start": "2024-01-01",
        "end": "2024-12-31"
    }},
    "original_question": "用户原始问题"
}}

## 规则
1. 只能从上面的标准词汇表中选择，禁止自创词汇
2. 遇到口语表达时，查找上面的口语别名映射表，转换为标准词
3. metrics: 可聚合的数值字段（金额、数量、人数）
4. dimensions: 用于分组/筛选的字段（时间、类别、状态等）
5. filters: 明确的筛选条件值
6. 如果无法理解，返回空数组"""

    def __init__(self):
        self.use_backup = config.use_backup_model
        if self.use_backup:
            self.api_key = config.backup_api_key
            self.api_url = config.backup_api_base_url
            self.model = config.backup_model_name
        else:
            self.api_key = config.api_key
            self.api_url = config.api_base_url
            self.model = config.model_name

    def switch_model(self, use_backup: bool = None):
        """切换使用的模型"""
        if use_backup is not None:
            self.use_backup = use_backup
        else:
            self.use_backup = not self.use_backup

        if self.use_backup:
            self.api_key = config.backup_api_key
            self.api_url = config.backup_api_base_url
            self.model = config.backup_model_name
        else:
            self.api_key = config.api_key
            self.api_url = config.api_base_url
            self.model = config.model_name

        logger.info(f"模型已切换: {'备用模型' if self.use_backup else '主模型'} ({self.model})")

    def parse(self, question: str, metrics_list: List[str], dimensions_list: List[str], aliases: List[Dict] = None) -> Dict[str, Any]:
        """
        解析自然语言问题

        Args:
            question: 用户口语问句
            metrics_list: 所有可用标准指标名列表
            dimensions_list: 所有可用标准维度名列表
            aliases: 口语别名映射列表 [{"spoken": "口语", "standard": "标准词"}]

        Returns:
            结构化字典：{metrics, dimensions, filters, time_range}
        """
        context = self._build_context(metrics_list, dimensions_list, aliases or [])

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT.format(metrics_and_dimensions=context[0], aliases_context=context[1])},
            {"role": "user", "content": f"请解析这个问题：{question}"}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 1024,
            "enable_thinking": False
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json=payload,
                timeout=config.api_timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            parsed = self._extract_json(content)
            parsed['original_question'] = question
            
            logger.info(f"解析完成 | 问题:{question[:30]}... | 指标:{parsed.get('metrics', [])} | 维度:{parsed.get('dimensions', [])}")
            return parsed
            
        except Exception as e:
            logger.error(f"解析失败: {str(e)}")
            raise APIError(f"大模型调用失败: {str(e)}")

    def _build_context(self, metrics: List[str], dimensions: List[str], aliases: List[Dict]) -> tuple:
        """构建上下文文本"""
        lines = ["### 标准指标（可聚合数值）"]
        for m in metrics:
            lines.append(f"- {m}")

        lines.append("\n### 标准维度（分组/筛选字段）")
        for d in dimensions:
            lines.append(f"- {d}")

        metrics_dims_context = '\n'.join(lines)

        aliases_lines = ["### 口语 → 标准词 映射表"]
        for a in aliases:
            aliases_lines.append(f"- \"{a['spoken']}\" → \"{a['standard']}\"")
        aliases_context = '\n'.join(aliases_lines) if aliases else "（暂无别名数据）"

        return metrics_dims_context, aliases_context

    @staticmethod
    def _extract_json(content: str) -> Dict:
        """从响应中提取JSON"""
        import re
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"metrics": [], "dimensions": [], "filters": {}}
