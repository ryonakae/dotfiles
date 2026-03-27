# Layouts and Swap Layouts

## 目次

- 使いどころ
- レイアウトの読み込み方
- KDL ノードの基本
- `pane` で覚えること
- `floating_panes` で覚えること
- `tab` と template
- `cwd` 合成
- swap layout
- 実用パターン
- 一次情報

## 使いどころ

`.kdl` を書く、既存レイアウトを編集する、`default_layout` を設定する、実行中タブへ layout を流し込むときに読む。

## レイアウトの読み込み方

| 操作 | コマンド | メモ |
| --- | --- | --- |
| 既定レイアウトを土台にする | `zellij setup --dump-layout default` | まずここから始める |
| 既定 swap layout を見る | `zellij setup --dump-swap-layout default` | `.swap.kdl` の土台に使う |
| 起動時に layout を適用する | `zellij --layout /path/to/layout.kdl` | `layout_dir` 内なら名前だけでもよい |
| 実行中セッションへ新タブとして追加する | `zellij --layout <name-or-path>` | 既存セッションでは追加動作になる |
| 必ず新セッションで起動する | `zellij --new-session-with-layout <name-or-path>` | 実行中セッション内でも新規作成する |
| 新しいタブへ layout を適用する | `zellij action new-tab --layout <path>` | `--name`, `--cwd` を併用できる |
| 現在タブを layout で上書きする | `zellij action override-layout <path>` | 必要に応じ `--retain-existing-*` を使う |

## KDL ノードの基本

レイアウト全体は必ず `layout { ... }` の下に置く。主要ノードは次のとおり。

| ノード | 役割 |
| --- | --- |
| `pane` | 通常ペイン、コマンドペイン、プラグインペイン、論理コンテナ |
| `tab` | Zellij のタブ |
| `floating_panes` | フローティングペイン群 |
| `pane_template` | 再利用可能な `pane` テンプレート |
| `tab_template` | 再利用可能な `tab` テンプレート |
| `default_tab_template` | 既存 `tab` と新規タブの既定骨組み |
| `new_tab_template` | 新規タブ専用の雛形 |
| `swap_tiled_layout` | タイルペイン用の可変レイアウト |
| `swap_floating_layout` | フローティングペイン用の可変レイアウト |
| `children` | template 内で子ノードを差し込む場所 |

最小例:

```kdl
layout {
    pane
    pane split_direction="vertical" {
        pane
        pane command="htop"
    }
}
```

## `pane` で覚えること

`pane` は「単独ペイン」と「子を持つ論理コンテナ」の両方を表す。子を持つときはコンテナの引数をタイトル行に書く。

| プロパティ | 用途 | 代表値 |
| --- | --- | --- |
| `split_direction` | 子ペインの並び方 | `"horizontal"` / `"vertical"` |
| `size` | 親内での固定幅または割合 | `5`, `"50%"` |
| `borderless` | pane frame を消す | `true` / `false` |
| `focus` | 起動時フォーカス | `true` / `false` |
| `name` | タイトル変更 | `"logs"` |
| `cwd` | 作業ディレクトリ | `"/repo"` や `"relative/path"` |
| `command` | シェルではなく直接実行するコマンド | `"htop"` |
| `args` | `command` の引数 | `"cargo" "test"` ではなく `command="cargo"` と併用する |
| `close_on_exit` | コマンド終了後すぐ閉じる | `true` / `false` |
| `start_suspended` | Enter までコマンドを実行しない | `true` / `false` |
| `edit` | ファイルをエディタで開く | `"./README.md"` |
| `plugin` | プラグインを置く | `plugin location="zellij:status-bar"` |
| `default_fg` / `default_bg` | pane 既定色 | `"#00e000"` |
| `stacked` | 子ペインを stack 表示にする | `true` |
| `expanded` | stack 内で最初に展開する子 | `true` |

注意点:

