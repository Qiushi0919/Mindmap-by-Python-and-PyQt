"""
================================================================================
模块: Command.py
功能: 实现撤销/重做命令模式
描述: 
    - 定义了各种命令类，用于实现撤销（Undo）和重做（Redo）功能
    - 所有命令类继承自QUndoCommand，实现undo()和redo()方法
    - 包括插入节点、删除节点、移动节点、修改颜色等命令
================================================================================
"""

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *      # 导入Qt图形界面相关的类
from PyQt5.QtCore import *     # 导入Qt核心功能相关的类
from PyQt5.QtWidgets import *  # 导入Qt窗口部件相关的类（包含QUndoCommand）

# ============================================================================
# 导入标准库模块
# ============================================================================
import sys  # 系统相关功能

# ============================================================================
# 导入自定义模块
# ============================================================================
from Config import *  # 导入配置常量（如MainThemeLevel, MoveCommandID等）


# ============================================================================
# Context类：命令上下文
# ============================================================================
class Context():
    """
    命令上下文类，用于存储命令执行所需的所有信息
    
    功能:
    - 封装命令执行时需要的场景、节点、位置、颜色等信息
    - 避免在命令类中直接引用全局变量，提高代码的可维护性
    
    属性:
    - m_scene: 图形场景对象（Graph实例）
    - m_activateNode: 当前激活的节点
    - m_nodeList: 节点列表（用于批量操作）
    - m_pos: 位置信息（坐标[x, y]或元组）
    - m_color: 节点背景颜色
    - m_textColor: 文本颜色
    """
    def __init__(self):
        """
        初始化上下文对象，将所有属性设置为None
        """
        self.m_scene = None        # 图形场景对象
        self.m_activateNode = None # 当前激活的节点
        self.m_nodeList = None     # 节点列表（用于批量操作，如移动子树）
        self.m_pos = None          # 位置信息（坐标[x, y]）
        self.m_color = None        # 节点背景颜色
        self.m_textColor = None    # 文本颜色


