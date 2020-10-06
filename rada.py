import requests
import time
import re
import csv

import gzip

from pyquery import PyQuery as pq


VOTE_URL_TEMPLATE = (
    "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_golos_print?g_id={0}&vid=1"
)
DOC_DIR = "source_docs"
DELAY = 1

VOTE_DETAILS = "votes.csv.gz"
VOTE_HEADERS = "vote_headers.csv"


def _init_csvs():
    """
    save CSV titles
    """
    s = "session,kind,docnum,date,time,title,yay,nay,abstain,dnv,total,result"
    with open(VOTE_HEADERS, "wt") as f:
        f.write(s + "\n")
    s = "docnum,date,time,name,vote"
    with gzip.open(VOTE_DETAILS, "wt") as f:
        f.write(s+ "\n")


def parse_vote_header(html):
    """
    <title>Результати поіменного голосування</title>
    <table  border="0" align="center" cellpadding="0" cellspacing="0"  width="100%">
    <tr><td align="center" class="f1"><b>ВЕРХОВНА РАДА УКРАЇНИ</b></td></tr>
    <tr><td align="center" class="f2">
    1 сесія&nbsp;&nbsp;9 скликання<br>
    <b>РЕЗУЛЬТАТИ ПОІМЕННОГО ГОЛОСУВАННЯ</b><br>
    № 2 від 29.08.2019 13:23:49<br>
    <b>Поіменне голосування  про проект Постанови про Тимчасову президію першої сесії Верховної Ради України дев'ятого скликання (№1001) - за основу та в цілому
    </b><br>
    За - 390  Проти - 0  Утрималися - 0  Не голосували - 31 Всього - 421<br>
    <b>Рішення прийнято</b>
    </td></tr></table>
    """

    doc = pq(html)
    headers = doc("td.f2").text().split("\n")
    """
    ['1 сесія\xa0\xa09 скликання', 
    'РЕЗУЛЬТАТИ ПОІМЕННОГО ГОЛОСУВАННЯ', 
    '№ 7 від 29.08.2019 14:54:57', 
    'Поіменне голосування про перехід до обговорення кандидатури на посаду Голови Верховної Ради України', 
    'За - 311 Проти - 6 Утрималися - 6 Не голосували - 95 Всього - 418', 
    'Рішення прийнято']
    """
    sess, kind, dt, title, summary, result = headers

    # '№ 7 від 29.08.2019 14:54:57'
    match = re.search(r"\s(\d*)\s.*\s(\d+\.\d+.\d+)\s(\d+\:\d+\:\d+)", dt)
    num, day, tme = match[1], match[2], match[3]

    rx = r"За - (\d+) Проти - (\d+) Утрималися - (\d+) Не голосували - (\d+) Всього - (\d+)"
    m = re.search(rx, summary)
    yay, nay, abstain, dnv, total = m[1], m[2], m[3], m[4], m[5]

    return (
        sess,
        kind,
        num,
        day,
        tme,
        title,
        yay,
        nay,
        abstain,
        dnv,
        total,
        result,
    )


def parse_vote_body(html) -> list:
    """
    Input is series of:

        <td class="hcol1">Урбанський А.І.</td>
        <td>Не голосував</td>

    Returns list of tuples like:

    [('Аліксійчук О.В.', 'За'), ('Аллахвердієва І.В.', 'За'),
        ('Ананченко М.О.', 'За'), ('Андрійович З.М.', 'За'),
        ...
    ]
    """
    rx = r'<td class\="hcol1">(.+?)<\/td>.*?<td>(.+?)<\/td>'
    return re.findall(rx, html, re.S)


def save_doc(id, html):
    with gzip.open(f"{DOC_DIR}/vote_{id}.html.gz", "w") as f:
        f.write(html)


def save_parsed_vote(header, votes):
    import os.path
    import csv

    if not (os.path.isfile(VOTE_HEADERS) and os.path.isfile(VOTE_DETAILS)):
        print("creating csv headers")
        _init_csvs()

    with open(VOTE_HEADERS, "at", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

    pre = header[2:5]  # num, day, time
    post = header[5:6]  # title

    with gzip.open(VOTE_DETAILS, "at", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(pre + vote for vote in votes)


def get_one_vote_doc(id) -> (int, str):
    """ get single vote result """

    print(f"Getting doc {id} ... ", end="")
    res = requests.get(VOTE_URL_TEMPLATE.format(id))
    print("ok" if res.status_code == 200 else f"error: {res.status_code}")
    # it really is in utf8
    # ¯\_(ツ)_/¯
    txt = res.text.replace("charset=windows-1251", "charset=utf8").replace("\xa0", "")
    return res.status_code, txt


def gen_docs(start=25, end=26):
    for id in range(start, end + 1):
        yield id, *get_one_vote_doc(id)
        time.sleep(DELAY)


def scrape_and_save(start=25, end=26):
    """dl and save a range of voting docs from rada"""
    for id, code, html in gen_docs(start, end):
        if code == 200:
            save_doc(id, html)
    print("Scraping done")


def get_and_parse_votes(start=25, end=26):
    """dl and parse a range of voting docs from rada"""
    for id, code, html in gen_docs(start, end):
        if code == 200:
            save_doc(id, html)
            header = parse_vote_header(html)
            votes = parse_vote_body(html)
            save_parsed_vote(header, votes)
        else:
            print(f"error {code}")


def reparse():
    import glob
    print("Will reparse all vote*.html files in ", DOC_DIR)
    _init_csvs()
    for fname in sorted(glob.glob(f"{DOC_DIR}/vote*.html.gz")):
        print("reparse: ", fname, end=' ... ')
        try:
            with gzip.open(fname, 'rt') as f:
                html = f.read()
                header = parse_vote_header(html)
                votes = parse_vote_body(html)
                save_parsed_vote(header, votes)
                print('ok')
        except Exception as e:
            print(e)




def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=["parse", "scrape", "reparse", "_init_csvs"],
        help="Mode of operation: \n parse: download and parse votes \n dl: just download \n reparse: parse a single vote result",
    )
    parser.add_argument("--start", default=25, type=int, help="starting seq #")
    parser.add_argument("--end", default=7800, type=int, help="last seq #")
    args = parser.parse_args()
    if args.mode == "scrape":
        scrape_and_save(args.start, args.end)
    elif args.mode == "parse":
        get_and_parse_votes(args.start, args.end)
    elif args.mode == "reparse":
        reparse()


if __name__ == "__main__":
    main()
