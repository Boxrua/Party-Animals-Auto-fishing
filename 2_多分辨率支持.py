import pyautogui
import time
import random
import os
import sys
import ctypes
import psutil
import threading
import keyboard
import numpy as np
import cv2
import mybox

# -------------------------- 新增：窗口定位核心函数 --------------------------
user32 = ctypes.WinDLL('user32', use_last_error=True)

def get_window_rect(hwnd):
    """获取窗口的位置和尺寸 (left, top, right, bottom)"""
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def get_party_animals_hwnd():
    """查找猛兽派对窗口的句柄（HWND）"""
    hwnd_list = []
    def enum_windows_proc(hwnd, lParam):
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value > 0 and user32.IsWindowVisible(hwnd):
            try:
                process = psutil.Process(pid.value)
                if process.name() == "PartyAnimals.exe":
                    hwnd_list.append(hwnd)
            except:
                pass
        return True
    user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_windows_proc), 0)
    return hwnd_list[0] if hwnd_list else None

def capture_game_window():
    """只截取猛兽派对游戏窗口的画面（适配窗口化/全屏）"""
    hwnd = get_party_animals_hwnd()
    if not hwnd:
        print("未找到猛兽派对窗口！")
        return None
    
    left, top, right, bottom = get_window_rect(hwnd)
    width = right - left
    height = bottom - top
    
    if width <= 0 or height <= 0:
        print("游戏窗口尺寸异常！")
        return None
    
    try:
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"截取游戏窗口失败：{e}")
        return None

# -------------------------- 原有代码（完全保留） --------------------------
取运行目录 = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, '_MEIPASS') else __file__))
kg = True #总开关

def create_default_config(): #创建默认的配置文件
    config_path = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, '_MEIPASS') else __file__))+"/box_config.ini"
    default_content = """[全局]
传奇截图=真
#修改为假或者其他文本则关闭该功能
暂停快捷键=F2
#组合快捷键请用+符号连接 例如F2+A

[轻杆]
抛竿时间=1-2.5
点按时间=0.5-1.5
间隔时间=0.01-0.2

[重杆]
抛竿时间=2-4
点按时间=0.5-1
长按时间=1.5-3
间隔时间=0.1-0.3

#单位为秒，所有参数必须是带-符号的动态范围，删除该文件后，脚本会尝试重新创建默认配置文件
"""
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            print(f"配置文件已创建: {config_path}")
        except Exception as e:
            print(f"创建配置文件失败: {e}")

