# rm 転送先の macos-trash への切り替え Implementation Plan

要件と判断理由の正本は [dig log](../dig/2026-10-17-macos-trash.md)。この計画では、実装に必要な契約・手順・検証だけをまとめる。

## Requirements

- Safehouse 内（`APP_SANDBOX_CONTAINER_ID=agent-safehouse`）で名前解決された rm を、gtrash ではなく macos-trash 経由で Finder のゴミ箱 `~/.Trash` へ移す。Safehouse 外では従来どおり、引数をそのまま `/bin/rm` へ exec する。
- Safehouse から `~/.Trash/.DS_Store` に限って内容の読み書きを許可し、Finder の「戻す」を使えるようにする。`~/.Trash` 配下のその他の内容の読み取り・書き換え・削除の拒否と、`/bin/rm` の実行拒否は維持する。
- gtrash 関連を削除する。対象は Brewfile の gtrash、`local-overrides.sb` の XDG 形式ごみ箱の保護ルール、`check_gtrash_runtime.py`、文書の gtrash 手順。
- 対象外: Safehouse 外の rm、`/bin/unlink` など rm 以外の削除手段、外部ボリュームのゴミ箱、リポジトリ全体のテスト方針。macos-trash 用の実機検証スクリプトは作らない。

### ラッパーの契約（Safehouse 内）

- オプションは先頭から、`--` か最初の非オプションまでを解釈する。`-` 単独とそれ以降の引数は対象として扱う。
- 受け付ける文字は `d` `f` `P` `R` `r` `v` `x`。`P`・`v`・`x` は効果なしとし、`-v` も何も表示しない。
- `i`・`I`・`W`、その他の文字、`--force` のような長いオプションはエラーにする。何も移さず、終了コード 1。
- 対象がない場合は、`-f` があれば何もせず 0、なければ使い方を stderr に出して 1。
- 各対象は次の順に判定する。移さない対象は stderr に `rm:` で始まる診断を出して最終的な終了コードを 1 にする。ただし `-f` で飛ばす存在しない対象は、診断も終了コードへの反映もしない。

| 対象 | 結果 |
|---|---|
| `/` や `//` のようにスラッシュだけ | 常にエラー |
| 末尾のスラッシュを除いた最後の要素が `.` か `..` | 常にエラー。`./`、`dir/..` も含む |
| 空文字、存在しない対象 | `-f` なら黙って飛ばす。なければエラー。壊れた symlink は存在する対象として扱う |
| symlink ではないディレクトリ | `-r` か `-R` があれば移す。`-d` だけなら空の場合だけ移す。それ以外はエラー |
| それ以外のファイルと symlink | 移す。ディレクトリを指す symlink もリンクとして移す |

- 移す対象は、`/opt/homebrew/opt/macos-trash/bin/trash -- <対象...>` として 1 回だけ渡す。ハイフンで始まる対象には `./` を付ける。移す対象がなければ macos-trash を呼ばない。
- 拒否した対象があっても、残りの対象は移す。macos-trash が非 0 で終わるか、拒否が 1 つでもあれば最終的に 1 で終わる。
- macos-trash が見つからない場合も、`/bin/rm` や PATH 上の別の実行ファイルへ fallback しない。

## Implementation Decisions

- 実装は Worktrunk の worktree で行い、テストとレビューを通してから master へ取り込む。`~/dotfiles/config/` は HOME へ直接リンクされているため、`~/dotfiles` 上の編集は、実行中のすべての Safehouse の rm と次回起動の policy に即座に反映される。
- 取り込み前に `/opt/homebrew/opt/macos-trash/bin/trash` が実行可能か確かめる。未導入なら取り込まず、ユーザーに導入を依頼する。未導入のまま取り込むと、Safehouse 内の rm が失敗する。
- 空文字は、rm と同じく存在しない対象として扱う。rm でも `lstat` が ENOENT になり、`-f` では黙って飛ばされるため。
- macos-trash は 1 回の呼び出しで全対象を受け取る。複数対象の「戻す」記録の補完が、1 回の呼び出しの中で行われるため。
- policy は、既存の deny の後に `(home-literal "/.Trash/.DS_Store")` への `file-read-data` と `file-write-data` の allow を追加する。後に書いた規則が優先される。`.DS_Store` の作成は現行 policy でも拒否されていない。
- テストは、ラッパー本文の絶対パスを偽の実行ファイルへ置き換える既存の方式を引き継ぐ。偽の macos-trash は引数を記録するだけで、本物のゴミ箱に触れない。

## Tasks

review 用の base commit: `23a232a`。

- [x] ラッパーと単体テスト: `config/.local/bin/rm` を上記の契約で書き換え、`scripts/tests/test_rm_trash.py` を偽の macos-trash 前提に書き換える。`scripts/tests/test_agent_runtime.py` の rm 解決テストは、偽の実行ファイルの差し替え先と期待する引数だけを直す。
  - 既存のテストは、ディスク上に存在しない対象を `-f` 付きで渡し、偽の実行ファイルの終了コード 23 がそのまま返ることを確かめている。新しい契約では、`-f` の存在しない対象は macos-trash を呼ぶ前に飛ばされ、失敗時の終了コードは 1 になる。macos-trash へ届く引数を確かめるテストは、対象を先に作ってから実行し、終了コードは 1 を期待する。`test_agent_runtime.py` も同様に直す。
  - `test_rm_trash.py` で押さえる境界: `--` の付与、ハイフンで始まる対象と `--` という名前の対象、拒否する対象と残りの処理継続、`-f` の有無での空文字と存在しない対象、対象なし、拒否するオプション、ディレクトリと `-r`・`-R`・`-d`、ディレクトリを指す symlink、macos-trash の失敗、macos-trash 欠落時に元が残り PATH 上の偽物を使わないこと、Safehouse 外での `/bin/rm` への引数保持、fish と子シェルからの解決。
  - 結果: `test_rm_trash.py` 11 件、`test_agent_runtime.py` 24 件が成功。`sh -n` も成功。
