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
M-x treesit-install-language-grammar RET yaml
M-x treesit-install-language-grammar RET json
```

### 5. Emacs 30.2 のビルド (Ubuntu 22.04)

ソースからビルドする場合の手順です。native-comp / GTK3 / GnuTLS / Tree-sitter を有効にしています。

```bash
# 依存パッケージ (主なもの)
sudo apt install build-essential texinfo libgtk-3-dev libgnutls28-dev \
  libjansson-dev libtree-sitter-dev libgccjit-12-dev gcc-12 g++-12

# ソース取得
git clone --depth 1 -b emacs-30.2 https://github.com/emacs-mirror/emacs.git
cd emacs

# configure (libgccjit が標準パスにない場合は LIBRARY_PATH / C_INCLUDE_PATH を指定)
export CC=gcc-12
export CFLAGS="-O1 -g"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/12
export C_INCLUDE_PATH=/usr/lib/gcc/x86_64-linux-gnu/12/include

./autogen.sh
./configure \
  --with-native-compilation \
  --with-gnutls \
  --with-x-toolkit=gtk3 \
  --with-tree-sitter \
  --with-imagemagick \
  --with-json \
  --with-modules

make -j$(nproc)
sudo make install
```

> **Note:** GCC 12 の `-O2` は `xdisp.c` の native-comp 中にICE (Internal Compiler Error) を起こすことがあるため、`-O1` を使用しています。

## ライセンス

MIT
