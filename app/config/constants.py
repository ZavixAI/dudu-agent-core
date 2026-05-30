"""Shared application constants."""

DEFAULT_TIMEZONE = "Asia/Shanghai"
UTC_TIMEZONE_NAME = "UTC"
ASSISTANT_RESPONSE_INSTRUCTION_FOR_ESTIMATE_PRICE = (
    "报价卡片已展示。不要重复价格明细，仅输出一句结束语：已经获取全部价格。"
)
ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_ORDER = (
    "订单卡片已展示。不要重复订单明细，仅输出一句结束语：已生成待支付订单信息。"
)
