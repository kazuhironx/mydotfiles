# mydotfiles

個人用 dotfiles リポジトリ。Zsh / tmux / Herdr / Emacs / Git に加えて、複数の AI コーディングエージェント (Claude Code / Codex / GitHub Copilot CLI) のグローバル指示を一元管理しています。

## 含まれる設定

| ディレクトリ | 内容 |
|---|---|
| `zsh/.zshrc` | Zsh 設定 |
| `tmux/.tmux.conf` | tmux 設定 |
| `herdr/config.toml` | Herdr 設定 (tmux 互換キーバインド) |
| `emacs/init.el` | Emacs 設定 |
| `starship/starship.toml` | Starship プロンプト設定 |
| `hunk/config.toml` | hunk 設定 (git の diff/pager 表示) |
| `git/.gitconfig` | Git 共有設定 (hunk pager / lfs / merge など) |
| `git/.gitconfig.local.example` | ユーザー固有設定のテンプレート (user/credential など) |
| `agents/AGENTS.md` | AI エージェント共通グローバル指示 (single source of truth) |
| `agents/skills/` | 全エージェント共通で使う Agent Skills (ツール非依存 methodology) |
| `scripts/setup-agmsg.sh` | agmsg のインストール / 更新 |
| `claude/CLAUDE.md` | Claude Code 用 (symlink → `agents/AGENTS.md`) |
| `claude/skills/` | Claude Code 専用 Agent Skills |
| `codex/AGENTS.md` | Codex 用 (symlink → `agents/AGENTS.md`) |
| `codex/skills/` | Codex 専用 Agent Skills |
| `copilot/copilot-instructions.md` | GitHub Copilot CLI 用 (symlink → `agents/AGENTS.md`) |
| `copilot/skills/` | GitHub Copilot CLI 専用 Agent Skills |
| `copilot/{hooks,scripts}/` | Copilot CLI 固有の hook / script |
| `scripts/bootstrap.sh` | clone 後 1 発で全設定をリンクする初期化スクリプト |
| `scripts/setup-skills.sh` | Agent Skills の per-skill symlink を貼り直す (bootstrap から呼ばれる) |

### AI エージェント設定の方針

`agents/AGENTS.md` を **唯一のソース** として、各ツールの設定パスへは
symlink を貼って同じ内容を参照させます。指示を更新するときは
`agents/AGENTS.md` だけ編集すれば全ツールに反映されます。

Agent Skills は配置先で対象ツールを切り分けます:

- `agents/skills/<name>/` — 全エージェントに配信される共通 skill
- `claude/skills/<name>/`  — Claude Code のみに配信
- `codex/skills/<name>/`   — Codex のみに配信
- `copilot/skills/<name>/` — GitHub Copilot CLI のみに配信

`~/.agents/skills/` と各ツールの `~/.<tool>/skills/` は **実ディレクトリ** にして、`scripts/setup-skills.sh`
が `agents/skills/` の共通 skill と `<tool>/skills/` の専用 skill を per-skill
symlink で配下に張ります。dir 全体を symlink にすると専用 skill を同居させ
られなくなるため、この方式にしています。新しい skill を後から足したいとき
は適切な場所に dir を作って `setup-skills.sh` を再実行するだけで反映されます。

#### crit (エージェント出力のレビュー)

