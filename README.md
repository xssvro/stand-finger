# 树莓派USB HID键盘鼠标模拟服务

## 项目简介

树莓派通过USB连接到目标电脑，作为USB HID设备（键盘+鼠标），接收网络命令后通过USB HID协议控制目标电脑。

**支持的树莓派型号**：
- ✅ 树莓派Zero/Zero W（推荐，只有一个USB口）
- ✅ 树莓派4（使用USB-A口，不是Type-C口）

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

**方式1：使用检查脚本（推荐）**

```bash
# 运行连接检查脚本
./check_usb_connection.sh
```

**方式2：手动检查（在树莓派上）**

```bash
# 检查设备文件
find /dev -name "hidg*"
# 或
[ -e /dev/hidg0 ] && echo "✓ 键盘设备存在" || echo "✗ 未找到键盘设备"
[ -e /dev/hidg1 ] && echo "✓ 鼠标设备存在" || echo "✗ 未找到鼠标设备"

# 检查USB Gadget状态
cat /sys/kernel/config/usb_gadget/pi4/UDC
# 如果有输出，说明已启用

# 查看USB连接事件
dmesg | tail -20 | grep -i "usb\|gadget"
```

应该看到 `/dev/hidg0` 和 `/dev/hidg1`。

## 二、连接设备到电脑

### ⚠️ 重要：树莓派的USB接口

**树莓派Zero**：
- 有两个Micro USB接口
- **USB数据口**（靠近HDMI）→ ✅ 用于USB Gadget
- **电源接口**（靠近SD卡）→ ❌ 只能供电

**树莓派4**：
- **USB Type-C口** → ❌ **只能供电，不能用于USB Gadget**
- **USB-A口**（USB 2.0或USB 3.0）→ ✅ **必须使用这些接口**
- 树莓派4有多个USB-A口，选择任意一个连接到电脑

### 连接步骤

**树莓派Zero**：
```
树莓派Zero                   目标电脑
┌─────────────┐              ┌─────────────┐
│             │              │             │
│  USB数据口  │ ───数据线───> │   USB口     │
│  (靠近HDMI) │              │             │
└─────────────┘              └─────────────┘
```

**树莓派4**：
```
树莓派4                      目标电脑
┌─────────────┐              ┌─────────────┐
│             │              │             │
│  USB-A口    │ ───数据线───> │   USB口     │
│  (任意一个) │              │             │
│             │              │             │
│  Type-C     │ ───电源线───> │  (仅供电)   │
│  (仅供电)   │              │             │
└─────────────┘              └─────────────┘
```

**连接步骤**：
1. **树莓派Zero**：使用USB数据线连接到USB数据口（靠近HDMI）
2. **树莓派4**：使用USB数据线连接到**USB-A口**（不是Type-C口）
3. 另一端连接到目标电脑的USB口
4. **树莓派4需要单独供电**：Type-C口连接电源适配器

### 验证连接

**在树莓派上检查**：

```bash
# 运行检查脚本
./check_usb_connection.sh

# 或手动检查
cat /sys/kernel/config/usb_gadget/pi4/UDC
# 如果有输出（如：20980000.usb），说明已连接
```

**在目标电脑上验证**：

**Linux**：
```bash
# 查看USB设备
lsusb | grep -i "raspberry\|hid\|1d6b"

# 查看输入设备
ls /dev/input/by-id/ | grep -i "keyboard\|mouse"
```

**Windows**：
- 打开"设备管理器"
- 展开"键盘"和"鼠标和其他指针设备"
- 应该看到"Raspberry Pi USB HID Keyboard Mouse"

**macOS**：
- 打开"系统信息" → "USB"
- 应该看到"Raspberry Pi USB HID Keyboard Mouse"

## 三、服务使用

### 安装依赖

在树莓派上：

```bash
pip install -r requirements.txt
```

### 启动服务

**⚠️ 必须使用root权限运行**（访问 `/dev/hidg*` 需要root权限）。