- `args` は `pane` のタイトル行には書けず、子ブロック内で書く。
- `edit` は `scrollback_editor` または `EDITOR` / `VISUAL` を使う。
- ルート `layout` 自体の既定 `split_direction` は `"horizontal"`。全体を縦並びにしたいなら論理コンテナ `pane split_direction="vertical"` を 1 枚置く。

## `floating_panes` で覚えること

`floating_panes` は root 直下にも `tab` の中にも置ける。中の `pane` はフローティングとして生成される。

```kdl
layout {
    floating_panes {
        pane command="lazygit"
        pane {
            x 1
            y "10%"
            width 200
            height "50%"
        }
    }
}
```

覚えること:

- `x`, `y`, `width`, `height` は固定値か `%` 指定を使える。
- `floating_panes` 内の `pane` には通常 `pane` の多くのプロパティを使える。
- `floating_panes` 内の `pane` は子ノードや `split_direction` のような無関係プロパティを持たせない。

## `tab` と template

`tab` も `pane` と同様に `split_direction`, `focus`, `name`, `cwd` を持てる。

```kdl
layout {
    tab name="editor" split_direction="vertical" {
        pane
        pane
    }
    tab name="logs" focus=true {
        pane command="tail" {
            args "-f" "log/development.log"
        }
    }
}
```

template 系:

- `pane_template`: 再利用する pane 断片を定義する
- `tab_template`: 再利用する tab 骨組みを定義する
- `children`: template 利用側の子ペインを差し込む
- `default_tab_template`: 全タブと今後の新規タブに共通する土台
- `new_tab_template`: 新しく開くタブ専用の雛形

`default_tab_template` の典型例:

```kdl
layout {
    default_tab_template {
        pane size=1 borderless=true {
            plugin location="zellij:tab-bar"
        }
        children
        pane size=2 borderless=true {
            plugin location="zellij:status-bar"
        }
    }

    tab name="work" {
        pane
        pane
    }
}
```

## `cwd` 合成

相対 `cwd` は次の順で積み上がる。

1. `pane`
2. `tab`
3. global `layout`
4. `zellij` を起動したときの作業ディレクトリ

例:

```kdl
layout {
    cwd "/hi"
    tab cwd="there" {
        pane cwd="friend"
    }
}
```

この `pane` は `/hi/there/friend` で開く。

## swap layout

swap layout は「ペイン数に応じて自動で入れ替わるレイアウト群」。通常の base layout に加えて持てる。

| ノード | 対象 |
| --- | --- |
| `swap_tiled_layout` | 通常のタイルペイン |
| `swap_floating_layout` | フローティングペイン |

制約:

- `max_panes`
- `min_panes`
- `exact_panes`

例:

```kdl
layout {
    swap_tiled_layout name="h2v" {
        tab max_panes=2 {
            pane
            pane
        }
        tab {
            pane split_direction="vertical" {
                pane
                pane
                pane
            }
        }
    }
}
```

覚えること:

- 現在の base layout も `Base` として切り替え対象になる。
- swap layout が条件に合わない状態で pane を開閉すると、自動で別の swap layout か `Base` に切り替わる。
- swap layout 内の `pane command=` や `plugin` は「そこに既に pane がある前提」で扱う。存在しない pane を新規生成するものではない。
- 長くなるなら `my-layout.swap.kdl` という別ファイルに分離してよい。

## 実用パターン

- 最初の 1 本は必ず `setup --dump-layout default` から作る。
- `default_tab_template` で tab-bar / status-bar を固定し、その間だけ可変にする。
- 役割がはっきりした pane は `name=` を付ける。
- ルートや tab に `cwd` を置き、個別 pane は相対パスで短く書く。
- 今あるタブの再配置だけなら `override-layout` を使い、別作業面の追加なら `new-tab --layout` を使う。
- 端末サイズが読めないフローティング配置は固定値より `%` を優先する。

## 一次情報

- https://zellij.dev/documentation/layouts.html
- https://zellij.dev/documentation/creating-a-layout.html
- https://zellij.dev/documentation/swap-layouts.html
