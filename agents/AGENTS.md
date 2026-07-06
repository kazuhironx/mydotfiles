# Global Agent Instructions

このファイルは Claude Code / Codex / GitHub Copilot CLI が共通で参照する
グローバル指示。プロジェクト固有指示があればそちらが優先。

## About me

- ソフトウェア開発者
- 文脈: 組み込み / C++ / Networking / Yocto

## Communication

- 回答は日本語
- 結論先出し、お世辞・前置き不要
- 不要な要約は省く

## Code conventions

- C++: Google Coding Standard
- コメントは WHY のみ。WHAT は名前で表現
- 投機的な抽象化や preemptive refactor は禁止
- 既存ファイル編集を新規作成より優先

## Git / Commit

- 1行目は簡潔に英語、必要に応じて2行目以降に詳細
- Conventional Commits 風 (`feat:` / `fix:` / `docs:` / `chore:` …)
- `--no-verify` 禁止
- `main` / `develop` への force-push 禁止
- `Co-Authored-By` トレーラーは付けない

## Command execution

破壊的・不可逆・外部影響のある操作のみ要確認。安全な操作(読み取り、
ビルド、テスト、ローカル git 操作、git 管理下ファイルの編集)は自動進行。

### プロセス kill は必ず PID 指定（self-match で自シェルを殺す事故を根絶）
`pkill -f NAME` / `kill $(pgrep -f NAME)` は **自分のコマンド行に NAME が含まれると自シェルごと kill**
され `exit 144` で処理が途中終了する。**`[N]AME` の bracket trick は pgrep の"引数自身"の self-match を
防ぐだけで、同一コマンド行の別の場所に NAME が生で出ていれば依然 self-match する**
(例: `timeout 210 python3 foo.py & ...; pkill -f foo.py` は前半の `foo.py` に当たる)。鉄則:
- **起動時に `PID=$!` を採り、`kill "$PID"` する**(最も確実)。
- pkill/pgrep を使うなら **その kill を単独コマンドにし、行内の他所に対象名を出さない**。
- 一括なら `pgrep -f "[b]racket"` で PID 列挙→PID で kill、かつその行に生の対象名を書かない。

### zsh の変数はデフォルトで word-split されない（POSIX sh と違う）
`$VAR` に空白区切りの複数語(コマンド+フラグ、オプション列)を入れて `$VAR ...` と実行すると、
**全体が1つのコマンド名/1引数**として扱われ "command not found" や引数無視で静かに失敗する
(例: `$CC -O2 x.c` が `aarch64-...-gcc -mcpu=... ...` を1コマンド名扱い、`ssh $SSHOPT ...` で -o が効かない)。鉄則:
- 複数語を実行するなら **`eval "$VAR ..."`** か **`${=VAR}`**(zsh の明示 split) を使う。
- ssh/scp のオプション列は**変数に入れずコマンドにインライン**で書く。
- 配列にできるなら配列(`cmd=(gcc -O2); $cmd`)。文字列展開に頼らない。
- 迷ったら **`bash -lc '...'`** で実行して zsh の非分割を回避(危ういコマンドは既定でこれにすると self-match/展開の両方を避けやすい)。
