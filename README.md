# mydotfiles

個人用 dotfiles リポジトリ。Zsh / tmux / Emacs / GitHub Copilot CLI の設定をまとめて管理しています。

## 含まれる設定

| ディレクトリ | 内容 |
|---|---|
| `zsh/.zshrc` | Zsh 設定 |
| `tmux/.tmux.conf` | tmux 設定 |
| `emacs/init.el` | Emacs 設定 |
| `copilot/` | GitHub Copilot CLI 設定 (skills, hooks, scripts) |

## インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/kazuhironx/mydotfiles.git ~/dotfiles
```

### 2. シンボリックリンクを作成

クローンしたら、各設定ファイルをホームディレクトリにシンボリックリンクするだけで使えます。

```bash
# Zsh
ln -sf ~/dotfiles/zsh/.zshrc ~/.zshrc

# tmux
ln -sf ~/dotfiles/tmux/.tmux.conf ~/.tmux.conf

# Emacs
ln -sf ~/dotfiles/emacs/init.el ~/.emacs.d/init.el

# GitHub Copilot CLI (グローバル設定)
ln -sf ~/dotfiles/copilot ~/.config/github-copilot/
```

> **Note:** 既存ファイルがある場合は事前にバックアップを取ってください。`ln -sf` は既存のリンクを上書きしますが、実ファイル/ディレクトリがある場合は手動で退避が必要です。

### 3. 反映

```bash
# Zsh — 新しいシェルを開くか:
source ~/.zshrc

# tmux — セッション内で:
tmux source-file ~/.tmux.conf
```

### 4. Emacs: Tree-sitter グラマーのインストール

Emacs 30 の Tree-sitter モード (`c-ts-mode`, `go-ts-mode` 等) を使うには、初回起動後に以下を実行してください。

```
M-x treesit-install-language-grammar RET c
M-x treesit-install-language-grammar RET cpp
M-x treesit-install-language-grammar RET go
M-x treesit-install-language-grammar RET rust
```

## ライセンス

MIT
