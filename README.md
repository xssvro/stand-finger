# 树莓派USB HID键盘鼠标模拟服务

## 项目简介

树莓派通过USB连接到目标电脑，作为USB HID设备（键盘+鼠标），接收网络命令后通过USB HID协议控制目标电脑。

## 一、设置树莓派

### 1. 编辑配置文件

**⚠️ 在树莓派上执行（通过SSH）**

根据Raspberry Pi OS版本，配置文件位置不同：
- **Bookworm (较新版本)**：`/boot/firmware/config.txt`
- **Bullseye及更早版本**：`/boot/config.txt`

```bash
# 自动检测并编辑配置文件
if [ -f /boot/firmware/config.txt ]; then
    sudo nano /boot/firmware/config.txt  # Bookworm
else
    sudo nano /boot/config.txt           # Bullseye及更早
fi
# 在文件末尾添加：dtoverlay=dwc2

# 编辑 /etc/modules
sudo nano /etc/modules
# 添加以下内容：
# dwc2
# libcomposite
```

### 2. 重启树莓派（必须）

```bash
sudo reboot
```

**⚠️ 重要**：修改配置文件后必须重启才能生效。

### 3. 创建并运行配置脚本

重启后，重新SSH连接到树莓派：

**方式1：使用项目中的脚本（推荐）**

```bash
# 将脚本复制到系统目录
sudo cp usb-gadget.sh /usr/local/bin/usb-gadget.sh
sudo chmod +x /usr/local/bin/usb-gadget.sh

# 运行脚本
sudo /usr/local/bin/usb-gadget.sh
```

**方式2：手动创建脚本**

```bash
# 创建配置脚本
sudo nano /usr/local/bin/usb-gadget.sh
```

复制以下内容：

```bash
#!/bin/bash
cd /sys/kernel/config/usb_gadget/

# 如果已存在配置，先清理
if [ -d "pi4" ]; then
    if [ -f "pi4/UDC" ] && [ -s "pi4/UDC" ]; then
        echo "" > pi4/UDC 2>/dev/null || true
        sleep 1
    fi
    rm -rf pi4
fi

mkdir -p pi4
cd pi4

# USB设备描述符
echo 0x1d6b > idVendor
echo 0x0104 > idProduct
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

# 字符串描述符
mkdir -p strings/0x409
echo "fedcba9876543210" > strings/0x409/serialnumber
echo "Raspberry Pi" > strings/0x409/manufacturer
echo "USB HID Keyboard Mouse" > strings/0x409/product

# 配置描述符
mkdir -p configs/c.1
mkdir -p configs/c.1/strings/0x409
echo "HID Keyboard + Mouse" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# HID键盘功能
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc
rm -f configs/c.1/hid.usb0 2>/dev/null || true
ln -sf functions/hid.usb0 configs/c.1/

# HID鼠标功能
mkdir -p functions/hid.usb1
echo 2 > functions/hid.usb1/protocol
echo 1 > functions/hid.usb1/subclass
echo 5 > functions/hid.usb1/report_length
echo -ne \\x05\\x01\\x09\\x02\\xa1\\x01\\x09\\x01\\xa1\\x00\\x05\\x09\\x19\\x01\\x29\\x05\\x15\\x00\\x25\\x01\\x95\\x05\\x75\\x01\\x81\\x02\\x95\\x01\\x75\\x03\\x81\\x03\\x05\\x01\\x09\\x30\\x09\\x31\\x15\\x81\\x25\\x7f\\x75\\x08\\x95\\x02\\x81\\x06\\x09\\x38\\x15\\x81\\x25\\x7f\\x75\\x08\\x95\\x01\\x81\\x06\\xc0\\xc0 > functions/hid.usb1/report_desc
rm -f configs/c.1/hid.usb1 2>/dev/null || true
ln -sf functions/hid.usb1 configs/c.1/

# 启用USB Gadget
UDC=$(ls /sys/class/udc | head -n1)
echo $UDC > UDC

echo "✓ USB Gadget配置成功！"
```

使脚本可执行并运行：

```bash
sudo chmod +x /usr/local/bin/usb-gadget.sh
sudo /usr/local/bin/usb-gadget.sh
```

### 4. 验证配置

