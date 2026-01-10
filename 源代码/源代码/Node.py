#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
================================================================================
模块: Node.py
功能: 思维导图节点类的实现
描述: 
    - Node类继承自QGraphicsTextItem，表示思维导图中的主题节点
    - 实现节点的绘制、编辑、移动、缩放等功能
    - 支持插入图片、链接、待办事项列表等扩展功能
    - 通过信号机制与场景（Graph）进行交互
================================================================================
"""

# ============================================================================
# 导入标准库模块
# ============================================================================
import re   # 正则表达式模块，用于解析和替换HTML中的链接
import sys  # 系统相关功能

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *      # 导入Qt图形界面相关的类（QColor, QPen, QPainter等）
from PyQt5.QtCore import *     # 导入Qt核心功能相关的类（pyqtSignal, QPointF, QRectF等）
from PyQt5.QtWidgets import *  # 导入Qt窗口部件相关的类（QGraphicsTextItem等）

# ============================================================================
# 导入自定义模块
# ============================================================================
from Config import *  # 导入配置常量（如MainThemeLevel, SecondThemeLevel等）


class Node(QGraphicsTextItem):
    """Node 节点类，重写自 QGraphicsTextItem

    主要表示思维导图中的一个“主题”节点，并在其上实现：
    - 自定义绘制（圆角矩形背景、文字颜色等）
    - 节点的选择、拖拽、缩放
    - 插入图片、插入/更新链接
    - 与场景（Scene）之间的信号联动，驱动连线、撤销重做等

    信号:
        nodeChanged: 节点内容或大小发生变化
        nodeMoved: 节点被移动（未在当前代码片段中使用）
        nodeEdited: 双击进入编辑模式
        nodeSelected: 鼠标点击选中节点
        nodeLostFocus: 文本编辑失去焦点
    """
    nodeChanged = pyqtSignal()
    nodeMoved = pyqtSignal(int, int)
    nodeEdited = pyqtSignal()
    nodeSelected = pyqtSignal()
    nodeLostFocus = pyqtSignal()

    def __init__(self, *args, **kwargs):
        """初始化节点的默认状态和属性"""
        super(Node, self).__init__(*args, **kwargs)

        # 逻辑结构关系
        self.parentNode = None          # 父节点
        self.sonNode = []               # 子节点列表
        # 简单的几何属性（部分在后面用 sceneBoundingRect 动态更新）
        self.x = 0
        self.y = 0
        self.width = 0
        # self.num = 0

        # 节点业务属性
        self.m_defaultText = ''         # 默认文本
        self.m_note = ''                # 备注内容
        self.m_link = 'https://'        # 默认链接前缀
        self.hasLink = False            # 是否已插入链接
        self.m_todolist = []            # 待办事项列表
        self.m_annotation = ''          # 批注内容
        self.todolist_pixmap_item = None  # todolist 图片项引用
        self.m_size = (60, 30)          # 默认尺寸（目前未直接使用）
        self.m_margin = 30              # 留白（目前 paint 中使用的是 boundingRect）
        self.m_border = False           # 是否画边框
        self.m_color = QColor(Qt.white) # 节点背景色
        self.m_colorCustomized = False  # 颜色是否被用户自定义过
        self.m_level = -1               # 节点层级（中心/分支/子主题等）
        self.m_textColor = QColor(Qt.black)  # 文本颜色
        self.m_editable = False         # 是否可编辑
        self.m_theme = 'Light'          # 主题：'Light'（浅色）、'Dark'（深色）、'Black & White'（黑白）
        # 批注功能不再使用图标，直接点击节点查看

        # 禁用默认的链接自动打开，我们需要自定义处理
        self.setOpenExternalLinks(False)
        # 连接链接激活信号，但在onLinkActivated中会检查是否真的点击了链接图标
        self.linkActivated.connect(self.onLinkActivated)
        # 支持被选中、拖动、位置变化通知
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        # 接受 Hover 事件，用于显示缩放光标
        self.setAcceptHoverEvents(True)

        # 缩放（拖拽右上角“手柄”）相关的状态
        self._resizing = False          # 是否正在缩放
        self._resize_start_pos = None   # 开始缩放时鼠标位置
        self._start_scale = 1.0         # 开始缩放时节点的缩放比例

    def setBorder(self, hasBorder):
        """
        设置是否显示节点边框
        
        功能:
        - 控制节点是否显示激活边框（虚线边框）
        - 激活边框用于标识当前选中的节点
        
        参数:
        - hasBorder: 布尔值，True表示显示边框，False表示隐藏边框
        
        说明:
        - 当节点被激活时，会显示边框以区别于其他节点
        - 边框在paint方法中绘制为虚线样式
        """
        self.m_border = hasBorder
        # 触发重绘，更新边框显示
        self.update()

    def setColor(self, color):
        """
        设置节点背景颜色（用户自定义颜色）
        
        功能:
        - 设置节点的背景颜色
        - 标记颜色已被用户自定义（覆盖主题默认颜色）
        
        参数:
        - color: QColor对象，节点的背景颜色
        
        说明:
        - 此方法用于用户手动设置节点颜色
        - 设置后，节点的颜色会被标记为自定义，主题切换时不会覆盖
        - 与_setColorInternal的区别：此方法会标记为自定义，_setColorInternal不会
        """
        self.m_color = color
        # 标记颜色已被用户自定义（覆盖主题默认颜色）
        self.m_colorCustomized = True
        # 触发重绘，更新颜色显示
        self.update()
    
    def _setColorInternal(self, color):
        """
        内部方法：设置节点背景颜色但不标记为自定义（用于设置默认颜色）
        
        功能:
        - 设置节点的背景颜色，但不标记为自定义
        - 用于设置主题默认颜色，允许主题切换时覆盖
        
        参数:
        - color: QColor对象，节点的背景颜色
        
        说明:
        - 此方法是内部方法，不应被外部直接调用
        - 主要用于setNodeLevel方法中设置主题默认颜色
        - 与setColor的区别：此方法不会标记为自定义，主题切换时会覆盖
        """
        self.m_color = color
        # 触发重绘，更新颜色显示
        self.update()

    def setTextColor(self, textColor):
        """
        设置节点中文本的颜色
        
        功能:
        - 设置节点文本的颜色
        - 立即应用到节点文本显示
        
        参数:
        - textColor: QColor对象，文本的颜色
        
        说明:
        - 文本颜色会影响节点中所有文本的显示
        - 包括节点标题、链接文本等
        - 在paint方法中通过setDefaultTextColor应用
        """
        self.m_textColor = textColor
        # 触发重绘，更新文本颜色显示
        self.update()

    def setMargin(self, margin):
        """
        设置节点的内部边距
        
        功能:
        - 设置节点文本与边框之间的边距
        - 用于控制节点内容与边框的距离
        
        参数:
        - margin: tuple，格式为(水平边距, 垂直边距)或单个数值
        
        说明:
        - 边距用于为节点顶部的信息按钮留出空间
        - 不同层级的节点使用不同的边距值
        - 中心主题节点使用(5, 18)，分支主题使用(3, 18)，子主题使用(2, 18)
        """
        self.margin = margin
        # 触发重绘，更新边距显示
        self.update()

    def setEditable(self, editable):
        """
        设置节点文本是否可被编辑
        
        功能:
        - 控制节点文本的编辑模式
        - 可编辑模式下，用户可以双击节点编辑文本
        - 不可编辑模式下，节点只能浏览和点击链接
        
        参数:
        - editable: 布尔值，True表示可编辑，False表示不可编辑
        
        说明:
        - 可编辑模式：Qt.TextEditorInteraction，允许编辑文本
        - 不可编辑模式：Qt.TextBrowserInteraction，只允许浏览和点击链接
        - 编辑模式切换时，会触发相应的信号通知场景
        """
        if not editable:
            # 不可编辑：禁止文本编辑，只允许浏览/点击链接
            # 先设置为无交互，再设置为浏览器交互（允许点击链接）
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.setTextInteractionFlags(Qt.TextBrowserInteraction)
            return

        # 可编辑：进入文本编辑模式（允许编辑文本）
        self.setTextInteractionFlags(Qt.TextEditorInteraction)

    def setNodeLevel(self, level):
        """根据层级和主题设置节点的默认样式和默认文本"""
        self.m_level = level

        if level == MainThemeLevel:
            # 中心主题
            # 增加顶部边距，为信息按钮留出空间（左右边距5，上下边距18，其中顶部18用于按钮）
            self.setMargin((5, 18))
            # 根据主题设置默认颜色（paint方法会根据主题绘制，这里只设置基础颜色）
            if self.m_theme == 'Light':
                self._setColorInternal(QColor(Qt.red))
                self.setTextColor(QColor(Qt.white))
            elif self.m_theme == 'Dark':
                self._setColorInternal(QColor(70, 80, 120))
                self.setTextColor(QColor(Qt.white))
            else:  # Black & White
                self._setColorInternal(QColor(200, 200, 200))
                self.setTextColor(QColor(Qt.black))
            self.m_colorCustomized = False  # 重置自定义标志
            self.setPlainText('第一级')
        elif level == SecondThemeLevel:
            # 分支主题
            # 增加顶部边距，为信息按钮留出空间
            self.setMargin((3, 18))
            # 根据主题设置默认颜色
            if self.m_theme == 'Light':
                self._setColorInternal(QColor(Qt.gray))
                self.setTextColor(QColor(Qt.black))
            elif self.m_theme == 'Dark':
                self._setColorInternal(QColor(60, 60, 70))
                self.setTextColor(QColor(Qt.white))  # 深色主题保持白色
            else:  # Black & White
                self._setColorInternal(QColor(240, 240, 240))
                self.setTextColor(QColor(Qt.black))  # 黑白主题改为黑色
            self.m_colorCustomized = False  # 重置自定义标志
            self.setPlainText('第二级')
        elif level == ThirdThemeLevel:
            # 子主题
            # 增加顶部边距，为信息按钮留出空间
            self.setMargin((2, 18))
            # 根据主题设置默认颜色
            if self.m_theme == 'Light':
                self._setColorInternal(QColor(Qt.white))
                self.setTextColor(QColor(Qt.black))
            elif self.m_theme == 'Dark':
                self._setColorInternal(QColor(50, 50, 55))
                self.setTextColor(QColor(Qt.white))  # 深色主题保持白色
            else:  # Black & White
                self._setColorInternal(QColor(255, 255, 255))
                self.setTextColor(QColor(Qt.black))  # 黑白主题改为黑色
            self.m_colorCustomized = False  # 重置自定义标志
            self.setPlainText('第三级')
        elif level == FreeThemeLevel:
            # 自由主题
            if self.m_theme == 'Light':
                self._setColorInternal(QColor(Qt.black))
                self.setTextColor(QColor(Qt.white))
            elif self.m_theme == 'Dark':
                self._setColorInternal(QColor(60, 70, 90))
                self.setTextColor(QColor(Qt.white))
            else:  # Black & White
                self._setColorInternal(QColor(230, 230, 230))
                self.setTextColor(QColor(Qt.black))
            self.m_colorCustomized = False  # 重置自定义标志
            # 注意：这里原来代码是 Qt.wwhite，应该是 Qt.white（保留原逻辑不改）
            self.setPlainText('自由主题')

    def insertPicture(self, image):
        """
        在节点文本开头插入一张小图片（图标）
        
        功能:
        - 在节点文本的开头位置插入一张图片
        - 图片显示为15x15像素的小图标
        
        参数:
        - image: 字符串，图片文件的路径或URL
        
        说明:
        - 图片会插入到文本的最前面
        - 使用HTML的<img>标签实现
        - 图片大小固定为15x15像素
        - 插入图片后，节点大小可能会改变，需要更新连接线
        """
        # 记录当前大小（后续调整连线等可能会用到）
        self.width = self.boundingRect().width()
        self.height = self.boundingRect().height()

        # 将光标移动到文本开头
        c = self.textCursor()
        c.setPosition(0)
        self.setTextCursor(c)

        # 调试输出：查看插入的图片路径
        print(image)
        # 使用 HTML 在文本中插入 <img> 标签
        # 图片大小固定为15x15像素
        c.insertHtml('<img src="{}" width=15 height=15></img>'.format(image))

    def insertLink(self, link):
        """
        在节点开头插入一个链接图标，点击后打开对应网址
        
        功能:
        - 在节点文本的开头位置插入一个链接图标
        - 点击图标后打开对应的网址
        - 链接图标使用SVG格式，大小为15x15像素
        
        参数:
        - link: 字符串，链接的URL地址
        
        说明:
        - 链接图标会插入到文本的最前面
        - 使用HTML的<a>标签和<img>标签实现
        - 链接样式会移除默认的蓝色和下划线，只显示图标
        - 链接颜色会根据节点的文本颜色自动调整
        - 插入链接后，节点的hasLink标志会被设置为True
        """
        # 记录当前大小（后续调整连线等可能会用到）
        self.width = self.boundingRect().width()
        self.height = self.boundingRect().height()

        # 获取文本光标对象
        c = self.textCursor()
        # 调试输出：当前光标对象和文档对象
        print(c)
        print(c.document())

        # 将光标移动到文本开头
        c.setPosition(0)
        self.setTextCursor(c)

        # 获取当前文本颜色，用于链接图标样式（使链接颜色与文本颜色一致）
        text_color = self.m_textColor.name()
        
        # 插入一个超链接，内部用 SVG 图标表示
        # 使用内联样式移除链接的默认样式（蓝色、下划线），确保只图标可点击
        # 在链接标签后添加空格，确保文本不会被链接包裹
        # 注意：SVG路径需要根据实际项目路径调整
        link_html = '<a href="{}" style="text-decoration: none; color: {}; display: inline-block;">' \
                   '<img src="/media/wsl/UBUNTU 18_0/example_pyqt5/MyXmind/images/link.svg" width=15 height=15></img></a> '.format(
                       link, text_color
                   )
        c.insertHtml(link_html)
        # 标记节点已包含链接
        self.hasLink = True

    def updateLink(self, link):
        """
        更新节点中第一个 href 链接为新的链接地址，并确保样式正确
        
        功能:
        - 查找节点HTML中的第一个链接
        - 将链接的URL更新为新的地址
        - 确保链接样式正确（移除默认的蓝色和下划线）
        
        参数:
        - link: 字符串，新的链接URL地址
        
        说明:
        - 使用正则表达式匹配和替换链接URL
        - 只更新第一个链接（如果节点中有多个链接）
        - 链接样式会根据节点的文本颜色自动调整
        - 如果链接标签没有样式属性，会自动添加
        """
        # 获取当前文本颜色，用于链接图标样式（使链接颜色与文本颜色一致）
        text_color = self.m_textColor.name()
        
        # 使用正则表达式匹配 href="xxx" 或 href='xxx' 中的 URL 部分
        # (?<=href=") 表示匹配href="之后的内容
        # .+? 表示非贪婪匹配任意字符
        # (?=") 表示匹配到下一个引号之前
        res_url = r"(?<=href=\").+?(?=\")|(?<=href=\').+?(?=\')"
        html_content = self.toHtml()
        
        # 替换第一个匹配的URL
        updated_html = re.sub(res_url, link, html_content, 1)
        
        # 确保链接标签有正确的样式（移除默认的蓝色和下划线）
        # 如果链接标签没有style属性，添加它
        if 'style=' not in updated_html or 'text-decoration: none' not in updated_html:
            # 查找第一个链接标签并添加样式
            # 匹配 <a href="..."> 或 <a href="..." style="...">
            updated_html = re.sub(
                r'(<a\s+href="[^"]+")(\s*style="[^"]*")?',
                r'\1 style="text-decoration: none; color: {}; display: inline-block;"'.format(text_color),
                updated_html,
                count=1  # 只替换第一个匹配
            )
        
        # 调试输出：打印替换后的完整 HTML
        print(updated_html)
        # 将替换后的 HTML 设置回节点
        self.setHtml(updated_html)

    def onLinkActivated(self, url):
        """
        处理链接激活事件 - 打开链接
        
        功能:
        - 当用户点击节点中的链接时，打开对应的网址
        - 使用系统默认浏览器打开链接
        
        参数:
        - url: 字符串，要打开的链接URL
        
        说明:
        - 此方法连接到QGraphicsTextItem的linkActivated信号
        - 当用户点击链接图标时，会触发此方法
        - 使用QDesktopServices.openUrl打开链接，会调用系统默认浏览器
        - 如果打开失败，会打印错误信息
        """
        # 当linkActivated信号触发时，说明确实点击了链接
        # 直接打开链接
        try:
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            # 使用系统默认浏览器打开链接
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            # 如果打开失败，打印错误信息
            print(f"无法打开链接: {e}")

    def setTheme(self, theme):
        """设置节点主题"""
        self.m_theme = theme
        # 如果节点已经设置了层级，需要根据新主题更新文本颜色
        if self.m_level != -1:
            # 保存当前状态
            current_text = self.toPlainText()
            had_link = self.hasLink
            current_link = self.m_link if had_link else None
            # 保存自定义颜色标志和颜色
            was_color_customized = self.m_colorCustomized
            saved_color = QColor(self.m_color)
            
            # 重新设置层级以更新颜色（但保持文本内容不变）
            # 注意：setNodeLevel 会调用 setPlainText，这会清空HTML内容
            self.setNodeLevel(self.m_level)
            
            # 如果颜色之前被自定义过，恢复自定义颜色和标志
            if was_color_customized:
                self.m_color = saved_color
                self.m_colorCustomized = True
            
            # 如果原来有文本内容，恢复文本（避免被默认文本覆盖）
            if current_text and current_text not in ['第一级', '第二级', '第三级', '自由主题']:
                self.setPlainText(current_text)
                # 确保文本颜色正确设置（setPlainText可能会重置颜色）
                self.setTextColor(self.m_textColor)
            
            # 重置链接标志，因为setPlainText已经清空了HTML
            self.hasLink = False
            
            # 如果原来有链接图标，重新插入
            if had_link and current_link and current_link != 'https://':
                self.insertLink(current_link)
        self.update()  # 触发重绘
    
    def paint(self, painter, option, w):
        """自定义绘制节点背景、边框和文本 - 根据主题和层级设置不同样式"""
        rect = self.boundingRect()
        
        # 根据主题和节点层级设置不同的颜色渐变
        # 如果颜色被自定义过，优先使用自定义颜色
        if self.m_colorCustomized:
            # 使用节点自定义颜色创建渐变
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            base_color = self.m_color
            if self.m_theme == 'Light':
                # 浅色主题：使用更亮的渐变
                lighter = QColor(min(255, base_color.red() + 30), 
                               min(255, base_color.green() + 30), 
                               min(255, base_color.blue() + 30))
                gradient.setColorAt(0, lighter)
                gradient.setColorAt(1, base_color)
                border_color = base_color.darker(120)
                # 选中状态的边框颜色（浅色主题）
                selected_border_color = QColor(255, 107, 181)  # #FF6BB5
                shadow_color1 = QColor(255, 182, 217, 100)
                shadow_color2 = QColor(255, 158, 199, 100)
                border_decor_color = QColor(255, 255, 255, 150)
            elif self.m_theme == 'Dark':
                # 深色主题：使用更暗的渐变
                darker = QColor(max(0, base_color.red() - 40), 
                              max(0, base_color.green() - 40), 
                              max(0, base_color.blue() - 40))
                gradient.setColorAt(0, darker)
                gradient.setColorAt(1, base_color.darker(150))
                border_color = base_color.darker(130)
                # 选中状态的边框颜色（深色主题）
                selected_border_color = QColor(100, 150, 200)  # 亮蓝色
                shadow_color1 = QColor(70, 100, 150, 100)
                shadow_color2 = QColor(50, 80, 130, 100)
                border_decor_color = QColor(200, 200, 200, 100)
            else:  # Black & White
                # 黑白主题：转换为灰度渐变，但保持明显的对比度
                gray_value = int(0.299 * base_color.red() + 0.587 * base_color.green() + 0.114 * base_color.blue())
                # 确保灰度值有足够的对比度，避免和默认灰色太接近
                # 如果灰度值太接近默认值，调整它使其更明显
                if gray_value < 100:
                    # 深色：使用更深的灰色
                    gray_value = max(50, gray_value)
                elif gray_value > 200:
                    # 浅色：使用更浅的灰色
                    gray_value = min(250, gray_value)
                lighter_gray = min(255, gray_value + 40)  # 增加对比度
                darker_gray = max(0, gray_value - 20)  # 增加对比度
                gradient.setColorAt(0, QColor(lighter_gray, lighter_gray, lighter_gray))
                gradient.setColorAt(1, QColor(darker_gray, darker_gray, darker_gray))
                border_color = QColor(max(0, gray_value - 40), max(0, gray_value - 40), max(0, gray_value - 40))
                # 选中状态的边框颜色（黑白主题）
                selected_border_color = QColor(0, 0, 0)  # 黑色
                shadow_color1 = QColor(150, 150, 150, 100)
                shadow_color2 = QColor(120, 120, 120, 100)
                border_decor_color = QColor(100, 100, 100, 150)
            border_width = 3 if self.m_level == MainThemeLevel else 2
        elif self.m_theme == 'Light':
            # 浅色主题 - 二次元可爱风格
            if self.m_level == MainThemeLevel:
                # 中心主题 - 粉紫色渐变
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(255, 182, 217))  # #FFB6D9
                gradient.setColorAt(1, QColor(255, 158, 199))  # #FF9EC7
                border_color = QColor(255, 140, 200)  # #FF8CC8
                border_width = 3
            elif self.m_level == SecondThemeLevel:
                # 分支主题 - 浅粉色渐变
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(255, 228, 240))  # #FFE4F0
                gradient.setColorAt(1, QColor(255, 214, 232))  # #FFD6E8
                border_color = QColor(255, 182, 217)  # #FFB6D9
                border_width = 2
            elif self.m_level == ThirdThemeLevel:
                # 子主题 - 淡粉色渐变
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(255, 245, 250))  # #FFF5FA
                gradient.setColorAt(1, QColor(255, 240, 248))  # #FFF0F8
                border_color = QColor(255, 214, 232)  # #FFD6E8
                border_width = 2
            else:
                # 自由主题或其他 - 使用自定义颜色或默认渐变
                if self.m_color == QColor(Qt.black):
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                    gradient.setColorAt(0, QColor(200, 220, 255))  # 淡蓝色
                    gradient.setColorAt(1, QColor(180, 200, 255))
                    border_color = QColor(150, 180, 255)
                else:
                    # 使用节点自定义颜色创建渐变
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                    base_color = self.m_color
                    lighter = QColor(min(255, base_color.red() + 30), 
                                   min(255, base_color.green() + 30), 
                                   min(255, base_color.blue() + 30))
                    gradient.setColorAt(0, lighter)
                    gradient.setColorAt(1, base_color)
                    border_color = base_color.darker(120)
                border_width = 2
            # 选中状态的边框颜色（浅色主题）
            selected_border_color = QColor(255, 107, 181)  # #FF6BB5
            shadow_color1 = QColor(255, 182, 217, 100)
            shadow_color2 = QColor(255, 158, 199, 100)
            border_decor_color = QColor(255, 255, 255, 150)
        elif self.m_theme == 'Dark':
            # 深色主题
            if self.m_level == MainThemeLevel:
                # 中心主题 - 深蓝紫色渐变
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(70, 80, 120))  # 深蓝紫
                gradient.setColorAt(1, QColor(50, 60, 100))
                border_color = QColor(90, 100, 140)
                border_width = 3
            elif self.m_level == SecondThemeLevel:
                # 分支主题 - 深灰色渐变
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(60, 60, 70))  # 深灰
                gradient.setColorAt(1, QColor(50, 50, 60))
                border_color = QColor(80, 80, 90)
                border_width = 2
            elif self.m_level == ThirdThemeLevel:
                # 子主题 - 中灰色渐变
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(50, 50, 55))  # 中灰
                gradient.setColorAt(1, QColor(45, 45, 50))
                border_color = QColor(70, 70, 75)
                border_width = 2
            else:
                # 自由主题或其他 - 使用自定义颜色或默认渐变
                if self.m_color == QColor(Qt.black):
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                    gradient.setColorAt(0, QColor(60, 70, 90))
                    gradient.setColorAt(1, QColor(50, 60, 80))
                    border_color = QColor(80, 90, 110)
                else:
                    # 使用节点自定义颜色创建渐变（变暗）
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                    base_color = self.m_color
                    darker = QColor(max(0, base_color.red() - 40), 
                                  max(0, base_color.green() - 40), 
                                  max(0, base_color.blue() - 40))
                    gradient.setColorAt(0, darker)
                    gradient.setColorAt(1, base_color.darker(150))
                    border_color = base_color.darker(130)
                border_width = 2
            # 选中状态的边框颜色（深色主题）
            selected_border_color = QColor(100, 150, 200)  # 亮蓝色
            shadow_color1 = QColor(70, 100, 150, 100)
            shadow_color2 = QColor(50, 80, 130, 100)
            border_decor_color = QColor(200, 200, 200, 100)
        else:  # Black & White
            # 黑白主题
            if self.m_level == MainThemeLevel:
                # 中心主题 - 深灰色
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(200, 200, 200))  # 浅灰
                gradient.setColorAt(1, QColor(150, 150, 150))  # 中灰
                border_color = QColor(100, 100, 100)  # 深灰
                border_width = 3
            elif self.m_level == SecondThemeLevel:
                # 分支主题 - 浅灰色
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(240, 240, 240))  # 很浅灰
                gradient.setColorAt(1, QColor(220, 220, 220))  # 浅灰
                border_color = QColor(180, 180, 180)  # 中灰
                border_width = 2
            elif self.m_level == ThirdThemeLevel:
                # 子主题 - 白色
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, QColor(255, 255, 255))  # 白色
                gradient.setColorAt(1, QColor(250, 250, 250))  # 几乎白色
                border_color = QColor(200, 200, 200)  # 浅灰
                border_width = 2
            else:
                # 自由主题或其他 - 使用自定义颜色或默认渐变
                if self.m_color == QColor(Qt.black):
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                    gradient.setColorAt(0, QColor(230, 230, 230))
                    gradient.setColorAt(1, QColor(210, 210, 210))
                    border_color = QColor(180, 180, 180)
                else:
                    # 使用节点自定义颜色创建渐变（转换为灰度）
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                    base_color = self.m_color
                    gray_value = int(0.299 * base_color.red() + 0.587 * base_color.green() + 0.114 * base_color.blue())
                    lighter_gray = min(255, gray_value + 30)
                    gradient.setColorAt(0, QColor(lighter_gray, lighter_gray, lighter_gray))
                    gradient.setColorAt(1, QColor(gray_value, gray_value, gray_value))
                    border_color = QColor(max(0, gray_value - 30), max(0, gray_value - 30), max(0, gray_value - 30))
                border_width = 2
            # 选中状态的边框颜色（黑白主题）
            selected_border_color = QColor(0, 0, 0)  # 黑色
            shadow_color1 = QColor(150, 150, 150, 100)
            shadow_color2 = QColor(120, 120, 120, 100)
            border_decor_color = QColor(100, 100, 100, 150)
        
        # 如果节点被选中，使用更鲜艳的边框
        if self.isSelected():
            border_color = selected_border_color
            border_width = 3
            # 添加阴影效果
            shadow_rect = rect.adjusted(2, 2, 2, 2)
            shadow_gradient = QLinearGradient(shadow_rect.topLeft(), shadow_rect.bottomRight())
            shadow_gradient.setColorAt(0, shadow_color1)
            shadow_gradient.setColorAt(1, shadow_color2)
            painter.setBrush(QBrush(shadow_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(shadow_rect, 12.0, 6.0)
        
        # 绘制主背景（带渐变）
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QBrush(border_color), border_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRoundedRect(rect, 12.0, 6.0)  # 更大的圆角，更可爱
        
        # 如果节点有边框标记（激活状态），绘制额外的装饰
        if self.m_border:
            # 绘制一个更细的内边框作为装饰
            inner_rect = rect.adjusted(2, 2, -2, -2)
            painter.setPen(QPen(border_decor_color, 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(inner_rect, 10.0, 5.0)
        
        painter.setBrush(Qt.NoBrush)
        # 设置默认文本颜色
        self.setDefaultTextColor(self.m_textColor)

        super().paint(painter, option, w)

        # 在节点顶部绘制一个小按钮，用于呼出节点信息窗口
        try:
            br = self.boundingRect()
            # 按钮尺寸：宽度30，高度3，位于顶部中央
            button_width = 30
            button_height = 3
            button_x = br.center().x() - button_width / 2
            # 按钮放在节点矩形内部，距离顶部2像素
            button_y = br.top() + 2
            button_rect = QRectF(button_x, button_y, button_width, button_height)
            
            # 根据主题设置按钮颜色
            if self.m_theme == 'Light':
                button_color = QColor(255, 182, 217)  # 粉色
                button_border = QColor(255, 140, 200)
            elif self.m_theme == 'Dark':
                button_color = QColor(100, 150, 200)  # 蓝色
                button_border = QColor(80, 130, 180)
            else:  # Black & White
                button_color = QColor(200, 200, 200)  # 灰色
                button_border = QColor(150, 150, 150)
            
            # 绘制按钮背景（纯实心填充，无文字）
            painter.setBrush(QBrush(button_color))
            painter.setPen(QPen(button_border, 1))
            painter.drawRoundedRect(button_rect, 2, 2)
        except Exception:
            pass
        
        # 当节点被选中时，在右下角绘制一个缩放手柄，根据主题使用不同颜色
        # 放在右下角避免与右上角的图标（批注图标、链接图标）重叠
        try:
            if self.isSelected():
                hs = 14
                br = self.boundingRect()
                # 将缩放手柄移到右下角，稍微超出右边界以便更容易点击
                handle_rect = QRectF(br.right() - hs + 4, br.bottom() - hs - 2, hs, hs)
                
                # 根据主题设置颜色
                if self.m_theme == 'Light':
                    # 浅色主题 - 粉色渐变
                    handle_gradient = QRadialGradient(handle_rect.center(), hs/2)
                    handle_gradient.setColorAt(0, QColor(255, 182, 217))
                    handle_gradient.setColorAt(1, QColor(255, 140, 200))
                    pen_color = QColor(255, 107, 181)
                    center_color = QColor(255, 255, 255)
                elif self.m_theme == 'Dark':
                    # 深色主题 - 亮蓝色渐变
                    handle_gradient = QRadialGradient(handle_rect.center(), hs/2)
                    handle_gradient.setColorAt(0, QColor(120, 170, 220))
                    handle_gradient.setColorAt(1, QColor(100, 150, 200))
                    pen_color = QColor(80, 130, 180)
                    center_color = QColor(255, 255, 255)
                else:  # Black & White
                    # 黑白主题 - 灰色渐变
                    handle_gradient = QRadialGradient(handle_rect.center(), hs/2)
                    handle_gradient.setColorAt(0, QColor(200, 200, 200))
                    handle_gradient.setColorAt(1, QColor(150, 150, 150))
                    pen_color = QColor(120, 120, 120)
                    center_color = QColor(255, 255, 255)
                
                painter.setBrush(QBrush(handle_gradient))
                painter.setPen(QPen(pen_color, 2))
                painter.drawEllipse(handle_rect)
                # 在中心绘制一个小点
                center = handle_rect.center()
                painter.setBrush(QBrush(center_color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(center, 3, 3)
        except Exception:
            pass


    def itemChange(self, change, value):
        """
        当节点的属性发生变化时，发出相应的信号
        
        功能:
        - 监听节点的属性变化（如位置变化）
        - 当位置变化时，发出nodeChanged信号，通知场景更新连接线
        
        参数:
        - change: QGraphicsItem.GraphicsItemChange枚举值，表示变化的类型
        - value: 变化后的新值
        
        返回:
        - 调用父类的itemChange方法并返回结果
        
        说明:
        - 当节点位置变化时（ItemPositionHasChanged），发出nodeChanged信号
        - 场景会监听此信号，自动更新连接线的位置
        - 其他类型的变化（如选择状态变化）由父类处理
        """
        # 当节点的位置发生变化时，发出 nodeChanged 信号，通知外部更新连线等
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.nodeChanged.emit()

        # 调用父类方法处理其他变化
        return super().itemChange(change, value)

    def mousePressEvent(self, e):
        """鼠标按下事件：判断是否点在信息按钮、缩放手柄上，或开始拖拽分组移动"""
        # 先判断是否点击在顶部信息按钮区域
        try:
            br = self.boundingRect()
            button_width = 30
            button_height = 3
            button_x = br.center().x() - button_width / 2
            # 按钮位置与绘制时保持一致
            button_y = br.top() + 2
            button_rect = QRectF(button_x, button_y, button_width, button_height)
            if e.button() == Qt.LeftButton and button_rect.contains(e.pos()):
                # 点击了信息按钮，触发显示节点信息窗口
                # 先设置当前节点为激活节点
                if self.scene() and hasattr(self.scene(), 'setActivateNode'):
                    self.scene().setActivateNode(self)
                # 触发显示节点信息信号
                if self.scene() and hasattr(self.scene(), 'showNodeInfo'):
                    self.scene().showNodeInfo.emit()
                e.accept()
                return
        except Exception:
            pass
        
        # 再判断是否点击在右下角的缩放手柄区域
        try:
            hs = 14  # handle size in item coordinates (与绘制时保持一致)
            br = self.boundingRect()
            # 将缩放手柄移到右下角，稍微超出右边界以便更容易点击
            handle_rect = QRectF(br.right() - hs + 4, br.bottom() - hs - 2, hs, hs)
            if e.button() == Qt.LeftButton and handle_rect.contains(e.pos()):
                # 开始缩放：先确保节点被选中
                self.setSelected(True)
                self.nodeSelected.emit()
                self._resizing = True
                # 使用场景坐标来计算缩放，确保缩放跟手
                self._resize_start_pos = QPointF(e.scenePos())
                self._resize_start_width = self.boundingRect().width() * self.scale()
                self._start_scale = self.scale()
                # 缩放时禁止拖动节点本身
                self.setFlag(QGraphicsItem.ItemIsMovable, False)
                e.accept()
                return
        except Exception:
            pass

        # 检查是否点击在链接图标区域（如果有链接的话）
        if self.hasLink and e.button() == Qt.LeftButton:
            try:
                click_pos = e.pos()
                # 考虑节点的缩放比例（默认是280%，即2.8倍）
                scale_factor = self.scale()
                # 检查点击位置是否在文本开头的图标区域
                # 链接图标在文本开头，大约15x15像素，考虑缩放后大约是42x42像素
                # 加上一些容差，使用50x50像素
                icon_size = 50 / scale_factor if scale_factor > 0 else 25
                if click_pos.x() < icon_size and click_pos.y() < icon_size:
                    # 点击在链接图标区域，打开链接
                    if self.m_link and self.m_link != 'https://':
                        from PyQt5.QtCore import QUrl
                        from PyQt5.QtGui import QDesktopServices
                        QDesktopServices.openUrl(QUrl(self.m_link))
                        e.accept()
                        return
            except Exception as ex:
                print(f"Error opening link: {ex}")
                pass
        
        # 若不是点击在手柄上，则交由父类处理（包含选择等默认行为）
        super().mousePressEvent(e)

        # 在默认处理后发出选中信号，方便 Graph/Scene 感知当前激活节点
        self.nodeSelected.emit()

        # 为可能的"多选一起拖动"做准备：
        # 记录当前场景中所有被选中的图元及其原始位置，后续移动时一起更新
        try:
            if e.button() == Qt.LeftButton and self.scene():
                selected = [it for it in self.scene().selectedItems() if isinstance(it, QGraphicsItem)]
                self._group_selected = selected if len(selected) > 1 else None  # 只有多个选中时才使用分组
                if self._group_selected:
                    self._group_orig_pos = {it: QPointF(it.pos()) for it in self._group_selected}
                    self._group_press_scene_pos = QPointF(e.scenePos())
                else:
                    # 单个节点拖拽：如果启用了移动子树模式，记录子树节点的原始位置
                    # 确保当前节点被激活
                    if self.scene() and hasattr(self.scene(), 'setActivateNode'):
                        self.scene().setActivateNode(self)
                    
                    # 初始化原始位置字典，包含当前节点
                    self._group_orig_pos = {self: QPointF(self.pos())}
                    
                    # 如果启用了移动子树模式，添加所有子节点和有连线的下级节点
                    if self.scene() and hasattr(self.scene(), 'm_moveWithSubtree') and self.scene().m_moveWithSubtree:
                        subtree = self.scene().getSubTree(self)
                        # getSubTree 包含节点本身，所以我们需要添加所有子节点
                        for child_node in subtree:
                            if child_node != self:  # 跳过节点本身（已经在_group_orig_pos中）
                                self._group_orig_pos[child_node] = QPointF(child_node.pos())
                        
                        # 获取与当前节点有连线的下级节点（层级更高的节点）
                        if hasattr(self.scene(), 'getConnectedLowerLevelNodes'):
                            connected_lower_nodes = self.scene().getConnectedLowerLevelNodes(self)
                            for connected_node in connected_lower_nodes:
                                # 如果该节点还没有被添加到_group_orig_pos中，添加它
                                if connected_node not in self._group_orig_pos:
                                    self._group_orig_pos[connected_node] = QPointF(connected_node.pos())
                                    # 同时添加该节点的子树（如果有）
                                    if hasattr(self.scene(), 'getSubTree'):
                                        connected_subtree = self.scene().getSubTree(connected_node)
                                        for sub_node in connected_subtree:
                                            if sub_node != connected_node and sub_node not in self._group_orig_pos:
                                                self._group_orig_pos[sub_node] = QPointF(sub_node.pos())
                        
                        # 调试输出
                        print(f"移动子树模式：记录了 {len(self._group_orig_pos)} 个节点的位置（包括有连线的下级节点）")
                    else:
                        print(f"单节点移动模式：只记录当前节点")
                    
                    self._group_press_scene_pos = QPointF(e.scenePos())
                self._dragging = True
        except Exception as ex:
            print(f"Error in mousePressEvent: {ex}")
            self._group_selected = None
            self._group_orig_pos = None
            self._group_press_scene_pos = None
            self._dragging = False

    def mouseDoubleClickEvent(self, e):
        """
        双击节点事件处理
        
        功能:
        - 记录节点的当前大小
        - 发出nodeEdited信号，通知场景节点进入编辑模式
        
        参数:
        - e: QGraphicsSceneMouseEvent对象，包含鼠标事件信息
        
        说明:
        - 双击节点通常会进入文本编辑模式
        - 场景会监听nodeEdited信号，执行相应的编辑操作
        - 记录节点大小用于后续调整连接线等操作
        """
        # 记录节点的当前大小（用于后续调整连线等操作）
        self.width = self.boundingRect().width()
        self.height = self.boundingRect().height()
        # 发出节点编辑信号（通常用于弹出编辑对话框等）
        self.nodeEdited.emit()

    def hoverMoveEvent(self, e):
        """
        鼠标悬停移动事件处理
        
        功能:
        - 检测鼠标是否悬停在信息按钮或缩放手柄上
        - 根据悬停位置显示相应的光标样式
        
        参数:
        - e: QGraphicsSceneHoverEvent对象，包含鼠标悬停事件信息
        
        说明:
        - 悬停在信息按钮上：显示手型光标（PointingHandCursor）
        - 悬停在缩放手柄上：显示缩放光标（SizeFDiagCursor）
        - 其他位置：显示默认箭头光标（ArrowCursor）
        """
        try:
            br = self.boundingRect()
            
            # 检查是否悬停在顶部信息按钮上
            button_width = 30
            button_height = 3
            button_x = br.center().x() - button_width / 2
            # 按钮位置与绘制时保持一致
            button_y = br.top() + 2
            button_rect = QRectF(button_x, button_y, button_width, button_height)
            if button_rect.contains(e.pos()):
                self.setCursor(Qt.PointingHandCursor)
                super().hoverMoveEvent(e)
                return
            
            # 检查是否悬停在缩放手柄上
            hs = 14  # 与绘制时保持一致
            handle_rect = QRectF(br.right() - hs + 4, br.bottom() - hs - 2, hs, hs)
            if handle_rect.contains(e.pos()):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        except Exception:
            pass
        super().hoverMoveEvent(e)

    def hoverLeaveEvent(self, e):
        """
        鼠标离开节点事件处理
        
        功能:
        - 当鼠标离开节点时，将光标恢复为默认箭头
        
        参数:
        - e: QGraphicsSceneHoverEvent对象，包含鼠标离开事件信息
        
        说明:
        - 当鼠标离开节点区域时，恢复默认光标样式
        - 用于清除之前设置的特殊光标（如手型光标、缩放光标）
        """
        try:
            self.setCursor(Qt.ArrowCursor)
        except Exception:
            pass
        super().hoverLeaveEvent(e)

    def mouseMoveEvent(self, e):
        """鼠标移动事件：处理缩放和拖拽两种情况"""
        # If currently resizing via the handle, scale the item according to
        # horizontal drag delta and update branches live.
        if getattr(self, '_resizing', False):
            try:
                start_pos = getattr(self, '_resize_start_pos', None)
                start_width = getattr(self, '_resize_start_width', None)
                if start_pos is None or start_width is None:
                    return
                
                # 记录旧的位置和大小，用于更新场景
                old_rect = self.sceneBoundingRect()
                
                # 使用场景坐标来计算缩放，确保缩放跟手
                current_scene_pos = e.scenePos()
                delta_x = current_scene_pos.x() - start_pos.x()
                # 根据场景坐标的移动距离来计算缩放比例
                if start_width != 0:
                    factor = 1.0 + (delta_x / start_width)
                    new_scale = max(0.2, self._start_scale * factor)
                else:
                    new_scale = self._start_scale
                # 根据横向拖动距离调整缩放比例，限制不小于 0.2
                self.setScale(new_scale)
                
                # 获取新的位置和大小
                new_rect = self.sceneBoundingRect()
                
                # 更新记录的大小，并通知场景重绘连线
                try:
                    if self.scene():
                        # update width/height bookkeeping from sceneBoundingRect
                        self.width = self.sceneBoundingRect().width()
                        self.height = self.sceneBoundingRect().height()
                        self.scene().adjustBranch()
                        
                        # 更新场景的绘制区域（旧位置和新位置的并集）
                        update_rect = old_rect.united(new_rect)
                        # 扩大更新区域，确保清除所有残留
                        update_rect.adjust(-10, -10, 10, 10)
                        self.scene().update(update_rect)
                except Exception:
                    pass
            except Exception:
                pass
            return

        # 拖拽时：立即移动图元本身，让连线实时跟随
        # 注意：此处不连续发出 nodeMoved，而是在鼠标释放时统一压入一个 MoveCommand，
        # 以方便撤销/重做记录"整体移动距离"。
        # During dragging (for any node), move items visually immediately so branches
        # follow the node. We handle both root and child nodes here.
        if getattr(self, '_dragging', False):
            # 记录所有要移动节点的旧位置，用于更新场景
            old_rects = {}
            if getattr(self, '_group_selected', None):
                # 多选节点拖拽
                for it in self._group_selected:
                    if isinstance(it, Node):
                        old_rects[it] = it.sceneBoundingRect()
            else:
                # 单个节点拖拽（可能包含子树）
                if self._group_orig_pos:
                    for node in self._group_orig_pos.keys():
                        if isinstance(node, Node):
                            old_rects[node] = node.sceneBoundingRect()
                else:
                    old_rects[self] = self.sceneBoundingRect()
            
            if getattr(self, '_group_selected', None):
                # 计算相对按下时的位移增量，应用到每个被选中的图元上
                delta = QPointF(e.scenePos() - self._group_press_scene_pos)
                for it, orig in self._group_orig_pos.items():
                    it.setPos(orig + delta)
                try:
                    # 通知场景更新所有连线
                    if self.scene():
                        self.scene().adjustBranch()
                        
                        # 更新场景的绘制区域（所有移动节点的旧位置和新位置的并集）
                        update_rect = QRectF()
                        for it in self._group_selected:
                            if isinstance(it, Node):
                                new_rect = it.sceneBoundingRect()
                                old_rect = old_rects.get(it, new_rect)
                                if update_rect.isNull():
                                    update_rect = old_rect.united(new_rect)
                                else:
                                    update_rect = update_rect.united(old_rect).united(new_rect)
                        # 扩大更新区域，确保清除所有残留
                        update_rect.adjust(-10, -10, 10, 10)
                        self.scene().update(update_rect)
                except Exception:
                    pass
            else:
                # 单个节点拖拽：根据移动子树模式决定移动哪些节点
                if getattr(self, '_group_press_scene_pos', None) is None:
                    # fallback to default behavior
                    super().mouseMoveEvent(e)
                    return
                delta = QPointF(e.scenePos() - self._group_press_scene_pos)
                # 移动所有在_group_orig_pos中记录的节点（包括子树节点）
                if self._group_orig_pos:
                    moved_count = 0
                    for node, orig in self._group_orig_pos.items():
                        if isinstance(node, Node):  # 确保是Node实例
                            node.setPos(orig + delta)
                            # 更新节点的x, y属性
                            node.x = orig.x() + delta.x()
                            node.y = orig.y() + delta.y()
                            moved_count += 1
                    # 调试输出
                    if moved_count > 1:
                        print(f"移动了 {moved_count} 个节点（包括子树）")
                else:
                    # 如果没有记录，只移动当前节点
                    orig = QPointF(self.pos() - delta)
                    self.setPos(orig + delta)
                    self.x = orig.x() + delta.x()
                    self.y = orig.y() + delta.y()
                
                try:
                    if self.scene():
                        self.scene().adjustBranch()
                        
                        # 更新场景的绘制区域（所有移动节点的旧位置和新位置的并集）
                        update_rect = QRectF()
                        if self._group_orig_pos:
                            for node in self._group_orig_pos.keys():
                                if isinstance(node, Node):
                                    new_rect = node.sceneBoundingRect()
                                    old_rect = old_rects.get(node, new_rect)
                                    if update_rect.isNull():
                                        update_rect = old_rect.united(new_rect)
                                    else:
                                        update_rect = update_rect.united(old_rect).united(new_rect)
                        else:
                            # 只移动当前节点
                            new_rect = self.sceneBoundingRect()
                            old_rect = old_rects.get(self, new_rect)
                            update_rect = old_rect.united(new_rect)
                        
                        # 扩大更新区域，确保清除所有残留
                        update_rect.adjust(-10, -10, 10, 10)
                        self.scene().update(update_rect)
                except Exception:
                    pass
        else:
            # 未处于拖拽状态时，交回父类默认行为
            super().mouseMoveEvent(e)

    def focusOutEvent(self, e):
        """文本编辑失去焦点时，发送 nodeLostFocus 信号"""
        self.nodeLostFocus.emit()

    def mouseReleaseEvent(self, e):
        """鼠标释放事件：结束缩放或拖拽，并在拖拽结束时记录撤销/重做命令"""
        # if we were resizing, finish resize and restore flags
        if getattr(self, '_resizing', False):
            try:
                self._resizing = False
                self.setFlag(QGraphicsItem.ItemIsMovable, True)
                # 更新缩放后的尺寸
                try:
                    self.width = self.sceneBoundingRect().width()
                    self.height = self.sceneBoundingRect().height()
                except Exception:
                    pass
                # 通知外部节点已发生变化（用于刷新连线等）
                self.nodeChanged.emit()
            except Exception:
                pass
            super().mouseReleaseEvent(e)
            return

        # 注意：节点信息窗口现在通过顶部按钮触发，不再通过单击整行文字触发

        # 结束拖拽时：计算总位移，并压入一个 MoveCommand，使撤销/重做可以恢复此次移动
        # 视觉上的移动已在拖拽过程中完成，因此这里创建命令时会标记 applied=True，
        # 防止 redo 时再次重复移动一次（具体实现在 MoveCommand 中）。
        try:
            if getattr(self, '_dragging', False) and self.scene():
                if getattr(self, '_group_press_scene_pos', None) is not None:
                    total_delta = QPointF(e.scenePos() - self._group_press_scene_pos)
                    dx = total_delta.x()
                    dy = total_delta.y()
                    if dx != 0 or dy != 0:
                        # 构造与 Graph.nodeMoved 类似的上下文对象
                        from Command import Context, MoveCommand
                        m_context = Context()
                        m_context.m_scene = self.scene()
                        # 确保使用当前节点作为激活节点
                        if not self.scene().m_activateNode or self.scene().m_activateNode != self:
                            self.scene().setActivateNode(self)
                        m_context.m_activateNode = self.scene().m_activateNode
                        # 如果移动的是多个选中节点，则使用该列表；
                        # 否则使用_group_orig_pos中记录的节点（包括子树节点）
                        if getattr(self, '_group_selected', None):
                            # only include Node instances
                            m_context.m_nodeList = [it for it in self._group_selected if isinstance(it, Node)]
                        else:
                            # 使用_group_orig_pos中记录的节点列表（已经在拖拽时移动了）
                            if self._group_orig_pos:
                                # 使用_group_orig_pos中记录的节点列表
                                m_context.m_nodeList = [node for node in self._group_orig_pos.keys() if isinstance(node, Node)]
                            else:
                                # 如果没有记录，只移动当前节点
                                m_context.m_nodeList = [self]
                        m_context.m_pos = [dx, dy]

                        # 将命令压入撤销栈，movement 已经在拖拽中应用，因此这里标记为已应用
                        if getattr(self.scene(), 'm_undoStack', None):
                            moveCommand = MoveCommand(m_context)
                            # set applied flag manually if supported
                            try:
                                moveCommand._applied = True
                            except Exception:
                                pass
                            self.scene().m_undoStack.push(moveCommand)
        except Exception:
            pass

        # 清理临时状态，结束本次拖拽
        self._group_selected = None
        self._group_orig_pos = None
        self._group_press_scene_pos = None
        self._dragging = False

        super().mouseReleaseEvent(e)

