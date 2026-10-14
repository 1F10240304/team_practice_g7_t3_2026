# ログイン機能 設計書

- 作成日: 2026-10-14
- 対象: team_project（学生・高齢者マッチングアプリ / Django）

## 目的

学生・高齢者が自分でアカウントを作成し、ログインして自分のマイページを使えるようにする。

## 範囲

- 新規登録（学生 / 高齢者）
- ログイン
- ログアウト

### やらないこと

- パスワード再設定
- メールアドレス・電話番号でのログイン
- 登録後の役割（学生 ⇔ 高齢者）の変更

## 画面とURL

| URL | name | 画面 | 内容 |
|---|---|---|---|
| `/accounts/login/` | `login` | ログイン | ユーザー名・パスワード。Django標準の `LoginView` |
| `/accounts/logout/` | `logout` | ログアウト | POSTのみ。完了後はログイン画面へ |
| `/signup/` | `select_role` | 役割の選択 | 「学生として登録」「高齢者として登録」の2ボタン（`select_role.html`） |
| `/signup/student/` | `student_signup` | 学生の登録 | ユーザー名・パスワード（2回）・名前・大学と学年 |
| `/signup/senior/` | `senior_signup` | 高齢者の登録 | ユーザー名・パスワード（2回）・名前・住んでいる地域 |
| `/mypage/` | `mypage` | （画面なし） | 役割に応じて学生 / 高齢者マイページへ振り分け |

ログイン・ログアウトは `config/urls.py` に `path("accounts/", include("django.contrib.auth.urls"))` を追加して使う。

## 入力項目

### アカウント

Django標準の `UserCreationForm`（ユーザー名・パスワード・パスワード確認）。

### プロフィール（登録時は最低限のみ）

| 役割 | 登録時の項目 | 後からマイページで入力 |
|---|---|---|
| 学生 | `name`, `university` | `introduction`, `skills` |
| 高齢者 | `name`, `area` | `introduction`, `needs` |

## 役割の判定

新しいモデルは追加しない。User に紐づくプロフィールの種類で判定する。

- `StudentProfile` がある → 学生
- `SeniorProfile` がある → 高齢者
- どちらもない（管理者など） → 役割なし

## 動き

1. **登録**: User とプロフィールを1つのトランザクションで同時に作成する（片方だけ作られることはない）。作成後は自動でログインし、自分のマイページへ移動する。
2. **ログイン後の移動先**: `LOGIN_REDIRECT_URL = "mypage"`。`/mypage/` で役割を判定して振り分ける。役割なしの場合は `/signup/` へ移動する。
3. **ログアウト後の移動先**: `LOGOUT_REDIRECT_URL = "login"`。
4. **役割が違うマイページを開いたとき**: 学生が `/mypage/senior/` を開いた場合などは、自分のマイページへリダイレクトする（既存コードでは別の役割のプロフィールが新しく作られてしまうため修正する）。役割なしのユーザーは `/signup/` へ移動する。
5. **ログイン済みで登録画面を開いたとき**: `/mypage/` へリダイレクトする。
6. **画面間のリンク**: ログイン画面 → 新規登録、登録画面 → ログイン、各マイページにログアウトボタン（POSTフォーム）。

## エラー処理

- ユーザー名の重複・パスワード不一致・パスワードが弱いなどは `UserCreationForm` のバリデーションエラーとしてフォーム上に表示する。
- プロフィール項目の未入力も同じくフォーム上にエラー表示する。
- ログイン失敗時は `LoginView` 標準のエラーメッセージを表示する。

## ファイル構成（予定）

- `team_project/forms.py`: 登録用フォーム（学生用・高齢者用）を追加
- `team_project/views.py`: `select_role`, `student_signup`, `senior_signup`, `mypage` を追加、既存マイページに役割チェックを追加
- `team_project/urls.py`: 上記URLを追加
- `config/urls.py`: `accounts/` を追加
- `config/settings.py`: `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` を追加
- `team_project/templates/registration/login.html`: ログイン画面
- `team_project/templates/select_role.html`, `student_signup.html`, `senior_signup.html`: 登録画面
- `team_project/static/css/`: 画面ごとのCSS（テンプレートに `<style>` / `<script>` は書かない）

## テスト

- 学生 / 高齢者として登録すると User とプロフィールが作られ、ログイン状態で自分のマイページへ移動する
- 入力エラー時は User もプロフィールも作られない
- `/mypage/` が役割に応じて正しく振り分ける（役割なしは `/signup/`）
- 役割が違うマイページを開くと自分のマイページへ戻され、プロフィールは作られない
- 未ログインでマイページを開くとログイン画面へ移動する
