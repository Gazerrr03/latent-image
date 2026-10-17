# 第 6 章 · 专用肖像与显影预览

用户于 2026-10-14 选择：**制作专用对齐肖像，并在显影时淡出遮挡**。这套素材不替换人物的常态遮眼设计。

**格雷的展示限制**：常态画面与镜面不出现主角，手直到最后才入画。下列完整正脸与全身图是内部建模、骨相对齐和终局制作参考，不能用作普通对话头像或提前展示的照片；只有第 6 章叠印、第 7 章镜中揭示允许露脸。

## 已交付

- `portraits/`：六张专用无遮眼肖像源图。格雷和安布罗斯复用对应 V2 正脸；其余四人用内置 imagegen 单独生成。不是新的 3D 人物造型。
- `aligned/`：六张 1254×1254 对齐肖像，由预览的 Canvas 渲染导出，原始源图保留。
- `registration.json`、`landmarks.json`：眼睛、嘴、鼻与下颌的位置检测、二维配准参数及剩余偏差。眼线与嘴部配准，鼻和下颌并非逐像素相同。
- `preview.html`：离线可播放、可拖动进度、可检查单人的 12 秒显影预览，图片内嵌，无网络依赖。
- `review/composite-preview-v1.mp4`：12 秒视频预览；`review/frame-*.png` 为六个检查时刻。
- `final/composite.png`：最后清晰定格的格雷，1254×1254。

## 实际制作机制

0—3 秒影像浮出；3—6 秒各人的遮眼物淡出；6—10 秒将已对齐的六层面部轮廓收敛到共同底脸；10—12 秒保持清晰格雷。

**最后两秒来自格雷的正脸层。** 六张图自然平均仍会有少量重影，不能声称它们天然合成了逐像素相同的格雷；这里用明确的层透明度收敛完成用户选定的视觉演出。衣服与发型不参与最终面部身份判断。

常态设计中的缎带、布条、低帽檐、面纱继续保留。专用无遮眼图只供显影素材制作。安布罗斯的普通模型仍不涂白，照片涂白的原图仅提供显影初段的遮挡片段。

## 来源与复现

源图、提示词、参考图、哈希见 `manifest.json` 和 `prompts/`。不宣称 CC0；按图像平台适用条款使用，无外部第三方参考素材。

只读位置检测使用 macOS Vision，坐标按 [Apple 官方说明](https://developer.apple.com/documentation/vision/vnfacelandmarks2d) 转为图像坐标；原始像素没有被检测程序改写。

工具：

- `tools/art/face_landmarks.swift`：检测位置（macOS）。
- `tools/art/build_composite_preview.py`：以检测数据生成离线 Canvas 演出页，需要 NumPy。
- `tools/art/capture_composite_preview.js`：用 Playwright CLI 导出对齐画面、静帧和录像。
- 视频转 MP4 使用本机 ffmpeg。

静帧已交到 `godot/art/footage/composite.png`，可由当前 Godot `develop(composite.png)` 槽读取。动态版本目前是独立预览；Godot 的现有显影逻辑仍是六秒图片淡入，本轮未改游戏 UI 代码。图片候选交付、动态预览与游戏机位验收是三个不同状态。