**依赖安装在虚拟环境(venv)中**，所以要用虚拟环境里的 Python 来跑：

```bash
# 方式1：使用启动脚本（推荐）
# 会激活 venv、安装依赖，并用 venv 里的 Python 启动
sudo ./start.sh

# 方式2：直接运行（使用虚拟环境中的 Python）
sudo ./venv/bin/python3 main.py
```

**不要用** `sudo python3 main.py`，那样会走系统 Python，找不到 venv 里装的依赖。

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

### 画圆速度与参数说明

**画圆速度**由 `duration` 和 `steps` 控制：
- **duration**：画完整一圈的总时间（秒），默认 2.0。越大越慢。
- **steps**：一圈分成多少步，默认 50。越大越平滑，每步间隔 = duration / steps。
- **radius**：圆的半径（像素），默认 100。

示例：`duration=2.0, steps=50` → 2 秒画完一圈，每步约 0.04 秒。

**屏幕尺寸**：USB HID 鼠标无法获取目标电脑的屏幕尺寸和当前坐标，只能做相对移动。  
“居中”是经验值（先向右下移 500,500，再向左上移 250,250），适合常见 1080p。其他分辨率可在代码里改 `DEFAULT_CENTER_OFFSET` / `DEFAULT_CENTER_BACK`，或通过 API 传 `center_move`、`center_back`（若后续接口支持）。

### 完整API列表

- `GET /health` - 健康检查
- `GET/POST /api/test` - 测试画圆（支持 ?radius=100&duration=2&steps=50）
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

**运行脚本后不需要重启树莓派**，USB Gadget会立即生效。

**排查步骤**：

1. **在树莓派上检查配置是否成功**：
   ```bash
   # 检查设备文件
   find /dev -name "hidg*"
   
   # 检查UDC是否启用
   cat /sys/kernel/config/usb_gadget/pi4/UDC
   # 应该有输出（如：20980000.usb），如果是空的说明未启用
   ```

2. **检查USB连接**：
   - ✅ 使用**数据线**（不是充电线）
   - ✅ 连接到**USB数据口**（靠近HDMI，不是电源接口）
   - ✅ 连接到目标电脑的USB口

3. **重新插拔USB连接**（重要）：
   - 断开树莓派与电脑的USB连接
   - 等待3-5秒
   - 重新连接
   - Windows会自动检测新设备

4. **如果UDC为空，重新运行脚本**：
   ```bash
   sudo ./usb-gadget.sh
   ```

5. **在Windows上刷新设备管理器**：
   - 在设备管理器中点击"操作" → "扫描检测硬件改动"
   - 或按F5刷新

6. **检查Windows设备管理器中的其他位置**：
   - "通用串行总线控制器"下可能有未知设备
   - "人体学输入设备"下可能有HID设备
   - 如果有黄色感叹号，可能需要安装驱动（通常不需要）

### 问题3：权限被拒绝

**错误信息**：`Permission denied: '/dev/hidg0'` 或 `Permission denied: '/dev/hidg1'`

**解决方案**：必须使用root权限运行服务：
```bash
sudo python3 main.py
# 或
sudo ./start.sh
```

### 问题4：树莓派4连接问题

**问题**：树莓派4使用USB Type-C连接，但设备无法识别

**原因**：树莓派4的USB Type-C口只能供电，不能传输数据

**解决方案**：
1. 使用**USB-A口**（USB 2.0或USB 3.0）连接到电脑
2. Type-C口用于单独供电（连接电源适配器）
3. 树莓派4有多个USB-A口，选择任意一个即可

## 注意事项

1. **必须使用root权限运行服务**（访问 `/dev/hidg*` 需要root权限）
2. **必须使用USB数据口**（靠近HDMI），不是电源接口
3. **必须使用数据线**（不是充电线）
4. **WiFi和以太网功能不受影响**，可以正常SSH连接
5. **USB主机功能受影响**，无法连接USB外设（键盘、鼠标、U盘等）
