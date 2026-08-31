# MindMap - 思维导图编辑器

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

一个现代化的桌面概念图编辑器，支持本地编辑，也可选通过 OrcaRouter 调用多模型 AI 生成概念图。

作者：谢秋实 朱拓源

更多系统框图、关键模块流程图、设计报告、软件运行界面在**报告**中有详细展示

---

## 📖 项目简介

MindMap 是一个基于 Python 和 PyQt5 开发的思维导图编辑软件。它提供多层级主题、曲线连接、手写批注、待办事项和文件导出等功能。AI 是可选能力：不填写 API Key 时，完整的本地编辑功能不受影响。

<img width="2504" height="1560" alt="image" src="https://github.com/user-attachments/assets/8df409c3-5f18-49f6-8c71-b0e086bc43d7" />

<img width="1224" height="974" alt="image" src="https://github.com/user-attachments/assets/de82e7ba-ef01-4f77-9a6c-16ac71a2a9ec" />

<img width="1796" height="1146" alt="image" src="https://github.com/user-attachments/assets/1fa99319-ec56-4181-8ba3-d3fc59b35d62" />

<img width="1784" height="744" alt="image" src="https://github.com/user-attachments/assets/05a05d69-518d-4b6a-81b6-4f4f6d8e69a4" />

<img width="728" height="471" alt="image" src="https://github.com/user-attachments/assets/751b3b62-4097-45fe-bd62-43fc3a547e9b" />

### 核心特点

- ✨ **AI 生成概念图**：通过 OrcaRouter 自由选择免费或付费模型
- 🎨 **现代概念图界面**：点阵画布、曲线分支、紧凑工具栏与多主题
- 🌐 **多语言支持**：支持中文和英文界面
- 🎯 **丰富的功能**：节点编辑、连接线管理、手写批注、待办事项等
- 💾 **完善的文件管理**：支持保存、加载、导出多种格式
- 🔄 **撤销/重做**：完整的操作历史管理
- 📝 **手写批注**：支持在思维导图上进行手写标注

---

## ✨ 功能特性

### 0. AI 概念图

- ✅ **OrcaRouter 可选 Provider**：不影响本地功能，支持 `orcarouter/free` 与其他模型 ID
- ✅ **主题生成**：输入中心主题和额外要求，自动创建三层概念图
- ✅ **隐私优先**：API Key 只在当前运行进程中保留，不写入项目或思维导图文件

### 1. 节点管理

- ✅ **多层级节点**：支持中心主题、分支主题、子主题、自由主题四个层级
- ✅ **节点编辑**：双击节点即可编辑文本内容
- ✅ **节点样式**：自定义节点背景颜色和文本颜色
- ✅ **节点缩放**：支持节点大小调整（拖拽右下角手柄）
- ✅ **节点移动**：支持单个节点移动或移动子树模式

### 2. 连接线管理

- ✅ **自动连接**：子节点自动与父节点连接
- ✅ **手动连线**：支持在不同节点之间创建连接线
- ✅ **连线管理**：批量创建和删除连接线
- ✅ **智能调整**：节点移动时连接线自动调整位置

### 3. 内容增强

- ✅ **备注功能**：为节点添加备注信息
- ✅ **链接功能**：为节点添加超链接，点击即可打开
- ✅ **批注功能**：为节点添加批注内容
- ✅ **节点信息**：集成显示节点的批注和链接信息
- ✅ **图标插入**：支持在节点中插入图片图标
- ✅ **待办事项**：为节点添加待办事项列表

### 4. 编辑操作

- ✅ **复制/粘贴**：支持节点及其子树的复制和粘贴
- ✅ **剪切/删除**：支持节点的剪切和删除操作
- ✅ **撤销/重做**：完整的操作历史，支持撤销和重做
- ✅ **移动子树**：移动节点时可选择是否同时移动子树

### 5. 文件管理

- ✅ **新建文件**：创建新的思维导图文件
- ✅ **打开文件**：打开已保存的思维导图（.mm格式）
- ✅ **保存文件**：保存思维导图为XML格式
- ✅ **另存为**：将思维导图保存到指定位置
- ✅ **自动保存**：每10秒自动保存一次（可配置）
- ✅ **最近文件**：记录最近打开的文件列表

### 6. 导出功能

- ✅ **导出PNG**：将思维导图导出为PNG图片
- ✅ **导出PDF**：将思维导图导出为PDF文档
- ✅ **打印功能**：支持直接打印思维导图
- ✅ **Markdown导入**：支持从Markdown文件导入思维导图

### 7. 界面定制

- ✅ **主题切换**：支持浅色、深色、黑白三种主题
- ✅ **语言切换**：支持中文和英文界面切换
- ✅ **视图缩放**：支持思维导图的放大和缩小
- ✅ **状态显示**：显示当前节点数量和操作提示

### 8. 手写批注

