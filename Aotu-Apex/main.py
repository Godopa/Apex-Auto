import win32gui
import win32ui
import win32api
from ctypes import windll
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
import pydirectinput
from pynput.mouse import Controller
from tools.mouse import mouse_down, mouse_up
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QTime, Qt
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QLabel
from PJYSDK import PJYSDK
from MainWindowUI import Ui_Form
import sys
import uuid

# 初始化 app_key 和 app_secret 在开发者后台新建软件获取
pjysdk = PJYSDK(app_key='cpcnlnrdqusva2ftjavg', app_secret='PAbg1ORh1Qpl8LLy43WGDA4eRmQ1gAsu')
pjysdk.debug = False

# 心跳失败回调
def on_heartbeat_failed(hret):
    print(hret.message)
    if hret.code == 10214:
        os._exit(1)  # 退出脚本
    print("心跳失败，尝试重登...")
    login_ret = pjysdk.card_login()
    if login_ret.code == 0:
        print("重登成功")
    else:
        print(login_ret.message)  # 重登失败
        os._exit(1)  # 退出脚本

mouse = Controller()
PicsCV = {}
Pics = {}
# 用于遍历位于项目中 "./pics" 文件夹中的所有文件，并将其中的PNG格式图像加载为PIL图像对象和OpenCV图像对象
# 并将它们存储到类的Pics和PicsCV字典中，以便后续在程序中使用
# 使用 for 循环遍历该列表，os.listdir("./pics") 返回指定目录下所有文件和文件夹的名称列表
for file in os.listdir("./pics"):
    # 使用 split() 方法以点号为分隔符将文件名分割成两部分，info[0] 是文件名部分，info[1] 是文件扩展名部分
    info = file.split(".")
    # 检查文件的扩展名是否为 "png"，确保只处理 PNG 格式的图像文件。
    if info[1] == "png" or info[1] == "jpg":
        # 使用PIL库的Image.open()方法打开图像文件，并将其加载为 PIL 图像对象 tmpImage
        tmpImage = Image.open("./pics/" + file)
        # 使用 OpenCV的cv2.imread()方法读取图像文件，并将其加载为 OpenCV 图像对象 imgCv
        imgCv = cv2.imread("./pics/" + file)
        # 将PIL图像对象tmpImage存储到类的 Pics 字典中，键为文件名（不包含扩展名），值为对应的 PIL 图像对象
        Pics.update({info[0]: tmpImage})
        # 将OpenCV图像对象imgCv存储到类的PicsCV字典中，键为文件名（不包含扩展名），值为对应的 OpenCV 图像对象
        PicsCV.update({info[0]: imgCv})