# ============================================================================
# InsertNodeCommand类：插入节点命令
# ============================================================================
class InsertNodeCommand(QUndoCommand):
    """
    插入节点命令类，用于实现插入节点的撤销/重做功能
    
    功能:
    - 在激活节点下插入一个新的子节点
    - 支持撤销（删除节点）和重做（恢复节点）
    - 根据父节点层级自动设置新节点的层级
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化插入节点命令
        
        参数:
        - context: 命令上下文对象，包含场景、激活节点、位置等信息
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(InsertNodeCommand, self).__init__(*args, **kwargs)

        # 保存上下文对象
        self.context = context

        # ====================================================================
        # 创建新节点并设置基本属性
        # ====================================================================
        # 使用场景的nodeFactory方法创建新节点（会连接信号）
        self.node = self.context.m_scene.nodeFactory()
        # 设置节点的坐标位置（从上下文中获取）
        self.node.x, self.node.y = self.context.m_pos
        # 设置节点编号（当前节点列表长度+1）
        self.node.num = len(self.context.m_scene.NodeList) + 1
        
        # ====================================================================
        # 根据父节点层级设置新节点的层级
        # ====================================================================
        if self.context.m_activateNode.m_level == MainThemeLevel:
            # 如果父节点是中心主题，子节点设为分支主题
            self.node.setNodeLevel(SecondThemeLevel)
        else:
            # 否则设为子主题
            self.node.setNodeLevel(ThirdThemeLevel)
            
    def undo(self):
        """
        撤销操作：删除刚才插入的节点
        
        执行步骤:
        1. 从场景节点列表中移除节点
        2. 从父节点的子节点列表中移除节点
        3. 清除节点的父节点引用
        4. 删除与节点相关的连接线
        5. 从场景中移除节点图形项
        6. 如果有其他子节点，调整父节点的其他子节点位置
        7. 重新激活父节点
        """
        # 从场景的节点列表中移除节点
        self.context.m_scene.NodeList.remove(self.node)
        # 从父节点的子节点列表中移除节点
        self.context.m_activateNode.sonNode.remove(self.node)
        # 清除节点的父节点引用
        self.node.parentNode = None

        # 删除与节点相关的连接线
        self.context.m_scene.removeBranch(self.node)
        # 从场景中移除节点图形项（不再显示）
        self.context.m_scene.removeItem(self.node)

        # 如果父节点还有其他子节点，需要调整它们的位置
        # reverse=True表示反向调整（撤销时的操作）
        if len(self.context.m_activateNode.sonNode) > 0:
            self.context.m_scene.adjustNode(self.context.m_activateNode, self.node, True)
            # 重新调整所有连接线位置
            self.context.m_scene.adjustBranch()

        # 重新激活父节点（因为子节点被删除了）
        self.context.m_scene.setActivateNode(self.context.m_activateNode)

    def redo(self):
        """
        重做操作：恢复插入的节点
        
        执行步骤:
        1. 设置节点的父节点关系
        2. 将节点添加到父节点的子节点列表
        3. 设置节点位置
        4. 如果有多个子节点，调整其他子节点位置
        5. 激活新插入的节点
        6. 将节点添加到场景中
        7. 创建与父节点的连接线
        """
        # 设置节点的父节点引用
        self.node.parentNode = self.context.m_activateNode
        # 将节点添加到父节点的子节点列表
        self.context.m_activateNode.sonNode.append(self.node)
        # 设置节点在场景中的位置
        self.node.setPos(*self.context.m_pos)
        
        # 如果父节点有多个子节点，需要调整其他子节点的位置
        if len(self.context.m_activateNode.sonNode) > 1:
            # 调整节点位置以避免重叠
            self.context.m_scene.adjustNode(self.context.m_activateNode, self.node)
            # 重新调整所有连接线位置
            self.context.m_scene.adjustBranch()

        # 激活新插入的节点（使其成为当前选中节点）
        self.context.m_scene.setActivateNode(self.node)

        # 将节点添加到场景中（使其显示在界面上）
        self.context.m_scene.addItem(self.node)
        # 将节点添加到场景的节点列表
        self.context.m_scene.NodeList.append(self.node)

        # 创建父节点与新节点的连接线
        self.context.m_scene.addBranch(self.node.parentNode, self.node)

# ============================================================================
# RemoveNodeCommand类：删除节点命令
# ============================================================================
class RemoveNodeCommand(QUndoCommand):
    """
    删除节点命令类，用于实现删除节点的撤销/重做功能
    
    功能:
    - 删除激活节点及其所有子节点（子树）
    - 支持撤销（恢复节点）和重做（再次删除）
    - 会删除整个子树，包括所有子节点和连接线
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化删除节点命令
        
        参数:
        - context: 命令上下文对象，context.m_nodeList包含要删除的所有节点
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(RemoveNodeCommand, self).__init__(*args, **kwargs)

        # 保存上下文对象
        self.context = context

    
    def undo(self):  
        """
        撤销操作：恢复被删除的节点及其子树
        
        执行步骤（对每个节点）:
        1. 将节点重新添加到父节点的子节点列表（如果有父节点）
        2. 恢复节点的位置
        3. 如果有多个子节点，调整父节点的其他子节点位置
        4. 将节点重新添加到场景中显示
        5. 恢复节点的连接线
        
        注意：使用正向遍历，确保先恢复父节点再恢复子节点
        """
        # 遍历所有被删除的节点（正向遍历）
        for node in self.context.m_nodeList:
            # 如果有父节点，将节点重新添加到父节点的子节点列表
            if node.parentNode:
                node.parentNode.sonNode.append(node)
                # 如果父节点有多个子节点，需要调整其他子节点的位置
                if len(node.parentNode.sonNode) > 1:
                    # 调整节点位置
                    self.context.m_scene.adjustNode(node.parentNode, node)
                    # 重新调整所有连接线位置
                    self.context.m_scene.adjustBranch()
                # 恢复父节点与该节点的连接线
                self.context.m_scene.addBranch(node.parentNode, node)
            
            # 调试输出：打印节点位置
            print(node.x, node.y)
            # 恢复节点在场景中的位置
            node.setPos(node.x, node.y)

            # 将节点重新添加到场景中（使其显示在界面上）
            self.context.m_scene.addItem(node)
            # 将节点重新添加到场景的节点列表
            self.context.m_scene.NodeList.append(node)

        # 重新激活之前被删除的节点（恢复激活状态）
        self.context.m_scene.setActivateNode(self.context.m_activateNode)

    def redo(self):
        """
        重做操作：再次删除节点及其子树
        
        执行步骤（对每个节点，反向遍历）:
        1. 从父节点的子节点列表中移除节点（如果有父节点）
        2. 从场景节点列表中移除节点
        3. 删除与节点相关的连接线
        4. 从场景中移除节点图形项
        5. 如果有其他子节点，调整父节点的其他子节点位置
        
        注意：使用反向遍历（[::-1]），确保先删除子节点再删除父节点
        """
        # 遍历所有要删除的节点（反向遍历，先删除子节点）
        for node in self.context.m_nodeList[::-1]:
            # 如果有父节点，从父节点的子节点列表中移除节点
            if node.parentNode:
                node.parentNode.sonNode.remove(node)
                # 如果父节点还有其他子节点，需要调整它们的位置
                # reverse=True表示反向调整（删除时的操作）
                if len(node.parentNode.sonNode) > 0:
                    self.context.m_scene.adjustNode(node.parentNode, node, True)
                    # 重新调整所有连接线位置
                    self.context.m_scene.adjustBranch()
            
            # 从场景的节点列表中移除节点
            self.context.m_scene.NodeList.remove(node)

            # 删除与节点相关的连接线
            self.context.m_scene.removeBranch(node)
            # 从场景中移除节点图形项（不再显示）
            self.context.m_scene.removeItem(node)

        # 激活被删除节点的父节点（如果有父节点），否则激活None
        if self.context.m_activateNode.parentNode:
            self.context.m_scene.setActivateNode(self.context.m_activateNode.parentNode)
        else:
            # 如果没有父节点（粘贴的节点），尝试激活场景中的第一个节点，或者设置为None
            if self.context.m_scene.NodeList:
                self.context.m_scene.setActivateNode(self.context.m_scene.NodeList[0])
            else:
                self.context.m_scene.setActivateNode(None)


