---
name: cyx-folder-deploy
description: 把一个本地文件夹里的项目（尤其 pnpm/Node monorepo、前后端分离的 Web 工作台）从零跑起来，并系统性排查「为什么跑不起来」。当用户说「帮我把这个项目跑起来」「这个项目怎么启动不了」「运行不起来」「pnpm 或 npm 装好但起不来」「localhost 返回 502 或 000」「pnpm 命令找不到」「端口不通」等时使用。即使项目根目录嵌套、缺 pnpm、缺配置文件、或之前的进程被会话重启清掉，也要用本技能先侦察再启动，不要凭空猜命令，也不要一上来就重装依赖。
---

# cyx-folder-deploy：把文件夹里的项目跑起来并排查起不来的原因

## 这个技能解决什么

用户丢来一个文件夹（往往是从别处拷来的、或隔了很久再打开的项目），要求"跑起来"。这类任务不是单一命令，而是一条链路：先看清项目是啥结构、缺什么工具链，再装、再编、再配、再起、再验证。真正的拦路石通常不是代码崩了，而是环境/PATH/配置/进程存活这些外围问题。本技能把这条链路和每个坑位固化下来，避免每次都从头排查。

适用信号（命中任意一条就启用）：
- "帮我把这个项目运行起来" / "把这个文件夹跑起来"
- "为什么跑不起来" / "启动不了" / "端口不通"
- 报错现象：`pnpm: command not found`、`localhost 返回 502`、`curl localhost 是 000`
- 项目里能看到 `pnpm-workspace.yaml`、多个 `packages/*`、前端 + 后端两个服务

不适用：纯静态 HTML/单文件、无需依赖安装就能跑的东西，那种直接打开即可，不必走这套流程。用户发来的是 **GitHub 链接、要从零部署**的，走 `cyx-github-deploy`（那边管"从仓库到第一次跑通"的路径选择和依赖取舍，这边管"已有文件夹跑不起来"的排查）。若**服务已跑起来、端口在听、但某个核心功能点了没反应**（任务不流转、生成无响应），属部署期遗漏的外部依赖（Redis/队列等），见 `cyx-github-deploy` 的「排障：功能点了没反应」取证顺序。

## 总流程（六步）

侦察 → 装工具链 → 装依赖 → 构建内部包 → 配工作区 → 启动并验证 → 固化。每一步都先验证再进下一步，不要跳步。

---

### 第 1 步：侦察项目结构

先看真实根目录在哪、项目是啥类型。

- 顶层没有 `package.json` 时，**目录可能嵌套了一层**（例如 `inkos-master/inkos-master/`）。先用 `ls` 确认，再进真正的根。
- 读这几个文件，判断启动方式：
  - `package.json`（根 + 各 `packages/*`）：看 `scripts`（dev/build/start）、`dependencies`
  - `pnpm-workspace.yaml`：确认是 monorepo
  - `README.md` / `README.zh.md`：看官方"本地运行"段落
  - `.env.example`：看需要哪些环境变量
  - `tsconfig.json`、`.nvmrc`、`.node-version`：看 node 版本要求
- 对每个子包，搞清楚它的角色（内核 / CLI / 网页前端 / 后端 API）和它怎么起。前端看 `vite.config.ts`（端口、代理），后端看入口文件（`src/api/index.ts` 之类）。

侦察到位的标准：你能说清"这个仓库有几个包、谁依赖谁、前端跑哪个端口、后端跑哪个端口、需不需要先 build"。

---

### 第 2 步：核对工具链（node / npm / pnpm）

```bash
node -v
npm -v
pnpm -v          # 很可能为空，见坑 2
cat .nvmrc        # 看要求的 node 大版本
```

- node 用 WorkBuddy 自带的 managed node（满足 ≥22 之类要求即可）。
- 如果项目强依赖 `pnpm`（有 `pnpm-lock.yaml` 且根 `package.json` 用 workspace），但 `pnpm -v` 报 `command not found`，**不要卡在这一步**，直接走坑 2 的"绕过 pnpm"方案，比反复装 pnpm 更稳。

