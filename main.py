"""
主服务入口
提供RESTful API接口用于控制鼠标和键盘
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from mouse_controller import MouseController
from keyboard_controller import KeyboardController
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化控制器
mouse_controller = MouseController()
keyboard_controller = KeyboardController()


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常'
    })


@app.route('/api/test', methods=['POST'])
def test_draw_circle():
    """测试服务：鼠标居中后画圆
    
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
        
        logger.info(f"执行测试：鼠标居中后画圆，半径={radius}, 持续时间={duration}秒")
        
        # 1. 鼠标居中
        mouse_controller.center()
        logger.info("鼠标已移动到屏幕中心")
        
        # 2. 画圆
        mouse_controller.draw_circle(
            radius=radius,
            steps=steps,
            duration=duration
        )
        logger.info("画圆完成")
        
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
        logger.error(f"测试服务执行失败: {str(e)}", exc_info=True)
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
        logger.error(f"获取鼠标位置失败: {str(e)}")
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
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: x, y'
            }), 400
        
        x = int(data['x'])
        y = int(data['y'])
        duration = data.get('duration', 0.1)
        
        mouse_controller.move_to(x, y, duration)
        
        return jsonify({
            'status': 'success',
            'message': f'鼠标已移动到 ({x}, {y})'
        })
    
    except Exception as e:
        logger.error(f"移动鼠标失败: {str(e)}")
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
        
        mouse_controller.click(button, count)
        
        return jsonify({
            'status': 'success',
            'message': f'已点击鼠标 {button} 按钮 {count} 次'
        })
    
    except Exception as e:
        logger.error(f"点击鼠标失败: {str(e)}")
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
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: text'
            }), 400
        
        text = data['text']
        interval = data.get('interval', 0.05)
        
        keyboard_controller.type(text, interval)
        
        return jsonify({
            'status': 'success',
            'message': f'已输入文本: {text}'
        })
    
    except Exception as e:
        logger.error(f"输入文本失败: {str(e)}")
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
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: key'
            }), 400
        
        key = data['key']
        keyboard_controller.tap(key)
        
        return jsonify({
            'status': 'success',
            'message': f'已按下按键: {key}'
        })
    
    except Exception as e:
        logger.error(f"按下按键失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'按键失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    logger.info("启动键盘鼠标模拟服务...")
    logger.info("服务地址: http://0.0.0.0:5000")
    logger.info("API文档:")
    logger.info("  POST /api/test - 测试服务：鼠标居中后画圆")
    logger.info("  GET  /api/mouse/position - 获取鼠标位置")
    logger.info("  POST /api/mouse/move - 移动鼠标")
    logger.info("  POST /api/mouse/click - 点击鼠标")
    logger.info("  POST /api/keyboard/type - 输入文本")
    logger.info("  POST /api/keyboard/press - 按下按键")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
