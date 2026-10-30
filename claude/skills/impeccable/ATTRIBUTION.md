Source: https://github.com/pbakaus/impeccable/tree/02523aec3e4c4580102d996d1b6a71fbe062e03f/.claude/skills/impeccable
Upstream: https://github.com/pbakaus/impeccable (docs: https://impeccable.style/docs)
Author: Paul Bakaus
License: Apache-2.0 (LICENSE and NOTICE.md copied from repo root)
Install method: README "Manual copy, no Node required" (skill version 4.8.0, engine 0.1.18).
Local changes: none to the skill. The design hook (SessionStart/PostToolUse/Stop) and
the .claude/agents/impeccable-* subagents from `npx impeccable install` are
intentionally not installed, to avoid always-on processing.
Engine binary is downloaded once by scripts/impeccable into ~/.impeccable/bin/<ver>/
and verified against scripts/engine-checksums.txt.
