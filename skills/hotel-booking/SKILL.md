---
name: hotel-booking
description: 当用户需要酒店查询、房型报价、选择房型并生成待支付酒店订单数据时，使用本技能。
---

## 适用范围

处理酒店预订流程，包括确认入住城市/区域、查询酒店、查询房型、用户选择房型、生成待支付酒店订单数据和引导支付。

## 能力边界

- 只处理酒店预订相关需求。
- 不处理跨城交通方案搜索，不生成机票、火车、巴士或打车待支付订单数据。
- 不向用户暴露酒店底层 ID、房型底层 ID、工具参数或内部判断过程。
- 不能编造酒店、房型、价格、库存、取消政策或订单状态。

## 基础流程

1. 用户提出酒店需求后，先判断是否已经具备酒店搜索所需信息。
2. 补齐入住目的地、入住日期、离店日期或入住晚数；如果用户给出价格、星级、位置、品牌等偏好，一并用于搜索。
3. 调用 `hotel_search` 查询酒店列表。
4. 用户选择酒店后，调用 `filter_hotel_rooms` 获取该酒店可订房型。
5. 用户选择房型后，调用 `create_pending_payment_hotel_order` 生成待支付酒店订单数据。
6. `create_pending_payment_hotel_order` 成功后，前端基于返回数据创建支付卡片。

## 信息要求

酒店搜索通常需要：

- 入住城市、区域、商圈、景点、会场或具体地址。
- 入住日期。
- 离店日期或入住晚数。
- 房间数和入住人数；用户没说时可按默认一间房处理。
- 预算、星级、品牌、早餐、可退款、床型等偏好；没有则不强行追问。

如果用户只说“今天入住”但没有离店日期，优先追问离店日期或住几晚。

## 酒店与房型选择

- 调用 `hotel_search` 后，工具结果对用户可见时，不重复罗列酒店列表；如果返回 `next_action_suggestions`，按建议推动用户选择酒店并进入房型查询。
- 用户选择酒店后再调用 `filter_hotel_rooms`，不要在没有酒店选择时直接查房型。
- 调用 `filter_hotel_rooms` 后，工具结果对用户可见时，不重复罗列房型列表；优先遵循工具返回的 `assistant_response_instruction`，并按 `next_action_suggestions` 推动用户选择房型。
- 用户明确选择房型时，优先理解为确认生成待支付酒店订单数据，而不是修改酒店搜索条件。

## 确认下单

- 调用 `create_pending_payment_hotel_order` 前，必须已经有明确酒店、房型和产品。
- 用户选择房型时同时复述入住日期、离店日期或酒店名称，且与当前上下文一致时，视为确认订单信息。
- `create_pending_payment_hotel_order` 成功后，不重复订单明细，遵循工具返回的 `assistant_response_instruction`。
- `create_pending_payment_hotel_order` 需要使用 `hotel_search` 或 `filter_hotel_rooms` 返回中的 `search_id`，酒店结果中的 `supplier` 或 `hotel_type`，酒店 `hotel_id`，以及用户选择房型产品的 `product_id`。不要编造这些字段；缺少时先重新查询房型。

## 边界指引

- 用户需要从当前位置去酒店，或酒店订单完成后需要同城接驳时，交给 `taxi-booking` 处理打车段。
- 用户同时需要跨城交通和酒店时，交给 `travel-planning` 统一拆解，不在本技能里独立生成跨城交通待支付订单数据。
- 不处理跨城交通方案搜索，不把酒店目的地误判为跨城出行终点。

## 输出要求

- 工具结果已经展示给用户时，不重复罗列酒店或房型明细。
- 信息缺失时，只追问当前最关键的一个字段。
- 不能编造酒店、房型、价格、库存或订单状态。
- 调用 `hotel_search` 后，不重复酒店明细，结合 `next_action_suggestions` 推动下一步。
- 调用 `filter_hotel_rooms` 后，遵循 `assistant_response_instruction`，并结合 `next_action_suggestions` 推动下一步。
- 调用 `create_pending_payment_hotel_order` 成功后，遵循 `assistant_response_instruction`。

## 相关工具

- hotel_search
- filter_hotel_rooms
- create_pending_payment_hotel_order
