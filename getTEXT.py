#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from ArticutAPI import Articut
import json
import os
import re
import time

account_path = "../data/account.info"
folder_path ="../data/臺灣澎湖地方法院_刑事"
People_path = '../data/PeopleALL.json'
Merged_path = "../data/MergedALL.json"
Crime_path = '../data/CrimeALL.json'
Penalty_path = "../data/PenaltyALL.json"

PeoplePat =re.compile(".*")
MergedPat = re.compile("((?<=犯</ENTITY_oov)|(?<=[犯結]</ACTION_verb>)|(?<=犯</ENTITY_nouny>)).*")
CrimePat = re.compile("((?<=犯</ENTITY_oov)|(?<=[犯結]</ACTION_verb>)|(?<=犯</ENTITY_nouny>)).*(<ENTITY_nouny>[^<]+</ENTITY_nouny>|<ENTITY_oov>罪</ENTITY_oov>|<ENTITY_nounHead>罪</ENTITY_nounHead>)")
PenaltyPat = re.compile("(?=<處</ACTION_verb>)?([^>]+>[^<]+</MODIFIER>|[^>]+>[^<]+</ENTITY_nouny>)([^>]+>[^<]+</ENTITY_nounHead>)?([^>]+>[^<]+</TIME_[^>]+>)")

try:
    with open(account_path, "r", encoding='utf8') as f:
        accountDICT = json.load(f)
except FileNotFoundError:
    print("make sure if you have the file")

def articut(inputSTR):
    articut = Articut(username=accountDICT["username"], apikey=accountDICT["apikey"])
    resultDICT = articut.parse(inputSTR)

    return resultDICT

def collect_file_path(folder_path,s=1000):    
    '''folder_path: str,
       s: int,起迄到第s個檔案,
       input: collect_file_path(folder_path,s),
       output: list of strings of filenames, e.g., Articut_刑事判決_102,易,85_2014-01-20.json
    '''
    filename=[]
    for file in os.listdir(folder_path)[:s]:
            filename.append(os.path.join(folder_path, file)) 
    return filename
    
def get_MainT_save(filename): 
    '''filename: list of str, 判決書的主文內容,
       input: get_MainT_save(filename), 
       output: list of string, ["梅有仁犯詐欺取財罪，共計伍罪，......。"]
    '''
    MText=[]
    for file in filename:
        try:
            with open(file, encoding = "utf8") as file:
                raw_data = json.load(file)       
                utt = raw_data["mainText"]
                if isinstance(utt, str) and len(utt) > 8:
                    '''
                    設定字數>8，是略過判為無罪的案件
                    '''
                    utt_result=(utt.replace("\n",""))
                    MText.append(utt_result)
                elif isinstance(utt, dict):
                    result_segmentation = utt.get("result_segmentation", "Key not found")
                    MText.append(re.sub("/", "", result_segmentation)) 
                    '''
                    有些資料沒有mainText的資料，所以從"result_segmentation"取。
                    '''
        except Exception as e:
            print(f"Failed: {e}")

    return  MText

def sentenceFilter(inputSTR, targetSTR="罪"):
    '''
    inputSTR: str,"梅有仁犯詐欺取財罪，共計伍罪，各處有期徒刑伍月，如易科罰金，均以新臺幣壹仟元折算壹日......。",
    targetSTR: str, "罪" or "處",
    input: sentenceFilter(MTtext,"罪"),
    output: list of string, ["梅有仁犯業務過失致人於死罪"]
    '''
    removePat = re.compile("[\u4E00-\u9FFF\d]")
    punctuation = "".join(set(removePat.sub("", inputSTR)))
    escaped_punctuation = re.escape(punctuation)
    if not escaped_punctuation: 
        escaped_punctuation = " "  
        
    puncPat = re.compile(f"[{escaped_punctuation}]")
    inputLIST = puncPat.split(inputSTR)

    resultLIST = []
    for input in inputLIST:
        if targetSTR in input:                                
            resultLIST.append(input)
    return resultLIST

def before_pat(resultLIST,target_i=0):
    '''
    resultLIST: list of string,['梅有仁犯業務過失致人於死罪','處有期徒刑伍月'],
    target_i: int, 0:罪, 1:處, 取"罪"的句子target_i=0; 要取"處"的句子target_i=1,
    input: before_pat(resultLIST, 0),
    output: list of string, ["梅有仁犯業務過失致人於死罪"]
    '''
    target_utt= []
    for sublist in resultLIST:
        if sublist:
            data=sublist[target_i]
            target_utt.append(data)
    return target_utt

def articut_text(target_utt):  
    '''
    target_utt: list of string, ["梅有仁犯業務過失致人於死罪"],
    input: articut_text(target_utt),
    output: list of string, "<ENTITY_person>梅有仁</ENTITY_person><ACTION_verb>犯</ACTION_verb><ENTITY_nouny>業務過失</ENTITY_nouny><ACTION_verb>致</ACTION_verb><ENTITY_noun>人</ENTITY_noun><FUNC_inner>於</FUNC_inner><ENTITY_nouny>死罪</ENTITY_nouny>"
    '''
    result_pos = []
    retry_delay = 0.8
    for i in target_utt:
        resultDICT = articut(i)
        if "result_pos" in resultDICT:
            result_pos.append(resultDICT["result_pos"])
        else:
            print("Key 'result_pos' not found in resultDICT:", resultDICT)
        time.sleep(retry_delay)
    return sum(result_pos, [])

