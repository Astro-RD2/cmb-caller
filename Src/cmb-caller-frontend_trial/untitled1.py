#!/usr/bin/env python3
# regex_toolkit.py
# -*- coding: utf-8 -*-
"""
正規表示式工具箱範例程式
- 支援多種範例：email/URL 驗證、日期擷取、log 解析、遮蔽信用卡、等等
- 使用 argparse 當作 CLI，並包含簡易單元測試示例
"""

import re
import argparse
import time
from typing import List, Tuple, Dict, Optional, Callable



# -------------------------
# 常用正則表達式（編譯以提速）
# -------------------------
RE_EMAIL = re.compile(
    r"""
    ^                                   # 行首
    (?P<local>[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+(?:\.[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+)*)  # local-part
    @
    (?P<domain>(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,})      # domain
    $                                   # 行尾
    """, re.VERBOSE
)


RE_URL = re.compile(
    r"""
    \b
    (?P<scheme>https?|ftp)://
    (?P<host>[^/\s:?#]+)
    (?::(?P<port>\d{1,5}))?
    (?P<path>/[^\s?#]*)?
    (?:\?(?P<query>[^\s#]*))?
    (?:#(?P<frag>\S+))?
    """,
    re.VERBOSE | re.IGNORECASE
)


               
'''               
               
RE_URL = re.compile(
    r"""
    \b
    (?P<scheme>https?|ftp)://
    (?P<host>[^/\s:?#]+)
    (?::(?P<port>\d{1,5}))?
    (?P<path>/[^\s?#]*)?
    (?:\?(?P<query>[^\s#]*))?
    (?:#(?P<frag>\S+))?
    """, re.VERBOSE | re.IGNORECASE
)

'''




# 簡單的 YYYY-MM-DD 或 YYYY/MM/DD
RE_DATE = re.compile(r'\b(?P<y>\d{4})[-/](?P<m>0[1-9]|1[0-2])[-/](?P<d>0[1-9]|[12]\d|3[01])\b')

# 常見國際電話（非常簡化）
RE_PHONE = re.compile(r'\+?\d{1,3}[-.\s]?(?:\(\d+\))?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}')

# Apache/Nginx 風格 Access log (非常簡化)
RE_APACHE_LOG = re.compile(
    r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+-\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+"(?P<req>[^"]+)"\s+(?P<status>\d{3})\s+(?P<size>\d+|-)'
)

# 信用卡檢測（非常寬鬆）與遮蔽群組
RE_CREDIT_CARD = re.compile(r'(?P<prefix>\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6[0-9]{3}))[-\s]?(?P<rest>(?:\d{4}[-\s]?){2,3}\d{1,4})')

# -------------------------
# 功能函式
# -------------------------
def validate_email(email: str) -> bool:
    """驗證 email 格式（不保證 deliverable）"""
    m = RE_EMAIL.match(email)
    return bool(m)

def extract_urls(text: str) -> List[Dict[str, Optional[str]]]:
    """從文字中擷取所有 URL（並回傳命名群組資訊）"""
    results = []
    for m in RE_URL.finditer(text):
        results.append(m.groupdict())
    return results

def extract_dates(text: str) -> List[str]:
    """擷取 YYYY-MM-DD / YYYY/MM/DD 格式的日期字串"""
    return [m.group(0) for m in RE_DATE.finditer(text)]

def mask_credit_cards(text: str) -> str:
    """
    將信用卡號遮蔽，只保留前 4 後 4，其他用 * 隱藏。
    使用 sub 的 callback 以保持群組資訊與靈活處理。
    """
    def _mask(m: re.Match) -> str:
        full = m.group(0)
        digits = re.sub(r'\D', '', full)
        if len(digits) < 12:
            return full  # 不處理太短的
        return digits[:4] + '-' + '*' * (len(digits) - 8) + '-' + digits[-4:]
    return RE_CREDIT_CARD.sub(lambda mm: _mask(mm), text)

def parse_apache_log(line: str) -> Optional[Dict[str, str]]:
    """解析一行 access log，回傳 dict 或 None"""
    m = RE_APACHE_LOG.search(line)
    return m.groupdict() if m else None

def find_phone_numbers(text: str) -> List[str]:
    """找出電話號碼（簡化版）"""
    return [m.group(0) for m in RE_PHONE.finditer(text)]

def normalize_whitespace(text: str) -> str:
    """把多個空白 (含換行、tab) 縮成一個空格"""
    return re.sub(r'\s+', ' ', text).strip()

def replace_with_callback(text: str, pattern: re.Pattern, callback: Callable[[re.Match], str]) -> str:
    """示範 sub callback 接受 Match 並回傳替換字串"""
    return pattern.sub(callback, text)

# 範例：用 regex 做簡單 CSV 清理（把包含逗號的欄位拆出）
RE_QUOTED_FIELD = re.compile(r'"([^"]*)"')

def simple_csv_split(line: str) -> List[str]:
    """
    非完美 CSV 解析器（只示範正則與 replace 的配合）。
    - 先把雙引號裡面的逗號用特殊符號替換，然後以逗號拆分，再還原。
    """
    placeholder = '\uE000'  # 私用區域符號
    protected = RE_QUOTED_FIELD.sub(lambda m: m.group(1).replace(',', placeholder), line)
    parts = [p.replace(placeholder, ',').strip() for p in protected.split(',')]
    return parts

