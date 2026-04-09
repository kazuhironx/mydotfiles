# Copilot Instructions (Global Default)

This file is the fallback instruction set used when a project does not have its own `copilot-instructions.md`.

## Language

- 回答は日本語で行うこと

## Coding Style

- Google Coding Standard に従うこと
- 主な使用言語: C++

## Commit Messages

- 1行目は簡潔に英語で書くこと
- 必要に応じて2行目以降に詳細を記載する

## Command Execution Policy

以下の操作は必ずユーザーに確認を取ってから実行すること:

- `rm` / ファイルやディレクトリの削除
- `git push` / リモートへの反映
- git管理外のファイルの編集・作成・削除
- その他、破壊的・不可逆な操作

以下の操作は確認不要で自動的に進めてよい:

- `grep`, `find`, `cat`, `ls` などの読み取り系コマンド
- `xargs`, `read`, `awk`, `sed`(表示のみ) などのデータ処理系
- git管理下のファイルの編集
- `git add`, `git commit`, `git status`, `git diff`, `git log` などのローカルgit操作
- ビルド、テスト、lint の実行
