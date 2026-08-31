"""
================================================================================
模块: Graph.py
功能: 思维导图场景（Scene）的实现
描述: 
    - Graph类继承自QGraphicsScene，是整个思维导图的场景管理类
    - 管理所有节点（Node）和连接线（Branch）
    - 实现节点的增删改查、移动、复制粘贴等操作
    - 支持文件的保存和加载（XML格式）
    - 支持导出为PNG和PDF格式
    - 实现手写批注功能
================================================================================
"""

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *          # 导入Qt图形界面相关的类
from PyQt5.QtCore import *         # 导入Qt核心功能相关的类
from PyQt5.QtWidgets import *      # 导入Qt窗口部件相关的类
from PyQt5.QtXml import *          # 导入Qt XML相关类（未使用但保留）
from PyQt5.QtPrintSupport import * # 导入Qt打印支持相关类（用于PDF导出）

# ============================================================================
# 导入标准库模块
# ============================================================================
import os                          # 操作系统相关功能（文件路径处理）
import sys                         # 系统相关功能
import math                        # 数学函数（当前未使用但保留）
import time                        # 时间相关功能（当前未使用但保留）
import random                      # 随机数生成（当前未使用但保留）
import xml.etree.ElementTree as ET # XML解析和生成（用于文件保存和加载）

# ============================================================================
# 导入自定义模块
# ============================================================================
from Node import Node              # 导入节点类
from Branch import Branch          # 导入连接线类
from Command import *              # 导入命令类（用于撤销/重做）
from Config import *               # 导入配置常量
from Annotation import AnnotationItem  # 导入批注项类