def pat_to_text(targetPat, result_POS):
    '''
    targetPat: re.compile(str), targetPat = re.compile("((?<=犯</ENTITY_oov)|(?<=[犯結]</ACTION_verb>)|(?<=犯</ENTITY_nouny>)).*(<ENTITY_nouny>[^<]+</ENTITY_nouny>|<ENTITY_oov>罪</ENTITY_oov>|<ENTITY_nounHead>罪</ENTITY_nounHead>)")
    result_POS: List of str, "<ENTITY_person>梅有仁</ENTITY_person><ACTION_verb>犯</ACTION_verb><ENTITY_nouny>業務過失</ENTITY_nouny><ACTION_verb>致</ACTION_verb><ENTITY_noun>人</ENTITY_noun><FUNC_inner>於</FUNC_inner><ENTITY_nouny>死罪</ENTITY_nouny>"
    input: pat_to_text(CrimePat, result_POS)
    output: List of str, ["<ENTITY_nouny>業務過失</ENTITY_nouny><ACTION_verb>致</ACTION_verb><ENTITY_noun>人</ENTITY_noun><FUNC_inner>於</FUNC_inner><ENTITY_nouny>死罪</ENTITY_nouny>"]
    '''
    Matches = list(targetPat.finditer(result_POS))
    if Matches:
        target_pos = Matches[0].group(0)
        return target_pos
    else:
        return ""

def target_result(TargetPat, target_pos): 
    ''' 
    TargetPat: re.compile(str), targetPat = re.compile("((?<=犯</ENTITY_oov)|(?<=[犯結]</ACTION_verb>)|(?<=犯</ENTITY_nouny>)).*(<ENTITY_nouny>[^<]+</ENTITY_nouny>|<ENTITY_oov>罪</ENTITY_oov>|<ENTITY_nounHead>罪</ENTITY_nounHead>)") 
    target_pos: List of string, ["<ACTION_verb>洗錢</ACTION_verb><ENTITY_nouny>防制法</ENTITY_nouny><KNOWLEDGE_lawTW>第十四條第一項</KNOWLEDGE_lawTW><FUNC_inner>之</FUNC_inner><ENTITY_nouny>洗錢罪</ENTITY_nouny>"],
    input: target_result(CrimePat, target_pos)
    output: Dict, {"洗錢防制法第十四條第一項之洗錢罪": "<ACTION_verb>洗錢</ACTION_verb><ENTITY_nouny>防制法</ENTITY_nouny><KNOWLEDGE_lawTW>第十四條第一項</KNOWLEDGE_lawTW><FUNC_inner>之</FUNC_inner><ENTITY_nouny>洗錢罪</ENTITY_nouny>"}
    '''
    Target_dict = {}
    for arti_raw in target_pos:
        TargetSTR = pat_to_text(TargetPat, arti_raw)
        Chinese_text = re.sub(r"[^\u4e00-\u9fff\d]", "", TargetSTR)
        
        pos_result = articut(Chinese_text)
        
        if 'result_pos' in pos_result:
            result_pos = pos_result["result_pos"][0]
        else:
            result_pos = "" 

        if Chinese_text:
            Target_dict[Chinese_text] = result_pos
            
    return Target_dict

def arti_and_save(data, TargetPat, Target_path):    
    ''' 
    data: list of str, ['許見安幫助犯洗錢防制法第十四條第一項之洗錢罪處有期徒刑參月', '項曉岑犯駕駛動力交通工具發生交通事故致人傷害而逃逸罪處有期徒刑陸月'],
    TargetPat: e.g., MergedPat = re.compile("((?<=犯</ENTITY_oov)|(?<=[犯結]</ACTION_verb>)|(?<=犯</ENTITY_nouny>)).*"),
    Target_path: str, Target_path = '../data/MergedALL.json',
    input: arti_and_save(merged_data, MergedPat, Merged_path)
    '''
    Target_posLIST = articut_text(data)
    Target_results = target_result(TargetPat, Target_posLIST)
    with open(Target_path, 'a',encoding='utf8') as file:
        json.dump(Target_results , file, ensure_ascii=False, indent=4)
    return Target_results


s = 2
if __name__ == '__main__':    
    
    file_path = collect_file_path(folder_path,s) #獲取資料夾裡面到.json檔
    results_FMT = get_MainT_save(file_path) #從剛剛得到的檔案中，extract主文並取得內容
    
    sentenceList=[] 
    for texts in results_FMT:
        target_utt = sentenceFilter(inputSTR=texts, targetSTR="罪") + sentenceFilter(inputSTR=texts, targetSTR="處")
        sentenceList.append(target_utt)
        clear_data = [c for c in sentenceList if len(c)== 2 and "罪" in c[0] and "處" in c[1]] #得到target utt list of ['許見安幫助犯洗錢防制法第十四條第一項之洗錢罪', '處有期徒刑參月']
    
    merged_data = [''.join(sublist) for sublist in clear_data] 
    
    #extract 犯(罪名+刑期,人） 
    People_resultsDICT = arti_and_save(merged_data, PeoplePat, People_path)
    
    # extract 罪名+刑期 
    merged_resultsDICT = arti_and_save(merged_data, MergedPat, Merged_path)

    # extract only 罪名
    crime_data= before_pat(clear_data, 0)
    Crime_resultsDICT = arti_and_save(crime_data,CrimePat,Crime_path)

    # extract only 刑期 
    penalty_data = before_pat(clear_data, 1)  
    penalty_resultsDICT = arti_and_save(penalty_data, PenaltyPat, Penalty_path)  
