# 外部スキルの Source registry 移行 Implementation Plan

## Requirements

ユーザー承認済み。root Flake の外部スキル input を Source registry へ移し、標準の探索・選択機能で設定を簡素化する。現在の13取得元・14外部スキルの revision と内容を維持し、更新は移行と分ける。共通・Claude 各12自作 live link、Claude 専用同名優先、隠しディレクトリ除外、Antigravity CLI の共通参照、管理外の兄弟項目を保持する。標準 HM link の通常の置換動作は変更しない。

背景は [既存の移行計画](../2026-10-03-nix-migration.md) T5a と [dig log](../../dig/2026-10-03-nix-migration.md)。今回の合意は、以前の「root lock に統一し registry を使わない」選択を置き換える。設定本文の live link 方針は維持する。

## Implementation Decisions

- 固定済み agent-skills-nix の `sourcesFromLock` / `mkSourceLockProgram` を利用し、ライブラリや無関係な Flake input は更新しない。子 Flake や独自更新スクリプトは追加しない。
- `config/nix/skill-sources/` に取得元ごとの宣言、`config/nix/skill-sources.lock.json` に標準 schema の lock を置く。初回 lock は既存の固定 revision から移し、追跡するブランチは取得元で確認する。hash 表現・取得方式の差は内容比較で確認する。
- `flake.nix` から13件の `skills-*` input を除き、標準更新 app `skills-sources-lock` を公開する。root から実行すると上記 registry / lock を使う。外部スキルの一括更新はこの app、システムと管理ライブラリの更新は既存 `dotfiles.sh update` とする。旧 input 名の互換経路は追加しない。
- 探索範囲と標準の名前選択で14件だけを採用する。無制限の `enableAll` で更新時に新しいスキルを自動追加しない。独自の重複した一覧や factory を作らず、同名優先・target 制御に必要な明示設定のみ残す。
- Nix 定義と lock の移行なので、恒久的な移行証明テストや新しいテスト基盤は追加せず、構文・評価・生成物比較・標準 build で検証する。

## Tasks

Review base: `cd40ce8fdfc20bb854a516b2322cad1f2573f0b7`。開始時の未 push 4コミットは同じ会話で作成した承認済み成果物であり、今回完了時の push に含める。Claude / Pi fast-mode / Zed の設定3件は他者差分として保持する。

- [x] 取得・選択・更新入口: `flake.nix` / `flake.lock` / `config/nix/home/skills.nix` と registry を変更し、標準 API で同じスキル集合を生成する。
- [x] 運用文書: `README.md` / `AGENTS.md` / `docs/setup.md` と旧移行計画の現行方針を更新し、registry 追加 → lock 更新 → build → switch を案内する。単体更新・`update all` の範囲が変わることを明示する。

実装記録: `sourcesFromLock` と `skills.enable` を使用し、自作と同名の場合だけ catalog から target 制御の明示設定を作る。manifest の探索範囲を限定し、未選択の同名スキルによる catalog 衝突も避ける。13取得元の default branch は GitHub repository API で確認（context7 / herdr は master、他は main）。初回 lock は旧 revision / SRI hash を保持して標準 schema-v1 / npins-v8 へ変換した。

## Final Validation

- [x] 13取得元の revision が移行前と一致し、残る Flake input の版・接続が不変。選択は従来の14件のみ。
- [x] Nix formatter、lock JSON、`git diff --check`、変更した文書のローカル参照が成功。
- [x] `bash scripts/dotfiles.sh build --host /tmp/dotfiles-machine.SyCOAn6p` が成功。新規 Git ソースは対象を明示して追加し、秘密を取り込まない。Safehouse の拒否を回避せず、許可済み通常 Herdr ペインを使う。
- [x] 生成物の共通・Claude 各14外部スキルの全ファイル内容が適用済み世代と一致。各12自作 live link・Antigravity 参照先、同名優先と隠し項目除外を維持。
- [x] 更新 app の help と一時 registry / lock を使う限定試行で標準更新処理が動くことを確認し、本番の14スキルは更新しない。
- [x] 独立 read-only レビューを実施し、blocking/high・decision required が残らない。
- [x] 生成物が既存と異なれば通常の switch と適用後の参照・管理外項目保持を確認。同一なら不要な再適用はしない。Zoom は既存のローカル skip 設定を維持する。

検証記録: 固定 build は終了コード0（`/tmp/dotfiles-registry-build.log`）。system は `/nix/store/l6vmarcxhmjhif7wv6000y7x19ssz8bv-darwin-system-26.11.4cff07d`、HM は `/nix/store/ak8ncdbr3g5sp7pblnwn8ayk6znnj9jf-home-manager-generation`。移行前 HM と各14外部の全ファイル hash・実行属性・symlink、各12自作参照、Antigravity 参照が一致。残る Flake node / edge は不変。限定一時 fixture で共通自作優先・Claude 専用優先・hidden 除外と標準 selectSkills の14件選択を確認した。更新 app の help と一時 stop-slop registry の実更新は終了コード0で、本番 lock は変更なし。Nix format、差分検査、文書参照33件の存在確認が成功。標準更新は本番全13取得元の最新版更新としては実行していない。新 system は通常の switch で適用し、終了コード0を確認した。実機の共通・Claude 各14外部 / 12自作と Antigravity の参照先が生成物と一致。管理外3項目（Claude `synced` を含む）の inode / mode / mtime / link metadata は適用前後で不変。Homebrew は Zoom の skip を表示し、83依存の処理を完了した。

## Gate Summary

実装コミット `8e7e8ef`、独立レビュー範囲 `cd40ce8..8e7e8ef`。指摘なしで correction cycle は不要。レビューはリポジトリ内の差分と lock に限定し、外部 API・store・実機の確認は実装側で行った。未解決の blocking/high・decision required・medium/low はない。実装後にコード変更はなく、有効な検証結果を再利用した。各スキルの機能実行や本番全取得元の最新版更新は今回の検証範囲に含めない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、この計画だけを同名のまま `docs/plans/archived/` へ移す。既存の大きな移行計画は未完了項目があるため移動しない。
