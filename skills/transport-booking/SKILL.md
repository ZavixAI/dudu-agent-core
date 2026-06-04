---
name: transport-booking
description: 跨城出行：搜索交通方案，用户选定后生成待支付机票/火车/巴士订单数据。
---

## 适用范围

处理跨城交通：出发地、目的地、日期 → `search_transport_options` → 用户选定方案 → 生成待支付交通订单数据。

## 核心原则

- 跨城搜索统一使用 `search_transport_options`，不用单项航班/火车/巴士搜索工具。
- 默认往返：有返回日期则分别查去程与返程；用户明确单程或无返程日期则只查单程。
- 须用户选定具体方案后再下单；不编造班次、票价或余票。
- 不处理酒店、同城打车；目的地为酒店/景点时先识别所在城市再搜交通。

## 执行流程

1. 补齐出发地、目的地、出发日期（及返程日期若往返）。
2. `search_transport_options`（往返则去程、返程各查一次）。
3. 推动用户从结果中选择方案。
4. 按类型调用 `create_pending_payment_flight_order` / `create_pending_payment_train_order` / `create_pending_payment_bus_order`（往返分别处理）。
5. 成功后前端展示支付卡片。

## 分步规则

### 信息补齐

- 必需：出发/到达城市或站点、出发日期。
- 可选：交通方式、时间、预算、舱位/座席；未提供则不强行追问。

### 搜索与选方案

- 结果对用户可见时不重复罗列全部方案；推动用户选择。
- 用户明确选定航班/车次/班次/时间/价格 → 确认为下单意图。
- 嫌贵、时间不合适、换方式 → 重新搜索，不直接下单。

### 生成待支付订单

| 类型 | 工具 | 主要字段 |
| --- | --- | --- |
| 航班 | create_pending_payment_flight_order | search_token、出发日期、flight_id/flightId、cabin_fare_id/cabinFareId |
| 火车 | create_pending_payment_train_order | search_id、train_no/trainNo、seat_type_name/seatTypeName、出发日期 |
| 巴士 | create_pending_payment_bus_order | search_id、gid |

- 火车下单成功：仅输出「这是给您的推荐出行方案」。
- 其他交通下单成功：不重复明细；有 `assistant_response_instruction` 则参考。

## 与其他技能协作

- 同城点到点 → `taxi-booking`。
- 交通+酒店+接驳 → `travel-planning`。

## 输出要求

- 缺信息只问一个最关键字段；不重复方案明细。
- `search_transport_options` 后：推动选方案，不罗列明细。
- `create_pending_payment_train_order` 成功：这是给您的推荐出行方案

## 相关工具

- search_transport_options
- create_pending_payment_flight_order
- create_pending_payment_train_order
- create_pending_payment_bus_order
