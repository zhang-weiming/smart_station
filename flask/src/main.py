from flask import Flask
from flask import request
import json
import sys
sys.path.append('/root/work/flaskbackend/smart_station/src')
# sys.path.append('/home/zwm/Workplace/SmartStation/flask/src')
from qa import answer

app = Flask(__name__)

@app.route('/')
def index():
    return 'Welcome, here is QA!'

# 判断新问题
@app.route('/smartQuestion', methods=['POST', 'GET'])
def get_answer():
    question = ''
    if request.method == 'POST':
        question = request.form.get('question', type=str, default='')
    elif request.method == 'GET':
        try:
            question = request.args.get('question')
        except:
            question = ''
    print('[question]', question)
    ans = answer(question.upper())
    # print('\nAnswer:')
    # print(json.loads(ans))
    return ans


if __name__ == '__main__':
    app.run(debug=True)
    # question = input('Input: ')
    # while question != 'EXIT':
    #     answers = answer(question)
    #     print('\nAnswer:')
    #     print(json.loads(answers))
    #     # if len(answers) > 0:
    #     #     a = 1
    #     #     for ans in answers:
    #     #         print( '\t[', a, '] ' + str(ans[0]) )
    #     #         print( '\t' + str(ans[1]).strip() )
    #     #         a += 1
    #     # else:
    #     #     print('\t抱歉，我不太懂您的意思 u.u')
    #     question = input('Input: ')
