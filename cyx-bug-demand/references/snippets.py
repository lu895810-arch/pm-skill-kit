# cyx-bug-demand 关键代码片段

> 全部来自 2026-09-29 真实交付中验证可用的写法。运行环境：Python 3.13.12（managed）+ openpyxl + Pillow。
> 踩坑背景见 SKILL.md「硬约束」，这里只放能直接抄的代码。

## 1. 保存安全：含图片工作簿的大改动，先存临时路径

```python
# 永远不要对含图片的工作簿直接 wb.save(原文件)——写图片阶段一旦报错，原文件半写损坏且不可抢救
TMP = DST + ".saving.xlsx"
wb.save(TMP)
import os
with open(TMP, "rb") as f:
    data = f.read()
with open(DST, "wb") as f:
    f.write(data)
os.remove(TMP)
```

## 2. 加载态图片：字节预读 + 换新 BytesIO（保存前必做）

```python
import io
from PIL import Image as PILImage

for img in ws._images:
    ref = img.ref
    raw = ref.read() if hasattr(ref, "read") else open(ref, "rb").read()
    img.ref = io.BytesIO(raw)          # 换新流，原流可能已被消费关闭
    W, H = PILImage.open(io.BytesIO(raw)).size   # 用独立 BytesIO 读尺寸
```

更稳（绕开 ref 状态混乱）：直接从压缩包媒体重建 Image 对象——

```python
import zipfile
from openpyxl.drawing.image import Image as XImage

z = zipfile.ZipFile(src_xlsx)
# 截图页（sheet3）的 drawing 逐锚点取 r:embed 的 rId，按 rels 映射到 xl/media/imageN.png
media_bytes = [z.read(f"xl/media/{name}") for name in media_names]
imgs = [XImage(io.BytesIO(b)) for b in media_bytes]
```

## 3. 界面截图页等距重排（统一格式：说明行 + 1 空行 + 图 1500px + 2 空行）

```python
import math
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.xdr import XDRPositiveSize2D

EMU = 9525
ROW_PX = 20          # 全表统一行高 15pt = 20px
DISP_W = 1500        # 截图统一显示宽度 px
GAP_AFTER_IMG = 2

row = 3
for text, img, (W, H) in zip(captions, imgs, orig_sizes):
    cy_px = round(DISP_W * H / W)                 # 等比显示高度
    img.anchor = OneCellAnchor(
        _from=AnchorMarker(col=0, colOff=0, row=row, rowOff=0),  # 0 基：说明行的下一行
        ext=XDRPositiveSize2D(cx=DISP_W * EMU, cy=cy_px * EMU),
    )
    rows_for_img = math.ceil(cy_px / ROW_PX)      # 图占行数，保证下一块起始行可算
    c = ws.cell(row=row, column=1); c.value = text; 复制说明行样式(c)
    row += 2 + rows_for_img + GAP_AFTER_IMG       # 说明行占 2 行（含空行）
for r in range(1, row + 2):
    ws.row_dimensions[r].height = 15
ws.sheet_format.defaultRowHeight = 15
```

## 4. 横向条形图：条上自带「类型名 数量」+ 最严重在顶

```python
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList

new = BarChart()
new.type = "bar"; new.grouping = "clustered"
new.gapWidth = 60; new.legend = None
new.width, new.height = old.width, 9        # 原位复用旧图 anchor/width/height
data = Reference(st, min_col=2, min_row=2, max_row=13)   # 含表头行
cats = Reference(st, min_col=1, min_row=3, max_row=13)
new.add_data(data, titles_from_data=True); new.set_categories(cats)

dl = DataLabelList()
dl.showCatName = True; dl.showVal = True    # 标签长在条上，不依赖轴标签
dl.showSerName = dl.showLegendKey = dl.showPercent = False
dl.separator = "  "; dl.numFmt = "0"; dl.dLblPos = "outEnd"
new.dataLabels = dl

new.y_axis.number_format = "0"; new.y_axis.majorUnit = 1    # 整数刻度
new.x_axis.scaling.orientation = "maxMin"   # 类别反转：表首行（最大）在顶部
new.y_axis.crosses = "max"                  # 数值轴保持在底部
new.x_axis.tickLblSkip = new.x_axis.tickMarkSkip = 1
new.anchor = old.anchor
```

注意：`tickLblPos="none"` openpyxl 不序列化，保存后必须 zip 层补（见片段 6）。

## 5. 饼图：语义配色 + 右图例 + 外侧百分比

