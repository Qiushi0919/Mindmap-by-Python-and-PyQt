"""
================================================================================
模块: Component.py
功能: 各种UI组件和辅助窗口的实现
描述: 
    - TodoListPixmapItem: 自定义的待办事项图片项
    - MySlider: 自定义滑块控件（用于缩放视图）
    - Note: 备注编辑窗口
    - Link: 链接编辑窗口
    - TodoList: 待办事项列表对话框
================================================================================
"""

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *      # 导入Qt图形界面相关的类
from PyQt5.QtWidgets import *  # 导入Qt窗口部件相关的类
from PyQt5.QtCore import *     # 导入Qt核心功能相关的类

# ============================================================================
# 导入自定义模块
# ============================================================================
from Config import *  # 导入配置常量（如NOTE_SIZE, LINK_SIZE等）


class TodoListPixmapItem(QGraphicsPixmapItem):
    """自定义的 TodoList 图片项，允许移动和选择，但禁用缩放"""
    
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        # 允许移动和选择，但不显示选择框（通过重写 paint 实现）
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
    
    def paint(self, painter, option, widget=None):
        """重写绘制方法，不绘制默认的选择框"""
        # 创建一个不包含选择状态的选项
        new_option = QStyleOptionGraphicsItem(option)
        new_option.state &= ~QStyle.State_Selected  # 移除选中状态标志
        super().paint(painter, new_option, widget)


class MySlider(QSlider):
    """ReWrite for QSlider

    Control View Scale
    Due to slide time delay, start a timer. 

    Attributes:
        view: QGraphicsView对象
    """
    def __init__(self, view, *args, **kwargs):
        super(MySlider, self).__init__(*args, **kwargs)
        self.view = view
        self.last_val = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.scaleView)

    def scaleView(self):
        print('after value: ', self.value())
        self.view.scale(self.value()/self.last_val, self.value()/self.last_val)
        self.timer.stop()

    def mousePressEvent(self, e):
        """record last time value"""
        print('last value: ', self.value())
        self.last_val = self.value()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        print('value:', self.value())
        self.timer.start(500)


