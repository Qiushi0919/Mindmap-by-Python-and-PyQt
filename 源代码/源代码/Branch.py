"""
================================================================================
模块: Branch.py
功能: 定义思维导图中节点之间的连接线（分支）
描述: 
    - Branch类继承自QGraphicsPathItem，表示两个节点之间的曲线
    - 提供调整连线位置的方法，使连线始终连接源节点和目标节点的合适位置
================================================================================
"""

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *      # 导入Qt图形界面相关的类
from PyQt5.QtCore import *     # 导入Qt核心功能相关的类（包含QPointF, QLineF等）
from PyQt5.QtWidgets import *  # 导入Qt窗口部件相关的类

# ============================================================================
# 导入标准库模块
# ============================================================================
import sys  # 系统相关功能


# ============================================================================
# Branch类：节点连接线
# ============================================================================
class Branch(QGraphicsPathItem):
    """
    重写QGraphicsPathItem类，用于表示思维导图中节点之间的连接线
    
    功能:
    - 连接源节点和目标节点
    - 自动调整连线位置，使其始终连接节点的合适位置
    - 支持自定义线条宽度和颜色
    
    属性:
    - srcNode: 源节点（连接的起始节点）
    - dstNode: 目标节点（连接的结束节点）
    - width: 线条宽度
    - color: 线条颜色
    - offsetScale: 偏移比例，用于计算连线起始点相对于节点中心的位置
    """
    
    def __init__(self, *args, **kwargs):
        """
        初始化分支连接线对象
        
        参数:
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(Branch, self).__init__(*args, **kwargs)

        # ====================================================================
        # 初始化连接线的属性
        # ====================================================================
        self.srcNode = None      # 源节点（连接的起始节点），初始化为None
        self.dstNode = None      # 目标节点（连接的结束节点），初始化为None
        self.width = 2.4         # 线条宽度（像素）
        self.color = QColor(96, 165, 250)
        self.m_theme = 'Light'   # 主题：'Light'（浅色）、'Dark'（深色）、'Black & White'（黑白）
        # 偏移比例：用于计算连线起始点位置
        # 0.4表示起始点位于源节点中心向右偏移节点宽度40%的位置
        self.offsetScale = 0.4
        # 设置Z值（深度值），-1表示连线在节点下方，这样节点会显示在连线之上
        self.setZValue(-1)
        
        # 根据主题设置默认颜色和宽度
        self.updateThemeStyle()

    def adjust(self):
        """
        调整连接线的位置，使连线始终连接源节点和目标节点的合适位置
        
        连线起始点（p1）:
        - x坐标：源节点中心x坐标 + 节点宽度 * 偏移比例（向右偏移）
        - y坐标：源节点中心y坐标
        
        连线结束点（p2）:
        - x坐标：目标节点左边界x坐标
        - y坐标：目标节点中心y坐标
        """
        source = self.srcNode.sceneBoundingRect()
        target = self.dstNode.sceneBoundingRect()
        flows_right = target.center().x() >= source.center().x()
        if flows_right:
            p1 = QPointF(source.right(), source.center().y())
            p2 = QPointF(target.left(), target.center().y())
            direction = 1
        else:
            p1 = QPointF(source.left(), source.center().y())
            p2 = QPointF(target.right(), target.center().y())
            direction = -1

        control = max(45.0, abs(p2.x() - p1.x()) * 0.48)
        path = QPainterPath(p1)
        path.cubicTo(
            QPointF(p1.x() + direction * control, p1.y()),
            QPointF(p2.x() - direction * control, p2.y()),
            p2,
        )
        self.setPath(path)
    
    def setTheme(self, theme):
        """设置连接线主题"""
        self.m_theme = theme
        self.updateThemeStyle()
        self.update()  # 触发重绘
    
    def updateThemeStyle(self):
        """根据主题更新连接线的样式"""
        if self.m_theme == 'Light':
            self.color = QColor(96, 165, 250)
            self.width = 2.4
        elif self.m_theme == 'Dark':
            # 深色主题 - 浅蓝色系
            self.color = QColor(100, 150, 200)  # 亮蓝色
            self.width = 2
        else:  # Black & White
            # 黑白主题 - 深灰色
            self.color = QColor(120, 120, 120)  # 中灰色
            self.width = 2
        
        # 更新画笔样式
        pen = QPen(QBrush(self.color), self.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)
    
    def paint(self, painter, option, widget=None):
        """自定义绘制连接线，根据主题应用不同样式"""
        # 根据主题设置画笔样式
        if self.m_theme == 'Light':
            pen = QPen(QBrush(self.color), self.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            shadow_pen = QPen(QBrush(QColor(59, 130, 246, 45)), self.width + 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(shadow_pen)
            painter.drawPath(self.path())
        elif self.m_theme == 'Dark':
            # 深色主题 - 亮蓝色，带发光效果
            pen = QPen(QBrush(self.color), self.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            # 添加轻微发光效果
            glow_pen = QPen(QBrush(QColor(100, 150, 200, 100)), self.width + 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(glow_pen)
            painter.drawPath(self.path())
        else:  # Black & White
            # 黑白主题 - 简洁的灰色线条
            pen = QPen(QBrush(self.color), self.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        
        # 绘制主线条
        painter.setPen(pen)
        painter.drawPath(self.path())
