#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
================================================================================
模块: main.py
功能: 思维导图应用程序的主入口文件
描述: 
    - 负责初始化应用程序和各个窗口
    - 建立主窗口、备注窗口、链接窗口之间的信号连接关系
    - 启动Qt应用程序的事件循环
================================================================================
"""

# ============================================================================
# 导入标准库模块
# ============================================================================
import os  # 用于操作系统相关功能
import sys  # 用于系统相关功能和退出程序

# ============================================================================
# 导入PyQt5模块
# ============================================================================
from PyQt5.QtGui import *      # 导入Qt图形界面相关的类
from PyQt5.QtWidgets import *  # 导入Qt窗口部件相关的类
from PyQt5.QtCore import *     # 导入Qt核心功能相关的类

# ============================================================================
# 导入自定义模块
# ============================================================================
from mainwindow import MainWindow  # 导入主窗口类
from Component import *            # 导入组件模块（包含Note、Link、AnnotationWindow等类）


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    应用程序入口函数，负责初始化主窗口和各功能窗口，并建立信号连接关系。
    
    执行流程:
    1. 创建Qt应用程序对象
    2. 初始化配置管理器
    3. 创建主窗口、备注窗口、链接窗口
    4. 建立各窗口之间的信号/槽连接
    5. 启动应用程序事件循环
    """
    # ========================================================================
    # 创建Qt应用程序对象
    # ========================================================================
    # QApplication管理整个应用程序的控制流和主设置
    # sys.argv是命令行参数列表，传递给Qt用于处理系统级参数
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    # 设置应用程序名称，用于在系统中标识该应用
    app.setApplicationName('MindMap')
    app.setOrganizationName('Qiushi0919')

    # ========================================================================
    # 初始化配置管理器
    # ========================================================================
    # Store mutable preferences in the user's application config directory.
    # This keeps packaged apps read-only and prevents recent paths from being
    # written into the source checkout.
    settings_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    QDir().mkpath(settings_dir)
    settings = QSettings(os.path.join(settings_dir, 'settings.ini'), QSettings.IniFormat)
    # 检查是否已有最近打开路径的配置项
    if not settings.value('lastpath'):
        # 若还没有保存过 lastpath，则初始化为空列表
        settings.setValue('lastpath', [])

    # ========================================================================
    # 创建主窗口和功能窗口
    # ========================================================================
    # 创建主窗口，传入配置管理器以便保存和读取设置
    window = MainWindow(settings)
    # 创建备注窗口，用于编辑节点的备注信息，传入当前主题
    NoteWindow = Note(theme=window.m_theme)
    # 创建链接窗口，用于编辑节点的超链接信息，传入当前主题
    LinkWindow = Link(theme=window.m_theme)
    # 创建批注窗口，用于编辑节点的批注信息，传入当前主题和父窗口（用于翻译）
    annotation_window = AnnotationWindow(window, theme=window.m_theme)
    # 创建节点信息窗口，集成批注和链接功能，传入父窗口（用于翻译）
    node_info_window = NodeInfoWindow(window, theme=window.m_theme)
    
    # 在主窗口中保存这些窗口的引用，以便主题切换时更新
    window.note_window = NoteWindow
    window.link_window = LinkWindow
    window.annotation_window = annotation_window
    window.node_info_window = node_info_window

    # ========================================================================
    # 主窗口 与 备注窗口之间的信号/槽连接
    # ========================================================================
    # 在主窗口中点击"添加备注"时，弹出备注窗口
    # addNote信号携带位置坐标和当前备注内容
    window.addNote.connect(NoteWindow.handle_addnote)
    # 关闭主窗口时，通知备注窗口一并关闭
    # close_signal是主窗口关闭时发出的信号
    window.close_signal.connect(NoteWindow.handle_close)
    # 当场景发出关闭信号时，同样关闭备注窗口
    # press_close是场景点击时发出的关闭子窗口的信号
    window.scene.press_close.connect(NoteWindow.handle_close)

    # 备注窗口编辑完成后，将备注内容回传给主窗口
    # note信号携带备注文本内容
    NoteWindow.note.connect(window.getNote)
    # 备注内容发生修改时，通知主窗口"内容已改变"，用于更新保存状态等
    # noteChange信号用于标记文档已被修改，需要保存
    NoteWindow.noteChange.connect(window.contentChanged)

    # ========================================================================
    # 主窗口 与 链接窗口之间的信号/槽连接
    # ========================================================================
    # 在主窗口中点击"添加链接"时，弹出链接编辑窗口
    # addLink信号携带位置坐标和当前链接内容
    window.addLink.connect(LinkWindow.handle_addLink)
    # 主窗口关闭时，关闭链接窗口
    window.close_signal.connect(LinkWindow.handle_close)
    # 场景发出关闭信号时，同样关闭链接窗口
    window.scene.press_close.connect(LinkWindow.handle_close)

    # 链接窗口确认后，将链接值回传给主窗口
    # link信号携带链接URL文本
    LinkWindow.link.connect(window.getLink)
    # 链接被修改时，通知主窗口"内容已改变"
    LinkWindow.linkChange.connect(window.contentChanged)

    # ========================================================================
    # 主窗口 与 批注窗口之间的信号/槽连接
    # ========================================================================
    # 在场景中右键节点选择"添加批注"时，弹出批注窗口
    # addAnnotation信号携带位置坐标和当前批注内容
    # 通过主窗口的中间处理函数，确保记录当前节点
    window.scene.addAnnotation.connect(window.handle_addAnnotation)
    # 关闭主窗口时，通知批注窗口一并关闭
    window.close_signal.connect(annotation_window.handle_close)
    # 当场景发出关闭信号时，同样关闭批注窗口
    window.scene.press_close.connect(annotation_window.handle_close)

    # 批注窗口编辑完成后，将批注内容回传给主窗口
    # annotation信号携带批注文本内容
    annotation_window.annotation.connect(window.getAnnotation)
    # 批注内容发生修改时，通知主窗口"内容已改变"，用于更新保存状态等
    # annotationChange信号用于标记文档已被修改，需要保存
    annotation_window.annotationChange.connect(window.contentChanged)

    # 当点击批注图标时，显示批注窗口
    # showAnnotation信号在节点点击批注图标时发出
    window.scene.showAnnotation.connect(window.show_annotation)
    
    # ========================================================================
    # 主窗口 与 节点信息窗口之间的信号/槽连接
    # ========================================================================
    # 当点击节点时，显示节点信息窗口（包含批注和链接）
    # showNodeInfo信号在节点被单击时发出
    window.scene.showNodeInfo.connect(window.show_node_info)
    # 关闭主窗口时，通知节点信息窗口一并关闭
    window.close_signal.connect(node_info_window.handle_close)
    # 当场景发出关闭信号时，同样关闭节点信息窗口
    window.scene.press_close.connect(node_info_window.handle_close)
    
    # 节点信息窗口编辑完成后，将批注内容回传给主窗口
    # 重写handle_close方法，在关闭时获取批注并保存
    original_handle_close = node_info_window.handle_close
    def _handle_node_info_close():
        if node_info_window.onMode:
            # 获取当前内容
            annotation_text = node_info_window.getCurrentContent()
            # 获取节点的链接（如果存在）
            target_node = getattr(window, '_node_info_editing_node', None)
            if not target_node:
                target_node = window.scene.m_activateNode
            link_text = getattr(target_node, 'm_link', 'https://') if target_node else 'https://'
            # 调用主窗口的处理函数，保存批注和链接
            window.getNodeInfo(annotation_text, link_text)
        # 调用原始的关闭方法
        original_handle_close()
    node_info_window.handle_close = _handle_node_info_close
    
    # 当点击OK按钮时，保存批注（handle_ok会发出annotation信号）
    def _handle_node_info_annotation(annotation_text):
        # 获取节点的链接（如果存在）
        target_node = getattr(window, '_node_info_editing_node', None)
        if not target_node:
            target_node = window.scene.m_activateNode
        link_text = getattr(target_node, 'm_link', 'https://') if target_node else 'https://'
        # 调用主窗口的处理函数，保存批注和链接
        window.getNodeInfo(annotation_text, link_text)
    node_info_window.annotation.connect(_handle_node_info_annotation)
    
    # 批注内容发生修改时，通知主窗口"内容已改变"
    node_info_window.annotationChange.connect(window.contentChanged)

    # ========================================================================
    # 启动应用程序事件循环
    # ========================================================================
    # app.exec_()启动Qt的事件循环，程序会一直运行直到窗口关闭
    # sys.exit()确保程序正常退出，返回应用程序的退出码
    sys.exit(app.exec_())


# ============================================================================
# 程序入口
# ============================================================================
if __name__ == '__main__':
    # 仅当本文件被直接运行时，才执行 main() 函数
    # 这样设计可以防止该文件被作为模块导入时自动执行main函数
    main()
