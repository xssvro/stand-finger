"""
主服务入口
提供 RESTful API 与 WebSocket 接口用于控制鼠标和键盘
"""
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock
from mouse_controller import MouseController
from keyboard_controller import KeyboardController
from logger import logger as colored_logger

# 配置标准logging（用于Flask内部日志）
logging.basicConfig(
    level=logging.WARNING,  # 只显示警告和错误
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
flask_logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求
sock = Sock(app)

# 初始化控制器
mouse_controller = MouseController()
keyboard_controller = KeyboardController()


def _handle_ws_action(data):
    """
    处理 WebSocket 消息，执行对应动作并返回结果字典。
    data 格式: {"action": "mouse_move"|"mouse_click"|"keyboard_type"|"keyboard_press"|"test", ...params}
    """
    action = (data or {}).get('action')
    if not action:
        return {'status': 'error', 'message': '缺少 action 字段'}

    try:
        if action == 'mouse_move':
            x = data.get('x')
            y = data.get('y')
            if x is None or y is None:
                return {'status': 'error', 'message': '缺少必要参数: x, y'}
            x, y = int(x), int(y)
            duration = float(data.get('duration', 0.1))
            absolute = data.get('absolute', False)
            screen_width = data.get('screen_width')
            screen_height = data.get('screen_height')
            if absolute and screen_width and screen_height and screen_width > 0 and screen_height > 0:
                x = max(0, min(32767, int(x * 32767 / screen_width)))
                y = max(0, min(32767, int(y * 32767 / screen_height)))
            colored_logger.info(
                f"[WS] 移动鼠标: ({data.get('x')}, {data.get('y')})" + (" [绝对]" if absolute else ""),
                category="MOUSE"
            )
            mouse_controller.move_to(x, y, duration, absolute=absolute)
            return {'status': 'success', 'message': '鼠标已移动', 'absolute': absolute}

        if action == 'mouse_click':
            button = data.get('button', 'left')
            count = int(data.get('count', 1))
            colored_logger.info(f"[WS] 点击鼠标: {button} x{count}", category="MOUSE")
            mouse_controller.click(button, count)
            return {'status': 'success', 'message': f'已点击鼠标 {button} 按钮 {count} 次'}

        if action == 'keyboard_type':
            text = data.get('text')
            if not text:
                return {'status': 'error', 'message': '缺少必要参数: text'}
            interval = float(data.get('interval', 0.05))
            colored_logger.info(f"[WS] 输入文本: {text[:50]}{'...' if len(text) > 50 else ''}", category="KEYBOARD")
            keyboard_controller.type(text, interval)
            return {'status': 'success', 'message': '已输入文本'}

        if action == 'keyboard_press':
            key = data.get('key')
            if not key:
                return {'status': 'error', 'message': '缺少必要参数: key'}
            colored_logger.info(f"[WS] 按下按键: {key}", category="KEYBOARD")
            keyboard_controller.tap(key)
            return {'status': 'success', 'message': f'已按下按键: {key}'}

        if action == 'test':
            radius = int(data.get('radius', 100))
            duration = float(data.get('duration', 2.0))
            steps = int(data.get('steps', 50))
            center_move = data.get('center_move')
            center_back = data.get('center_back')
            center_move_x = center_move[0] if isinstance(center_move, (list, tuple)) and len(center_move) >= 2 else None
            center_move_y = center_move[1] if isinstance(center_move, (list, tuple)) and len(center_move) >= 2 else None
            center_back_x = center_back[0] if isinstance(center_back, (list, tuple)) and len(center_back) >= 2 else None
            center_back_y = center_back[1] if isinstance(center_back, (list, tuple)) and len(center_back) >= 2 else None
            colored_logger.info(f"[WS] 测试画圆 radius={radius}", category="API")
            mouse_controller.center(move_x=center_move_x, move_y=center_move_y, back_x=center_back_x, back_y=center_back_y)
            mouse_controller.draw_circle(radius=radius, steps=steps, duration=duration)
            return {'status': 'success', 'message': '测试完成：鼠标已居中并画圆', 'data': {'radius': radius, 'duration': duration, 'steps': steps}}

        return {'status': 'error', 'message': f'未知 action: {action}'}
    except RuntimeError as e:
        if '绝对定位不可用' in str(e):
            return {'status': 'error', 'message': str(e), 'hint': '请重新运行 usb-gadget.sh 以启用绝对指针（/dev/hidg2）'}
        raise
    except Exception as e:
        colored_logger.error(f"[WS] 执行失败: {e}", category="API")
        return {'status': 'error', 'message': str(e)}


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    colored_logger.debug("健康检查请求", category="API")
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常'
    })


