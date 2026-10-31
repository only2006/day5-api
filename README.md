# AI 聊天助手

一个支持流式输出的网页对话应用：输入问题，回答逐字显示。
前端单页 + FastAPI 后端，支持多轮上下文与 token 成本统计。

> 演示动图：把录屏保存为 `docs/demo.gif` 即可在此显示（可选，不影响运行）。

## 快速开始

```bash
uv sync
cp .env.example .env      # 填入 DEEPSEEK_API_KEY
uv run uvicorn main:app --reload --port 8000
```

打开 http://127.0.0.1:8000　接口文档：http://127.0.0.1:8000/docs

> 演示地址是临时内网穿透，随时可能失效，所以只保证"本地一条命令能跑起来"。

## 功能

- **流式输出**：SSE 推送，首字延迟 < 1 秒，不是等全文生成完再显示
- **多轮对话**：客户端维护上下文，超过 10 轮自动截断，避免 token 爆炸
- **成本可见**：每轮返回 prompt / completion token，前端可选显示
- **输入校验**：消息长度、条数、temperature 范围都有上限，非法输入返回 422
- **错误兜底**：超时 / 限流 / 断网都有明确提示，不向前端泄露堆栈

## 技术栈

| 层 | 选型 | 为什么 |
|---|---|---|
| 后端 | FastAPI | 自动生成 `/docs`，pydantic 校验开箱即用 |
| 模型 | DeepSeek（OpenAI 兼容） | 便宜、国内直连、接口标准 |
| 流式 | SSE + fetch ReadableStream | `EventSource` 只支持 GET，POST 必须用 fetch |
| 前端 | 原生 HTML / JS | 无需构建工具，先把链路跑通 |

## 踩过的坑

1. **SSE 被缓冲，前端一次性刷出**
   一开始没设 `X-Accel-Buffering: no`，中间层把整个响应攒完才发。加了响应头 + 前端 `/diag` 测首字节时间才定位到。

2. **`EventSource` 用不了**
   它只支持 GET，而接口是 POST 且要传 `messages` 数组。最后用 `fetch` + `ReadableStream` 手动解析 `data: {...}\n\n`。

3. **中文偶尔乱码 / 丢字**
   `TextDecoder.decode()` 没加 `{stream: true}`，一个汉字被切在两次 `read()` 之间。加上后就正常了。

4. **最后半块 JSON 解析失败**
   `split("\n\n")` 之后直接遍历，没把最后一段留在 buffer 里 —— 那段可能只读了一半。

5. **静态文件挂在 `/` 把路由全吃掉**
   `app.mount("/", StaticFiles(...))` 之后 `/docs`、`/chat` 全 404。改成挂 `/static` + 根路径用 `FileResponse`。

## 后续计划

- [ ] 接入知识库（RAG）：上传文档后基于资料回答，并给出引用来源
- [ ] 会话持久化：目前历史只存在浏览器内存，刷新就没了
- [ ] 正式部署 + 自定义域名