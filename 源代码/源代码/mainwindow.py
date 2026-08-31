# -*- coding: utf-8 -*-

"""
================================================================================
模块: mainwindow.py
功能: 思维导图应用程序的主窗口实现
描述: 
    - MainWindow类：应用程序的主窗口，包含菜单栏、工具栏、状态栏等
    - CustomGraphicsView类：自定义的图形视图，支持虚线框选和手写模式
    - 实现文件操作（新建、打开、保存、导出等）
    - 实现编辑操作（撤销、重做、复制、粘贴、删除等）
    - 实现界面样式设置
    - 管理与场景（Graph）的交互
================================================================================
"""

# ============================================================================
# 导入标准库模块
# ============================================================================
import os   # 操作系统相关功能（文件路径处理）
import sys  # 系统相关功能

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *          # 导入Qt图形界面相关的类
from PyQt5.QtWidgets import *      # 导入Qt窗口部件相关的类
from PyQt5.QtCore import *         # 导入Qt核心功能相关的类
from PyQt5.QtPrintSupport import * # 导入Qt打印支持相关类（用于打印功能）

# ============================================================================
# 导入自定义模块
# ============================================================================
from Graph import Graph  # 导入场景类（Graph）
from Component import *  # 导入组件模块（Note, Link, TodoList等）
from Config import *     # 导入配置常量
from Node import Node    # 导入节点类
from Annotation import HandwritingDialog, AnnotationItem  # 导入手写相关类
from AIDialog import AIGenerationDialog, AIGenerationThread
from AIProvider import DEFAULT_MODEL


class CustomGraphicsView(QGraphicsView):
    """自定义 GraphicsView，支持虚线框选"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rubberBandOrigin = QPoint()
        self._rubberBandRect = QRect()
        self._isDragging = False
        self._handwritingMode = False
        self._handwritingModeType = None  # 'pen' 或 'eraser'
        self._theme = 'Black & White'  # 默认黑白主题
        
    def setTheme(self, theme):
        """设置主题"""
        self._theme = theme
        
    def drawRubberBand(self, painter, rubberBandRect):
        """重写绘制橡皮筋选择框，根据主题使用不同颜色的虚线样式"""
        if not rubberBandRect.isValid():
            return
        
        # 根据主题设置颜色
        if self._theme == 'Light':
            # 浅色主题 - 粉色虚线框
            pen_color = QColor(255, 140, 200)  # #FF8CC8
            fill_color = QColor(255, 182, 217, 30)  # #FFB6D9 半透明
        elif self._theme == 'Dark':
            # 深色主题 - 亮蓝色虚线框
            pen_color = QColor(100, 150, 200)  # 亮蓝色
            fill_color = QColor(100, 150, 200, 30)  # 亮蓝色半透明
        else:  # Black & White
            # 黑白主题 - 灰色虚线框
            pen_color = QColor(120, 120, 120)  # 中灰色
            fill_color = QColor(200, 200, 200, 30)  # 浅灰色半透明
        
        pen = QPen(pen_color, 2, Qt.DashLine)
        pen.setDashPattern([6, 4])  # 设置虚线样式：6像素实线，4像素空白
        painter.setPen(pen)
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(rubberBandRect, 4, 4)  # 圆角矩形
    
    def setHandwritingMode(self, enabled, mode_type):
        """设置手写模式状态"""
        self._handwritingMode = enabled
        self._handwritingModeType = mode_type

    def wheelEvent(self, event):
        """Use Ctrl/Command + wheel for smooth canvas zoom."""
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
            current_scale = self.transform().m11()
            target_scale = current_scale * factor
            if 0.2 <= target_scale <= 4.0:
                self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件：记录起始位置"""
        if event.button() == Qt.LeftButton:
            # 如果是在手写模式下，且是笔模式，不显示框选
            if self._handwritingMode and self._handwritingModeType == 'pen':
                # 笔模式下，不处理框选，直接传递给场景
                super().mousePressEvent(event)
                return
            
            # 检查是否点击在 TodoList 图片上
            item = self.itemAt(event.pos())
            from Component import TodoListPixmapItem
            if isinstance(item, TodoListPixmapItem):
                # 如果点击的是 TodoList 图片，不显示框选，直接传递事件
                super().mousePressEvent(event)
                return
            
            # 橡皮擦模式或非手写模式：允许框选
            # 如果点击的是空白区域，准备框选
            if item is None or not isinstance(item, Node):
                # 橡皮擦模式下，开始框选
                if self._handwritingMode and self._handwritingModeType == 'eraser':
                    self._rubberBandOrigin = event.pos()
                    self._isDragging = True
                # 非手写模式下，正常框选节点
                elif not self._handwritingMode:
                    self._rubberBandOrigin = event.pos()
                    self._isDragging = True
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件：更新框选区域"""
        if self._isDragging and event.buttons() & Qt.LeftButton:
            # 计算框选矩形
            self._rubberBandRect = QRect(self._rubberBandOrigin, event.pos()).normalized()
            # 更新视图以重绘虚线框
            self.viewport().update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件：完成框选，选中框内的节点或擦除批注"""
        if event.button() == Qt.LeftButton and self._isDragging:
            self._isDragging = False
            
            # 获取框选区域（场景坐标）
            start_scene = self.mapToScene(self._rubberBandOrigin)
            end_scene = self.mapToScene(event.pos())
            selection_rect = QRectF(start_scene, end_scene).normalized()
            
            # 如果框选区域足够大（避免误触）
            if selection_rect.width() > 5 and selection_rect.height() > 5:
                # 橡皮擦模式：删除框内的批注
                if self._handwritingMode and self._handwritingModeType == 'eraser':
                    items_to_remove = []
                    for item in self.scene().items(selection_rect, Qt.IntersectsItemShape, Qt.DescendingOrder):
                        if isinstance(item, AnnotationItem):
                            # 检查批注是否在框内（使用boundingRect判断）
                            item_rect = item.boundingRect()
                            item_scene_rect = item.mapRectToScene(item_rect)
                            if selection_rect.contains(item_scene_rect):
                                items_to_remove.append(item)
                    
                    # 删除找到的批注
                    for item in items_to_remove:
                        self.scene().removeItem(item)
                        if hasattr(self.scene(), 'AnnotationList') and item in self.scene().AnnotationList:
                            self.scene().AnnotationList.remove(item)
                    
                    if items_to_remove:
                        if hasattr(self.scene(), 'contentChanged'):
                            self.scene().contentChanged.emit()
                # 非手写模式：选中框内的节点
                elif not self._handwritingMode:
                    # 清除之前的选择
                    self.scene().clearSelection()
                    
                    # 选中框内的所有节点
                    for item in self.scene().items(selection_rect, Qt.IntersectsItemShape, Qt.DescendingOrder):
                        if isinstance(item, Node):
                            item.setSelected(True)
            
            # 清除虚线框
            self._rubberBandRect = QRect()
            self.viewport().update()
        
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """重写绘制事件，绘制虚线框"""
        super().paintEvent(event)
        if self._isDragging and not self._rubberBandRect.isNull():
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.Antialiasing)
            self.drawRubberBand(painter, self._rubberBandRect)