class Note(QMainWindow):
    """New a Note SubWindow

    new a window under activateNode

    Signals:
        note: close Note Window send note content
        noteChange: Note Window text Change
    """
    note = pyqtSignal(str)
    noteChange = pyqtSignal()

    def __init__(self, *args, theme='Light', **kwargs):
        super(Note, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.boldCheck = True
        self.italicCheck = True
        self.underlineCheck = True
        self.theme = theme

        # 根据主题应用样式
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()

        self.toolbar = self.addToolBar('toolbar')

        bold_action = QAction('B', self)
        bold_action.triggered.connect(self.bold)
        self.toolbar.addAction(bold_action)

        skew_action = QAction('I', self)
        skew_action.triggered.connect(self.skew)
        self.toolbar.addAction(skew_action)

        underline_action = QAction('U', self)
        underline_action.triggered.connect(self.underline)
        self.toolbar.addAction(underline_action)

        self.textEdit = QTextEdit(self)
        self.textEdit.textChanged.connect(self.text_changed)

        # 创建OK按钮
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.handle_ok)

        # 创建布局
        vb = QVBoxLayout()
        vb.addWidget(self.textEdit)
        vb.addWidget(self.okButton)

        w = QWidget()
        w.setLayout(vb)
        self.setCentralWidget(w)

        self.resize(*NOTE_SIZE)
    
    def applyCuteStyle(self):
        """应用可爱风格"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 3px solid #FFB6D9;
                border-radius: 15px;
            }
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                border: none;
                border-radius: 8px;
                padding: 4px;
            }
            QToolButton {
                background: #FFFFFF;
                border: 2px solid #FFB6D9;
                border-radius: 6px;
                padding: 4px 8px;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 10pt;
                min-width: 30px;
            }
            QToolButton:hover {
                background: #FFB6D9;
                color: #FFFFFF;
            }
            QTextEdit {
                background: #FFFFFF;
                border: 2px solid #FFB6D9;
                border-radius: 10px;
                padding: 8px;
                color: #5A5A5A;
                font-size: 10pt;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                border: 2px solid #FF8CC8;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9EC7, stop:1 #FF8CC8);
                border: 2px solid #FF6BB5;
            }
            QPushButton:pressed {
                background: #FF8CC8;
            }
        """)
    
    def applyDarkStyle(self):
        """应用深色主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #2B2B2B;
                border: 3px solid #555555;
                border-radius: 15px;
            }
            QToolBar {
                background: #3C3C3C;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }
            QToolButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 4px 8px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
                min-width: 30px;
            }
            QToolButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QToolButton:pressed {
                background: #666666;
            }
            QTextEdit {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 8px;
                color: #FFFFFF;
                font-size: 10pt;
            }
            QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QPushButton:pressed {
                background: #666666;
            }
        """)
    
    def applyBlackWhiteStyle(self):
        """应用黑白主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QToolBar {
                background: #F5F5F5;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 4px 8px;
                color: #000000;
                font-weight: normal;
                font-size: 10pt;
                min-width: 30px;
            }
            QToolButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QToolButton:pressed {
                background: #E0E0E0;
            }
            QTextEdit {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 8px;
                color: #000000;
                font-size: 10pt;
            }
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
    
    def setTheme(self, theme):
        """设置主题并应用样式"""
        self.theme = theme
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()

    def changeFormat(self, fmt):
        cursor = self.textEdit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)

    def bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if self.boldCheck else QFont.Normal)
        self.changeFormat(fmt)
        self.boldCheck = not self.boldCheck

    def skew(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italicCheck)
        self.changeFormat(fmt)
        self.italicCheck = not self.italicCheck

    def underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underlineCheck)
        self.changeFormat(fmt)
        self.underlineCheck = not self.underlineCheck

    def handle_addnote(self, x, y, note):
        self.move(x, y)
        self.textEdit.setText(note)
        if not self.isVisible():
            self.show()

    def handle_ok(self):
        """点击OK按钮时保存备注"""
        self.note.emit(self.textEdit.toPlainText())
        self.close()

    def handle_close(self):
        self.note.emit(self.textEdit.toPlainText())
        self.close()

    def text_changed(self):
        self.noteChange.emit()


class Link(QMainWindow):
    """New a Link Window

    new a Link Window under activateNode

    Signals:
        link: close Link Window send link content
        linkChange: Link Window text Change
    """
    link = pyqtSignal(str)
    linkChange = pyqtSignal()

    def __init__(self, *args, theme='Light', **kwargs):
        super(Link, self).__init__(*args, **kwargs)
        self.onMode = False
        self.theme = theme

        self.setWindowFlags(Qt.FramelessWindowHint)

        # 根据主题应用样式
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()

        self.label = QLabel(self)
        self.label.setText('超链接')

        self.lineEdit = QLineEdit(self)

        vb = QVBoxLayout()
        vb.addWidget(self.label)
        vb.addWidget(self.lineEdit)

        w = QWidget()
        w.setLayout(vb)
        
        self.setCentralWidget(w)
        self.lineEdit.textChanged.connect(self.link_changed)

        self.resize(*LINK_SIZE)
    
    def applyCuteStyle(self):
        """应用可爱风格"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 3px solid #FFB6D9;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 11pt;
                padding: 4px;
            }
            QLineEdit {
                background: #FFFFFF;
                border: 2px solid #FFB6D9;
                border-radius: 10px;
                padding: 6px;
                color: #5A5A5A;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #FF8CC8;
            }
        """)
    
    def applyDarkStyle(self):
        """应用深色主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #2B2B2B;
                border: 3px solid #555555;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11pt;
                padding: 4px;
            }
            QLineEdit {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 6px;
                color: #FFFFFF;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #666666;
            }
        """)
    
    def applyBlackWhiteStyle(self):
        """应用黑白主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QLabel {
                background: transparent;
                color: #000000;
                font-weight: normal;
                font-size: 11pt;
                padding: 4px;
            }
            QLineEdit {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                color: #000000;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #999999;
            }
        """)
    
    def setTheme(self, theme):
        """设置主题并应用样式"""
        self.theme = theme
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()

    def handle_addLink(self, x, y, link):
        self.move(x, y)
        self.lineEdit.setText(link)
        if not self.isVisible():
            self.onMode = True
            self.show()

    def handle_close(self):
        if self.onMode:
            self.onMode = False
            self.link.emit(self.lineEdit.text())
            self.close()
        
    def link_changed(self):
        self.linkChange.emit()


class AnnotationWindow(QMainWindow):
    """New an Annotation Window

    new a window under activateNode

    Signals:
        annotation: close Annotation Window send annotation content
        annotationChange: Annotation Window text Change
    """
    annotation = pyqtSignal(str)
    annotationChange = pyqtSignal()

    def __init__(self, *args, theme='Light', **kwargs):
        super(AnnotationWindow, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.theme = theme
        self.onMode = False  # 标志：是否在编辑模式下（类似Link窗口）
        
        # 获取翻译函数：从parent获取，如果parent有tr方法则使用，否则使用默认
        parent = args[0] if args else None
        self.tr_func = getattr(parent, 'tr', lambda x: x) if parent else lambda x: x

        # 根据主题应用样式
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()

        self.label = QLabel(self)
        self.label.setText(self.tr_func('Annotation'))

        self.textEdit = QTextEdit(self)
        self.textEdit.setPlaceholderText(self.tr_func('Please enter annotation content...'))
        # 设置批注文本框高度为100像素，与NodeInfoWindow保持一致
        self.textEdit.setFixedHeight(100)

        # 创建OK按钮
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.handle_ok)

        vb = QVBoxLayout()
        vb.addWidget(self.label)
        vb.addWidget(self.textEdit)
        vb.addWidget(self.okButton)

        w = QWidget()
        w.setLayout(vb)
        
        self.setCentralWidget(w)
        self.textEdit.textChanged.connect(self.annotation_changed)

        # 使用NODE_INFO_SIZE以保持与NodeInfoWindow一致的尺寸
        from Config import NODE_INFO_SIZE
        self.resize(*NODE_INFO_SIZE)
    
    def applyCuteStyle(self):
        """应用可爱风格"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 3px solid #FFB6D9;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 11pt;
                padding: 4px;
            }
            QTextEdit {
                background: #FFFFFF;
                border: 2px solid #FFB6D9;
                border-radius: 10px;
                padding: 6px;
                color: #5A5A5A;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 2px solid #FF8CC8;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #FF8CC8;
            }
        """)
    
    def applyDarkStyle(self):
        """应用深色主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #2B2B2B;
                border: 3px solid #555555;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11pt;
                padding: 4px;
            }
            QTextEdit {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 6px;
                color: #FFFFFF;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 2px solid #666666;
            }
            QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QPushButton:pressed {
                background: #666666;
            }
        """)
    
    def applyBlackWhiteStyle(self):
        """应用黑白主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QLabel {
                background: transparent;
                color: #000000;
                font-weight: normal;
                font-size: 11pt;
                padding: 4px;
            }
            QTextEdit {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                color: #000000;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 1px solid #999999;
            }
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
    
    def setTheme(self, theme):
        """设置主题并应用样式"""
        self.theme = theme
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()
    
    def updateLanguage(self):
        """更新窗口文本以匹配当前语言"""
        if hasattr(self, 'label'):
            self.label.setText(self.tr_func('Annotation'))
        if hasattr(self, 'textEdit'):
            self.textEdit.setPlaceholderText(self.tr_func('Please enter annotation content...'))

    def handle_addAnnotation(self, x, y, annotation):
        self.move(x, y)
        # 确保正确设置批注内容（如果annotation是None，设置为空字符串）
        annotation_text = annotation if annotation is not None else ''
        self.textEdit.setPlainText(annotation_text)
        # 无论窗口是否可见，都设置为编辑模式，确保OK按钮可以保存
        self.onMode = True  # 进入编辑模式
        if not self.isVisible():
            self.show()

    def handle_ok(self):
        """点击OK按钮时保存批注"""
        # 点击OK按钮时，无论onMode状态如何，都保存批注
        # 因为用户点击OK就表示想要保存
        self.onMode = False  # 退出编辑模式
        # 获取当前文本内容并发送信号
        annotation_text = self.textEdit.toPlainText()
        self.annotation.emit(annotation_text)
        self.close()

    def handle_close(self):
        # 只有在编辑模式下才发送批注内容（类似Link窗口的逻辑）
        if self.onMode:
            self.onMode = False  # 退出编辑模式
            # 获取当前文本内容并发送信号
            annotation_text = self.textEdit.toPlainText()
            self.annotation.emit(annotation_text)
        self.close()
        
    def annotation_changed(self):
        self.annotationChange.emit()


