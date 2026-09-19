# 投資残高トラッカー

毎月の投資残高(資産クラス別)を記録し、全体資産の推移とポートフォリオ配分を
可視化する個人用Streamlitアプリ。Gemini APIで月次コメント生成・チャット質問・
証券会社画面のスクリーンショット/PDFからのデータ自動抽出ができます。
データベースや認証は使わず、ローカルのCSV/JSONファイルに保存します。

## セットアップ

```bash
cd portfolio_tracker
pip install -r requirements.txt
```

### Gemini APIキーの設定(いずれか1つ)

1. `.streamlit/secrets.toml.example` を `.streamlit/secrets.toml` にコピーして
   キーを記入する(推奨)
2. 環境変数 `GEMINI_API_KEY` を設定する
3. アプリ起動後、サイドバーに直接入力する(そのセッション中のみ有効・保存されません)

APIキーは https://aistudio.google.com/apikey から取得できます。

## 起動

```bash
streamlit run app.py
```

## 画面構成

- **ダッシュボード** (`app.py`): 総資産・前月比・年初来の指標、資産クラス別の
  積み上げ推移グラフ、最新月のポートフォリオ配分ドーナツチャート
- **データ入力**: 対象月を選んで資産クラスごとの残高を入力・保存。証券会社の
  画面キャプチャやPDFをアップロードしてGeminiに読み取らせることも可能。
  過去データは表で直接編集できます。
- **AIコメント**: 対象月のデータを踏まえてGeminiが月次の振り返りコメントを
  生成します(投資助言ではなく記録の振り返り用途)。
- **チャット**: 手元の資産データを踏まえて自由に質問できるチャット画面。

## データの保存先

`data/` 配下にすべてCSV/JSONで保存されます(DB不要)。

- `portfolio.csv`: 月×資産クラスの残高(ロング形式)
- `config.json`: 資産クラスの一覧
- `notes.json`: 月次メモ
- `comments.json`: Geminiが生成した月次コメントの履歴

これらは個人データのため `.gitignore` で除外しています。
