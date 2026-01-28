#!/bin/bash
# USB HID Gadget配置脚本
# 将树莓派配置为USB HID键盘+鼠标设备
# 使用方法: sudo ./usb-gadget.sh

set -e  # 遇到错误立即退出（某些地方需要忽略错误）

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印函数
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

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  USB HID Gadget 配置脚本${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# 检查root权限
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "必须使用root权限运行此脚本"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 检查libcomposite模块
check_modules() {
    if [ ! -d "/sys/kernel/config/usb_gadget" ]; then
        print_error "/sys/kernel/config/usb_gadget 目录不存在"
        echo ""
        echo "可能的原因："
        echo "1. 未添加 dtoverlay=dwc2 到配置文件"
        echo "2. 未添加 libcomposite 到 /etc/modules"
        echo "3. 未重启树莓派"
        echo ""
        
        # 检查模块是否已加载
        if ! lsmod | grep -q libcomposite; then
            print_warning "libcomposite 模块未加载"
            read -p "是否尝试手动加载模块？(y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_info "正在加载模块..."
                modprobe libcomposite 2>/dev/null && print_success "libcomposite 模块加载成功" || print_warning "无法加载 libcomposite"
                modprobe dwc2 2>/dev/null && print_success "dwc2 模块加载成功" || print_warning "无法加载 dwc2"
                
                if [ ! -d "/sys/kernel/config/usb_gadget" ]; then
                    print_error "模块加载后仍然无法找到 /sys/kernel/config/usb_gadget"
                    echo "请检查配置并重启树莓派"
                    exit 1
                fi
            else
                print_error "请完成配置后重启树莓派，然后重新运行此脚本"
                exit 1
            fi
        else
            print_error "模块已加载但目录不存在，可能需要重启"
            exit 1
        fi
    fi
}

# 清理旧配置
cleanup_old_config() {
    if [ -d "/sys/kernel/config/usb_gadget/pi4" ]; then
        print_warning "检测到已存在的配置"
        if [ -f "/sys/kernel/config/usb_gadget/pi4/UDC" ] && [ -s "/sys/kernel/config/usb_gadget/pi4/UDC" ]; then
            print_info "正在禁用现有USB Gadget..."
            echo "" > /sys/kernel/config/usb_gadget/pi4/UDC 2>/dev/null || true
            sleep 1
        fi
        print_info "清理旧配置..."
        rm -rf /sys/kernel/config/usb_gadget/pi4
    fi
}

# 创建USB Gadget配置
create_gadget() {
    print_info "创建USB Gadget配置..."
    
    cd /sys/kernel/config/usb_gadget/ || {
        print_error "无法进入 /sys/kernel/config/usb_gadget/ 目录"
        exit 1
    }
    
    cleanup_old_config
    
    # 创建gadget目录
    mkdir -p pi4
    cd pi4 || {
        print_error "无法创建或进入 pi4 目录"
        exit 1
    }
    
    # USB设备描述符
    print_info "设置USB设备描述符..."
    echo 0x1d6b > idVendor      # Linux Foundation
    echo 0x0104 > idProduct    # Multifunction Composite Gadget
    echo 0x0100 > bcdDevice    # v1.0.0
    echo 0x0200 > bcdUSB       # USB2
    
    # 字符串描述符
    print_info "设置字符串描述符..."
    mkdir -p strings/0x409
    echo "fedcba9876543210" > strings/0x409/serialnumber
    echo "Raspberry Pi" > strings/0x409/manufacturer
    echo "USB HID Keyboard Mouse" > strings/0x409/product
    
    # 配置描述符
    print_info "设置配置描述符..."
    mkdir -p configs/c.1
    mkdir -p configs/c.1/strings/0x409
    echo "HID Keyboard + Mouse" > configs/c.1/strings/0x409/configuration
    echo 250 > configs/c.1/MaxPower
    
    # HID键盘功能
    print_info "配置键盘功能..."
    mkdir -p functions/hid.usb0
    echo 1 > functions/hid.usb0/protocol
    echo 1 > functions/hid.usb0/subclass
    echo 8 > functions/hid.usb0/report_length
    # USB HID键盘报告描述符
    echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc
    
    # 移除已存在的符号链接并创建新的
    rm -f configs/c.1/hid.usb0 2>/dev/null || true
    ln -sf functions/hid.usb0 configs/c.1/ || {
        print_error "无法创建键盘功能符号链接"
        exit 1
    }
    print_success "键盘功能配置完成"
    
    # HID鼠标功能
    print_info "配置鼠标功能..."
    mkdir -p functions/hid.usb1
    echo 2 > functions/hid.usb1/protocol
    echo 1 > functions/hid.usb1/subclass
    echo 5 > functions/hid.usb1/report_length
    # USB HID鼠标报告描述符
    echo -ne \\x05\\x01\\x09\\x02\\xa1\\x01\\x09\\x01\\xa1\\x00\\x05\\x09\\x19\\x01\\x29\\x05\\x15\\x00\\x25\\x01\\x95\\x05\\x75\\x01\\x81\\x02\\x95\\x01\\x75\\x03\\x81\\x03\\x05\\x01\\x09\\x30\\x09\\x31\\x15\\x81\\x25\\x7f\\x75\\x08\\x95\\x02\\x81\\x06\\x09\\x38\\x15\\x81\\x25\\x7f\\x75\\x08\\x95\\x01\\x81\\x06\\xc0\\xc0 > functions/hid.usb1/report_desc
    
    # 移除已存在的符号链接并创建新的
    rm -f configs/c.1/hid.usb1 2>/dev/null || true
    ln -sf functions/hid.usb1 configs/c.1/ || {
        print_error "无法创建鼠标功能符号链接"
        exit 1
    }
    print_success "鼠标功能配置完成"
}

# 启用USB Gadget
enable_gadget() {
    print_info "启用USB Gadget..."
    
    UDC=$(ls /sys/class/udc 2>/dev/null | head -n1)
    if [ -z "$UDC" ]; then
        print_error "未找到USB控制器"
        echo "请确保树莓派已通过USB连接到目标电脑"
        exit 1
    fi
    
    echo $UDC > UDC || {
        print_error "无法启用USB Gadget"
        exit 1
    }
    
    print_success "USB Gadget已启用"
    print_info "USB控制器: $UDC"
}

# 验证设备文件
verify_devices() {
    print_info "等待设备文件创建..."
    sleep 2
    
    # 检查设备文件
    if [ -e "/dev/hidg0" ] && [ -e "/dev/hidg1" ]; then
        print_success "设备文件已创建:"
        echo "  /dev/hidg0 (键盘)"
        echo "  /dev/hidg1 (鼠标)"
        return 0
    elif [ -e "/dev/hidg0" ]; then
        print_warning "只找到 /dev/hidg0，可能只有一个HID设备"
        return 1
    else
        print_warning "设备文件尚未创建，可能需要几秒钟"
        print_info "请稍后运行验证命令"
        return 1
    fi
}

# 主函数
main() {
    print_header
    
    # 检查root权限
    check_root
    
    # 检查模块
    check_modules
    
    # 创建配置
    create_gadget
    
    # 启用Gadget
    enable_gadget
    
    # 验证设备
    verify_devices
    
    echo ""
    print_success "USB HID Gadget配置完成！"
    echo ""
    print_info "验证命令:"
    echo "  find /dev -name 'hidg*'"
    echo "  [ -e /dev/hidg0 ] && echo '键盘设备存在'"
    echo "  [ -e /dev/hidg1 ] && echo '鼠标设备存在'"
    echo ""
    print_info "下一步: 连接树莓派到目标电脑的USB口（使用数据线）"
}

# 运行主函数
main
