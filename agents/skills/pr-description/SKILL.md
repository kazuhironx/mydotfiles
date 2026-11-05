---
name: pr-description
description: プルリクエストの説明（本文と図）を書く手順。差分を読み、振る舞いと構成の変化を見つけ、図がレビューを助けるときだけ図を作る（Before/After を同じ配置で並べた SVG を PNG にして PR に貼るのが既定で、Mermaid で十分なときだけ Mermaid）。図は explainer の figure-check で、本文は yomiyasu で検査してから出す。エージェントが自分の判断で PR を作るとき、利用者に PR を出すよう頼まれたとき（「PR を出して」「Draft PR」「gh pr create」）、既存の PR の本文を書き直すときに、名前を出されなくても使う。PR のレビューやコメントへの返信だけのときは使わない。
---

# pr-description

PR の本文は、レビュアーが「マージすると何が変わるか」「何が壊れうるか」を判定するための文書です。
ファイルの一覧や、変更後のコードの説明では足りません。**変更の前と後で何が違うか**を書きます。

この skill は、PR を作る・本文を更新する**すべての場合**に通します。
利用者が図や検査を指示しなくても、手順 1〜9 を自分で進めます。
push と PR の作成そのものは、リポジトリの規則（CLAUDE.md など）が確認を求めていれば、その確認を先に取ります。

## 手順

### 0. 準備（図を作るかどうかに関わらず、最初に）

```sh
S=<この SKILL.md のディレクトリ>                     # 例: ~/.claude/skills/pr-description
EXPLAINER=$S/../explainer; YOMIYASU=$S/../yomiyasu    # 隣に並んだ skill
W=${XDG_CACHE_HOME:-$HOME/.cache}/pr-description/work/<repo>-<branch>; mkdir -p $W
```

- 下書き・本文・図は、すべて `$W` に置く。**リポジトリの中にファイルを作らない。**
- 図の道具（npm・chromium）は、図を作ると決めたときだけ手順 5-2 で入れる。
- 既に PR があるかを `gh pr list --head <branch> --json number,url` で見る。あれば手順 8 は `gh pr edit` になる。`<branch>` は PR にするブランチ（`git branch --show-current`）。コミットの範囲だけを渡され、ブランチが決まっていなければ、この確認は手順 8 で push するときに行う。
  見つかった PR が対象のコミットを含むかを `gh pr view <n> --json commits` で確かめる。含まなければ別の変更の PR なので、新しいブランチから `gh pr create` にする。

```
1. 差分を読む        git diff <base>...HEAD と、変更箇所の周りのコード
2. 変化を書き出す    振る舞いの変化と構成の変化を、根拠つきで箇条にする
3. 図が要るか決める   下の「図を作る条件」。要らなければ 6 へ
4. 図の形式を選ぶ    下の「図の形式と種類」
5. 図を作って検査する SVG → PNG が既定。Mermaid で十分なときだけ Mermaid
6. 本文を書く        下の「本文の型」
7. 本文を検査する     explain-before-shorten → yomiyasu（日本語の本文のとき）→ ref-check.py（参照の書き方）
8. 出す             gh pr create / gh pr edit --body-file。PNG は --attach で PR に直接貼る
9. 表示を確かめる     PR のページで図が描画されているか
```

### 1. 差分を読む

- base は PR の向き先（多くは `origin/main`）。`git fetch` してから `git diff --stat <base>...HEAD` と `git diff <base>...HEAD` を読む。
- 差分の行だけで判断しない。変更した関数の呼び出し元・呼び出し先、設定を読む側、テストを読む。
- 変更の理由が、提案書・ADR・issue・コミットメッセージにあれば読む。

### 2. 変化を書き出す

内部メモに、次の 2 種類を分けて書く。**どの行にも根拠（`path:line`、コマンドとその出力、コミット）を付ける。**

- **振る舞いの変化**：入力・条件・出力・エラー・順序・既定値・互換性のうち、変わるもの。
- **構成の変化**：コンポーネント・プロセス・コンテナ・モジュールの追加と削除、依存の向き、データや信号の経路、責務の移動。

根拠が付けられない行は書かない。これが図と本文の材料のすべてです。

### 3. 図を作る条件

次の**どれか**に当たり、かつ文章だけではレビュアーが関係を追いにくいときに作る。