class Graph(QGraphicsScene):
    """ReWrite QGraphicsScene

    Add Node and Branch to Scene
    
    Signals:
        contentChanged: node content change signal
        nodeNumChange: num od node changed
        messageShow: message show in status bar
        press_close: press scene close subWindow(Note Window and Link Window)
        addAnnotation: (int, int, str) -> (pos_x, pos_y, annotation_text)
        showAnnotation: show annotation window for current node
        showNodeInfo: show node info window (annotation and link) for current node
    """
    brachDistance = 80
    contentChanged = pyqtSignal()
    nodeNumChange = pyqtSignal(int)
    messageShow = pyqtSignal(str)
    press_close = pyqtSignal()
    addAnnotation = pyqtSignal(int, int, str)
    showAnnotation = pyqtSignal()
    showNodeInfo = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(Graph, self).__init__(*args, **kwargs)

        # Provide a generous, stable workspace instead of relying on Qt's
        # auto-growing scene rectangle. This makes navigation feel like a
        # dedicated concept-map canvas from the first launch.
        self.setSceneRect(-5000, -3500, 10000, 7000)
        self.center_x =  self.sceneRect().x() + self.sceneRect().width()/2
        self.center_y = self.sceneRect().y() + self.sceneRect().height()/2
        self.m_activateNode = None
        # 翻译函数引用，由MainWindow设置
        self.tr_func = None
        # 主题引用，由MainWindow设置
        self.m_theme = 'Light'  # 默认浅色主题
        # 移动子树模式，由MainWindow设置
        self.m_moveWithSubtree = True  # 默认移动节点时同时移动子树

        self.NodeList = []
        self.BranchList = []
        self.AnnotationList = []  # 批注列表
        self.m_context = None
        self.m_editingMode = False
        
        # 手写模式相关
        self.handwritingMode = False
        # 默认颜色根据主题设置（初始为浅色主题）
        self.handwritingSettings = {
            'mode': 'pen',
            'color': QColor(255, 107, 181),  # 浅色主题默认粉色
            'width': 3
        }
        self.currentAnnotation = None
        self.currentPath = None

        # 设置可爱的背景渐变
        gradient = QLinearGradient(0, 0, 0, 1000)
        gradient.setColorAt(0, QColor(255, 245, 250))  # #FFF5FA - 淡粉色
        gradient.setColorAt(1, QColor(255, 240, 248))  # #FFF0F8 - 更淡的粉色
        self.setBackgroundBrush(QBrush(gradient))

        self.addFirstNode()

    def drawBackground(self, painter, rect):
        """Draw a quiet dot grid to give the canvas visual structure."""
        super(Graph, self).drawBackground(painter, rect)
        if self.m_theme == 'Dark':
            dot_color = QColor(85, 98, 125, 105)
        elif self.m_theme == 'Black & White':
            dot_color = QColor(165, 174, 190, 90)
        else:
            dot_color = QColor(174, 190, 214, 105)

        grid = 40
        left = int(math.floor(rect.left() / grid) * grid)
        top = int(math.floor(rect.top() / grid) * grid)
        points = []
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                points.append(QPointF(x, y))
                y += grid
            x += grid
        painter.setPen(QPen(dot_color, 1.4))
        painter.drawPoints(points)

    # ========================================================================
    # 节点工厂方法：生成 Node 并且将 Node 与 Slots 连接
    # ========================================================================
    def nodeFactory(self):
        """
        节点工厂方法，用于创建新的节点并建立信号连接
        
        功能:
        - 创建新的Node实例
        - 设置节点的主题样式
        - 设置节点的初始缩放比例（280%）
        - 连接节点的各种信号到场景的槽函数
        
        返回:
        - Node: 新创建的节点对象
        
        信号连接:
        - nodeChanged -> self.nodeChanged: 节点内容或大小变化时触发
        - nodeEdited -> self.nodeEdited: 节点进入编辑模式时触发
        - nodeSelected -> self.nodeSelected: 节点被选中时触发
        - nodeMoved -> self.nodeMoved: 节点被移动时触发
        - nodeLostFocus -> self.nodeLostFocus: 节点失去焦点时触发
        """
        node = Node()
        # 设置节点的主题（浅色/深色/黑白）
        node.setTheme(self.m_theme)
        
        # A restrained default scale keeps generated maps readable without
        # turning the toolbar-sized labels into oversized cards.
        node.setScale(1.45)

        # 连接节点的各种信号到场景的槽函数，实现节点与场景的交互
        node.nodeChanged.connect(self.nodeChanged)      # 节点变化时更新连接线
        node.nodeEdited.connect(self.nodeEdited)        # 节点编辑时进入编辑模式
        node.nodeSelected.connect(self.nodeSelected)    # 节点选中时激活节点
        node.nodeMoved.connect(self.nodeMoved)          # 节点移动时更新位置
        node.nodeLostFocus.connect(self.nodeLostFocus)   # 节点失去焦点时退出编辑模式

        return node
    
    def setTheme(self, theme):
        """
        设置场景主题并更新所有节点和连接线
        
        功能:
        - 更新场景的主题属性
        - 更新所有节点的主题样式
        - 更新所有连接线的主题样式
        - 根据主题更新手写批注的默认颜色
        
        参数:
        - theme: 主题名称，可选值：'Light'（浅色）、'Dark'（深色）、'Black & White'（黑白）
        
        说明:
        - 主题切换会影响所有节点的背景色、文本颜色、边框样式等
        - 主题切换会影响所有连接线的颜色和样式
        - 手写批注的颜色也会根据主题自动调整
        """
        self.m_theme = theme
        # 更新所有节点的主题（会重新绘制节点）
        for node in self.NodeList:
            node.setTheme(theme)
        # 更新所有连接线的主题（会重新绘制连接线）
        for branch in self.BranchList:
            branch.setTheme(theme)
        # 根据主题更新手写设置的默认颜色
        if theme == 'Light':
            self.handwritingSettings['color'] = QColor(255, 107, 181)  # 粉色
        elif theme == 'Dark':
            self.handwritingSettings['color'] = QColor(100, 150, 200)  # 亮蓝色
        else:  # Black & White
            self.handwritingSettings['color'] = QColor(120, 120, 120)  # 中灰色
    
    def setMoveWithSubtree(self, enabled):
        """
        设置移动子树模式
        
        功能:
        - 控制移动节点时是否同时移动其子树（子节点）
        - 控制移动节点时是否同时移动与其有连线的下级节点
        
        参数:
        - enabled: 布尔值，True表示启用移动子树模式，False表示禁用
        
        说明:
        - 当启用时，移动节点会同时移动其所有子节点和通过连线连接的下级节点
        - 当禁用时，只移动当前节点，子节点和连接的下级节点保持原位置
        """
        self.m_moveWithSubtree = enabled

    def setUndoStack(self, stack):
        """
        设置撤销/重做栈
        
        功能:
        - 将场景与撤销/重做栈关联，使场景的操作可以撤销和重做
        
        参数:
        - stack: QUndoStack对象，用于管理撤销/重做命令
        
        说明:
        - 所有可撤销的操作（如插入节点、删除节点、移动节点、修改颜色等）
          都会创建对应的命令对象并推入此栈
        - 用户可以通过撤销/重做功能恢复或重复之前的操作
        """
        self.m_undoStack = stack

    def addFirstNode(self):
        """
        添加第一个节点（中心主题节点）
        
        功能:
        - 创建思维导图的中心主题节点
        - 将节点放置在场景中心位置
        - 设置节点为中心主题层级（MainThemeLevel）
        - 激活该节点并添加到场景中
        
        说明:
        - 这是场景初始化时调用的方法，用于创建思维导图的根节点
        - 中心主题节点是思维导图的起点，其他所有节点都是它的子节点或后代节点
        - 中心主题节点不能被删除，这是思维导图的基本结构要求
        """
        # 使用工厂方法创建新节点（会自动连接信号）
        node = self.nodeFactory()
        # 将节点放置在场景中心位置
        node.setPos(self.center_x, self.center_y)
        # 设置节点为中心主题层级（会应用相应的样式）
        node.setNodeLevel(MainThemeLevel)

        # 激活该节点（使其成为当前选中的节点）
        self.setActivateNode(node)

        # 将节点添加到场景中（使其显示在界面上）
        self.addItem(node)
        # 将节点添加到场景的节点列表中（用于管理所有节点）
        self.NodeList.append(node)

    # ========================================================================
    # 添加连接线（Branch）
    # ========================================================================
    def addBranch(self, srcNode, dstNode):
        """
        在两个节点之间添加连接线
        
        功能:
        - 创建新的连接线对象
        - 设置连接线的源节点和目标节点
        - 根据当前主题设置连接线的样式
        - 调整连接线的位置，使其正确连接两个节点
        - 将连接线添加到场景中
        
        参数:
        - srcNode: 源节点（连接的起始节点）
        - dstNode: 目标节点（连接的结束节点）
        
        说明:
        - 连接线会自动调整位置，使其从源节点的右侧连接到目标节点的左侧
        - 连接线的颜色和样式会根据当前主题自动设置
        - 连接线的Z值设置为-1，确保节点显示在连接线之上
        """
        # 创建新的连接线对象
        branch = Branch()
        # 设置连接线的源节点和目标节点
        branch.srcNode = srcNode
        branch.dstNode = dstNode
        # 设置连接线的主题（会应用相应的颜色和样式）
        branch.setTheme(self.m_theme)
        # 调整连接线的位置，使其正确连接两个节点
        branch.adjust()

        # 将连接线添加到场景中（使其显示在界面上）
        self.addItem(branch)
        # 将连接线添加到场景的连接线列表中（用于管理所有连接线）
        self.BranchList.append(branch)

    # ========================================================================
    # 删除连接线（Branch）
    # ========================================================================
    def removeBranch(self, m_node):
        """
        删除与指定节点相关的所有连接线
        
        功能:
        - 遍历所有连接线，找到与指定节点相关的连接线
        - 从场景中移除这些连接线
        - 从连接线列表中移除这些连接线
        
        参数:
        - m_node: 节点对象，删除与该节点相关的所有连接线
        
        说明:
        - 当节点被删除时，需要删除所有与该节点相关的连接线
        - 连接线可能是以该节点为源节点或目标节点
        - 此方法会删除所有相关的连接线，无论方向如何
        """
        # 遍历所有连接线
        for branch in self.BranchList:
            # 检查连接线的源节点或目标节点是否为指定节点
            if branch.srcNode == m_node or branch.dstNode == m_node:
                # 从场景中移除连接线（不再显示）
                self.removeItem(branch)
                # 从连接线列表中移除连接线
                self.BranchList.remove(branch)

    # 检查两个节点之间是否存在连接线
    def hasBranch(self, node1, node2):
        """检查两个节点之间是否存在连接线（双向检查）"""
        for branch in self.BranchList:
            if (branch.srcNode == node1 and branch.dstNode == node2) or \
               (branch.srcNode == node2 and branch.dstNode == node1):
                return branch
        return None

    # 删除两个节点之间的连接线
    def removeBranchBetween(self, node1, node2):
        """删除两个节点之间的连接线（双向检查）"""
        branch = self.hasBranch(node1, node2)
        if branch:
            self.removeItem(branch)
            self.BranchList.remove(branch)
            return True
        return False

    # ========================================================================
    # 设置活动节点（激活节点）
    # ========================================================================
    def setActivateNode(self, node):
        """
        设置当前激活的节点
        
        功能:
        - 取消之前激活节点的边框显示
        - 设置新的激活节点
        - 显示新激活节点的边框
        
        参数:
        - node: 要激活的节点对象，如果为None则取消激活
        
        说明:
        - 激活节点是当前被选中的节点，用户的操作（如添加子节点、修改颜色等）
          都是针对激活节点进行的
        - 激活节点会显示边框，以区别于其他节点
        - 如果传入None，则取消激活（不显示任何节点的边框）
        """
        # 如果之前有激活节点，取消其边框显示
        if self.m_activateNode is not None:
            self.m_activateNode.setBorder(False)
        
        # 设置新的激活节点
        self.m_activateNode = node
        # 如果新节点不为None，显示其边框
        if self.m_activateNode is not None:
            self.m_activateNode.setBorder(True)

    # 获得子节点的最大位置
    def getSonNodeMaxPos(self):
        maxY = -float('inf')
        for node in self.getSubTree(self.m_activateNode):
            if node.y > maxY:
                maxY = node.y
        #print('maxY: ', maxY)
        return maxY

    # ========================================================================
    # 获取子树（深度优先搜索）
    # ========================================================================
    def getSubTree(self, node):
        """
        获取指定节点的所有子节点（子树），使用广度优先搜索算法
        
        功能:
        - 从指定节点开始，递归获取其所有子节点
        - 包括直接子节点、子节点的子节点等所有后代节点
        - 返回包含所有子节点的列表
        
        参数:
        - node: 起始节点对象
        
        返回:
        - list: 包含所有子节点的列表（包括起始节点本身）
        
        说明:
        - 使用队列实现广度优先搜索（BFS）
        - 返回的列表中第一个元素是起始节点本身
        - 如果传入None，返回空列表
        - 此方法用于复制、移动、删除子树等操作
        """
        subTree = []
        # 如果节点为None，返回空列表
        if node is None:
            return subTree

        # 使用队列实现广度优先搜索
        queue = []
        queue.insert(0, node)  # 将起始节点加入队列
        
        # 遍历队列，直到所有节点都被处理
        while queue:
            # 从队列尾部取出一个节点
            v = queue.pop()
            # 调试输出：打印节点和其位置
            print('v: {}  center: {} '.format(v, (v.x, v.y)))
            # 将节点添加到子树列表中
            subTree.append(v)
            # 将该节点的所有子节点加入队列（从头部插入，保持广度优先）
            for sonNode in v.sonNode:
                queue.insert(0, sonNode)

        return subTree
    
    # ========================================================================
    # 获取子树的连接线
    # ========================================================================
    def getSubTreeBranch(self, node):
        """
        获取指定节点的子树中的所有连接线
        
        功能:
        - 获取指定节点的所有子节点
        - 找到所有以这些子节点为目标节点的连接线
        - 返回这些连接线的列表
        
        参数:
        - node: 起始节点对象
        
        返回:
        - list: 包含子树中所有连接线的列表
        
        说明:
        - 只返回以子树中的节点为目标节点的连接线
        - 不包括以子树中的节点为源节点的连接线（这些连接线指向子树外部）
        - 此方法用于删除子树时，需要同时删除相关的连接线
        """
        subTreeBranch = [] 
        # 获取指定节点的所有子节点
        nodeList = self.getSubTree(node)
        # 遍历所有连接线，找到目标节点在子树中的连接线
        for branch in self.BranchList:
            # 如果连接线的目标节点在子树中，将其添加到列表
            if branch.dstNode in nodeList:
                subTreeBranch.append(branch)
    
        return subTreeBranch
    
    def getConnectedLowerLevelNodes(self, node):
        """获取与节点有连线的下级节点（层级更高的节点）
        
        参数:
        - node: 当前节点
        
        返回:
        - 与当前节点有连线且层级更高的节点列表
        """
        connected_nodes = []
        for branch in self.BranchList:
            # 检查连接线的两个节点
            other_node = None
            if branch.srcNode == node:
                other_node = branch.dstNode
            elif branch.dstNode == node:
                other_node = branch.srcNode
            
            # 如果找到连接的节点，且该节点的层级更高（是下级节点）
            if other_node and other_node.m_level > node.m_level:
                connected_nodes.append(other_node)
        
        return connected_nodes

    # ========================================================================
    # 移动子树
    # ========================================================================
    def moveTree(self, node, dy):
        """
        移动指定节点及其所有子节点（子树）在垂直方向上的位置
        
        功能:
        - 获取指定节点的所有子节点
        - 将所有子节点在垂直方向上移动指定距离
        - 更新所有子节点的y坐标
        
        参数:
        - node: 起始节点对象
        - dy: 垂直移动距离（像素），正数向下移动，负数向上移动
        
        说明:
        - 此方法用于调整节点位置，避免节点重叠
        - 只移动垂直方向（Y坐标），不改变水平方向（X坐标）
        - 移动后需要调用adjustBranch()更新连接线位置
        """
        # 获取指定节点的所有子节点
        subTree = self.getSubTree(node)
        # 遍历所有子节点，移动它们的位置
        for subNode in subTree:
            # 在场景中移动节点（视觉上的移动）
            subNode.moveBy(0, dy)
            # 更新节点的y坐标（逻辑上的移动）
            subNode.y += dy

    # ========================================================================
    # 递归调整父树节点位置
    # ========================================================================
    def adjustNode(self, parent, son, reverse=False):
        """
        递归调整父节点的其他子节点位置，避免节点重叠
        
        功能:
        - 当添加或删除子节点时，需要调整父节点的其他子节点位置
        - 如果其他子节点在新子节点的上方，向下移动
        - 如果其他子节点在新子节点的下方，向上移动
        - 递归调整父节点的父节点，确保整个树结构协调
        
        参数:
        - parent: 父节点对象
        - son: 新添加或删除的子节点对象
        - reverse: 布尔值，False表示添加节点时的调整，True表示删除节点时的调整
        
        说明:
        - 此方法用于保持节点之间的间距，避免节点重叠
        - reverse参数控制移动方向：False时向下移动上方节点，True时向上移动下方节点
        - 递归调用确保整个树结构都得到调整
        """
        # 根据reverse参数确定移动方向的正负号
        sign = 1 if reverse else -1
        # 遍历父节点的所有子节点
        for node in parent.sonNode:
            # 跳过当前正在处理的子节点
            if node == son:
                continue
            # 如果其他子节点在新子节点的上方，向下移动
            if node.y < son.y:
                # 移动距离为节点边距和高度的一半
                self.moveTree(node, sign * (node.m_margin + node.m_size[1]) / 2)
            # 如果其他子节点在新子节点的下方，向上移动
            elif node.y > son.y:
                # 移动距离为节点边距和高度的一半（负号表示向上）
                self.moveTree(node, -1 * sign * (node.m_margin + node.m_size[1]) / 2)
            else:
                # 如果y坐标相同，跳过（理论上不应该发生）
                continue
        
        # 如果父节点还有父节点，递归调整
        if parent.parentNode:
            self.adjustNode(parent.parentNode, parent, reverse)

    # ========================================================================
    # 调整所有连接线位置（在调整节点位置后调用）
    # ========================================================================
    def adjustBranch(self):
        """
        调整场景中所有连接线的位置
        
        功能:
        - 遍历所有连接线
        - 重新计算每条连接线的起始点和结束点
        - 使连接线正确连接源节点和目标节点
        
        说明:
        - 当节点位置发生变化时，需要调用此方法更新连接线位置
        - 连接线的位置会根据源节点和目标节点的当前位置自动调整
        - 此方法通常在移动节点、添加节点、删除节点后调用
        """
        # 遍历所有连接线，重新调整它们的位置
        for branch in self.BranchList:
            branch.adjust()

    # ========================================================================
    # 获取子节点位置（TODO: 支持两侧节点）
    # ========================================================================
    def getSonPos(self):
        """
        计算激活节点的第一个子节点的位置
        
        功能:
        - 如果激活节点没有子节点，计算第一个子节点的位置（放在右侧，Y坐标对齐）
        - 如果激活节点已有子节点，计算新子节点的位置（放在最后一个子节点下方）
        
        返回:
        - tuple: (x, y) 子节点的位置坐标
        
        说明:
        - 子节点默认放在父节点的右侧
        - 第一个子节点的Y坐标与父节点对齐
        - 后续子节点依次向下排列
        - brachDistance是节点之间的水平间距
        """
        # 如果激活节点没有子节点，这是第一个子节点
        if len(self.m_activateNode.sonNode) == 0:
            # 调试输出：打印节点位置信息
            print('my y: {0}, scene y: {1}:'.format(self.m_activateNode.y, 
                    self.m_activateNode.sceneBoundingRect().y()))
            print('activate Node: ', self.m_activateNode.boundingRect().width())
            # 第一个子节点放在父节点右侧，Y坐标与父节点对齐
            return self.m_activateNode.sceneBoundingRect().width() + \
                    self.m_activateNode.sceneBoundingRect().x() + \
                    self.brachDistance, \
                    self.m_activateNode.sceneBoundingRect().y()
        else:
            # 如果已有子节点，获取子节点中的最大Y坐标
            maxY = self.getSonNodeMaxPos()
            # 新子节点放在最后一个子节点下方，加上边距
            return self.m_activateNode.sceneBoundingRect().width() + \
                    self.m_activateNode.sceneBoundingRect().x() + \
                    self.brachDistance, \
                    maxY + self.m_activateNode.m_margin
    
    def getSonPosForNode(self, parent_node):
        """
        为指定父节点计算第一个子节点的位置
        
        参数:
        - parent_node: 父节点
        
        返回:
        - (x, y): 子节点的位置坐标
        """
        if len(parent_node.sonNode) == 0:
            # 第一个子节点，放在父节点右侧，Y坐标与父节点对齐
            return parent_node.sceneBoundingRect().right() + self.brachDistance, \
                   parent_node.sceneBoundingRect().y()
        else:
            # 如果有子节点，计算在最后一个子节点下方
            last_son = parent_node.sonNode[-1]
            last_son_rect = last_son.sceneBoundingRect()
            return parent_node.sceneBoundingRect().right() + self.brachDistance, \
                   last_son_rect.bottom() + 50

    def layoutTree(self, root_node):
        """Lay out a hierarchy by leaf order to avoid generated-node overlap."""
        if not root_node:
            return

        next_leaf_y = [self.center_y]
        horizontal_gap = 310.0
        vertical_gap = 105.0

        def place(node, depth):
            child_positions = [place(child, depth + 1) for child in node.sonNode]
            if child_positions:
                y_pos = sum(child_positions) / float(len(child_positions))
            else:
                y_pos = next_leaf_y[0]
                next_leaf_y[0] += max(vertical_gap, node.sceneBoundingRect().height() + 44.0)
            x_pos = self.center_x + depth * horizontal_gap
            node.setPos(x_pos, y_pos)
            node.x = x_pos
            node.y = y_pos
            return y_pos

        root_y = place(root_node, 0)
        shift_y = self.center_y - root_y
        if shift_y:
            for node in self.getSubTree(root_node):
                node.setPos(node.x, node.y + shift_y)
                node.y += shift_y

    # ========================================================================
    # 添加子节点
    # ========================================================================
    def addSonNode(self):
        """
        在激活节点下添加一个新的子节点
        
        功能:
        - 检查是否有激活节点
        - 计算新子节点的位置
        - 创建插入节点命令并推入撤销栈
        - 发出内容变化和节点数量变化信号
        
        说明:
        - 新节点的层级根据父节点的层级自动设置：
          * 如果父节点是中心主题，子节点设为分支主题
          * 否则设为子主题
        - 新节点的位置根据父节点的子节点情况自动计算
        - 操作可以通过撤销/重做功能恢复或重复
        - Context对象必须是局部对象，不能共享，否则会导致引用错误
        """
        # 检查是否有激活节点
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        # 创建命令上下文对象（必须是局部对象，不能共享）
        # 注意：Context为局部对象，不要共享为全局对象，引用传递会出现错误
        m_context = Context()
        m_context.m_activateNode = self.m_activateNode  # 设置激活节点
        m_context.m_scene = self                          # 设置场景
        m_context.m_pos = self.getSonPos()               # 计算子节点位置

        # 创建插入节点命令
        insertNodeCommand = InsertNodeCommand(m_context)
        # 将命令推入撤销栈（可以撤销/重做）
        self.m_undoStack.push(insertNodeCommand)
        
        # 发出内容变化信号（通知主窗口文档已修改，需要保存）
        self.contentChanged.emit()
        # 发出节点数量变化信号（通知主窗口更新节点计数）
        self.nodeNumChange.emit(len(self.NodeList))
        # 显示提示信息
        self.messageShow.emit(self.tr('Info: add new node !'))

    def addSiblingNode(self):
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        if not self.m_activateNode.parentNode:
            print('Warning: Bade Node')
            self.messageShow.emit(self.tr('Warning: Bade Node'))
            return

        self.m_activateNode.m_border = False
        self.m_activateNode = self.m_activateNode.parentNode
        self.addSonNode()

    # 删除节点
    def removeNode(self):
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return
        # 检查是否是中心节点（通过层级判断，而不是parentNode）
        # 只有真正的中心节点（MainThemeLevel）才不能删除
        from Config import MainThemeLevel
        if self.m_activateNode.m_level == MainThemeLevel:
            print('Warning: Base Node')
            self.messageShow.emit(self.tr('Warning: Base Node'))
            return

        # 获取要删除的子树节点列表
        subtree_nodes = self.getSubTree(self.m_activateNode)
        
        # 检查子树中的每个节点，是否有通过连线连接到其他节点的下级节点
        # 如果有，这些下级节点不应该被删除
        nodes_to_exclude = set()  # 使用集合避免重复
        
        for node in subtree_nodes:
            # 获取通过连线连接到该节点的下级节点
            connected_lower_nodes = self.getConnectedLowerLevelNodes(node)
            for connected_node in connected_lower_nodes:
                # 检查这个连接的节点是否连接到子树外的节点
                # 如果连接到子树外的节点，则不应该被删除
                should_exclude = False
                for branch in self.BranchList:
                    other_node = None
                    if branch.srcNode == connected_node:
                        other_node = branch.dstNode
                    elif branch.dstNode == connected_node:
                        other_node = branch.srcNode
                    
                    # 如果连接的另一个节点不在子树中，则这个节点应该被排除
                    if other_node and other_node not in subtree_nodes:
                        should_exclude = True
                        break
                
                if should_exclude:
                    # 排除这个节点及其所有子节点（通过父子关系）
                    connected_subtree = self.getSubTree(connected_node)
                    nodes_to_exclude.update(connected_subtree)
        
        # 从删除列表中排除不应该删除的节点
        nodes_to_delete = [node for node in subtree_nodes if node not in nodes_to_exclude]

        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_scene = self
        m_context.m_nodeList = nodes_to_delete

        removeNodeCommand = RemoveNodeCommand(m_context)
        self.m_undoStack.push(removeNodeCommand)

        self.contentChanged.emit()
        self.nodeNumChange.emit(len(self.NodeList))
        self.messageShow.emit(self.tr('Info: remove node !'))

    # Node 移动
    def nodeMoved(self, x, y):
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return
        
        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_scene = self
        m_context.m_pos = [x, y]
        m_context.m_nodeList = self.getSubTree(self.m_activateNode)

        moveCommand = MoveCommand(m_context)
        self.m_undoStack.push(moveCommand)

        self.messageShow.emit(self.tr('Info: move node !'))

    # Node 选中
    def nodeSelected(self):
        sender = self.sender()
        print('node Selected Sender: ', sender)
        # print('node number: ', sender.num)
        self.setActivateNode(sender)
        
        # 如果节点有批注，单击时显示批注窗口（可选：也可以改为双击）
        # 这里先不自动显示，让用户通过双击或右键菜单查看

    # Node 文本编辑
    def nodeEdited(self):
        print('node edited Mode')
        print(self.m_activateNode.toHtml())
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        self.m_editingMode = True
        self.m_activateNode.setEditable(True)
        self.setFocusItem(self.m_activateNode)

        self.messageShow.emit(self.tr('Info: editing node !'))

    def nodeChanged(self):
        #self.adjustBranch()
        self.contentChanged.emit()    

    # 递归调整树, 以使 rootNode 在 subtree 中处于中点
    def adjustSubTreeNode(self):
        dx = self.m_activateNode.sceneBoundingRect().width() - self.m_activateNode.width
        dy = self.m_activateNode.sceneBoundingRect().height() - self.m_activateNode.height
        nodeList = self.getSubTree(self.m_activateNode)
        for node in nodeList:
            if node == self.m_activateNode:
                if dy:
                    self.m_activateNode.y -= dy/2
                    self.m_activateNode.moveBy(0, -dy/2)
                else:
                    continue
            else:
                node.x += dx
                node.moveBy(dx, 0)

    # Node 失焦事件
    def nodeLostFocus(self):
        print('focusOut')
        if self.m_editingMode:
            self.m_editingMode = False
            print(self.m_activateNode.boundingRect().width())
            self.adjustSubTreeNode()
            self.adjustBranch()
            if self.m_activateNode:
                self.m_activateNode.setEditable(False)

    def moveUp(self):
        if self.m_activateNode.parentNode and \
            len(self.m_activateNode.parentNode.sonNode) > 1:
    
            activateY = self.m_activateNode.y
            closestY = -float('inf')
            closestNode = None
        
            for node in self.m_activateNode.parentNode.sonNode:
                if node.y < activateY and closestY < node.y:
                    closestY = node.y
                    closestNode = node
            if closestNode is not None:
                self.setActivateNode(closestNode)
    
    def moveDown(self):
        if self.m_activateNode.parentNode and \
            len(self.m_activateNode.parentNode.sonNode) > 1:

            activateY = self.m_activateNode.y
            closestY = float('inf')
            closestNode = None

            for node in self.m_activateNode.parentNode.sonNode:
                if node.y > activateY and closestY > node.y:
                    closestY = node.y
                    closestNode = node
            if closestNode is not None:
                self.setActivateNode(closestNode)

    def moveRight(self):
        if self.m_activateNode.sonNode:
            minY = float('inf')
            minNode = None
            for node in self.m_activateNode.sonNode:
                if node.y < minY:
                    minY = node.y
                    minNode = node
            self.setActivateNode(minNode)
    
    def moveLeft(self):
        if self.m_activateNode.parentNode:
            self.setActivateNode(self.m_activateNode.parentNode)

    # 通过方向键移动 activateNode
    def keyPressEvent(self, e):
        if self.m_activateNode and not self.m_editingMode:

            if e.key() == Qt.Key_Escape:
                self.nodeLostFocus()

            elif e.key() == Qt.Key_Right:
                self.moveRight()

            elif e.key() == Qt.Key_Left:
                self.moveLeft()

            elif e.key() == Qt.Key_Up:
                self.moveUp()

            elif e.key() == Qt.Key_Down:
                self.moveDown()
            else:
                super().keyPressEvent(e)
        else:
            super().keyPressEvent(e)
    
    # ========================================================================
    # 剪切节点（TODO: 添加到Command，支持撤销和重做）
    # ========================================================================
    def cut(self):
        """
        剪切激活节点及其子树
        
        功能:
        - 检查是否有激活节点
        - 将节点及其子树复制到剪贴板
        - 删除节点及其子树
        
        说明:
        - 剪切操作实际上是复制+删除的组合
        - 目前此操作不支持撤销/重做（TODO: 需要改进）
        - 建议先复制，确认后再删除，或使用删除+撤销的方式
        """
        # 检查是否有激活节点
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        # 先复制节点到剪贴板
        self.copy()
        # 然后删除节点
        self.removeNode()

    # ========================================================================
    # 复制子树
    # ========================================================================
    def copy(self):
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        # 检查是否是中心节点，如果是则提示警告
        from Config import MainThemeLevel
        if self.m_activateNode.m_level == MainThemeLevel:
            self.messageShow.emit(self.tr('Warning: Cannot copy center node!'))
            return

        subTree = []
        nodeList = self.getSubTree(self.m_activateNode)
        # 创建节点位置到节点的映射，用于保存连接线
        pos_to_node = {}
        
        for node in nodeList:
            subTreeNode = {}
            subTreeNode['htmlContent'] = node.toHtml()
            subTreeNode['pos'] = (node.x, node.y)
            subTreeNode['m_level'] = node.m_level  # 保存节点层级
            # 保存节点的其他属性
            subTreeNode['m_color_red'] = node.m_color.red()
            subTreeNode['m_color_green'] = node.m_color.green()
            subTreeNode['m_color_blue'] = node.m_color.blue()
            subTreeNode['m_textColor_red'] = node.m_textColor.red()
            subTreeNode['m_textColor_green'] = node.m_textColor.green()
            subTreeNode['m_textColor_blue'] = node.m_textColor.blue()
            subTreeNode['m_note'] = node.m_note
            subTreeNode['m_link'] = node.m_link
            subTreeNode['m_annotation'] = getattr(node, 'm_annotation', '')
            subTreeNode['m_colorCustomized'] = getattr(node, 'm_colorCustomized', False)
            
            son = []
            for sonNode in node.sonNode:
                son.append((sonNode.x, sonNode.y))
            subTreeNode['son'] = son

            subTree.append(subTreeNode)
            pos_to_node[(node.x, node.y)] = node
        
        # 保存连接线信息（只保存子树内部的连接线）
        branches = []
        for branch in self.BranchList:
            # 检查连接线的源节点和目标节点是否都在子树中
            if branch.srcNode in nodeList and branch.dstNode in nodeList:
                branches.append({
                    'src_pos': (branch.srcNode.x, branch.srcNode.y),
                    'dst_pos': (branch.dstNode.x, branch.dstNode.y)
                })
        
        # 将连接线信息添加到数据中
        copy_data = {
            'nodes': subTree,
            'branches': branches
        }
        
        clipboard = QApplication.clipboard()
        clipboard.setText(str(copy_data))

        self.messageShow.emit(self.tr('Info: Copy Successfully !'))

    # 生成 subtree
    def genSubTree(self, nodeInfo, nodeList):
        if not nodeInfo['son']:
            return

        sorted(nodeInfo['son'], key=lambda a:a[1], reverse=True)
        self.m_activateNode.setHtml(nodeInfo['htmlContent'])
        sonInfo = []
        for pos in nodeInfo['son']:
            for nodeInfo in nodeList:
                if pos == nodeInfo['pos']:
                    sonInfo.append(nodeInfo)

        for info in sonInfo:
            self.addSonNode()
            self.m_activateNode.setHtml(info['htmlContent'])
            self.genSubTree(info, nodeList)
            self.setActivateNode(self.m_activateNode.parentNode)

    # ========================================================================
    # 粘贴子树
    # ========================================================================
    def paste(self):
        # Paste copied nodes as independent nodes (no connections to existing nodes)
        clipboard = QApplication.clipboard()

        if not clipboard.text():
            print('Error: clipboard has not text content !')
            self.messageShow.emit(self.tr('Error: clipboard has not text content !'))
            return

        try:
            copy_data = eval(clipboard.text())
            # 兼容旧格式（直接是节点列表）
            if isinstance(copy_data, list):
                nodeList = copy_data
                branches = []
            elif isinstance(copy_data, dict):
                nodeList = copy_data.get('nodes', [])
                branches = copy_data.get('branches', [])
            else:
                raise ValueError('Invalid clipboard format')
        except Exception:
            print('Error: invalid clipboard content for paste !')
            self.messageShow.emit(self.tr('Error: invalid clipboard content for paste !'))
            return

        if not nodeList:
            self.messageShow.emit(self.tr('Error: clipboard has no nodes !'))
            return

        # Determine a base position to paste around: prefer active node, else center
        try:
            if self.m_activateNode:
                base_x = self.m_activateNode.pos().x()
                base_y = self.m_activateNode.pos().y()
            else:
                base_x = self.center_x
                base_y = self.center_y
        except Exception:
            base_x = self.center_x
            base_y = self.center_y

        # Use the first node's original pos as anchor to preserve relative layout
        try:
            anchor_x, anchor_y = nodeList[0]['pos']
        except Exception:
            anchor_x, anchor_y = 0, 0

        created = []
        pos_to_node = {}  # 原位置到新节点的映射，用于恢复连接线
        offset_step = 20
        for i, info in enumerate(nodeList):
            node = self.nodeFactory()
            
            # 先恢复节点层级（必须在设置HTML之前，因为setNodeLevel会调用setPlainText）
            if 'm_level' in info:
                level = info['m_level']
                node.m_level = level
                # 只设置层级相关的样式（边距等），不设置文本和颜色
                # 因为我们要恢复原来的HTML内容和颜色
                if level == MainThemeLevel:
                    node.setMargin((5, 18))
                elif level == SecondThemeLevel:
                    node.setMargin((3, 18))
                elif level == ThirdThemeLevel:
                    node.setMargin((2, 18))
                else:  # FreeThemeLevel
                    pass  # 自由主题不需要特殊边距
            else:
                # 如果没有层级信息（旧格式），设置为自由主题层级
                from Config import FreeThemeLevel
                node.m_level = FreeThemeLevel
            
            # 恢复HTML内容（必须在设置层级之后）
            node.setHtml(info.get('htmlContent', ''))
            
            # 恢复节点颜色（必须在设置HTML之后）
            if 'm_color_red' in info:
                node.m_color = QColor(int(info['m_color_red']), 
                                     int(info['m_color_green']), 
                                     int(info['m_color_blue']))
                if info.get('m_colorCustomized', False):
                    node.m_colorCustomized = True
                # 更新显示
                node.update()
            
            # 恢复文本颜色
            if 'm_textColor_red' in info:
                node.m_textColor = QColor(int(info['m_textColor_red']), 
                                         int(info['m_textColor_green']), 
                                         int(info['m_textColor_blue']))
                # 设置文本颜色
                node.setDefaultTextColor(node.m_textColor)
            
            # 恢复其他属性
            if 'm_note' in info:
                node.m_note = info['m_note']
            if 'm_link' in info:
                node.m_link = info['m_link']
            if 'm_annotation' in info:
                node.m_annotation = info['m_annotation']
            
            # preserve relative offset from anchor, and move near base
            try:
                x, y = info.get('pos', (0, 0))
                nx = base_x + (x - anchor_x) + offset_step
                ny = base_y + (y - anchor_y) + offset_step * i
                node.setPos(nx, ny)
                # 保存新位置到节点的映射
                pos_to_node[(x, y)] = node
            except Exception:
                node.setPos(base_x + offset_step, base_y + offset_step * i)

            # add node to scene but DO NOT set parent/son relationships or add branches
            self.addItem(node)
            self.NodeList.append(node)
            created.append(node)

        # 恢复连接线
        for branch_info in branches:
            try:
                src_pos = branch_info['src_pos']
                dst_pos = branch_info['dst_pos']
                # 找到对应的新节点
                src_node = pos_to_node.get(src_pos)
                dst_node = pos_to_node.get(dst_pos)
                if src_node and dst_node:
                    # 检查是否已存在连接线
                    if not self.hasBranch(src_node, dst_node):
                        self.addBranch(src_node, dst_node)
            except Exception as e:
                print(f'Error restoring branch: {e}')
                pass

        # 调整所有连接线
        self.adjustBranch()

        # notify changes
        self.contentChanged.emit()
        self.nodeNumChange.emit(len(self.NodeList))
        self.messageShow.emit(self.tr('Info: Paste Successfully !'))

    # ========================================================================
    # 修改节点背景颜色
    # ========================================================================
    def nodeColor(self):
        """
        修改激活节点的背景颜色
        
        功能:
        - 检查是否有激活节点
        - 打开颜色选择对话框
        - 获取用户选择的颜色
        - 创建修改颜色命令并推入撤销栈
        - 发出提示信息
        
        说明:
        - 如果用户取消对话框，不执行任何操作
        - 操作可以通过撤销/重做功能恢复或重复
        - 修改后的颜色会覆盖主题默认颜色，并标记为自定义颜色
        """
        # 检查是否有激活节点
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        # 创建颜色选择对话框
        dialog = QColorDialog()
        # 设置对话框标题（已本地化）
        dialog.setWindowTitle(self.tr('Set Node Color'))
        # 设置对话框的当前颜色为节点的当前颜色
        dialog.setCurrentColor(self.m_activateNode.m_color)
        # 显示对话框，如果用户取消则返回
        if not dialog.exec():
            return

        # 创建命令上下文对象
        m_context = Context()
        m_context.m_activateNode = self.m_activateNode      # 设置激活节点
        m_context.m_color = dialog.selectedColor()           # 设置用户选择的颜色
        m_context.m_scene = self                             # 设置场景

        # 创建修改节点颜色命令
        nodeColorCommand = NodeColorCommand(m_context)
        # 将命令推入撤销栈（可以撤销/重做）
        self.m_undoStack.push(nodeColorCommand)

        # 显示提示信息
        self.messageShow.emit(self.tr('change node color'))

    # ========================================================================
    # 修改节点中文本颜色
    # ========================================================================
    def textColor(self):
        """
        修改激活节点的文本颜色
        
        功能:
        - 检查是否有激活节点
        - 打开颜色选择对话框
        - 获取用户选择的颜色
        - 创建修改文本颜色命令并推入撤销栈
        - 发出提示信息
        
        说明:
        - 如果用户取消对话框，不执行任何操作
        - 操作可以通过撤销/重做功能恢复或重复
        - 修改后的文本颜色会立即应用到节点文本
        """
        # 检查是否有激活节点
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return

        # 创建颜色选择对话框
        dialog = QColorDialog()
        # 设置对话框标题（已本地化）
        dialog.setWindowTitle(self.tr('Set Text Color'))
        # 设置对话框的当前颜色为节点的当前文本颜色
        dialog.setCurrentColor(self.m_activateNode.m_textColor)
        # 显示对话框，如果用户取消则返回
        if not dialog.exec():
            return

        # 创建命令上下文对象
        m_context = Context()
        m_context.m_activateNode = self.m_activateNode      # 设置激活节点
        m_context.m_textColor = dialog.selectedColor()      # 设置用户选择的文本颜色
        m_context.m_scene = self                            # 设置场景

        # 创建修改文本颜色命令
        textColorCommand = TextColorCommand(m_context)
        # 将命令推入撤销栈（可以撤销/重做）
        self.m_undoStack.push(textColorCommand)

        # 显示提示信息
        self.messageShow.emit(self.tr('Info: change text color !'))

    # rewrite rightclick menu
    # 重写scene右键菜单事件, 区分有无 item 的右键菜单事件
    def tr(self, text):
        """
        翻译方法，使用设置的翻译函数
        
        参数:
        - text: 要翻译的文本
        
        返回:
        - str: 翻译后的文本
        """
        if self.tr_func:
            return self.tr_func(text)
        return text
    
    def contextMenuEvent(self, e):
        selectedItem = self.itemAt(e.scenePos(), QTransform())
        print(selectedItem)

        # 检查是否是 TodoList 图片项
        from Component import TodoListPixmapItem
        if isinstance(selectedItem, TodoListPixmapItem):
            rightclick_menu = QMenu()
            
            # Delete
            delete_action = QAction(self.tr('Delete'), self)
            delete_action.setShortcut('Delete')
            delete_action.triggered.connect(lambda: self.deleteTodoListImage(selectedItem))
            rightclick_menu.addAction(delete_action)
            
            rightclick_menu.exec(QCursor().pos())
            return

        if selectedItem and not self.m_editingMode:
            rightclick_menu = QMenu()

            # Cut
            cut_action = QAction(self.tr('Cut'), self)
            cut_action.setShortcut('Ctrl+X')
            cut_action.triggered.connect(self.cut)
            rightclick_menu.addAction(cut_action)

            # Copy
            copy_action = QAction(self.tr('Copy'), self)
            copy_action.setShortcut('Ctrl+C')
            copy_action.triggered.connect(self.copy)
            rightclick_menu.addAction(copy_action)

            # Paste
            paste_action = QAction(self.tr('Paste'), self)
            paste_action.setShortcut('Ctrl+V')
            paste_action.triggered.connect(self.paste)
            rightclick_menu.addAction(paste_action)

            # Delete
            delete_action = QAction(self.tr('Delete'), self)
            delete_action.setShortcut('Delete')
            delete_action.triggered.connect(self.removeNode)
            rightclick_menu.addAction(delete_action)

            rightclick_menu.addSeparator()

            # Set Color
            set_color_action = QAction(self.tr('Set Color'), self)
            set_color_action.triggered.connect(self.nodeColor)
            rightclick_menu.addAction(set_color_action)

            # Set Text Color
            set_textColor_action = QAction(self.tr('Set Text Color'), self)
            set_textColor_action.triggered.connect(self.textColor)
            rightclick_menu.addAction(set_textColor_action)

            # Insert Link
            insert_link_action = QAction(self.tr('Link'), self)
            def _insert_link():
                # ask user for a URL and insert into the selected node
                url, ok = QInputDialog.getText(None, self.tr('Insert Link'), self.tr('Enter URL:'), text='https://')
                if ok and url:
                    # ensure the selected item is active node
                    self.setActivateNode(selectedItem)
                    try:
                        selectedItem.insertLink(url)
                    except Exception:
                        # fallback: call via scene helper
                        self.m_activateNode.insertLink(url)
                    self.contentChanged.emit()
                    self.adjustSubTreeNode()
                    self.adjustBranch()
            insert_link_action.triggered.connect(_insert_link)
            rightclick_menu.addAction(insert_link_action)

            # Insert Image
            insert_image_action = QAction(self.tr('Image'), self)
            def _insert_image():
                # open file dialog to pick a local image
                fname, _ = QFileDialog.getOpenFileName(None, self.tr('Select Image'), QDir.homePath(), 'Images (*.png *.jpg *.jpeg *.bmp *.svg)')
                if fname:
                    # set active node and insert picture via Node method
                    self.setActivateNode(selectedItem)
                    try:
                        # use file URL form so HTML img src resolves
                        from PyQt5.QtCore import QUrl
                        url = QUrl.fromLocalFile(fname).toString()
                        selectedItem.insertPicture(url)
                    except Exception:
                        try:
                            selectedItem.insertPicture(fname)
                        except Exception:
                            # fallback to scene helper
                            self.insertPicture(fname)
                    self.contentChanged.emit()
                    self.adjustSubTreeNode()
                    self.adjustBranch()
            insert_image_action.triggered.connect(_insert_image)
            rightclick_menu.addAction(insert_image_action)

            rightclick_menu.addSeparator()

            # Add Annotation
            add_annotation_action = QAction(self.tr('Annotation'), self)
            def _add_annotation():
                # set active node
                self.setActivateNode(selectedItem)
                # get node position and size for annotation window
                # 使用与getPos()相同的参考点：节点底部中心点，以保持与按钮调出窗口一致的位置
                node_rect = selectedItem.boundingRect()
                # 计算节点底部中心点（与getPos()方法一致）
                p = QPointF(node_rect.center().x(), node_rect.bottomRight().y())
                scene_p = selectedItem.mapToScene(p)
                # convert scene position to global position
                view = self.views()[0] if self.views() else None
                if view:
                    view_pos = view.mapFromScene(scene_p)
                    global_pos = view.viewport().mapToGlobal(view_pos)
                    # get annotation text from node
                    annotation_text = getattr(selectedItem, 'm_annotation', '')
                    # emit signal with position and annotation text (往左偏移250像素，往上偏移230像素)
                    # 使用NODE_INFO_SIZE以保持与按钮调出窗口一致的位置计算方式
                    from Config import NODE_INFO_SIZE
                    x = int(global_pos.x()) - NODE_INFO_SIZE[0]//2 - 250
                    y = int(global_pos.y()) - 230
                    self.addAnnotation.emit(x, y, annotation_text)
            add_annotation_action.triggered.connect(_add_annotation)
            rightclick_menu.addAction(add_annotation_action)
            
            # View Annotation (only show if node has annotation)
            if hasattr(selectedItem, 'm_annotation') and selectedItem.m_annotation and selectedItem.m_annotation.strip():
                view_annotation_action = QAction(self.tr('View Annotation'), self)
                def _view_annotation():
                    self.setActivateNode(selectedItem)
                    self.showAnnotation.emit()
                view_annotation_action.triggered.connect(_view_annotation)
                rightclick_menu.addAction(view_annotation_action)

            rightclick_menu.exec(QCursor().pos())
        else:
            super().contextMenuEvent(e)

    # TODO: add relation between freeTheme and theme
    def buildRelation(self):
        """Build a relation (branch) between selected nodes.

        Expected usage:
        - Select two nodes (Ctrl+click or rubber-band select) and trigger
          the Relation action. A Branch will be created between the first
          and second selected Node.

        This was left TODO in the original project; implement a simple
        behavior here so users can create arbitrary relations between
        nodes (not limited to parent/child branches).
        """
        selected = [it for it in self.selectedItems() if isinstance(it, Node)]
        if len(selected) < 2:
            self.messageShow.emit(self.tr('Info: select two nodes to create relation !'))
            return

        src = selected[0]
        dst = selected[1]

        # avoid creating duplicate identical branches
        for b in self.BranchList:
            if (b.srcNode == src and b.dstNode == dst) or (b.srcNode == dst and b.dstNode == src):
                self.messageShow.emit(self.tr('Info: relation already exists !'))
                return

        # create branch and refresh
        self.addBranch(src, dst)
        self.adjustBranch()
        self.contentChanged.emit()
        self.messageShow.emit(self.tr('Info: relation created !'))

    def lineManage(self):
        """管理选中节点之间的连接线
        
        功能：
        - 选中两个或多个节点，对每一对节点独立处理：
            - 如果两个节点之间有连线：删除连线
            - 如果两个节点之间没有连线：添加连线
        """
        selected = [it for it in self.selectedItems() if isinstance(it, Node)]
        
        if len(selected) < 2:
            self.messageShow.emit('Info: 请至少选中两个节点！')
            return

        added_count = 0
        removed_count = 0

        # 对每一对节点独立判断：有连线则删除，无连线则添加
        for i in range(len(selected)):
            for j in range(i + 1, len(selected)):
                node1 = selected[i]
                node2 = selected[j]
                
                existing_branch = self.hasBranch(node1, node2)
                
                if existing_branch:
                    # 有连线：删除
                    self.removeBranchBetween(node1, node2)
                    removed_count += 1
                else:
                    # 无连线：添加
                    self.addBranch(node1, node2)
                    added_count += 1

        # 调整所有连接线并刷新
        self.adjustBranch()
        self.contentChanged.emit()
        
        # 显示操作结果
        if added_count > 0 and removed_count > 0:
            self.messageShow.emit(self.tr('Info: 已创建 {} 条连接线，已删除 {} 条连接线！').format(added_count, removed_count))
        elif added_count > 0:
            self.messageShow.emit(self.tr('Info: 已创建 {} 条连接线！').format(added_count))
        elif removed_count > 0:
            self.messageShow.emit(self.tr('Info: 已删除 {} 条连接线！').format(removed_count))

    def node_(self, node, father): 
        ET.SubElement(father,
            'node', {
                'x':str(node.x),
                'y':str(node.y),
                'son_num': str(len(node.sonNode)),
                'width':str(node.width),
                'm_color_red':str(node.m_color.red()),
                'm_color_green':str(node.m_color.green()),
                'm_color_blue':str(node.m_color.blue()),
                'm_level':str(node.m_level),
                'm_textColor_red':str(node.m_textColor.red()),
                'm_textColor_green':str(node.m_textColor.green()),
                'm_textColor_blue':str(node.m_textColor.blue()),
                'm_note': node.m_note,
                'm_link': node.m_link,
                'm_annotation': getattr(node, 'm_annotation', ''),
                'htmlContent':node.toHtml()
            })

    # 将 scene 中的信息写入文件中
    def writeContentToXmlFile(self, filename):
        # 检查文件名是否有效
        if not filename:
            raise ValueError('Filename is empty or None')
        
        # 检查是否有节点
        if not self.NodeList or len(self.NodeList) == 0:
            raise ValueError('No nodes to save')
        
        #最外层节点标签为'data',没有任何属性
        root = ET.Element('data')
        tree = self.getSubTree(self.NodeList[0])
        
        # 创建节点索引映射，用于保存连接线时引用节点
        node_to_index = {}
        for idx, node in enumerate(tree):
            node_to_index[node] = idx
        
        #树中的所有节点在xml中均以'data'为根节点，为并列结构
        for v in tree:
            self.node_(v,root)
        
        # 保存所有连接线信息（包括非父子关系的连接线）
        branches_element = ET.SubElement(root, 'branches')
        for branch in self.BranchList:
            # 检查连接线的源节点和目标节点是否都在树中
            if branch.srcNode in node_to_index and branch.dstNode in node_to_index:
                branch_elem = ET.SubElement(branches_element, 'branch')
                branch_elem.set('src_index', str(node_to_index[branch.srcNode]))
                branch_elem.set('dst_index', str(node_to_index[branch.dstNode]))
        
        whole_tree = ET.ElementTree(root)
        # 确保目录存在
        import os
        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        whole_tree.write(filename, encoding='utf-8')

    # 将 scene 中信息写入 PNG 图片
    def writeContentToPngFile(self, filename):
        img = QImage(self.sceneRect().width(), self.sceneRect().height(), QImage.Format_ARGB32_Premultiplied)

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(Qt.white))
        self.render(p)
        p.setBackground(QColor(Qt.white))
        p.end()

        img.save(filename)

    # 将 scene 中信息写入 PDF 文件
    def writeContentToPdfFile(self, filename):
        # 生成 Printer 对象
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)

        # 将 scene 中信息 render 到 painter上
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(Qt.white))
        self.render(painter)
        painter.setBackground(QColor(Qt.white))
        painter.end()

    # 从 XML 文件中读取 scene 信息
    def readContentFromXmlFile(self, filename):
        tree = ET.ElementTree()
        try:
            tree.parse(filename)
        except:
            print('Error: tree parse error !')
            return False
        root = tree.getroot()
        print('root: ', root)
        node_list = []
        attr_list = []
        for node_attr in root:
            # 跳过非节点元素（如branches）
            if node_attr.tag != 'node':
                continue
            
            node = self.nodeFactory()
            
            attr = node_attr.attrib
            print(attr)
            #将xml中的数据存入节点中
            node.x = float(attr['x'])
            node.y = float(attr['y'])
            node.width = float(attr['width'])
            node.m_color = QColor(float(attr['m_color_red']),
                                    float(attr['m_color_green']), 
                                    float(attr['m_color_blue']))
            # 从文件加载的颜色应该被认为是自定义的（用户之前保存过）
            node.m_colorCustomized = True
            node.m_level = int(attr['m_level'])
            node.m_textColor = QColor(float(attr['m_textColor_red']), 
                                        float(attr['m_textColor_green']),
                                        float(attr['m_textColor_blue']))
            node.m_note = attr['m_note']
            node.m_link = attr['m_link']
            if node.m_link != 'https://':
                node.hasLink = True
            # 恢复批注内容
            node.m_annotation = attr.get('m_annotation', '')
            node.setHtml(attr['htmlContent'])
            
            # 批注功能不再使用图标，直接点击节点查看

            node.setPos(node.x, node.y)
            self.addItem(node)
            self.NodeList.append(node)

            attr_list.append(attr)
            node_list.append(node)
            
        #由于写xml文件中节点是根据深度优先遍历的结果进行排序的
        #xml中的第一个节点一定是根节点
        # 先建立父子关系（但不创建连接线）
        node_scan_head = 1
        for m in range(len(node_list)):
            node_scan_tail = node_scan_head + int(attr_list[m]['son_num'])
            for n in range(node_scan_head,node_scan_tail):
                node_list[m].sonNode.append(node_list[n])
                node_list[n].parentNode = node_list[m]
            node_scan_head = node_scan_tail
        
        # 检查是否有branches元素（新格式）
        branches_element = root.find('branches')
        if branches_element is not None:
            # 新格式：只从branches元素中加载连接线，不根据父子关系自动创建
            # 这样可以正确恢复被删除的连接线状态
            for branch_elem in branches_element.findall('branch'):
                try:
                    src_index = int(branch_elem.get('src_index'))
                    dst_index = int(branch_elem.get('dst_index'))
                    
                    # 检查索引是否有效
                    if 0 <= src_index < len(node_list) and 0 <= dst_index < len(node_list):
                        src_node = node_list[src_index]
                        dst_node = node_list[dst_index]
                        
                        # 检查连接线是否已存在（避免重复创建）
                        if not self.hasBranch(src_node, dst_node):
                            self.addBranch(src_node, dst_node)
                except (ValueError, TypeError) as e:
                    print(f'Error loading branch: {e}')
                    continue
        else:
            # 旧格式（向后兼容）：根据父子关系自动创建连接线
            for m in range(len(node_list)):
                for son_node in node_list[m].sonNode:
                    if not self.hasBranch(node_list[m], son_node):
                        self.addBranch(node_list[m], son_node)
        
        # 调整所有连接线
        self.adjustBranch()
        
        return True
    
    def readContentFromMarkdown(self, filename):
        """
        从Markdown文件读取内容并生成思维导图
        
        参数:
        - filename: Markdown文件路径
        
        返回:
        - True: 成功导入
        - False: 导入失败
        
        功能:
        - 解析Markdown文件，提取一级、二级、三级标题
        - 根据标题层级创建对应的节点
        - 建立节点之间的父子关系
        """
        try:
            # 读取Markdown文件
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f'Error reading markdown file: {e}')
            return False

        return self.readContentFromMarkdownText(content)

    def readContentFromMarkdownText(self, content):
        """Build a mind map directly from Markdown heading text."""
        if not isinstance(content, str) or not content.strip():
            return False
        
        # 清空现有节点和连接线
        self.removeAllBranches()
        self.removeAllNodes()
        
        # 解析Markdown标题
        import re
        lines = content.split('\n')
        
        # 存储节点层级关系
        # 使用列表存储每个层级的最后一个节点
        last_nodes = [None, None, None, None]  # 索引0不使用，1-3对应一级、二级、三级标题
        
        # 节点位置计算
        base_x = self.center_x
        base_y = self.center_y
        x_offset = self.brachDistance + 200  # 水平间距，使用场景的brachDistance
        
        node_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 匹配标题：一级标题 #，二级标题 ##，三级标题 ###
            match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if match:
                level_markers = match.group(1)
                title_text = match.group(2).strip()
                level = len(level_markers)  # 1, 2, 或 3
                
                if level > 3:
                    continue  # 只处理一级到三级标题
                
                # 创建节点
                node = self.nodeFactory()
                
                # 根据层级设置节点类型
                if level == 1:
                    node.setNodeLevel(MainThemeLevel)
                    # 一级标题作为中心主题，放在中心位置
                    node.setPos(base_x, base_y)
                    node.x = base_x
                    node.y = base_y
                    last_nodes[1] = node
                    last_nodes[2] = None  # 重置下级节点
                    last_nodes[3] = None
                    # 添加到场景和列表
                    self.addItem(node)
                    self.NodeList.append(node)
                elif level == 2:
                    node.setNodeLevel(SecondThemeLevel)
                    # 二级标题作为分支主题
                    parent = last_nodes[1]
                    if parent:
                        # 使用getSonPos方法计算位置，确保不重叠
                        if len(parent.sonNode) == 0:
                            # 第一个子节点，使用getSonPos计算初始位置
                            pos_x, pos_y = self.getSonPosForNode(parent)
                        else:
                            # 后续子节点，计算在最后一个子节点下方
                            last_son = parent.sonNode[-1]
                            last_son_rect = last_son.sceneBoundingRect()
                            # 计算新节点的Y坐标：最后一个子节点的底部 + 间距
                            pos_y = last_son_rect.bottom() + 50  # 50像素间距
                            pos_x = parent.sceneBoundingRect().right() + self.brachDistance
                        
                        node.setPos(pos_x, pos_y)
                        node.x = pos_x
                        node.y = pos_y
                        
                        # 建立父子关系
                        parent.sonNode.append(node)
                        node.parentNode = parent
                        
                        # 添加到场景和列表
                        self.addItem(node)
                        self.NodeList.append(node)
                        
                        # 调整节点位置以避免重叠
                        if len(parent.sonNode) > 1:
                            self.adjustNode(parent, node)
                        
                        # 创建连接线
                        self.addBranch(parent, node)
                    else:
                        # 如果没有一级标题，作为中心主题处理
                        node.setNodeLevel(MainThemeLevel)
                        node.setPos(base_x, base_y)
                        node.x = base_x
                        node.y = base_y
                        last_nodes[1] = node
                        # 添加到场景和列表
                        self.addItem(node)
                        self.NodeList.append(node)
                    last_nodes[2] = node
                    last_nodes[3] = None  # 重置下级节点
                elif level == 3:
                    node.setNodeLevel(ThirdThemeLevel)
                    # 三级标题作为子主题
                    parent = last_nodes[2] if last_nodes[2] else last_nodes[1]
                    if parent:
                        # 使用类似的方法计算位置
                        if len(parent.sonNode) == 0:
                            # 第一个子节点
                            pos_x, pos_y = self.getSonPosForNode(parent)
                        else:
                            # 后续子节点
                            last_son = parent.sonNode[-1]
                            last_son_rect = last_son.sceneBoundingRect()
                            pos_y = last_son_rect.bottom() + 50  # 50像素间距
                            pos_x = parent.sceneBoundingRect().right() + self.brachDistance
                        
                        node.setPos(pos_x, pos_y)
                        node.x = pos_x
                        node.y = pos_y
                        
                        # 建立父子关系
                        parent.sonNode.append(node)
                        node.parentNode = parent
                        
                        # 添加到场景和列表
                        self.addItem(node)
                        self.NodeList.append(node)
                        
                        # 调整节点位置以避免重叠
                        if len(parent.sonNode) > 1:
                            self.adjustNode(parent, node)
                        
                        # 创建连接线
                        self.addBranch(parent, node)
                    else:
                        # 如果没有上级标题，作为二级主题处理
                        node.setNodeLevel(SecondThemeLevel)
                        node.setPos(base_x + x_offset, base_y)
                        node.x = base_x + x_offset
                        node.y = base_y
                        # 添加到场景和列表
                        self.addItem(node)
                        self.NodeList.append(node)
                    last_nodes[3] = node
                
                # 设置节点文本（在添加到场景后设置，以便正确计算大小）
                node.setPlainText(title_text)
                
                # 如果节点已经添加到场景，更新位置
                if node in self.NodeList:
                    # 重新调整连接线
                    if node.parentNode:
                        self.adjustBranch()
                
                node_count += 1
        
        # 如果没有找到任何标题，返回False
        if node_count == 0:
            return False
        
        # 调整节点布局
        if self.NodeList:
            self.layoutTree(self.NodeList[0])
        self.adjustBranch()
        
        # 更新节点数量
        self.nodeNumChange.emit(len(self.NodeList))
        if self.NodeList:
            self.setActivateNode(self.NodeList[0])
        self.contentChanged.emit()
        
        return True

    # 删除 scene 中所有 node
    def removeAllNodes(self):
        for node in self.NodeList:
            self.removeItem(node)
        
        self.NodeList.clear()

    # 删除 scene 中所有 branch
    def removeAllBranches(self):
        for branch in self.BranchList:
            self.removeItem(branch)

        self.BranchList.clear()
    
    def deleteTodoListImage(self, pixmap_item):
        """删除 TodoList 图片"""
        # 从场景中移除
        self.removeItem(pixmap_item)
        
        # 从所有节点中查找并清除引用
        for node in self.NodeList:
            if hasattr(node, 'todolist_pixmap_item') and node.todolist_pixmap_item == pixmap_item:
                node.todolist_pixmap_item = None
                break
        
        # 触发内容改变
        self.contentChanged.emit()
        self.messageShow.emit(self.tr('Info: TodoList image deleted !'))

    # 插入图片并且调整节点位置
    def insertPicture(self, image):
        if not self.m_activateNode:
            print('Warning: no activate node !')
            self.messageShow.emit(self.tr('Warning: no activate node !'))
            return
        self.m_activateNode.insertPicture(image)
        self.contentChanged.emit()
        self.adjustSubTreeNode()
        self.adjustBranch()

    def setHandwritingMode(self, enabled, settings=None):
        """设置手写模式"""
        self.handwritingMode = enabled
        if settings:
            self.handwritingSettings = settings
        # 更新光标
        if enabled:
            if settings and settings.get('mode') == 'eraser':
                # 橡皮擦光标
                cursor = QCursor(QPixmap(16, 16))
            else:
                # 笔光标 - 使用自定义光标或默认
                cursor = QCursor(Qt.CrossCursor)
        else:
            cursor = QCursor(Qt.ArrowCursor)
        
        # 通知视图更新光标（需要通过信号或直接访问）
        if hasattr(self, 'views') and self.views():
            for view in self.views():
                view.setCursor(cursor)
    
    def mousePressEvent(self, e):
        self.press_close.emit()
        
        # 手写模式下的绘制逻辑
        if self.handwritingMode and e.button() == Qt.LeftButton:
            if self.handwritingSettings.get('mode') == 'pen':
                # 笔模式：开始绘制新路径
                self.currentPath = QPainterPath()
                self.currentPath.moveTo(e.scenePos())
                
                # 创建新的批注项
                pen = QPen(
                    self.handwritingSettings['color'],
                    self.handwritingSettings['width'],
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin
                )
                self.currentAnnotation = AnnotationItem(self.currentPath, pen)
                self.addItem(self.currentAnnotation)
                self.AnnotationList.append(self.currentAnnotation)
                
                e.accept()
                return
            # 橡皮擦模式：由视图处理框选删除，这里不做处理
            elif self.handwritingSettings.get('mode') == 'eraser':
                # 橡皮擦模式由视图的框选功能处理，这里只传递事件
                e.accept()
                return
        
        super().mousePressEvent(e)
    
    def mouseMoveEvent(self, e):
        # 手写模式下的绘制逻辑
        if self.handwritingMode and self.currentAnnotation and self.currentPath:
            # 继续绘制路径
            self.currentPath.lineTo(e.scenePos())
            self.currentAnnotation.setPath(self.currentPath)
            e.accept()
            return
        
        super().mouseMoveEvent(e)
    
    def mouseReleaseEvent(self, e):
        # 手写模式下的绘制逻辑
        if self.handwritingMode and e.button() == Qt.LeftButton:
            if self.currentAnnotation:
                self.contentChanged.emit()
                self.currentAnnotation = None
                self.currentPath = None
            e.accept()
            return
        
        super().mouseReleaseEvent(e)
