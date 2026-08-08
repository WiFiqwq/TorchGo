# GitHub 发布清单

## 首次公开前

- [x] 选择并加入 MIT 开源许可证。
- [x] 根据许可证调整应用“关于”页面中的版权措辞。
- [ ] 确认 `lntano021114@gmail.com` 可以公开展示。
- [ ] 确认 Logo、题库和全部代码均有权公开发布。
- [ ] 查看 `git status`，确保没有个人记录、APK、密钥或本地配置。
- [ ] 在 GitHub 创建空仓库，不要额外生成 README 或 `.gitignore`。

## 本地首次提交

```bash
git add .
git status
git commit -m "Initial open-source release"
git remote add origin https://github.com/<用户名>/TorchGo.git
git push -u origin main
```

## GitHub 仓库设置建议

- Description：`离线 PyTorch 与计算机视觉学习、检测和复习工具`
- Topics：`pytorch`、`computer-vision`、`education`、`android`、`capacitor`、`python`
- 开启 Issues 和 Discussions。
- 保持 Actions 与 Dependabot 启用。
- 为 `main` 分支启用 Pull Request 和 CI 检查保护。

## 发布 APK

正式 Release 应使用独立的发布密钥签名。密钥、密码和签名配置不得提交到仓库。建议通过 GitHub Secrets 或本地安全环境注入，并在 Releases 页面附上 APK 的 SHA-256。