# 该函数接受一个可选参数 region，用于指定截图的区域。返回值是截取的图像和窗口的左上角坐标 (left, top)
def Screenshot(region=None):  # -> (im, (left, top))
    # 初始化重试次数try_count为3，并设置一个标志变量success为False，用于跟踪是否成功截取截图
    try_count = 3
    success = False
    # 开始一个while 循环，只有当重试次数大于 0 并且尚未成功时继续执行。每次循环尝试次数减
    while try_count > 0 and not success:
        try:
            try_count -= 1
            # 查找窗口类名为"UnityWndClass"的窗口句柄Handle，并将该窗口设为活动窗口。
            Handle = win32gui.FindWindow(None, "Apex Legends")
            win32gui.SetActiveWindow(Handle)
            hwnd = Handle
            # 获取窗口的矩形坐标(left, top, right, bot)
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
            # 调整窗口大小
            win32gui.MoveWindow(hwnd, left, top, 1280, 720, True)
            # 设置截图的宽度和高度，并将其转换为整数。
            width = 1280
            height = 720
            RealRate = (width, height)
            width = int(width)
            height = int(height)
            # 获取窗口的设备上下文句柄 hwndDC，并创建一个兼容的内存设备上下文 saveDC
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            # 创建一个兼容的位图saveBitMap并选择到内存设备上下文中
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            # 调用PrintWindow函数将窗口内容复制到内存设备上下文中
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
            # 获取位图的信息和数据，并使用PIL.Image.frombuffer将其转换为Image对象
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            im = Image.frombuffer(
                "RGB",
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            # 删除位图和设备上下文，释放资源。
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            # 将图像调整为1280x720大小
            im = im.resize((1280, 720))
            # 如果提供了region参数，则裁剪图像以符合指定区域
            if region is not None:
                im = im.crop((region[0], region[1], region[0] + region[2], region[1] + region[3]))
            # 如果PrintWindow函数成功，设置success为True，并返回图像和窗口的左上角坐标(left, top)
            if result:
                success = True
                return im, (left, top)
        except Exception as e:
            print("截图时出现错误:", repr(e))
            # sleep(200)
    # 如果所有重试次数用尽且未成功，则返回None和(0, 0)
    return None, (0, 0)
def ShowImg(image):
    plt.imshow(image)
    plt.show()

# 用于在指定的图像区域中查找模板图像的位置
# image: 要搜索的图像
# template: 模板图像
# region: 可选参数，表示在图像中要进行模板匹配的区域，默认为 None
# confidence: 匹配的置信度阈值，默认为 0.8
def LocateOnImage(image, template, region=None, confidence=0.8):
    # 如果提供了region参数，则解包region为(x, y, w, h)，表示要搜索的区域的左上角坐标 (x, y)、宽度 w 和高度 h
    if region is not None:
        x, y, w, h = region
        # 使用切片操作从image中提取指定的区域
        imgShape = image.shape
        image = image[y:y + h, x:x + w, :]
    # 使用OpenCV在image中搜索template图像。匹配方法使用归一化的相关系数匹配方法 (cv2.TM_CCOEFF_NORMED)
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    # 使用minMaxLoc函数找到匹配结果矩阵res中的匹配度最高的位置
    _, _, _, maxLoc = cv2.minMaxLoc(res)
    # 检查匹配结果矩阵res中是否有任何值大于或等于置信度阈值confidence
    if (res >= confidence).any():
        # 如果存在满足条件的匹配，返回匹配位置的坐标
        # 如果指定了region，则返回的是相对于整个图像的坐标，需要加上区域的起始坐标(region[0], region[1]是模板图像在区域中的左上角坐标)
        return region[0] + maxLoc[0], region[1] + maxLoc[1]
    else:
        # 如果没有匹配度满足条件，则返回 None
        return None

# 用于在屏幕截图中查找模板图像的位置
# templateName: 模板图像的名称，用于从PicsCV中获取模板图像
# region: 搜索区域，表示在图像中要进行模板匹配的区域
# confidence: 匹配的置信度阈值，默认为 0.8
# img: 可选参数，如果提供了图像，则在该图像中查找模板，而不是在屏幕截图中查找。
def LocateOnScreen(templateName, region, confidence=0.8, img=None):
    # 如果提供了img参数，则将其赋值给image
    if img is not None:
        image = img
    # 如果没有提供img参数，则调用self.Screenshot()方法截取屏幕截图，并将截图赋值给image
    else:
        image, _ = Screenshot()
    # 将PIL.Image对象image转换为NumPy数组，然后将颜色空间从RGB转换为BGR，以便OpenCV可以处理
    imgcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    # 调用LocateOnImage函数，在图像imgcv中查找模板图像
    return LocateOnImage(imgcv, PicsCV[templateName], region=region, confidence=confidence)


Handle = win32gui.FindWindow(None, "Apex Legends")
# 模拟鼠标左键点击，接受一个参数pos，表示要点击的位置坐标
def LeftClick(pos):
    RealRate = (1280, 720)
    # 将传入的位置坐标pos根据屏幕分辨率和实际比例进行转换，计算出在窗口中的相对位置 (x, y)
    x = int((pos[0] / 1280) * RealRate[0])
    y = int((pos[1] / 720) * RealRate[1])

    # 获取窗口的左上角坐标 (left, top)，并将相对位置(x, y)转换为绝对位置 (m, n)
    left, top, _, _ = win32gui.GetWindowRect(Handle)
    m, n = int(left + x+20), int(top + y+45)
    # 将鼠标移动到计算得到的绝对位置(m, n)，即窗口内部的点击位置
    win32api.SetCursorPos((m, n))
    QThread.msleep(1000)

    # 模拟左键点击
    pydirectinput.leftClick()
    # mouse_down()
    # QThread.msleep(200)
    # mouse_up()

# 用于在屏幕截图或给定图像中查找模板图像的位置，并在该位置执行点击操作
def ClickOnImage(templateName, region=None, confidence=0.8, img=None):
    if img is not None:
        image = img
    else:
        image, _ = Screenshot()
    imgcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    result = LocateOnImage(imgcv, PicsCV[templateName], region=region, confidence=confidence)

    if result is not None:
        LeftClick(result)

# 用于在屏幕截图或给定图像中查找模板图像的位置，并在该位置执行点击操作
def FindOnImage(templateName, region=None, confidence=0.8, img=None):
    if img is not None:
        image = img
    else:
        image, _ = Screenshot()
    imgcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    result = LocateOnImage(imgcv, PicsCV[templateName], region=region, confidence=confidence)

    if result is not None:
        return result

# 单击键盘
def press_key(key):
    pydirectinput.keyDown(key)
    QThread.msleep(50)
    pydirectinput.keyUp(key)
    QThread.msleep(1000)

# 长按键盘
def long_press_key(key):
    pydirectinput.keyDown(key)
    QThread.msleep(2000)
    pydirectinput.keyUp(key)
    QThread.msleep(1000)

def long_press_key2(key):
    pydirectinput.keyDown(key)
    QThread.msleep(5000)
    pydirectinput.keyUp(key)
    QThread.msleep(1000)

def game_run():
    # 往前
    long_press_key2('w')
    QThread.msleep(1000)

    # 攻击
    pydirectinput.leftClick()
    QThread.msleep(200)
    pydirectinput.leftClick()
    QThread.msleep(200)
    pydirectinput.leftClick()
    QThread.msleep(1000)

    # 跳
    press_key('space')
    QThread.msleep(500)
    press_key('space')

    # 技能Q
    press_key('q')
    QThread.msleep(1000)

    # 技能Z
    press_key('z')
    QThread.msleep(200)
    pydirectinput.leftClick()
    QThread.msleep(1000)

    # 往左
    long_press_key('a')
    QThread.msleep(1000)

    # 往右
    long_press_key('d')
    QThread.msleep(1000)

    # 往后
    long_press_key('s')
    QThread.msleep(1000)

is_run = True
def start():
    print("开始匹配...")
    # 获取窗口焦点
    try:
        win32gui.SetForegroundWindow(Handle)
    except Exception as e:
        print(e)
    QThread.msleep(1000)

    while is_run:
        if not is_run:
            break
        # 准备开始匹配
        ClickOnImage("zunbei", region=(0, 0, 1920, 1080))
        if FindOnImage("fhdt", region=(0, 0, 1920, 1080)) is not None or FindOnImage("jixu", region=(0, 0, 1920, 1080)) is not None:
            press_key('space')
        if FindOnImage("catczdt", region=(0, 0, 1920, 1080)) is not None:
            long_press_key('space')
        if FindOnImage("xuebao", region=(0, 0, 1920, 1080)) is not None:
            game_run()
        QThread.msleep(2000)

def stop():
    print("结束脚本")
    os._exit(1)  # 退出脚本


class MyPyQT_Form(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(MyPyQT_Form, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint |    # 使能最小化按钮
                            QtCore.Qt.WindowCloseButtonHint #|       # 使能关闭按钮
                            #QtCore.Qt.WindowStaysOnTopHint)         # 窗体总在最前端
                            )
        self.setFixedSize(self.width(), self.height())              # 固定窗体大小
        self.setWindowIcon(QIcon('favicon.ico'))
        self.is_run = True

        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.loginButton.clicked.connect(self.login)  # 按下登录按钮
        self.runButton.clicked.connect(self.start_worker_thread)  # 按下运行按钮
        self.stopButton.clicked.connect(self.on_task_finished)  # 按下停止按钮

        self.timer_count = 0
        self.timer = QTimer(self)

        self.start_time = QTime.currentTime()

        self.worker_thread = WorkerThread()  # 创建工作线程

        window_pale = QtGui.QPalette()
        self.setPalette(window_pale)

        self.card1 = ""  # 卡密保存处理
        try:
            with open('card.txt', 'r') as file:
                lines = file.readlines()
                if lines:
                    self.card1 = lines[0].strip()  # 读取文件的第一行并去除首尾空白字符
        except Exception as e:
            print(e)
        if self.card1 != "":
            self.CardEdit.setText(self.card1)
    def start_worker_thread(self):
        # 启动工作线程
        self.worker_thread.start()
        # 禁用按钮，避免重复点击
        self.runButton.setEnabled(False)

    def on_task_finished(self):
        # 任务完成后的处理，比如重新启用按钮
        self.runButton.setEnabled(True)
        stop()

    def update_time(self):
        elapsed_seconds = self.start_time.elapsed() // 1000  # Time elapsed in seconds
        days = elapsed_seconds // (24 * 3600)
        hours = (elapsed_seconds % (24 * 3600)) // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        time_str = f"{days}天{hours}时{minutes}分{seconds}秒"
        self.yxsjlabel.setText(time_str)

    def keyPressEvent(self, event):
        # 按下 F9 键时退出软件
        if event.key() == Qt.Key_F9:
            stop()
    def login(self):

        passWordCar = self.CardEdit.text().strip()
        pjysdk.on_heartbeat_failed = on_heartbeat_failed  # 设置心跳失败回调函数
        device_id = str(uuid.getnode())
        pjysdk.set_device_id(device_id)
        pjysdk.set_card(passWordCar)  # 设置卡密pip
        ret = pjysdk.card_login()  # 卡密登录
        # notice = pjysdk.get_software_notice()  # 获取软件通知
        try:
            # 尝试执行登录操作，如果登录失败，会抛出异常
            # 这里的代码应该包括登录逻辑
            if ret["code"] != 0:  # 登录失败
                raise Exception(ret.get("message", "登录失败"))
            else:
                QMessageBox.information(self, "登录成功", "到期时间：" + ret["result"]["expires"])
                self.daoqilabel.setText(ret["result"]["expires"])
                self.runButton.setEnabled(True)
                self.stopButton.setEnabled(True)
                new_data = f"{passWordCar}\n"
                with open('card.txt', 'w') as file:  # 使用 'w' 模式会清空文件内容
                    file.write(new_data)

                self.timer.start(1000)  # Update every second
                self.timer.timeout.connect(self.update_time)
        except Exception as e:
            # 捕获异常并处理登录失败的情况
            error_message = str(e)
            print(e)
            if error_message == "时间戳大于当前服务器时间":
                QMessageBox.critical(self, "登录失败", error_message + "，请重新校准本地时间！")
                os._exit(1)  # 退出脚本
            elif error_message == "签名已过期":
                QMessageBox.critical(self, "登录失败", error_message + "，请重新校准本地时间！")
                os._exit(1)  # 退出脚本
            else:
                QMessageBox.critical(self, "登录失败", error_message)
                os._exit(1)  # 退出脚本

class WorkerThread(QThread):
    task_finished = pyqtSignal()  # 定义任务完成的信号

    def __init__(self, parent=None):
        super(WorkerThread, self).__init__(parent)
    def run(self):
        # 在这里执行耗时操作，比如你的game_run()函数
        start()
        # 发送任务完成信号
        self.task_finished.emit()

if __name__ == '__main__':
    os.environ["GIT_PYTHON_REFRESH"] = 'quiet'

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    border: 2px solid #2980b9;
                    border-radius: 5px;
                    color: white;
                    padding: 2px 4px;
                }

                QPushButton:hover {
                    background-color: #2980b9;
                    border: 2px solid #3498db;
                }

                QComboBox {
                    background-color: white;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    padding: 4px;
                }

                QComboBox:drop-down {
                    border: 0;
                }

                QComboBox QAbstractItemView:item {
                    height: 30px;
                    font-weight: normal;
                }

                QLabel {
                    color: #3498db;
                }
            """)
    my_pyqt_form = MyPyQT_Form()
    my_pyqt_form.show()
    sys.exit(app.exec_())

