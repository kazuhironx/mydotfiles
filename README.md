# mydotfiles

個人用のdotfilesリポジトリです。Zsh、Herdr、Emacs、Gitの設定に加えて、複数のAIコーディングエージェント（Claude Code、Codex、GitHub Copilot CLI）のグローバル指示をまとめて管理しています。

## 含まれる設定

| ディレクトリ | 内容 |
|---|---|
| `zsh/.zshrc` | Zshの設定 |
| `herdr/config.toml` | Herdrの設定（`C-t` prefixのキーバインド） |
| `emacs/init.el` | Emacsの設定 |
| `starship/starship.toml` | Starshipのプロンプト設定 |
| `hunk/config.toml` | hunkの設定（gitのdiffとpagerの表示） |
| `git/.gitconfig` | Gitの共有設定（hunk pager、lfs、mergeなど） |
| `git/.gitconfig.local.example` | ユーザー固有設定（userやcredential）のテンプレート |
| `agents/AGENTS.md` | AIエージェント共通のグローバル指示（唯一のソース） |
| `agents/skills/` | 全エージェントが共通で使うAgent Skills（ツールに依存しない手法） |
| `scripts/setup-agmsg.sh` | agmsgのインストールと更新 |
| `claude/CLAUDE.md` | Claude Code用（`agents/AGENTS.md`へのsymlink） |
| `claude/skills/` | Claude Code専用のAgent Skills |
| `claude/settings.json` | Claude Codeのユーザー設定（`~/.claude/settings.json`） |
| `claude/statusline.sh` | Claude Codeのstatuslineスクリプト |
| `codex/AGENTS.md` | Codex用（`agents/AGENTS.md`へのsymlink） |
| `codex/skills/` | Codex専用のAgent Skills |
| `copilot/copilot-instructions.md` | GitHub Copilot CLI用（`agents/AGENTS.md`へのsymlink） |
| `copilot/skills/` | GitHub Copilot CLI専用のAgent Skills |
| `scripts/bootstrap.sh` | clone後に1回実行し、全設定をリンクする初期化スクリプト |
| `scripts/setup-skills.sh` | Agent Skillsのsymlinkをskill単位で張り直すスクリプト（bootstrapが呼ぶ） |

### AIエージェント設定の方針

`agents/AGENTS.md`を唯一のソースとし、各ツールの設定パスにsymlinkを張って同じ内容を読ませます。
指示を更新するときは、`agents/AGENTS.md`だけを編集してください。

Agent Skillsは、置くディレクトリで配信先のツールを分けます。

- `agents/skills/<name>/`は全エージェントに配信する共通skill
- `claude/skills/<name>/`はClaude Codeだけに配信
- `codex/skills/<name>/`はCodexだけに配信
- `copilot/skills/<name>/`はGitHub Copilot CLIだけに配信

`~/.agents/skills/`と各ツールの`~/.<tool>/skills/`は実ディレクトリのままにします。
`scripts/setup-skills.sh`は、`agents/skills/`の共通skillと`<tool>/skills/`の専用skillを、skill単位のsymlinkとしてその中に張ります。
ディレクトリ全体をsymlinkにすると、専用skillを同じ場所に置けなくなるため、この方式にしています。
skillを追加するときは、適切な場所にディレクトリを作って`setup-skills.sh`を再実行してください。

#### crit（エージェント出力のレビュー）

