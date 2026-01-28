# 树莓派键盘鼠标模拟服务

## 项目简介

本项目用于在树莓派上运行一个服务，通过USB HID设备模拟键盘和鼠标操作。

## 功能特性

- 实时监听传入的命令
- 模拟鼠标操作（移动、点击、画圆等）
- 模拟键盘操作（输入文本、按键等）
- RESTful API接口

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务

```bash
python main.py
```

服务默认运行在 `http://0.0.0.0:5000`

## API接口

### 测试服务 - 鼠标居中画圆
```
POST /api/test
```

## 注意事项

- 需要root权限运行（用于模拟HID设备）
- 确保树莓派已配置为USB HID设备模式
