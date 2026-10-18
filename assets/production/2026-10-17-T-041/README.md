# T-041 两间卧室设计包

打开 `index.html` 逐张审查效果图、平面图与已知偏差。交付状态为候选设计待用户审查。

正式文件按任务书放在：

- `assets/2d/T-041-主人的卧室兼书房/`
- `assets/2d/T-041-女主人的卧室/`

每间有 5 张 v3 PNG、平面布置图 SVG/PNG/PDF、实际提示词、物件清单与来源说明。`review/iterations/` 留存首轮图。生成原件继续保留在 `.codex/generated_images/`，路径与哈希见清单。

## 尺寸与布置

平面图为真实 1:50，A3 PDF 按 100% 打印；PNG 为 3360×2376。开口从 T-039 v1 二楼 SVG 独立解析核对，6 处开口的坐标误差为 0。通道用直径 0.60 m 圆盘在 0.01 m 网格上检查，门扇扫掠区不放家具。检查限于二维设计，不替代 Godot 实机通行。

女主人梳妆台北移 0.55 m，软凳收进台下，为床西到梳妆台保留通道。所有具体坐标见 layout.json 与两份物件清单。生成透视图只作陈设、气氛、道具形态参考，精确尺寸按矢量图。

## 文件

- `manifest.json`：选用效果图的原生/导出尺寸、SHA-256、生成原件路径、逐图状态，以及平面图文件校验。
- `generation-log.json`：首轮和选用图的实际提示词、原件路径、参考路径。
- `jobs.json`：初始 10 条任务提示词；发生修订时，以 generation-log 与设计包 prompts 下实际选用提示词为准。
- `visual-review.json`、`审查说明.md`：人工视觉检查记录与剩余偏差。
- `layout-check.json`：开口、门扇与通行检查。

## 重建设计图与审查入口

从项目根目录运行（重建平面图和复制已有生成图，不会发起新的生图调用）：

```sh
python3 tools/art/build_t041_package.py
python3 tools/art/render_t041_package.py
python3 tools/art/copy_t041_images.py
python3 tools/art/review_t041_package.py
```

需要 Pillow、Playwright、PyMuPDF 与本机 Google Chrome。原件被移动或删除时，复制与哈希校验会报错；不要以新图悄悄替换同一个生成记录。
