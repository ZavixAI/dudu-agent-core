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
2. 将需求拆成跨城交通、酒店和可选的同城接驳打车；整体规划默认需要往返跨城交通，除非用户明确只要单程。
3. 调用 `search_transport_options` 查询跨城交通方案；默认分别按出发日期查去程、按返回日期查返程。
4. 补齐入住日期、离店日期或入住晚数后，调用 `hotel_search` 查询酒店列表；缺少这些信息时不要先查酒店。
5. 用户选择交通方案后，按交通类型调用对应工具生成待支付交通订单数据。
6. 用户选择酒店后，调用 `filter_hotel_rooms` 查询该酒店可订房型。
7. 用户选择房型后，调用 `create_pending_payment_hotel_order` 生成待支付酒店订单数据。
8. 优先规划送站打车，即从用户当前位置、酒店或出发地前往去程交通的出发机场/车站。
9. 送站打车完成后，再规划到达后的接站/去酒店接驳，即从到达机场/车站前往酒店或用户指定地点。
10. 需要接驳打车时，调用 `location_search` 验证上车点和目的地。
11. 调用 `ride_estimate_price` 获取打车报价；如果已有航班、火车或巴士出发/到达时间，必须按预约单传 `order_type=2` 和 `booking_time_str`。
12. 用户选择车型后，调用 `create_pending_payment_taxi_order` 生成打车待支付订单。

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
- 酒店段必须先补齐入住日期、离店日期或入住晚数，再调用 `hotel_search`；不要查一步问一步。
- 酒店搜索结果中存在符合用户偏好的明显匹配项时，直接调用 `filter_hotel_rooms` 查询房型；房型结果中存在符合偏好的可订产品时，直接调用 `create_pending_payment_hotel_order`。
- 只有酒店或房型选择不明确、多个候选无法判断或偏好冲突时，才询问用户确认。
- 跨城交通搜索统一使用 `search_transport_options`；不要使用单独的航班、火车或巴士搜索工具。
- 整体规划默认需要分别让用户确认去程交通方案和返程交通方案；只有用户明确说单程、不需要返程或返回日期未知时，才按单程处理。
- 去程和返程都确认后，分别按交通类型调用对应的待支付订单工具；不要只生成单程待支付交通订单数据。
- 交通和酒店待支付数据都生成后，优先安排送站打车；送站打车处理完成后，再继续安排到达后的接站/去酒店接驳。
- 如果用户明确只要交通 + 酒店、明确不需要打车，或上下车点缺失且无法从交通/酒店结果推断，不要主动生成打车待支付订单数据；可以简短询问是否需要安排对应接驳打车。

## 接驳打车规则

- 默认接驳顺序是先规划送站打车，再规划到达后的接站/去酒店接驳；不是只有用户明确提出接站才规划接站。
- 送站打车的上车点优先使用酒店地址、用户当前位置或用户指定地点，目的地使用去程交通的出发机场/车站。
- 接站打车的上车点使用到达机场/车站，目的地使用酒店地址或用户指定地点。
- 必须先调用 `location_search` 验证上车点和目的地，再调用 `ride_estimate_price`。
- 送站打车如果已有交通出发时间，必须调用 `ride_estimate_price` 时传 `order_type=2` 和 `booking_time_str`，让报价被识别为预约单；不要漏传时间。
- 接站打车如果已有交通到达时间，也应调用 `ride_estimate_price` 时传 `order_type=2` 和 `booking_time_str`；无法确定实际用车时间时，先追问用户希望几点从机场/车站出发。
- `booking_time_str` 使用格式 `YYYY-MM-DD HH:mm`。如果只有交通出发时间但没有明确上车时间，可按需要提前到达机场/车站的常识估算一个送站上车时间；无法可靠估算时，先追问用户希望几点出发。
- 调用 `ride_estimate_price` 工具拿到车辆报价时，调用后用户可以看到工具执行结果，仅需输出“请选择您想要的车型”，禁止输出额外内容。
- 用户选择车型后调用 `create_pending_payment_taxi_order` 生成打车待支付订单数据，调用后用户可以看到结果，仅需输出“请点击完成支付”，禁止输出额外内容，`create_pending_payment_taxi_order` 成功后该打车子任务结束。
- `create_pending_payment_taxi_order` 成功后，后续支付、取消或订单确认统一由前端卡片承接；用户再要求支付或取消时，引导用户点击卡片，不要再次调用打车下单工具。

## 图示流程

1. 用户说明跨城目的地、出发日期和停留时间。
2. 调用 `search_transport_options` 查询跨城交通；默认分别查询去程和返程。
3. 调用 `hotel_search` 查询酒店列表。
4. 用户确认交通方案后，按类型调用 `create_pending_payment_flight_order`、`create_pending_payment_train_order` 或 `create_pending_payment_bus_order`；往返场景对去程和返程分别调用。
5. 用户确认酒店后调用 `filter_hotel_rooms`，再根据用户选择调用 `create_pending_payment_hotel_order`。
6. 基于交通和酒店的待支付数据、搜索结果或用户选择项优先规划送站打车。
7. 送站打车完成后，再规划到达后的接站/去酒店接驳。
8. 需要接驳打车时调用 `location_search`、`ride_estimate_price` 和 `create_pending_payment_taxi_order`；有出发或到达时间时，`ride_estimate_price` 必须按预约单传时间。

## 拆解指引

- 跨城段交给 `transport-booking` 的规则处理。
- 酒店段交给 `hotel-booking` 的规则处理。
- 同城接驳段交给 `taxi-booking` 的规则处理。
- 不要把跨城城市之间的移动当成打车；只有站点、机场、酒店、景点之间的同城接驳才进入打车流程。

## 输出要求

- 一次只推动当前最关键的确认动作，避免同时让用户选择过多事项。
- 整体规划过程中避免输出大段文字；只给出当前阶段最必要的确认、选择或下一步提示。
- 工具结果已经展示给用户时，不重复输出完整列表。
- 不能编造交通、酒店、房型、打车报价或订单状态。
- 调用 `search_transport_options` 后，不重复交通方案明细，并推动用户选择交通方案；如果工具返回 `assistant_response_instruction` 则参考它。
- 调用 `hotel_search` 后，不重复酒店明细；如果工具返回 `next_action_suggestions` 则参考它，否则按本技能规则推动用户选择酒店或进入房型查询。
- 调用 `filter_hotel_rooms` 后，不重复房型明细；如果工具返回 `assistant_response_instruction` 或 `next_action_suggestions` 则参考它，否则按本技能规则推动房型选择或生成待支付订单。
- 调用 `ride_estimate_price` 后，只能输出：请选择您想要的车型
- 调用 `create_pending_payment_taxi_order` 成功后，只能输出：请点击完成支付
- 调用 `create_pending_payment_hotel_order` 成功后，只能输出：这是给您的推荐酒店
- 调用 `create_pending_payment_train_order` 成功后，只能输出：这是给您的推荐出行方案
- 调用其他交通或酒店待支付订单工具成功后，不重复订单明细；如有工具返回的 `assistant_response_instruction` 则参考它，并继续推动下一个未完成环节。
- 当交通和酒店都已生成待支付数据且没有未完成选择时，优先推进送站打车；送站打车完成后，再推进到达后的接站/去酒店接驳。

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