[crit](https://crit.md/)は、エージェントの計画、差分、実行中のページをブラウザ上でインラインレビューするCLIです。
`crit`と`crit-cli`の2つのskillは、各ツールの`<tool>/skills/`に専用skillとして置いています。
upstreamがツールごとにauthor名、実行方式（Claudeはbackground実行、Codexはforeground実行）、frontmatterを変えているためです。
ファイルは[upstreamのintegrations](https://github.com/tomasz-tomczyk/crit/tree/main/integrations)から変更せずに取り込んでいます。
更新するときは、各skillの`ATTRIBUTION.md`に書いたソースから取り直してください。
skillを動かすには`crit`本体のインストールも必要です（[依存ツール](#オプショナル)を参照）。

#### hunk-review（差分レビューセッションへのエージェント参加）

[hunk](https://www.hunk.dev/)のライブdiffセッションに、エージェントが`hunk session *`経由で参加し、該当行にインラインコメントを付けるskillです。
`hunk-review`は共通の`agents/skills/`に置き、全ツールへ配信しています。
critと違って、upstreamのSKILL.mdがツールに依存せず、内容が同じだからです。
`hunkdiff` npmパッケージに同梱された`$(hunk skill path)`から変更せずに取り込み、更新は`ATTRIBUTION.md`に書いた手順で行います。
使うときは、端末で`hunk diff`を起動しておき、エージェントに「hunkセッションをレビューして」と依頼してください。
指摘が差分の該当行の横に表示されます（`hunk/config.toml`の`agent_notes = true`で表示を有効にしています）。

#### explainer、explainer-book、first-reader（人間向けの説明資料）

[mizchi/explainer](https://github.com/mizchi/explainer)の3つのskillを、共通の`agents/skills/`に変更せずに取り込んでいます。
`explainer`は、読み手1人のペルソナに合わせた速習資料を書き、引用した出力と図を道具で検証します。
`explainer-book`はその章立て版です。`../explainer/scripts/`を呼ぶので、2つのskillは同じディレクトリに並べて置いてください。
`first-reader`は、公開前の下書きを模擬読者に読ませ、読むのをやめた箇所を報告するskillです。下書きの書き直しはしません。
explainer系のスクリプトを動かすには、資料を置くリポジトリにnpmパッケージを入れる必要があります（[依存ツール](#オプショナル)を参照）。
更新するときは、各`ATTRIBUTION.md`に書いたコミットから取り直してください。

#### yomiyasu（AIっぽい日本語のリライト）

[nanaism/yomiyasu](https://github.com/nanaism/yomiyasu)（[解説記事](https://zenn.dev/algoartis/articles/0b1c731881b25c)）を、共通の`agents/skills/`に取り込んでいます。
AIが生成した日本語の非生物主語、比喩動詞、名詞化、過剰な装飾を書き直すskillです。
同梱の`scripts/yomiyasu_lint.py`（Python 3の標準ライブラリだけで動く）で、文章を静的に採点できます。
`design-doc`も、日本語の文体はこのskillに従います。

プロジェクト固有の指示としては、各リポジトリの`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md`が優先です。
Claude Code（v2.1.277以降）は、プロジェクトに`CLAUDE.md`が無ければ`AGENTS.md`を読みます。
そのため、プロジェクト側は`AGENTS.md`を1つ置けば全ツールに読ませられます。
ユーザーレベルの`~/.claude/CLAUDE.md`はこのフォールバックの対象外なので、symlinkを残しています。
Claude Codeは`~/.agents/skills/`も探索せず、`~/.claude/skills/`だけを読みます。
このため、skill単位のsymlinkは引き続き必要です。

## 依存ツール

### 必須

| ツール | 用途 | インストール |
|--------|------|-------------|
| `zsh` | シェル | `sudo apt install zsh` |
| `herdr` | エージェント対応のターミナルマルチプレクサ | `curl -fsSL https://herdr.dev/install.sh \| sh` |
| `emacs`（30以上） | エディタ | [ビルド手順](#6-emacs-302-のビルド-ubuntu-2204) |
| `git`（2.35以上） | バージョン管理（`merge.conflictstyle = zdiff3`に必要） | `sudo apt install git` |
| `hunk` | diffとpagerの表示（`core.pager = hunk pager`で使う。Node 18以上が必要） | `npm i -g hunkdiff`（[詳細](#7-hunk-のインストール)） |
| `git-lfs` | Large File Storage | `sudo apt install git-lfs` |
| `fzf` | ファジー検索（zshの履歴） | `sudo apt install fzf` |
| `fd-find` | ファイル名検索（consult-fd、affe） | `sudo apt install fd-find` |
| `ripgrep` | ファイル内容の検索（consult-ripgrep） | `sudo apt install ripgrep` |
| `starship` | プロンプト | `curl -sS https://starship.rs/install.sh \| sh` |
| `zsh-autosuggestions` | 入力補完 | `sudo apt install zsh-autosuggestions` |
| `zsh-syntax-highlighting` | シンタックスハイライト | `sudo apt install zsh-syntax-highlighting` |

### LSPサーバー（言語別）

| ツール | 言語 | インストール |
|--------|------|-------------|
| `clangd` | C/C++ | `sudo apt install clangd` |
| `gopls` | Go | `go install golang.org/x/tools/gopls@latest` |
| `rust-analyzer` | Rust | `rustup component add rust-analyzer` |

### オプショナル

| ツール | 用途 | インストール |
|--------|------|-------------|
| `ghq` | リポジトリ管理（consult-ghq） | `go install github.com/x-motemen/ghq@latest` |
| `emacs-lsp-booster` | eglotの高速化 | [GitHub](https://github.com/blahgeek/emacs-lsp-booster) |
| `pandoc` | Markdownのプレビュー | `sudo apt install pandoc` |
| `asdf` | バージョンマネージャ | [公式手順](https://asdf-vm.com/) |
| `git-gtr` | git worktreeの管理 | `git clone https://github.com/coderabbitai/git-worktree-runner ~/dev/github.com/coderabbitai/git-worktree-runner && ln -s ~/dev/github.com/coderabbitai/git-worktree-runner/bin/git-gtr ~/.local/bin/`（[GitHub](https://github.com/coderabbitai/git-worktree-runner)） |
| GitHub Copilot CLI | AIアシスタント | `npm install -g @githubnext/github-copilot-cli` |
| `crit` | エージェント出力のブラウザレビュー（`crit`と`crit-cli`のskillが使う） | [公式手順](https://crit.md/) |
| `sqlite3` | agmsgのメッセージ保存 | `sudo apt install sqlite3` |
| Node 24以上とnpm | `explainer`系skillのスクリプト。資料を置くリポジトリで`npm i -D @mizchi/vlmkit @mizchi/vlmkit-anim marked playwright`を実行する（Mermaidの図を使うなら`mermaid`、アイコンを使うなら`@iconify-json/lucide @iconify-json/logos`も入れる） | [公式](https://nodejs.org/) |
| Python 3 | `first-reader`と`yomiyasu`のスクリプト（標準ライブラリだけで動く） | `sudo apt install python3` |

## インストール

### 1. リポジトリをクローン

`git/.gitconfig`の`ghq.root = ~/dev`に合わせて、ghqと同じ場所にcloneします。
ghqが入っていれば、`ghq get kazuhironx/mydotfiles`でも同じ場所に入ります。
各スクリプトは自分の位置からリポジトリのパスを求めるので、別の場所に置いても問題ありません。

```bash
git clone https://github.com/kazuhironx/mydotfiles.git ~/dev/github.com/kazuhironx/mydotfiles
cd ~/dev/github.com/kazuhironx/mydotfiles
```

### 2. bootstrapスクリプトを実行

clone後に`scripts/bootstrap.sh`を1回実行すると、すべてのリンクが張られます。

```bash
scripts/bootstrap.sh
```

このスクリプトは次の作業をします。

- zsh、Herdr、emacs、starship、hunk、gitの設定ファイルへのsymlinkを`~`側に張る
- `AGENTS.md`へのsymlinkを張る（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.copilot/copilot-instructions.md`）
- Claude Codeの`~/.claude/settings.json`と`~/.claude/statusline.sh`へのsymlinkを張る
- `~/.gitconfig.local`が無ければexampleからコピーする（既にあれば変更しない）
- `scripts/setup-skills.sh`を呼び、Agent Skillsのsymlinkをskill単位で張る

スクリプトは何度実行しても同じ結果になります。
既存の実ファイルや実ディレクトリは上書きせず、symlinkだけを張り替えます。
ユーザー固有のgit設定（`user.name`、`user.email`、`credential.helper`など）は`~/.gitconfig.local`に書いてください。

> **Note:** 共有の`~/.gitconfig`は末尾で`[include] path = ~/.gitconfig.local`を読み込みます。マシン固有の設定は`~/.gitconfig.local`に書き、mydotfilesでは管理しません。このファイルが無くても、gitはエラーを出さずに無視します。

skillのリンクだけを張り直したいとき（skillを追加したときなど）は、`scripts/setup-skills.sh`を単独で実行してください。
削除したskillの古いsymlinkも、このときに消えます。

### Agent Team（agmsg）

`scripts/setup-agmsg.sh`は、[agmsg](https://github.com/fujibee/agmsg)の最新の`main`をインストールまたは更新します。
実行時のDBとteamの登録情報の置き場所は、Gitで管理しない`~/.agents/skills/agmsg/`です。

```bash
sudo apt install sqlite3
scripts/setup-agmsg.sh
```

Herdrの中で対象のプロジェクトを開き、Claude Codeを起動してモデルをFableに切り替えます。

```bash
claude
```

```text
/model fable
```

続いて、各エージェントの役割とモデルをプロンプトで指定してください。構成はタスクごとに変えられます。

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

agmsgはエージェント間の通信と役割の管理を、Herdrはpaneとプロセスの管理を受け持ちます。
agmsgの`spawn`は使わず、Herdrでpaneを作って各エージェントのCLIを起動してください。

### 3. 反映

```bash
# Zsh — 新しいシェルを開くか:
source ~/.zshrc

# Herdr — 起動中なら:
herdr server reload-config
```

### 4. Herdr

`herdr`を実行すると、default sessionを起動するか、既存のsessionに再接続します。

主なキーバインドは次のとおりです。

| 操作 | キー |
|---|---|
| prefix | `C-t` |
| paneを閉じる | `C-t 0` |
| paneを新しいtabへ移す | `C-t 1` |
| 上下に分割、左右に分割 | `C-t 2`、`C-t 3` |
| 次のpaneへ移る | `C-t o`、`C-t C-o` |
| tabを閉じる、tabを作る | `C-t k`、`C-t c` |
| 直前のpaneまたはtabへ戻る | `C-t t`、`C-t ,` |
| workspace、tab、paneのpicker | `C-t w` |
| paneの最大化を切り替える | `C-t z` |
| 現在のrepoをhunk diffでレビューする | `C-t d` |
| tab 1から9へ直接移る | `M-1`から`M-9` |
| 通知元へ移る（`C-t ,`で戻る） | `C-t .` |

tabへの直接移動は1から9までです。
Herdrにはpaneの出力を続けて記録する機能が無いので、記録が必要なコマンドは`tee`などに通してください。

マウスで選択した範囲は、そのままクリップボードにコピーされます。
Herdrがマウス操作を受け取っている間に端末の右クリックメニューを開くには、`Shift`を押しながら右クリックしてください。

Herdrのインストール後に対象のエージェントのintegrationを追加すると、エージェントのセッションをより正確に復元できます。
各コマンドは既存のエージェントのhook設定を書き換えるので、実行前に差分を確認してください。

```bash
herdr integration install claude
herdr integration install codex
herdr integration install copilot
```

### 5. Emacs: Tree-sitter グラマーのインストール

Emacs 30のTree-sitterモード（`c-ts-mode`、`go-ts-mode`など）を使うには、初回起動後に次のコマンドを実行してください。

```
M-x treesit-install-language-grammar RET c
M-x treesit-install-language-grammar RET cpp
M-x treesit-install-language-grammar RET go
M-x treesit-install-language-grammar RET rust
M-x treesit-install-language-grammar RET yaml
M-x treesit-install-language-grammar RET json
```

### 6. Emacs 30.2 のビルド (Ubuntu 22.04)

ソースからビルドする場合の手順です。native-comp、GTK3、GnuTLS、Tree-sitterを有効にしています。

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

> **Note:** GCC 12の`-O2`は、`xdisp.c`をnative-compするときにICE（Internal Compiler Error）を起こすことがあります。そのため`-O1`を使っています。

> **Note:** configureでは、`init.el`が実際に使う機能（native-comp、tree-sitter、eglot、magit、GUI）だけを有効にしています。画像拡張（`--with-imagemagick`）や動的モジュール（`--with-modules`）が必要なら、configureのオプションと対応する`lib*-dev`パッケージを追加してください。Emacs 30はJSONのサポートを内蔵したので、`--with-json`と`libjansson-dev`は不要です。

### 7. hunk のインストール

`~/.gitconfig`で`core.pager = hunk pager`を指定しているので、[hunk](https://www.hunk.dev/)が無いと`git diff`、`git log`、`git show`が動きません。
hunkにはNode.js 18以上が必要です。
設定はbootstrapが`hunk/config.toml`を`~/.config/hunk/config.toml`にsymlinkして共有します。

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

> **Note:** hunkはフルスクリーンのTUIビューアなので、deltaの`--color-only`のようなインラインフィルタ（`interactive.diffFilter`）としては使えません。旧来の`[interactive]`と`[delta]`のセクションは削除しました。`git add -p`はgit既定の色付きdiffで表示されます。

## ライセンス

MIT
