# Hermes の変更時だけ停止を要求する Implementation Plan

## Requirements

[dig log](../dig/2026-10-13-hermes-conditional-activation.md) と、その後の「起動定義の比較に集約し、シンプルにする」方針への承認に基づく。dig log の Q1 は、以下の合意で解決する。

- 実配置と候補の gateway / dashboard 起動定義が同じなら、Hermes の停止確認も plist の再配置もしない。
- 起動定義が異なる、または初回配置なら、既存の停止確認を通してから配置する。本体・wrapper の変更は、起動定義内の Nix store パスの変更で検出する。
- 読み取り失敗や未知の配置・手動変更・symlink の衝突はエラーで止める。既存の所有確認を弱めない。
- 独自の履歴・状態ファイル、自動停止・再起動、rollback、汎用的な差分管理は追加しない。
- 今回の対象は実装・テスト・ビルド。実サービスの停止や実機適用は行わない。

## Implementation Decisions

- `nix/home/hermes.nix` の生成済み plist を比較対象の正本にする。既存の `hermes-launch-agents` と Home Manager の旧世代参照を利用し、比較用 manifest は作らない。
- `switch` の適用前チェックと Home Manager の配置前チェックは、同じ生成チェックを呼ぶ。変更時だけ既存の `check-stopped.sh` に進むため、変更なしの経路では GUI セッションや稼働プロセスの検査を行わない。
- 配置時は同一の plist を書き直さない。比較コマンドの「内容不一致」と「読み取りエラー」を区別する。
- plist の PATH に含まれる Home Manager パッケージ環境が変わる場合も起動定義の変更として扱う。PATH の再設計はしない。
- 旧ビルド成果物のメタデータを不用意に壊さず、適用入口の変更は必要最小限にする。

## Tasks

レビュー base: `bda85de9fae5f11216319a6d5cfd231e878bf526`。同一セッションのパスワード要求設定は独立コミット `8b1b4f9` に分離した。

- [x] 条件付きチェックと配置: `nix/home/hermes.nix`、必要に応じて `config/.config/hermes/`、`nix/darwin/default.nix`、`scripts/dotfiles.py` の関連箇所を変更する。
  - 共通チェックで判定を一か所に保ち、既存の停止チェック・所有確認を再利用する。
- [x] 回帰テストと手順: `scripts/tests/test_dotfiles_cli.py` と必要最小限の Hermes 配置テスト、`docs/usage.md`、スキルの関連運用条件を更新する。
  - テスト境界は既存 switch と生成された Home Manager activation。実 HOME やサービスを変更せず、仮の配置先と停止チェックを使う。
  - 他作業の変更がある `docs/apps.md`、`scripts/tests/test_agent_runtime.py`、gateway 管理関数には重ねて編集しない。必要になった場合は変更の所有者を確認する。
  - 同じセッションのパスワード即時要求設定とテストは維持する。
  - `scripts/tests/test_hermes_activation.py` を新設し、生成されたチェックと activation を一時 HOME で検証。既存の他作業テストは変更していない。
  - focused validation: 配置テスト7件と CLI テスト64件、計71件成功・skipなし。独立レビューと全体ビルドは未完了。

## Final Validation

- [ ] 変更なし: 稼働中を表す停止チェックでも適用前チェックが通り、配置済み plist の内容・更新時刻が変わらない。
- [ ] 変更あり・初回配置: 停止チェックが呼ばれ、失敗時に配置しない。停止済みなら必要な plist だけ配置する。本体または wrapper の参照変更も検出する。
- [ ] 不正配置・読み取り失敗: 変更なしと誤判定せずエラーになる。既存の所有・symlink・手動変更保護が維持される。
- [ ] 関連テストを失敗から成功へ進め、`uv run --no-project python -m unittest scripts.tests.test_dotfiles_cli` と配置テストを実行する。実 Nix 不在による skip は成功扱いしない。
- [ ] `bash scripts/dotfiles.sh build --configuration private` を実行し、生成したチェック・activation の構文と参照先を確認する。実際の switch は実行しない。
- [ ] `git diff --check` と差分確認で対象外変更の混入がないことを確認する。新規 Nix 参照ファイルはパスを明示して Git 追跡対象にし、未追跡の秘密をビルドに取り込まない。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