[crit](https://crit.md/) はエージェントの計画・差分・実行中ページをブラウザ上で
インラインレビューする CLI です。`crit` / `crit-cli` の 2 skill を各ツールの
`<tool>/skills/` に **専用 skill** として配置しています (共通 `agents/skills/`
ではない)。upstream が author 名・実行方式 (Claude は background 実行、Codex は
foreground) ・frontmatter をツールごとに変えており、内容が同一ではないためです。
ファイルは [upstream の integrations](https://github.com/tomasz-tomczyk/crit/tree/main/integrations)
から verbatim で vendoring しており、更新は各 skill の `ATTRIBUTION.md` 記載の
ソースから再取得します。skill が動くには `crit` バイナリ本体のインストールが
必要です ([依存ツール](#オプショナル) 参照)。

#### hunk-review (差分レビューセッションへのエージェント参加)

[hunk](https://www.hunk.dev/) のライブ diff セッションへエージェントが `hunk session *`
経由で参加し、該当行にインラインコメントを刺す skill です。`hunk-review` 1 skill を
**共通 `agents/skills/`** に配置し、全ツールへ配信しています (crit と違い upstream の
SKILL.md がツール非依存で内容が同一のため)。`hunkdiff` npm パッケージ同梱の
`$(hunk skill path)` から verbatim で vendoring し、更新は `ATTRIBUTION.md` 記載の
手順で再取得します。使い方: 端末で `hunk diff` を起動しておき、エージェントに
「hunk セッションをレビューして」と依頼すると、指摘が差分の該当行脇に表示されます
(`hunk/config.toml` の `agent_notes = true` が表示を有効化)。

プロジェクト固有の指示は各リポジトリの `AGENTS.md` /
`CLAUDE.md` / `.github/copilot-instructions.md` が優先されます。

## 依存ツール

### 必須

| ツール | 用途 | インストール |
|--------|------|-------------|
| `zsh` | シェル | `sudo apt install zsh` |
| `tmux` (3.6+) | ターミナルマルチプレクサ | `sudo apt install tmux` |
| `herdr` | Agent-aware ターミナルマルチプレクサ | `curl -fsSL https://herdr.dev/install.sh \| sh` |
| `emacs` (30+) | エディタ | [ビルド手順](#6-emacs-302-のビルド-ubuntu-2204) |
| `git` (2.35+) | バージョン管理 (`merge.conflictstyle = zdiff3` に必要) | `sudo apt install git` |
| `hunk` | diff/pager 表示 (`core.pager = hunk pager`, Node 18+ 必須) | `npm i -g hunkdiff` ([詳細](#7-hunk-のインストール)) |
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
| `crit` | エージェント出力のブラウザレビュー (`crit` / `crit-cli` skill が利用) | [公式手順](https://crit.md/) |
| `sqlite3` | agmsg のメッセージ保存 | `sudo apt install sqlite3` |

## インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/kazuhironx/mydotfiles.git ~/dotfiles
```

### 2. bootstrap スクリプトを実行

クローン後、付属の `scripts/bootstrap.sh` を 1 回叩けば全配線が済みます。

```bash
~/dotfiles/scripts/bootstrap.sh
```

このスクリプトは以下をまとめてやります:

- zsh / tmux / Herdr / emacs / starship / git の `~` 側 symlink
- AGENTS.md の symlink (`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` / `~/.copilot/copilot-instructions.md`)
- `~/.gitconfig.local` を未作成なら example からコピー (既存があれば触らない)
- `scripts/setup-skills.sh` を呼んで Agent Skills の per-skill symlink を配置

idempotent (再実行 OK)、既存の実ファイル / 実ディレクトリは上書きしません (symlink のみ差し替え)。
ユーザー固有 git 設定 (`user.name` / `user.email` / `credential.helper` 等) は
`~/.gitconfig.local` を編集してください。

> **Note:** 共有 `~/.gitconfig` の末尾で `[include] path = ~/.gitconfig.local` を読み込むため、マシン固有設定は `~/.gitconfig.local` に書きます。**mydotfiles では管理しません** (マシンごと)。ファイルが存在しない場合は git は黙って無視するので安全です。

Skill だけ貼り直したいとき (新しい skill 追加時など) は `scripts/setup-skills.sh` を単独で叩けます。

### Agent Team (agmsg)

[agmsg](https://github.com/fujibee/agmsg) の最新 `main` をインストールまたは更新します。
実行時 DB と team 登録は Git 管理外の `~/.agents/skills/agmsg/` に置きます。

```bash
sudo apt install sqlite3
~/dotfiles/scripts/setup-agmsg.sh
```

Herdr 内で対象プロジェクトを開き、Claude Code を起動して Fable に切り替えます。

```bash
claude
```

```text
/model fable
```

続いて、役割とモデルをプロンプトで指定します。構成はタスクごとに変更できます。

```text
あなたはこのプロジェクトの orchestrator です。
最初に /agmsg で team に orchestrator として参加してください。

Herdr を使って次の peer Agent を別 pane に起動してください。

- implementer: Codex。実装とテストを担当する
- qa: Claude Code / claude-opus-4-8。変更せず、diff、テスト結果、
  要件適合性を検証する

implementer の初期プロンプトには `$agmsg actas implementer`、qa の初期プロンプトには
`/agmsg actas qa` と具体的な依頼を含めてください。
Agent 間の依頼と報告には agmsg を使ってください。

implementer の完了報告後に qa を起動してください。
qa の指摘があれば implementer に修正を依頼し、再度 qa を実行してください。
重大な指摘がなく、検証結果を確認できるまで完了扱いにしないでください。

今回の依頼:
Issue #123 を実装してください。
```

agmsg は Agent 間の通信と role 管理、Herdr は pane とプロセス管理を担当します。
agmsg の `spawn` は使わず、Herdr で pane を作成して各 Agent CLI を起動します。

### 3. 反映

```bash
# Zsh — 新しいシェルを開くか:
source ~/.zshrc

# tmux — セッション内で:
tmux source-file ~/.tmux.conf

# Herdr — 起動中なら:
herdr server reload-config
```

### 4. Herdr への移行

tmux はロールバック用に残し、Herdr と併用できます。
`herdr` を実行すると default session を起動または再接続します。

主なキーバインドは次のとおりです。

| 操作 | キー |
|---|---|
| prefix | `C-t` |
| pane を閉じる | `C-t 0` |
| pane を新規 tab へ分離 | `C-t 1` |
| 上下 / 左右に分割 | `C-t 2` / `C-t 3` |
| 次の pane | `C-t o` / `C-t C-o` |
| tab を閉じる / 作る | `C-t k` / `C-t c` |
| 直前の pane/tab | `C-t t` |
| workspace・tab・pane picker | `C-t w` |
| pane を zoom（最大化トグル） | `C-t z` |
| hunk diff で現在の repo をレビュー | `C-t d` |
| tab 1..9 へ直接移動 | `M-1` .. `M-9` |
| 通知元へ移動 | `C-t O` |

Herdr の tab index は 1..9 のため、tmux の `M-0` (window 10) に相当する直接移動はありません。
tmux の status line と `@unread` は Herdr の sidebar、agent state、画面内通知へ置き換わります。
`pipe-pane` に相当する継続的な pane ログはないため、必要なコマンド側で `tee` などを使用します。

マウス選択はそのままコピーされます。
Herdr がマウスを capture している間に端末側の右クリックメニューを使う場合は、`Shift` を押しながら右クリックします。

Agent のセッション復元精度を上げる場合は、Herdr のインストール後に対象だけ integration を追加します。
各コマンドは既存の Agent hook 設定を更新するため、実行前に差分を確認してください。

```bash
herdr integration install claude
herdr integration install codex
herdr integration install copilot
```

### 5. Emacs: Tree-sitter グラマーのインストール

Emacs 30 の Tree-sitter モード (`c-ts-mode`, `go-ts-mode` 等) を使うには、初回起動後に以下を実行してください。

```
M-x treesit-install-language-grammar RET c
M-x treesit-install-language-grammar RET cpp
M-x treesit-install-language-grammar RET go
M-x treesit-install-language-grammar RET rust
M-x treesit-install-language-grammar RET yaml
M-x treesit-install-language-grammar RET json
```

### 6. Emacs 30.2 のビルド (Ubuntu 22.04)

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

### 7. hunk のインストール

`~/.gitconfig` で `core.pager = hunk pager` を指定しているため、[hunk](https://www.hunk.dev/) が無いと `git diff` / `git log` / `git show` が動きません。Node.js 18+ が必要です。設定は `hunk/config.toml` を `~/.config/hunk/config.toml` に symlink して共有します (bootstrap が配線)。

#### npm

```bash
npm i -g hunkdiff
```

#### Homebrew

```bash
brew install modem-dev/tap/hunk
```

#### Nix

```bash
nix run github:modem-dev/hunk
```

#### 確認

```bash
hunk --version
git diff   # hunk のレビュー UI で side-by-side / 行番号付きに表示されればOK
```

> **Note:** hunk はフルスクリーンの TUI ビューアのため、delta の `--color-only` のような
> インラインフィルタ用途 (`interactive.diffFilter`) には使えません。旧 `[interactive]` /
> `[delta]` セクションは削除し、`git add -p` は git 既定の色付き diff にフォールバックします。

## ライセンス

MIT
