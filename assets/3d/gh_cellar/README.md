# 暗房 1926 · 千人千面

一个依据密室平面图与四张三维参考图重建的 **1920 年代伦敦地下摄影暗房**。场景完全在 Blender 中程序化建模，包含建筑结构、家具、暗房器物、材质、体积光与多机位电影感渲染。

![contact sheet](renders/contact_sheet.jpg)

## 项目文件

| 文件 | 内容 |
| --- | --- |
| `Darkroom_1926.blend` | 最终可编辑 Blender 场景（Blender 5.2.2 LTS，纹理已打包） |
| `renders/final/hero_wide.png` | 全景建立镜头，16 mm |
| `renders/final/table_hero.png` | 工作台主镜头，20.5 mm |
| `renders/final/center.png` | 正面肖像墙与工作台，30 mm |
| `renders/final/east_ladder.png` | 东侧木梯、储物箱与阁楼入口，24 mm |
| `renders/final/bench_detail.png` | 大画幅皮腔相机细节，54 mm |
| `renders/final/portraits.png` | 北墙肖像群，45 mm |
| `renders/final/plan_annotated.png` | 带尺寸与区域标注的俯视平面渲染 |
| `renders/contact_sheet.jpg` | 六张成片的总览联系表 |
| `renders/raw/` | 未调色的 Cycles 原始渲染 |
| `textures/` | 程序生成与参考图派生的贴图 |
| `build_scene.py` | 场景构建入口；`build_architecture.py` / `build_props.py` / `scene_lib.py` 为模块 |
| `render_final.py` | 最终机位与分辨率渲染脚本（原始帧输出到 `renders/raw/`） |
| `postprocess.py` | 电影感调色、辉光、暗角、颗粒与平面标注 |
| `finalize_blend.py` | 打包纹理并写入项目元信息 |
| `make_wood.py` / `make_textures.py` / `make_alt_portraits.py` | 程序纹理与肖像素材生成 |

## 空间与平面图对应

- 房间净尺寸：**10.0 m（东西）× 8.0 m（南北）× 2.6 m（净高）**
- 北墙（+Y）：肖像墙、长木画架、九幅老照片、窄搁板
- 西墙（−X）：暗房水槽柜、黄铜水龙头、药瓶、上层柜、围裙与工作外套、晾片绳
- 东墙（+X）：靠墙木梯与阁楼入口、储物木箱、工具挂杆、化学药品架
- 南墙（−Y）：厚重的暗房门、门缝暖光
- 中央：3.45 m 旧木工作台，主位大画幅皮腔相机、油灯、显影盘、相纸、底片、放大镜等
- 天花：旧木梁、铺板、中央天窗与东侧阁楼入口；天窗冷光与油灯暖光形成冷暖对照
- 地面：不规则青石板、灰缝、裂缝、水渍、干草、散落相纸与帆布

## 美术方向

- **时间与地点**：1926 年 10 月，伦敦某栋联排建筑的地下暗房；房间属于摄影师 J. Reynolds。
- **色彩**：以油灯的琥珀色为视觉中心，天窗的冷青蓝作为轮廓光；砖墙与旧木保持低饱和的红棕与灰褐。
- **光线**：天窗体积光 + 油灯实用光源 + 暗房红灯 + 门缝暖光；以大面积阴影保留密室压迫感。
- **材质**：砖墙逐块建模并做色差、缺砖与烟熏；旧木使用程序木纹与对象级随机偏移；金属分为黑铁、黄铜、氧化铜；玻璃区分窗玻璃、油灯玻璃、镜头玻璃与底片玻璃。
- **细节**：大画幅相机的皮腔由叠加式手风琴褶片、木质前后座与黄铜镜头组构成；暗房水槽为搪瓷盆与黄铜龙头；木梯、板条箱、绳索、灰尘、蛛网与纸屑均单独建模。

## 技术规格

- Blender **5.2.2 LTS**
- Cycles，OptiX GPU
- 成片 1920 × 1080，128–160 samples，OpenImageDenoise
- AgX · Medium High Contrast，后期再做胶片颗粒、辉光与暗角
- 平面图 1800 × 1440，64 samples
- 所有纹理已打包进 `.blend`；`textures/` 仍保留源文件，便于替换
- 肖像墙照片来自用户提供的参考图局部，经裁切、去色、做旧与颗粒处理，以避免引入外部版权素材

## 打开与复现

直接打开：

```powershell
& 'D:\blender\blender.exe' 'D:\千人千面blender\新建文件夹\Darkroom_1926.blend'
```

重新生成场景：

```powershell
& 'D:\blender\blender.exe' -b --factory-startup --python build_scene.py
```

重新渲染全部机位：

```powershell
& 'D:\blender\blender.exe' -b --factory-startup --python render_final.py
```

重新调色与生成联系表：

```powershell
& 'C:\Users\cong\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe' postprocess.py
```

## 机位

| 机位 | 位置 (m) | 镜头 | 用途 |
| --- | --- | --- | --- |
| Hero wide | (0.38, −3.28, 1.48) | 16 mm | 全景建立，展示完整平面关系 |
| Table hero | (−2.60, −1.06, 1.38) | 20.5 mm | 工作台与油灯主视觉 |
| Center | (−0.26, −2.72, 1.42) | 30 mm | 正面肖像墙与相机 |
| East ladder | (−1.70, −2.32, 1.45) | 24 mm | 木梯、阁楼入口与储物 |
| Bench detail | (−1.55, −1.35, 1.43) | 54 mm | 皮腔相机与桌面器物 |
| Portraits | (−0.10, −1.55, 1.56) | 45 mm | 北墙肖像群 |
| Plan | (0, 0, 8.5) ortho | — | 俯视平面记录 |

---

*“每一张脸都被时间显影过一次。”*
