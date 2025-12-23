
# coding:utf-8
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from markupsafe import Markup
from starlette.background import BackgroundTask
import sqlite3
import itertools
import pandas as pd
import random
from pathlib import Path

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
TEMPLATE_DIR = BASE_DIR / 'templates'

app = FastAPI()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.globals['static'] = lambda filename: f"/static/{filename}"
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

WORDS_PATH = STATIC_DIR / 'words.csv'
HANZI_DB_PATH = STATIC_DIR / 'hanzi.db'

# load word database
all_word_data = pd.read_csv(str(WORDS_PATH), encoding='gbk')
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
with sqlite3.connect(str(HANZI_DB_PATH)) as con:
    all_char_data = pd.read_sql('select * from hanzi', con=con)
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
for ind, ch in enumerate(all_char_data['Character']):
    char_loc[ch] = ind


def filter_in_df(data, filters):
    for f in filters:
        component = f.split(',')
        if component[0] == 'true' and (component[4] != '' or component[3] == u'是空？nan'):
            a = component[1]
            op = component[3]
            b = component[4]
            if op == u'等于':
                if (a != 'Unicode') and b.isdigit():
                    b = int(b)
                data = data[data[a] == b]
            elif op == u'不等于':
                if (a != 'Unicode') and b.isdigit():
                    b = int(b)
                data = data[data[a] != b]
            elif op == u'大于':
                data = data[data[a] > float(b)]
            elif op == u'大于等于':
                data = data[data[a] >= float(b)]
            elif op == u'小于':
                data = data[data[a] < float(b)]
            elif op == u'小于等于':
                data = data[data[a] <= float(b)]
            elif op == u'包含':
                data = data[data[a].astype(str).str.contains(b)]
            elif op == u'不包含':
                data = data[~data[a].astype(str).str.contains(b)]
            elif op == u'是空？nan':
                data = data[data[a].isnull()]
            elif op == u'不是空？nan':
                data = data[~data[a].isnull()]
    return data


def apply_filters(raw_data, query):
    if not query:
        return raw_data
    filters = query.split(';') if ';' in query else [query]
    return filter_in_df(raw_data, filters)


markup = lambda x: Markup('"' + ','.join(x) + '"')


@app.get('/')
@app.get('/char_query')
async def load_char_query_page(request: Request):
    logger.debug('new access')
    char_column_selected = ['Unicode', 'Character', 'Pinyin_flat', 'TotalStrokes', 'Radical', 'Freq(Unihan)']
    context = {
        'request': request,
        'char_column_selected': markup(char_column_selected),
        'char_column_all': markup(char_column_all),
        'char_column_all_tip': markup(char_column_all_tip),
        'title': 'Chinese Character Database - Query character',
    }
    return templates.TemplateResponse('char_query.html', context)


@app.get('/word_query')
async def load_word_query_page(request: Request):
    word_column_selected = ['W_Count']
    char_column_selected = ['Character', 'Pinyin_flat', 'TotalStrokes', 'Freq(Unihan)']
    context = {
        'request': request,
        'word_column_selected': markup(word_column_selected),
        'word_column_all': markup(word_column_all),
        'word_column_all_tip': markup(word_column_all_tip),
        'char_column_selected': markup(char_column_selected),
        'char_column_all': markup(char_column_all),
        'char_column_all_tip': markup(char_column_all_tip),
        'title': 'Chinese Character Database - Query word',
    }
    return templates.TemplateResponse('word_query.html', context)


def _split_csv(value):
    value = value or ''
    return [item for item in value.split(',') if item]


@app.post('/get_columns_of_word_query')
async def get_columns_of_word_query(request: Request):
    form = await request.form()
    word_column_selected = _split_csv(form.get('word_column_selected', ''))
    char_column_selected = _split_csv(form.get('char_column_selected', ''))
    data_filtered = apply_filters(all_word_data, form.get('filter', ''))
    char_n = data_filtered['W_Length'].max()
    columns_name = ['Word'] + word_column_selected + ['%s_%d' % (n, i) for i in range(char_n) for n in char_column_selected]
    return PlainTextResponse(str(markup(columns_name)))


def _get_sorting(form):
    ascending = form.get('order[0][dir]', 'asc') == 'asc'
    try:
        sort_target = int(form.get('order[0][column]', 0))
    except ValueError:
        sort_target = 0
    return ascending, sort_target


@app.post('/view_change_on_word_query')
async def view_change_on_word_query(request: Request):
    form = await request.form()
    word_column_selected = _split_csv(form.get('word_column_selected', ''))
    char_column_selected = _split_csv(form.get('char_column_selected', ''))
    start = int(form.get('start', 0) or 0)
    length = int(form.get('length', 0) or 0)
    ascending, sort_target = _get_sorting(form)
    data_filtered = apply_filters(all_word_data, form.get('filter', ''))
    if 0 < sort_target < (len(word_column_selected) + 1):
        data_filtered = data_filtered.sort_values(word_column_selected[sort_target - 1], ascending=[ascending])
    processed = []
    for _, row in data_filtered.iloc[start:start + length - 1].iterrows():
        word = row['Word']
        try:
            ws = list(row[word_column_selected])
        except Exception:
            ws = [0 for _ in word_column_selected]
        chs = [all_char_data.loc[char_loc[ch]][char_column_selected].values.tolist()
               for ch in word if u'一' <= ch <= u'鿿']
        processed.append([word] + ws + list(itertools.chain(*chs)))
    processed_df = pd.DataFrame(processed)
    processed_df = processed_df.where(pd.notnull(processed_df), None)
    return JSONResponse({
        'recordsTotal': len(all_word_data),
        'recordsFiltered': len(data_filtered),
        'data': processed_df.values.tolist(),
    })


