#!/usr/bin/env python3
# verify_render.py — 本地 HTML 排版自验（零依赖）
#
# 本机默认没有 Playwright。要"看渲染结果 / 验证排版"不需要装它：
# 直接用 ms-playwright 缓存里的 Chromium 无头截图即可。
#
# 用法：
#   python verify_render.py <文件.html> [--offsets 0,1500,3000] [--width 1600] [--out 目录]
#
# 原理：
#   1. 找 Chromium 可执行文件（CHROME_PATH 环境变量 → ms-playwright 缓存 → 常见安装位）。
#   2. 对每组 offset，生成一份临时副本，在 </head> 前注入
#        <style>html{margin-top:-Npx}</style>
#      把目标区域"顶"到视口顶部，再 --screenshot 截全屏，等于截到滚动区。
#   3. 输出 _render_0.png / _render_1500.png ... 到 --out（默认当前目录），脚本结束删临时副本。
#
# 与 webapp-testing 技能的"零依赖降级路径"同源，但封装成可复用脚本。

import sys, os, re, subprocess, shutil, tempfile, argparse

def find_chrome():
    env = os.environ.get("CHROME_PATH")
    if env and os.path.exists(env):
        return env
    # ms-playwright 缓存：默认在用户目录
    home = os.path.expanduser("~")
    candidates = []
    base = os.path.join(home, "AppData", "Local", "ms-playwright")
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            if name.startswith("chromium"):
                # chrome-win64/chrome.exe 或 chrome-linux/chrome
                for sub in ("chrome-win64/chrome.exe", "chrome-linux/chrome",
                            "chromium_headless_shell-*/chrome-win64/headless_shell.exe"):
                    if "*" in sub:
                        import glob
                        for p in glob.glob(os.path.join(base, name, sub)):
                            candidates.append(p)
                    else:
                        candidates.append(os.path.join(base, name, sub))
    # 其他常见安装位
    candidates += [
        r"C:/Program Files/Google/Chrome/Application/chrome.exe",
        r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="要验证的 HTML 文件路径")
    ap.add_argument("--offsets", default="0,1600,3200",
                    help="逗号分隔的滚动偏移(px)，每张截一张；0 即首屏")
    ap.add_argument("--width", type=int, default=1600, help="视口宽度")
    ap.add_argument("--height", type=int, default=900, help="视口高度")
    ap.add_argument("--out", default=".", help="输出目录")
    args = ap.parse_args()

    html = os.path.abspath(args.html)
    if not os.path.exists(html):
        print("找不到文件:", html); sys.exit(1)

    chrome = find_chrome()
    if not chrome:
        # 最后尝试 Playwright（若用户后来装了）
        try:
            import playwright  # noqa
            print("未找到独立 Chromium；请装 Playwright 或用 CHROME_PATH 指定浏览器。")
        except Exception:
            print("未找到 Chromium。设置 CHROME_PATH 或安装 ms-playwright。")
        sys.exit(2)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    offsets = [int(x) for x in args.offsets.split(",") if x.strip() != ""]

    tmp_files = []
    try:
        raw = open(html, encoding="utf-8").read()
        for off in offsets:
            inject = f"<style>html{{margin-top:-{off}px}}</style></head>"
            patched = raw.replace("</head>", inject, 1)
            if "</head>" not in raw:   # 没有 head 也兜住
                patched = raw
            fd, tmp = tempfile.mkstemp(suffix=".html", prefix="_vr_")
            os.write(fd, patched.encode("utf-8")); os.close(fd)
            tmp_files.append(tmp)
            out_png = os.path.join(out_dir, f"_render_{off}.png")
            cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                   "--no-sandbox", f"--window-size={args.width},{args.height}",
                   f"--screenshot={out_png}", f"file:///{tmp}"]
            print("→", os.path.basename(out_png), "offset", off)
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        for t in tmp_files:
            try: os.remove(t)
            except OSError: pass

    print("完成。输出：", os.path.abspath(out_dir))

if __name__ == "__main__":
    main()
