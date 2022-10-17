import json
import re
from bs4 import BeautifulSoup


def load_html(n):
    PATH = f"html_test_{n}.json"  # テスト用ファイルのパス
    with open(PATH, "r") as f:
        d = json.load(f)

    html_text = d["parse"]["text"]["*"]
    pid = d["parse"]["pageid"]
    title = d["parse"]["title"].lstrip("Wikipedia:井戸端/subj/")
    return html_text, pid, title


# htmlテキストを整形し、split_html()でコメントに分割
def slice_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    # コメントのレベル抽出
    tags = soup.find_all(
        "a", attrs={"class": "ext-discussiontools-init-replylink-reply"}
    )
    cmt_levels = [[p.name for p in tag.parents].count("dd") for tag in tags]
    # お知らせ削除
    for s in soup.find_all("table", attrs={"class": "plainlinks tmbox tmbox-notice"}):
        s.decompose()
    # スレッドの関連タグ削除
    for s in soup.find_all("div", attrs={"class": "nowraplinks plainlinks"}):
        s.decompose()
    # タイトル部分削除
    for s in soup.find_all("h2", attrs={"class": "ext-discussiontools-init-section"}):
        s.decompose()
    # 整形したhtmlをテキスト化したものを引数に
    cmts = split_html(soup.text)
    return cmts, cmt_levels


def split_html(html_text):
    REP_CMT = re.compile(r".+返信\[返信\]$")
    text_lines = html_text.splitlines()

    def trim_comment():
        i = 0
        start = 0  # コメント冒頭
        end = -1
        while i < len(text_lines):
            line = text_lines[i]  # 行ごとにテキストを見る
            m = REP_CMT.match(line)
            if m is not None:  # もし 行末尾が 返信[返信] となっていれば
                end = i + 1
                cmt = "\n".join(text_lines[start:end])  # そこをコメントの区切りとする
                yield cmt.strip()
                start = i + 1  # 次の行をコメント冒頭に設定
            i += 1

    cmts = list(trim_comment())
    return cmts


def rep_bold():
    BOLD_TEMPLATES = (
        r"^賛成\s",
        r"^条件付賛成\s",
        r"^強く賛成\s",
        r"^反対\s",
        r"^条件付反対\s",
        r"^強く反対\s",
        r"^保留\s",
        r"^中立\s",
        r"^棄権\s",
        r"^提案\s",
        r"^理由\s",
        r"^コメント\s",
        r"^返信\s",
        r"^質問\s",
        r"^除去\s",
        r"^情報\s",
        r"^報告\s",
        r"^取り下げ\s",
        r"^終了\s",
        r"^提案無効\s",
        r"^コ\s",
        r"^コメ\s",
        r"^横から失礼\s",
        r"^返\s",
        r"^感謝\s",
        r"^完了\s",
        r"^メモ\s",
        r"^済\s",
        r"^対処\s",
        r"^注\s",
        r"^告知\s",
    )  # コメントテンプレートの文字列
    return re.compile("|".join(BOLD_TEMPLATES))
