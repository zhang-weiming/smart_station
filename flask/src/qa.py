import codecs
# import pynlpir
import jieba
import numpy as np
import math
import pymysql
import json
import random

NEW_LINE = '\n'

BASE_DIR_PATH = ''
WORD_BANK_FILE_PAYH = '../data/WordBank.txt'
VECTORS_FILE_PAYH = '../data/vectors.txt'
STOP_WORD_FILE_PATH = '../data/dict/stop_word_UTF_8.txt'
USER_DICT_FILE_PATH = '../data/user_dict_word.txt'

host = '47.94.111.175'
user = 'school'
password = 'school123123.'
database = 'railwayquestion'
table_question = 'question'

word_bank = []
vectors = []
stop_word_list = []
place_dict = {
    '出租':'#1', 
    '公交':'#2', 
    '地铁':'#3', 
    '停用场':'#4', 
    '租车公司':'#5', 
    '旅行社':'#6', 
    '当地景点':'#7', 
    '检票口':'#8', 
    '服务台':'#9', 
    '餐饮':'#10', 
    '寄存处':'#11', 
    '商店':'#12', 
    '厕所':'#13', 
    '开水':'#14'
}

# 求一个向量的模长
def calLen(vec):
    vec = np.mat(vec)
    num = (float)(vec * vec.T)
    return math.sqrt(num)
# 对向量单位化
def norm(vec):
    vec = np.mat(vec)
    vecLen = calLen(vec)
    if vecLen > 0:
        vec = vec / vecLen
    return vec
# 求余弦距离
def cos_sim(v1, v2):
    v1 = np.mat(v1)
    v2 = np.mat(v2)
    num = (float)(v1 * v2.T)
    return num

# 加载词库
def load_word_bank(filePath):
    fr = codecs.open(filePath, 'r', encoding='utf-8')
    content = fr.read()
    fr.close()
    word_bank = content.split(NEW_LINE)
    word_bank.pop()
    # word_bank.remove( word_bank[-1] )
    for i in range(len(word_bank)):
        word_bank[i] = word_bank[i].strip()
    return word_bank

# 加载停用词
def load_TYC():
    fr = codecs.open(STOP_WORD_FILE_PATH, 'r', encoding='utf-8')
    content = fr.read()
    fr.close()
    stop_word_list = content.split(NEW_LINE)
    stop_word_list.remove( stop_word_list[-1] )
    for i in range(0, len(stop_word_list)):
        stop_word_list[i] = stop_word_list[i].strip()
    return stop_word_list

def ask_place(segment):
    for key in place_dict:
        if key in segment:
            ans_dict = dict()
            ans_dict['question'] = key
            ans_dict['answer'] = place_dict[key]
            ans_str = json.dumps(ans_dict, ensure_ascii=False)
            return True, ans_str
    return False, ''

