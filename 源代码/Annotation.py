# -*- coding: utf-8 -*-

"""
================================================================================
模块: Annotation.py
功能: 手写批注功能相关类
描述: 
    - AnnotationItem类：表示手写绘制的批注路径项
    - HandwritingDialog类：手写模式设置对话框（笔/橡皮擦模式选择）
================================================================================
"""

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *      # 导入Qt图形界面相关的类（QPen, QColor, QPainterPath等）
from PyQt5.QtCore import *     # 导入Qt核心功能相关的类
from PyQt5.QtWidgets import *  # 导入Qt窗口部件相关的类（QDialog, QGraphicsPathItem等）


# ============================================================================
# AnnotationItem类：批注绘制项
# ============================================================================
class AnnotationItem(QGraphicsPathItem):
    """
    批注绘制项类，用于在思维导图上绘制自由路径（手写批注）
    
    功能:
    - 继承自QGraphicsPathItem，表示一个可绘制的路径图形项
    - 用于存储和显示手写绘制的批注路径
    - 支持自定义画笔样式（颜色、宽度等）
    
    属性:
    - path: 绘制的路径（QPainterPath对象）
    - pen: 画笔样式（颜色、宽度、线型等）
    """
    
    def __init__(self, path=None, pen=None, *args, **kwargs):
        """
        初始化批注项对象
        
        参数:
        - path: 绘制的路径（QPainterPath对象），如果为None则创建空路径
        - pen: 画笔样式（QPen对象），如果为None则使用默认样式
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(AnnotationItem, self).__init__(*args, **kwargs)
        
        # ====================================================================
        # 设置绘制路径
        # ====================================================================
        if path:
            # 如果提供了路径，则使用提供的路径
            self.setPath(path)
        else:
            # 否则创建空路径（后续可以添加路径点）
            self.setPath(QPainterPath())
        
        # ====================================================================
        # 设置画笔样式
        # ====================================================================
        if pen:
            # 如果提供了画笔样式，则使用提供的样式
            self.setPen(pen)
        else:
            # 否则使用默认笔样式
            # 颜色：粉色(255, 107, 181)，宽度：3像素，实线，圆角端点，圆角连接
            default_pen = QPen(QColor(255, 107, 181), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            self.setPen(default_pen)
        
        # ====================================================================
        # 设置图形项的属性
        # ====================================================================
        # 批注项应该在节点之上，但低于选择框
        # Z值100确保批注显示在节点（Z值通常为0）之上，但在选择框（Z值更高）之下
        self.setZValue(100)
        # 允许被选中（用于橡皮擦删除功能）
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # 批注不应该被移动（保持绘制时的位置）
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


# ============================================================================
# HandwritingDialog类：手写设置对话框
# ============================================================================
class HandwritingDialog(QDialog):
    """
    手写设置对话框类，用于配置手写模式的参数
    
    功能:
    - 提供笔模式和橡皮擦模式的选择
    - 设置画笔颜色（仅在笔模式下）
    - 设置画笔粗细（宽度）
    - 返回用户选择的设置
    
    属性:
    - mode: 模式类型（'pen' 或 'eraser'）
    - color: 画笔颜色（仅笔模式使用）
    - width: 画笔粗细（像素）
    """
    
    def __init__(self, parent=None, theme='Light'):
        """
        初始化手写设置对话框
        
        参数:
        - parent: 父窗口对象，默认为None
        - theme: 主题名称，'Light'（浅色）、'Dark'（深色）、'Black & White'（黑白），默认为'Light'
        """
        # 调用父类构造函数
        super().__init__(parent)
        # 保存主题信息
        self.theme = theme
        # 设置对话框标题
        self.setWindowTitle('Handwriting Settings')
        # 设置窗口标志：对话框模式，显示标题栏和关闭按钮
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        # 设置为模态对话框（阻止用户与父窗口交互直到对话框关闭）
        self.setModal(True)
        
        # ====================================================================
        # 初始化默认设置
        # ====================================================================
        self.mode = 'pen'  # 模式：'pen'（笔）或 'eraser'（橡皮擦）
        # 根据主题设置默认颜色
        if theme == 'Light':
            self.color = QColor(255, 107, 181)  # 默认粉色（#FF6BB5）
        elif theme == 'Dark':
            self.color = QColor(100, 150, 200)  # 深色主题：亮蓝色
        else:  # Black & White
            self.color = QColor(120, 120, 120)  # 黑白主题：中灰色
        self.width = 3  # 默认画笔宽度（像素）
        
        # 初始化用户界面
        self.initUI()
        # 根据主题应用样式表
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()
    
    def initUI(self):
        """
        初始化用户界面
        
        功能:
        - 创建模式选择区域（笔/橡皮擦）
        - 创建颜色选择区域（仅在笔模式下启用）
        - 创建粗细选择滑块
        - 创建确定和取消按钮
        """
        # ====================================================================
        # 创建主布局（垂直布局）
        # ====================================================================
        layout = QVBoxLayout()
        
        # ====================================================================
        # 模式选择区域
        # ====================================================================
        mode_group = QGroupBox('Mode')  # 创建分组框
        mode_layout = QHBoxLayout()     # 水平布局
        
        # 创建"笔"单选按钮，默认选中
        self.pen_radio = QRadioButton('Pen')
        self.pen_radio.setChecked(True)
        # 连接切换信号到处理函数
        self.pen_radio.toggled.connect(self.onModeChanged)
        mode_layout.addWidget(self.pen_radio)
        
        # 创建"橡皮擦"单选按钮
        self.eraser_radio = QRadioButton('Eraser')
        # 连接切换信号到处理函数
        self.eraser_radio.toggled.connect(self.onModeChanged)
        mode_layout.addWidget(self.eraser_radio)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # ====================================================================
        # 颜色选择区域（仅在笔模式下显示）
        # ====================================================================
        self.color_group = QGroupBox('Color')
        color_layout = QHBoxLayout()
        
        # 创建颜色选择按钮
        self.color_button = QPushButton()
        self.color_button.setFixedSize(60, 30)  # 固定按钮大小
        self.updateColorButton()  # 更新按钮显示当前颜色
        # 点击按钮时打开颜色选择对话框
        self.color_button.clicked.connect(self.chooseColor)
        color_layout.addWidget(self.color_button)
        
        # 创建颜色标签（显示颜色十六进制值）
        self.color_label = QLabel('#FF6BB5')
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()  # 添加弹性空间
        
        self.color_group.setLayout(color_layout)
        layout.addWidget(self.color_group)
        
        # ====================================================================
        # 粗细选择区域
        # ====================================================================
        width_group = QGroupBox('Width')
        width_layout = QVBoxLayout()
        
        # 创建水平滑块（范围1-20，默认值3）
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setMinimum(1)   # 最小值：1像素
        self.width_slider.setMaximum(20)  # 最大值：20像素
        self.width_slider.setValue(3)     # 默认值：3像素
        # 连接值改变信号到处理函数
        self.width_slider.valueChanged.connect(self.onWidthChanged)
        width_layout.addWidget(self.width_slider)
        
        # 创建宽度标签（显示当前宽度值）
        self.width_label = QLabel('3 px')
        width_layout.addWidget(self.width_label)
        
        width_group.setLayout(width_layout)
        layout.addWidget(width_group)
        
        # ====================================================================
        # 按钮区域
        # ====================================================================
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 在按钮前添加弹性空间（右对齐按钮）
        
        # 确定按钮：接受对话框并返回设置
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)  # 调用accept()关闭对话框并返回Accepted
        button_layout.addWidget(ok_button)
        
        # 取消按钮：取消对话框
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)  # 调用reject()关闭对话框并返回Rejected
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # ====================================================================
        # 设置对话框布局和大小
        # ====================================================================
        self.setLayout(layout)
        self.resize(300, 200)  # 设置对话框初始大小
    
    def applyCuteStyle(self):
        """应用可爱风格"""
        style = """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
                background: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QRadioButton {
                font-size: 11pt;
                color: #5A5A5A;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator::unchecked {
                border: 2px solid #FFB6D9;
                border-radius: 9px;
                background: #FFFFFF;
            }
            QRadioButton::indicator::checked {
                border: 2px solid #FF8CC8;
                border-radius: 9px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #5A5A5A;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QSlider::groove:horizontal {
                background: #FFE4F0;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF8CC8);
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QLabel {
                color: #5A5A5A;
                font-weight: bold;
            }
        """
        self.setStyleSheet(style)
    
    def applyDarkStyle(self):
        """应用深色主题样式"""
        style = """
            QDialog {
                background: #2B2B2B;
                color: #FFFFFF;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
                background: #3C3C3C;
                color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #FFFFFF;
            }
            QRadioButton {
                font-size: 11pt;
                color: #FFFFFF;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator::unchecked {
                border: 2px solid #555555;
                border-radius: 9px;
                background: #3C3C3C;
            }
            QRadioButton::indicator::checked {
                border: 2px solid #777777;
                border-radius: 9px;
                background: #555555;
            }
            QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QPushButton:pressed {
                background: #666666;
            }
            QSlider::groove:horizontal {
                background: #3C3C3C;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #555555;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: #666666;
            }
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
            }
        """
        self.setStyleSheet(style)
    
    def applyBlackWhiteStyle(self):
        """应用黑白主题样式"""
        style = """
            QDialog {
                background: #FFFFFF;
                color: #000000;
            }
            QGroupBox {
                font-weight: normal;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 10px;
                background: #FFFFFF;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #000000;
            }
            QRadioButton {
                font-size: 11pt;
                color: #000000;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator::unchecked {
                border: 1px solid #CCCCCC;
                border-radius: 9px;
                background: #FFFFFF;
            }
            QRadioButton::indicator::checked {
                border: 1px solid #999999;
                border-radius: 9px;
                background: #E0E0E0;
            }
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
            }
            QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
            QSlider::groove:horizontal {
                background: #E0E0E0;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #CCCCCC;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: #999999;
            }
            QLabel {
                color: #000000;
                font-weight: normal;
            }
        """
        self.setStyleSheet(style)
    
    def onModeChanged(self):
        """
        模式改变时的处理函数
        
        功能:
        - 根据选择的单选按钮更新模式
        - 在笔模式下启用颜色选择，在橡皮擦模式下禁用颜色选择
        """
        if self.pen_radio.isChecked():
            # 笔模式：启用颜色选择功能
            self.mode = 'pen'
            self.color_group.setEnabled(True)
        else:
            # 橡皮擦模式：禁用颜色选择功能（橡皮擦不需要颜色）
            self.mode = 'eraser'
            self.color_group.setEnabled(False)
    
    def chooseColor(self):
        """
        打开颜色选择对话框并选择颜色
        
        功能:
        - 弹出Qt颜色选择对话框
        - 如果用户选择了有效颜色，则更新当前颜色并刷新显示
        """
        # 打开颜色选择对话框，传入当前颜色作为初始值
        color = QColorDialog.getColor(self.color, self, 'Choose Pen Color')
        if color.isValid():  # 检查用户是否选择了有效颜色（而不是点击取消）
            # 更新当前颜色
            self.color = color
            # 更新颜色按钮的显示
            self.updateColorButton()
            # 更新颜色标签的文本（显示颜色的十六进制值，大写）
            self.color_label.setText(color.name().upper())
    
    def updateColorButton(self):
        """
        更新颜色按钮的显示
        
        功能:
        - 创建一个与当前颜色相同的图标
        - 将图标设置到颜色按钮上，让用户直观看到当前选择的颜色
        """
        # 创建一个小尺寸的像素图
        pixmap = QPixmap(60, 30)
        # 用当前颜色填充像素图
        pixmap.fill(self.color)
        # 将像素图设置为按钮的图标
        self.color_button.setIcon(QIcon(pixmap))
    
    def onWidthChanged(self, value):
        """
        滑块值改变时的处理函数
        
        参数:
        - value: 滑块的新值（画笔宽度，单位：像素）
        
        功能:
        - 更新当前宽度值
        - 更新宽度标签的显示文本
        """
        # 更新当前宽度值
        self.width = value
        # 更新标签显示（格式：数字 + " px"）
        self.width_label.setText(f'{value} px')
    
    def getSettings(self):
        """
        获取用户选择的设置
        
        返回:
        - dict: 包含模式、颜色、宽度的字典
        
        功能:
        - 返回用户在当前对话框中选择的所有设置
        - 用于传递给场景以启用手写模式
        """
        return {
            'mode': self.mode,      # 模式：'pen' 或 'eraser'
            'color': self.color,    # 画笔颜色（QColor对象）
            'width': self.width     # 画笔宽度（整数，单位：像素）
        }
