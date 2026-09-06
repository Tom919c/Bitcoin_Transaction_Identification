# Browser Transport Evidence — packet btc-expcampaign-20260906-01

日期：2026-09-06。传输方式：chrome-devtools-mcp 控制 Chrome 浏览器访问 chatgpt.com（用户明确指定的传输方式；偏离技能默认的 ChatGPT 桌面应用内浏览器，已向用户说明）。

## Preflight（发送前）

- 页面：Chrome 标签页 1，https://chatgpt.com/c/6a9d243f-6660-83ea-917d-5b2438b06c1b（会话"研究创新方案"，即产出深度研究报告的会话）。
- 认证状态：已登录（可见历史会话、composer、个人资料菜单按钮）。
- 模型可见性：composer"思考强度"菜单展开后显示"GPT-5.6 Sol（已选中）"与"GPT-5.5"，思考强度为"高"。requested_reasoner = GPT-5.6 Sol。
- 阻断状态：无登录墙、无 CAPTCHA、无速率限制、无异常活动提示。
- 自动化同意门：automation-consent status = READY（启用，disclosure v1）。

## Submission（发送）

- 通过 a11y 快照定位 composer（textbox"与 ChatGPT 聊天"），用 fill 一次性写入 packet + reasoning-request 全文；快照复核输入框 value 与 packet 文件一致。
- 点击"发送提示词"按钮一次；用户消息出现在会话中（uid=5_0 全文可见），随后出现"停止回答"按钮与"正在思考"状态，确认提交成功。
- 未重试、未重复发送。

## Response（接收）

- 等待生成完成：轮询确认"停止回答"按钮消失，且页面文本中 BEGIN_REASONING_RESULT / END_REASONING_RESULT 各出现 2 次（1 次为用户消息模板，1 次为完整回复）。
- 通过页面上最新回复的"复制回复"按钮（可见复制动作）复制一次，剪贴板读取得到完整契约文本，含 packet_id: btc-expcampaign-20260906-01。
- 未从 DOM 直接抓取回复正文；未刷新、未继续追问、未重发。

## Postflight（完成后）

- 会话与 Preflight 相同；模型仍为 GPT-5.6 Sol / 思考强度"高"。
- 回复操作组（复制回复/评价回复/分享）可见，回复完整。

## 备注

- 模型身份为可见 UI 级证据（选择器标签"已选中"GPT-5.6 Sol），非后端密码学证明；按技能规则记为 unverified 的可见证据基础。
- 本文件不含回复正文与 packet 正文。
