import json


def load_html(n):
    PATH = f"Annotation_samples/sample_{n}.json"
    with open(PATH, "r") as f:
        d = json.load(f)

    cmts = d["commnts"]
    cmt_lvs = d["comment_levels"]
    pid = d["pageid"]
    title = d["title"].lstrip("Wikipedia:井戸端/subj/")
    return cmts, cmt_lvs, pid, title