@app.route('/api/test', methods=['GET', 'POST'])
def test_draw_circle():
    """测试服务：鼠标移动后画圆
    
    支持 GET 和 POST。
    GET: ?radius=100&duration=2.0&steps=50&center_move_x=500&center_move_y=500&center_back_x=250&center_back_y=250
    POST: 请求体 {"radius": 100, "duration": 2.0, "steps": 50, "center_move": [500,500], "center_back": [250,250]}
    """
    try:
        if request.method == 'GET':
            radius = int(request.args.get('radius', 100))
            duration = float(request.args.get('duration', 2.0))
            steps = int(request.args.get('steps', 50))
            center_move_x = request.args.get('center_move_x', type=int)
            center_move_y = request.args.get('center_move_y', type=int)
            center_back_x = request.args.get('center_back_x', type=int)
            center_back_y = request.args.get('center_back_y', type=int)
        else:
            data = request.get_json() or {}
            radius = data.get('radius', 100)
            duration = data.get('duration', 2.0)
            steps = data.get('steps', 50)
            center_move = data.get('center_move')
            center_back = data.get('center_back')
            center_move_x = center_move[0] if isinstance(center_move, (list, tuple)) and len(center_move) >= 2 else None
            center_move_y = center_move[1] if isinstance(center_move, (list, tuple)) and len(center_move) >= 2 else None
            center_back_x = center_back[0] if isinstance(center_back, (list, tuple)) and len(center_back) >= 2 else None
            center_back_y = center_back[1] if isinstance(center_back, (list, tuple)) and len(center_back) >= 2 else None
        
        colored_logger.info(f"执行测试：鼠标移动后画圆，半径={radius}, 持续时间={duration}秒, steps={steps}", category="API")
        
        # 1. 执行相对移动（模拟居中，可传参适配不同屏幕）
        mouse_controller.center(
            move_x=center_move_x, move_y=center_move_y,
            back_x=center_back_x, back_y=center_back_y
        )
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


@app.route('/api/mouse/move', methods=['GET', 'POST'])
def move_mouse():
    """移动鼠标
    
    支持 GET 和 POST。
    GET: ?x=100&y=200&duration=0.5&absolute=false&screen_width=1920&screen_height=1080
    POST: 请求体 {"x": 100, "y": 200, "duration": 0.5, "absolute": false, "screen_width": 1920, "screen_height": 1080}
    
    参数:
        x: X坐标（相对模式为移动量，绝对模式为逻辑坐标 0-32767 或像素）
        y: Y坐标（同上）
        duration: 相对移动持续时间（秒），可选
        absolute: 若 true 则按绝对坐标移动（需 /dev/hidg2）
        screen_width: 可选，与 screen_height 一起传入时，x/y 视为像素并自动归一化到 0-32767
        screen_height: 可选
    """
    try:
        if request.method == 'GET':
            x_str = request.args.get('x')
            y_str = request.args.get('y')
            if not x_str or not y_str:
                colored_logger.warning("移动鼠标请求缺少参数", category="API")
                return jsonify({
                    'status': 'error',
                    'message': '缺少必要参数: x, y'
                }), 400
            x = int(x_str)
            y = int(y_str)
            duration = float(request.args.get('duration', 0.1))
            absolute_str = request.args.get('absolute', 'false').lower()
            absolute = absolute_str in ('true', '1', 'yes', 'on')
            screen_width = request.args.get('screen_width', type=int)
            screen_height = request.args.get('screen_height', type=int)
        else:
            data = request.get_json() or {}
            if 'x' not in data or 'y' not in data:
                colored_logger.warning("移动鼠标请求缺少参数", category="API")
                return jsonify({
                    'status': 'error',
                    'message': '缺少必要参数: x, y'
                }), 400
            x = int(data['x'])
            y = int(data['y'])
            duration = data.get('duration', 0.1)
            absolute = data.get('absolute', False)
            screen_width = data.get('screen_width')
            screen_height = data.get('screen_height')

        # 保存原始坐标用于日志（在归一化之前）
        original_x = x
        original_y = y

        if absolute and screen_width and screen_height and screen_width > 0 and screen_height > 0:
            # 像素坐标转逻辑坐标 0-32767
            x = int(x * 32767 / screen_width)
            y = int(y * 32767 / screen_height)
            x = max(0, min(32767, x))
            y = max(0, min(32767, y))

        colored_logger.info(
            f"移动鼠标: ({original_x}, {original_y})"
            + (" [绝对]" if absolute else f"，持续时间: {duration}秒"),
            category="MOUSE"
        )
        mouse_controller.move_to(x, y, duration, absolute=absolute)
        colored_logger.success("鼠标已移动", category="MOUSE")

        return jsonify({
            'status': 'success',
            'message': '鼠标已移动',
            'absolute': absolute
        })
    except RuntimeError as e:
        if '绝对定位不可用' in str(e):
            return jsonify({
                'status': 'error',
                'message': str(e),
                'hint': '请重新运行 usb-gadget.sh 以启用绝对指针（/dev/hidg2）'
            }), 400
        raise
    except Exception as e:
        colored_logger.error(f"移动鼠标失败: {str(e)}", category="API")
        return jsonify({
            'status': 'error',
            'message': f'移动失败: {str(e)}'
        }), 500


