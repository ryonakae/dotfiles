# Autonomous Skill Curator

> v0.12.0 「The Curator Release」で導入。

## 概要

Hermes が自身のスキルライブラリを自動メンテナンスする機能。`hermes curator` が gateway の cron ticker 上でバックグラウンド実行され、デフォルト 7 日サイクルでスキルを採点・統合・剪定する。

`logs/curator/run.json` と `REPORT.md` に結果を出力。bundled / hub スキルは保護される（v0.16.0 で built-in も prune 可能に）。

## CLI

```bash
hermes curator              # background 実行（cron ticker）
hermes curator run          # 同期実行（結果即時、v0.13.0）
hermes curator status       # usage 順ランク表示（most-used / least-used）
hermes curator archive      # アーカイブ
hermes curator prune        # bundled/hub 以外を剪定
hermes curator list-archived
```

## 設定

```yaml
curator:
  enabled: true
  cycle_days: 7
  protect_bundled: true
  protect_built_in: true       # v0.16.0、false で built-in も prune 可

auxiliary:
  curator:                     # 統一管理（v0.12.0）
    provider: ""
    model: ""
    timeout: 600
```

## 自己改善ループ（background review fork）

v0.12.0 で大幅強化:

- **class-first（ルーブリック式）採点**
- **active-update バイアス**
- **`references/` / `templates/` サブファイル対応**
- **parent の live runtime（provider/model/credentials）継承**

## 動作

1. すべてのスキルを usage（呼出回数 / 直近利用 / outcome score）でスコアリング
2. 似たスキルは統合提案を生成
3. 採点が低くかつ bundled でないスキルは剪定対象
4. 結果を `~/.hermes/logs/curator/REPORT.md` に記録

## 注意事項

- 自動 prune を信頼しない場合は `protect_built_in: true` と `cycle_days: 0` で停止し、`hermes curator status` を手動確認
- bundled スキルは v0.16.0 で大幅軽量化（spotify, linear, kanban-codex-lane など削除、niche スキルは optional 降格）