- 4 つ以上の要素の間の関係（経路・依存）が変わる
- 処理や通信の**順序**が変わる
- 状態の遷移が変わる
- 変更の前と後で構成が違い、並べると差が一目で分かる

**作らない**：誤字の修正、依存の更新、1 ファイル内のリファクタリング、テストだけの追加、ドキュメントの言い回しだけの変更、要素が 3 つ以下で文章で言える変更。
設計や構成を**提案する文書**（CP・ADR・設計書）を足す PR は、文書の変更でも、提案する構成について上の条件を当てる。
そのとき図の After は「提案が実装された後」の姿になるので、本文に「この PR で実際に変わるのは X だけ」と書き、図との区別を付ける。
作らなかったときは、本文に図が無い理由を書かない（書かないのが普通なので）。

### 4. 図の形式と種類

**既定は SVG を手で描き、PNG にして PR に貼る。** Mermaid は配置を道具が決めるので、Before と After で同じ箱を同じ位置に置けず、差が読み取りにくい。
Mermaid を使うのは、次の**すべて**に当たるときだけ。

- Before と After を並べて見比べる図ではない（変更後の順序や状態だけを見せれば足りる）
- 図の中に測った値（回数・時間の目盛り）を入れない
- 動く場所（ホスト・VM・コンテナ）の囲みが要らないか、1 段だけ
- 要素が 8 つ以下で、Mermaid の自動配置で矢印が読める

| 見せたいこと | 形式 |
|---|---|
| 構成・経路・依存の Before/After | **SVG → PNG**（下の「見やすい Before/After の型」） |
| 振る舞いの Before/After（回数・間隔・タイミング） | **SVG → PNG**。構成の帯の下に、測った値の目盛りを Before と After で同じ軸に並べる |
| 変更後の呼び出し・通信の順序だけ | Mermaid `sequenceDiagram` |
| 変更後の状態の遷移だけ | Mermaid `stateDiagram-v2` |
| データの形の変化 | 表。図なら Mermaid `classDiagram` / `erDiagram` |

#### 見やすい Before/After の型（SVG）

`$S/references/before-after.svg` を写して使う（幅 1040、ライトとダークの配色、`data-node`・`data-edge` 付き）。

1. **Before を上、After を下に置き、両方にある箱は同じ x 座標・同じ大きさにする。** 目が差だけを拾う。Before の囲みの高さは中身に合わせて低くしてよい（空いた段を残さない）。
2. **色は変わる箱と線だけに付ける。** 足すものは緑（`.new`・`.lnew`）、問題のある・消すものは赤（`.bad`）、変わらないものは灰色（`.box`・`.ln`）。凡例はタイトルに書く（「After（この PR。緑が足すもの）」）。
3. **無いものは点線の箱で見せる**（`.none`。例：「受け手なし」）。Before で欠けていたものが、After で埋まると分かる。
4. **動く場所を囲む**（`.zone`。ホスト・VM・コンテナ）。囲みの名前に実行方式を書く（「host B（systemd）」）。
5. **線にはプロトコルとポート**（「AMQP :5672」）。箱の 2 行目に役割や状態を小さく書く。
6. **振る舞いの差は、測った値を図に入れる。** 例：100 ms ごとの送信を 3 秒見たときの目盛りを、Before は 0 回（赤）、After は 30 回（緑）と同じ軸で並べ、右端に回数を書く。値は実際に測った出力から取り、出典を本文に書く。
7. **タイトルに比べている版を書く**（「Before（main abc1234）」「After（この PR）」）。
8. **図の下に 1〜3 行の注記**で、箱と線では言えない事実（起動の順・外し方など）を書く。図の中の語も本文と同じく、リポジトリの用語の決まり（CLAUDE.md など）に従う。
9. 文字は 12px 以上。線が文字や箱を横切らないよう、ゾーンの間に線のラベルの幅を空ける。

### 5. 図を作って検査する

#### 5-1. 事実シートを先に作る

図を描く前に、手順 2 のメモから `<name>.facts.json` を作る。**図に描く箱とラベルは、すべてここから取る。**

```json
{ "labels": ["api", "queue", "worker", "AMQP :5672"], "forbidden": ["cache"] }
```

Mermaid のときだけ `"edges": ["api->queue", "queue->worker"]` を足す。**SVG に `edges` を書くと figure-check が ✗ を出す。**

