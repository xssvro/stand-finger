"""
键盘控制模块 - USB HID协议
通过USB HID设备文件发送键盘事件到被插入的电脑
"""
import os
import struct
import time
from typing import List, Optional
from logger import logger


class KeyboardController:
    """USB HID键盘控制器"""
    
    # USB HID键盘设备文件路径
    KEYBOARD_DEVICE_PATHS = ['/dev/hidg0', '/dev/hidg1']
    
    # USB HID键盘按键码映射
    # 参考: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
    KEY_CODES = {
        'a': 4, 'b': 5, 'c': 6, 'd': 7, 'e': 8, 'f': 9, 'g': 10, 'h': 11,
        'i': 12, 'j': 13, 'k': 14, 'l': 15, 'm': 16, 'n': 17, 'o': 18, 'p': 19,
        'q': 20, 'r': 21, 's': 22, 't': 23, 'u': 24, 'v': 25, 'w': 26, 'x': 27,
        'y': 28, 'z': 29,
        '1': 30, '2': 31, '3': 32, '4': 33, '5': 34, '6': 35, '7': 36, '8': 37,
        '9': 38, '0': 39,
        'enter': 40, 'esc': 41, 'backspace': 42, 'tab': 43, 'space': 44,
        '-': 45, '=': 46, '[': 47, ']': 48, '\\': 49, ';': 51, "'": 52, '`': 53,
        ',': 54, '.': 55, '/': 56,
        'caps_lock': 57,
        'f1': 58, 'f2': 59, 'f3': 60, 'f4': 61, 'f5': 62, 'f6': 63,
        'f7': 64, 'f8': 65, 'f9': 66, 'f10': 67, 'f11': 68, 'f12': 69,
        'insert': 73, 'home': 74, 'page_up': 75, 'delete': 76, 'end': 77,
        'page_down': 78,
        'right': 79, 'left': 80, 'down': 81, 'up': 82,
        'num_lock': 83,
        'keypad_/': 84, 'keypad_*': 85, 'keypad_-': 86, 'keypad_+': 87,
        'keypad_enter': 88, 'keypad_1': 89, 'keypad_2': 90, 'keypad_3': 91,
        'keypad_4': 92, 'keypad_5': 93, 'keypad_6': 94, 'keypad_7': 95,
        'keypad_8': 96, 'keypad_9': 97, 'keypad_0': 98, 'keypad_.': 99,
    }
    
    # 修饰键（Modifier keys）
    MODIFIER_KEYS = {
        'ctrl': 1,      # Left Control
        'shift': 2,     # Left Shift
        'alt': 4,       # Left Alt
        'gui': 8,       # Left GUI (Windows key)
        'ctrl_r': 16,   # Right Control
        'shift_r': 32,  # Right Shift
        'alt_r': 64,    # Right Alt
        'gui_r': 128,   # Right GUI
    }
    
    def __init__(self, device_path: Optional[str] = None):
        """初始化键盘控制器
        
        Args:
            device_path: USB HID键盘设备文件路径，如果为None则自动检测
        """
        self.device_path = device_path
        self.device_file = None
        self._open_device()
    
    def _open_device(self):
        """打开USB HID设备文件"""
        if self.device_path:
            paths_to_try = [self.device_path]
        else:
            paths_to_try = self.KEYBOARD_DEVICE_PATHS
        
        for path in paths_to_try:
            try:
                if os.path.exists(path):
                    self.device_file = open(path, 'wb')
                    self.device_path = path
                    logger.success(f"成功打开键盘设备: {path}", category="KEYBOARD")
                    return
            except (PermissionError, IOError) as e:
                logger.warning(f"无法打开 {path}: {e}", category="KEYBOARD")
                continue
        
        raise RuntimeError(
            f"无法找到可用的USB HID键盘设备。请确保：\n"
            f"1. 树莓派已配置为USB Gadget模式\n"
            f"2. 已加载libcomposite模块\n"
            f"3. 已创建HID功能\n"
            f"4. 使用root权限运行程序"
        )
    
    def _write_keyboard_report(self, modifiers: int = 0, keys: List[int] = None):
        """写入键盘HID报告
        
        USB HID键盘报告格式（8字节）:
        Byte 0: 修饰键位掩码 (Ctrl, Shift, Alt, GUI)
        Byte 1: 保留
        Byte 2-7: 按键码（最多6个按键同时按下）
        
        Args:
            modifiers: 修饰键位掩码
            keys: 按键码列表（最多6个）
        """
        if not self.device_file:
            return
        
        if keys is None:
            keys = []
        
        # 限制按键数量
        keys = keys[:6]
        
        # 填充到6个按键
        while len(keys) < 6:
            keys.append(0)
        
        # 打包HID报告
        report = struct.pack('BBBBBBBB', modifiers, 0, *keys)
        
        try:
            self.device_file.write(report)
            self.device_file.flush()
        except IOError as e:
            raise RuntimeError(f"写入键盘设备失败: {e}")
    
    def _get_key_code(self, key: str) -> tuple:
        """获取按键码和修饰键
        
        Returns:
            (key_code, modifier): 按键码和修饰键位掩码
        """
        key_lower = key.lower()
        
        # 检查是否是修饰键
        if key_lower in self.MODIFIER_KEYS:
            return (0, self.MODIFIER_KEYS[key_lower])
        
        # 检查是否是普通按键
        if key_lower in self.KEY_CODES:
            return (self.KEY_CODES[key_lower], 0)
        
        # 如果是单个字符，尝试转换
        if len(key) == 1:
            char = key.lower()
            if char in self.KEY_CODES:
                return (self.KEY_CODES[char], 0)
        
        raise ValueError(f"未知按键: {key}")
    
    def press(self, key: str):
        """按下按键
        
        Args:
            key: 按键名称（如 'a', 'enter', 'ctrl' 等）
        """
        key_code, modifier = self._get_key_code(key)
        
        if modifier:
            # 如果是修饰键，只设置修饰键位
            self._write_keyboard_report(modifiers=modifier)
        else:
            # 普通按键
            self._write_keyboard_report(keys=[key_code])
    
    def release(self, key: str):
        """释放按键"""
        self._write_keyboard_report(modifiers=0, keys=[0])
    
    def tap(self, key: str):
        """点击按键（按下并释放）
        
        Args:
            key: 按键名称
        """
        self.press(key)
        time.sleep(0.01)
        self.release(key)
    
    def press_combination(self, *keys):
        """按下组合键
        
        Args:
            *keys: 按键列表，如 ('ctrl', 'c')
        """
        modifiers = 0
        key_codes = []
        
        for key in keys:
            key_code, modifier = self._get_key_code(key)
            if modifier:
                modifiers |= modifier
            else:
                key_codes.append(key_code)
        
        self._write_keyboard_report(modifiers=modifiers, keys=key_codes)
        time.sleep(0.01)
        self._write_keyboard_report(modifiers=0, keys=[0])
    
    def type(self, text: str, interval: float = 0.05):
        """输入文本
        
        Args:
            text: 要输入的文本
            interval: 每个字符之间的间隔时间（秒）
        """
        for char in text:
            if char == ' ':
                self.tap('space')
            elif char == '\n':
                self.tap('enter')
            elif char.isupper():
                # 大写字母：按下Shift + 小写字母
                self.press('shift')
                self.tap(char.lower())
                self.release('shift')
            elif char in self.KEY_CODES:
                self.tap(char)
            else:
                # 特殊字符可能需要Shift，这里简化处理
                self.tap(char)
            
            time.sleep(interval)
    
    def __del__(self):
        """清理资源"""
        if self.device_file:
            try:
                self._write_keyboard_report(modifiers=0, keys=[0])
                self.device_file.close()
            except:
                pass