@app.route('/api/mouse/click', methods=['GET', 'POST'])
def click_mouse():
    """点击鼠标
    
    支持 GET 和 POST。
    GET: ?button=left&count=1
    POST: 请求体 {"button": "left", "count": 1}
    
    参数:
        button: 按钮类型 (left, right, middle)，默认 left
        count: 点击次数，默认 1
    """
    try:
        if request.method == 'GET':
            button = request.args.get('button', 'left')
            count = int(request.args.get('count', 1))
        else:
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


@app.route('/api/keyboard/type', methods=['GET', 'POST'])
def type_text():
    """输入文本
    
    支持 GET 和 POST。
    GET: ?text=Hello%20World&interval=0.05
    POST: 请求体 {"text": "Hello World", "interval": 0.05}
    
    参数:
        text: 要输入的文本（必需）
        interval: 字符间隔（秒），默认 0.05
    """
    try:
        if request.method == 'GET':
            text = request.args.get('text')
            if not text:
                colored_logger.warning("输入文本请求缺少参数", category="API")
                return jsonify({
                    'status': 'error',
                    'message': '缺少必要参数: text'
                }), 400
            interval = float(request.args.get('interval', 0.05))
        else:
            data = request.get_json() or {}
            if 'text' not in data:
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


@app.route('/api/keyboard/press', methods=['GET', 'POST'])
def press_key():
    """按下按键
    
    支持 GET 和 POST。
    GET: ?key=enter
    POST: 请求体 {"key": "enter"}
    
    参数:
        key: 按键名称（必需）
    """
    try:
        if request.method == 'GET':
            key = request.args.get('key')
            if not key:
                colored_logger.warning("按下按键请求缺少参数", category="API")
                return jsonify({
                    'status': 'error',
                    'message': '缺少必要参数: key'
                }), 400
        else:
            data = request.get_json() or {}
            if 'key' not in data:
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


@sock.route('/ws')
def websocket_handler(ws):
    """
    WebSocket 端点：ws://<host>:5000/ws
    
    客户端发送 JSON 消息，格式: {"action": "<动作名>", ...参数}
    支持 action: mouse_move, mouse_click, keyboard_type, keyboard_press, test
    服务端回复 JSON: {"status": "success"|"error", "message": "...", ...}
    """
    colored_logger.info("WebSocket 客户端已连接", category="API")
    while True:
        try:
            msg = ws.receive()
        except Exception:
            break
        if msg is None:
            break
        try:
            data = json.loads(msg)
        except (json.JSONDecodeError, TypeError) as e:
            ws.send(json.dumps({'status': 'error', 'message': f'无效 JSON: {e}'}))
            continue
        result = _handle_ws_action(data)
        try:
            ws.send(json.dumps(result, ensure_ascii=False))
        except Exception:
            break
    colored_logger.info("WebSocket 客户端已断开", category="API")


if __name__ == '__main__':
    colored_logger.banner("USB HID 键盘鼠标模拟服务")
    colored_logger.success("服务启动中...", category="SYSTEM")
    colored_logger.info("服务地址: http://0.0.0.0:5000", category="NETWORK")
    colored_logger.info("API接口列表:", category="API")
    colored_logger.info("  GET/POST /api/test - 测试服务：鼠标移动后画圆", category="API")
    colored_logger.info("  GET/POST /api/mouse/move - 移动鼠标", category="API")
    colored_logger.info("  GET/POST /api/mouse/click - 点击鼠标", category="API")
    colored_logger.info("  GET/POST /api/keyboard/type - 输入文本", category="API")
    colored_logger.info("  GET/POST /api/keyboard/press - 按下按键", category="API")
    colored_logger.info("  WebSocket ws://0.0.0.0:5000/ws - 高效双向通信（action: mouse_move/mouse_click/keyboard_type/keyboard_press/test）", category="API")
    log_path = colored_logger.get_log_path()
    if log_path:
        colored_logger.info(f"日志文件: {log_path}", category="SYSTEM")
    colored_logger.separator()
    colored_logger.success("服务已启动，等待请求...", category="SYSTEM")

    app.run(host='0.0.0.0', port=5000, debug=False)
