#!/bin/bash
# 启动键盘鼠标模拟服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 打印带颜色的消息函数
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
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo -e "${CYAN}${BOLD}  USB HID 键盘鼠标模拟服务${NC}"
    echo -e "${CYAN}${BOLD}========================================${NC}"
}

print_header
print_info "正在启动服务..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    print_error "未找到Python3，请先安装Python3"
    exit 1
fi
print_success "Python3 已安装"

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    print_info "创建虚拟环境..."
    python3 -m venv venv
    print_success "虚拟环境创建完成"
else
    print_success "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
print_info "检查并安装依赖..."
pip install -q -r requirements.txt
print_success "依赖安装完成"

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then 
    print_error "必须使用root权限运行（sudo）"
    echo -e "${YELLOW}请使用: ${BOLD}sudo ./start.sh${NC}"
    exit 1
fi
print_success "权限检查通过（root）"

# 检查USB HID设备是否存在
if [ ! -e "/dev/hidg0" ] && [ ! -e "/dev/hidg1" ]; then
    print_warning "未找到USB HID设备 (/dev/hidg0 或 /dev/hidg1)"
    print_warning "请确保已配置USB HID Gadget模式（参考 USB_HID_SETUP.md）"
    print_info "继续运行..."
else
    print_success "USB HID设备已就绪"
fi

# 启动服务
echo ""
print_success "启动服务..."
echo ""
python3 main.py
