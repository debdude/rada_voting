import requests
import time
import re
import csv
from pyquery import PyQuery as pq


VOTE_URL_TEMPLATE = (
    "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_golos_print?g_id={0}&vid=1"
)
DOC_DIR = "docs"
DELAY = 1


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
    return {
        "session": sess,
        "kind": kind,
        "docnum": num,
        "date": day,
        "time": tme,
        "title": title,
        "summary": summary,
        "result": result,
    }


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
    with open(f"{DOC_DIR}/vote_{id}.html", "w") as f:
        f.write(html)


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
    """scrape a range of voting docs from rada"""
    for id, code, html in gen_docs(start, end):
        if code == 200:
            save_doc(id, html)
    print("Scraping done")


def get_and_parse_votes(start=25, end=26):
    """scrape a range of voting docs from rada"""
    for id, code, html in gen_docs(start, end):
        if code == 200:
            save_doc(id, html)
            header = parse_vote_header(html)
            votes = parse_vote_body(html)

        else:
            print(f"error {code}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=["parse", "scrape", "reparse"],
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
        reparse(args.start, args.end)


if __name__ == "__main__":
    main()
