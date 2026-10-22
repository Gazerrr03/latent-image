# 手柄连接诊断（macOS）

在项目根目录运行：

```sh
python3 tools/diagnostics/controller_watch.py
```

每秒检查 USB 设备树、HID 手柄设备；同时启动独立 Godot 诊断进程，记录它识别到的手柄和按键、摇杆变化。只在设备状态变化时输出，摇杆变化作了阈值过滤；不记录键盘按键。Godot 诊断入口不加载主场景，也不读写玩家存档。

默认日志：`~/Library/Logs/DigitalMedia/controller-watch.log`。Ctrl+C 结束监听并清理子进程。`--duration 1800` 可限定为 30 分钟；`--interval 1` 设置检查间隔，`--log /tmp/controller.log` 可指定日志路径。找不到 Godot 时仍监听 USB / HID，并明确提示。

判断方法：

- 只有 USB Hub：系统能看到拓展坞，还没看到手柄通过它枚举为 USB 设备；需要通过拔插确认是否有变化。
- USB 新增设备，但 HID / Godot 没有：物理数据连接已建立，手柄模式、驱动或设备支持仍需检查。
- Godot 显示手柄名称：引擎已经识别；再按键、转摇杆，确认有输入事件。

本程序的初始实机检查已覆盖 USB / HID 查询、Godot 启动及限时退出。实体手柄插拔及按键事件需在设备实际连接后验证。
