# 既存環境を移行・復旧する

[README](../README.md) / 既存環境の移行

Nix / Home Manager / nix-homebrew 管理から Brewfile と mise へ切り替える Mac 用。新規 Mac は[初回セットアップ](setup.md)、移行済み環境の更新は[日常操作](usage.md)を使う。

既存の Nix 管理 Homebrew を検出すると通常 setup は止まる。通常 setup に所有解除・サービス切替・Nix 撤去は含まれない。移行は対象 Mac の実状態を照合し、各段階の適用・権限変更・削除の直前に対象を確認して承認する。別 Mac の操作や秘密の収集は含めない。

## 1. 現在の所有と復旧先を確認する

1. Git 差分と候補の宣言・関連検証結果を確認する。他者の変更を保持する。
2. 対象の system / Home Manager 世代、管理リンク、Hermes plist、稼働サービス、Homebrew 本体リンク・marker・shell 登録、Nix の daemon / APFS volume を記録する。
3. 既存バックアップの復元先に衝突がないか確認する。秘密・認証・DB・memory・session・管理外の兄弟は移動・削除しない。
4. 旧構成・所有解除前世代は、撤去前まで参照できるよう保持する。GC は行わない。

関係のないアプリの全件棚卸しや、HOME 全量の退避は不要。保全するのは変更・衝突する対象だけ。

## 2. Nix が動く間に代替と所有解除を準備する

必要な Homebrew パッケージ、mise runtime、選択済み外部リポジトリを対象限定で準備する。取得元が存在してから、配置に使うルートと構成別 mise 宣言を確認して trust する。

**旧所有を解除する前に、実 HOME の配置 dry-run を60秒の制限付きで完了確認する。** 家用の例：

```fish
/usr/bin/python3 -c 'import os, subprocess; subprocess.run(["/opt/homebrew/bin/mise", "-C", os.path.expanduser("~/dotfiles"), "-E", "default,private", "dot", "apply", "--dry-run"], timeout=60, check=True)'
```

この時点では apply しない。既知の旧 Home Manager リンクによる衝突以外の問題、未知の実体、timeout があれば所有解除を開始しない。dry-run 成功は後続の成功を保証しない。

### 一時 Home Manager 成果物を準備する

所有解除用の一時構成は [nix/release-home-manager.nix](../nix/release-home-manager.nix)。現行 lock を更新せず、標準 Home Manager の空の管理集合をビルドする。

```fish
cd ~/dotfiles
nix build .#release-home-manager --no-update-lock-file --no-link --json
```

JSON の `outputs.out` を控える。成果物の対象ユーザー・HOME と実機の旧世代を照合し、`home-files` に所有リンクがなく、activation がサービス操作やアプリのコピーを追加しないことを確認する。ビルド成功だけでは実機の所有は解除されない。

一時構成は通常 setup に組み込まず、最終 Nix 撤去時に削除する。

## 3. 所有リンクと Hermes 定義を引き渡す

