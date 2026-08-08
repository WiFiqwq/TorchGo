# 参与贡献

感谢你愿意帮助改进 TorchGo。

## 开始之前

1. 先搜索已有 Issue，避免重复工作。
2. 较大的功能建议先创建 Issue，说明目标、交互和兼容性影响。
3. 不要提交个人学习记录、APK、Android SDK、JDK、密钥或构建缓存。

## 开发流程

1. Fork 仓库并创建功能分支。
2. 在 `apps/android` 执行 `npm ci` 和 `npx cap sync android`。
3. 完成修改后检查 JavaScript 语法：`node --check apps/android/www/app.js`。
4. 修改题库源数据后运行 `python tools/export_quiz_data.py`。
5. 至少完成一次 Android Debug APK 构建。
6. 提交 Pull Request，说明修改内容、验证方式和界面变化。

## 题库贡献要求

每道应用题应包含：

- 唯一 ID；
- 所属章节；
- 题目类型与难度；
- 清晰、互斥的四个选项；
- 唯一正确答案；
- 能解释原因而非只重复答案的解析。

知识卡片应包含名词、类别、核心解释和补充理解。新增内容需要避免与现有卡片重复。

## 代码风格

- HTML、CSS、JavaScript 使用 2 个空格缩进。
- Python 使用 4 个空格缩进。
- 保持应用离线可用，不要无必要地增加远程服务或跟踪组件。
- 界面需要兼顾窄屏手机，并确保长文本可以换行。
