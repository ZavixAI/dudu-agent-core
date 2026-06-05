---
name: hotel-booking
description: 酒店预订：搜索酒店与房型，按用户过往偏好推荐并生成待支付酒店订单数据。
---

## 适用范围

处理酒店预订：补齐搜索条件 → 查酒店 → 查房型 → 生成待支付酒店订单数据；支付由前端卡片承接。

## 核心原则

- 无特殊需求时：`hotel_search` → 按过往偏好选一家酒店 → `filter_hotel_rooms` → 选最合适可订房型 → `create_pending_payment_hotel_order`，不轮询确认酒店、房型或品牌预算偏好。
- 只补齐搜索必需信息：入住地、入住日期、离店日期或晚数；偏好从过往推断，不逐项追问。
- 仅当与用户明确指定冲突、无可订项、候选无法区分、用户要换酒店/房型时，才询问用户。
- 不处理跨城交通与同城打车；不暴露底层 ID；不编造酒店、房型或库存。

## 执行流程

1. 判断搜索必需信息是否齐全；缺入住/离店日期或晚数时一次性补齐（如只说今天入住则追问离店或住几晚）。
2. `hotel_search`。
3. 按过往偏好选定一家酒店，`filter_hotel_rooms`。
4. 按过往偏好选定可订房型，`create_pending_payment_hotel_order`。
5. 成功后前端展示支付卡片。

## 分步规则

### 信息补齐

- 必需：入住城市/区域/地址、入住日期、离店日期或入住晚数。
- 可选：房间数、人数（默认一间房）；星级、品牌、预算等未提及时用过往偏好，不追问。
- 缺日期/晚数时不调用 `hotel_search`；不查一步问一步。

### 搜索与推荐

- `hotel_search` 后：不重复罗列列表；按过往偏好选性价比最合适的一家，进入 `filter_hotel_rooms`。
- `filter_hotel_rooms` 后：不重复罗列房型；选最合适可订产品，进入 `create_pending_payment_hotel_order`。
- 用户明确点选某酒店/房型：视为确认下单，非修改搜索条件。
- 工具若返回 `next_action_suggestions` / `assistant_response_instruction` 可参考，否则按本技能推进。

### 生成待支付订单

- 调用 `hotel_search` 后，工具结果对用户可见时，不重复罗列酒店列表；优先根据用户偏好选择合适酒店并进入房型查询。
- 如果用户已经给出明确偏好且搜索结果中存在明显匹配酒店，直接调用 `filter_hotel_rooms`；只有结果不明确、多个候选无法判断或缺少关键偏好时，才询问用户选择酒店。
- 调用 `hotel_search` 时最多查询前 3 页；如果前 3 页没有指定酒店的明显匹配，不要继续翻页，应提示未找到该酒店，并推荐附近可订酒店或询问用户是否更换条件。
- 调用 `filter_hotel_rooms` 后，工具结果对用户可见时，不重复罗列房型列表；如果存在明显符合偏好的房型产品，直接进入待支付订单生成。
- 用户明确选择房型时，优先理解为确认生成待支付酒店订单数据，而不是修改酒店搜索条件。
- 须有明确酒店、房型、`product_id`。
- 字段来自工具返回：`search_id`、`supplier` 或 `hotel_type`、`hotel_id`、`product_id`；不得编造。
- 成功后仅输出「这是给您的推荐酒店」。

## 与其他技能协作

- 去酒店或酒店后接驳 → `taxi-booking`。
- 交通+酒店组合 → `travel-planning`；不在此技能生成跨城交通待支付数据。

## 输出要求

- 缺信息只问一个最关键字段；不重复酒店/房型明细；不编造状态。
- `create_pending_payment_hotel_order` 成功：这是给您的推荐酒店

## 相关工具

- hotel_search
- filter_hotel_rooms
- create_pending_payment_hotel_order
