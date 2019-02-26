# coding:utf-8
from flask import Flask, url_for, render_template, Markup, jsonify, request,Response,Markup
import sqlite3
import os
import itertools
import numpy as np
import pandas as pd
import random
import gc

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.jinja_env.globals['static'] = (
    lambda filename: url_for('static', filename = filename)
)

# load word database
all_word_data = pd.read_csv('static/words.csv',encoding='gbk')
word_column_all = list(all_word_data.columns)
word_column_all_tips = {'Word': u'词',
'W_Length': u'词长',
'W_TotalStrokes': u'总笔画',
'W_Count': u'词频（来自SUBTLEX-CH）【2】',
'W(log)': u'词频的log10对数（来自SUBTLEX-CH）【2】',
'W_million': u'每百万的词频（来自SUBTLEX-CH）【2】',
'W_CD': u'出现该词的影片数量（来自SUBTLEX-CH）【2】',
'W_CD(ratio)': u'出现该词的影片百分比（来自SUBTLEX-CH）【2】',
'W_CD(log)': u'出现该词的影片数量的log10对数（来自SUBTLEX-CH）【2】'
}
word_column_all_tip = [word_column_all_tips[col] for col in word_column_all]

# load character database
con = sqlite3.connect('static/hanzi.db')
all_char_data = pd.read_sql('select * from hanzi',con=con)
# all_char_data[['CHR_Count', 'CHR_CD(log)', 'CHR(log)', 'CHR_CD', 'CHR_CD(ratio)', 'CHR_million']] = all_char_data[[
#     'CHR_Count', 'CHR_CD(log)', 'CHR(log)', 'CHR_CD', 'CHR_CD(ratio)', 'CHR_million']].fillna(0)
for num_attr in ['TotalStrokes', 'RadicalStrokes', 'CHR_Count', 'CHR_CD(log)', 'CHR(log)', 'CHR_CD', 'CHR_CD(ratio)', 'CHR_million', 'Freq(Unihan)', 'Freq(tmcn)', 'Freq(TGH)', 'GradeLevel']:
    all_char_data[num_attr] = pd.to_numeric(
        all_char_data[num_attr], errors='coerce')
char_column_all = list(all_char_data.columns)
char_column_all_tips = {'Unicode': u'Unicode编码【1】',
'Character': u'汉字【1】',
'Pinyin': u'拼音【4】',
'Pinyin_flat': u'拼音（声调以数字表示）',
'TotalStrokes': u'笔画数【1】',
'Radical': u'部首【5】',
'RadicalStrokes': u'部首笔画【由Radical和TotalStrokes生成】',
'Stroke_Order': u'笔画顺序（点丶横一竖丨斜ノ折フ）【4】',
'Stroke_Order2': u'笔画顺序（点4横1竖2斜3折5）【5】',
'Structure': u'字形结构【4】',
'Definition': u'英文释义【1】',

'CHR_Count': u'字频（来自SUBTLEX-CH，包含常用字）【2】',
'CHR_million': u'每百万字的字频（来自SUBTLEX-CH，包含常用字）【2】',
'CHR(log)': u'字频的log10对数（来自SUBTLEX-CH，包含常用字）【2】',
'CHR_CD': u'出现该字的影片数量（来自SUBTLEX-CH，包含常用字）【2】',
'CHR_CD(log)': u'出现该字的影片数量的log10对数（来自SUBTLEX-CH，包含常用字）【2】',
'CHR_CD(ratio)': u'出现该字的影片百分比（来自SUBTLEX-CH，包含常用字）【2】',

'Freq(Unihan)': u'字频（来自Unihan）【1】',
'Freq(tmcn)': u'字频（来自tmcn，包含所有汉字）【4】',
'Freq(TGH)': u'在《通用规范汉字表》的位置(level1:常用字，level2:二级字表，level3:三级字表)【7】',
'GradeLevel': u'《朗文初級中文詞典》的分级【1】',

'Component': u'汉字部件构造【5】',
'Start&End': u'首尾分解查字【5】',
'IDS1st': u'表意文字描述序列（Ideographic Description Sequences）（原始）【3】',
'IDS2nd': u'表意文字描述序列（Ideographic Description Sequences）（第二次分解）【由IDS1st生成】',
'IDS3rd': u'表意文字描述序列（Ideographic Description Sequences）（第三次分解）【由IDS2nd生成】',
'Formation': u'汉字结构/六书【6】',
'Outline': u'字体信息',

'ToGB': u'对应简体字【5】',
'ToBIG5': u'对应繁体字【5】',
'ToOdd': u'对应异体字【5】',

'Simplified': u'简体字形式【1】',
'Traditional': u'繁体字形式【1】',
'SemanticVariant': u'语义相同的异体字形式1【1】',
'SpSemanticVariant': u'语义重合的异体字形式2【1】',
'ZVariant': u'拼写变形的异体字形式3【1】',

'UTF8': u'UTF-8编码',
'Wubi86': u'五笔86【5】',
'Wubi98': u'五笔98【5】',
'Cangjie': u'仓颉码【1】',
'FourCornerCode': u'四角码【1】',

'kMandarin': u'常见的发音拼音【1】',
'kXHC1983': u'《现代汉语词典》给出的拼音【1】',
'kHanyuPinlu': u'《现代汉语频率词典》给出的拼音和频率【1】',
'kCantonese': u'广东话发音【1】',
'kJapaneseKun': u'日语训读【1】',
'kJapaneseOn': u'日语音读【1】',
'kKorean': u'韩语发音【1】',
}

