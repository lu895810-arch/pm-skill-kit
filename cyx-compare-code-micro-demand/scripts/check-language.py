#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cyx-compare-code-micro-demand 语言机检。

对「对比需求文档」交付物做去 AI 味初筛：扫描 AI 味标签 / 套话 / 行业缩语 / 轻度口语 / emoji。
只做初筛——个别词在特定语境可能确实需要，人工复核每条命中后再决定改词还是放行。

用法：
    python scripts/check-language.py <交付HTML或MD>

退出码：0 = 无命中；1 = 有命中（逐条打印「类别 · 行号 · 片段」）。
"""
import io
import re
import sys

# 词表与 references/language-guard.md 保持一致；改词表时两处一起改。
CATEGORIES = [
    ('AI 味标签', [
        '一句话说清', '一句话结论', '一句话解读', '一句话总结', '一句话看清', '一句话读懂',
        '核心要点', '核心观点', '核心结论', '敲黑板', '划重点', '干货', '硬核', '保姆级',
        '执行摘要',
    ]),
    ('套话', [
        '赋能', '抓手', '闭环', '生态化', '组合拳', '颗粒度', '沉淀', '护城河',
        '镜像式互补', '开箱即用', '底座更完备', '把功夫花在',
    ]),
    ('行业缩语', [
        '耦合', '粒度', '跑通', '运维', '兜底', '语义', '系统性', '可插拔', '全量',
        '排障', '空烧', '打补丁', '数据主权', '可视化', '透视', '快照语义', '生产节拍',
        '链路', '幂等', '对齐比对', '治理',
    ]),
    ('口语词', [
        '很麻烦', '很烦', '就能用', '白白', '活儿', '东西', '手感', '挑片', '抽卡',
        '搞定', '说白了', '咱们', '咋', '啥', '弄好', '挺好',
    ]),
]

# ★☆（U+2605/U+2606）在对比矩阵里作评分刻度，属白名单，不算装饰 emoji
EMOJI_ALLOW = {'★', '☆'}
EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]')


def blank_out(m):
    """把命中的块替换成等量换行，保持行号不变。"""
    return '\n' * m.group(0).count('\n')


def clean(text):
    text = re.sub(r'<!--.*?-->', blank_out, text, flags=re.S)
    text = re.sub(r'<style[^>]*>.*?</style>', blank_out, text, flags=re.S | re.I)
    text = re.sub(r'<script[^>]*>.*?</script>', blank_out, text, flags=re.S | re.I)
    return text


def snippet(line, word):
    i = line.find(word)
    a = max(0, i - 12)
    b = min(len(line), i + len(word) + 12)
    s = line[a:b].strip()
    if a > 0:
        s = '…' + s
    if b < len(line):
        s = s + '…'
    return s


def main():
    if len(sys.argv) < 2:
        print('用法: python scripts/check-language.py <交付HTML或MD>')
        return 0
    path = sys.argv[1]
    try:
        raw = io.open(path, encoding='utf-8').read()
    except OSError as e:
        print('读不到文件: %s' % e)
        return 2

    text = clean(raw) if path.lower().endswith(('.html', '.htm')) else raw
    lines = text.split('\n')

    total = 0
    for cat, words in CATEGORIES:
        hits = []
        for n, line in enumerate(lines, 1):
            for w in words:
                if w in line:
                    hits.append((n, w, snippet(line, w)))
        if hits:
            print('\n【%s】命中 %d 处' % (cat, len(hits)))
            for n, w, s in hits:
                print('  L%-5d %-8s %s' % (n, w, s))
            total += len(hits)

    emoji = [(n, m) for n, line in enumerate(lines, 1)
             for m in EMOJI_RE.findall(line) if m not in EMOJI_ALLOW]
    if emoji:
        print('\n【emoji 装点】命中 %d 处' % len(emoji))
        for n, m in emoji:
            print('  L%-5d %s' % (n, m))
        total += len(emoji)

    print('\n—— 合计 %d 处待复核（脚本只做初筛，逐条人工确认改词还是放行）——' % total)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
