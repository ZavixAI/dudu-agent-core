"""Shared application constants."""

DEFAULT_TIMEZONE = "Asia/Shanghai"
UTC_TIMEZONE_NAME = "UTC"
ASSISTANT_RESPONSE_INSTRUCTION_FOR_ESTIMATE_PRICE = (
    "报价卡片已展示。不要重复价格明细，仅输出：请选择您想要的车型"
)
ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_TAXI_ORDER = (
    "订单卡片已展示。不要重复订单明细，仅输出：请点击完成支付"
)
ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_HOTEL_ORDER = (
    "订单卡片已展示。不要重复订单明细，仅输出：这是给您的推荐酒店"
)
ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_TRAIN_ORDER = (
    "订单卡片已展示。不要重复订单明细，仅输出：这是给您的推荐出行方案"
)
ASSISTANT_RESPONSE_INSTRUCTION_FOR_PENDING_PAYMENT_ORDER = (
    "订单卡片已展示。不要重复订单明细，仅输出：请点击完成支付"
)
NEXT_ACTION_SUGGESTIONS_FOR_HOTEL_SEARCH = ["filter_hotel_rooms"]
NEXT_ACTION_SUGGESTIONS_FOR_LOCATION_SEARCH = ["ride_estimate_price"]
