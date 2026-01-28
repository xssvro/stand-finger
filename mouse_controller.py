"""
鼠标控制模块
用于模拟鼠标操作
"""
import math
import time
from typing import Tuple, Optional
try:
    from pynput.mouse import Controller, Button
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("警告: pynput未安装，鼠标控制功能将不可用")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("警告: pyautogui未安装，将使用默认屏幕尺寸")


class MouseController:
    """鼠标控制器"""
    
    def __init__(self):
        """初始化鼠标控制器"""
        if PYNPUT_AVAILABLE:
            self.mouse = Controller()
        else:
            self.mouse = None
            print("警告: 鼠标控制器初始化失败")
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        if self.mouse:
            return self.mouse.position
        return (0, 0)
    
    def move_to(self, x: int, y: int, duration: float = 0.1):
        """移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动持续时间（秒）
        """
        if not self.mouse:
            return
        
        current_pos = self.mouse.position
        steps = max(10, int(duration * 100))  # 至少10步
        
        for i in range(steps + 1):
            t = i / steps
            # 使用缓动函数使移动更平滑
            ease_t = t * t * (3 - 2 * t)  # smoothstep
            new_x = int(current_pos[0] + (x - current_pos[0]) * ease_t)
            new_y = int(current_pos[1] + (y - current_pos[1]) * ease_t)
            self.mouse.position = (new_x, new_y)
            time.sleep(duration / steps)
    
    def move_relative(self, dx: int, dy: int):
        """相对移动鼠标
        
        Args:
            dx: X方向移动距离
            dy: Y方向移动距离
        """
        if not self.mouse:
            return
        
        current_pos = self.mouse.position
        self.mouse.position = (current_pos[0] + dx, current_pos[1] + dy)
    
    def click(self, button: str = 'left', count: int = 1):
        """点击鼠标
        
        Args:
            button: 按钮类型 ('left', 'right', 'middle')
            count: 点击次数
        """
        if not self.mouse:
            return
        
        button_map = {
            'left': Button.left,
            'right': Button.right,
            'middle': Button.middle
        }
        
        btn = button_map.get(button.lower(), Button.left)
        for _ in range(count):
            self.mouse.click(btn)
            if count > 1:
                time.sleep(0.1)
    
    def press(self, button: str = 'left'):
        """按下鼠标按钮"""
        if not self.mouse:
            return
        
        button_map = {
            'left': Button.left,
            'right': Button.right,
            'middle': Button.middle
        }
        
        btn = button_map.get(button.lower(), Button.left)
        self.mouse.press(btn)
    
    def release(self, button: str = 'left'):
        """释放鼠标按钮"""
        if not self.mouse:
            return
        
        button_map = {
            'left': Button.left,
            'right': Button.right,
            'middle': Button.middle
        }
        
        btn = button_map.get(button.lower(), Button.left)
        self.mouse.release(btn)
    
    def scroll(self, dx: int, dy: int):
        """滚动鼠标滚轮
        
        Args:
            dx: 水平滚动距离
            dy: 垂直滚动距离
        """
        if not self.mouse:
            return
        
        self.mouse.scroll(dx, dy)
    
    def center(self):
        """将鼠标移动到屏幕中心"""
        if not self.mouse:
            return
        
        # 获取屏幕尺寸
        if PYAUTOGUI_AVAILABLE:
            screen_width, screen_height = pyautogui.size()
        else:
            # 默认值，如果pyautogui不可用
            screen_width = 1920
            screen_height = 1080
        
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        self.move_to(center_x, center_y)
    
    def draw_circle(self, center_x: Optional[int] = None, 
                    center_y: Optional[int] = None, 
                    radius: int = 100, 
                    steps: int = 50,
                    duration: float = 2.0):
        """画一个圆
        
        Args:
            center_x: 圆心X坐标，如果为None则使用当前鼠标位置
            center_y: 圆心Y坐标，如果为None则使用当前鼠标位置
            radius: 圆的半径（像素）
            steps: 画圆的步数（越多越平滑）
            duration: 画圆的总时间（秒）
        """
        if not self.mouse:
            return
        
        if center_x is None or center_y is None:
            current_pos = self.mouse.position
            center_x = center_x or current_pos[0]
            center_y = center_y or current_pos[1]
        
        # 移动到起始点（圆的最右侧）
        start_x = center_x + radius
        start_y = center_y
        self.move_to(start_x, start_y, duration=0.2)
        
        # 画圆
        step_duration = duration / steps
        for i in range(steps + 1):
            angle = 2 * math.pi * i / steps
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))
            self.mouse.position = (x, y)
            time.sleep(step_duration)
        
        # 回到起始点
        self.move_to(start_x, start_y, duration=0.1)