class MainWindow(QMainWindow):
    """Main Window

    Show the main window for app

    Signals:
        addNote: (int, int, str) -> (pos_x, pos_y, note_text)
        addLink: (int, int, str) -> (pos_x, pos_y, link_text)
        close_signal: MainWindow close signal
    """
    addNote = pyqtSignal(int, int, str)
    addLink = pyqtSignal(int, int, str)
    close_signal = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        # self.path = None
        self.root = QFileInfo(__file__).absolutePath()
        self.m_contentChanged = False
        self.m_filename = None
        self.m_undoStack = None
        self.m_dockShow = True
        self.m_settings = settings
        self.m_language = 'zh_CN'  # 当前语言：'zh_CN'（中文）或'en_US'（英文）
        self.m_theme = 'Light'  # 默认使用现代浅色概念图主题
        self.m_moveWithSubtree = True  # 移动节点时是否同时移动子树，默认为True
        self._orcarouter_api_key = os.environ.get('ORCAROUTER_API_KEY', '')
        self.ai_thread = None
        self.ai_progress = None
        
        # ====================================================================
        # 翻译字典
        # ====================================================================
        self.translations = {
            'zh_CN': {
                'File': '文件',
                'Edit': '编辑',
                'Insert': '插入',
                'Theme': '主题',
                'Black & White': '黑白',
                'Light': '浅色',
                'Dark': '深色',
                'Language': '语言',
                'Help': '帮助',
                'AI': 'AI',
                'Generate Concept Map': 'AI 生成概念图',
                'OrcaRouter Documentation': 'OrcaRouter 文档',
                'New file': '新建文件',
                'New File': '新建文件',
                'Open file': '打开文件',
                'Open File': '打开文件',
                'Last open file': '最近打开的文件',
                'Save': '保存',
                'Save File': '保存文件',
                'Save as': '另存为',
                'Import from Markdown': '从Markdown导入',
                'Export as': '导出为',
                'PNG': 'PNG',
                'PDF': 'PDF',
                'Print...': '打印...',
                'Quit': '退出',
                'Undo': '撤销',
                'Redo': '重做',
                'Cut': '剪切',
                'Copy': '复制',
                'Paste': '粘贴',
                'Delete': '删除',
                'line manage': '连线管理',
                'note': '备注',
                'link': '链接',
                'Link': '链接',
                'Annotation': '批注',
                'Please enter annotation content...': '请输入批注内容...',
                'icon': '图标',
                'About': '关于',
                'hot key help': '快捷键帮助',
                'Hot Key Help': '快捷键帮助',
                'handwriting': '手写',
                'subtopic': '子主题',
                'relation': '关系',
                'todolist': '待办事项',
                'Todo List': '待办事项列表',
                '➕ Add': '➕ 添加',
                '🗑️ Delete': '🗑️ 删除',
                '✨ Finish': '✨ 完成',
                'Close': '关闭',
                'Add Todo Item': '添加待办事项',
                'Enter todo item:': '请输入待办事项：',
                'Move with subtree': '移动子树',
                'Set Color': '设置颜色',
                'Set Text Color': '设置文本颜色',
                'Image': '图像',
                'Insert Link': '插入链接',
                'Select Image': '选择图像',
                'Enter URL:': '输入URL：',
                # 状态消息
                'Info: add new node !': '信息：已添加新节点！',
                'Info: remove node !': '信息：已删除节点！',
                'Info: move node !': '信息：已移动节点！',
                'Info: editing node !': '信息：正在编辑节点！',
                'Info: Copy Successfully !': '信息：复制成功！',
                'Info: Paste Successfully !': '信息：粘贴成功！',
                'Info: change text color !': '信息：已更改文本颜色！',
                'Info: relation created !': '信息：关系已创建！',
                'Info: relation already exists !': '信息：关系已存在！',
                'Info: select two nodes to create relation !': '信息：请选择两个节点以创建关系！',
                'Info: TodoList image deleted !': '信息：待办事项图片已删除！',
                'View Annotation': '查看批注',
                'Warning: no activate node !': '警告：没有激活的节点！',
                'Warning: Base Node': '警告：根节点',
                'Warning: Bade Node': '警告：无效节点',
                'Error: clipboard has not text content !': '错误：剪贴板没有文本内容！',
                'Error: invalid clipboard content for paste !': '错误：剪贴板内容无效，无法粘贴！',
                'Error: clipboard has no nodes !': '错误：剪贴板没有节点！',
                'change node color': '更改节点颜色',
                'Info: 请至少选中两个节点！': '信息：请至少选中两个节点！',
                'Info: 请至少选中两个节点！': '信息：请至少选中两个节点！',
                'Info: 已创建 {} 条连接线，已删除 {} 条连接线！': '信息：已创建 {} 条连接线，已删除 {} 条连接线！',
                'Info: 已创建 {} 条连接线！': '信息：已创建 {} 条连接线！',
                'Info: 已删除 {} 条连接线！': '信息：已删除 {} 条连接线！',
                'Error: the file is read only !': '错误：文件为只读！',
                'Error: Failed to import Markdown file!': '错误：导入Markdown文件失败！',
                'Info: Markdown file imported successfully!': '信息：Markdown文件导入成功！',
                'Language switched to Chinese': '语言已切换为：中文',
                'Language switched to English': 'Language switched to: English',
                'Topic': '主题',
                'Topic: ': '主题: ',
                'Save MindMap': '保存思维导图',
                'The MindMap has been modified !': '思维导图已被修改！',
                'Do you want to save this file ?': '您想要保存此文件吗？',
                'Save': '保存',
                'Discard': '放弃',
                'Cancel': '取消',
            },
            'en_US': {
                'File': 'File',
                'Edit': 'Edit',
                'Insert': 'Insert',
                'Theme': 'Theme',
                'Black & White': 'Black & White',
                'Light': 'Light',
                'Dark': 'Dark',
                'Language': 'Language',
                'Help': 'Help',
                'AI': 'AI',
                'Generate Concept Map': 'Generate Concept Map',
                'OrcaRouter Documentation': 'OrcaRouter Documentation',
                'New file': 'New file',
                'New File': 'New File',
                'Open file': 'Open file',
                'Open File': 'Open File',
                'Last open file': 'Last open file',
                'Save': 'Save',
                'Save File': 'Save File',
                'Save as': 'Save as',
                'Import from Markdown': 'Import from Markdown',
                'Export as': 'Export as',
                'PNG': 'PNG',
                'PDF': 'PDF',
                'Print...': 'Print...',
                'Quit': 'Quit',
                'Undo': 'Undo',
                'Redo': 'Redo',
                'Cut': 'Cut',
                'Copy': 'Copy',
                'Paste': 'Paste',
                'Delete': 'Delete',
                'line manage': 'Line manage',
                'note': 'Note',
                'link': 'Link',
                'Link': 'Link',
                'Annotation': 'Annotation',
                'Please enter annotation content...': 'Please enter annotation content...',
                'icon': 'Icon',
                'About': 'About',
                'hot key help': 'Hot key help',
                'Hot Key Help': 'Hot Key Help',
                'handwriting': 'Handwriting',
                'subtopic': 'Subtopic',
                'relation': 'Relation',
                'todolist': 'TodoList',
                'Set Color': 'Set Color',
                'Set Text Color': 'Set Text Color',
                'Image': 'Image',
                'Insert Link': 'Insert Link',
                'Select Image': 'Select Image',
                'Enter URL:': 'Enter URL:',
                # 状态消息
                'Info: add new node !': 'Info: add new node !',
                'Info: remove node !': 'Info: remove node !',
                'Info: move node !': 'Info: move node !',
                'Info: editing node !': 'Info: editing node !',
                'Info: Copy Successfully !': 'Info: Copy Successfully !',
                'Info: Paste Successfully !': 'Info: Paste Successfully !',
                'Info: change text color !': 'Info: change text color !',
                'Info: relation created !': 'Info: relation created !',
                'Info: relation already exists !': 'Info: relation already exists !',
                'Info: select two nodes to create relation !': 'Info: select two nodes to create relation !',
                'Info: TodoList image deleted !': 'Info: TodoList image deleted !',
                'View Annotation': 'View Annotation',
                'Warning: no activate node !': 'Warning: no activate node !',
                'Warning: Base Node': 'Warning: Base Node',
                'Warning: Bade Node': 'Warning: Bade Node',
                'Error: clipboard has not text content !': 'Error: clipboard has not text content !',
                'Error: invalid clipboard content for paste !': 'Error: invalid clipboard content for paste !',
                'Error: clipboard has no nodes !': 'Error: clipboard has no nodes !',
                'change node color': 'change node color',
                'Info: 请至少选中两个节点！': 'Info: Please select at least two nodes!',
                'Info: 已创建 {} 条连接线，已删除 {} 条连接线！': 'Info: Created {} lines, deleted {} lines!',
                'Info: 已创建 {} 条连接线！': 'Info: Created {} lines!',
                'Info: 已删除 {} 条连接线！': 'Info: Deleted {} lines!',
                'Error: the file is read only !': 'Error: the file is read only !',
                'Error: Failed to import Markdown file!': 'Error: Failed to import Markdown file!',
                'Info: Markdown file imported successfully!': 'Info: Markdown file imported successfully!',
                'Language switched to Chinese': 'Language switched to: Chinese',
                'Language switched to English': 'Language switched to: English',
                'Topic': 'Topic',
                'Topic: ': 'Topic: ',
                'Save MindMap': 'Save MindMap',
                'The MindMap has been modified !': 'The MindMap has been modified !',
                'Do you want to save this file ?': 'Do you want to save this file ?',
                'Save': 'Save',
                'Discard': 'Discard',
                'Cancel': 'Cancel',
            }
        }
        
        # 菜单项引用字典，用于语言切换时更新文本
        self.menu_items = {}
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.file_autoSave)

        self.setWindowIcon(QIcon(self.root + '/images/window.jpg'))
        print(self.root)

        self.scene = Graph()
        # 设置场景的翻译函数，使其能够访问翻译功能
        self.scene.tr_func = self.tr
        # 设置场景的主题
        self.scene.setTheme(self.m_theme)
        # 设置场景的根路径，用于加载文件时恢复批注图标
        self.scene.root_path = self.root
        self.scene.contentChanged.connect(self.contentChanged)
        self.scene.nodeNumChange.connect(self.nodeNumChange)
        self.scene.messageShow.connect(self.messageShow)

        self.view = CustomGraphicsView()
        # 设置视图的初始主题
        self.view.setTheme(self.m_theme)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        # 启用视口更新优化，减少残留
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # 或者使用智能更新模式（推荐）
        # self.view.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        #view.setContextMenuPolicy(Qt.CustomContextMenu)
        # view.setInteractive(False)
        self.view.setScene(self.scene)

        self.setCentralWidget(self.view)
        self.view.show()

        self.initUI()
        
        # 初始化完成后，根据默认主题应用样式
        self.changeTheme(self.m_theme)

    def initUI(self):
        self.setUpDockWidget()
        self.setUpMenuBar()
        self.setUpToolBar()
        self.setUpStatusBar()
        self.setUpIconToolBar()
        # 样式应用将在 initUI() 完成后通过 changeTheme() 统一处理

        self.update_title()

        self.resize(1440, 920)
        self.center()

        self.show()
    
    def applyCuteStyle(self):
        """应用二次元可爱风格样式"""
        cute_style = """
        /* 主窗口背景 - 渐变粉色 */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFE4F0, stop:1 #FFD6E8);
        }
        
        /* 菜单栏样式 */
        QMenuBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11pt;
            padding: 4px;
            border-bottom: 2px solid #FF8CC8;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 6px 12px;
            border-radius: 8px;
        }
        
        QMenuBar::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF8CC8, stop:1 #FF6BB5);
        }
        
        QMenuBar::item:pressed {
            background: #FF6BB5;
        }
        
        /* 菜单样式 */
        QMenu {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:1 #FFE4F0);
            border: 2px solid #FFB6D9;
            border-radius: 12px;
            padding: 4px;
            color: #5A5A5A;
            font-size: 10pt;
        }
        
        QMenu::item {
            padding: 8px 24px 8px 32px;
            border-radius: 8px;
            margin: 2px;
        }
        
        QMenu::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            color: #FFFFFF;
        }
        
        QMenu::separator {
            height: 1px;
            background: #FFB6D9;
            margin: 4px 8px;
        }
        
        /* 工具栏样式 */
        QToolBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFE4F0, stop:1 #FFD6E8);
            border: none;
            padding: 4px;
            spacing: 4px;
        }
        
        QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:1 #FFE4F0);
            border: 2px solid #FFB6D9;
            border-radius: 12px;
            padding: 6px;
            color: #5A5A5A;
            font-weight: bold;
            min-width: 160px;
            min-height: 90px;
            max-width: 250px;
            max-height: 90px;
            text-align: center;
            padding: 4px 8px;
        }
        
        QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            border: 2px solid #FF8CC8;
            color: #FFFFFF;
        }
        
        QToolButton:pressed {
            background: #FF8CC8;
            border: 2px solid #FF6BB5;
        }
        
        QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF8CC8, stop:1 #FF6BB5);
            border: 2px solid #FF5AA3;
            color: #FFFFFF;
        }
        
        QToolButton:checked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF6BB5, stop:1 #FF5AA3);
            border: 2px solid #FF4A93;
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            color: #FFFFFF;
            font-weight: bold;
            border-top: 2px solid #FF8CC8;
            padding: 4px;
        }
        
        QStatusBar::item {
            border: none;
        }
        
        QLabel {
            color: #FFFFFF;
            font-weight: bold;
            padding: 2px 8px;
        }
        
        /* 按钮样式 */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:1 #FFE4F0);
            border: 2px solid #FFB6D9;
            border-radius: 12px;
            padding: 6px 16px;
            color: #5A5A5A;
            font-weight: bold;
            font-size: 10pt;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            border: 2px solid #FF8CC8;
            color: #FFFFFF;
        }
        
        QPushButton:pressed {
            background: #FF8CC8;
            border: 2px solid #FF6BB5;
        }
        
        /* 滑块样式 */
        QSlider::groove:horizontal {
            background: #FFE4F0;
            height: 8px;
            border-radius: 4px;
            border: 1px solid #FFB6D9;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF8CC8);
            width: 20px;
            height: 20px;
            margin: -6px 0;
            border-radius: 10px;
            border: 2px solid #FF6BB5;
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF8CC8, stop:1 #FF6BB5);
        }
        
        /* Dock窗口样式 */
        QDockWidget {
            background: #FFE4F0;
            color: #5A5A5A;
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(float.png);
        }
        
        QDockWidget::title {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            padding: 6px;
            border-radius: 4px;
            color: #FFFFFF;
            font-weight: bold;
        }
        
        /* 列表样式 */
        QListWidget {
            background: #FFFFFF;
            border: 2px solid #FFB6D9;
            border-radius: 8px;
            color: #5A5A5A;
        }
        
        QListWidget::item {
            padding: 6px;
            border-radius: 4px;
        }
        
        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB6D9, stop:1 #FF9EC7);
            color: #FFFFFF;
        }
        
        /* 文本编辑框样式 */
        QTextEdit, QLineEdit {
            background: #FFFFFF;
            border: 2px solid #FFB6D9;
            border-radius: 8px;
            padding: 4px;
            color: #5A5A5A;
            selection-background-color: #FFB6D9;
            selection-color: #FFFFFF;
        }
        
        QTextEdit:focus, QLineEdit:focus {
            border: 2px solid #FF8CC8;
        }
        """
        self.setStyleSheet(cute_style)

    def applyModernLightStyle(self):
        """Apply the default modern concept-map workspace style."""
        self.setStyleSheet("""
        QMainWindow { background: #F4F7FB; color: #183153; }
        QMenuBar {
            background: #FFFFFF; color: #334155;
            border-bottom: 1px solid #E2E8F0;
            padding: 5px 10px; font-size: 10.5pt;
        }
        QMenuBar::item { background: transparent; border-radius: 7px; padding: 6px 11px; }
        QMenuBar::item:selected { background: #EAF3FF; color: #1769E0; }
        QMenu {
            background: #FFFFFF; color: #334155;
            border: 1px solid #DCE5F0; border-radius: 10px; padding: 6px;
        }
        QMenu::item { padding: 8px 28px; border-radius: 7px; }
        QMenu::item:selected { background: #EAF3FF; color: #1769E0; }
        QMenu::separator { height: 1px; background: #E8EEF6; margin: 5px 8px; }
        QToolBar {
            background: #FFFFFF; border: none;
            border-bottom: 1px solid #E2E8F0; spacing: 5px; padding: 7px 10px;
        }
        QToolButton {
            background: transparent; color: #475569;
            border: 1px solid transparent; border-radius: 10px;
            padding: 5px 9px; min-width: 70px; min-height: 52px;
            max-width: 112px; font-size: 9pt;
        }
        QToolButton:hover { background: #F0F6FF; border-color: #CFE2FF; color: #1769E0; }
        QToolButton:pressed, QToolButton:checked {
            background: #E3F0FF; border-color: #A7CBFF; color: #0F5FD6;
        }
        QStatusBar {
            background: #FFFFFF; color: #64748B;
            border-top: 1px solid #E2E8F0; padding: 3px;
        }
        QStatusBar QLabel { color: #64748B; font-weight: normal; padding: 2px 8px; }
        QDockWidget { color: #334155; background: #FFFFFF; }
        QDockWidget::title { background: #F3F7FC; padding: 7px; }
        QListWidget { background: #FFFFFF; color: #334155; border: 1px solid #DCE5F0; }
        """)
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def tr(self, text):
        """
        翻译方法，根据当前语言返回对应的翻译文本
        
        参数:
        - text: 要翻译的文本（英文原始文本）
        
        返回:
        - str: 翻译后的文本
        """
        if self.m_language in self.translations:
            return self.translations[self.m_language].get(text, text)
        return text
    
    def updateMenuLanguage(self):
        """
        更新所有菜单项的文本以匹配当前语言
        
        功能:
        - 遍历所有保存的菜单项引用
        - 使用翻译字典更新文本
        """
        # 更新菜单栏标题
        if 'File' in self.menu_items:
            self.menu_items['File'].setTitle(self.tr('File'))
        if 'Edit' in self.menu_items:
            self.menu_items['Edit'].setTitle(self.tr('Edit'))
        if 'Insert' in self.menu_items:
            self.menu_items['Insert'].setTitle(self.tr('Insert'))
        if 'Theme' in self.menu_items:
            self.menu_items['Theme'].setTitle(self.tr('Theme'))
        if 'Language' in self.menu_items:
            self.menu_items['Language'].setTitle(self.tr('Language'))
        if 'AI' in self.menu_items:
            self.menu_items['AI'].setTitle(self.tr('AI'))
        
        # 更新菜单项文本
        menu_texts = ['New file', 'New File', 'Open file', 'Open File', 'Last open file', 
                      'Save', 'Save File', 'Save as', 'Import from Markdown', 'Export as', 'Print...', 'Quit', 
                      'Undo', 'Redo', 'Cut', 'Copy', 'Paste', 'Delete', 'line manage', 
                      'note', 'link', 'icon', 'About', 'hot key help', 'handwriting', 
                      'subtopic', 'relation', 'todolist', 'Move with subtree', 'Black & White', 'Light', 'Dark',
                      'Generate Concept Map', 'OrcaRouter Documentation']
        
        for text in menu_texts:
            if text in self.menu_items:
                item = self.menu_items[text]
                if isinstance(item, QAction):
                    item.setText(self.tr(text))
                elif isinstance(item, QMenu):
                    item.setTitle(self.tr(text))
        
        # 更新Dock窗口标题和内容
        if hasattr(self, 'dock'):
            self.dock.setWindowTitle(self.tr('Hot Key Help'))
            # 更新热键列表内容
            widget = self.dock.widget()
            if isinstance(widget, QListWidget):
                widget.clear()
                if self.m_language == 'zh_CN':
                    widget.addItems(['Ctrl + X 剪切', 'Ctrl + C 复制'])
                else:
                    widget.addItems(['Ctrl + X Cut', 'Ctrl + C Copy'])
        
        # 更新状态栏中的主题数量标签
        if hasattr(self, 'label2') and hasattr(self, 'scene') and hasattr(self.scene, 'NodeList'):
            node_count = len(self.scene.NodeList)
            self.label2.setText(self.tr('Topic: ') + str(node_count))
    
    def update_title(self):
        self.setWindowTitle('%s - MindMap' % (os.path.basename(self.m_filename) if self.m_filename else 'Untitled'))

    def setUpDockWidget(self):
        """Dock Widget Show Hot Key Help"""
        self.dock = QDockWidget(self.tr('Hot Key Help'), self)
        self.dock.setAllowedAreas(Qt.RightDockWidgetArea)
        hotkeyList = QListWidget(self)
        if self.m_language == 'zh_CN':
            hotkeyList.addItems(['Ctrl + X 剪切', 'Ctrl + C 复制'])
        else:
            hotkeyList.addItems(['Ctrl + X Cut', 'Ctrl + C Copy'])
        self.dock.setWidget(hotkeyList)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.hide()

    ###########################################################################
    #
    #  menubar
    #
    ###########################################################################
    def setUpMenuBar(self):
        self.m_undoStack = QUndoStack(self)
        #self.m_undoView = QUndoView(self.m_undoStack, self)
        ###########################################################################
        # file menu
        ###########################################################################
        file_menu = self.menuBar().addMenu(self.tr('File'))
        self.menu_items['File'] = file_menu

        # new file
        new_file_action = QAction(self.tr('New file'), self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.file_new)
        file_menu.addAction(new_file_action)
        self.menu_items['New file'] = new_file_action

        # open file
        open_file_action = QAction(self.tr('Open file'), self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        self.menu_items['Open file'] = open_file_action

        # last open file
        self.last_open_file_menu = QMenu(self.tr('Last open file'), self)
        self.file_last_open()
        # TODO: function bind with action
        file_menu.addMenu(self.last_open_file_menu)
        self.menu_items['Last open file'] = self.last_open_file_menu

        file_menu.addSeparator()

        # save file
        self.save_file_action = QAction(self.tr('Save'), self)
        self.save_file_action.setShortcut('Ctrl+S')
        self.save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(self.save_file_action)
        self.menu_items['Save'] = self.save_file_action

        # save file as ...
        saveas_file_action = QAction(self.tr('Save as'), self)
        saveas_file_action.setShortcut('Ctrl+Shift+S')
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        self.menu_items['Save as'] = saveas_file_action

        file_menu.addSeparator()
        
        # import from markdown
        import_md_action = QAction(self.tr('Import from Markdown'), self)
        import_md_action.triggered.connect(self.importFromMarkdown)
        file_menu.addAction(import_md_action)
        self.menu_items['Import from Markdown'] = import_md_action

        file_menu.addSeparator()

        # export as 
        exportas_menu = QMenu(self.tr('Export as'), self)
        self.menu_items['Export as'] = exportas_menu
        # TODO: function bind with action
        exportas_png_action = QAction('PNG', self)
        exportas_png_action.triggered.connect(self.exportas_png)
        exportas_menu.addAction(exportas_png_action)

        exportas_pdf_action = QAction('PDF', self)
        exportas_pdf_action.triggered.connect(self.exportas_pdf)
        exportas_menu.addAction(exportas_pdf_action)

        file_menu.addMenu(exportas_menu)

        file_menu.addSeparator()

        # print file
        print_action = QAction(self.tr('Print...'), self)
        print_action.setShortcut('Ctrl+P')
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        self.menu_items['Print...'] = print_action

        file_menu.addSeparator()

        # quit
        quit_action = QAction(self.tr('Quit'), self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.quit)
        file_menu.addAction(quit_action)
        self.menu_items['Quit'] = quit_action

        #############################################################################
        # Edit menu
        #############################################################################
        edit_menu = self.menuBar().addMenu(self.tr('Edit'))
        self.menu_items['Edit'] = edit_menu

        # undo
        self.undo_action = self.m_undoStack.createUndoAction(self, self.tr('Undo'))
        self.undo_action.setShortcut('Ctrl+Z')
        edit_menu.addAction(self.undo_action)
        self.menu_items['Undo'] = self.undo_action

        # Redo
        self.redo_action = self.m_undoStack.createRedoAction(self, self.tr('Redo'))
        self.redo_action.setShortcut('Ctrl+Y')
        edit_menu.addAction(self.redo_action)
        self.menu_items['Redo'] = self.redo_action

        edit_menu.addSeparator()

        # Cut
        cut_action = QAction(self.tr('Cut'), self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(self.scene.cut)
        edit_menu.addAction(cut_action)
        self.menu_items['Cut'] = cut_action

        # Copy
        copy_action = QAction(self.tr('Copy'), self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.scene.copy)
        edit_menu.addAction(copy_action)
        self.menu_items['Copy'] = copy_action

        # Paste
        paste_action = QAction(self.tr('Paste'), self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.scene.paste)
        edit_menu.addAction(paste_action)
        self.menu_items['Paste'] = paste_action

        # Delete
        delete_action = QAction(self.tr('Delete'), self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.scene.removeNode)
        edit_menu.addAction(delete_action)
        self.menu_items['Delete'] = delete_action

        edit_menu.addSeparator()

        # Line Manage
        line_manage_action = QAction(self.tr('line manage'), self)
        line_manage_action.triggered.connect(self.scene.lineManage)
        edit_menu.addAction(line_manage_action)
        self.menu_items['line manage'] = line_manage_action

        ##########################################################################
        # Insert menu
        ##########################################################################
        insert_menu = self.menuBar().addMenu(self.tr('Insert'))
        self.menu_items['Insert'] = insert_menu

        add_notes_action = QAction(self.tr('note'), self)
        add_notes_action.triggered.connect(self.add_notes)
        insert_menu.addAction(add_notes_action)
        self.menu_items['note'] = add_notes_action

        add_link_action = QAction(self.tr('link'), self)
        add_link_action.triggered.connect(self.add_link)
        insert_menu.addAction(add_link_action)
        self.menu_items['link'] = add_link_action

        add_icon_action = QAction(self.tr('icon'), self)
        add_icon_action.triggered.connect(self.add_icon)
        insert_menu.addAction(add_icon_action)
        self.menu_items['icon'] = add_icon_action

        ##########################################################################
        # AI menu (optional OrcaRouter provider)
        ##########################################################################
        ai_menu = self.menuBar().addMenu(self.tr('AI'))
        self.menu_items['AI'] = ai_menu

        self.ai_generate_action = QAction(
            QIcon(self.root + '/icons/ai-spark.svg'),
            self.tr('Generate Concept Map'),
            self,
        )
        self.ai_generate_action.setShortcut('Ctrl+Shift+G')
        self.ai_generate_action.triggered.connect(self.openAIGenerator)
        ai_menu.addAction(self.ai_generate_action)
        self.menu_items['Generate Concept Map'] = self.ai_generate_action

        ai_docs_action = QAction(self.tr('OrcaRouter Documentation'), self)
        ai_docs_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://docs.orcarouter.ai'))
        )
        ai_menu.addAction(ai_docs_action)
        self.menu_items['OrcaRouter Documentation'] = ai_docs_action

        ##########################################################################
        # Theme menu
        ##########################################################################
        theme_menu = self.menuBar().addMenu(self.tr('Theme'))
        self.menu_items['Theme'] = theme_menu

        # 创建动作组，确保只有一个主题被选中（互斥）
        theme_group = QActionGroup(self)
        
        # 黑白主题选项
        blackwhite_action = QAction(self.tr('Black & White'), self)
        blackwhite_action.setCheckable(True)
        blackwhite_action.setChecked(self.m_theme == 'Black & White')
        blackwhite_action.triggered.connect(lambda: self.changeTheme('Black & White'))
        theme_group.addAction(blackwhite_action)
        theme_menu.addAction(blackwhite_action)
        self.menu_items['Black & White'] = blackwhite_action  # 保存到menu_items以便语言切换时更新
        
        # 浅色主题选项
        light_action = QAction(self.tr('Light'), self)
        light_action.setCheckable(True)
        light_action.setChecked(self.m_theme == 'Light')
        light_action.triggered.connect(lambda: self.changeTheme('Light'))
        theme_group.addAction(light_action)
        theme_menu.addAction(light_action)
        self.menu_items['Light'] = light_action  # 保存到menu_items以便语言切换时更新
        
        # 深色主题选项
        dark_action = QAction(self.tr('Dark'), self)
        dark_action.setCheckable(True)
        dark_action.setChecked(self.m_theme == 'Dark')
        dark_action.triggered.connect(lambda: self.changeTheme('Dark'))
        theme_group.addAction(dark_action)
        theme_menu.addAction(dark_action)
        self.menu_items['Dark'] = dark_action  # 保存到menu_items以便语言切换时更新
        
        # 保存主题选项的引用，用于更新选中状态
        self.theme_actions = {
            'Black & White': blackwhite_action,
            'Light': light_action,
            'Dark': dark_action
        }

        ##########################################################################
        # Language menu
        ##########################################################################
        language_menu = self.menuBar().addMenu(self.tr('Language'))
        self.menu_items['Language'] = language_menu

        # 创建动作组，确保只有一个选项被选中（互斥）
        language_group = QActionGroup(self)
        
        # 中文选项
        chinese_action = QAction('中文 (Chinese)', self)
        chinese_action.setCheckable(True)  # 设置为可选中状态
        # 根据当前语言设置初始选中状态
        chinese_action.setChecked(self.m_language == 'zh_CN')
        chinese_action.triggered.connect(lambda: self.changeLanguage('zh_CN'))
        language_group.addAction(chinese_action)  # 添加到动作组
        language_menu.addAction(chinese_action)

        # 英文选项
        english_action = QAction('English (英文)', self)
        english_action.setCheckable(True)  # 设置为可选中状态
        # 根据当前语言设置初始选中状态
        english_action.setChecked(self.m_language == 'en_US')
        english_action.triggered.connect(lambda: self.changeLanguage('en_US'))
        language_group.addAction(english_action)  # 添加到动作组
        language_menu.addAction(english_action)

        # 保存语言选项的引用，用于更新选中状态
        self.language_actions = {
            'zh_CN': chinese_action,
            'en_US': english_action
        }


    ###########################################################################
    #
    #  ToolBar
    #
    ############################################################################
    def setUpToolBar(self):
        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # 统一图标尺寸
        icon_size = 28
        self.toolbar.setIconSize(QSize(icon_size, icon_size))
        self.toolbar.setMovable(False)
        
        # 设置工具栏按钮的统一大小，确保对齐
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # 辅助函数：加载并缩放图标到统一尺寸
        def getScaledIcon(icon_path, size=icon_size):
            """加载图标并缩放到指定尺寸"""
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(size, size)
            return QIcon(pixmap)

        ###########################################################################
        #  New File
        ###########################################################################
        #new_file_action = QAction(getScaledIcon(self.root + '/images/filenew.png'), self.tr('New File'), self)
        #new_file_action.triggered.connect(self.file_new)
        #self.toolbar.addAction(new_file_action)
        #self.menu_items['New File'] = new_file_action

        ###########################################################################
        #  Save File
        ###########################################################################
        #save_file_action = QAction(getScaledIcon(self.root + '/images/filesave.png'), self.tr('Save File'), self)
        #save_file_action.triggered.connect(self.file_save)
        #self.toolbar.addAction(save_file_action)
        #self.menu_items['Save File'] = save_file_action

        ###########################################################################
        #  Open File
        ###########################################################################
        #open_file_action = QAction(getScaledIcon(self.root + '/images/fileopen.png'), self.tr('Open File'), self)
        #open_file_action.triggered.connect(self.file_open)
        #self.toolbar.addAction(open_file_action)
        #self.menu_items['Open File'] = open_file_action

        ###########################################################################
        #  Handwriting
        ###########################################################################
        self.handwriting_action = QAction(getScaledIcon(self.root + '/images/手写.png'), self.tr('handwriting'), self)
        self.handwriting_action.setCheckable(True)  # 设置为可切换状态
        self.handwriting_action.triggered.connect(self.toggleHandwriting)
        self.toolbar.addAction(self.handwriting_action)
        self.menu_items['handwriting'] = self.handwriting_action

        # AI concept map generation
        self.ai_generate_action.setIcon(getScaledIcon(self.root + '/icons/ai-spark.svg'))
        self.toolbar.addAction(self.ai_generate_action)

        ############################################################################
        #  New Son Node (子主题)
        ############################################################################
        new_sonNode_action = QAction(getScaledIcon(self.root + '/images/子主题.png'), self.tr('subtopic'), self)
        new_sonNode_action.triggered.connect(self.scene.addSonNode)
        self.toolbar.addAction(new_sonNode_action)
        self.menu_items['subtopic'] = new_sonNode_action

        ############################################################################
        #  Line Manage
        ############################################################################
        # 使用菜单中已存在的 line_manage_action，确保文本同步更新
        if 'line manage' in self.menu_items:
            line_manage_action = self.menu_items['line manage']
            # 为工具栏设置图标（统一尺寸）
            line_manage_action.setIcon(getScaledIcon(self.root + '/images/连线管理.png'))
        else:
            line_manage_action = QAction(getScaledIcon(self.root + '/images/连线管理.png'), self.tr('line manage'), self)
            line_manage_action.triggered.connect(self.scene.lineManage)
            self.menu_items['line manage'] = line_manage_action
        self.toolbar.addAction(line_manage_action)

        ############################################################################
        #  TodoList
        ############################################################################
        todolist_action = QAction(getScaledIcon(self.root + '/images/待办事项.png'), self.tr('todolist'), self)
        todolist_action.triggered.connect(self.showTodoList)
        self.toolbar.addAction(todolist_action)
        self.menu_items['todolist'] = todolist_action

        ############################################################################
        #  Delete
        ############################################################################
        # 使用菜单中已存在的 delete_action，确保文本同步更新
        if 'Delete' in self.menu_items:
            delete_action = self.menu_items['Delete']
            # 为工具栏设置图标（统一尺寸）
            delete_action.setIcon(getScaledIcon(self.root + '/images/删除.png'))
        else:
            delete_action = QAction(getScaledIcon(self.root + '/images/删除.png'), self.tr('Delete'), self)
            delete_action.triggered.connect(self.scene.removeNode)
            self.menu_items['Delete'] = delete_action
        self.toolbar.addAction(delete_action)

        ############################################################################
        #  undo
        #############################################################################
        self.undo_action.setIcon(getScaledIcon(self.root + '/images/撤销.png'))
        self.toolbar.addAction(self.undo_action)

        ##############################################################################
        #  redo
        ##############################################################################
        self.redo_action.setIcon(getScaledIcon(self.root + '/images/重做.png'))
        self.toolbar.addAction(self.redo_action)

        ##############################################################################
        #  Move with subtree
        ##############################################################################
        self.move_subtree_action = QAction(getScaledIcon(self.root + '/images/移动子树.png'), self.tr('Move with subtree'), self)
        self.move_subtree_action.setCheckable(True)  # 设置为可切换状态
        self.move_subtree_action.setChecked(self.m_moveWithSubtree)  # 默认选中
        self.move_subtree_action.triggered.connect(self.toggleMoveWithSubtree)
        self.toolbar.addAction(self.move_subtree_action)
        self.menu_items['Move with subtree'] = self.move_subtree_action

        self.scene.setUndoStack(self.m_undoStack)
        # 设置场景的移动子树模式
        self.scene.setMoveWithSubtree(self.m_moveWithSubtree)

    def setUpIconToolBar(self):
        self.icontoolbar = QToolBar('icon toolbar', self)

        m_signalMapper = QSignalMapper(self)

        # application-system
        application_system_action = QAction(QIcon(self.root + '/icons/applications-system.svg'), 'Applications-system', self)
        application_system_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(application_system_action, self.root + '/icons/applications-system.svg')

        # trash icon
        trash_action = QAction(QIcon(self.root + '/icons/user-trash-full.svg'), 'Trash', self)
        trash_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(trash_action, self.root + '/icons/user-trash-full.svg')

        # mail icon
        mail_action = QAction(QIcon(self.root + '/icons/mail-attachment.svg'), 'Mail', self)
        mail_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(mail_action, self.root + '/icons/mail-attachment.svg')

        # warn icon
        warn_action = QAction(QIcon(self.root + '/icons/dialog-warning.svg'), 'Warning', self)
        warn_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(warn_action, self.root + '/icons/dialog-warning.svg')

        # how icon
        help_action = QAction(QIcon(self.root + '/icons/help-browser.svg'), 'Help', self)
        help_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(help_action, self.root + '/icons/help-browser.svg')

        # calendar icon
        calendar_action = QAction(QIcon(self.root + '/icons/x-office-calendar.svg'), 'Calendar', self)
        calendar_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(calendar_action, self.root + '/icons/x-office-calendar.svg')

        # system_users icon
        system_users_action = QAction(QIcon(self.root + '/icons/system-users.svg'), 'System-users', self)
        system_users_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(system_users_action, self.root + '/icons/system-users.svg')

        # info icon
        info_action = QAction(QIcon(self.root + '/icons/dialog-information.svg'), 'Infomation', self)
        info_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(info_action, self.root + '/icons/dialog-information.svg')

        m_signalMapper.mapped[str].connect(self.scene.insertPicture)

        self.icontoolbar.addAction(application_system_action)
        self.icontoolbar.addAction(trash_action)
        self.icontoolbar.addAction(mail_action)
        self.icontoolbar.addAction(warn_action)
        self.icontoolbar.addAction(help_action)
        self.icontoolbar.addAction(calendar_action)
        self.icontoolbar.addAction(system_users_action)
        self.icontoolbar.addAction(info_action)

        self.addToolBar(Qt.LeftToolBarArea, self.icontoolbar)
        self.icontoolbar.hide()

    def setUpStatusBar(self):
        zoomSlider = MySlider(self.view, Qt.Horizontal)
        zoomSlider.setMaximumWidth(200)
        zoomSlider.setRange(1, 200)
        zoomSlider.setSingleStep(10)
        zoomSlider.setValue(100)

        self.label1 = QLabel('100%')
        self.label2 = QLabel(self.tr('Topic: ') + '1')
        self.label3 = QLabel('Ready · Ctrl+Shift+G to generate with AI')

        widget = QWidget(self)
        hbox = QHBoxLayout()
        
        hbox.addWidget(self.label2)
        hbox.addWidget(zoomSlider)
        hbox.addWidget(self.label1)
        hbox.addWidget(self.label3)

        widget.setLayout(hbox)

        zoomSlider.valueChanged.connect(self.labelShow)        

        self.statusBar().addWidget(widget, 5)
    
    def nodeNumChange(self, v):
        self.label2.setText(self.tr('Topic: ') + str(v))

    def labelShow(self, v):
        self.label1.setText(str(v) + '%')
    
    def messageShow(self, text):
        self.label3.setText(text)

    def contentChanged(self, changed=True):
        print(self.m_contentChanged)
        if not self.m_contentChanged and changed:
            self.timer.start(AUTOSAVE_TIME)
            self.setWindowTitle('*' + self.windowTitle())
            self.m_contentChanged = True

            fileinfo = QFileInfo(self.m_filename)
            if 'Untitled' not in self.windowTitle() and fileinfo.isWritable():
                self.save_file_action.setEnabled(True)
        
        elif self.m_contentChanged and not changed:
            self.timer.stop()
            self.setWindowTitle(self.windowTitle()[1:])
            self.m_contentChanged = False
            self.save_file_action.setEnabled(False)

    # TODO: scene center move
    def file_new(self):
        if not self.close_file():
            return

        self.m_filename = None
        self.scene.addFirstNode()
        self.update_title()
    
    # TODO: make sure file is valid !
    def file_open(self, filename=''):
        if not self.close_file():
            return

        cur_filename = self.m_filename
        if not filename:
            if self.sender().text() in self.m_settings.value('lastpath'):
                self.m_filename = self.root + '/files/' + self.sender().text()
                print(self.m_filename)
            else:
                dialog = QFileDialog(self, 'Open mindmap', self.root + '/files', 'MindMap(*.mm)')
                dialog.setAcceptMode(QFileDialog.AcceptOpen)
                dialog.setDefaultSuffix('mm')

                if not dialog.exec():
                    return
                self.m_filename = dialog.selectedFiles()[0]    
        else:
            self.m_filename = filename

        fileInfo = QFileInfo(self.m_filename)
        if not fileInfo.isWritable():
            print('Read-Only File !')
        
        if not self.scene.readContentFromXmlFile(self.m_filename):
            self.m_filename = cur_filename
            return

        lastpath = self.m_settings.value('lastpath')
        if os.path.basename(self.m_filename) not in lastpath:
            lastpath.append(os.path.basename(self.m_filename))
            self.m_settings.setValue('lastpath', lastpath)
            self.file_last_open()
        
        self.update_title()
    
    def importFromMarkdown(self):
        """从Markdown文件导入思维导图"""
        if not self.close_file():
            return
        
        # 打开文件选择对话框
        dialog = QFileDialog(self, self.tr('Import from Markdown'), self.root + '/files', 'Markdown(*.md *.markdown)')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setDefaultSuffix('md')
        
        if not dialog.exec():
            return
        
        filename = dialog.selectedFiles()[0]
        
        # 调用场景的markdown导入方法
        if not self.scene.readContentFromMarkdown(filename):
            self.messageShow(self.tr('Error: Failed to import Markdown file!'))
            return
        
        # 清空文件名（因为是导入的，不是打开的文件）
        self.m_filename = None
        self.update_title()
        self.messageShow(self.tr('Info: Markdown file imported successfully!'))

    def openAIGenerator(self):
        """Open the optional OrcaRouter concept-map generator."""
        if self.ai_thread and self.ai_thread.isRunning():
            return

        saved_model = self.m_settings.value('ai/orcarouter/model', DEFAULT_MODEL)
        dialog = AIGenerationDialog(
            api_key=self._orcarouter_api_key,
            model=str(saved_model or DEFAULT_MODEL),
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.values()
        # Keep the secret in memory for this process only. QSettings stores only
        # the non-sensitive model choice.
        self._orcarouter_api_key = values['api_key']
        self.m_settings.setValue('ai/orcarouter/model', values['model'])

        self.ai_progress = QProgressDialog(
            'OrcaRouter is building your concept map…', '', 0, 0, self
        )
        self.ai_progress.setWindowTitle('AI Concept Map')
        self.ai_progress.setCancelButton(None)
        self.ai_progress.setWindowModality(Qt.WindowModal)
        self.ai_progress.setMinimumDuration(0)
        self.ai_progress.show()

        self.ai_generate_action.setEnabled(False)
        self.ai_thread = AIGenerationThread(values, self)
        self.ai_thread.generated.connect(self._onAIGenerationFinished)
        self.ai_thread.failed.connect(self._onAIGenerationFailed)
        self.ai_thread.finished.connect(self._cleanupAIGeneration)
        self.ai_thread.start()

    def _onAIGenerationFinished(self, markdown):
        if self.ai_progress:
            self.ai_progress.close()
        if not self.close_file():
            return
        if not self.scene.readContentFromMarkdownText(markdown):
            QMessageBox.warning(self, 'AI Concept Map', 'The generated outline could not be imported.')
            return

        self.m_filename = None
        # The scene marks itself changed during import. Re-apply that state
        # after resetting the title so the unsaved marker remains correct.
        self.m_contentChanged = False
        self.timer.stop()
        self.update_title()
        self.contentChanged(True)
        bounds = self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100)
        if bounds.isValid():
            self.view.fitInView(bounds, Qt.KeepAspectRatio)
        self.messageShow('AI concept map generated with OrcaRouter')

    def _onAIGenerationFailed(self, message):
        if self.ai_progress:
            self.ai_progress.close()
        QMessageBox.critical(self, 'OrcaRouter request failed', message)

    def _cleanupAIGeneration(self):
        if self.ai_thread:
            self.ai_thread.deleteLater()
        self.ai_thread = None
        self.ai_progress = None
        self.ai_generate_action.setEnabled(True)

    def file_last_open(self):
        lastpath = self.m_settings.value('lastpath')

        if not lastpath:
            last_open_action = QAction('no last file', self)
            self.last_open_file_menu.addAction(last_open_action)
        else:
            self.last_open_file_menu.clear()
            for filename in lastpath:
                last_open_action = QAction(filename, self)
                last_open_action.triggered.connect(self.file_open)
                self.last_open_file_menu.addAction(last_open_action)

    def file_save(self, checkIfReadOnly=True):
        # 如果文件名为空，调用另存为
        if not self.m_filename:
            self.file_saveas()
            return
        
        # 检查文件是否可写（如果文件不存在，isWritable() 可能返回 False，但我们可以创建新文件）
        fileinfo = QFileInfo(self.m_filename)
        if checkIfReadOnly and fileinfo.exists() and not fileinfo.isWritable():
            self.messageShow('Error: the file is read only !')
            return

        try:
            print(self.m_filename)
            self.scene.writeContentToXmlFile(self.m_filename)
            self.contentChanged(False)
            self.m_undoStack.clear()
            self.messageShow(self.tr('Info: File saved successfully!'))
        except Exception as e:
            print(f'Error saving file: {e}')
            self.messageShow(f'Error: Failed to save file: {str(e)}')

    def file_autoSave(self):
        fileInfo = QFileInfo(self.m_filename)
        if self.windowTitle() != 'Untitled' and fileInfo.isWritable():
            self.file_save()

    def file_saveas(self):
        dialog = QFileDialog(self, 'Save mindmap as', self.root + '/files', 'MindMap(*.mm)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('mm')

        if not dialog.exec():
            return False

        self.m_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.file_save(False)
        self.update_title()
        return True

    def file_print(self):
        printer = QPrinter(QPrinter.HighResolution)
        if QPrintDialog(printer).exec() == QDialog.Accepted:
            painter = QPainter(printer)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter)
            painter.end()

    def close_file(self):
        if self.m_contentChanged:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle(self.tr('Save MindMap'))
            msgBox.setText(self.tr('The MindMap has been modified !'))
            msgBox.setInformativeText(self.tr('Do you want to save this file ?'))
            msgBox.setStandardButtons(QMessageBox.Save|
                                        QMessageBox.Discard|
                                        QMessageBox.Cancel)

            msgBox.setDefaultButton(QMessageBox.Save)
            # 汉化按钮文本
            saveButton = msgBox.button(QMessageBox.Save)
            if saveButton:
                saveButton.setText(self.tr('Save'))
            discardButton = msgBox.button(QMessageBox.Discard)
            if discardButton:
                discardButton.setText(self.tr('Discard'))
            cancelButton = msgBox.button(QMessageBox.Cancel)
            if cancelButton:
                cancelButton.setText(self.tr('Cancel'))
            
            # 调整窗口大小
            msgBox.resize(500, 200)
            
            # 确保浅色主题下文字为黑色
            if self.m_theme == 'Light':
                msgBox.setStyleSheet("""
                    QMessageBox {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFFFFF, stop:1 #FFE4F0);
                        color: #000000;
                    }
                    QMessageBox QLabel {
                        color: #000000;
                    }
                    QMessageBox QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFFFFF, stop:1 #FFE4F0);
                        border: 2px solid #FFB6D9;
                        border-radius: 8px;
                        padding: 6px 16px;
                        color: #000000;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QMessageBox QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFB6D9, stop:1 #FF9EC7);
                        color: #FFFFFF;
                    }
                """)
            ret = msgBox.exec()

            if ret == QMessageBox.Save:
                if 'Untitled' in self.windowTitle():
                    if not self.file_saveas():
                        return False
                else:
                    self.file_save()
            elif ret == QMessageBox.Cancel:
                return False

        self.m_contentChanged = False
        self.scene.removeAllNodes()
        self.scene.removeAllBranches()
        self.m_undoStack.clear()
        return True

    def exportas_png(self):
        dialog = QFileDialog(self, 'Export mindmap as', self.root + '/files', 'MindMap(*.png)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('png')

        if not dialog.exec():
            return False

        png_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.scene.writeContentToPngFile(png_filename)

    def exportas_pdf(self):
        dialog = QFileDialog(self, 'Export mindmap as', self.root + '/files', 'MindMap(*.pdf)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('pdf')

        if not dialog.exec():
            return False

        pdf_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.scene.writeContentToPdfFile(pdf_filename)
            
    def quit(self):
        self.close_signal.emit()
        if self.m_contentChanged and not self.close_file():
            return
        qApp.quit()

    def closeEvent(self, e):
        self.close_signal.emit()
        if self.m_contentChanged and not self.close_file():
            e.ignore()
        else:
            e.accept()

    def getPos(self, size, offset_x=0, offset_y=0):
        p = QPointF(self.scene.m_activateNode.boundingRect().center().x(), 
                self.scene.m_activateNode.boundingRect().bottomRight().y())
        sceneP = self.scene.m_activateNode.mapToScene(p)
        viewP = self.view.mapFromScene(sceneP)
        pos = self.view.viewport().mapToGlobal(viewP)
        x = pos.x() - size[0]/2 + offset_x
        y = pos.y() + offset_y
        return x, y

    def add_notes(self):
        x, y = self.getPos(NOTE_SIZE)
        print(x, y)
        self.addNote.emit(x, y, self.scene.m_activateNode.m_note)

    def getNote(self, note):
        self.scene.m_activateNode.m_note = note

    def add_link(self):
        x, y = self.getPos(LINK_SIZE)
        print(x, y)
        self.addLink.emit(x, y, self.scene.m_activateNode.m_link)

    def getLink(self, link):
        self.scene.m_activateNode.m_link = link
        if not self.scene.m_activateNode.hasLink and link != 'https://':
            self.scene.m_activateNode.hasLink = True
            self.scene.m_activateNode.insertLink(link)
            self.scene.adjustSubTreeNode()
            self.scene.adjustBranch()
        elif self.scene.m_activateNode.hasLink:
            self.scene.m_activateNode.updateLink(link)

    def getAnnotation(self, annotation):
        # 使用记录中的节点（如果存在），否则使用当前激活节点
        # 这样可以确保批注保存到打开批注窗口时的节点，而不是当前激活节点
        target_node = getattr(self, '_annotation_editing_node', None)
        if not target_node:
            target_node = self.scene.m_activateNode
        
        # 确保有目标节点
        if not target_node:
            return
        
        # 确保annotation是字符串类型
        annotation_text = annotation if annotation is not None else ''
        
        # 保存批注到目标节点（每个节点都有独立的m_annotation属性）
        target_node.m_annotation = annotation_text
        # 批注功能不再使用图标，直接点击节点查看
        
        # 清除记录，准备下次使用
        if hasattr(self, '_annotation_editing_node'):
            delattr(self, '_annotation_editing_node')
    
    def getNodeInfo(self, annotation, link):
        """处理节点信息窗口关闭，保存批注和链接"""
        # 使用记录中的节点（如果存在），否则使用当前激活节点
        target_node = getattr(self, '_node_info_editing_node', None)
        if not target_node:
            target_node = self.scene.m_activateNode
        
        # 确保有目标节点
        if not target_node:
            return
        
        # 保存批注
        annotation_text = annotation if annotation is not None else ''
        target_node.m_annotation = annotation_text
        
        # 保存链接
        link_text = link if link is not None else 'https://'
        target_node.m_link = link_text
        
        # 更新链接图标
        if link_text != 'https://' and link_text.strip():
            if not target_node.hasLink:
                target_node.hasLink = True
                target_node.insertLink(link_text)
                self.scene.adjustSubTreeNode()
                self.scene.adjustBranch()
            else:
                target_node.updateLink(link_text)
        else:
            # 如果链接被清空，移除链接图标
            if target_node.hasLink:
                # 移除链接图标的HTML
                html = target_node.toHtml()
                # 使用正则表达式移除链接图标的HTML
                import re
                pattern = r'<a href="https?://[^"]*">.*?</a>'
                html = re.sub(pattern, '', html)
                target_node.setHtml(html)
                target_node.hasLink = False
        
        # 清除记录，准备下次使用
        if hasattr(self, '_node_info_editing_node'):
            delattr(self, '_node_info_editing_node')

    def handle_addAnnotation(self, x, y, annotation):
        """处理添加批注信号，记录当前节点并显示批注窗口"""
        # 记录当前正在编辑批注的节点（防止在编辑过程中节点切换）
        # 必须在显示窗口之前记录，确保保存到正确的节点
        if self.scene.m_activateNode:
            self._annotation_editing_node = self.scene.m_activateNode
        else:
            # 如果没有激活节点，清除之前的记录，避免保存到错误的节点
            if hasattr(self, '_annotation_editing_node'):
                delattr(self, '_annotation_editing_node')
        # 显示批注窗口
        self.annotation_window.handle_addAnnotation(x, y, annotation)
    
    def show_annotation(self):
        """显示当前激活节点的批注窗口（保留用于右键菜单）"""
        if not self.scene.m_activateNode:
            return
        
        # 记录当前正在编辑批注的节点（防止在编辑过程中节点切换）
        self._annotation_editing_node = self.scene.m_activateNode
        
        # 获取节点位置（往左偏移250像素，往上偏移230像素）- 使用NODE_INFO_SIZE以保持与按钮调出窗口一致
        from Config import NODE_INFO_SIZE
        x, y = self.getPos(NODE_INFO_SIZE, offset_x=-250, offset_y=-230)
        # 获取当前批注内容
        annotation_text = getattr(self.scene.m_activateNode, 'm_annotation', '')
        # 显示批注窗口
        self.annotation_window.handle_addAnnotation(x, y, annotation_text)
    
    def show_node_info(self):
        """显示当前激活节点的信息窗口（批注）"""
        if not self.scene.m_activateNode:
            return
        
        # 记录当前正在编辑的节点（防止在编辑过程中节点切换）
        self._node_info_editing_node = self.scene.m_activateNode
        
        # 获取节点位置（往左偏移250像素，往上偏移230像素）
        from Config import NODE_INFO_SIZE
        x, y = self.getPos(NODE_INFO_SIZE, offset_x=-250, offset_y=-230)
        # 获取当前批注内容
        annotation_text = getattr(self.scene.m_activateNode, 'm_annotation', '')
        # 显示节点信息窗口
        self.node_info_window.handle_showNodeInfo(x, y, annotation_text)

    def about(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('About 429 MindMap')
        msgBox.setText('MindMap written in PyQt5')
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setInformativeText('Report Bug to: \n 1140873504@qq.com')
        pic = QPixmap(self.root + '/images/window.jpg')
        msgBox.setIconPixmap(pic.scaled(50, 50))
        msgBox.exec()

    def hot_key(self):
        if not self.dock.isVisible():
            self.dock.show()

    def add_icon(self):
        if self.icontoolbar.isVisible():
            self.icontoolbar.hide()
        else:
            self.icontoolbar.show()
    
    def toggleHandwriting(self, checked):
        """切换手写模式"""
        if checked:
            # 打开设置对话框，传入当前主题
            dialog = HandwritingDialog(self, theme=self.m_theme)
            if dialog.exec() == QDialog.Accepted:
                settings = dialog.getSettings()
                # 启用手写模式
                self.scene.setHandwritingMode(True, settings)
                # 更新视图的拖拽模式，禁用框选以便绘制
                self.view.setDragMode(QGraphicsView.NoDrag)
                # 设置视图的手写模式状态
                self.view.setHandwritingMode(True, settings['mode'])
                # 更新光标
                if settings['mode'] == 'eraser':
                    self.view.setCursor(QCursor(Qt.PointingHandCursor))
                else:
                    self.view.setCursor(QCursor(Qt.CrossCursor))
                # 按钮保持高亮状态（通过工具栏按钮设置样式）
                # 获取工具栏按钮并设置样式
                toolbar_widgets = self.toolbar.widgetForAction(self.handwriting_action)
                if toolbar_widgets:
                    toolbar_widgets.setStyleSheet("""
                        QToolButton {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FFB6D9, stop:1 #FF9EC7);
                            border: 2px solid #FF8CC8;
                            color: #FFFFFF;
                        }
                    """)
                # 如果 toolbar_widgets 不存在，不需要做任何操作
            else:
                # 用户取消，恢复按钮状态
                self.handwriting_action.setChecked(False)
        else:
            # 关闭手写模式
            self.scene.setHandwritingMode(False, None)
            # 恢复视图的拖拽模式
            self.view.setDragMode(QGraphicsView.RubberBandDrag)
            # 关闭视图的手写模式
            self.view.setHandwritingMode(False, None)
            # 恢复默认光标
            self.view.setCursor(QCursor(Qt.ArrowCursor))
            # 清除按钮高亮状态 - 获取工具栏按钮的 widget 并清除样式
            toolbar_widgets = self.toolbar.widgetForAction(self.handwriting_action)
            if toolbar_widgets:
                toolbar_widgets.setStyleSheet("")
    
    def toggleMoveWithSubtree(self, checked):
        """切换移动子树模式"""
        self.m_moveWithSubtree = checked
        # 更新场景的移动子树模式
        if hasattr(self, 'scene'):
            self.scene.setMoveWithSubtree(checked)
    
    def showTodoList(self):
        """显示 TodoList 对话框"""
        if not hasattr(self, 'todo_list_dialog'):
            self.todo_list_dialog = TodoList(self, theme=self.m_theme)
            # 连接关闭信号，保存 todolist 到当前节点
            self.todo_list_dialog.finished.connect(self.saveTodoList)
        
        # 设置场景和节点引用
        if hasattr(self.scene, 'm_activateNode') and self.scene.m_activateNode:
            self.todo_list_dialog.setSceneAndNode(self.scene, self.scene.m_activateNode)
            # 如果节点有保存的 todolist 数据，加载它
            if hasattr(self.scene.m_activateNode, 'm_todolist'):
                self.todo_list_dialog.loadTodoItems(self.scene.m_activateNode.m_todolist)
            else:
                self.todo_list_dialog.loadTodoItems([])
        else:
            # 如果没有激活节点，提示用户
            QMessageBox.warning(self, 'Warning', 'Please select a node first!')
            return
        
        self.todo_list_dialog.show()
        self.todo_list_dialog.raise_()
        self.todo_list_dialog.activateWindow()
    
    def saveTodoList(self, result):
        """保存 TodoList 到当前节点"""
        if hasattr(self.scene, 'm_activateNode') and self.scene.m_activateNode:
            if hasattr(self, 'todo_list_dialog'):
                self.scene.m_activateNode.m_todolist = self.todo_list_dialog.getTodoItems()
                self.contentChanged(True)
    
    def changeLanguage(self, lang_code):
        """
        切换语言
        
        参数:
        - lang_code: 语言代码，'zh_CN'表示中文，'en_US'表示英文
        
        功能:
        - 更新当前语言设置
        - 更新菜单项的选中状态
        - 更新所有菜单项的文本
        """
        # 更新当前语言
        self.m_language = lang_code
        
        # 更新所有语言选项的选中状态
        for code, action in self.language_actions.items():
            action.setChecked(code == lang_code)
        
        # 更新所有菜单项的文本
        self.updateMenuLanguage()
        
        # 更新批注窗口的文本
        if hasattr(self, 'annotation_window') and self.annotation_window:
            self.annotation_window.updateLanguage()
        if hasattr(self, 'node_info_window') and self.node_info_window:
            self.node_info_window.updateLanguage()
        
        # 显示切换提示信息
        if lang_code == 'zh_CN':
            self.messageShow(self.tr('Language switched to Chinese'))
        else:
            self.messageShow(self.tr('Language switched to English'))
    
    def changeTheme(self, theme_name):
        """
        切换主题
        
        参数:
        - theme_name: 主题名称，'Light'（浅色）、'Dark'（深色）、'Black & White'（黑白）
        
        功能:
        - 更新当前主题设置
        - 更新主题选项的选中状态
        - 应用对应的主题样式
        """
        # 更新当前主题
        self.m_theme = theme_name
        
        # 更新所有主题选项的选中状态
        if hasattr(self, 'theme_actions'):
            for name, action in self.theme_actions.items():
                action.setChecked(name == theme_name)
        
        # 更新场景和视图的主题
        self.scene.setTheme(theme_name)
        self.view.setTheme(theme_name)
        
        # 更新各个子窗口的主题
        if hasattr(self, 'note_window'):
            self.note_window.setTheme(theme_name)
        if hasattr(self, 'link_window'):
            self.link_window.setTheme(theme_name)
        if hasattr(self, 'annotation_window'):
            self.annotation_window.setTheme(theme_name)
        if hasattr(self, 'node_info_window'):
            self.node_info_window.setTheme(theme_name)
        
        # 应用对应的主题样式
        if theme_name == 'Light':
            self.applyModernLightStyle()
            gradient = QLinearGradient(0, 0, 0, 1000)
            gradient.setColorAt(0, QColor(247, 250, 255))
            gradient.setColorAt(1, QColor(238, 245, 253))
            self.scene.setBackgroundBrush(QBrush(gradient))
        elif theme_name == 'Dark':
            # 深色主题
            self.applyDarkStyle()
            # 更新场景背景为深色
            gradient = QLinearGradient(0, 0, 0, 1000)
            gradient.setColorAt(0, QColor(40, 40, 40))  # 深灰色
            gradient.setColorAt(1, QColor(30, 30, 30))  # 更深灰色
            self.scene.setBackgroundBrush(QBrush(gradient))
        elif theme_name == 'Black & White':
            # 黑白主题
            self.applyBlackWhiteStyle()
            # 更新场景背景为白色
            self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255)))
        
        # 应用对话框主题样式（追加到主窗口样式表）
        self.applyDialogTheme()
        # 合并主窗口样式和对话框样式并应用到QApplication
        current_style = self.styleSheet()
        if hasattr(self, 'dialog_style') and self.dialog_style:
            QApplication.instance().setStyleSheet(current_style + self.dialog_style)
        
        # 更新场景主题并刷新所有节点
        if hasattr(self, 'scene'):
            self.scene.setTheme(theme_name)
        
        # 更新视图的虚线框主题
        if hasattr(self, 'view') and self.view:
            self.view.setTheme(theme_name)
        
        # 更新已打开的TodoList对话框主题
        if hasattr(self, 'todo_list_dialog') and self.todo_list_dialog:
            self.todo_list_dialog.setTheme(theme_name)
        
        # 更新Note、Link和Annotation窗口主题（如果已创建）
        if hasattr(self, 'note_window') and self.note_window:
            self.note_window.setTheme(theme_name)
        if hasattr(self, 'link_window') and self.link_window:
            self.link_window.setTheme(theme_name)
        if hasattr(self, 'annotation_window') and self.annotation_window:
            self.annotation_window.setTheme(theme_name)
        
        # 显示切换提示信息
        if self.m_language == 'zh_CN':
            self.messageShow('主题已切换为：' + self.tr(theme_name))
        else:
            self.messageShow('Theme switched to: ' + self.tr(theme_name))
    
    def applyDarkStyle(self):
        """应用深色主题样式"""
        dark_style = """
        /* 主窗口背景 - 深色 */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2B2B2B, stop:1 #1E1E1E);
        }
        
        /* 菜单栏样式 */
        QMenuBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3C3C3C, stop:1 #2B2B2B);
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11pt;
            padding: 4px;
            border-bottom: 2px solid #555555;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 6px 12px;
            border-radius: 8px;
        }
        
        QMenuBar::item:selected {
            background: #555555;
        }
        
        QMenuBar::item:pressed {
            background: #666666;
        }
        
        /* 菜单样式 */
        QMenu {
            background: #2B2B2B;
            border: 2px solid #555555;
            border-radius: 8px;
            padding: 4px;
            color: #FFFFFF;
            font-size: 10pt;
        }
        
        QMenu::item {
            padding: 8px 24px 8px 32px;
            border-radius: 6px;
            margin: 2px;
        }
        
        QMenu::item:selected {
            background: #555555;
            color: #FFFFFF;
        }
        
        QMenu::separator {
            height: 1px;
            background: #555555;
            margin: 4px 8px;
        }
        
        /* 工具栏样式 */
        QToolBar {
            background: #2B2B2B;
            border: none;
            padding: 4px;
            spacing: 4px;
        }
        
        QToolButton {
            background: #3C3C3C;
            border: 2px solid #555555;
            border-radius: 8px;
            padding: 6px;
            color: #FFFFFF;
            font-weight: bold;
            min-width: 160px;
            min-height: 90px;
            max-width: 250px;
            max-height: 90px;
            text-align: center;
        }
        
        QToolButton:hover {
            background: #555555;
            border: 2px solid #666666;
            color: #FFFFFF;
        }
        
        QToolButton:pressed {
            background: #666666;
        }
        
        QToolButton:checked {
            background: #666666;
            border: 2px solid #777777;
            color: #FFFFFF;
        }
        
        QToolButton:checked:hover {
            background: #777777;
            border: 2px solid #888888;
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background: #2B2B2B;
            color: #FFFFFF;
            font-weight: bold;
            border-top: 2px solid #555555;
            padding: 4px;
        }
        
        QStatusBar::item {
            border: none;
        }
        
        QLabel {
            color: #FFFFFF;
            font-weight: bold;
            padding: 2px 8px;
        }
        """
        self.setStyleSheet(dark_style)
    
    def applyBlackWhiteStyle(self):
        """应用黑白主题样式"""
        bw_style = """
        /* 主窗口背景 - 白色 */
        QMainWindow {
            background: #FFFFFF;
        }
        
        /* 菜单栏样式 */
        QMenuBar {
            background: #F5F5F5;
            color: #000000;
            font-weight: bold;
            font-size: 11pt;
            padding: 4px;
            border-bottom: 1px solid #CCCCCC;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background: #E0E0E0;
        }
        
        QMenuBar::item:pressed {
            background: #CCCCCC;
        }
        
        /* 菜单样式 */
        QMenu {
            background: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
            font-size: 10pt;
        }
        
        QMenu::item {
            padding: 8px 24px 8px 32px;
            border-radius: 4px;
            margin: 2px;
        }
        
        QMenu::item:selected {
            background: #E0E0E0;
            color: #000000;
        }
        
        QMenu::separator {
            height: 1px;
            background: #CCCCCC;
            margin: 4px 8px;
        }
        
        /* 工具栏样式 */
        QToolBar {
            background: #FFFFFF;
            border: none;
            border-bottom: 1px solid #CCCCCC;
            padding: 4px;
            spacing: 4px;
        }
        
        QToolButton {
            background: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 4px;
            padding: 6px;
            color: #000000;
            font-weight: normal;
            min-width: 160px;
            min-height: 90px;
            max-width: 250px;
            max-height: 90px;
            text-align: center;
        }
        
        QToolButton:hover {
            background: #F5F5F5;
            border: 1px solid #999999;
        }
        
        QToolButton:pressed {
            background: #E0E0E0;
        }
        
        QToolButton:checked {
            background: #CCCCCC;
            border: 1px solid #999999;
            color: #000000;
        }
        
        QToolButton:checked:hover {
            background: #BBBBBB;
            border: 1px solid #888888;
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background: #F5F5F5;
            color: #000000;
            font-weight: normal;
            border-top: 1px solid #CCCCCC;
            padding: 4px;
        }
        
        QStatusBar::item {
            border: none;
        }
        
        QLabel {
            color: #000000;
            font-weight: normal;
            padding: 2px 8px;
        }
        """
        self.setStyleSheet(bw_style)
        
        # 应用对话框主题样式
        self.applyDialogTheme()
    
    def applyDialogTheme(self):
        """
        应用对话框主题样式
        
        功能:
        - 根据当前主题为所有对话框（QColorDialog、QInputDialog、QMessageBox等）设置样式
        - 使用QApplication.setStyleSheet()来全局应用样式
        """
        if self.m_theme == 'Light':
            self.dialog_style = """
            QDialog, QMessageBox, QProgressDialog { background: #F8FAFD; color: #334155; }
            QDialog QLabel, QMessageBox QLabel { color: #475569; }
            QLabel#dialogTitle { color: #163A63; font-size: 17pt; font-weight: 700; }
            QLineEdit, QTextEdit, QComboBox {
                background: #FFFFFF; color: #24364B;
                border: 1px solid #CBD8E8; border-radius: 8px;
                padding: 7px; selection-background-color: #B9D8FF;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 2px solid #4C9AFF; }
            QPushButton {
                background: #FFFFFF; color: #2864B5;
                border: 1px solid #BFD5F2; border-radius: 8px;
                padding: 7px 14px; min-width: 74px;
            }
            QPushButton:hover { background: #EAF3FF; border-color: #7CB2F5; }
            QPushButton:default { background: #1976E9; color: #FFFFFF; border-color: #1976E9; }
            QPushButton:default:hover { background: #0F68D6; }
            QCheckBox { color: #52657B; spacing: 6px; }
            QProgressBar { border: 1px solid #D4DEEA; border-radius: 6px; background: #FFFFFF; }
            QProgressBar::chunk { background: #2496ED; border-radius: 5px; }
            """
            return
        if self.m_theme == 'Light':
            # 浅色主题对话框样式（可爱风格）
            dialog_style = """
            /* QColorDialog样式 */
            QColorDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                color: #000000;
            }
            QColorDialog QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #000000;
                font-weight: bold;
            }
            QColorDialog QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QColorDialog QLabel {
                color: #000000;
            }
            
            /* QInputDialog样式 */
            QInputDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                color: #000000;
            }
            QInputDialog QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #000000;
                font-weight: bold;
            }
            QInputDialog QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QInputDialog QLineEdit {
                border: 2px solid #FFB6D9;
                border-radius: 6px;
                padding: 4px;
                background: #FFFFFF;
                color: #000000;
            }
            QInputDialog QLabel {
                color: #000000;
            }
            
            /* QMessageBox样式 */
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                color: #000000;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #000000;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QMessageBox QLabel {
                color: #000000;
            }
            
            /* QFileDialog样式 */
            QFileDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                color: #000000;
            }
            QFileDialog QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #000000;
                font-weight: bold;
            }
            QFileDialog QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QFileDialog QLabel {
                color: #000000;
            }
            QFileDialog QLineEdit {
                color: #000000;
            }
            QFileDialog QTreeView {
                color: #000000;
            }
            QFileDialog QListView {
                color: #000000;
            }
            
            /* QPrintDialog样式 */
            QPrintDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                color: #000000;
            }
            QPrintDialog QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFE4F0);
                border: 2px solid #FFB6D9;
                border-radius: 8px;
                padding: 6px 16px;
                color: #000000;
                font-weight: bold;
            }
            QPrintDialog QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6D9, stop:1 #FF9EC7);
                color: #FFFFFF;
            }
            QPrintDialog QLabel {
                color: #000000;
            }
            """
        elif self.m_theme == 'Dark':
            # 深色主题对话框样式
            dialog_style = """
            /* QColorDialog样式 */
            QColorDialog {
                background: #2B2B2B;
                color: #FFFFFF;
            }
            QColorDialog QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QColorDialog QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QColorDialog QPushButton:pressed {
                background: #666666;
            }
            
            /* QInputDialog样式 */
            QInputDialog {
                background: #2B2B2B;
                color: #FFFFFF;
            }
            QInputDialog QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QInputDialog QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QInputDialog QLineEdit {
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 4px;
                background: #3C3C3C;
                color: #FFFFFF;
            }
            
            /* QMessageBox样式 */
            QMessageBox {
                background: #2B2B2B;
                color: #FFFFFF;
            }
            QMessageBox QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QMessageBox QPushButton:pressed {
                background: #666666;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
            }
            
            /* QFileDialog样式 */
            QFileDialog {
                background: #2B2B2B;
                color: #FFFFFF;
            }
            QFileDialog QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QFileDialog QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            QFileDialog QTreeView, QFileDialog QListView {
                background: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            QFileDialog QLineEdit {
                background: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            
            /* QPrintDialog样式 */
            QPrintDialog {
                background: #2B2B2B;
                color: #FFFFFF;
            }
            QPrintDialog QPushButton {
                background: #3C3C3C;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px 16px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPrintDialog QPushButton:hover {
                background: #555555;
                border: 2px solid #666666;
            }
            """
        else:  # Black & White
            # 黑白主题对话框样式
            dialog_style = """
            /* QColorDialog样式 */
            QColorDialog {
                background: #FFFFFF;
                color: #000000;
            }
            QColorDialog QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
            }
            QColorDialog QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            
            /* QInputDialog样式 */
            QInputDialog {
                background: #FFFFFF;
                color: #000000;
            }
            QInputDialog QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
            }
            QInputDialog QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QInputDialog QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 4px;
                background: #FFFFFF;
                color: #000000;
            }
            
            /* QMessageBox样式 */
            QMessageBox {
                background: #FFFFFF;
                color: #000000;
            }
            QMessageBox QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            QMessageBox QLabel {
                color: #000000;
            }
            
            /* QFileDialog样式 */
            QFileDialog {
                background: #FFFFFF;
                color: #000000;
            }
            QFileDialog QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
            }
            QFileDialog QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            
            /* QPrintDialog样式 */
            QPrintDialog {
                background: #FFFFFF;
                color: #000000;
            }
            QPrintDialog QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px 16px;
                color: #000000;
                font-weight: normal;
            }
            QPrintDialog QPushButton:hover {
                background: #F5F5F5;
                border: 1px solid #999999;
            }
            """
        
        # 将对话框样式存储
        self.dialog_style = dialog_style
        # 对话框样式已经包含在QApplication的全局样式表中
        # 由于QApplication.setStyleSheet()会覆盖，我们需要在主窗口样式之后应用
        # 但为了避免冲突，我们直接在主窗口样式表中包含对话框样式
        # 这样对话框会自动继承主题样式


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('MyXind')

    window = MainWindow()
    NoteWindow = Note()
    LinkWindow = Link()

    window.addNote.connect(NoteWindow.handle_addnote)
    window.close_signal.connect(NoteWindow.handle_close)
    window.scene.press_close.connect(NoteWindow.handle_close)

    NoteWindow.note.connect(window.getNote)
    NoteWindow.noteChange.connect(window.contentChanged)

    window.addLink.connect(LinkWindow.handle_addLink)
    window.close_signal.connect(LinkWindow.handle_close)
    window.scene.press_close.connect(LinkWindow.handle_close)

    LinkWindow.link.connect(window.getLink)
    LinkWindow.linkChange.connect(window.contentChanged)

    sys.exit(app.exec_())
