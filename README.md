# activity-watch-log-2-diary

[ActivityWatch](https://activitywatch.net/) のログをAI使って日記に変換するプロジェクト

## 構成メモ

```mermaid
flowchart TD
    A[アンドロイド] --> |操作ログ収集| C[ActivityWatch]
    B[デスクトップ] --> |操作ログ収集| D[ActivityWatch]
    C --> |ログバケットアップロード| E[Tasker]
    E --> |Up| F[Googleドライブ]
    F --> |ログの取得・結合・短縮|G[バッチ - デスクトップ]
    D --> |ログの取得・結合・短縮|G
    G --> |要約| H[AI（Chatgpt）]
    H --> |日記として保存| I[Obsidian]
```

## 要素

- プログラムとActivityWatchを操作してプロンプトを生成するバッチ
- AIに食わせるためにログをスリムにするプログラム
- スリム化したログを元に日記を作るプロンプトのテンプレート
- GoogleドライブからAndroidのログバケットを取得しActivityWatchにエクスポートする機能
- (将来的に) 生成したプロンプトをAIに渡して日記に変換して格納するプログラム
- (将来的に) この処理を定期的に実行するタイマー処理（Cron？Windowsスケジューラー？スタートアップでバッチ起動？）

## 備考

AIで作ってるので可読性は皆無です

主にコードのバージョン履歴管理がメインです

