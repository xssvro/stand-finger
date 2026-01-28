"""
键盘控制模块
用于模拟键盘操作
"""
import time
try:
    from pynput.keyboard import Controller, Key
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("警告: pynput未安装，键盘控制功能将不可用")


class KeyboardController:
    """键盘控制器"""
    
    def __init__(self):
        """初始化键盘控制器"""
        if PYNPUT_AVAILABLE:
            self.keyboard = Controller()
        else:
            self.keyboard = None
            print("警告: 键盘控制器初始化失败")
    
    def type(self, text: str, interval: float = 0.05):
        """输入文本
        
        Args:
            text: 要输入的文本
            interval: 每个字符之间的间隔时间（秒）
        """
        if not self.keyboard:
            return
        
        for char in text:
            self.keyboard.type(char)
            time.sleep(interval)
    
    def press(self, key: str):
        """按下按键
        
        Args:
            key: 按键名称（如 'a', 'enter', 'space' 等）
        """
        if not self.keyboard:
            return
        
        try:
            # 尝试转换为特殊键
            key_obj = self._get_key(key)
            self.keyboard.press(key_obj)
        except (ValueError, AttributeError):
            # 如果是普通字符，直接输入
            self.keyboard.press(key)
    
    def release(self, key: str):
        """释放按键
        
        Args:
            key: 按键名称
        """
        if not self.keyboard:
            return
        
        try:
            key_obj = self._get_key(key)
            self.keyboard.release(key_obj)
        except (ValueError, AttributeError):
            self.keyboard.release(key)
    
    def tap(self, key: str):
        """点击按键（按下并释放）
        
        Args:
            key: 按键名称
        """
        if not self.keyboard:
            return
        
        try:
            key_obj = self._get_key(key)
            self.keyboard.press(key_obj)
            self.keyboard.release(key_obj)
        except (ValueError, AttributeError):
            self.keyboard.press(key)
            self.keyboard.release(key)
    
    def press_combination(self, *keys):
        """按下组合键
        
        Args:
            *keys: 按键列表，如 ('ctrl', 'c')
        """
        if not self.keyboard:
            return
        
        key_objs = []
        for key in keys:
            try:
                key_obj = self._get_key(key)
                key_objs.append(key_obj)
            except (ValueError, AttributeError):
                key_objs.append(key)
        
        # 按下所有键
        for key_obj in key_objs:
            self.keyboard.press(key_obj)
        
        # 释放所有键（逆序）
        for key_obj in reversed(key_objs):
            self.keyboard.release(key_obj)
    
    def _get_key(self, key_name: str):
        """将字符串转换为Key对象
        
        Args:
            key_name: 按键名称
        
        Returns:
            Key对象或字符串
        """
        key_map = {
            'alt': Key.alt,
            'alt_l': Key.alt_l,
            'alt_r': Key.alt_r,
            'alt_gr': Key.alt_gr,
            'backspace': Key.backspace,
            'caps_lock': Key.caps_lock,
            'cmd': Key.cmd,
            'cmd_l': Key.cmd_l,
            'cmd_r': Key.cmd_r,
            'ctrl': Key.ctrl,
            'ctrl_l': Key.ctrl_l,
            'ctrl_r': Key.ctrl_r,
            'delete': Key.delete,
            'down': Key.down,
            'end': Key.end,
            'enter': Key.enter,
            'esc': Key.esc,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12,
            'home': Key.home,
            'left': Key.left,
            'page_down': Key.page_down,
            'page_up': Key.page_up,
            'right': Key.right,
            'shift': Key.shift,
            'shift_l': Key.shift_l,
            'shift_r': Key.shift_r,
            'space': Key.space,
            'tab': Key.tab,
            'up': Key.up,
        }
        
        key_lower = key_name.lower()
        if key_lower in key_map:
            return key_map[key_lower]
        
        # 如果不在映射中，返回原字符串
        return key_name
