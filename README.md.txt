# 水司智搜 · Smart Workspace 🌊
> 一款专为水务工程造价和采购打造的极速物资匹配与 AI 合同解析工具。

## ✨ 核心功能
- **极速匹配**：基于 RapidFuzz 的智能打分（名称 60% + 规格 40%），毫秒级比对万条数据。
- **AI 视觉解析**：接入多模态大模型（如通义千问），一键提取 PDF 扫描件中的物资明细。
- **数据安全**：纯本地运行，采用 Windows DPAPI 加密保存密码，自动生成备份。
- **Win11 现代 UI**：基于 CustomTkinter 的 Fluent Design 极简界面。

## 🖼️ 界面预览
*(在这里插入几张你之前截图里的漂亮界面图！非常重要！)*

## 🚀 快速开始
1. 克隆仓库：
   `git clone https://github.com/你的用户名/shuisi-smart-workspace.git`
2. 安装依赖：
   `pip install -r requirements.txt`
3. 准备数据目录：
   在根目录新建 `life` 文件夹，将 `sample_history.xlsx` 重命名为 `历史价格库.xlsx` 放进去。
4. 运行程序：
   `python run_match.py`

## 📦 打包指南
本项目提供 `build.spec` 文件。运行 `pyinstaller --clean build.spec` 即可打包。为防止杀毒软件误报，建议使用 `--onedir` 模式并关闭 UPX 压缩。

## 📄 开源协议
[LICENSE]