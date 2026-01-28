#!/bin/bash
# USB连接检查脚本
# 检查USB Gadget连接状态

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  [INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ [SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  [WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}❌ [ERROR]${NC} $1"
}

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  USB连接状态检查${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查1: USB控制器
print_info "检查USB控制器..."
UDC=$(ls /sys/class/udc 2>/dev/null | head -n1)
if [ -n "$UDC" ]; then
    print_success "找到USB控制器: $UDC"
else
    print_error "未找到USB控制器"
fi
echo ""

# 检查2: USB Gadget配置
print_info "检查USB Gadget配置..."
if [ -d "/sys/kernel/config/usb_gadget/pi4" ]; then
    print_success "USB Gadget配置存在"
    
    # 检查UDC状态
    if [ -f "/sys/kernel/config/usb_gadget/pi4/UDC" ]; then
        UDC_STATUS=$(cat /sys/kernel/config/usb_gadget/pi4/UDC 2>/dev/null || echo "")
        if [ -n "$UDC_STATUS" ] && [ "$UDC_STATUS" != "" ]; then
            print_success "USB Gadget已启用 (UDC: $UDC_STATUS)"
        else
            print_warning "USB Gadget未启用 (UDC为空)"
        fi
    fi
else
    print_error "USB Gadget配置不存在"
    echo "  请运行: sudo ./usb-gadget.sh"
fi
echo ""

# 检查3: HID设备文件
print_info "检查HID设备文件..."
if [ -e "/dev/hidg0" ]; then
    print_success "/dev/hidg0 存在 (键盘设备)"
    ls -l /dev/hidg0
else
    print_error "/dev/hidg0 不存在"
fi

if [ -e "/dev/hidg1" ]; then
    print_success "/dev/hidg1 存在 (鼠标设备)"
    ls -l /dev/hidg1
else
    print_error "/dev/hidg1 不存在"
fi
echo ""

# 检查4: USB连接状态（通过dmesg）
print_info "检查最近的USB连接事件..."
RECENT_USB=$(dmesg | tail -20 | grep -i "usb\|gadget\|hid" | tail -5)
if [ -n "$RECENT_USB" ]; then
    echo "$RECENT_USB"
else
    print_warning "未找到最近的USB事件"
fi
echo ""

# 检查5: USB设备列表（如果已连接）
print_info "检查USB设备..."
if command -v lsusb &> /dev/null; then
    USB_DEVICES=$(lsusb 2>/dev/null)
    if [ -n "$USB_DEVICES" ]; then
        echo "USB设备列表:"
        echo "$USB_DEVICES"
    else
        print_warning "lsusb命令不可用或未找到USB设备"
    fi
else
    print_warning "lsusb命令不可用"
fi
echo ""

# 总结
echo -e "${CYAN}========================================${NC}"
if [ -e "/dev/hidg0" ] && [ -e "/dev/hidg1" ]; then
    UDC_STATUS=$(cat /sys/kernel/config/usb_gadget/pi4/UDC 2>/dev/null || echo "")
    if [ -n "$UDC_STATUS" ]; then
        print_success "USB HID Gadget 配置正常！"
        print_info "设备应该可以在目标电脑上识别"
        echo ""
        print_info "在目标电脑上验证："
        echo "  Linux: lsusb | grep -i raspberry"
        echo "  Windows: 打开设备管理器查看"
    else
        print_warning "设备文件存在但UDC未启用"
        print_info "请运行: sudo ./usb-gadget.sh"
    fi
else
    print_error "USB HID设备未就绪"
    print_info "请检查："
    echo "  1. 是否运行了配置脚本: sudo ./usb-gadget.sh"
    echo "  2. 是否通过USB数据线连接到目标电脑"
    echo "  3. 是否使用了正确的USB口（数据口，不是电源口）"
fi
echo -e "${CYAN}========================================${NC}"
