"""
主服务入口
提供RESTful API接口用于控制鼠标和键盘
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from mouse_controller import MouseController
from keyboard_controller import KeyboardController
from logger import logger as colored_logger
import logging

# 配置标准logging（用于Flask内部日志）
logging.basicConfig(
    level=logging.WARNING,  # 只显示警告和错误
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
flask_logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化控制器
mouse_controller = MouseController()
keyboard_controller = KeyboardController()


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    colored_logger.debug("健康检查请求", category="API")
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常'
    })


@app.route('/api/test', methods=['POST'])
def test_draw_circle():
    """测试服务：鼠标移动后画圆
    
    注意：USB HID鼠标只能做相对移动，无法获取绝对位置
    此服务会先执行一个相对移动，然后以当前位置为圆心画圆
    
    请求体（可选）:
    {
        "radius": 100,      # 圆的半径，默认100
        "duration": 2.0,    # 画圆时间（秒），默认2.0
        "steps": 50         # 画圆步数，默认50
    }
    """
    try:
        data = request.get_json() or {}
        radius = data.get('radius', 100)
        duration = data.get('duration', 2.0)
        steps = data.get('steps', 50)
        
        colored_logger.info(f"执行测试：鼠标移动后画圆，半径={radius}, 持续时间={duration}秒", category="API")
        
        # 1. 执行一个相对移动（模拟居中操作）
        mouse_controller.center()
        colored_logger.success("鼠标已执行相对移动", category="MOUSE")
        
        # 2. 画圆（以当前位置为圆心）
        mouse_controller.draw_circle(
            radius=radius,
            steps=steps,
            duration=duration
        )
        colored_logger.success("画圆完成", category="MOUSE")
        
        return jsonify({
            'status': 'success',
            'message': '测试完成：鼠标已居中并画圆',
            'data': {
                'radius': radius,
                'duration': duration,
                'steps': steps
            }
        })
    
    except Exception as e:
        colored_logger.error(f"测试服务执行失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'执行失败: {str(e)}'
        }), 500


@app.route('/api/mouse/position', methods=['GET'])
def get_mouse_position():
    """获取当前鼠标位置"""
    try:
        x, y = mouse_controller.get_position()
        return jsonify({
            'status': 'success',
            'data': {
                'x': x,
                'y': y
            }
        })
    except Exception as e:
        colored_logger.error(f"获取鼠标位置失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'获取失败: {str(e)}'
        }), 500


@app.route('/api/mouse/move', methods=['POST'])
def move_mouse():
    """移动鼠标到指定位置
    
    请求体:
    {
        "x": 100,           # 目标X坐标
        "y": 200,           # 目标Y坐标
        "duration": 0.5     # 移动持续时间（秒），可选
    }
    """
    try:
        data = request.get_json()
        if not data or 'x' not in data or 'y' not in data:
            colored_logger.warning("移动鼠标请求缺少参数", category="API")
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: x, y'
            }), 400
        
        x = int(data['x'])
        y = int(data['y'])
        duration = data.get('duration', 0.1)
        
        colored_logger.info(f"移动鼠标到 ({x}, {y})，持续时间: {duration}秒", category="MOUSE")
        mouse_controller.move_to(x, y, duration)
        colored_logger.success(f"鼠标已移动到 ({x}, {y})", category="MOUSE")
        
        return jsonify({
            'status': 'success',
            'message': f'鼠标已移动到 ({x}, {y})'
        })
    
    except Exception as e:
        colored_logger.error(f"移动鼠标失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'移动失败: {str(e)}'
        }), 500


@app.route('/api/mouse/click', methods=['POST'])
def click_mouse():
    """点击鼠标
    
    请求体:
    {
        "button": "left",   # 按钮类型: left, right, middle
        "count": 1          # 点击次数，可选
    }
    """
    try:
        data = request.get_json() or {}
        button = data.get('button', 'left')
        count = data.get('count', 1)
        
        colored_logger.info(f"点击鼠标: {button} 按钮，{count} 次", category="MOUSE")
        mouse_controller.click(button, count)
        colored_logger.success(f"已点击鼠标 {button} 按钮 {count} 次", category="MOUSE")
        
        return jsonify({
            'status': 'success',
            'message': f'已点击鼠标 {button} 按钮 {count} 次'
        })
    
    except Exception as e:
        colored_logger.error(f"点击鼠标失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'点击失败: {str(e)}'
        }), 500


@app.route('/api/keyboard/type', methods=['POST'])
def type_text():
    """输入文本
    
    请求体:
    {
        "text": "Hello World",  # 要输入的文本
        "interval": 0.05         # 字符间隔（秒），可选
    }
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            colored_logger.warning("输入文本请求缺少参数", category="API")
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: text'
            }), 400
        
        text = data['text']
        interval = data.get('interval', 0.05)
        
        colored_logger.info(f"输入文本: {text[:50]}{'...' if len(text) > 50 else ''}", category="KEYBOARD")
        keyboard_controller.type(text, interval)
        colored_logger.success(f"已输入文本: {text[:50]}{'...' if len(text) > 50 else ''}", category="KEYBOARD")
        
        return jsonify({
            'status': 'success',
            'message': f'已输入文本: {text}'
        })
    
    except Exception as e:
        colored_logger.error(f"输入文本失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'输入失败: {str(e)}'
        }), 500


@app.route('/api/keyboard/press', methods=['POST'])
def press_key():
    """按下按键
    
    请求体:
    {
        "key": "enter"  # 按键名称
    }
    """
    try:
        data = request.get_json()
        if not data or 'key' not in data:
            colored_logger.warning("按下按键请求缺少参数", category="API")
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: key'
            }), 400
        
        key = data['key']
        colored_logger.info(f"按下按键: {key}", category="KEYBOARD")
        keyboard_controller.tap(key)
        colored_logger.success(f"已按下按键: {key}", category="KEYBOARD")
        
        return jsonify({
            'status': 'success',
            'message': f'已按下按键: {key}'
        })
    
    except Exception as e:
        colored_logger.error(f"按下按键失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'按键失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    colored_logger.banner("USB HID 键盘鼠标模拟服务")
    colored_logger.success("服务启动中...", category="SYSTEM")
    colored_logger.info("服务地址: http://0.0.0.0:5000", category="NETWORK")
    colored_logger.info("API接口列表:", category="API")
    colored_logger.info("  POST /api/test - 测试服务：鼠标移动后画圆", category="API")
    colored_logger.info("  GET  /api/mouse/position - 获取鼠标位置", category="API")
    colored_logger.info("  POST /api/mouse/move - 移动鼠标", category="API")
    colored_logger.info("  POST /api/mouse/click - 点击鼠标", category="API")
    colored_logger.info("  POST /api/keyboard/type - 输入文本", category="API")
    colored_logger.info("  POST /api/keyboard/press - 按下按键", category="API")
    colored_logger.separator()
    colored_logger.success("服务已启动，等待请求...", category="SYSTEM")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
