# 既存環境を移行・復旧する

[README](../README.md) / 既存環境の移行

Nix / Home Manager / nix-homebrew 管理が残る Mac を Brewfile と mise へ切り替える場合の確認事項。新規 Mac は[初回セットアップ](setup.md)、導入済み環境の更新は[日常操作](usage.md)を使う。

通常 setup に所有解除・サービス切替・Nix 撤去は含まれない。対象 Mac の実状態と管理元を確認し、専用の移行手順を決めてから進める。適用・権限変更・削除は、各工程の直前に対象を確認して承認する。

## 所有リンクを引き渡す

1. Git 差分、現在の管理リンク、Home Manager 世代、Hermes plist と稼働サービスを確認する。他者の変更を保持する。
2. 必要な Homebrew パッケージ、mise runtime、選択済み外部リポジトリを準備する。Hermes は別承認で[初回導入 task](apps.md#初回設定と起動)を使い、準備中は既存のリンク・plist・サービスを変更しない。
3. [設定配置の dry-run](troubleshooting.md#設定配置だけ再開する)を実 HOME で60秒の制限付きで行う。既知の Home Manager リンクの衝突以外の問題、未知の実体、timeout があれば所有解除を始めない。
4. 対象 Mac の管理構成に合わせて所有解除方法を確認する。対象ユーザー・HOME・解除されるリンク・サービスへの作用を照合し、別承認で実行する。Home Manager の無効化だけでリンクが消えると仮定しない。
5. 終了コードと解除済み範囲を確認してから、[mise の直接リンク](usage.md#設定ファイルを変更する)を配置する。切替中に新たな実体ができた場合も force で上書きしない。

保全するのは変更・衝突する対象だけ。秘密・認証・DB・memory・session・管理外の兄弟を移動・削除せず、既存バックアップを上書きしない。所有解除前の構成と世代は、切替確認まで参照可能に保つ。

Hermes plist は管理元の生成結果と実配置を照合してから、ユーザー所有の通常ファイルへ引き渡す。[配置処理](apps.md#初回設定と起動)の衝突保護を迂回しない。必要なサービス操作は[管理関数](apps.md#hermes-を停止更新する)で行い、停止中だったサービスは起動しない。Herdr hook も二重登録せず、既存所有の解除後に[標準 integration](apps.md#claude-code)を使う。

## Homebrew を引き継ぐ場合

Cellar / Caskroom / Taps とアプリ・データを保持し、Homebrew 全体の uninstaller は使わない。

- 本体リンク・管理 marker・fake repository の由来と、使用する公式 installer の revision・処理内容を確認する。
- 既知の管理対象だけを保全・解除し、別承認で既存 prefix に標準 Homebrew 本体を導入する。未知の通常ファイルは上書きしない。
- `brew --version`、`brew --prefix`、本体の参照先を確認する。標準本体へ引き渡した後は、それを置き換える Nix の activation を実行しない。

## 起動確認と Nix 撤去

新しい login 端末で Homebrew / mise の解決先、runtime、plugin、選択スキルを確認する。Hermes は launcher・CLI と、稼働中サービスの登録済み Program / PATH・実プロセスを確認する。CLI の PATH だけで完了扱いにせず、未稼働サービスは検証のために起動しない。

nix-darwin と Nix 本体の撤去は別工程にする。使用時点の[nix-darwin 標準撤去手順](https://github.com/nix-darwin/nix-darwin#uninstalling)と[Nix の macOS 撤去手順](https://nix.dev/manual/nix/latest/installation/uninstall.html)を確認し、対象 Mac に合った操作を別途承認する。

- nix-darwin の `/etc` 復元候補・shell・system サービスへの作用を確認する。`/etc/shells` が Nix 管理リンクなら直接追記せず、通常ファイルへの復元後に[Homebrew fish の登録・選択](setup.md#6-fish-に切り替える)を行う。
- Nix 本体は installer 種別、daemon、build users、profile、実 APFS volume を照合する。volume 識別子を推測せず、既存 shell 設定を古いバックアップで一括上書きしない。
- store 利用プロセスが残る場合は削除を止める。プロセス名や PATH だけで判断せず、volume の実利用も確認する。古い shell の終了は作業を保存してから行う。
- 各工程の後に shell・Homebrew・mise・設定・稼働サービスが保持されていることを確認する。未稼働サービスはそのまま保持する。

失敗時は終了コード、変更済み範囲、成功済み工程を確認して止める。自動再試行・rollback や、成功済み工程の無条件再実行は行わない。

## 以前の状態へ戻す場合

構成の適用だけで、本文・アプリ・データまで元に戻るわけではない。対象ごとに復旧する。

| 対象 | 確認すること |
|---|---|
| 管理リンク | 管理元を変える前に、現在の所有を標準 unapply などで解除する |
| Git 正本の本文 | 後続の変更を失わないよう差分を確認する |
| Homebrew アプリ・mise runtime | 対象ごとに必要な版・導入状態を確認する |
| macOS preferences | 変更前の値・型・未設定状態に戻す。未設定なら対象キーの削除が必要 |
| DB・Docker volume・認証 | 個別の整合したバックアップから復元する |

再起動・ログアウトは作業を保存してから行う。未知のリンクの一括退避、バックアップへの上書き、自動 rollback は行わない。
