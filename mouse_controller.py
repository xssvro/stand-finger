"""
鼠标控制模块 - USB HID协议
通过USB HID设备文件发送鼠标事件到被插入的电脑
"""
import struct
import time
from typing import Optional
import os
from logger import logger


class MouseController:
    """USB HID鼠标控制器"""
    
    # USB HID鼠标设备文件路径
    # 通常 /dev/hidg0 是键盘，/dev/hidg1 是鼠标
    # 如果只有一个HID设备，可能是 /dev/hidg0
    MOUSE_DEVICE_PATHS = ['/dev/hidg1', '/dev/hidg0']
    
    def __init__(self, device_path: Optional[str] = None):
        """初始化鼠标控制器
        
        Args:
            device_path: USB HID鼠标设备文件路径，如果为None则自动检测
        """
        self.device_path = device_path
        self.device_file = None
        self._open_device()
    
    def _open_device(self):
        """打开USB HID设备文件"""
        if self.device_path:
            paths_to_try = [self.device_path]
        else:
            paths_to_try = self.MOUSE_DEVICE_PATHS
        
        for path in paths_to_try:
            try:
                if os.path.exists(path):
                    self.device_file = open(path, 'wb')
                    self.device_path = path
                    logger.success(f"成功打开鼠标设备: {path}", category="MOUSE")
                    return
            except (PermissionError, IOError) as e:
                logger.warning(f"无法打开 {path}: {e}", category="MOUSE")
                continue
        
        raise RuntimeError(
            f"无法找到可用的USB HID鼠标设备。请确保：\n"
            f"1. 树莓派已配置为USB Gadget模式\n"
            f"2. 已加载libcomposite模块\n"
            f"3. 已创建HID功能\n"
            f"4. 使用root权限运行程序"
        )
    
    def _write_mouse_report(self, buttons: int = 0, x: int = 0, y: int = 0, wheel: int = 0):
        """写入鼠标HID报告
        
        USB HID鼠标报告格式（5字节）:
        Byte 0: 按钮状态 (bit 0=左键, bit 1=右键, bit 2=中键)
        Byte 1: X轴移动 (-127 到 127)
        Byte 2: Y轴移动 (-127 到 127)
        Byte 3: 滚轮 (-127 到 127)
        Byte 4: 保留（通常为0）
        
        Args:
            buttons: 按钮状态位掩码
            x: X轴相对移动量（-127到127）
            y: Y轴相对移动量（-127到127）
            wheel: 滚轮移动量（-127到127）
        """
        if not self.device_file:
            return
        
        # 限制移动范围
        x = max(-127, min(127, x))
        y = max(-127, min(127, y))
        wheel = max(-127, min(127, wheel))
        
        # 打包HID报告
        report = struct.pack('bbbb', buttons, x, y, wheel)
        
        try:
            self.device_file.write(report)
            self.device_file.flush()
        except IOError as e:
            raise RuntimeError(f"写入鼠标设备失败: {e}")
    
    def move_relative(self, dx: int, dy: int):
        """相对移动鼠标
        
        Args:
            dx: X方向移动距离（像素）
            dy: Y方向移动距离（像素）
        """
        # 如果移动距离超过127，需要分多次移动
        while dx != 0 or dy != 0:
            move_x = max(-127, min(127, dx))
            move_y = max(-127, min(127, dy))
            
            self._write_mouse_report(x=move_x, y=move_y)
            
            dx -= move_x
            dy -= move_y
            
            if dx != 0 or dy != 0:
                time.sleep(0.01)  # 短暂延迟，避免移动过快
    
    def move_to(self, x: int, y: int, duration: float = 0.1):
        """移动鼠标到指定位置（相对移动）
        
        注意：USB HID鼠标只能发送相对移动，无法获取绝对位置
        此函数将目标坐标视为相对移动量
        
        Args:
            x: 目标X坐标（作为相对移动量）
            y: 目标Y坐标（作为相对移动量）
            duration: 移动持续时间（秒）
        """
        # USB HID鼠标只能做相对移动
        # 这里将x, y作为相对移动量处理
        steps = max(1, int(duration * 100))
        step_x = x / steps
        step_y = y / steps
        
        for i in range(steps):
            self.move_relative(int(step_x), int(step_y))
            time.sleep(duration / steps)
    
    def click(self, button: str = 'left', count: int = 1):
        """点击鼠标
        
        Args:
            button: 按钮类型 ('left', 'right', 'middle')
            count: 点击次数
        """
        button_map = {
            'left': 1,      # bit 0
            'right': 2,     # bit 1
            'middle': 4     # bit 2
        }
        
        button_mask = button_map.get(button.lower(), 1)
        
        for _ in range(count):
            # 按下
            self._write_mouse_report(buttons=button_mask)
            time.sleep(0.01)
            # 释放
            self._write_mouse_report(buttons=0)
            if count > 1:
                time.sleep(0.1)
    
    def press(self, button: str = 'left'):
        """按下鼠标按钮"""
        button_map = {
            'left': 1,
            'right': 2,
            'middle': 4
        }
        button_mask = button_map.get(button.lower(), 1)
        self._write_mouse_report(buttons=button_mask)
    
    def release(self, button: str = 'left'):
        """释放鼠标按钮"""
        self._write_mouse_report(buttons=0)
    
    def scroll(self, dx: int, dy: int):
        """滚动鼠标滚轮
        
        Args:
            dx: 水平滚动距离
            dy: 垂直滚动距离（正数向上，负数向下）
        """
        self._write_mouse_report(wheel=dy)
        time.sleep(0.01)
        self._write_mouse_report(wheel=0)  # 停止滚动
    
    # 默认“居中”相对移动量（像素），用于 center()
    # USB HID 无法获取屏幕尺寸，这里是经验值，可通过 set_center_offset 修改
    DEFAULT_CENTER_OFFSET = (500, 500)
    DEFAULT_CENTER_BACK = (250, 250)

    def set_center_offset(self, move_x: int = 500, move_y: int = 500, back_x: int = 250, back_y: int = 250):
        """设置 center() 使用的相对移动量（根据目标屏幕尺寸调整）"""
        self._center_move = (move_x, move_y)
        self._center_back = (back_x, back_y)

    def center(self, move_x: Optional[int] = None, move_y: Optional[int] = None,
               back_x: Optional[int] = None, back_y: Optional[int] = None):
        """将鼠标向“中心”方向做相对移动
        
        USB HID 无法获取屏幕尺寸和当前坐标，只能做相对移动。
        这里先向右下移动 (move_x, move_y)，再向左上移动 (back_x, back_y)。
        默认值适合常见 1080p 屏幕，其他分辨率可传参或调用 set_center_offset。
        """
        default_move = getattr(self, '_center_move', self.DEFAULT_CENTER_OFFSET)
        default_back = getattr(self, '_center_back', self.DEFAULT_CENTER_BACK)
        mx = move_x if move_x is not None else default_move[0]
        my = move_y if move_y is not None else default_move[1]
        bx = back_x if back_x is not None else default_back[0]
        by = back_y if back_y is not None else default_back[1]
        self.move_relative(mx, my)
        time.sleep(0.1)
        self.move_relative(-bx, -by)
    
    def draw_circle(self, center_x: Optional[int] = None, 
                    center_y: Optional[int] = None, 
                    radius: int = 100, 
                    steps: int = 50,
                    duration: float = 2.0):
        """画一个圆
        
        注意：由于USB HID鼠标只能做相对移动，此函数以当前位置为圆心画圆
        
        Args:
            center_x: 忽略（USB HID鼠标无法获取绝对位置）
            center_y: 忽略（USB HID鼠标无法获取绝对位置）
            radius: 圆的半径（像素）
            steps: 画圆的步数（越多越平滑）
            duration: 画圆的总时间（秒）
        """
        import math
        
        step_duration = duration / steps
        
        for i in range(steps + 1):
            angle = 2 * math.pi * i / steps
            # 计算每一步的相对移动
            if i == 0:
                # 第一步：移动到起始位置（圆的最右侧）
                dx = int(radius * math.cos(angle))
                dy = int(radius * math.sin(angle))
            else:
                # 后续步骤：计算相对于上一步的移动
                prev_angle = 2 * math.pi * (i - 1) / steps
                prev_x = radius * math.cos(prev_angle)
                prev_y = radius * math.sin(prev_angle)
                curr_x = radius * math.cos(angle)
                curr_y = radius * math.sin(angle)
                dx = int(curr_x - prev_x)
                dy = int(curr_y - prev_y)
            
            self.move_relative(dx, dy)
            time.sleep(step_duration)

    def __del__(self):
        """清理资源"""
        if self.device_file:
            try:
                self.device_file.close()
            except:
                pass
