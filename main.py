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
取运行目录 = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, '_MEIPASS') else __file__))
kg = True #总开关
#打包命令 pyinstaller -F --add-data "pic;pic" main.py


def create_default_config(): #创建默认的配置文件
    config_path = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, '_MEIPASS') else __file__))+"/box_config.ini"
    default_content = """[全局]
传奇截图=真
#修改为假或者其他文本则关闭该功能
暂停快捷键=P
#组合快捷键请用+符号连接 例如F2+A


[轻杆]
抛竿时间=1-2.5
点按时间=0.3-0.8
间隔时间=0.01-0.2

[重杆]
抛竿时间=2-4
点按时间=0.8-1.5
长按时间=1.8-3.5
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
    # else:
    #     print("配置文件已存在，无需创建。")

def get_resource_path(relative_path):
    """
    适配两种场景的路径获取（核心修复：仅做路径拼接，不做无效编码转换）
    1. IDE调试：读取脚本同级目录/pic/xxx.png
    2. 打包EXE：读取临时目录/pic/xxx.png（--add-data 打包进去的资源）
    """
    try:
        # PyInstaller 打包后的临时资源目录
        base_path = sys._MEIPASS
    except Exception:
        # 调试模式下的脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 拼接并规范化路径（确保跨平台兼容性）
    full_path = os.path.join(base_path, relative_path)
    full_path = os.path.normpath(full_path)
    full_path = os.path.abspath(full_path)
    return full_path

# 修复：替换 pyautogui.locateOnScreen 的中文路径问题
def cv_imread(file_path):
    """
    替代 cv2.imread，解决中文路径读取问题
    :param file_path: 图片路径（可含中文）
    :return: 图片数组（失败返回None）
    """
    try:
        # 以二进制流读取文件，避开 cv2.imread 的路径编码问题
        file_bytes = np.fromfile(file_path, dtype=np.uint8)
        # 解码为OpenCV可用的图片格式
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



# 设置pyautogui的参数：识别图片的置信度（0-1，越高越精准），失败时不抛出异常
pyautogui.FAILSAFE = False  # 关闭鼠标移到角落触发的安全退出
pyautogui.PAUSE = 0.01       # 操作间的默认延迟，降低可提高速度

def press_mouse_left(duration):
    """
    长按鼠标左键指定时长后松开
    :param duration: 长按的秒数（浮点数）
    """
    pyautogui.mouseDown(button='left')  # 按下左键
    time.sleep(duration)                # 保持按下状态
    pyautogui.mouseUp(button='left')    # 松开左键

def check_image_exists(img_path, confidence=0.8):
    """
    替代 pyautogui.locateOnScreen，解决中文路径识别问题
    :param img_path: 图片路径
    :param confidence: 识别置信度
    :return: True（存在）/False（不存在）
    """
    try:
        # 1. 读取模板图片（支持中文路径）
        template = cv_imread(img_path)
        if template is None:
            return False
        
        # 2. 获取屏幕截图（转为OpenCV格式）
        screenshot = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 3. 模板匹配（替代 pyautogui.locateOnScreen）
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        # 查找匹配值大于置信度的位置
        locations = np.where(result >= confidence)
        
        # 4. 判断是否匹配到
        return len(locations[0]) > 0
    except Exception as e:
        print(f"图片识别失败：{img_path}，错误：{e}")
        return False

def window_name():
    """获取当前前台窗口的进程名 猛兽进程名PartyAnimals.exe """ 
    try:
        # 使用ctypes获取前台窗口
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_id = pid.value
        
        # 使用psutil获取进程名
        process = psutil.Process(process_id)
        return process.name()
    except Exception as e:
        # 如果无法获取进程名，返回空字符串
        return ""


def main_loop():
    global kg
    """主循环：执行所有指定操作"""
    #print("程序已启动，按 Ctrl+C 终止...")
    #print("请在5秒内切换至猛兽派对窗口")
    #time.sleep(1)
    while kg:
        try:
            while True:
                if kg == False: #手动暂停
                    break
                # 第一步：长按鼠标左键2-4秒后松开
                press_duration_1 = random.uniform(float(抛竿时间[0]), float(抛竿时间[1]))
                print(f"尝试抛竿：长按左键 {press_duration_1:.2f} 秒")
                press_mouse_left(press_duration_1)
                if check_image_exists(manle_path) != False:
                    print("检测到鱼桶满载或缺少鱼饵，自动暂停程序！您可以按下F2来重新抛竿钓鱼")
                    kg = False
                    break
                time.sleep(4.5)
                if check_image_exists(shibai_path) == False:
                    break
                else:
                    print("抛竿失败！")

            # # 第一步：长按鼠标左键2-4秒后松开
            # press_duration_1 = random.uniform(1, 2.5)
            # print(f"尝试抛竿：长按左键 {press_duration_1:.2f} 秒")
            # press_mouse_left(press_duration_1)
            if kg == False: #手动暂停
                break
            
            # 第二步：循环检测1.png，直到出现
            print("开始监测是否上鱼")
            while not check_image_exists(img1_path):
                if kg == False: #手动暂停
                    break
                time.sleep(0.1)  # 每0.1秒检测一次，降低CPU占用
            if kg == False: #手动暂停
                break
            print("监测到已上鱼，执行下一步操作")
            
            # 第三步：长按鼠标左键0.5-1秒后松开
            press_duration_2 = random.uniform(0.3, 0.8)
            print(f"开始尝试拉鱼：长按左键 {press_duration_2:.2f} 秒")
            press_mouse_left(press_duration_2)

            # 第四步：循环长按0.5-1秒松开，间隔0.1-0.3秒，直到检测到2.png
            print("循环操作中，监测钓鱼成功后退出循环...")
            i = 0
            while (not check_image_exists(img2_path)) and (not check_image_exists(taopao_path)):
                i = i+1
                if kg == False: #手动暂停
                    break
                if i % 3 == 0 and 杆配置 == "2":
                    press_mouse_left(random.uniform(float(长按时间[0]), float(长按时间[1]))) #长按拉线
                    continue
                # 长按0.1-0.5秒
                press_duration_3 = random.uniform(float(点按时间[0]), float(点按时间[1]))
                press_mouse_left(press_duration_3) #点按拉线
                
                # 松开后间隔0.1-0.3秒
                interval = random.uniform(float(间隔时间[0]), float(间隔时间[1]))
                time.sleep(interval)
            
            if kg == False: #手动暂停
                break
            
            if check_image_exists(taopao_path) == True: #检测拉鱼失败后进入下一次循环
                print("检测到拉鱼失败，3秒后尝试重新抛竿！")
                time.sleep(3)
                continue

            print("钓鱼成功，1.5秒后单击以进行收入鱼桶，2.5秒后尝试重新钓鱼")
            time.sleep(1.5)
            pyautogui.mouseDown(button='left')
            pyautogui.mouseUp(button='left')
            # 第五步：等待3秒，然后重新开始整个流程
            time.sleep(1)

        except Exception as e:
            # 捕获其他异常，避免程序崩溃
            print(f"程序出现异常：{e}，等待1秒后继续")
            time.sleep(1)


def 线程检测():
    while True:
        if check_image_exists(chuanqi_path,0.85) != False:
            save_dir = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, '_MEIPASS') else __file__))+"/截图"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)  # makedirs 会创建所有不存在的父目录
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
window_name_x = threading.Thread(target=线程检测,daemon=True)




if __name__ == "__main__":
    #mybox.写配置项(r"\1.ini","全局","test","啊啊啊")
    
    print(
        "猛兽派对-Auto-fishing 1.1.4 \n脚本使用Python编译运行，仅供学习交流，切勿传播\nby 哈基盒\n请确保游戏分辨率处于1920×1080状态下，按下F2以暂停脚本\n大于1080p的显示器请将游戏切换至窗口模式\n"
    )

    create_default_config() #创建配置文件
    
    杆配置 = str(input("【1】轻杆\n【2】重杆\n【3】打开配置文件\n输入其他则退出程序\n请输入数字配置并按下回车(默认配置文件下，除新手杆以外不论轻杆重杆都建议使用重杆的配置)："))
    
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
    keyboard.add_hotkey(快捷键,全局暂停) #注册全局快捷键

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

