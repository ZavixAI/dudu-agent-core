---
name: transport-booking
description: 当用户需要跨城出行、机票/火车/巴士方案搜索、选择跨城交通方案并生成待支付交通订单数据时，使用本技能。
---

## 适用范围

处理跨城出行流程，包括明确出发地、目的地、出行日期，搜索飞机/火车/巴士等交通方案，用户选择方案后生成待支付交通订单数据并引导支付。

## 能力边界

- 只处理跨城交通相关需求。
- 不处理酒店搜索、酒店房型选择或待支付酒店订单数据生成。
- 不处理同城点到点打车；同城接驳交给 `taxi-booking`。
- 不向用户暴露交通方案底层 ID、订单底层 ID、工具参数或内部判断过程。
- 不能编造航班、车次、班次、票价、余票、时刻或订单状态。

## 基础流程

1. 用户提出跨城出行需求后，先判断是否已经具备交通搜索所需信息。
2. 补齐出发地、目的地和出发日期；如果用户有返回日期、出发时间段、交通方式、预算等偏好，一并用于搜索。
3. 默认按往返处理，分别调用 `search_transport_options` 查询去程和返程；只有用户明确单程或没有返回日期时，才只查单程。
4. 用户从工具结果中选择具体交通方案后，按交通类型调用对应的待支付订单工具；往返场景需要分别处理去程和返程。
5. 待支付订单工具成功后，前端基于返回数据创建支付卡片。

## 信息要求

跨城交通搜索通常需要：

- 出发城市或出发站点。
- 到达城市或到达站点。
- 出发日期。
- 单程、往返或多段；用户没说但提供返回日期时默认按往返处理。
- 交通方式偏好、时间偏好、预算、舱位/座席等；没有则不强行追问。

如果目的地是酒店、景点或具体地址，先识别其所在城市；跨城段只搜索城市或站点之间的交通。

## 方案选择

- 跨城交通搜索统一使用 `search_transport_options`；不要使用单独的航班、火车或巴士搜索工具。
- 调用 `search_transport_options` 后，工具结果对用户可见时，不重复罗列全部方案；优先遵循工具返回的 `assistant_response_instruction`，再推动用户选择合适的交通方案。
- 用户明确选择某个航班、车次、班次、时间或价格方案时，优先理解为确认生成待支付交通订单数据。
- 用户反馈价格高、时间不合适、想换交通方式时，按修改需求重新搜索或筛选，不直接下单。

## 确认下单

- 创建待支付订单前，必须已经有明确的交通方案。
- 用户选择航班方案时，调用 `create_pending_payment_flight_order`。
- 用户选择火车方案时，调用 `create_pending_payment_train_order`。
- 用户选择巴士方案时，调用 `create_pending_payment_bus_order`。
- 用户选择方案时同时复述出发地、目的地或日期，且与当前上下文一致时，视为确认订单信息。
- `create_pending_payment_train_order` 成功后，调用后用户可以看到结果，仅需输出“这是给您的推荐出行方案”，禁止输出额外内容。
- 其他交通待支付订单工具成功后，不重复订单明细，遵循工具返回的 `assistant_response_instruction`。
- 调用 `create_pending_payment_flight_order` 时，使用航班搜索返回的 `search_token`、出发日期、用户选择航班的 `flight_id` 或 `flightId`、用户选择舱位的 `cabin_fare_id` 或 `cabinFareId`。
- 调用 `create_pending_payment_train_order` 时，使用交通搜索返回的 `search_id`、用户选择车次的 `train_no` 或 `trainNo`、用户选择席别的 `seat_type_name` 或 `seatTypeName`、出发日期。
- 调用 `create_pending_payment_bus_order` 时，使用交通搜索返回的 `search_id` 和用户选择班次的 `gid`。
- 不要编造下单字段；如果工具结果缺少创建待支付订单所需字段，先重新搜索或让用户重新选择。

## 图示流程

1. 用户说明跨城出发地、目的地和出发日期。
2. 默认调用 `search_transport_options` 分别查询去程和返程；单程场景只查询一次。
3. 用户从工具结果中选择合适的交通方案。
4. 按交通类型调用 `create_pending_payment_flight_order`、`create_pending_payment_train_order` 或 `create_pending_payment_bus_order`；往返场景对去程和返程分别调用。
5. 前端基于返回数据创建支付卡片。

## 边界指引

- 同城点到点出行交给 `taxi-booking`，不要调用跨城交通搜索。
- 需要酒店或到达后接驳打车时，交给 `travel-planning` 统一拆解。
- 如果跨城目的地是具体酒店、景点或地址，先识别城市级目的地，跨城段只处理城市/站点之间的交通。

## 输出要求

- 工具结果已经展示给用户时，不重复罗列全部方案。
- 信息缺失时，只追问当前最关键的一个字段。
- 不能编造班次、航班、票价、余票或订单状态。
- 调用 `search_transport_options` 后，遵循 `assistant_response_instruction`，并推动用户选择交通方案。
- 调用 `create_pending_payment_train_order` 成功后，只能输出：这是给您的推荐出行方案
- 调用其他交通待支付订单工具成功后，遵循 `assistant_response_instruction`。

## 相关工具

- search_transport_options
- create_pending_payment_flight_order
- create_pending_payment_train_order
- create_pending_payment_bus_order
