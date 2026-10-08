"""音声テキスト → 依頼データへの構造化。

AI-MOP（OpenAI互換のChat Completions API）が設定されていればAIで構造化し、
未設定・通信失敗・不正な応答のときは簡易ルール方式に自動で切り替えます。

環境変数（未設定ならルール方式のみで動作）:
    AI_MOP_BASE_URL  例: https://example.com/v1   （末尾に /chat/completions を付けて呼び出します）
    AI_MOP_API_KEY   APIキー
    AI_MOP_MODEL     省略時は gpt-5.4-nano

戻り値の形は常に次のとおりです。
    {'title': str, 'location': str, 'desired_time': str, 'missing': [str, ...]}
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

FIELDS = ('title', 'location', 'desired_time')
WEEKDAYS = '月火水木金土日'

SYSTEM_PROMPT = """\
あなたは、高齢者の話し言葉から「お手伝いの依頼」を整理するアシスタントです。
次のJSONだけを返してください。説明文は不要です。
{{"title": "...", "location": "...", "desired_time": "..."}}

ルール:
- title: お願いしたい内容を「〜をお願いしたいです」の丁寧な一文にする（例: 電球の交換をお願いしたいです）。
- location: 話に出てきた場所（都道府県・市区町村など）。話に出ていなければ空文字。推測しない。
- desired_time: 希望の日時を「6/1（日）午前中」の形式にする。「明日」「来週の月曜」などは、今日の日付を基準に直す。話に出ていなければ空文字。推測しない。
- 聞き取りの誤りと思われる語は、文脈から自然な語に直してよい。
今日の日付: {today}
"""


# ---------------------------------------------------------------- AI-MOP
def _today_text() -> str:
    now = datetime.now(ZoneInfo('Asia/Tokyo'))
    return f'{now.year}年{now.month}月{now.day}日（{WEEKDAYS[now.weekday()]}）'


def _clean(value) -> str:
    return value.strip()[:100] if isinstance(value, str) else ''


def _call_ai_mop(text: str):
    """AI-MOPで構造化する。使えない場合は None を返す。"""
    base_url = os.environ.get('AI_MOP_BASE_URL', '').strip()
    api_key = os.environ.get('AI_MOP_API_KEY', '').strip()
    if not base_url or not api_key:
        return None

    payload = {
        'model': os.environ.get('AI_MOP_MODEL', 'gpt-5.4-nano'),
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT.format(today=_today_text())},
            {'role': 'user', 'content': text},
        ],
        'response_format': {'type': 'json_object'},
    }
    req = urllib.request.Request(
        base_url.rstrip('/') + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            body = json.load(res)
        parsed = json.loads(body['choices'][0]['message']['content'])
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None

    result = {key: _clean(parsed.get(key)) for key in FIELDS}
    return result if result['title'] else None


# ---------------------------------------------------------- ルール方式（予備）
_TITLE_RULES = [
    (r'電球', '電球の交換をお願いしたいです'),
    (r'買い物|買って|買い出し', '買い物をお願いしたいです'),
    (r'掃除|そうじ', 'お掃除をお願いしたいです'),
    (r'スマホ|携帯|パソコン|使い方', 'スマホ・パソコンの使い方を教えてほしいです'),
    (r'荷物|運んで|運ぶ', '荷物を運んでほしいです'),
    (r'庭|草むしり|草取り', 'お庭の手入れをお願いしたいです'),
]

_LOCATION_RE = re.compile(
    r'(?:東京都|北海道|(?:京都|大阪)府|[一-龥]{2,3}県)?[一-龥ァ-ヶー]{1,5}[市区町村]'
)
_DATE_RE = re.compile(
    r'\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|今日|明日|明後日|あさって|今週末|来週|今週|週末'
    r'|[月火水木金土日]曜日?'
)
_TIME_RE = re.compile(r'午前中|午前|午後|朝|昼|夕方|夜|\d{1,2}時')


def _rule_based(text: str) -> dict:
    title = ''
    for pattern, label in _TITLE_RULES:
        if re.search(pattern, text):
            title = label
            break
    if not title and text:
        title = text[:40]

    m = _LOCATION_RE.search(text)
    location = m.group(0) if m else ''

    time_parts = [m.group(0) for m in (_DATE_RE.search(text), _TIME_RE.search(text)) if m]
    return {'title': title, 'location': location, 'desired_time': ' '.join(time_parts)}


# ---------------------------------------------------------------- 公開関数
def structure_request(text: str) -> dict:
    """話し言葉のテキストから依頼の項目を取り出す。"""
    text = (text or '').strip()
    result = _call_ai_mop(text) if text else None
    if result is None:
        result = _rule_based(text)

    result['missing'] = [key for key in FIELDS if not result[key]]
    return result