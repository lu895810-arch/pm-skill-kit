---
name: webapp-testing
description: Toolkit for interacting with and testing local web applications. Verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs. Also covers the zero-dependency fallback for this machine, where Playwright is NOT installed — use headless Chromium directly to screenshot and verify a local HTML file's layout.
license: Complete terms in LICENSE.txt
agent_created: true
display_name: "Web 应用测试"
display_name_en: "WebApp Testing"
---

# Web Application Testing

To test local web applications, write native Python Playwright scripts.

## 第 0 步：先确认 Playwright 装没装（不要跳）

本机（Windows 桌面环境）**默认没有 Playwright**。先探一下，别直接开写脚本：

```bash
"C:/Users/admin/.workbuddy/binaries/python/versions/3.13.12/python.exe" -c "import playwright" 2>&1 | tail -1
# ModuleNotFoundError → 走下面的「零依赖降级路径」
```

### 零依赖降级路径：直接用 Chromium 无头截图

只要目的是**看渲染结果 / 验证排版**，不需要装 Playwright。本机已有 Chromium 缓存：

```bash
CHROME="C:/Users/admin/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-sandbox \
  --window-size=1440,980 \
  --screenshot="OUT.png" "file:///C:/绝对路径/页面.html"
```

- **每次截图前先定位 chrome.exe**（上面那个版本号目录会变，别写死）：
  `find "C:/Users/admin/AppData/Local/ms-playwright" -maxdepth 3 -iname "chrome.exe"`
- 输出路径和输入 URL **都要用绝对路径**；URL 走 `file:///` 三斜杠。
- 中文文件名路径可以直接用，Chromium 能认，不用 URL 编码。
- 默认只截当前视口（`--window-size` 决定），**没有 full-page**。

### 想看首屏以下的部分：注入负 margin

Chromium 无头截图截不到滚动区之外。要截页面中段/尾段，复制一份临时副本，在 `</head>` 前注入：

```python
s = s.replace('</head>', '<style>html{margin-top:-2050px}</style></head>')
```

截完**把临时副本和 png 都删掉**，别留在 Lulu 的桌面上。

### 什么时候还是得装 Playwright

需要**点击、填表单、等 JS、抓 console 日志**这类交互时才值得装：
`install_binary` 装完后用 `scripts/with_server.py`。纯"看排版对不对"用上面的降级路径就够了，别为了截图装一整套。

**Helper Scripts Available**（以下均假设 Playwright 已装）:
- `scripts/with_server.py` - Manages server lifecycle (supports multiple servers)

**Always run scripts with `--help` first** to see usage. DO NOT read the source until you try running the script first and find that a customized solution is abslutely necessary. These scripts can be very large and thus pollute your context window. They exist to be called directly as black-box scripts rather than ingested into your context window.

## Decision Tree: Choosing Your Approach

```
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         ├─ Success → Write Playwright script using selectors
    │         └─ Fails/Incomplete → Treat as dynamic (below)
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Run: python scripts/with_server.py --help
        │        Then use the helper + write simplified Playwright script
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for networkidle
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Example: Using with_server.py

To start a server, run `--help` first, then use the helper:

**Single server:**
```bash
python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_automation.py
```

**Multiple servers (e.g., backend + frontend):**
```bash
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_automation.py
```

To create an automation script, include only Playwright logic (servers are managed automatically):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Always launch chromium in headless mode
    page = browser.new_page()
    page.goto('http://localhost:5173') # Server already running and ready
    page.wait_for_load_state('networkidle') # CRITICAL: Wait for JS to execute
    # ... your automation logic
    browser.close()
```

## Reconnaissance-Then-Action Pattern

1. **Inspect rendered DOM**:
   ```python
   page.screenshot(path='/tmp/inspect.png', full_page=True)
   content = page.content()
   page.locator('button').all()
   ```

2. **Identify selectors** from inspection results

3. **Execute actions** using discovered selectors

## Common Pitfall

❌ **Don't** inspect the DOM before waiting for `networkidle` on dynamic apps
✅ **Do** wait for `page.wait_for_load_state('networkidle')` before inspection

## Best Practices

- **Use bundled scripts as black boxes** - To accomplish a task, consider whether one of the scripts available in `scripts/` can help. These scripts handle common, complex workflows reliably without cluttering the context window. Use `--help` to see usage, then invoke directly. 
- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Use descriptive selectors: `text=`, `role=`, CSS selectors, or IDs
- Add appropriate waits: `page.wait_for_selector()` or `page.wait_for_timeout()`

## Reference Files

- **examples/** - Examples showing common patterns:
  - `element_discovery.py` - Discovering buttons, links, and inputs on a page
  - `static_html_automation.py` - Using file:// URLs for local HTML
  - `console_logging.py` - Capturing console logs during automation