class NodeInfoWindow(QMainWindow):
    """节点信息窗口 - 批注编辑窗口
    
    当用户点击节点时，显示此窗口，可以查看和编辑批注
    
    Signals:
        annotation: 关闭窗口时发送批注内容
        annotationChange: 批注内容改变时发出
    """
    annotation = pyqtSignal(str)
    annotationChange = pyqtSignal()
    
    def __init__(self, *args, theme='Light', **kwargs):
        super(NodeInfoWindow, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.theme = theme
        self.onMode = False  # 标志：是否在编辑模式下
        
        # 获取翻译函数：从parent获取，如果parent有tr方法则使用，否则使用默认
        parent = args[0] if args else None
        self.tr_func = getattr(parent, 'tr', lambda x: x) if parent else lambda x: x
        
        # 根据主题应用样式
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()
        
        # 创建UI组件
        self.annotation_label = QLabel(self)
        self.annotation_label.setText(self.tr_func('Annotation'))
        
        self.annotation_textEdit = QTextEdit(self)
        self.annotation_textEdit.setPlaceholderText(self.tr_func('Please enter annotation content...'))
        # 设置批注文本框高度为100像素
        self.annotation_textEdit.setFixedHeight(100)
        
        # 创建OK按钮
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.handle_ok)
        
        # 布局
        vb = QVBoxLayout()
        vb.addWidget(self.annotation_label)
        vb.addWidget(self.annotation_textEdit)
        vb.addWidget(self.okButton)
        
        w = QWidget()
        w.setLayout(vb)
        self.setCentralWidget(w)
        
        # 连接信号
        self.annotation_textEdit.textChanged.connect(self.annotation_changed)
        
        self.resize(*NODE_INFO_SIZE)
    
    def applyCuteStyle(self):
        """应用可爱风格"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 3px solid #FFB6D9;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 11pt;
                padding: 4px;
            }
            QTextEdit {
                background: #FFFFFF;
                border: 2px solid #FFB6D9;
                border-radius: 10px;
                padding: 6px;
                color: #5A5A5A;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 2px solid #FF8CC8;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #FF8CC8;
            }
        """)
    
    def applyDarkStyle(self):
        """应用深色主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #2B2B2B;
                border: 3px solid #555555;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11pt;
                padding: 4px;
            }
            QTextEdit {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 6px;
                color: #FFFFFF;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 2px solid #666666;
            }
            QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QPushButton:pressed {
                background: #666666;
            }
        """)
    
    def applyBlackWhiteStyle(self):
        """应用黑白主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QLabel {
                background: transparent;
                color: #000000;
                font-weight: normal;
                font-size: 11pt;
                padding: 4px;
            }
            QTextEdit {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                color: #000000;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 1px solid #999999;
            }
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
    
    def setTheme(self, theme):
        """设置主题并应用样式"""
        self.theme = theme
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()
    
    def updateLanguage(self):
        """更新窗口文本以匹配当前语言"""
        if hasattr(self, 'annotation_label'):
            self.annotation_label.setText(self.tr_func('Annotation'))
        if hasattr(self, 'annotation_textEdit'):
            self.annotation_textEdit.setPlaceholderText(self.tr_func('Please enter annotation content...'))
    
    def handle_showNodeInfo(self, x, y, annotation):
        """显示节点信息窗口，设置批注内容"""
        self.move(x, y)
        # 设置批注内容
        annotation_text = annotation if annotation is not None else ''
        self.annotation_textEdit.setPlainText(annotation_text)
        # 无论窗口是否可见，都设置为编辑模式，确保OK按钮可以保存
        self.onMode = True  # 进入编辑模式
        if not self.isVisible():
            self.show()
    
    def handle_ok(self):
        """点击OK按钮时保存批注"""
        # 点击OK按钮时，无论onMode状态如何，都保存批注
        # 因为用户点击OK就表示想要保存
        self.onMode = False  # 退出编辑模式
        # 获取当前内容
        annotation_text = self.annotation_textEdit.toPlainText()
        # 发送批注内容
        self.annotation.emit(annotation_text)
        self.close()
    
    def handle_close(self):
        """关闭窗口时发送批注内容"""
        if self.onMode:
            self.onMode = False  # 退出编辑模式
            # 获取当前内容
            annotation_text = self.annotation_textEdit.toPlainText()
            # 发送批注内容
            self.annotation.emit(annotation_text)
        self.close()
    
    def getCurrentContent(self):
        """获取当前窗口中的批注内容"""
        return self.annotation_textEdit.toPlainText()
    
    def annotation_changed(self):
        """批注内容改变时发出信号"""
        self.annotationChange.emit()


class TodoList(QDialog):
    """TodoList 对话框，用于编辑待办事项列表"""
    
    def __init__(self, parent=None, theme='Light'):
        super().__init__(parent)
        self.parent_window = parent  # 保存父窗口引用，用于翻译
        # 翻译函数：如果parent有tr方法则使用，否则使用默认
        self.tr_func = getattr(parent, 'tr', lambda x: x) if parent else lambda x: x
        
        self.setWindowTitle(self.tr_func('Todo List'))
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setModal(False)  # 非模态对话框，可以同时操作主窗口
        
        # 保存主题信息
        self.theme = theme
        
        # 待办事项列表
        self.todo_items = []
        # 存储场景和节点引用，用于 finish 功能
        self.scene = None
        self.node = None
        
        self.initUI()
        # 根据主题应用样式
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # 标题
        self.title_label = QLabel(self.tr_func('Todo List'))
        layout.addWidget(self.title_label)
        
        # 待办事项列表
        self.todo_list = QListWidget()
        self.todo_list.setAlternatingRowColors(True)
        # 连接复选框状态改变信号，自动更新删除线
        self.todo_list.itemChanged.connect(self.onItemChanged)
        layout.addWidget(self.todo_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 添加按钮
        add_button = QPushButton(self.tr_func('➕ Add'))
        add_button.clicked.connect(self.addTodoItem)
        button_layout.addWidget(add_button)
        
        # 删除按钮
        delete_button = QPushButton(self.tr_func('🗑️ Delete'))
        delete_button.clicked.connect(self.deleteTodoItem)
        button_layout.addWidget(delete_button)
        
        button_layout.addStretch()
        
        # Finish 按钮
        finish_button = QPushButton(self.tr_func('✨ Finish'))
        finish_button.clicked.connect(self.finishTodoList)
        button_layout.addWidget(finish_button)
        
        # 关闭按钮
        close_button = QPushButton(self.tr_func('Close'))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(400, 500)
    
    def applyCuteStyle(self):
        """应用可爱风格"""
        style = """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
            }
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #5A5A5A;
            }
            QListWidget {
                background: #FFFFFF;
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                color: #5A5A5A;
                font-size: 11pt;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QListWidget::item:alternate {
                background: #FFF5FA;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #5A5A5A;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #FF8CC8;
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
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #FFFFFF;
            }
            QListWidget {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 11pt;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: #555555;
                color: #FFFFFF;
            }
            QListWidget::item:alternate {
                background: #353535;
            }
            QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QPushButton:pressed {
                background: #666666;
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
            QLabel {
                font-size: 16pt;
                font-weight: normal;
                color: #000000;
            }
            QListWidget {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                color: #000000;
                font-size: 11pt;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: #E0E0E0;
                color: #000000;
            }
            QListWidget::item:alternate {
                background: #F5F5F5;
            }
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """
        self.setStyleSheet(style)
    
    def setTheme(self, theme):
        """设置主题并应用样式"""
        self.theme = theme
        if theme == 'Light':
            self.applyCuteStyle()
        elif theme == 'Dark':
            self.applyDarkStyle()
        else:  # Black & White
            self.applyBlackWhiteStyle()
    
    def addTodoItem(self):
        """添加待办事项"""
        text, ok = QInputDialog.getText(self, self.tr_func('Add Todo Item'), self.tr_func('Enter todo item:'))
        if ok and text:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.todo_list.addItem(item)
            self.todo_items.append({'text': text, 'completed': False})
    
    def deleteTodoItem(self):
        """删除选中的待办事项"""
        current_item = self.todo_list.currentItem()
        if current_item:
            row = self.todo_list.row(current_item)
            self.todo_list.takeItem(row)
            if row < len(self.todo_items):
                self.todo_items.pop(row)
    
    def loadTodoItems(self, items):
        """加载待办事项列表"""
        # 暂时断开信号，避免加载时触发
        self.todo_list.itemChanged.disconnect()
        self.todo_list.clear()
        self.todo_items = items if items else []
        for item_data in self.todo_items:
            item = QListWidgetItem(item_data.get('text', ''))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if item_data.get('completed', False):
                item.setCheckState(Qt.Checked)
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                # 根据主题设置颜色
                if self.theme == 'Dark':
                    item.setForeground(QColor('#888888'))
                elif self.theme == 'Black & White':
                    item.setForeground(QColor('#666666'))
                else:  # Light
                    item.setForeground(QColor('#999999'))
            else:
                item.setCheckState(Qt.Unchecked)
                # 根据主题设置颜色
                if self.theme == 'Dark':
                    item.setForeground(QColor('#FFFFFF'))
                elif self.theme == 'Black & White':
                    item.setForeground(QColor('#000000'))
                else:  # Light
                    item.setForeground(QColor('#5A5A5A'))
            self.todo_list.addItem(item)
        # 重新连接信号
        self.todo_list.itemChanged.connect(self.onItemChanged)
    
    def getTodoItems(self):
        """获取待办事项列表"""
        items = []
        for i in range(self.todo_list.count()):
            item = self.todo_list.item(i)
            items.append({
                'text': item.text(),
                'completed': (item.checkState() == Qt.Checked)
            })
        return items
    
    def onItemChanged(self, item):
        """当列表项改变时（包括复选框状态），自动更新删除线"""
        if item.checkState() == Qt.Checked:
            # 已完成 - 添加删除线
            font = item.font()
            font.setStrikeOut(True)
            item.setFont(font)
            # 根据主题设置颜色
            if self.theme == 'Dark':
                item.setForeground(QColor('#888888'))
            elif self.theme == 'Black & White':
                item.setForeground(QColor('#666666'))
            else:  # Light
                item.setForeground(QColor('#999999'))
        else:
            # 未完成 - 移除删除线
            font = item.font()
            font.setStrikeOut(False)
            item.setFont(font)
            # 根据主题设置颜色
            if self.theme == 'Dark':
                item.setForeground(QColor('#FFFFFF'))
            elif self.theme == 'Black & White':
                item.setForeground(QColor('#000000'))
            else:  # Light
                item.setForeground(QColor('#5A5A5A'))
        
        # 更新内部状态
        row = self.todo_list.row(item)
        if row < len(self.todo_items):
            self.todo_items[row]['completed'] = (item.checkState() == Qt.Checked)
    
    def finishTodoList(self):
        """将 todolist 渲染成图片并添加到场景"""
        if not self.scene or not self.node:
            return
        
        # 渲染 todolist 为图片
        pixmap = self.renderTodoListToPixmap()
        
        # 检查节点是否已经有 todolist 图片
        if hasattr(self.node, 'todolist_pixmap_item') and self.node.todolist_pixmap_item:
            # 更新现有图片
            self.node.todolist_pixmap_item.setPixmap(pixmap)
            # 调整位置到节点右侧
            node_rect = self.node.sceneBoundingRect()
            self.node.todolist_pixmap_item.setPos(
                node_rect.right() + 20,
                node_rect.top()
            )
        else:
            # 创建新的图片项（使用自定义类，禁用选择框和缩放）
            pixmap_item = TodoListPixmapItem(pixmap)
            pixmap_item.setZValue(50)  # 在节点之上，但在批注之下
            
            # 设置位置到节点右侧
            node_rect = self.node.sceneBoundingRect()
            pixmap_item.setPos(
                node_rect.right() + 20,
                node_rect.top()
            )
            
            # 添加到场景
            self.scene.addItem(pixmap_item)
            
            # 保存引用到节点
            self.node.todolist_pixmap_item = pixmap_item
        
        # 触发内容改变
        if hasattr(self.scene, 'contentChanged'):
            self.scene.contentChanged.emit()
    
    def renderTodoListToPixmap(self):
        """将 todolist 渲染为图片"""
        # 计算所需尺寸
        items = self.getTodoItems()
        if not items:
            # 如果没有项目，创建一个空的小图片
            pixmap = QPixmap(200, 50)
            # 根据主题设置背景色
            if self.theme == 'Dark':
                pixmap.fill(QColor(40, 40, 40))
            elif self.theme == 'Black & White':
                pixmap.fill(QColor(255, 255, 255))
            else:  # Light
                pixmap.fill(QColor(255, 245, 250))
            return pixmap
        
        # 计算文本尺寸
        font = QFont('Arial', 12)
        font_metrics = QFontMetrics(font)
        max_width = 0
        total_height = 40  # 标题高度
        
        for item_data in items:
            text = item_data['text']
            if item_data['completed']:
                # 已完成项显示删除线
                text = '✓ ' + text
            else:
                text = '☐ ' + text
            width = font_metrics.width(text) + 80  # 增加左右内边距，使外框更宽
            max_width = max(max_width, width)
            total_height += 30
        
        # 增加底部内边距，使外框高度更大
        total_height += 30
        
        # 创建图片（增加最小宽度）
        pixmap = QPixmap(max(max_width, 300), total_height)
        # 根据主题设置背景色
        if self.theme == 'Dark':
            pixmap.fill(QColor(40, 40, 40))
            bg_color = QColor(60, 60, 60)
            border_color = QColor(100, 100, 100)
            title_color = QColor(255, 255, 255)
            text_color = QColor(255, 255, 255)
            completed_color = QColor(150, 150, 150)
        elif self.theme == 'Black & White':
            pixmap.fill(QColor(255, 255, 255))
            bg_color = QColor(255, 255, 255)
            border_color = QColor(200, 200, 200)
            title_color = QColor(0, 0, 0)
            text_color = QColor(0, 0, 0)
            completed_color = QColor(100, 100, 100)
        else:  # Light
            pixmap.fill(QColor(255, 245, 250))
            bg_color = QColor(255, 255, 255)
            border_color = QColor(255, 182, 217)
            title_color = QColor(90, 90, 90)
            text_color = QColor(90, 90, 90)
            completed_color = QColor(153, 153, 153)
        
        # 绘制内容
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景框
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(5, 5, pixmap.width() - 10, pixmap.height() - 10, 8, 8)
        
        # 绘制标题
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        painter.setPen(title_color)
        painter.drawText(20, 45, self.tr_func('Todo List'))
        
        # 绘制待办事项
        y = 80
        painter.setFont(font)
        for item_data in items:
            text = item_data['text']
            if item_data['completed']:
                # 已完成项：显示删除线
                painter.setPen(completed_color)
                font_strike = QFont(font)
                font_strike.setStrikeOut(True)
                painter.setFont(font_strike)
                painter.drawText(20, y, '✓ ' + text)
            else:
                # 未完成项
                painter.setPen(text_color)
                painter.setFont(font)
                painter.drawText(20, y, '☐ ' + text)
            y += 30
        
        painter.end()
        return pixmap
    
    def setSceneAndNode(self, scene, node):
        """设置场景和节点引用"""
        self.scene = scene
        self.node = node