---

### 第 3 步：安装依赖

优先用 pnpm（项目锁文件是 `pnpm-lock.yaml` 时）：

```bash
pnpm install
```

如果 `pnpm` 命令不在 PATH（见坑 2），改用 managed npm 全局装一次，或干脆在第 6 步用 `node` 直接调入口、本步仍用 `pnpm install`：

```bash
npm install -g pnpm@9
```

装完先看一眼有没有报错（peer 冲突一般可忽略，EINTEGRITY / 网络错才要处理）。

---

### 第 4 步：先构建被依赖的内部包（monorepo 关键顺序）

monorepo 里常有一个包被另一个包**直接 import 它的 `dist` 产物**。如果只起前端/后端而不先编这个包，启动会报"找不到模块"或"dist/index.html 不存在"。

- 用 grep 在后端入口里找 `import ... from '@scope/core'` 之类的内部包引用。
- 先 build 它：

```bash
pnpm --filter @scope/core build
# 绕过 pnpm 时：
cd packages/core && node <构建脚本或 tsc/tsx>   # 看 core 的 package.json scripts
```

确认 `packages/core/dist/` 生成后再起上层服务。

---

### 第 5 步：处理"必须在一个项目目录里运行"的要求

有些应用（如 InkOS Studio）**不能从源码仓库根直接起**，它要求在"一个写作/工作项目目录"里运行，根下必须有合法的项目配置文件（如 `inkos.json`，存服务/模型配置）。

为什么要单独建工作区：把这种运行时配置写进源码仓库会污染它（也常常因为缺这个文件直接启动失败）。正确做法是**新建一个独立于源码仓库的工作区目录**，在里面放配置文件，再用环境变量把应用指向它。

找字段要求的方法：读源码里的配置 schema（搜 `ProjectConfigSchema`、`inkos.json`、`config loader`），确认必填字段（通常至少 `name`、版本号、`llm` 的 provider/baseUrl/model）。密钥不要写进这个配置文件——多数应用把密钥单独存 `.inkos/secrets.json`，由网页 UI 填写。

```bash
mkdir -p /c/Users/admin/Desktop/inkos-workspace
# 在工作区里写一份合法的 inkos.json（字段照 schema 填）
```

---

### 第 6 步：启动并验证

**绕过 pnpm 直接启动**（最稳，避免 PATH 问题）。先确认入口文件名：

```bash
cd packages/studio
node -e "const j=require('./node_modules/vite/package.json');console.log(j.bin)"
node -e "const j=require('./node_modules/tsx/package.json');console.log(j.bin)"
```

拿到入口后分别启动后端（API）和前端（vite），都放后台常驻：

```bash
# 后端 API（示例端口 4569），用环境变量指定项目根
INKOS_STUDIO_PORT=4569 INKOS_PROJECT_ROOT="C:/Users/admin/Desktop/inkos-workspace" \
  node node_modules/tsx/dist/cli.mjs watch src/api/index.ts

# 前端 vite（示例端口 4567，反向代理 /api 到后端）
node node_modules/vite/bin/vite.js --host --port 4567
```

端口、环境变量名、入口路径都按侦察结果替换。两个都起后，**务必做真实连通验证**——见坑 5，别被代理 502 骗了：

```bash
curl --noproxy localhost -s -o /dev/null -w "%{http_code}\n" http://localhost:4567/
curl --noproxy localhost -s -o /dev/null -w "%{http_code}\n" http://localhost:4569/
curl --noproxy localhost -s http://localhost:4569/api/v1/services/config | head -c 200
```

`--noproxy localhost` 是关键：直连本机，绕过系统 HTTP 代理。

---

### 第 7 步：固化，方便下次一键恢复

WorkBuddy 的后台进程**不会跨会话 / 应用重启存活**（见坑 6）。把启动方式写进一个脚本，下次只需一条命令：