- [x] Safehouse の設定と検証スクリプト: `config/.config/agent-safehouse/local-overrides.sb` から XDG 形式の正規表現の行を削除し、`.DS_Store` の allow を追加し、gtrash に触れたコメントを macos-trash に直す。`scripts/tests/check_safehouse_runtime.py` からは XDG 形式のごみ箱の項目だけを除く。`.Trash/private.txt` の拒否、`/bin/rm` の実行拒否、そのほかの項目は残し、新しい確認項目は足さない。`scripts/tests/check_gtrash_runtime.py` は削除する。
  - 結果: `check_safehouse_runtime.py` の `py_compile` が成功。実行は Safehouse 外が必要なため、適用手順 3 でユーザーが行う。
- [x] Brewfile: `brew/Brewfile.default` から gtrash を削除し、macos-trash をアルファベット順の位置に追加する。
  - 結果: `brew bundle list` に macos-trash が含まれ、gtrash は含まれない。
- [x] 文書: `docs/troubleshooting.md` の「削除したファイルを復元する」を、Finder の「戻す」の手順に書き換える。
  - 含める内容は 5 点。Safehouse 内の rm は Finder のゴミ箱へ移す。通常端末の rm は直接削除で戻せない。通常端末でゴミ箱を使う場合は macOS 標準の `trash` を使い、複数を一度に渡すと一部の「戻す」が欠けることがある。「戻す」が出ない項目は元の場所へ手で移す。外部ボリューム上のファイルは移動に失敗して元が残る。
  - `docs/dig/2026-10-02-safehouse-compatibility.md` の gtrash に触れる節の冒頭に、[2026-10-17 の dig log](../dig/2026-10-17-macos-trash.md) で macos-trash へ置き換えたことを追記する。
  - 結果: `git diff --check` 成功。gtrash の参照は dig log と計画以外に残っていない。

## 適用手順

実装者は master への取り込み後、以下をユーザーに案内する。どれも Safehouse 外の通常端末で行う操作で、実装者は実行しない。

1. 取り込み前に macos-trash を導入する。

   ```fish
   brew install macos-trash
   ```

2. 取り込み後、Safehouse で動いているエージェントをすべて終了する。Hermes は稼働中のサービスだけを止める。

   ```fish
   hermes-gateway stop
   hermes-dashboard stop
   ```

3. policy を検証し、gtrash とその保存先、調査時の検証用項目を削除する。gtrash の保存先は中身を確認せずフォルダごと消してよいと合意済み。

   ```fish
   cd ~/dotfiles
   uv run --no-project python scripts/tests/check_safehouse_runtime.py
   brew uninstall gtrash
   rm -rf ~/.local/share/Trash
   rm -f ~/.Trash/.DS_Store
   rm -rf ~/.Trash/claude-trash-probe-* ~/.Trash/fake-home-probe.txt
   ```

   検証用項目をすでに消している場合、fish は一致しない glob を含む最後の行をエラーで飛ばす。そのエラーは無視してよい。`.DS_Store` の削除は別の行にしてあるので影響しない。

4. 止めた Hermes のサービスだけを `start` で再開し、エージェントを起動し直す。
5. 「戻す」を確かめる。

   ```fish
   echo test > ~/put-back-check.txt
   safe rm ~/put-back-check.txt
   stat -f %z ~/.Trash/.DS_Store
   ```

   サイズが 0 より大きく、Finder のゴミ箱で `put-back-check.txt` を右クリックして「戻す」が出れば完了。サイズが 0 なら、標準 API が `.DS_Store` 以外にも書き込みを必要としている。Safehouse の設定の追加変更を別途検討する。

## Final Validation

- [ ] ラッパーの契約: `uv run --no-project python scripts/tests/test_rm_trash.py` → 全テスト OK
- [ ] 起動経路からの rm 解決: `uv run --no-project python scripts/tests/test_agent_runtime.py` → 全テスト OK
- [ ] 構文: `sh -n config/.local/bin/rm` と `uv run --no-project python -m py_compile scripts/tests/check_safehouse_runtime.py` → エラーなし
- [ ] Brewfile: `brew bundle list --file=brew/Brewfile.default` → macos-trash を含み、gtrash を含まない。Safehouse 内で brew が動かない場合は、Brewfile の差分 2 行を目視で確かめる。
- [ ] gtrash の残存: `git grep -n gtrash -- . ':!docs/dig' ':!docs/plans'` → 該当なし
- [ ] 差分: `git diff --check` → 出力なし
- [ ] policy: 適用手順 3 の `check_safehouse_runtime.py` → `SAFEHOUSE_RUNTIME_PASS`。Safehouse 内では実行できないため、ユーザーが取り込み後に行う。
- [ ] 「戻す」: 適用手順 5 → `.DS_Store` が 0 バイトより大きく、Finder で「戻す」が出る。ユーザーが行う。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
