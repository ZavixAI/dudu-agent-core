---
name: travel-planning
description: 当用户需要整体规划跨城交通、酒店和到达后打车等组合行程时，使用本技能。
---

## 适用范围

处理整体出行规划，负责把跨城交通、酒店预订和同城接驳打车拆成可执行的子任务，并按顺序推动用户确认。

## 能力边界

- 只处理包含多个履约环节的整体行程，例如跨城交通 + 酒店、跨城交通 + 酒店 + 到达后打车。
- 不直接编造交通、酒店、房型、打车报价或订单状态。
- 不把跨城城市之间的移动当成同城打车。
- 不向用户暴露底层 ID、工具参数、内部拆解过程或替换关系。

## 基础流程

1. 用户提出整体规划需求后，先补齐出发地、目的地、出发日期、返回日期或入住天数。
2. 将需求拆成跨城交通、酒店和可选的同城接驳打车。
3. 调用 `rideclaw_aggregated_transport_search_v2` 查询跨城交通方案。
4. 调用 `rideclaw_search_hotels` 查询酒店列表。
5. 用户选择交通方案后，调用对应的 `create_order` 创建交通订单。
6. 用户选择酒店后，调用 `rideclaw_filter_hotel_rooms` 查询该酒店可订房型。
7. 用户选择房型后，调用 `create_hotel_order` 创建酒店订单。
8. 基于已创建交通订单的到达站点、时间和酒店订单地址，判断是否需要安排站点到酒店的同城接驳。
9. 需要接驳时，调用 `rideclaw_search_location` 验证站点和酒店地址。
10. 调用 `rideclaw_estimate_price` 获取接驳打车报价。
11. 用户选择车型后，调用 `create_taxi_order` 生成打车支付订单。

## 信息要求

整体规划通常需要：

- 出发地。
- 目的地城市。
- 出发日期。
- 返回日期、离店日期或停留天数。
- 出行人数、房间数；用户没说时按默认一人一间或项目默认策略处理。
- 交通方式、酒店预算、酒店位置、接驳需求等偏好；没有则不强行追问。

如果关键信息缺失，一次只追问一个最影响下一步搜索的问题。

## 并行与确认顺序

- 可以先分别查询跨城交通和酒店列表，但不要同时要求用户确认太多事项。
- 先推动用户选择跨城交通方案，再推动用户选择酒店和房型。
- 交通和酒店订单都创建后，才判断是否需要站点到酒店的同城接驳打车。
- 如果用户明确只要交通 + 酒店，不要主动创建打车订单；只在用户提出或流程需要接驳时进入打车。

## 接驳打车规则

- 接驳打车的上车点优先使用交通订单的到达机场、车站或下车站点。
- 接驳打车的目的地优先使用酒店订单中的酒店地址。
- 必须先调用 `rideclaw_search_location` 验证接驳上车点和目的地，再调用 `rideclaw_estimate_price`。
- 调用 `rideclaw_estimate_price` 后，工具结果对用户可见时，仅提示用户选择车型。
- 用户选择车型后调用 `create_taxi_order`，成功后仅提示用户完成支付。

## 图示流程

1. 用户说明跨城目的地、出发日期和停留时间。
2. 调用 `rideclaw_aggregated_transport_search_v2` 查询跨城交通。
3. 调用 `rideclaw_search_hotels` 查询酒店列表。
4. 用户确认交通方案后调用 `create_order`。
5. 用户确认酒店后调用 `rideclaw_filter_hotel_rooms`，再根据用户选择调用 `create_hotel_order`。
6. 基于交通订单和酒店订单信息判断是否需要接驳。
7. 需要接驳时调用 `rideclaw_search_location`、`rideclaw_estimate_price` 和 `create_taxi_order`。

## 拆解指引

- 跨城段交给 `transport-booking` 的规则处理。
- 酒店段交给 `hotel-booking` 的规则处理。
- 同城接驳段交给 `taxi-booking` 的规则处理。
- 不要把跨城城市之间的移动当成打车；只有站点、机场、酒店、景点之间的同城接驳才进入打车流程。

## 输出要求

- 一次只推动当前最关键的确认动作，避免同时让用户选择过多事项。
- 工具结果已经展示给用户时，不重复输出完整列表。
- 不能编造交通、酒店、房型、打车报价或订单状态。
- 调用 `rideclaw_aggregated_transport_search_v2` 后，只提示用户选择交通方案。
- 调用 `rideclaw_search_hotels` 后，只提示用户选择酒店。
- 调用 `rideclaw_filter_hotel_rooms` 后，只提示用户选择房型。
- 调用 `rideclaw_estimate_price` 后，只提示用户选择车型。
- 调用任一创建订单工具成功后，只提示用户完成支付或继续确认下一个未完成环节。

## 相关工具

- rideclaw_aggregated_transport_search_v2
- create_order
- rideclaw_search_hotels
- rideclaw_filter_hotel_rooms
- create_hotel_order
- rideclaw_search_location
- rideclaw_estimate_price
- create_taxi_order