- `labels`：図に出すすべての名前。手順 2 で根拠を付けたものだけ。
- `forbidden`：差分に無いが、書きたくなる名前（推測した部品、変更で消えたもの、機密の値）。
- `edges`：Mermaid（.mmd）のときだけ書く。ノード ID の `a->b`。**点線や「受け手なし」の箱への線も含め、描くすべての辺**を書く（足りないと facts が ✗ になる）。SVG の辺は `data-edge` で arrows が見る。
- **差分にも根拠にも無いコンポーネントややりとりを描かない。** 分からない関係は描かずに、本文の「確かめていないこと」に書く。

#### 5-2. 道具を用意する

```sh
TOOLS=$(bash $S/scripts/setup.sh)   # 初回は npm と chromium を入れる。2 回目からは即座に返る。$W はこの下にある
```

#### 5-3. SVG → PNG の場合（既定）

- `cp $S/references/before-after.svg $W/<name>.svg` から始め、手順 4 の型で描く。
- 箱の `<g>` に `data-node="<id>"`、矢印の `<path>` に `data-edge="<from>-><to>"` を付ける（arrows の検査が効く）。
- `cd $W && node $EXPLAINER/scripts/figure-check.mjs $W/<name>.svg --facts $W/<name>.facts.json` で ✗ を 0 にし、出力された `.figure-check/<name>/<name>.sheet.png` と `<name>.edges.png` を **Read で開いて目で見る**。Before と After で同じ箱が同じ位置にあるか、色が変わる箱だけに付いているかも見る。最後の PNG だけで済ませず、この 2 枚も開く。
- PNG の図に限り、`tiny`（スマホ幅で文字が小さい）は残してよい（幅 1040 の画像をデスクトップで見る前提）。残したら報告に書く。ほかの ✗ は 0 にする。
- PNG にし、Read で開いて最後に見る：`(cd $TOOLS && node $S/scripts/svg2png.mjs $W/<name>.svg $W/<name>.png 1040)`

#### 5-4. Mermaid の場合（手順 4 の条件にすべて当たるときだけ）

```sh
# $W/<name>.mmd を書いてから。cd $W が要る：figure-check は今いるディレクトリに test-results/ と .vlmkit/ を書くので、リポジトリの中で実行しない
cd $W && node $EXPLAINER/scripts/figure-check.mjs $W/<name>.mmd --facts $W/<name>.facts.json --write
```

- `mermaid: rendered` が出れば構文は正しい。出なければ、表示されたエラーを直して再実行する。**構文の検査を通さずに PR に出さない。**
- Mermaid では、出たすべての ✗ を 0 にする。△ は落ちないが、辺のシートで目で見る。
- `tiny`（スマホ幅で文字が小さい）は、まず配置で直す：横に長い鎖を `flowchart TB` や subgraph の `direction TB` にし、Before と After の subgraph を `B ~~~ A`（見えない線）で縦に積む。
  **配置で消えないときは、ラベル（ポート番号・アドレスなど）を削って消さない。** ラベルを残し、`tiny` が残ったことを報告に書く（PR はデスクトップで読む前提）。
- `~~~` は配置のための線なので、facts の `edges` に書かない。arrows の辺のシートには 1 本として出るが、無視してよい。
- subgraph のタイトルを線が貫通する ✗ が消えないとき（subgraph の `direction` は、外への辺があると効かない）は、内側の subgraph をやめ、場所をノードのラベルに入れる（例：`worker (host B)`）。
- 出力された `.figure-check/<name>/<name>.sheet.png` と `<name>.edges.png` を **Read で開いて目で見る**。各矢印が「どこからどこへ」と読めるか、Before と After の違いが分かるか。
- GitHub の Mermaid は手元の mermaid より古いことがある。新しい構文（`@{ icon: … }`、`architecture-beta` など）は使わない。

上限は 5 ラウンド。それでも ✗ が残るなら、図を小さく（要素を減らして）するか、図をやめて文章にする。

### 6. 本文の型

見出しはリポジトリの PR テンプレート（`.github/pull_request_template.md`）があればそれに従う。無ければ次の順。