```bash
# start-studio.sh（放在独立工作区目录，不进源码仓库）
#!/usr/bin/env bash
set -e
STUDIO=/c/Users/admin/Desktop/inkos-master/inkos-master/packages/studio
ROOT=/c/Users/admin/Desktop/inkos-workspace
cd "$STUDIO"
INKOS_STUDIO_PORT=4569 INKOS_PROJECT_ROOT="$ROOT" \
  node node_modules/tsx/dist/cli.mjs watch src/api/index.ts &
node node_modules/vite/bin/vite.js --host --port 4567 &
wait
```

同时把启动要点、踩过的坑、那个 502 假象写进项目记忆（`.workbuddy/memory/MEMORY.md`），下次直接照着起。

如果用户希望**关机 / 重开 WorkBuddy 之后自动起来、完全不依赖会话**，那是 Windows 计划任务（开机自启，脱离会话），属于动系统启动项，先跟用户确认再动手，不要自作主张。

---

## 六个坑位（每个都给 why + 解法）

### 坑 1：根目录嵌套 + 顶层没有 package.json
仓库常被再包一层同名目录。先在文件管理器/终端里 `ls` 确认真实根，再进去做一切操作。在错的根上 `pnpm install` 会装到你不想装的地方。

### 坑 2：pnpm 不在 PATH（managed node 全局 prefix 陷阱）
用 managed node 的 `npm install -g pnpm` 装的 pnpm，落在** node 自己的全局 prefix 目录**，而 Git Bash 的 PATH 默认只含 `Roaming\npm` 等少数路径，所以当前会话里 `pnpm` 找不到（报 `command not found`），即便之前某次会话能跑。
解法有两层：
- 临时用：把 node 的全局 bin 加进当前会话 PATH，再 `pnpm exec`。
- 彻底绕开（推荐）：不用 `pnpm` 命令，直接用 `node` 执行项目里已经装好的包入口文件（坑 6 的启动命令）。项目 `node_modules` 里 vite/tsx 的软链都在，`require.resolve` 能定位，只是 pnpm 没建 `.bin` 链接、且受 `exports` 限制，所以手动 `node node_modules/<pkg>/<bin入口>` 最稳。

### 坑 3：monorepo 内部包要先 build
上层服务 import 的是内部包的 `dist`，没先编就会"找不到模块 / dist 不存在"。先用 grep 确认谁依赖谁，再 `pnpm --filter` 或 `node` 构建那个包。

### 坑 4：应用需要运行时项目配置（inkos.json 之类）
源码仓库本身不是"工作项目"，缺配置文件直接启动失败。新建**独立工作区**放配置，用环境变量指过去，不污染源码。

### 坑 5：系统代理导致 localhost 502 假象（最易误判）
机器上若有系统 HTTP 代理，你 `curl localhost:4567` 时请求会被代理拦下、返回 `502`，但你以为"服务挂了"。`netstat -ano | grep :4567` 会显示**根本没人监听**。用 `curl --noproxy localhost` 直连，真连得上就是 `200`。诊断端口状态时永远以 `netstat` / `--noproxy curl` 为准，不要信裸 `curl` 的 502。

### 坑 6：后台进程不跨会话存活
WorkBuddy 的后台命令（vite / tsx watch）只在当前会话内活着，会话结束或应用重启就被清掉，原后台句柄也会失效（状态变 `failed`）。所以"跑不起来"十有八九是**进程没了**，不是代码坏了。先 `netstat` 确认端口空闲、再按第 6 步重拉即可，不要去重装依赖或重 build。

---

## 输出给用户的口径

排查完要分清"表层现象"和"真正根因"再汇报，按"是什么 → 为什么 → 怎么办"讲：
- 先说清当前真实状态（端口是否在监听、有没有残留进程、配置文件/构建产物是否还在）。
- 再讲根因（进程被杀 / pnpm 不在 PATH / 缺配置 / 代理假象）。
- 最后讲做了什么、还差用户哪一步（比如去网页里配 API Key 才能真正用）。

不要一上来就重装依赖或重新 build——大部分"跑不起来"是环境/进程问题，地基没坏。