# 给问题question匹配合适的答案
def answer(question):
    # t1 = time.time()
    # pynlpir.open()
    # segment = pynlpir.segment(question, pos_tagging=False) # 分词 
    # pynlpir.close()
    jieba.load_userdict(USER_DICT_FILE_PATH)
    segment = jieba.lcut(question, cut_all=True)
    print('[segment]', segment)
    is_place, place = ask_place(segment)
    if is_place:
        return place
    else:
        i = 0
        # 把每个词都替换成对应的id，词库中没有则抛弃
        while i < len(segment):
            if segment[i] in stop_word_list:
                segment.pop(i)
            else:
                if segment[i] in word_bank:
                    # 把每个词都替换成对应的id
                    segment[i] = word_bank.index( segment[i] )
                    i += 1
                else:
                    # 词库中没有该词，替换可能的近义词
                    synonym = proc_synonym(segment[i])
                    print('\t[proc_synonym]',segment[i], '->',  synonym)
                    if len(synonym) > 0:
                        segment[i] = word_bank.index( synonym[random.randint(0, len(synonym) - 1)] )
                        i += 1
                    else:
                        segment.pop(i)
        # 将问题文本表示为向量
        words = list(set(segment))
        words.sort()
        vector = [0 for ii in range(0, len(word_bank))]
        for word in words:
            vector[word] = segment.count(word)
        s = '[vector]'
        for v in range(len(vector)):
            if vector[v] > 0:
                s += str(v) + ' '
        print(s)
        # if calLen(vector) > 0:
        vector = norm(vector) # 问题文本的向量
        # 计算 该问题向量 和 所有已知问题向量 的余弦相似度
        sims = []
        for doc in vectors:
            vec = doc[1]
            sim = cos_sim(vector, vec) # 计算余弦距离
            sims.append(sim)
            # if sim > maxSim:
            #     maxSim = sim # 更新最近问题的余弦距离
            #     indexOfSim = doc[0] # 最近问题的id（此处变量类型为字符串，便于组织sql语句）
        index_list = []
        ans_cnt = len(sims) - sims.count(0)
        # 非零的相似度距离分数 按 三个以上 和 以下 分类处理
        if ans_cnt > 2:
            ans_cnt = 3
        for i in range(0, ans_cnt):
            maxIdx = sims.index( max(sims) ) # 当前最大值的索引
            sims[maxIdx] = 0 # 当前最大值归零，相当于删除该值
            index_list.append(maxIdx + 1) # 记录当前最大值的索引值 + 1，加1 是因为数据库中的id比这里的索引值大1
        print('MaxSimIndex_list', index_list)
        if len(index_list) > 0:
            answers = get_answers_from_db(index_list)
            for i in range(0, len(answers)):
                ans = answers[i]
                ans_json = dict() # 近义问题与答案的dict，方便后面转换为json格式
                ans_json['question'] = str(ans[0]).strip()
                ans_json['answer'] = str(ans[1]).strip()
                answers[i] = ans_json
                ans_str = json.dumps(answers, ensure_ascii=False)
                # print('[qa]', ans_str)
            return ans_str # 以json格式返回结果
        else:
            # 没有找到答案，返回空
            return str(json.dumps([]))

# 从数据库中获取 特定id 的问题-答案集
def get_answers_from_db(index_list):
    # t1 = time.time()
    db = pymysql.connect(host=host, user=user, password=password, database=database, charset='utf8') # 连接数据库
    cursor = db.cursor() # 建立游标
    answers = []
    for index in index_list:
        sql = "select question, answer from %s where id=%d;" % (table_question, index)
        cursor.execute(sql) # 执行查询
        ans = cursor.fetchone()
        answers.append(ans)
    # 关闭数据库连接
    cursor.close()
    db.close()
    # print('\t[getAnswers]', time.time() - t1)
    return answers

# 读取向量
# 参数 word_bank_len ，是词库的长度
def load_vectors(word_bank_len):
    try:
        fr = codecs.open(VECTORS_FILE_PAYH, 'r', encoding='utf-8')
        content = fr.read() # 读文件
    except IOError:
        print('[Error] 读取词库文件失败')
        return []
    else:
        fr.close() # 关闭文件
    vectors = content.split(NEW_LINE) # 按行分割
    vectors.pop() # 去掉末尾的空元素
    for i in range(0, len(vectors)):
        vector_info = vectors[i].strip()
        vector_info = vector_info.split('|') # [id, 'index:value ...'] 具体结构参考 ../data/vectors.txt
        temp_vector = [0 for i in range(0, word_bank_len)]
        parts = vector_info[1].split(' ')
        for part in parts:
            indexAndNum = part.split(':')
            temp_vector[int(indexAndNum[0])] = float(indexAndNum[1]) # 整理向量各维度参数
        vector_info[1] = temp_vector
        vectors[i] = vector_info # （覆盖）保存为 vectors 中的第 i 个元素
    return vectors

# 可能近义词处理
def proc_synonym(word):
    word = list(word)
    words = []
    flag = False
    for w in word:
        for ww in word_bank:
            if w in ww:
                words.append(ww)
                flag = True
                break
        if flag:
            break
    return words
def loadWordVec():
    pass


word_bank = load_word_bank(WORD_BANK_FILE_PAYH) # 加载词库
vectors = load_vectors(len(word_bank)) # 加载已知问题的向量
stop_word_list = load_TYC() # 加载停用词
jieba.lcut('test')

# 入口
if __name__ == '__main__':
    # 判断新问题
    question = input('Input: ')
    while question != 'EXIT':
        answers = answer(question.upper())
        print('Answer:', answers)
        print()
        # for ans in answers:
        #     print(ans)
        question = input('Input: ')