# ============================================================================
# MoveCommand类：移动节点命令
# ============================================================================
class MoveCommand(QUndoCommand):
    """
    移动节点命令类，用于实现移动节点的撤销/重做功能
    
    功能:
    - 移动节点及其子树到新位置
    - 支持撤销（移动回原位置）和重做（再次移动）
    - 支持命令合并，将连续的移动操作合并为单个命令
    - 处理拖拽操作，避免重复应用移动
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化移动节点命令
        
        参数:
        - context: 命令上下文对象，context.m_pos包含移动的偏移量[dx, dy]
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(MoveCommand, self).__init__(*args, **kwargs)
        # 保存上下文对象
        self.context = context
        
        # ====================================================================
        # _applied标志位说明
        # ====================================================================
        # _applied表示此命令描述的移动是否已经在场景中执行
        # 当为True时，第一次调用redo()将不执行任何操作（no-op）
        # 这样在拖拽操作后立即推入命令时，可以避免重复应用移动
        self._applied = False

    def undo(self):
        """
        撤销操作：将节点移动回原位置
        
        执行步骤（对每个节点）:
        1. 将节点向相反方向移动（-dx, -dy）
        2. 更新节点的坐标记录
        3. 调整所有连接线位置
        4. 重新激活节点
        """
        # 遍历所有要移动的节点
        for node in self.context.m_nodeList:
            # 获取移动偏移量
            dx, dy = self.context.m_pos
            # 将节点向相反方向移动（撤销移动）
            node.moveBy(-dx, -dy)
            # 更新节点坐标记录
            node.x -= dx
            node.y -= dy
        # 重新调整所有连接线位置（因为节点位置改变了）
        self.context.m_scene.adjustBranch()
        # 重新激活节点
        self.context.m_scene.setActivateNode(self.context.m_activateNode)

    def redo(self):
        """
        重做操作：再次移动节点到新位置
        
        执行步骤:
        1. 如果移动已经应用（_applied=True），跳过执行（避免重复移动）
        2. 对所有节点应用移动偏移量
        3. 更新节点的坐标记录
        4. 调整所有连接线位置
        5. 设置_applied标志为True
        
        注意：当命令在拖拽后创建时，移动已经在视觉上完成，
        因此第一次redo()应该跳过，避免重复移动
        """
        # 如果此命令的移动已经在场景中应用（如拖拽操作）
        # 跳过第一次redo()调用，避免重复应用移动
        if self._applied:
            # 标记为未应用，以便未来的redo()（在undo之后）会应用移动
            self._applied = False
            return

        # 遍历所有要移动的节点
        for node in self.context.m_nodeList:
            # 获取移动偏移量
            dx, dy = self.context.m_pos
            # 将节点移动到新位置
            node.moveBy(dx, dy)
            # 更新节点坐标记录
            node.x += dx
            node.y += dy
        # 重新调整所有连接线位置（因为节点位置改变了）
        self.context.m_scene.adjustBranch()
        # 重新激活节点
        self.context.m_scene.setActivateNode(self.context.m_activateNode)
        # 标记移动已经应用到场景
        self._applied = True

    def mergeWith(self, command):
        """
        合并移动命令
        
        功能:
        - 将连续的移动操作合并为单个命令
        - 减少撤销栈中的命令数量，提高性能
        
        参数:
        - command: 要合并的命令对象
        
        返回:
        - True: 合并成功
        - False: 无法合并（命令类型不同或激活节点不同）
        """
        # 检查命令ID是否相同（必须是MoveCommand）
        if command.id() != self.id():
            print('id diff')
            return False
        # 检查激活节点是否相同（只能合并同一节点的移动）
        if self.context.m_activateNode != command.context.m_activateNode:
            print('activate node diff')
            return False
        # 注释掉的代码：检查节点列表是否相同（如果需要更严格的合并条件）
        '''if self.context.m_nodeList != command.context.m_activateNode:
            print('subTree diff')
            return False'''
        
        # 合并移动偏移量（累加）
        self.context.m_pos[0] += command.context.m_pos[0]
        self.context.m_pos[1] += command.context.m_pos[1]

        return True

    def id(self):
        """
        返回命令的唯一标识ID
        
        返回:
        - MoveCommandID: 移动命令的ID常量
        """
        return MoveCommandID


# ============================================================================
# NodeColorCommand类：修改节点背景颜色命令
# ============================================================================
class NodeColorCommand(QUndoCommand):
    """
    修改节点背景颜色命令类，用于实现修改节点颜色的撤销/重做功能
    
    功能:
    - 修改激活节点的背景颜色
    - 支持撤销（恢复原颜色）和重做（再次应用新颜色）
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化修改节点颜色命令
        
        参数:
        - context: 命令上下文对象，context.m_color包含新颜色，context.m_activateNode是要修改的节点
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(NodeColorCommand, self).__init__(*args, **kwargs)
        # 保存上下文对象
        self.context = context
        # 保存节点的原始颜色（用于撤销时恢复）
        self.color = self.context.m_activateNode.m_color

    def undo(self):
        """
        撤销操作：恢复节点的原始颜色
        
        执行步骤:
        1. 将节点颜色设置为保存的原始颜色
        2. 重新激活节点（触发界面更新）
        """
        # 调试输出
        print('node color undo')
        # 恢复节点的原始颜色
        self.context.m_activateNode.setColor(self.color)
        # 重新激活节点（触发界面更新）
        self.context.m_scene.setActivateNode(self.context.m_activateNode)

    def redo(self):
        """
        重做操作：再次应用新颜色
        
        执行步骤:
        1. 将节点颜色设置为上下文中的新颜色
        2. 重新激活节点（触发界面更新）
        """
        # 应用新颜色（从上下文获取）
        self.context.m_activateNode.setColor(self.context.m_color)
        # 重新激活节点（触发界面更新）
        self.context.m_scene.setActivateNode(self.context.m_activateNode)


