#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import re
import json
from ArticutAPI import Articut

'''
根據罪名，得到最長刑期
'''

def extract_keys(data, keys_set=None):
    if keys_set is None:
        keys_set = set()

    if isinstance(data, dict):
        for key, value in data.items():
            keys_set.add(key)
            extract_keys(value, keys_set)
    elif isinstance(data, list):
        for item in data:
            extract_keys(item, keys_set)

    return keys_set

# json.load 檔案得到資料
def utternace(Merged_path):
    with open(Merged_path, 'r', encoding="utf-8") as file:
        data = json.load(file)
        Merged = extract_keys(data, keys_set=None)
        MergetLIST = list(Merged)
        m =[i for i in MergetLIST if i]
        print(f"目前有{len(m)}句utt",'\n')
    return m

#國字換成數字
numbers = list(range(1, 11))
Chinese_numbers = '壹貳參肆伍陸柒捌玖拾'
num_dict = {ch: num for ch, num in zip(Chinese_numbers, numbers)}

def replace_chinese_with_arabic(texts, num_dict):
    def replace_match(match):
        return str(num_dict[match.group()])

    replaced_texts = []
    for text in texts:
        pattern = '[' + ''.join(num_dict.keys()) + ']'
        new_text = re.sub(pattern, replace_match, text)
        replaced_texts.append(new_text)

    return replaced_texts

# 檢查"有期徒刑"的國字大小寫替換
def check_target_replaced(replaced_texts, utt, targetCheckSTR="有期徒刑"):
    C1=[ r for r in replaced_texts if targetCheckSTR in r]
    C1_check = [ u for u in utt if targetCheckSTR in u]
    C1_and_check = {C1:C1_check for C1, C1_check in zip(C1, C1_check)}
    return C1_and_check

# 取出最大數字
def find_largest_number_string(strings):
    def extract_number(s):
        match = re.search(r'\d+', s)  # Use raw string for regex pattern
        return int(match.group()) if match else 0  # Only call group() if match is not None

    return max(strings, key=extract_number, default="No valid string found")

# 取出某個罪名的最長刑期
def check_crime_MaxPenalty(first_check, crimeSTR):
    check_crime = check_target_replaced([c for c in first_check.keys()], [c for c in first_check.values()], crimeSTR) #檢查"有期徒刑"的國字大小寫替換
    Ｍax_penalty = find_largest_number_string([c for c in check_crime.keys()]) # 取出最長刑期
    return Ｍax_penalty

#load罪名抓出最大刑期
def MaxPenalty(Crime_path):
    MaxPenalty=[]   
    with open(Crime_path, 'r', encoding='utf8')as f:
        Crime = json.load(f)
        data_utt=[C for C in Crime.keys()]
    
    for crime in data_utt:
        crime_max=check_crime_MaxPenalty(first_check, crime)
        for c in crime_max.split('\n'):
            if c!='No valid string found':
                MaxPenalty.append(c)
            else: 
                pass
    return set(MaxPenalty)


Merged_path = "../data/MergedALL.json" # 原始資料(罪名加上刑期)
Crime_path = '../data/CrimeALL.json' # 所有罪名
result_path = "../data/results.json"  # 罪名加上刑期最重的


if __name__ == '__main__':
    utt = utternace(Merged_path)
    replaced_texts = replace_chinese_with_arabic(utt, num_dict)
    first_check = check_target_replaced(replaced_texts, utt, "有期徒刑")
    MaxPenalty = MaxPenalty(Crime_path)
    print(MaxPenalty)
    
