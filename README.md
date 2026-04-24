# mydotfiles

個人用 dotfiles リポジトリ。Zsh / tmux / Emacs / GitHub Copilot CLI の設定をまとめて管理しています。

## 含まれる設定

| ディレクトリ | 内容 |
|---|---|
| `zsh/.zshrc` | Zsh 設定 |
| `tmux/.tmux.conf` | tmux 設定 |
| `emacs/init.el` | Emacs 設定 |
| `starship/starship.toml` | Starship プロンプト設定 |
| `git/.gitconfig` | Git 共有設定 (delta / lfs / merge など) |
| `git/.gitconfig.local.example` | ユーザー固有設定のテンプレート (user/credential など) |
| `copilot/` | GitHub Copilot CLI 設定 (skills, hooks, scripts) |

## 依存ツール

### 必須

| ツール | 用途 | インストール |
|--------|------|-------------|
| `zsh` | シェル | `sudo apt install zsh` |
| `tmux` (3.6+) | ターミナルマルチプレクサ | `sudo apt install tmux` |
| `emacs` (30+) | エディタ | [ビルド手順](#5-emacs-302-のビルド-ubuntu-2204) |
| `git` (2.35+) | バージョン管理 (`merge.conflictstyle = zdiff3` に必要) | `sudo apt install git` |
| `git-delta` | diff/pager 表示 | `sudo apt install git-delta` |
| `git-lfs` | Large File Storage | `sudo apt install git-lfs` |
| `fzf` | ファジー検索 (zsh履歴, tmux picker) | `sudo apt install fzf` |
| `fd-find` | ファイル名検索 (consult-fd, affe) | `sudo apt install fd-find` |
| `ripgrep` | ファイル内容検索 (consult-ripgrep) | `sudo apt install ripgrep` |
| `starship` | プロンプト | `curl -sS https://starship.rs/install.sh \| sh` |
| `zsh-autosuggestions` | 入力補完 | `sudo apt install zsh-autosuggestions` |
| `zsh-syntax-highlighting` | シンタックスハイライト | `sudo apt install zsh-syntax-highlighting` |

### LSP サーバー (言語別)

| ツール | 言語 | インストール |
|--------|------|-------------|
| `clangd` | C/C++ | `sudo apt install clangd` |
| `gopls` | Go | `go install golang.org/x/tools/gopls@latest` |
| `rust-analyzer` | Rust | `rustup component add rust-analyzer` |

### オプショナル

| ツール | 用途 | インストール |
|--------|------|-------------|
| `ghq` | リポジトリ管理 (consult-ghq) | `go install github.com/x-motemen/ghq@latest` |
| `emacs-lsp-booster` | eglot 高速化 | [GitHub](https://github.com/blahgeek/emacs-lsp-booster) |
| `pandoc` | Markdown プレビュー | `sudo apt install pandoc` |
| `asdf` | バージョンマネージャ | [公式手順](https://asdf-vm.com/) |
| `git-gtr` | git worktree 管理 | `go install github.com/nicr9/git-gtr@latest` |
| GitHub Copilot CLI | AI アシスタント | `npm install -g @githubnext/github-copilot-cli` |

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

# Starship
mkdir -p ~/.config
ln -sf ~/dotfiles/starship/starship.toml ~/.config/starship.toml

# GitHub Copilot CLI (グローバル設定)
ln -sf ~/dotfiles/copilot ~/.config/github-copilot/

# Git (共有設定)
ln -sf ~/dotfiles/git/.gitconfig ~/.gitconfig
# ユーザー固有設定 (user.name / email など) はテンプレートからコピーして編集
cp ~/dotfiles/git/.gitconfig.local.example ~/.gitconfig.local
$EDITOR ~/.gitconfig.local
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
  libtree-sitter-dev libgccjit-12-dev gcc-12 g++-12 \
  libncurses-dev \
  libxpm-dev libpng-dev libjpeg-dev libgif-dev libtiff-dev librsvg2-dev libwebp-dev

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
  --with-tree-sitter

make -j$(nproc)
sudo make install
```

> **Note:** GCC 12 の `-O2` は `xdisp.c` の native-comp 中にICE (Internal Compiler Error) を起こすことがあるため、`-O1` を使用しています。

> **Note:** `init.el` で実際に使う機能 (native-comp, tree-sitter, eglot, magit, GUI) のみ有効化しています。画像拡張 (`--with-imagemagick`) や動的モジュール (`--with-modules`) が必要な場合は configure オプションと対応する `lib*-dev` パッケージを追加してください。Emacs 30 では JSON サポートが内蔵化されたため `--with-json` / `libjansson-dev` は不要です。

## ライセンス

MIT