```
## 何をするか          1〜3 文。変更の目的と、マージ後に何ができるようになるか
## 変わるところ        図（あれば）と、変化の箇条。「前は X、後は Y」の形で
## この PR の差分      ファイル単位の要点。手順 2 の「構成の変化」と食い違わないこと
## 影響               他のリポジトリ・利用者・互換性・入れる順番。無ければ節ごと省く
## 確かめたこと・確かめていないこと
### 確かめたこと       実行したテストとコマンドと結果
### 確かめていないこと  実行できなかった検査（理由つき）など。下の箇条を参照
```

小見出しは `###` で書く。「確かめたこと:」のように末尾にコロンを付けたラベルにしない（yomiyasu の lint が trailing_colon として拾う）。

- **「何が在るか」ではなく「何が変わるか」を書く。** 変更後の構成だけを説明する文は、変更前と比べた形に直す。
- 手順 2 のメモに無い主張を書かない。テストの結果は実際の出力から書く。
- 「確かめていないこと」に入れるもの：実行できなかったテストや lint（理由つき）、**変更が狙った効果そのものを確かめていなければその効果**、GitHub での表示。
  テストの中身をコードを読んで説明したときは、実行していないと分かるように書く。
  リポジトリを変えない代わりの確認はしてよい。例：`git archive <head> | tar -x -C $W/tree` で書き出した木でテストを走らせる、`bash -n` で構文だけ見る。したら、何で代えたかと、それで確かめられないこと（例：shellcheck の警告が消えたこと）を書く。
  数分かかるテストは、バックグラウンドで走らせて結果を待つ。
  テストが skipped や INCOMPLETE を含んで終わったら、件数と理由をそのまま書く（「通った」とまとめない）。
- リポジトリのリリースやバージョンの規則（「この変更は次のリリースで patch を上げる」など）が当たるなら「影響」に書く。
- Mermaid は ```` ```mermaid ```` のコードブロックで本文に入れる。
- **Issue と PR の参照**は、PR を出すリポジトリのものだけ `#N` と書き、ほかのリポジトリのものは必ず `owner/repo#N` と書く。GitHub は `#N` を PR のリポジトリの番号として解決するので、別リポジトリの番号を `#N` と書くと、無関係な Issue にリンクされる。
  - `repo#N`（owner なし）は GitHub がリンクしないので使わない。
  - `https://github.com/<owner>/<repo>/(pull|issues)/N` の URL は貼らず、上の短い形に直す。
  - `Fixes` / `Closes` で閉じる Issue も同じ書き方にする（`Fixes owner/repo#N`）。
- リポジトリの規則（機密の値を本文に貼らない、署名・trailer の決まり）に従う。

### 7. 本文を検査する

本文が日本語なら、次の順に通す（日本語以外なら yomiyasu は使わず、2 の照合だけする）。

1. `explain-before-shorten`：最初の下書き `$W/pr-body.draft.md` を、論理と前提が抜けていないか整えて `$W/pr-body.ebs.md` に書く。直すところが無ければ、そのまま写して「変更なし」と記録する。
2. `yomiyasu`：`pr-body.ebs.md` を推敲して `$W/pr-body.md` に書く。explain-before-shorten が残した条件・用語・数値を削らない。yomiyasu の SKILL.md は長い（数百行）ので、Read を offset で分けて最後まで読む。途中で打ち切るなら、少なくとも「基本原則」「文書の立場と文末」と、検査コマンドの節（`yomiyasu_check.py` が出てくる節）は読み、どこまで読んだかを報告に書く。references/ は `doc-types/pr.md` だけでよく、ほかは候補の判断に迷ったときに引く。検査は次のとおり。
   ```sh
   python3 $YOMIYASU/scripts/yomiyasu_check.py run --source $W/pr-body.ebs.md --final $W/pr-body.md --doc-type pr --stance=説明 --fact-gaps
   python3 $YOMIYASU/scripts/yomiyasu_check.py verify --final $W/pr-body.md
   ```
   最初の `run` の前に、本文を一度通して読み、誤字や空白の崩れを直しておく。
   候補が出たら、yomiyasu の SKILL.md の基準で直すか残すかを決める。直したら `run` を**もう 1 回だけ**実行して `verify` に進む（yomiyasu の「直すのは 1 回まで」に合わせる）。
   それでも残る info の候補は、残す理由を報告に 1 行書けば残してよい。
   attribution の行など、手順 8 で末尾に足す定型の行は `verify` の後に足してよく、`run` をやり直さない。
