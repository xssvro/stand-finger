"""
彩色日志工具模块
提供美观的、分类清晰的日志输出
"""
import sys
from datetime import datetime
from enum import Enum

try:
    from colorama import Fore, Back, Style, init
    COLORAMA_AVAILABLE = True
    init(autoreset=True)  # 自动重置颜色
except ImportError:
    COLORAMA_AVAILABLE = False
    # 定义空的颜色类，避免错误
    class Fore:
        BLACK = ''
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        RESET = ''
    
    class Style:
        BRIGHT = ''
        DIM = ''
        RESET_ALL = ''


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ColoredLogger:
    """彩色日志记录器"""
    
    # 日志级别颜色映射
    LEVEL_COLORS = {
        LogLevel.DEBUG: Fore.CYAN,
        LogLevel.INFO: Fore.BLUE,
        LogLevel.SUCCESS: Fore.GREEN,
        LogLevel.WARNING: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
        LogLevel.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    
    # 日志级别图标
    LEVEL_ICONS = {
        LogLevel.DEBUG: "🔍",
        LogLevel.INFO: "ℹ️",
        LogLevel.SUCCESS: "✅",
        LogLevel.WARNING: "⚠️",
        LogLevel.ERROR: "❌",
        LogLevel.CRITICAL: "🚨",
    }
    
    # 分类颜色映射
    CATEGORY_COLORS = {
        'MOUSE': Fore.MAGENTA,
        'KEYBOARD': Fore.CYAN,
        'API': Fore.BLUE,
        'SYSTEM': Fore.YELLOW,
        'USB': Fore.GREEN,
        'NETWORK': Fore.CYAN,
        'DEFAULT': Fore.WHITE,
    }
    
    def __init__(self, name: str = "HID"):
        """初始化日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.name = name
        self.enabled = True
    
    def _format_message(self, level: LogLevel, category: str, message: str) -> str:
        """格式化日志消息
        
        Args:
            level: 日志级别
            category: 日志分类
            message: 日志消息
        
        Returns:
            格式化后的日志字符串
        """
        if not COLORAMA_AVAILABLE:
            # 如果没有colorama，返回简单格式
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"[{timestamp}] [{level.value}] [{category}] {message}"
        
        # 获取颜色
        level_color = self.LEVEL_COLORS.get(level, Fore.WHITE)
        category_color = self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS['DEFAULT'])
        icon = self.LEVEL_ICONS.get(level, "")
        
        # 格式化时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建日志消息
        parts = [
            f"{Fore.WHITE}{Style.DIM}[{timestamp}]{Style.RESET_ALL}",
            f"{level_color}{Style.BRIGHT}[{level.value}]{Style.RESET_ALL}",
            f"{category_color}[{category}]{Style.RESET_ALL}",
            f"{icon} {message}"
        ]
        
        return " ".join(parts)
    
    def debug(self, message: str, category: str = "DEFAULT"):
        """调试日志"""
        if self.enabled:
            print(self._format_message(LogLevel.DEBUG, category, message))
    
    def info(self, message: str, category: str = "SYSTEM"):
        """信息日志"""
        if self.enabled:
            print(self._format_message(LogLevel.INFO, category, message))
    
    def success(self, message: str, category: str = "SYSTEM"):
        """成功日志"""
        if self.enabled:
            print(self._format_message(LogLevel.SUCCESS, category, message))
    
    def warning(self, message: str, category: str = "SYSTEM"):
        """警告日志"""
        if self.enabled:
            print(self._format_message(LogLevel.WARNING, category, message), file=sys.stderr)
    
    def error(self, message: str, category: str = "SYSTEM"):
        """错误日志"""
        if self.enabled:
            print(self._format_message(LogLevel.ERROR, category, message), file=sys.stderr)
    
    def critical(self, message: str, category: str = "SYSTEM"):
        """严重错误日志"""
        if self.enabled:
            print(self._format_message(LogLevel.CRITICAL, category, message), file=sys.stderr)
    
    def separator(self, char: str = "=", length: int = 60):
        """打印分隔线"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.WHITE}{Style.DIM}{char * length}{Style.RESET_ALL}")
        else:
            print(char * length)
    
    def banner(self, title: str):
        """打印横幅"""
        self.separator()
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}{' ' * 15}{title}{Style.RESET_ALL}")
        else:
            print(f"{' ' * 15}{title}")
        self.separator()


# 创建全局日志实例
logger = ColoredLogger("HID")

# 便捷函数
def debug(msg: str, category: str = "DEFAULT"):
    """调试日志"""
    logger.debug(msg, category)

def info(msg: str, category: str = "SYSTEM"):
    """信息日志"""
    logger.info(msg, category)

def success(msg: str, category: str = "SYSTEM"):
    """成功日志"""
    logger.success(msg, category)

def warning(msg: str, category: str = "SYSTEM"):
    """警告日志"""
    logger.warning(msg, category)

def error(msg: str, category: str = "SYSTEM"):
    """错误日志"""
    logger.error(msg, category)

def critical(msg: str, category: str = "SYSTEM"):
    """严重错误日志"""
    logger.critical(msg, category)