def get_resource_path(relative_path):
    """
    适配两种场景的路径获取（核心修复：仅做路径拼接，不做无效编码转换）
    1. IDE调试：读取脚本同级目录/pic/xxx.png
    2. 打包EXE：读取临时目录/pic/xxx.png（--add-data 打包进去的资源）
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    full_path = os.path.join(base_path, relative_path)
    full_path = os.path.normpath(full_path)
    full_path = os.path.abspath(full_path)
    return full_path

def cv_imread(file_path):
    """
    替代 cv2.imread，解决中文路径读取问题
    :param file_path: 图片路径（可含中文）
    :return: 图片数组（失败返回None）
    """
    try:
        file_bytes = np.fromfile(file_path, dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("图片解码失败")
        return img
    except Exception as e:
        print(f"读取图片失败：{file_path}，错误：{e}")
        return None

# 重新定义图片路径（确保pic文件夹在脚本同目录）
img1_path = get_resource_path(os.path.join("pic", "1.png"))
img2_path = get_resource_path(os.path.join("pic", "2.png"))
manle_path = get_resource_path(os.path.join("pic", "3.png"))
shibai_path = get_resource_path(os.path.join("pic", "4.png"))
taopao_path = get_resource_path(os.path.join("pic", "5.png"))
chuanqi_path = get_resource_path(os.path.join("pic", "6.png"))

# 设置pyautogui的参数
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

def press_mouse_left(duration):
    """长按鼠标左键指定时长后松开"""
    pyautogui.mouseDown(button='left')
    time.sleep(duration)
    pyautogui.mouseUp(button='left')

# -------------------------- 核心修复：check_image_exists --------------------------
def check_image_exists(img_path, confidence=0.8):
    """
    适配窗口化/全屏、任意分辨率的图片识别
    """
    try:
        # 1. 读取1080p模板（尺寸不变）
        template = cv_imread(img_path)
        if template is None:
            return False
        
        # 2. 只截取游戏窗口画面
        game_screenshot = capture_game_window()
        if game_screenshot is None:
            return False
        
        # 3. 缩放游戏窗口画面到1080p
        game_h, game_w = game_screenshot.shape[:2]
        base_w = 1920
        base_h = 1080
        screenshot_scaled = cv2.resize(
            game_screenshot, 
            (base_w, base_h), 
            interpolation=cv2.INTER_LINEAR
        )
        
        # 4. 模板匹配（原有逻辑）
        result = cv2.matchTemplate(screenshot_scaled, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)
        
        return len(locations[0]) > 0
    except Exception as e:
        print(f"图片识别失败：{img_path}，错误：{e}")
        return False

# -------------------------- 原有代码（完全保留） --------------------------
def window_name():
    """获取当前前台窗口的进程名""" 
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_id = pid.value
        process = psutil.Process(process_id)
        return process.name()
    except Exception as e:
        return ""

def main_loop():
    global kg
    while kg:
        try:
            while True:
                if kg == False:
                    break
                press_duration_1 = random.uniform(float(抛竿时间[0]), float(抛竿时间[1]))
                print(f"尝试抛竿：长按左键 {press_duration_1:.2f} 秒")
                press_mouse_left(press_duration_1)
                if check_image_exists(manle_path) != False:
                    print("检测到鱼桶满载或缺少鱼饵，自动暂停程序！您可以按下F2来重新抛竿钓鱼")
                    kg = False
                    break
                time.sleep(4.5)
                if check_image_exists(shibai_path,0.6) == False:
                    break
                else:
                    print("抛竿失败！")

            if kg == False:
                break
            
            print("开始监测是否上鱼")
            while not check_image_exists(img1_path,0.7):
                if kg == False:
                    break
                time.sleep(0.1)
            if kg == False:
                break
            print("监测到已上鱼，执行下一步操作")
            
            press_duration_2 = random.uniform(0.3, 0.8)
            print(f"开始尝试拉鱼：长按左键 {press_duration_2:.2f} 秒")
            press_mouse_left(press_duration_2)

            print("循环操作中，监测钓鱼成功后退出循环...")
            i = 0
            while (not check_image_exists(img2_path)) and (not check_image_exists(taopao_path)):
                i = i+1
                if kg == False:
                    break
                if i % 3 == 0 and 杆配置 == "2":
                    press_mouse_left(random.uniform(float(长按时间[0]), float(长按时间[1])))
                    continue
                press_duration_3 = random.uniform(float(点按时间[0]), float(点按时间[1]))
                press_mouse_left(press_duration_3)
                interval = random.uniform(float(间隔时间[0]), float(间隔时间[1]))
                time.sleep(interval)
            
            if kg == False:
                break
            
            if check_image_exists(taopao_path) == True:
                print("检测到拉鱼失败，3秒后尝试重新抛竿！")
                time.sleep(3)
                continue

            print("钓鱼成功，1.5秒后单击以进行收入鱼桶，2.5秒后尝试重新钓鱼")
            time.sleep(1.5)
            pyautogui.mouseDown(button='left')
            pyautogui.mouseUp(button='left')
            time.sleep(1)

        except Exception as e:
            print(f"程序出现异常：{e}，等待1秒后继续")
            time.sleep(1)

def 线程检测():
    while True:
        if check_image_exists(chuanqi_path,0.85) != False:
            save_dir = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, '_MEIPASS') else __file__))+"/截图"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                print(f"创建目录: {save_dir}")
            t = time.localtime()
            time.sleep(1)
            pyautogui.screenshot(save_dir+f"/{t.tm_year}年{t.tm_mon:02d}月{t.tm_mday:02d}日_{t.tm_hour:02d}时{t.tm_min:02d}分{t.tm_sec:02d}秒.png")
            print("检测到传奇鱼，尝试截图保存")
            time.sleep(10)
        time.sleep(0.5)

def 全局暂停():
    global kg
    if kg == True:
        kg = False
        print("已按下F2 程序手动暂停")
    else:
        kg = True
        print("已按下F2 程序已继续运行")
        threading.Thread(target=main_loop).start()

快捷键 = mybox.读配置项(取运行目录+r"\box_config.ini","全局","暂停快捷键","F2")
window_name_x = threading.Thread(target=线程检测)

if __name__ == "__main__":
    print(
        "猛兽派对-Auto-fishing 1.1.41-Test \n脚本使用Python编译运行，仅供学习交流，切勿传播\nby 哈基盒\n请确保游戏分辨率处于1920×1080状态下，按下F2以暂停脚本\n大于1080p的显示器请将游戏切换至窗口模式\n"
    )

    create_default_config()
    
    杆配置 = str(input("【1】轻杆\n【2】重杆\n【3】打开配置文件\n输入其他则退出程序\n请输入数字配置并按下回车："))
    
    if 杆配置 == "1":
        抛竿时间 = mybox.读配置项(取运行目录+r"\box_config.ini","轻杆","抛竿时间","1-2.5").split("-")
        点按时间 = mybox.读配置项(取运行目录+r"\box_config.ini","轻杆","点按时间","0.3-0.8").split("-")
        间隔时间 = mybox.读配置项(取运行目录+r"\box_config.ini","轻杆","间隔时间","0.01-0.3").split("-")
        print("配置已切换至轻杆配置")
    elif 杆配置 =="2":
        抛竿时间 = mybox.读配置项(取运行目录+r"\box_config.ini","重杆","抛竿时间","1-2.5").split("-")
        点按时间 = mybox.读配置项(取运行目录+r"\box_config.ini","重杆","点按时间","0.3-0.8").split("-")
        间隔时间 = mybox.读配置项(取运行目录+r"\box_config.ini","重杆","间隔时间","0.01-0.3").split("-")
        长按时间 = mybox.读配置项(取运行目录+r"\box_config.ini","重杆","长按时间","1.5-3").split("-")
        print("配置已切换至重杆配置")
    elif 杆配置 =="3":
        os.startfile(取运行目录+r"\box_config.ini")
        print("已打开脚本配置文件，程序将在3秒后主动关闭（修改完配置文件记得保存噢！）")
        time.sleep(3)
        os._exit(1)
    else:
        print("用户主动退出程序")
        os._exit(1)
    keyboard.add_hotkey(快捷键,全局暂停)

    传奇截图 = mybox.读配置项(取运行目录+r"\box_config.ini","全局","传奇截图","真")
    if 传奇截图 == "真":
        window_name_x.start()
        print("[提示] 钓上传奇自动截图功能已开启")
    else:
        print("[提示] 钓上传奇自动截图功能已关闭")

    print("\n请切换至猛兽派对窗口以运行脚本（需要拿着鱼竿站在水边）")
    while True:
        if window_name() == "PartyAnimals.exe":
            print("窗口已切换至游戏，请不要在脚本运行期间点击任何按键和操作鼠标左右键！")
            break
    
    main_loop()