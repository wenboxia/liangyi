# 在线入口 · 部署说明

`web/` 是一个无状态的分步 API + 一个静态页。每个请求只走链条的一步（演示档最长约 80 秒），
运行目录整个在请求体里来回传，服务端不存任何东西。引擎一行不改，`restore()` 从产物重建窗口历史。

## 本地

```bash
pip install -r requirements.txt
cp .env.example .env          # 填四个 key + LIANGYI_OWNER_TOKEN
python3 web/server.py         # http://127.0.0.1:8765
```

自己不受每天 3 次的限制：URL 后面加 `?owner=<你的 LIANGYI_OWNER_TOKEN>`。

## Vercel

仓库里已有：`api/plan.py`、`api/step.py`（Python 函数）、`api/_shared.py`、`vercel.json`
（`maxDuration: 300`，`/` → `web/index.html`）、`.vercelignore`（**挡住 `.env`** 和 runs/ 等档案）。

```bash
npx vercel login
npx vercel link          # 建项目
npx vercel --prod
```

然后在 Vercel 项目 → Settings → Environment Variables 填五个：
`OPENROUTER_API_KEY` `DEEPSEEK_API_KEY` `MOONSHOT_API_KEY` `ZHIPU_API_KEY` `LIANGYI_OWNER_TOKEN`
（改完环境变量要再 `npx vercel --prod` 一次才生效）。

**限次在 serverless 上的实话**：实例之间不共享内存，纯内存计数基本不起作用。
要让「每 IP 每天 3 次」真的挡得住，在 Vercel Marketplace 加一个 Upstash Redis（免费档够用），
它会自动注入 `KV_REST_API_URL` / `KV_REST_API_TOKEN`，`api/_shared.py` 检测到就切到 KV 计数。
没配时响应头会带 `X-Liangyi-Limit: memory` 提醒这是弱限次。

**函数时长**：`maxDuration: 300` 需要 Fluid Compute（Hobby 套餐也支持）。
若部署后第一步就报超时，去项目 Settings → Functions 确认 Fluid Compute 已开。

## 或者一台小机器（Railway / Render / Fly）

直接 `python3 web/server.py`，`PORT` 交给平台。内存限次在单进程上是有效的。

## 花费

演示档一条完整链约 **$0.07–0.09、8–10 分钟**（CLI 实测 10.4 分钟 / $0.084；网页端到端 7 分 59 秒 / $0.072，含自动生成角色）。
每 IP 每天 3 次，100 个访客一天上限约 $24。正式档（`primary`）不适合在线——单盲那一步最长跑过 1199 秒。