# ============================================================================
# TextColorCommand类：修改文本颜色命令
# ============================================================================
class TextColorCommand(QUndoCommand):
    """
    修改文本颜色命令类，用于实现修改节点文本颜色的撤销/重做功能
    
    功能:
    - 修改激活节点的文本颜色
    - 支持撤销（恢复原颜色）和重做（再次应用新颜色）
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化修改文本颜色命令
        
        参数:
        - context: 命令上下文对象，context.m_textColor包含新颜色，context.m_activateNode是要修改的节点
        - *args, **kwargs: 传递给父类的参数
        """
        # 调用父类构造函数
        super(TextColorCommand, self).__init__(*args, **kwargs)
        # 保存上下文对象
        self.context = context
        # 保存节点的原始文本颜色（用于撤销时恢复）
        self.textColor = self.context.m_activateNode.m_textColor

    def undo(self):
        """
        撤销操作：恢复节点的原始文本颜色
        
        执行步骤:
        1. 将节点文本颜色设置为保存的原始颜色
        2. 重新激活节点（触发界面更新）
        """
        # 恢复节点的原始文本颜色
        self.context.m_activateNode.setTextColor(self.textColor)
        # 重新激活节点（触发界面更新）
        self.context.m_scene.setActivateNode(self.context.m_activateNode)

    def redo(self):
        """
        重做操作：再次应用新文本颜色
        
        执行步骤:
        1. 将节点文本颜色设置为上下文中的新颜色
        2. 重新激活节点（触发界面更新）
        """
        # 应用新文本颜色（从上下文获取）
        self.context.m_activateNode.setTextColor(self.context.m_textColor)
        # 重新激活节点（触发界面更新）
        self.context.m_scene.setActivateNode(self.context.m_activateNode)


