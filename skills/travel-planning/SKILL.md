---
name: travel-planning
description: 整体规划：拆解跨城交通、酒店、送站/接站接驳，按子技能规则推进并控制输出长度。
---

## 适用范围

多环节组合行程（如跨城交通 + 酒店 + 接驳打车）。负责拆解顺序、补齐关键信息、协调各段工具调用。

## 核心原则

- 跨城交通：须用户确认去程/返程方案后再生成待支付交通数据（规则见 `transport-booking`）。
- 酒店与接驳打车：无特殊需求时按过往偏好直接推荐并下单（规则见 `hotel-booking`、`taxi-booking`），不轮询确认酒店、房型、车型偏好。
- 接驳顺序：先送站（去机场/车站），再接站/去酒店；不是只有用户提接站才做接站。
- 默认往返跨城交通；用户明确单程或无返程日期则单程。
- 一次只推进当前最关键确认；不输出大段文字、不重复工具列表。

## 执行流程

1. 补齐出发地、目的地城市、出发日期、返回/离店日期或停留天数。
2. **跨城交通**：`search_transport_options`（往返分别查）→ 用户选方案 → 对应 `create_pending_payment_*` 订单工具。
3. **酒店**（须先有入住/离店日期）：`hotel_search` → 按偏好选酒店 → `filter_hotel_rooms` → 选房型 → `create_pending_payment_hotel_order`。
4. **送站打车**：`location_search` → `ride_estimate_price`（有出发时间则预约单传 `order_type=2`、`booking_time_str`）→ 按偏好选车型 → `create_pending_payment_taxi_order`。
5. **接站/去酒店**：同上；有到达时间则预约单传时间。
6. 各段待支付数据生成后，未完成环节继续按序推进；用户明确不要打车且无法推断上下车点时可简短询问。

## 分步规则

### 信息补齐

- 关键缺失时一次只问一个最影响下一步的问题。
- 酒店段缺入住/离店/晚数时不先 `hotel_search`。

### 跨城交通段

- 仅用 `search_transport_options`。
- 去程、返程分别确认并分别生成待支付数据（单程例外）。
- 详细选方案与下单字段见 `transport-booking`。

### 酒店段

- 与 `hotel-booking` 一致：搜索必需信息补齐后，按过往偏好自动选酒店与房型并下单。
- 仅无法选定或与用户指定冲突时询问。

### 接驳打车段

- 与 `taxi-booking` 一致：验证地点 → 估价 → 按偏好直接下单。
- 送站上车点：酒店/当前位置/用户指定；目的地：去程出发机场/车站。
- 接站上车点：到达机场/车站；目的地：酒店或用户指定。
- `booking_time_str` 格式 `YYYY-MM-DD HH:mm`；仅有出发/到达时间时可估算送站上车时间，无法估算再问用户。
- 待支付打车订单成功后，支付/取消引导卡片，不重复下单。

### 推进顺序

- 可先并行查交通与酒店列表，但不要同时让用户确认多项。
- 优先完成跨城交通方案确认，再推进酒店与接驳。
- 交通与酒店待支付数据就绪后：先送站，再接站。

## 与其他技能协作

- 各段细则分别以 `transport-booking`、`hotel-booking`、`taxi-booking` 为准。
- 跨城城市间移动不算打车；仅站点/机场/酒店/景点间同城接驳走打车流程。

## 输出要求

- 简短；工具已展示的不重复列表；不编造状态。
- `search_transport_options` 后：推动选方案。
- `create_pending_payment_hotel_order` 成功：这是给您的推荐酒店
- `create_pending_payment_train_order` 成功：这是给您的推荐出行方案
- 接驳自动下单：`ride_estimate_price` 后不单独输出选车型；`create_pending_payment_taxi_order` 成功：请点击完成支付
- 需用户选车型时：`ride_estimate_price` 后：请选择您想要的车型
- 其他待支付工具：参考 `assistant_response_instruction`，并推进下一未完成段

## 相关工具

- search_transport_options
- create_pending_payment_flight_order
- create_pending_payment_train_order
- create_pending_payment_bus_order
- hotel_search
- filter_hotel_rooms
- create_pending_payment_hotel_order
- location_search
- ride_estimate_price
- create_pending_payment_taxi_order
