

<p align="center">
  <img src="assets/torchgo-logo.png" width="150" alt="TorchGo Logo">
</p>

<h1 align="center">TorchGo · 火炬学</h1>

<p align="center">面向 PyTorch 与计算机视觉学习者的离线学习、检测与复习工具。</p>

## 项目简介

TorchGo 将知识卡片、应用题、章节检测、整体测试和模拟考试整合到同一套题库中。目前包含 10 章、579 张知识卡片和 200 道应用题，共 779 项学习内容。

Android 版采用 Capacitor 封装离线 Web 应用；桌面版采用 Python/Tkinter。学习记录仅保存在用户设备上，不依赖服务器或账号。




https://github.com/user-attachments/assets/fe58059b-3fb7-4009-be87-a9908ccebd76





## 主要功能

- 完整题库学习：知识卡片与应用题使用同一套可见内容。
- 学习断点恢复：保存题目顺序、当前位置、已选答案和卡片展开状态。
- 间隔复习：按照 1、3、7、14、30、60 天安排复习。
- 章节检测：可选择章节、题量和难度。
- 整体测试：跨十章随机抽题。
- 50 题模拟考试：限时、答题卡、标记复查、自动保存和错题解析。
- 完全离线：不申请网络权限，学习数据只保存在本机。

## 知识章节

1. Tensor 与 PyTorch 基础
2. Dataset、DataLoader 与数据
3. 神经网络训练机制
4. CNN 基础
5. 经典 CNN 与 Backbone
6. 深度学习训练技巧
7. 图像分类
8. 语义分割
9. 目标检测与车道线检测
10. Transformer 与现代视觉网络

## 仓库结构

```text
TorchGo/
├─ apps/
│  ├─ android/       # Capacitor Android 应用
│  │  ├─ www/        # 界面、交互和题库数据
│  │  └─ android/    # 原生 Android 工程
│  └─ desktop/       # Python/Tkinter 桌面版
├─ assets/            # 品牌资源
├─ docs/              # 项目文档
├─ tools/             # 题库导出工具
└─ .github/           # CI、Issue 和 PR 模板
```

## Android 开发

### 环境要求

- Node.js 22 或更高版本
- JDK 21
- Android SDK Platform 36
- Android Studio，或 VS Code + Android/Java 扩展

### 安装与同步

```powershell
cd apps/android
npm ci
npx cap sync android
```

使用 Android Studio 时，打开 `apps/android/android`。使用 VS Code 时，可以直接打开仓库根目录或 `apps/android`。

### 构建调试 APK

Windows：

```powershell
.\android\gradlew.bat -p .\android assembleDebug
```

macOS/Linux：

```bash
./android/gradlew -p ./android assembleDebug
```

生成文件位于：

```text
apps/android/android/app/build/outputs/apk/debug/app-debug.apk
```

## 桌面版运行

桌面版只依赖 Python 标准库和 Tkinter。在 Windows 上可以双击：

```text
apps/desktop/start-torchgo.bat
```

也可以直接运行：

```bash
python apps/desktop/quiz_app.py
```

桌面版会在程序目录生成本地 JSON 学习记录，这些文件已经加入 `.gitignore`。

## 更新题库

题库源数据位于 `apps/desktop`。修改后运行：

```bash
python tools/export_quiz_data.py
```

脚本会重新生成 Android 版使用的 `apps/android/www/data.js`。

## 参与贡献

提交 Issue 或 Pull Request 前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。题库内容的修改需要同时提供正确答案、解析、章节、类型和难度信息。

## 隐私

TorchGo 不需要账号，Android 版不申请网络权限。学习进度、考试历史和错题记录只保存在本机。卸载应用或清除应用数据会删除这些记录。

## 版本

当前版本：V1.0。更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。你可以使用、修改、分发和用于商业项目，但需要保留原始版权与许可证声明。

## 作者    




- 开发者：王利群
- 联系邮箱：lntano021114@gmail.com
- Copyright © 2026 王利群.
