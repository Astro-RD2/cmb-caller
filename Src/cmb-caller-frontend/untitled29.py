# -*- coding: utf-8 -*-
"""
Created on Fri Jun 20 14:40:48 2025

@author: RoyChing
"""
import json

# 定義 C 數列
c_series = [f"z{i:04d}" for i in range(1, 11)]  # z0001~z0010


def process_data(input_data):
    # 判斷是 A 系列還是 B 系列
    data = json.loads(input_data)

    if data["caller_id"] != "all":
        # A 系列 - 直接印出 caller_id
        print(data["caller_id"])
    else:
        # B 系列 - 印出 C 數列中非 excluded 的值
        excluded = data["excluded"]
        # 從 excluded 中提取 caller_id (去掉 vendor_id 前綴)
        excluded_ids = [x.split('_')[1] for x in excluded if '_' in x]

        # 找出 C 數列中不在 excluded_ids 的值
        result = [x for x in c_series if x not in excluded_ids]
        print(result)


# 測試 A 系列
print("處理 A 系列:")
a_series = [
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"z0001","excluded":""}',
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"z0005","excluded":""}',
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"z0008","excluded":""}'
]

for a in a_series:
    process_data(a)

# 測試 B 系列
print("\n處理 B 系列:")
b_series = [
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"all","excluded":["tawe_z0001","tawe_z0004","tawe_z0003"]}',
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"all","excluded":["tawe_z0009","tawe_z0005"]}'
]

for b in b_series:
    process_data(b)

print("\n處理 C 系列:")
process_data(
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"z0001","excluded":""}')
process_data(
    '{"action":"reset_caller","vendor_id":"tawe","caller_id":"all","excluded":["tawe_z0001","tawe_z0004","tawe_z0003"]}')
