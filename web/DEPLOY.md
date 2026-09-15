# 在线入口 · 部署说明

`web/` 是一个无状态的分步 API + 一个静态页。每个请求只走链条的一步（演示档最长约 80 秒），
运行目录整个在请求体里来回传，服务端不存任何东西。引擎一行不改，`restore()` 从产物重建窗口历史。

`POST /api/step` 请求体：`{seed, files, mode, decision}`。`mode` 取 `auto` / `hitl`，**开链时定死**，之后从 `run.json` 读；
`hitl` 到必停点时响应带 `awaiting`（选项、上下文、材料包），这一步的产出暂存在 `files` 里的 `_pending.json`，
下一个请求带 `decision: {position, choice, instruction}` 回来接着走——选 `accept` 不再调模型。

运行控制（停止 / 继续 / 重试这一步 / 下载运行记录）全在浏览器端：`files` 对象就是全部状态，
停止只是不发下一个请求，继续就是带着现有 `files` 再进循环，重试是重发同一请求，下载是把 `files` 拼成一份 `.md`。
服务端不需要为这些做任何事。

## 本地

```bash
pip install -r requirements.txt
cp .env.example .env          # 填四个 key + LIANGYI_OWNER_TOKEN
python3 web/server.py         # http://127.0.0.1:8765
```

自己不受每天 3 次的限制：URL 后面加 `?owner=<你的 LIANGYI_OWNER_TOKEN>`。

## Vercel（现状：已部署，push 即上线）

线上 https://liangyi-five.vercel.app ，Vercel 项目已连 GitHub `wenboxia/liangyi`，**push 到 `main` 自动重新部署**，
不需要再手动 `vercel --prod`。环境变量、Upstash KV 都已配好。

仓库里的部署相关文件：

- `api/index.py`——**唯一的 Python 函数**，同时处理 `/`（返回 `web/index.html`）、`/api/plan`、`/api/step`。
  Vercel 不会自动发现 `api/*.py` 下的多个文件，所以并成一个入口
- `pyproject.toml`——依赖（openai / pyyaml / python-dotenv / rich）+ `[tool.vercel] entrypoint = "api.index:handler"`。
  **Vercel 只读 pyproject，不读 requirements.txt**，新依赖两边都要加
- `api/_shared.py`——限次（KV / 内存）与 owner 令牌
- `vercel.json`——`maxDuration: 300`
- `.vercelignore`——**挡住 `.env`** 和 runs/、archive/、docs/ 等档案

从零重建时：

```bash
npx vercel login
npx vercel link
npx vercel --prod
```

然后在 Vercel 项目 → Settings → Environment Variables 填五个：
`OPENROUTER_API_KEY` `DEEPSEEK_API_KEY` `MOONSHOT_API_KEY` `ZHIPU_API_KEY` `LIANGYI_OWNER_TOKEN`
（密钥由项目所有者自己填，不经 AI 之手）。改环境变量后要重新部署一次才生效；Git 已连的话 push 一个空 commit 即可。

**限次在 serverless 上的实话**：实例之间不共享内存，纯内存计数基本不起作用。
要让「每 IP 每天 3 次」真的挡得住，在 Vercel Marketplace 加一个 Upstash Redis（免费档够用），
它会注入 `KV_REST_API_URL` / `KV_REST_API_TOKEN`（或 `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN`，两套名字都认），
`api/_shared.py` 检测到就切到 KV 计数。响应头 `X-Liangyi-Limit: kv` 表示生效，`memory` 表示只有弱限次。

**Deployment Protection** 要关掉，否则 API 请求会被 302 到登录页。

**函数时长**：`maxDuration: 300` 需要 Fluid Compute（Hobby 套餐也支持）。
若部署后第一步就报超时，去项目 Settings → Functions 确认 Fluid Compute 已开。

## 或者一台小机器（Railway / Render / Fly）

直接 `python3 web/server.py`，`PORT` 交给平台。内存限次在单进程上是有效的。

## 花费

演示档一条完整链约 **$0.07–0.09、8–10 分钟**（线上实测 8.6 分钟 / $0.078；CLI 10.4 分钟 / $0.084；本地端到端 7 分 59 秒 / $0.072，含自动生成角色）。
每 IP 每天 3 次，100 个访客一天上限约 $24。正式档（`primary`）不适合在线——单盲那一步最长跑过 1199 秒。