- ✅ **手写模式**：支持在思维导图上进行手写标注
- ✅ **画笔工具**：可选择画笔或橡皮擦模式
- ✅ **颜色选择**：手写颜色根据主题自动调整
- ✅ **批注管理**：支持批注的显示、隐藏和删除

---

## 🛠 技术栈

### 开发语言
- **Python 3.9+**

### GUI框架
- **PyQt5 5.15+**

### 核心模块
- `QGraphicsScene` - 场景管理
- `QGraphicsView` - 视图显示
- `QGraphicsTextItem` - 文本节点
- `QUndoStack` - 撤销/重做栈
- `QColorDialog` - 颜色选择对话框
- `QFileDialog` - 文件对话框

### 文件格式
- **XML** - 思维导图文件格式（.mm）
- **PNG** - 图片导出格式
- **PDF** - 文档导出格式
- **Markdown** - 导入支持

---

## 🚀 安装与运行

### 环境要求

- Python 3.9 或更高版本
- PyQt5 5.15 或更高版本

### 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone https://github.com/Qiushi0919/Mindmap-by-Python-and-PyQt.git
   cd Mindmap-by-Python-and-PyQt/源代码/源代码
   ```

2. **安装依赖**
   ```bash
   python -m pip install -r requirements.txt
   ```

### 运行程序

在 `源代码/源代码` 目录下执行：

```bash
python main.py
```

程序启动后，将显示主窗口界面。

### 使用 OrcaRouter AI

1. 在 [OrcaRouter](https://www.orcarouter.ai/) 创建 API Key。
2. 在应用中选择 **AI → AI 生成概念图**，或按 `Ctrl+Shift+G`。
3. 填入 Key、模型 ID 和中心主题，然后点击“Generate”。

默认模型是 `orcarouter/free`。免费容量可能限流，以 [OrcaRouter 模型目录](https://docs.orcarouter.ai/getting-started/models) 为准。也可通过环境变量 `ORCAROUTER_API_KEY` 预填 Key。

### 下载 EXE / DMG

已配置 GitHub Actions 跨平台构建。推送 `v*` 版本标签后，GitHub Releases 会自动附带 Windows x64 EXE、macOS Apple Silicon DMG 和 macOS Intel DMG。

---

## 📖 使用说明

### 基本操作

#### 创建节点
- **添加子节点**：选中节点后，按 `Insert` 键或点击工具栏"子主题"按钮
- **添加同级节点**：选中节点后，按 `Ctrl+Insert` 键
- **编辑节点**：双击节点即可编辑文本内容

#### 移动节点
- **单个移动**：直接拖拽节点
- **移动子树**：启用"移动子树"模式后，移动节点会同时移动其所有子节点
- **键盘移动**：使用方向键 `↑` `↓` `←` `→` 切换激活节点

#### 复制粘贴
- **复制**：选中节点后，按 `Ctrl+C` 或右键菜单选择"复制"
- **粘贴**：按 `Ctrl+V` 或右键菜单选择"粘贴"
- **剪切**：按 `Ctrl+X` 或右键菜单选择"剪切"

#### 删除节点
- 选中节点后，按 `Delete` 键或右键菜单选择"删除"
- **注意**：中心主题节点无法删除

### 样式设置

#### 修改节点颜色
1. 选中要修改的节点
2. 右键菜单选择"设置颜色"
3. 在颜色对话框中选择颜色
4. 点击确定应用

#### 修改文本颜色
1. 选中要修改的节点
2. 右键菜单选择"设置文本颜色"
3. 在颜色对话框中选择颜色
4. 点击确定应用

#### 切换主题
1. 点击菜单栏"主题"菜单
2. 选择"浅色"、"深色"或"黑白"主题
3. 所有节点和连接线会自动应用新主题样式

### 连接线管理

#### 创建连接线
1. 点击菜单栏"插入" → "关系"或工具栏"连线管理"按钮
2. 选择两个节点（先选源节点，再选目标节点）
3. 系统会自动创建连接线

#### 批量管理连接线
1. 选中多个节点（至少两个）
2. 点击"连线管理"按钮
3. 系统会自动创建或删除节点之间的连接线

### 手写批注

#### 启用手写模式
1. 点击工具栏"手写"按钮
2. 选择"画笔"或"橡皮擦"模式
3. 在思维导图上进行绘制

#### 退出手写模式
- 再次点击"手写"按钮即可退出

### 待办事项

#### 添加待办事项
1. 选中节点
2. 点击菜单栏"插入" → "待办事项"
3. 在对话框中输入待办事项内容
4. 点击"添加"按钮

#### 管理待办事项
- 在待办事项列表中，可以：
  - 点击"完成"标记已完成
  - 点击"删除"移除待办事项

### 快捷键

| 功能 | 快捷键 |
|------|--------|
| 新建文件 | `Ctrl+N` |
| 打开文件 | `Ctrl+O` |
| 保存文件 | `Ctrl+S` |
| 另存为 | `Ctrl+Shift+S` |
| 撤销 | `Ctrl+Z` |
| 重做 | `Ctrl+Y` |
| 复制 | `Ctrl+C` |
| 粘贴 | `Ctrl+V` |
| 剪切 | `Ctrl+X` |
| 删除 | `Delete` |
| 添加子节点 | `Insert` |
| 添加同级节点 | `Ctrl+Insert` |
| 切换激活节点 | `↑` `↓` `←` `→` |
| 退出编辑 | `Esc` |
| AI 生成概念图 | `Ctrl+Shift+G` |

---

## 📁 项目结构

```
Mindmap-by-Python-and-PyQt/
├── 源代码/源代码/
│   ├── main.py             # 程序入口
│   ├── mainwindow.py       # 主窗口与 AI 交互
│   ├── AIProvider.py       # OrcaRouter API 客户端与输出校验
│   ├── AIDialog.py         # AI 生成窗口与异步任务
│   ├── Graph.py            # 画布、导入与布局
│   ├── Node.py             # 节点绘制与交互
│   ├── Branch.py           # 曲线分支
│   ├── icons/              # SVG 界面图标
│   ├── images/             # 应用与工具栏图片
│   └── files/              # 示例导图
├── tests/                   # 自动化测试
├── scripts/                 # 本地打包和图标生成脚本
├── MindMap.spec             # PyInstaller 打包配置
└── .github/workflows/       # EXE / DMG 构建与 Release
```

### 核心模块说明

- **main.py**：应用程序入口，初始化主窗口和各功能窗口，建立信号连接
- **mainwindow.py**：主窗口类，包含菜单栏、工具栏、状态栏，管理文件操作和界面设置
- **Graph.py**：场景管理类，继承自QGraphicsScene，管理所有节点和连接线
- **Node.py**：节点类，继承自QGraphicsTextItem，实现节点的绘制、编辑、移动等功能
- **Branch.py**：连接线类，继承自 QGraphicsPathItem，实现节点之间的曲线
- **AIProvider.py**：不引入额外 SDK 的 OrcaRouter OpenAI-compatible 客户端
- **Command.py**：命令模式实现，支持撤销/重做功能
- **Component.py**：组件模块，包含备注窗口、链接窗口、待办事项等
- **Annotation.py**：批注和手写功能实现
- **Config.py**：全局配置常量，包括节点层级、命令ID、窗口尺寸等

---

## 💻 开发说明

### 代码风格

- 使用中文注释，详细说明函数功能和参数
- 遵循PEP 8 Python代码规范
- 使用有意义的变量名和函数名

### 扩展开发

#### 添加新功能

1. **添加新的节点属性**：
   - 在 `Node.py` 中添加属性
   - 在 `Graph.py` 的保存/加载方法中处理新属性

2. **添加新的命令**：
   - 在 `Command.py` 中创建新的命令类
   - 继承 `QUndoCommand` 并实现 `undo()` 和 `redo()` 方法

3. **添加新的主题**：
   - 在 `Node.py` 的 `paint()` 方法中添加主题样式
   - 在 `Branch.py` 的 `updateThemeStyle()` 方法中添加主题样式
   - 在 `mainwindow.py` 的菜单中添加主题选项

#### 调试技巧

- 使用 `print()` 输出调试信息
- 检查系统应用配置目录中的 `settings.ini`
- 查看控制台输出的错误信息

---

## 📝 更新日志

### 最新版本特性

- ✅ 可选 OrcaRouter Provider 与 AI 概念图生成
- ✅ 现代点阵画布、蓝色节点系统与曲线分支
- ✅ Windows EXE / macOS DMG 自动构建与 GitHub Release
- ✅ 支持三种主题：浅色、深色、黑白
- ✅ 支持中英文双语界面
- ✅ 支持手写批注功能
- ✅ 支持待办事项列表
- ✅ 支持节点信息窗口（集成批注和链接）
- ✅ 支持移动子树模式
- ✅ 支持连接线管理
- ✅ 支持Markdown导入
- ✅ 完善的撤销/重做功能
- ✅ 自动保存功能

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

本项目基于开源项目进行二次开发。如果您知道原项目的来源或需要修改许可证，请通过 Issue 联系我们。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m '  some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 分支与发布策略

- 新功能使用短期 `feature/*` 分支，通过 Pull Request 合并回 `main`。
- Windows 和 macOS 共用同一份源码，不设平台专用长期分支。
- 可下载安装包放入 GitHub Releases，不提交到 `main` 或单独的二进制分支。

---

## 👥 作者

- **开发者** - 谢秋实 朱拓源 熊锦宸

---

## 🙏 致谢

- 感谢 PyQt5 社区提供的优秀框架
- 感谢原开源项目 [Mindmap-by-Python-PyQt](https://github.com/Qiushi0919/Mindmap-by-Python-PyQt/tree/main) 的作者和贡献者（本项目基于此开源项目进行二次开发）
- 感谢所有贡献者的支持和建议

---

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件：1061839153@qq.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！⭐**

Made with ❤️ by MindMap Team

</div>
