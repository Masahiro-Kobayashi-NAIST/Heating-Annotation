import streamlit as st
from html_shaper import rep_bold
from load_comments import load_html


def main():
    TOTAL_PAGES = 100

    # インスタンスを建てる (boot時のみ初期化の処理)
    if "_is_boot" not in st.session_state:
        st.session_state["_is_boot"] = True
        app = MainApp(
            TOTAL_PAGES, _is_boot=True
        )  # この中で st.session_state["page"] も初期化している
    else:
        app = MainApp()

    # キャッシュからページ番号読み込み(+ 初回読み込み時のみコメントデータの準備)
    app.set_page_now(st.session_state["page"])

    # ウィジェットの配置
    app.load_page_now()
    app.arrange_widgets()


# session_stateの初期化・更新、ウィジェット配置、アノテーションデータの生成をするクラス
class MainApp:
    def __init__(self, total_pages=None, _is_boot=False) -> None:
        if _is_boot:
            assert type(total_pages) is int
            self._totalpgs = st.session_state["totalpgs"] = total_pages
            for i in range(total_pages):  # 全ページを未読状態にしておく
                st.session_state[i + 1] = False

            if "page" not in st.session_state:  # 現在のページ番号を1として初期化
                st.session_state["page"] = 1
        else:
            assert total_pages is None
            self._totalpgs = st.session_state["totalpgs"]

    def set_page_now(self, n):
        self.page_now = n
        # 初めてn番目のページを読み込んだときの動作
        if not st.session_state[n]:
            self._initialize_page()

    def _initialize_page(self):
        n = self.page_now
        st.session_state[n] = True  # n番目のページを既読状態に
        # キャッシュ
        cmts, cmt_lvs, pid, title = load_html(n)
        st.session_state[f"pid_{n}"] = pid
        st.session_state[f"title_{n}"] = title
        st.session_state[f"cmt_{n}"] = cmts
        st.session_state[f"cmtlen_{n}"] = len(cmts)
        st.session_state[f"cmtlvs_{n}"] = cmt_lvs

        def initialize_checked(n):  # チェック状態の初期化
            pid = st.session_state[f"pid_{n}"]
            cmtlen = st.session_state[f"cmtlen_{n}"]
            for j in range(cmtlen):
                k = f"{pid}_{j}"  # ページID = pid のスレッドの n 番目のコメントのチェック状態
                if k not in st.session_state:
                    st.session_state[k] = False

        initialize_checked(n)

    # n番目の(静的)データをキャッシュからインスタンス変数に割り当てる
    def load_page_now(self):
        n = self.page_now
        self.pid = st.session_state[f"pid_{n}"]
        self.title = st.session_state[f"title_{n}"]
        self.cmts = st.session_state[f"cmt_{n}"]
        self.cmtlen = st.session_state[f"cmtlen_{n}"]
        self.cmtlvs = st.session_state[f"cmtlvs_{n}"]

    # ウィジェット配置。markdownの"#"で隙間を作る
    def arrange_widgets(self):
        self._arrange_header()
        self._arrange_name_field()
        st.markdown("#")
        self._arrange_pgn("upper")
        st.markdown("#")
        self._arrange_thread()
        st.markdown("#")
        self._arrange_pgn("lower")
        st.markdown("#")
        st.markdown("#")
        self._arrange_export_field()

    # タイトル部分
    @staticmethod
    def _arrange_header():
        from PIL import Image

        st.markdown(
            "<style>" + open(r"style.css").read() + "</style>", unsafe_allow_html=True
        )  # CSS読み込み
        # タイトル
        col_headerL, col_headerR = st.columns([5, 1])
        with col_headerL:
            st.title("議論の過熱に関する調査実験")
        with col_headerR:
            image = Image.open("sociocom-logo-circle.png")  # ラボのGoogle Driveにあるロゴ画像
            st.image(image)

    # 名前登録部分
    @staticmethod
    def _arrange_name_field():
        st.header("ユーザー登録")
        if "name" not in st.session_state:
            st.session_state["name"] = ""

        # ユーザー名入力フィールド設定。全角だとstreamlitの不具合でjsonがDLできないので半角に強制
        s = st.text_input("最初にユーザー名を半角文字で入力してください。", key="input")
        # 全角文字と空文字列の場合以外に session_state に登録
        if not s.isascii():  # asciiかどうかの判定。windowsだと代替のcurseモジュールがないと動かない
            st.error("使用できない文字が含まれています")
        elif s != "":
            st.session_state["name"] = s
        # ユーザー名が登録されていない場合
        if not st.session_state["name"]:
            st.warning("ユーザー名が登録されていません。")
        else:
            st.markdown(f"あなたのユーザー名: {st.session_state['name']}")
        st.markdown("#")
        st.markdown("""---""")
        st.header("アノテーション")
        st.markdown(
            "- 以下に表示されているのは、Wikipediaの編集者が議論を行うページ上に建てたスレッドの会話テキストです。\n"
            "- スレッドページ内で**過熱 (過剰な論争や言い争い)** が起こっていると思う場合、そこに該当するコメントにチェックをつけてください。\n"
            "- コメントのインデントは**返信**を意味します。\n"
            "\t- 収集したhtmlデータから自動的にコメントとインデントを生成しているため、コメントの区切りや表示がおかしかったり元のテキストと返信先が一致しないことがあります。ご了承ください。"
        )

    # ページ数の増減ボタン（上下兼用）
    def _arrange_pgn(self, embbed_key):
        left_col, center_col, right_col = st.columns(3)
        with left_col:
            if st.session_state["page"] > 1:
                st.button(
                    label="<< Prev",
                    on_click=self._minus_one_page,
                    key=f"{embbed_key}_left",
                )
        with right_col:
            if st.session_state["page"] < self._totalpgs:
                st.button(
                    label="Next >>",
                    on_click=self._plus_one_page,
                    key=f"{embbed_key}_right",
                )
        # 現在のページ番号
        with center_col:
            st.write(f"スレッド: {st.session_state['page']} / {self._totalpgs}")

    # アノテーションの部分
    def _arrange_thread(self):
        from streamlit_extras.colored_header import colored_header

        # ヘッダ
        colored_header(
            label=self.title,
            description="過熱している投稿にチェックをつけてください。",
            color_name="blue-green-70",
        )
        # 各コメントのアノテーションエリア
        for i, comment in enumerate(self.cmts):
            level = self.cmtlvs[i] * 2
            col1, col2 = st.columns([1, 5])
            # チェックボックスの配置
            with col1:
                k = f"{self.pid}_{i}"
                st.checkbox(
                    "HOT", key=f"{k}_chk", value=st.session_state[k]
                )  # valueにキャッシュを代入して状態を復元
            # コメントの配置
            with col2:
                is_init_line = True
                for line in comment.splitlines():
                    if line:
                        if is_init_line:  # 行頭のテンプレートを検出し、htmlで装飾する
                            line = rep_bold().sub(
                                lambda x: f'<span style="font-weight: bold">{x.group(0)[:-1]} </span>',
                                line,
                            )
                        placeholder = st.empty()  # チェックされたかどうかで見た目を変える
                        if not st.session_state[f"{k}_chk"]:
                            embbed = f'<p style="padding-left: {level}em;">{line}</p>'
                            placeholder.markdown(embbed, unsafe_allow_html=True)
                        else:
                            embbed = f'<p style="padding-left: {level}em;"><mark style="background: linear-gradient(transparent 80%, #ff7f7f 95%);">{line}</mark></p>'  # markタグで装飾
                            placeholder.markdown(embbed, unsafe_allow_html=True)
                    if is_init_line:
                        is_init_line = False
            # コメントごとの区切り線
            if i < self.cmtlen - 1:
                st.markdown("""---""")
        # フッタ
        st.markdown(
            """<hr style="height:3px;border:none;color:#00D6B2;background-color:#00D6B2;" /> """,
            unsafe_allow_html=True,
        )

    def _arrange_export_field(self):  # アノテーションデータのエクスポート
        st.header("データ生成")
        st.warning("すべてのページを確認してからエクスポートしてください", icon=None)
        is_checked = st.checkbox("すべてのページを確認しました")
        if is_checked:
            # ユーザー名の確認
            is_name_filled = bool(st.session_state["name"])
            if not is_name_filled:
                st.error("ユーザー名が空白です")
            # ページ既読の確認
            elif not all([st.session_state[i + 1] for i in range(self._totalpgs)]):
                st.error("未読のページがあります")
            else:
                self._arrange_dl_field()

    def _arrange_dl_field(self):  # DBに送信するのではなくアノテーションデータをいったん手元にDLしてもらう形にした
        import json

        is_next = st.button("DATA EXPORT")
        # 書き出し準備ができた状態で "DATA EXPORT" を押すと書き出し
        if is_next:
            dict_for_dl = self._generate_data()
            st.write("アノテーションデータを生成しました")
            st.download_button(
                label="JSONをダウンロード",
                data=json.dumps(dict_for_dl, indent=4),
                file_name=f'Annotation_{st.session_state["name"]}.json',
                mime="application/json",
            )

    def _generate_data(self):  # アノテーションデータを生成
        for i in range(len(self.cmts)):
            k = f"{self.pid}_{i}"
            st.session_state[k] = st.session_state[f"{k}_chk"]  # 現在のページの状態を保存してから
        annot_data = {
            st.session_state[f"pid_{i+1}"]: {
                j: st.session_state[f"{st.session_state[f'pid_{i+1}']}_{j}"]
                for j in range(st.session_state[f"cmtlen_{i+1}"])
            }
            for i in range(self._totalpgs)
        }  # 二重の辞書内包表記
        data = {"Name": st.session_state["name"], "Annotation": annot_data}
        return data

    # ページ遷移を行うコールバック関数
    def _minus_one_page(self):
        st.session_state["page"] -= 1
        for i in range(len(self.cmts)):
            k = f"{self.pid}_{i}"  # 遷移前にチェック状態を保存しておく
            st.session_state[k] = st.session_state[f"{k}_chk"]

    def _plus_one_page(self):  # 上と同様
        st.session_state["page"] += 1
        for i in range(len(self.cmts)):
            k = f"{self.pid}_{i}"
            st.session_state[k] = st.session_state[f"{k}_chk"]


if __name__ == "__main__":
    main()