# 簡單效能測試：比較編譯 pattern 與 inline pattern 的速度
def perf_test(pattern_str: str, text: str, runs: int = 10000) -> Dict[str, float]:
    # inline (每次 compile)
    t0 = time.perf_counter()
    for _ in range(runs):
        re.search(pattern_str, text)
    t1 = time.perf_counter()
    # compiled
    p = re.compile(pattern_str)
    t2 = time.perf_counter()
    for _ in range(runs):
        p.search(text)
    t3 = time.perf_counter()
    return {
        "inline_ms": (t1 - t0) * 1000,
        "compiled_ms": (t3 - t2) * 1000,
        "compiled_overhead_ms": (t2 - t1) * 1000
    }

# -------------------------
# CLI & Demo
# -------------------------
def demo_all():
    demo_text = """
    Hello! Contact: alice@example.com or bob.smith+tag@sub.domain.co.uk.
    Visit: https://example.com:8080/path/to/page?q=1#frag or http://test.local/
    Dates: 2023-01-15, 2024/02/28 and invalid 2024-02-31.
    Phones: +886-912-345-678, (02) 1234-5678, 0912 345 678
    Log: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
    CC: 4111 1111 1111 1111 and 5500-0000-0000-0004
    CSV: "a, b", c, "d, e, f"
    """

    print("=== validate_email ===")
    for e in ["alice@example.com", "bad@@example", "bob.smith+tag@sub.domain.co.uk"]:
        print(f"{e:40} -> {validate_email(e)}")
    print()

    print("=== extract_urls ===")
    for u in extract_urls(demo_text):
        print(u)
    print()

    print("=== extract_dates ===")
    print(extract_dates(demo_text))
    print()

    print("=== find_phone_numbers ===")
    print(find_phone_numbers(demo_text))
    print()

    print("=== parse_apache_log ===")
    print(parse_apache_log("127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] \"GET /apache_pb.gif HTTP/1.0\" 200 2326"))
    print()

    print("=== mask_credit_cards ===")
    print(mask_credit_cards(demo_text))
    print()

    print("=== simple_csv_split ===")
    print(simple_csv_split('"a, b", c, "d, e, f"'))
    print()

    print("=== normalize_whitespace ===")
    print(normalize_whitespace("  This   is \n a\t test   "))
    print()

    print("=== perf_test (email-ish) ===")
    perf = perf_test(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', demo_text, runs=5000)
    print(perf)
    print()

def run_cli_demo(args):
    if args.demo == 'all':
        demo_all()
    elif args.demo == 'email':
        print("Email 測試")
        for e in args.inputs:
            print(f"{e:40} -> {validate_email(e)}")
    elif args.demo == 'urls':
        for i, u in enumerate(extract_urls(" ".join(args.inputs)), 1):
            print(f"{i}. {u}")
    elif args.demo == 'dates':
        print(extract_dates(" ".join(args.inputs)))
    elif args.demo == 'mask_cc':
        for text in args.inputs:
            print(mask_credit_cards(text))
    elif args.demo == 'parse_log':
        for line in args.inputs:
            print(parse_apache_log(line))
    elif args.demo == 'csv':
        for line in args.inputs:
            print(simple_csv_split(line))
    elif args.demo == 'perf':
        pattern = args.pattern or r'\d{3}-\d{3}-\d{4}'
        text = " ".join(args.inputs) or "Contact 123-456-7890 sample text"
        print(perf_test(pattern, text, runs=args.runs))
    else:
        print("未知 demo 選項，請使用 --help 查看可用項目。")

# -------------------------
# 簡單單元測試（手動風格）
# -------------------------
def _unit_tests():
    assert validate_email("alice@example.com")
    assert not validate_email("not-an-email")
    assert "https://example.com" in " ".join(u['scheme'] + "://" + u['host'] for u in extract_urls("https://example.com"))
    assert "2023-01-15" in extract_dates("2023-01-15")
    assert "4111-****-****-1111" not in mask_credit_cards("4111 1111 1111 1111")  # 我們的 mask 是 4111-****-****-1111 形式或類似
    print("所有簡單測試通過。")

# -------------------------
# main
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Regex Toolkit Demo")
    parser.add_argument('demo', nargs='?', default='all', choices=['all','email','urls','dates','mask_cc','parse_log','csv','perf'],
                        help='要執行的範例')
    parser.add_argument('--inputs', '-i', nargs='*', default=[
        'alice@example.com', 
        'bob.smith+tag@sub.domain.co.uk', 
        '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET / HTTP/1.0" 200 1234',
        '4111 1111 1111 1111', 
        '"a, b", c, "d, e, f"'
    ], help='輸入示例（多值）')
    parser.add_argument('--pattern', '-p', help='perf 測試的 pattern')
    parser.add_argument('--runs', '-r', type=int, default=2000, help='perf 測試次數')
    parser.add_argument('--test', action='store_true', help='執行內建單元測試')
    args = parser.parse_args()

    if args.test:
        _unit_tests()
        return

    run_cli_demo(args)

if __name__ == '__main__':
    main()
