"""Shared application constants."""

DEFAULT_TIMEZONE = "Asia/Shanghai"
UTC_TIMEZONE_NAME = "UTC"
ASSISTANT_RESPONSE_INSTRUCTIONS = {
    "ride": {
        "estimate_price": "报价卡片已展示。不要重复价格明细，仅输出：请选择您想要的车型",
        "pending_payment_taxi_order": "订单卡片已展示。不要重复订单明细，仅输出：请点击完成支付",
    },
    "hotel": {
        "pending_payment_order": "订单卡片已展示。不要重复订单明细，仅输出：这是给您的推荐酒店",
    },
    "transport": {
        "pending_payment_train_order": "订单卡片已展示。不要重复订单明细，仅输出：这是给您的推荐出行方案",
        "pending_payment_flight_order": "订单卡片已展示。不要重复订单明细，仅输出：请点击完成支付",
        "pending_payment_bus_order": "订单卡片已展示。不要重复订单明细，仅输出：请点击完成支付",
    },
}
NEXT_ACTION_SUGGESTIONS = {
    "hotel_search": ["filter_hotel_rooms"],
    "location_search": ["ride_estimate_price"],
}