```bash
# 检查设备文件（在树莓派上）
find /dev -name "hidg*"
# 或
[ -e /dev/hidg0 ] && echo "✓ 键盘设备存在" || echo "✗ 未找到键盘设备"
[ -e /dev/hidg1 ] && echo "✓ 鼠标设备存在" || echo "✗ 未找到鼠标设备"
```

应该看到 `/dev/hidg0` 和 `/dev/hidg1`。

## 二、连接设备到电脑

### ⚠️ 重要：树莓派Zero的USB接口

树莓派Zero有两个Micro USB接口：

1. **USB数据口**（靠近HDMI接口）
   - ✅ **必须使用这个接口**
   - 用于USB数据传输
   - 连接到目标电脑的USB口

2. **电源接口**（靠近SD卡槽）
   - ❌ **不能使用**
   - 只能供电，不能传输数据

### 连接步骤

```
树莓派Zero                   目标电脑
┌─────────────┐              ┌─────────────┐
│             │              │             │
│  USB数据口  │ ───数据线───> │   USB口     │
│  (靠近HDMI) │              │             │
└─────────────┘              └─────────────┘
```

1. 使用**USB数据线**（不是充电线）
2. 连接到树莓派的**USB数据口**（靠近HDMI）
3. 另一端连接到目标电脑的USB口
4. 树莓派会从电脑获取电源（通常不需要单独供电）

### 验证连接

在**目标电脑**上验证：

**Linux**：
```bash
lsusb | grep -i "raspberry\|hid"
```

**Windows**：
- 打开"设备管理器"
- 应该看到"Raspberry Pi USB HID Keyboard Mouse"

## 三、服务使用

### 安装依赖

在树莓派上：

```bash
pip install -r requirements.txt
```

### 启动服务

**⚠️ 必须使用root权限运行**：

```bash
# 方式1：使用启动脚本（推荐）
sudo ./start.sh

# 方式2：直接运行
sudo python3 main.py
```

服务默认运行在 `http://0.0.0.0:5000`

### 获取树莓派IP地址

在树莓派上：

```bash
hostname -I
```

### API接口

假设树莓派IP为 `192.168.1.100`：

**健康检查**：
```bash
curl http://192.168.1.100:5000/health
```

**测试画圆**：
```bash
curl -X POST http://192.168.1.100:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{"radius": 100, "duration": 2.0}'
```

**移动鼠标**：
```bash
curl -X POST http://192.168.1.100:5000/api/mouse/move \
  -H "Content-Type: application/json" \
  -d '{"x": 100, "y": 200}'
```

**点击鼠标**：
```bash
curl -X POST http://192.168.1.100:5000/api/mouse/click \
  -H "Content-Type: application/json" \
  -d '{"button": "left", "count": 1}'
```

**输入文本**：
```bash
curl -X POST http://192.168.1.100:5000/api/keyboard/type \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

**按下按键**：
```bash
curl -X POST http://192.168.1.100:5000/api/keyboard/press \
  -H "Content-Type: application/json" \
  -d '{"key": "enter"}'
```

### 完整API列表

- `GET /health` - 健康检查
- `POST /api/test` - 测试画圆
- `GET /api/mouse/position` - 获取鼠标位置
- `POST /api/mouse/move` - 移动鼠标
- `POST /api/mouse/click` - 点击鼠标
- `POST /api/keyboard/type` - 输入文本
- `POST /api/keyboard/press` - 按下按键

## 故障排除

### 问题1：找不到 /dev/hidg* 设备

**检查模块是否加载**：
```bash
lsmod | grep libcomposite
```

如果未加载，手动加载：
```bash
sudo modprobe libcomposite
sudo modprobe dwc2
```

然后重新运行配置脚本：
```bash
sudo /usr/local/bin/usb-gadget.sh
```

### 问题2：目标电脑无法识别设备

1. 检查是否使用了数据线（不是充电线）
2. 检查是否连接到USB数据口（不是电源接口）
3. 重新插拔USB连接
4. 检查配置脚本是否成功运行

### 问题3：权限被拒绝

确保使用root权限运行服务：
```bash
sudo python3 main.py
```

## 注意事项

1. **必须使用root权限运行服务**（访问 `/dev/hidg*` 需要root权限）
2. **必须使用USB数据口**（靠近HDMI），不是电源接口
3. **必须使用数据线**（不是充电线）
4. **WiFi和以太网功能不受影响**，可以正常SSH连接
5. **USB主机功能受影响**，无法连接USB外设（键盘、鼠标、U盘等）