```python
from openpyxl.chart import PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.legend import Legend
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties

new = PieChart()
data = Reference(st, min_col=2, min_row=17, max_row=20)  # 含表头
cats = Reference(st, min_col=1, min_row=18, max_row=20)
new.add_data(data, titles_from_data=True); new.set_categories(cats)

colors = ["C00000", "ED7D31", "70AD47"]     # 高红 / 中橙 / 低绿
for i, c in enumerate(colors):
    dp = DataPoint(idx=i); dp.graphicalProperties = GraphicalProperties(solidFill=c)
    pts.append(dp)
new.series[0].data_points = pts

dl = DataLabelList()
dl.showPercent = True                       # 只留百分比——数值与占比共用 numFmt，同显必坏一个
dl.showVal = dl.showCatName = dl.showSerName = dl.showLegendKey = False
dl.numFmt = "0.0%"; dl.dLblPos = "outEnd"   # 外侧防遮挡
new.dataLabels = dl

lg = Legend(); lg.position = "r"; lg.overlay = False   # 类别名交给图例
new.legend = lg
```

## 6. recalc 后 zip 层补丁（每次 recalc 后必查必补）

LibreOffice 重算会：丢饼图 numFmt、把 catAx 的 tickLblPos 重置回 nextTo、把集合级 dLbls 改写成逐点 dLbl。

```python
import zipfile, os, re

def zip_patch(path, patches: dict):        # patches: {zip内路径: 新文本}
    tmp = path + ".tmp"
    zin = zipfile.ZipFile(path)
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    for item in zin.namelist():
        data = patches.get(item)
        data = data.encode("utf-8") if data else zin.read(item)
        zout.writestr(item, data)
    zin.close(); zout.close()
    with open(path, "wb") as f:             # os.replace 在预览锁下会 WinError 5，直接覆写可行
        f.write(open(tmp, "rb").read())
    os.remove(tmp)

z = zipfile.ZipFile(path)
pie_n = next(n for n in z.namelist() if n.startswith("xl/charts/chart") and "pieChart" in z.read(n).decode("utf-8"))
xml = z.read(pie_n).decode("utf-8")

# ① 逐点标签补 numFmt（LibreOffice 改写成 <dLbl><idx/> 后集合级 numFmt 丢失）
NF = '<c:numFmt formatCode="0.0%" sourceLinked="0"/>'
for i in range(3):
    old = f'<c:dLbl><c:idx val="{i}"/>'
    if old + "<c:numFmt" not in xml:
        xml = xml.replace(old, old + NF, 1)

# ② 柱状图 catAx 隐藏游离轴标签
xml_bar = z.read(bar_n).decode("utf-8")
blk = re.search(r"<c:catAx>.*?</c:catAx>", xml_bar, re.S).group(0)
xml_bar = xml_bar.replace(blk, blk.replace('<c:tickLblPos val="nextTo"/>', '<c:tickLblPos val="none"/>'))

zip_patch(path, {pie_n: xml, bar_n: xml_bar})
```

校验 XML 时**匹配字符串必须含空格**：`'<legendPos val="r" />'` 不是 `'<legendPos val="r"/>'`——先打印原文片段再写断言。

## 7. 核验显示尺寸（openpyxl 读回的是原生尺寸，不是显示尺寸）

```python
import zipfile, re
z = zipfile.ZipFile(path)
for n in z.namelist():
    if re.match(r"xl/drawings/drawing\d+\.xml", n):
        xml = z.read(n).decode("utf-8")
        for col, row, cx, cy in re.findall(
            r"<xdr:from><xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>.*?<xdr:ext cx=\"(\d+)\" cy=\"(\d+)\"", xml, re.S):
            print("row", int(row) + 1, "size px", int(cx) // 9525, int(cy) // 9525)
```

## 8. 清统计表旧区域（先 unmerge 再清值）

```python
for rng in [r for r in list(st.merged_cells.ranges) if r.min_row >= 3]:
    st.unmerge_cells(str(rng))
for row in st.iter_rows(min_row=3, max_row=20, min_col=1, max_col=3):
    for cell in row:
        cell.value = None
```

## 9. 统计表降序重排（公式引用本行 A 列，重写即可）

```python
from collections import Counter
cnt = Counter(明细 C 列类型值)
order = sorted(orig_types, key=lambda t: (-cnt[t], -orig.index(t)))  # 平手按原顺序逆序破
for i, t in enumerate(order):
    r = 3 + i
    st.cell(row=r, column=1).value = t
    st.cell(row=r, column=2).value = f"=COUNTIF(问题清单!$C$3:$C$19,A{r})"
    st.cell(row=r, column=3).value = f'=IF(OR(B{r}="",B{r}=0),"",B{r}/B$14)'
```