@app.post('/view_change_on_word_analysis')
async def view_change_on_word_analysis(request: Request):
    form = await request.form()
    word_column_selected = _split_csv(form.get('word_column_selected', ''))
    char_column_selected = _split_csv(form.get('char_column_selected', ''))
    start = int(form.get('start', 0) or 0)
    length = int(form.get('length', 0) or 0)
    ascending, sort_target = _get_sorting(form)
    words = _split_csv(form.get('words', ''))
    processed = []
    for word in words:
        try:
            ws = all_word_data[all_word_data['Word'] == word][word_column_selected].values[0].tolist()
        except Exception:
            ws = [0 for _ in word_column_selected]
        chs = [all_char_data.loc[char_loc[ch]][char_column_selected].values.tolist()
               for ch in word if u'一' <= ch <= u'鿿']
        processed.append([word] + ws + list(itertools.chain(*chs)))
    processed_df = pd.DataFrame(processed)
    processed_df = processed_df.where(pd.notnull(processed_df), None)
    if sort_target > 0:
        processed_df = processed_df.sort_values(sort_target, ascending=[ascending])
    page = processed_df.iloc[start:start + length - 1]
    return JSONResponse({
        'recordsTotal': len(all_word_data),
        'recordsFiltered': len(processed_df),
        'data': page.values.tolist(),
    })


@app.post('/view_change_char_query')
async def view_change_char_query(request: Request):
    form = await request.form()
    char_column_selected = _split_csv(form.get('char_column_selected', ''))
    start = int(form.get('start', 0) or 0)
    length = int(form.get('length', 0) or 0)
    ascending, sort_target = _get_sorting(form)
    try:
        sort_column = char_column_selected[sort_target]
        data_filtered = apply_filters(all_char_data, form.get('filter', ''))[char_column_selected]
        data = data_filtered.sort_values(sort_column, ascending=[ascending])
        data = data.astype(str)
        subset = data.iloc[start:start + length - 1]
        return JSONResponse({
            'recordsTotal': len(all_char_data),
            'recordsFiltered': len(data),
            'data': subset.values.tolist(),
        })
    except Exception as exc:
        logger.error('char query failed: %s', exc)
        return PlainTextResponse('invalid', status_code=400)


def _stringify_unicode_columns(dataframe):
    for col_name in dataframe.columns:
        if 'Unicode' in col_name:
            dataframe[col_name] = dataframe[col_name].astype(str)


@app.post('/char_query/getExcel')
async def get_char_query_file(request: Request):
    form = await request.form()
    char_column_selected = _split_csv(form.get('char_column_selected', ''))
    data_filtered = apply_filters(all_char_data, form.get('filter', ''))
    filename = str(random.randint(1000, 9999))
    if 'Unicode' in data_filtered.columns:
        data_filtered['Unicode'] = data_filtered['Unicode'].astype(str)
    output_path = STATIC_DIR / f'{filename}.csv'
    data_filtered[char_column_selected].to_csv(output_path, index=False, encoding='utf-8')
    return PlainTextResponse(filename)


@app.post('/word_query/getExcel')
async def get_word_query_file(request: Request):
    form = await request.form()
    word_column_selected = _split_csv(form.get('word_column_selected', ''))
    char_column_selected = _split_csv(form.get('char_column_selected', ''))
    processed = []
    try:
        data_filtered = apply_filters(all_word_data, form.get('filter', ''))
        if len(data_filtered) > 4000:
            return PlainTextResponse('0')
        for _, row in data_filtered.iterrows():
            word = row['Word']
            try:
                ws = list(row[word_column_selected])
            except Exception:
                ws = [0 for _ in word_column_selected]
            chs = [all_char_data.loc[char_loc[ch]][char_column_selected].values.tolist()
                   for ch in word if u'一' <= ch <= u'鿿']
            processed.append([word] + ws + list(itertools.chain(*chs)))
    except Exception:
        words = _split_csv(form.get('words', ''))
        if len(words) > 4000:
            return PlainTextResponse('0')
        for word in words:
            try:
                ws = all_word_data[all_word_data['Word'] == word][word_column_selected].values[0].tolist()
            except Exception:
                ws = [0 for _ in word_column_selected]
            chs = [all_char_data.loc[char_loc[ch]][char_column_selected].values.tolist()
                   for ch in word if u'一' <= ch <= u'鿿']
            processed.append([word] + ws + list(itertools.chain(*chs)))
    processed_df = pd.DataFrame(processed)
    processed_df = processed_df.where(pd.notnull(processed_df), None)
    filename = str(random.randint(1000, 9999))
    char_n = (len(processed_df.columns) - len(word_column_selected) - 1) // len(char_column_selected)
    processed_df.columns = ['Word'] + word_column_selected + ['%s_%d' % (n, i) for i in range(char_n) for n in char_column_selected]
    _stringify_unicode_columns(processed_df)
    output_path = STATIC_DIR / f'{filename}.csv'
    processed_df.to_csv(output_path, index=False, encoding='utf-8')
    return PlainTextResponse(filename)


def _cleanup_file(path: Path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


@app.get('/download/{filename}')
async def download(filename: str):
    file_path = STATIC_DIR / f'{filename}.csv'
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found')
    headers = {
        'Content-Description': 'File Transfer',
        'Cache-Control': 'no-cache',
    }
    background = BackgroundTask(_cleanup_file, file_path)
    return FileResponse(
        path=str(file_path),
        media_type='application/octet-stream',
        filename='export.csv',
        headers=headers,
        background=background,
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('init:app', host='0.0.0.0', port=8000, reload=True)
