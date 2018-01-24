#!/usr/bin/python3
import os
import codecs
# import pynlpir
import jieba
import numpy as np
import math
import pymysql
import platform

NEW_LINE = '\n'

WORD_BANK_FILE_PATH = '../data/WordBank.txt'
STOP_WORD_FILE_PATH = '../data/dict/stop_word_UTF_8.txt'
# STOP_WORD_FILE_PATH = '../data/dict/biao_dian.txt'
DOCS_FILE_PATH = '../data/corpus/questions.txt'
VECTORS_FILE_PATH = '../data/vectors.txt'

user = 'root'
password = 'keyan123'
dbName = 'test_db'
tableName = 'question'

stop_word_list = []
word_bank = []



# def loadDocs(filePath, encoding='utf-8'):
#     f = codecs.open(filePath, 'r', encoding=encoding)
#     content = f.read()
#     f.close()
#     text_list = content.split(NEW_LINE)
#     text_list.remove( text_list[-1] )
#     # for i in range(0, len(text_list)):
#     #     text_list[i] = text_list[i].strip()
#     return text_list

def calLen(vec):
    vec = np.mat(vec)
    num = (float)(vec * vec.T)
    return math.sqrt(num)

def norm(vec):
    vec = np.mat(vec)
    return vec / calLen(vec)

def cosSim(v1, v2):
    v1 = np.mat(v1)
    v2 = np.mat(v2)
    num = (float)(v1 * v2.T)
    return num

# 加载数据
def load_docs_from_db(encoding='utf-8'):
    db = pymysql.connect("localhost", user, password, dbName, charset='utf8') # 连接数据库
    cursor = db.cursor() # 建立游标
    sql = 'select id, question from %s;'
    cursor.execute(sql % tableName) # 执行查询
    textList = list()
    for row in cursor.fetchall():
        row = list(row)
        row[1] = jieba.lcut(row[1])
        textList.append( row )
    return textList

def load_docs_from_file(encoding='utf-8'):
    fr = codecs.open(DOCS_FILE_PATH, 'r', encoding=encoding)
    content = fr.read()
    fr.close()
    q_list = content.split(NEW_LINE)
    q_list.pop()
    for i in range(len(q_list)):
        q_list[i] = q_list[i].strip()
    return q_list


# '''
# 建立词库
def build_word_bank(doc_list):
    # pynlpir.open()
    word_bank = set()
    for doc in doc_list: # 遍历每一个文档
        # segment = pynlpir.segment(doc, pos_tagging=False)
        segment = jieba.lcut(doc)
        for word in segment:
            word = word.strip()
            if word not in stop_word_list: # 停用词
                word_bank.add(word) # 加入set中
    fw = codecs.open(WORD_BANK_FILE_PATH, 'w', encoding='utf-8')
    for word in word_bank:
        fw.write(word + NEW_LINE)
    fw.close()
    print('writting finished')
    # pynlpir.close()


# 加载词库
def load_word_bank():
    fr = codecs.open(WORD_BANK_FILE_PATH, 'r', encoding='utf-8')
    content = fr.read()
    fr.close()
    word_bank = content.split(NEW_LINE)
    word_bank.pop()
    for i in range(len(word_bank)):
        word_bank[i] = word_bank[i].strip()
    return word_bank

# 文本表示，词袋模型
def bow(doc_list):
    # pynlpir.open()
    fw = codecs.open(VECTORS_FILE_PATH, 'w', 'utf-8')
    id = 1
    for doc in doc_list:
        # segment = pynlpir.segment(doc, pos_tagging=False) # 分词
        segment = jieba.lcut(doc) # 分词
        j = 0
        while j < len(segment):
            if segment[j] in word_bank:
                segment[j] = word_bank.index( segment[j] ) # 把每个词都替换成对应的id（词袋中的索引值）
                j += 1 # 指针后移
            else:
                segment.pop(j) # 词库中没有该词，抛弃
    # for i in range(0, len(textList)): # 遍历每一个文档
        # doc = textList[i]
        words = list(set(segment))
        words.sort()
        temp_vector = '' # 向量字符串
        vector_len = 0 # 向量的模
        for word in words: # 遍历一个文档中的所有词语，计算向量所有参数的平方和
            vector_len += math.pow(segment.count(word), 2)
        vector_len = math.sqrt(vector_len)
        for word in words: # 遍历一个文档中的所有词语，整理向量字符串
            temp_vector += str(word) + ':' + str( segment.count(word) / vector_len ) + ' '
        # textList[i][1] = tempVector.strip() # 去掉字符串前后空格
        line = '%d|%s' % (id, temp_vector.strip()) + NEW_LINE
        # print(line)
        # exit(0)
        fw.write(line)
        print('writed', id)
        id += 1
        # print('vectorLen', vectorLen, '\nvector', textList[i])
    fw.close()
    # pynlpir.close()
    print('Done!')
    # return textList

# # 保存到数据库
# def save(textList):
#     db = pymysql.connect("localhost", user, password, dbName, charset='utf8') # 连接数据库
#     cursor = db.cursor() # 建立游标
#     a = 1
#     for doc in textList: # 遍历每一个文档
#         sql = "update question set vector='" + doc[1] + "' where id=" + str(doc[0]) + ";"
#         state = cursor.execute(sql) # 执行更新操作
#         print('update', a, 'state', state)
#         a += 1
#     db.commit() # 提交操作
#     cursor.close()
#     db.close()
    
# 加载停用词
def load_TYC():
    fr = codecs.open(STOP_WORD_FILE_PATH, 'r', encoding='utf-8')
    content = fr.read()
    fr.close()
    stop_word_list = content.split(NEW_LINE)
    stop_word_list.pop()
    stop_word_list.remove( stop_word_list[-1] )
    for i in range(0, len(stop_word_list)):
        stop_word_list[i] = stop_word_list[i].strip()
    return stop_word_list


# # 去停用词
# def quTYC(text_list, flag_list, stop_word_list):
#     for i in range(0, len(text_list)):
#         j = 0
#         while j < len(text_list[i][-1]):
#             # word = text_list[i][-1][j]
#             if text_list[i][-1][j] in stop_word_list:
#                 text_list[i][-1].remove( text_list[i][-1][j] )
#                 flag_list[i].remove( flag_list[i][j] )
#             else:
#                 j += 1
#         print('quTYC', i)
#     return text_list, flag_list
# '''

stop_word_list = load_TYC() # 加载停用词

# 入口
if __name__ == '__main__':
    # wordBank = loadWordBank()
    # # 建立词库
    # stopWordList = loadTYC()
    # buildWordBank()
    # 文本表示，并保存到数据库
    # textList = bow()
    # save(textList)
    

    doc_list = load_docs_from_file()
    # build_word_bank(doc_list) # 建立词库
    
    word_bank = load_word_bank() # 文本表示
    # print(doc_list)
    bow(doc_list)
