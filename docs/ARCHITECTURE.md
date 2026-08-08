# 项目架构

## 数据流

`apps/desktop` 中的 Python 模块是题库源数据。`tools/export_quiz_data.py` 将章节映射、知识卡片和应用题导出为 `apps/android/www/data.js`。

Android 版由三层组成：

1. `www/data.js`：离线题库数据；
2. `www/app.js` 与 `www/styles.css`：状态、交互和界面；
3. `android/`：Capacitor 容器、应用资源和原生返回事件。

## 本地状态

Android 版使用 WebView 的 `localStorage` 保存：

- 学习掌握状态与复习日期；
- 未完成学习会话；
- 测试答题统计；
- 未完成考试；
- 成绩历史。

桌面版使用程序目录下的 JSON 文件保存同类数据。这些运行时文件不进入版本控制。

## 生成文件

以下内容由安装、同步或构建过程生成，不应手工维护：

- `node_modules/`；
- `android/capacitor-cordova-android-plugins/`；
- `android/app/src/main/assets/`；
- 所有 `build/` 和 `.gradle/` 目录；
- APK/AAB 文件。