# ============================================================================
# 未实现的命令类（TODO: 待实现）
# ============================================================================
# 注意：以下命令类尚未完整实现，仅作为占位符

# TODO: Cut, Copy, Paste Command
# ============================================================================
# CutCommand类：剪切命令（未实现）
# ============================================================================
class CutCommand(QUndoCommand):
    """
    剪切节点命令类（未实现）
    
    功能（计划）:
    - 剪切节点及其子树到剪贴板
    - 支持撤销（恢复节点）和重做（再次删除）
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化剪切命令（未实现）
        """
        super(CutCommand, self).__init__(*args, **kwargs)

    def undo(self):
        """
        撤销操作（未实现）
        """
        pass

    def redo(self):
        """
        重做操作（未实现）
        """
        pass


# ============================================================================
# CopyCommand类：复制命令（未实现）
# ============================================================================
class CopyCommand(QUndoCommand):
    """
    复制节点命令类（未实现）
    
    功能（计划）:
    - 复制节点及其子树到剪贴板
    - 注意：复制操作通常不需要撤销/重做
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化复制命令（未实现）
        """
        super(CopyCommand, self).__init__(*args, **kwargs)

    def undo(self):
        """
        撤销操作（未实现，复制操作通常不需要撤销）
        """
        pass

    def redo(self):
        """
        重做操作（未实现，复制操作通常不需要重做）
        """
        pass


# ============================================================================
# PasteCommand类：粘贴命令（未实现）
# ============================================================================
class PasteCommand(QUndoCommand):
    """
    粘贴节点命令类（未实现）
    
    功能（计划）:
    - 从剪贴板粘贴节点及其子树
    - 支持撤销（删除粘贴的节点）和重做（再次粘贴）
    """
    def __init__(self, context, *args, **kwargs):
        """
        初始化粘贴命令（未实现）
        """
        super(PasteCommand, self).__init__(*args, **kwargs)

    def undo(self):
        """
        撤销操作：删除粘贴的节点（未实现）
        """
        pass

    def redo(self):
        """
        重做操作：再次粘贴节点（未实现）
        """
        pass