char_column_all_tip = [char_column_all_tips[col] for col in char_column_all]

char_loc = dict()
for ind,ch in enumerate(all_char_data['Character']):
    char_loc[ch] = ind

def filter_in_df(data,filters):
    for f in filters:
        component = f.split(',')
        if component[0]=='true' and (component[4]!='' or component[3]== u'是空的/nan'):
            a = component[1] # target
            op = component[3] # operator
            b = component[4]
            if op == u'等于':
                if (a != 'Unicode') and b.isdigit():
                    condition = data[a]==int(b)
                else:
                    condition = data[a]==b
            elif op == u'大于':
                b = int(b)
                condition = data[a]>b
            elif op == u'小于':
                b = int(b)
                condition = data[a]<b
            elif op == u'包含':
                condition = data[a].str.contains(b)
            elif op == u'在列表中':
                try:
                    b = b.split('&')+[int(i) for i in b.split('&')]
                except:
                    b = b.split('&')
                condition = data[a].isin(b)
            elif op == u'开始于':
                condition = data[a].str.startswith(b)
            elif op == u'结束于':
                condition = data[a].str.endswith(b)
            elif op == u'是空的/nan':
                condition = data[a].isnull()
            if component[2]=='true': # not
                condition = ~condition
            data = data[condition]
    return data 

def filter(raw_data,query):
    if ';' in query:
        filters = query.split(';')
    else:
        filters = [query]

    return filter_in_df(raw_data,filters)

markup = lambda x: Markup('"'+','.join(x)+'"')

@app.route('/')
@app.route('/char_query')
def load_char_query_page():
    logger.debug("new access")

    char_column_selected = ['Unicode','Character','Pinyin_flat','TotalStrokes','Radical','Freq(Unihan)']
    page = render_template('char_query.html',
        char_column_selected = markup(char_column_selected),
        char_column_all = markup(char_column_all),
        char_column_all_tip = markup(char_column_all_tip),
        title='Chinese Character Database - Query character') 
    return page

@app.route('/word_query')
def load_word_query_page():
    word_column_selected = ['W_Count']
    
    char_column_selected = ['Character','Pinyin_flat','TotalStrokes','Freq(Unihan)']
    page = render_template('word_query.html',
        word_column_selected = markup(word_column_selected),
        word_column_all = markup(word_column_all),
        word_column_all_tip = markup(word_column_all_tip),
        char_column_selected = markup(char_column_selected),
        char_column_all = markup(char_column_all),
        char_column_all_tip = markup(char_column_all_tip),
        title='Chinese Character Database - Query word') 
    return page

@app.route('/get_columns_of_word_query', methods=['POST'])
def get_columns_of_word_query():
    word_column_selected = request.form['word_column_selected'].split(',')
    char_column_selected = request.form['char_column_selected'].split(',')
    data_filtered = filter(all_word_data, request.form['filter'])

    char_n = data_filtered['W_Length'].max()
    columns_name = ['Word'] + word_column_selected + ['%s_%d' %(n,i) for i in range(char_n) for n in char_column_selected]

    return markup(columns_name)

@app.route('/view_change_on_word_query', methods=['POST'])
def view_change_on_word_query(): # paging at the beginning, so the sort doesn't work well
    word_column_selected = request.form['word_column_selected'].split(',')
    char_column_selected = request.form['char_column_selected'].split(',')

    start = int(request.form['start'])
    length = int(request.form['length'])

    order = 1 if request.form['order[0][dir]']=='asc' else 0
    sort_target = int(request.form['order[0][column]'])

    data_filtered = filter(all_word_data, request.form['filter'])
    if 0<sort_target<(len(word_column_selected)+1): # default: keep the word list order
        data_filtered = data_filtered.sort_values(word_column_selected[sort_target-1], ascending=[order])

    processed = []
    for ind,row in data_filtered.iloc[start:start+length-1].iterrows():
        word = row['Word']
        try:
            ws = list(row[word_column_selected])

        except:
            ws = [0 for i in word_column_selected]

        chs = [all_char_data.loc[char_loc[ch]][
                char_column_selected].values.tolist() 
                  for ch in word if u'\u4e00' <= ch <= u'\u9fff']
        
        processed.append([word]+ws+list(itertools.chain(*chs)))

    processed = pd.DataFrame(processed)
    processed = processed.where((pd.notnull(processed)), None) # replace 'NaN' with None 

    page = jsonify(recordsTotal=len(all_word_data),recordsFiltered=len(data_filtered),
        data=processed.values.tolist()) 
 
    return page

