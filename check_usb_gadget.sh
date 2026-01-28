#!/bin/bash
# USB HID Gadget 配置检查脚本
# 兼容 bash 和 zsh

# 如果是 zsh，设置选项以避免通配符错误
if [ -n "$ZSH_VERSION" ]; then
    setopt NULL_GLOB 2>/dev/null || true
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  USB HID Gadget 配置检查${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查1: 内核模块
echo -e "${BLUE}[1] 检查内核模块...${NC}"
if lsmod | grep -q libcomposite; then
    echo -e "${GREEN}✓ libcomposite 模块已加载${NC}"
else
    echo -e "${RED}✗ libcomposite 模块未加载${NC}"
    echo -e "${YELLOW}  尝试加载: sudo modprobe libcomposite${NC}"
fi

if lsmod | grep -q dwc2; then
    echo -e "${GREEN}✓ dwc2 模块已加载${NC}"
else
    echo -e "${RED}✗ dwc2 模块未加载${NC}"
    echo -e "${YELLOW}  尝试加载: sudo modprobe dwc2${NC}"
fi
echo ""

# 检查2: USB控制器
echo -e "${BLUE}[2] 检查USB控制器...${NC}"
UDC=$(ls /sys/class/udc 2>/dev/null | head -n1)
if [ -n "$UDC" ]; then
    echo -e "${GREEN}✓ 找到USB控制器: $UDC${NC}"
else
    echo -e "${RED}✗ 未找到USB控制器${NC}"
fi
echo ""

# 检查3: USB Gadget配置
echo -e "${BLUE}[3] 检查USB Gadget配置...${NC}"
if [ -d "/sys/kernel/config/usb_gadget/pi4" ]; then
    echo -e "${GREEN}✓ USB Gadget配置目录存在${NC}"
    
    # 检查UDC是否设置
    UDC_VALUE=$(cat /sys/kernel/config/usb_gadget/pi4/UDC 2>/dev/null)
    if [ -n "$UDC_VALUE" ]; then
        echo -e "${GREEN}✓ USB Gadget已启用 (UDC: $UDC_VALUE)${NC}"
    else
        echo -e "${YELLOW}⚠ USB Gadget未启用 (UDC为空)${NC}"
        if [ -n "$UDC" ]; then
            echo -e "${YELLOW}  可以运行: echo $UDC | sudo tee /sys/kernel/config/usb_gadget/pi4/UDC${NC}"
        fi
    fi
    
    # 检查HID功能
    if [ -d "/sys/kernel/config/usb_gadget/pi4/functions/hid.usb0" ]; then
        echo -e "${GREEN}✓ 键盘功能已配置${NC}"
    else
        echo -e "${RED}✗ 键盘功能未配置${NC}"
    fi
    
    if [ -d "/sys/kernel/config/usb_gadget/pi4/functions/hid.usb1" ]; then
        echo -e "${GREEN}✓ 鼠标功能已配置${NC}"
    else
        echo -e "${RED}✗ 鼠标功能未配置${NC}"
    fi
else
    echo -e "${RED}✗ USB Gadget配置目录不存在${NC}"
    echo -e "${YELLOW}  需要运行配置脚本: sudo /usr/local/bin/usb-gadget.sh${NC}"
fi
echo ""

# 检查4: 设备文件
echo -e "${BLUE}[4] 检查设备文件...${NC}"
if [ -e "/dev/hidg0" ]; then
    echo -e "${GREEN}✓ /dev/hidg0 存在 (键盘设备)${NC}"
    ls -l /dev/hidg0
else
    echo -e "${RED}✗ /dev/hidg0 不存在${NC}"
fi

if [ -e "/dev/hidg1" ]; then
    echo -e "${GREEN}✓ /dev/hidg1 存在 (鼠标设备)${NC}"
    ls -l /dev/hidg1
else
    echo -e "${RED}✗ /dev/hidg1 不存在${NC}"
fi
echo ""

# 检查5: 配置文件
echo -e "${BLUE}[5] 检查配置文件...${NC}"
if [ -f "/boot/firmware/config.txt" ]; then
    if grep -q "dtoverlay=dwc2" /boot/firmware/config.txt; then
        echo -e "${GREEN}✓ /boot/firmware/config.txt 包含 dtoverlay=dwc2${NC}"
    else
        echo -e "${YELLOW}⚠ /boot/firmware/config.txt 未包含 dtoverlay=dwc2${NC}"
    fi
elif [ -f "/boot/config.txt" ]; then
    if grep -q "dtoverlay=dwc2" /boot/config.txt; then
        echo -e "${GREEN}✓ /boot/config.txt 包含 dtoverlay=dwc2${NC}"
    else
        echo -e "${YELLOW}⚠ /boot/config.txt 未包含 dtoverlay=dwc2${NC}"
    fi
else
    echo -e "${RED}✗ 未找到config.txt文件${NC}"
fi

if [ -f "/etc/modules" ]; then
    if grep -q "libcomposite" /etc/modules && grep -q "dwc2" /etc/modules; then
        echo -e "${GREEN}✓ /etc/modules 包含所需模块${NC}"
    else
        echo -e "${YELLOW}⚠ /etc/modules 未包含所需模块${NC}"
    fi
fi
echo ""

# 总结
echo -e "${CYAN}========================================${NC}"
if [ -e "/dev/hidg0" ] && [ -e "/dev/hidg1" ]; then
    echo -e "${GREEN}✓ USB HID Gadget 配置正常！${NC}"
    echo -e "${GREEN}  可以开始使用服务了${NC}"
else
    echo -e "${RED}✗ USB HID Gadget 配置不完整${NC}"
    echo -e "${YELLOW}  请按照上述检查结果进行修复${NC}"
    echo ""
    echo -e "${YELLOW}快速修复步骤：${NC}"
    echo -e "  1. 确保已添加 dtoverlay=dwc2 到 config.txt"
    echo -e "  2. 确保已添加模块到 /etc/modules"
    echo -e "  3. 重启树莓派"
    echo -e "  4. 运行配置脚本: sudo /usr/local/bin/usb-gadget.sh"
fi
echo -e "${CYAN}========================================${NC}"
