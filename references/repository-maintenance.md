# 发布仓库维护约定

## 授权与范围

用户要求将 xueshu 发布到 `git@github.com:zhouyanyu/xueshu-skill.git`，后续修改 skill 时同步更新仓库及必要的 README，通过 PowerShell 使用 SSH 上传。仓库已由 `xueshu` 更名为 `xueshu-skill`，旧 checkout 同步前先核对并更新 origin。

- SSH：`git@github.com:zhouyanyu/xueshu-skill.git`
- 浏览入口：`https://github.com/zhouyanyu/xueshu-skill`
- 发布：`SKILL.md`、`agents/`、`references/`、`scripts/`、README 和必要的验证文件或发布配置。
- 排除：原书、提取正文、个人笔记、阅读进度、Wiki、私钥凭据、缓存和临时文件。

这是随 skill 修改执行的持续同步约定，不是后台监听或定时任务。普通精读、问答和 Wiki 更新不触发发布。安装目录和 frontmatter 名称保持 `xueshu`。其他使用者的 fork 或定制不自动向原作者仓库发布；只有明确要求时才改变目标。

## PowerShell 与 Windows SSH

使用 PowerShell 调用 Git，远端保持上述 SSH 地址。优先 Windows 自带 OpenSSH，保留正常主机密钥校验：

```powershell
git -c 'core.sshCommand=C:/Windows/System32/OpenSSH/ssh.exe -o BatchMode=yes -o ConnectTimeout=15' ls-remote --symref 'git@github.com:zhouyanyu/xueshu-skill.git' HEAD
```

可为本 checkout 设置 `core.sshCommand`，不改全局配置。需要诊断代理时可用 `ssh-add -l` 查看公开指纹，不读取私钥。主机密钥冲突、认证失败、连接超时或仓库权限不足时保留工作，报告具体阻碍；不关闭主机校验、不改用未经授权的发布方式。

如果推送提示 denied to 某个其他账号，检查 github.com 主机配置是否通过 `IdentityFile` 和 `IdentitiesOnly` 固定了该账号密钥；代理中有原账号密钥不代表实际使用了它。已确认存在可访问本仓库的原账号密钥时，仅为本 checkout 的 `core.sshCommand` 增加 `-o IdentitiesOnly=yes -i <对应密钥路径>`。保留其他账号配置和代理密钥，不读取密钥内容，不把个人密钥路径写入公共仓库。

## 每次更新

1. 检查安装目录、交付副本和可用 checkout，确认此次变更及他人变更。优先复用 checkout，否则在当前任务工作目录克隆；过去聊天的路径不保证存在。
2. 获取远端最新状态，确认默认分支。已有远端正常快进或合并，空仓库可建立 `main`。不重置他人变更、不强制推送；不能可靠处理的冲突保留修改并报告。
3. 同步根目录技能文件。行为、用法、输出、安装或依赖变化时更新 README；不将未实现自动化写成已支持。
4. 运行可用的 skill 格式校验和引用检查；变动脚本运行相应验证。纯文档更新无需新增无关测试。检查 README 示例与实际流程一致。
5. 审查 diff，只暂存本次发布文件，排除个人材料、缓存、凭据和临时文件。核对安装副本与发布内容一致。
6. 创建清楚的提交，通过 PowerShell 和 SSH 正常推送已确认分支。用户原始请求和本约定授权此范围内同步，无需每次重复询问；工具权限仍按环境处理。
7. 用 `git ls-remote` 对比远端分支与本地 HEAD，一致才报告完成。失败时保留本地提交、交付文件和下一续接点。

不能把修改本 skill 扩展成发布用户知识库，也不能为未来未知变更预先创建提交。