1. アプリを新規起動しない切替時間を確保する。必要な Hermes 操作は[管理関数](apps.md#hermes-を停止更新する)で別承認のもと実行する。停止中だったサービスを起動しない。
2. 引渡し対象と保全先を確認し、承認後に対象ユーザーの通常端末で一時 Home Manager 成果物を activate する。

```fish
/nix/store/確認済みの-home-manager-generation/activate --driver-version 1
```

上のパスは手順2の `outputs.out` に置き換える。未知の store 成果物や、別 Mac の成果物をそのまま使わない。

3. 終了コードと所有解除済み範囲を確認する。HM の無効化だけでリンクが消えると仮定せず、残ったリンクの由来を確認する。
4. [mise の直接リンク](usage.md#設定ファイルを変更する)を配置する。切替中に新たな実体ができた場合も force で上書きしない。
5. Hermes plist は旧管理結果と実配置の一致を確認して、別途ユーザー所有の通常ファイルへ引き渡す。symlink や手動変更を自動上書きしない。通常配置スクリプトの衝突保護を迂回しない。
6. 旧 Herdr hook の解除後、必要なら[標準 integration](apps.md#claude-code)を入れる。settings の既存差分を保持する。

失敗時は変更済み範囲を確認して止める。旧構成の無条件再適用や自動 rollback は行わない。

## 4. Homebrew を引き継ぐ場合

nix-homebrew は Homebrew 本体を Nix store のリンクへ置き換え、marker と fake repository も作る。Cellar / Caskroom / Taps とアプリ・データは保持し、Homebrew 全体の uninstaller は使わない。

1. 使用する公式 installer の revision と処理内容を確認する。
2. 既知の Nix 管理本体リンク・marker・fake repository だけを対象限定で保全・解除する。未知の通常ファイルは上書きしない。
3. 別承認のうえで既存 prefix に標準 Homebrew 本体を導入する。Cellar / Caskroom / Taps を保持する。
4. `brew --version` と `brew --prefix`、本体のリンク先を確認し、Nix store 参照が外れたことを確認する。

この順序は HM 引渡し activation と調整する。標準本体導入後に旧 homebrew-enabled activation を実行しない。公式手順で保全した移行が成立しない場合は、実操作前に相談する。実機対象と installer を確認する前に、削除コマンドを組み立てない。

## 5. 非 Nix の起動を確認する

[Homebrew fish の登録・選択](setup.md#6-fish-に切り替える)を別承認で行い、新規 login 端末で PATH・runtime・plugin・選択スキルの読み込みを確認する。既存の Cua 用 PATH 追加など、関係のない設定は保持する。

Hermes は launcher、CLI、配置済み plist の Program / PATH を確認する。稼働サービスがある場合だけ、承認下で管理関数から明示的に切り替え、登録済み実行先と実プロセスが旧 store を使っていないことを確認する。CLI の PATH 確認だけで完了扱いしない。未稼働のサービスは検証目的で起動しない。

Hermes の追加依存の完全一致や全機能確認は移行の前提にしない。問題があれば個別に対応する。

## 6. nix-darwin と Nix 本体を撤去する

非 Nix の受入後、nix-darwin と Nix 本体を別工程で撤去する。対象の標準 uninstaller の内容と実機状態を再確認し、工程ごとに承認を得る。

nix-darwin の標準 uninstaller は空構成 activation を行うが、HM の所有リンクや Hermes plist を解除するものではない。system サービス、`/etc/static`、shell に作用し、`/etc/**/*.before-nix-darwin` を元の名前へ戻す。Nix daemon が installer 版へ復帰する場合もある。

- `/etc` の復元候補が新しい shell 設定などを上書きする場合は、実行前に解決する。古いバックアップを一括復元しない。
- nix-darwin 撤去後は、終了コードだけでなく shell・サービス・Homebrew・設定が保持されていることを確認する。
- Nix 本体は installer 種別、daemon、build users、profile、実 APFS volume を照合し、[上流 macOS 撤去手順](https://nix.dev/manual/nix/latest/installation/uninstall.html)で対象を示して再承認する。volume の識別子を推測しない。
- 旧 Nix を使うプロセスが残る場合は削除を止める。空の `/nix` mountpoint が再起動まで残ること自体は失敗ではない。

[nix-darwin の標準撤去手順](https://github.com/nix-darwin/nix-darwin#uninstalling)も使用時点で確認する。実機切替・撤去はまだ完了していないため、移行に必要な Nix ファイルは当面残す。撤去完了後に一時構成を含む旧宣言を整理し、恒久的な dual mode は残さない。

## 以前の状態へ戻す場合

所有の引渡しと、本文・アプリ・状態の復旧を分ける。Nix 世代だけでは全状態は戻らない。

| 対象 | 確認すること |
|---|---|
| mise と Home Manager のリンク | 同じ宛先を旧世代へ渡す前に、対象を標準 unapply で解除する |
| Git 正本の本文 | 後続の変更を失わないよう差分を確認する |
| Homebrew アプリ・mise runtime | 対象ごとに必要な版・導入状態を確認する |
| macOS preferences | 変更前の値・型・未設定状態に戻す。未設定なら対象キーの削除が必要 |
| DB・Docker volume・認証 | 個別の整合したバックアップから復元する |

再起動・ログアウトは作業を保存してから行う。未知のリンクの一括退避、バックアップへの上書き、自動 rollback は行わない。