3. 直した本文を手順 2 のメモと読み比べ、主張・数値・ファイル名・コマンドが変わっていないか確かめる。
4. Issue と PR の参照を検査する（本文の言語に関わらず）：
   ```sh
   python3 $S/scripts/ref-check.py $W/pr-body.md   # PR を出すリポジトリは git remote origin から取る。違うなら --repo OWNER/REPO
   ```
   ✗ を 0 にする。`✓ #N` は PR のリポジトリにある Issue / PR の題名を出すので、手順 2 のメモと照らして意図した相手かを確かめる（別リポジトリのつもりだったら `owner/repo#N` に直す）。
   `?`（gh から見えず未確認）が残ったら、その参照を報告に書く。△ は直してよいが残しても落ちない。
   Claude Code では同じ検査が PreToolUse hook（`claude/settings.json`）としても動き、`gh pr|issue create|edit|comment` の本文に ✗ があると実行を止める。止められたら、出力された ✗ を直してから実行し直す。hook は Codex・Copilot CLI では動かないので、この手順は省かない。

報告には、1 と 2 でそれぞれ何を直したか（または「変更なし」）を 1 行ずつ書く。

### 8. 出す

- push がまだなら、リポジトリの規則が求める確認を取ってから `git push -u origin <branch>`。
- 本文は `$W/pr-body.md` を `gh pr create --body-file`（手順 0 で PR が見つかったなら `gh pr edit <n> --body-file`）で渡す。セッションの指示が PR の末尾に付ける行（attribution など）を求めていれば、渡す前に足す。
- **PNG はリポジトリにコミットしない。** `docs/` に置いてコミットの SHA で参照すると、レビュー中に表示されない。`gh` の `--attach` で PR に直接アップロードする：
  1. 本文の図の位置に `![<図の要点>]($W/<name>.png)` と書く。alt には図の要点（何が何に変わるか）を 1 文で書く。
  2. `gh pr create --body-file $W/pr-body.md --attach $W/<name>.png`（既存の PR なら `gh pr edit <n> --body-file $W/pr-body.md --attach $W/<name>.png`）。図が複数なら `--attach` を図の数だけ繰り返す。gh が本文の参照をアップロード先の URL に書き換える。
  3. 本文の参照のパスは、`--attach` に渡すパスと一字一句同じに書く（片方だけ相対パスにしない）。違うと参照が書き換わらず、画像が本文の末尾に別に足される。
- 一部の添付が失敗しても PR は作成・更新され、gh は 0 以外で終わる。そのときは stderr を読み、失敗した PNG だけを `gh pr edit <n> --body-file $W/pr-body.md --attach …` でやり直す。
- `--attach` が無い古い gh（`gh pr create --help` に出ない）なら、gh を更新するよう利用者に頼む。

### 9. 表示を確かめる

- Mermaid：`gh pr view <n> --web` か、ブラウザで PR を開き、図が描画されている（エラーの表示が無い）ことを確かめる。ブラウザが無ければ、手順 5-4 の `mermaid: rendered` までを確かめたと報告する。
- PNG：`gh pr view <n> --json body -q .body` で、画像の参照にローカルのパスが残っておらず、`https://github.com/user-attachments/assets/…` に書き換わっていることを確かめる。private リポジトリでは、この URL を curl で取ると認証なしで 404、トークン付きでも画像ではなく HTML が返るので、curl では表示を確かめられない。ブラウザを操作できるなら、PR のページで画像が読み込まれていること（`naturalWidth` が 0 でない）も確かめる。できなければ、本文の URL までを確かめたと報告する。

## 報告

利用者への報告には次を書く。

- PR の URL
- 図を作ったか、作らなかったか。作ったなら種類（Mermaid / PNG）と、figure-check の結果（✗ の数、残した △ と tiny）
- 本文の検査（explain-before-shorten・yomiyasu）を通したか
- ref-check.py の結果（✗ の数と、未確認 `?` の参照）
- 確かめていないこと（表示を確認できなかった、テストを実行できなかった、など）

## やってはいけないこと

- 差分にも根拠にも無いコンポーネントや通信を図に描く。
- 構文の検査を通していない Mermaid を PR に出す。
- PNG を `docs/` などに置いてコミットする。
- 小さな変更に図を付ける。
- 実行していないテストを「確かめた」に書く。
- 別リポジトリの Issue / PR を `#N` や `repo#N` で書く。