@app.route('/view_change_on_word_analysis', methods=['POST'])
def view_change_on_word_analysis(): # paging at the end
    word_column_selected = request.form['word_column_selected'].split(',')
    char_column_selected = request.form['char_column_selected'].split(',')

    start = int(request.form['start'])
    length = int(request.form['length'])

    order = 1 if request.form['order[0][dir]']=='asc' else 0
    sort_target = int(request.form['order[0][column]'])

    words = request.form['words'].split(',')

    processed = []
    for word in words:
        try:
            ws = all_word_data[all_word_data['Word'] == word][word_column_selected].values[0].tolist()
        except:
            ws = [0 for i in word_column_selected]
        chs = [all_char_data.loc[char_loc[ch]][
                char_column_selected].values.tolist()
                  for ch in word if u'\u4e00' <= ch <= u'\u9fff']
        processed.append([word]+ws+list(itertools.chain(*chs)))

    processed = pd.DataFrame(processed)
    processed = processed.where((pd.notnull(processed)), None) # replace 'NaN' with None 
    if sort_target>0: # default: keep the word list order
        processed = processed.sort_values(sort_target, ascending=[order])

    page = jsonify(recordsTotal=len(all_word_data),recordsFiltered=len(processed),
        data=processed.iloc[start:start+length-1].values.tolist()) 
 
    return page

@app.route('/view_change_char_query', methods=['POST'])
def view_change_char_query():
    char_column_selected = request.form['char_column_selected'].split(',')
    start = int(request.form['start'])
    length = int(request.form['length'])

    order = 1 if request.form['order[0][dir]']=='asc' else 0
    sort_target = int(request.form['order[0][column]'])
    sort_target = char_column_selected[sort_target]

    try:
        data_filtered = filter(all_char_data, request.form['filter'])[char_column_selected]
        data = data_filtered.sort_values(sort_target, ascending=[order])
        data = data.astype(str)
        page = jsonify(recordsTotal=len(all_char_data),recordsFiltered=len(data),
            data=data.iloc[start:start+length-1].values.tolist())
        return page
    except Exception as e:
        print(e)
        return 'invalid'

@app.route('/char_query/getExcel',methods=['POST'])
def get_char_query_file():
    char_column_selected = request.form['char_column_selected'].split(',')

    data_filtered = filter(all_char_data, request.form['filter'])

    filename = str(random.randint(1000,9999))
    if 'Unicode' in data_filtered.columns:
        data_filtered['Unicode'] = data_filtered['Unicode'].astype(str) # stringify "Unicode" column
    data_filtered[char_column_selected].to_csv('static/%s.csv' %filename,index=False, encoding='gbk')

    del data_filtered 
    return filename

@app.route('/word_query/getExcel',methods=['POST'])
def get_word_query_file():
    word_column_selected = request.form['word_column_selected'].split(',')
    char_column_selected = request.form['char_column_selected'].split(',')
    processed = []

    try:
        data_filtered = filter(all_word_data, request.form['filter'])
        if len(data_filtered)>4000:
            return '0'
        for ind,row in data_filtered.iterrows():
            word = row['Word']
            try:
                ws = list(row[word_column_selected])

            except:
                ws = [0 for i in word_column_selected]

            chs = [all_char_data.loc[char_loc[ch]][
                    char_column_selected].values.tolist() 
                      for ch in word if u'\u4e00' <= ch <= u'\u9fff']
            
            processed.append([word]+ws+list(itertools.chain(*chs)))
    except:
        words = request.form['words'].split(',')
        if len(words)>4000:
            return '0'
        for word in words:
            try:
                ws = all_word_data[all_word_data['Word'] == word][word_column_selected].values[0].tolist()
            except:
                ws = [0 for i in word_column_selected]

            chs = [all_char_data.loc[char_loc[ch]][
                    char_column_selected].values.tolist() 
                      for ch in word]
            processed.append([word]+ws+list(itertools.chain(*chs)))

    processed = pd.DataFrame(processed)
    processed = processed.where((pd.notnull(processed)), None) # replace 'NaN' with None 
    filename = str(random.randint(1000,9999))

    char_n = (len(processed.columns) - len(word_column_selected) - 1)//len(char_column_selected)
    processed.columns = ['Word'] + word_column_selected + ['%s_%d' %(n,i) for i in range(char_n) for n in char_column_selected]

    for col_name in processed.columns:
        if 'Unicode' in col_name:
            processed[col_name] = processed[col_name].astype(str) # stringify "Unicode" column

    processed.to_csv('static/%s.csv' %filename,index=False, encoding='gbk')
    del processed 
    return filename


@app.route('/download/<filename>')
def download(filename):
    path = 'static/%s.csv' %filename
    response = Response()
    response.status_code = 200
    response.headers['Content-Description'] = 'File Transfer'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename=export.csv'
    response.headers['Content-Length'] = os.path.getsize(path)
    with open(path, 'rb') as f:
        response.data = f.read()
    os.remove(path)
    return response

if __name__ == '__main__':
    app.debug = True
    app.run()
