#!/usr/bin/env python3
"""Monitor macOS USB enumeration, HID gamepads, and Godot controller input."""
import argparse
import datetime as dt
import json
import plistlib
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def usb_devices():
    result = subprocess.run(['ioreg', '-a', '-r', '-c', 'IOUSBHostDevice'], capture_output=True, check=True, timeout=8)
    found = {}
    def visit(nodes, parent='Mac'):
        for node in nodes:
            name = node.get('USB Product Name')
            branch = parent
            if name and 'idVendor' in node and 'idProduct' in node:
                location = f"{node.get('locationID', 0):08x}"
                ident = f"{node['idVendor']:04x}:{node['idProduct']:04x}@{location}"
                found[ident] = {'name': name, 'vendor': node.get('USB Vendor Name', ''), 'parent': parent}
                branch = parent + ' → ' + name
            visit(node.get('IORegistryEntryChildren', []), branch)
    visit(plistlib.loads(result.stdout))
    return found


def hid_gamepads():
    result = subprocess.run(['hidutil', 'list'], capture_output=True, text=True, check=True, timeout=8)
    found = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 7)
        if len(fields) < 8 or not fields[0].startswith('0x'):
            continue
        try:
            page, usage = int(fields[3], 0), int(fields[4], 0)
        except ValueError:
            continue
        # Generic Desktop: Joystick, Game Pad, Multi-axis Controller only.
        if page == 1 and usage in (4, 5, 8):
            found[fields[5]] = {'vendor': fields[0], 'product': fields[1], 'usage': usage, 'transport': fields[6], 'description': fields[7]}
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=0, help='Seconds to watch; 0 means until Ctrl+C.')
    parser.add_argument('--interval', type=float, default=1)
    parser.add_argument('--log', type=Path, default=Path.home() / 'Library/Logs/DigitalMedia/controller-watch.log')
    args = parser.parse_args()
    if args.interval < 0.2 or args.duration < 0:
        parser.error('interval must be >= 0.2 and duration >= 0')
    args.log.parent.mkdir(parents=True, exist_ok=True)
    stream = args.log.open('a', encoding='utf-8', buffering=1)
    def log(message):
        stamp = dt.datetime.now().astimezone().isoformat(timespec='seconds')
        line = f'[{stamp}] {message}'
        print(line, flush=True)
        stream.write(line + '\n')
    events = queue.Queue()
    process = None
    godot = shutil.which('godot')
    if godot:
        process = subprocess.Popen([godot, '--headless', '--path', str(ROOT / 'godot'), '--script', 'res://tools/watch_gamepad.gd'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        def read_engine():
            for line in process.stdout:
                events.put(line.rstrip())
        threading.Thread(target=read_engine, daemon=True).start()
    else:
        log('Godot 未找到；继续监听 USB / HID。')
    log('开始监听 USB / HID / Godot。可拔插手柄、按键或转动摇杆；Ctrl+C 停止。')
    previous = {}
    gamepads = None
    reported_exit = False
    deadline = time.monotonic() + args.duration if args.duration else float('inf')
    try:
        while time.monotonic() < deadline:
            for kind, read in [('USB', usb_devices), ('HID 手柄', hid_gamepads)]:
                try:
                    current = read()
                    if kind not in previous:
                        log(f'{kind} 初始数量：{len(current)}')
                    old = previous.get(kind, {})
                    for ident, data in current.items():
                        if old.get(ident) != data:
                            log(f'{kind} 已发现 {ident} {json.dumps(data, ensure_ascii=False)}')
                    for ident in old.keys() - current.keys():
                        log(f'{kind} 已移除 {ident} {json.dumps(old[ident], ensure_ascii=False)}')
                    previous[kind] = current
                except (subprocess.SubprocessError, ValueError, OSError) as error:
                    log(f'{kind} 查询失败：{error}')
            while not events.empty():
                line = events.get_nowait()
                if line.startswith('PADWATCH '):
                    record = json.loads(line[len('PADWATCH '):])
                    if record['kind'] == 'gamepads':
                        if record['devices'] != gamepads:
                            gamepads = record['devices']
                            log('Godot 手柄：' + json.dumps(gamepads, ensure_ascii=False))
                    else:
                        log('手柄输入：' + json.dumps(record, ensure_ascii=False))
                elif 'ERROR' in line or 'Error' in line:
                    log('Godot：' + line)
            if process and process.poll() is not None and not reported_exit:
                log(f'Godot 监听已退出，退出码 {process.returncode}；USB / HID 仍在监听。')
                reported_exit = True
            time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
    except KeyboardInterrupt:
        pass
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        log('监听结束。')
        stream.close()


if __name__ == '__main__':
    main()
