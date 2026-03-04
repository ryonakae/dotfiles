# Pencil Design and Develop スキル

このスキルは、AIコーディングエージェントが Pencil の `.pen` ファイルを、用途に応じた実行モードで扱うためのものです。

## 主なユースケース

1. Pencil 上で画面・コンポーネントを設計/編集する。
2. Pencil のデザインファイルを読み取り、フロントエンド実装を行う。

## 追加で対応するモード

1. コード側の変更を Pencil デザインへ同期する。
2. Pencil MCP 接続や実行時トラブルを切り分ける。

## 実行方針

1. デフォルトは 1 依頼につき 1 モード実行。
2. 複数モード連続実行は、ユーザーが明示した場合のみ実行。
3. `Design ↔ Code` は双方向対応の意味であり、常に連続実行する意味ではない。

## 主な特徴

1. 品質ゲート中心のワークフロー（再利用、トークン、overflow、視覚検証）。
2. 設計/実装マッピング/障害対応/レスポンシブを段階的に読み込む参照構成。
3. MCP 実装差異を吸収するツール名マッピング。
4. 選択モードと未実行モードを明示する出力契約。

## ディレクトリ構成

- `SKILL.md`: 発火条件とモード別ワークフロー。
- `references/`: 詳細手順とチェックリスト。
- `README.md`: 英語概要と利用ガイド。
- `README.ja.md`: 日本語概要。

## 呼び出し例

- `Use $pencil-design-and-develop to design a new dashboard in Pencil.`
- `Use $pencil-design-and-develop to read this .pen file and implement it in React.`
