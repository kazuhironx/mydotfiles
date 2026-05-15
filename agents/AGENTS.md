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
