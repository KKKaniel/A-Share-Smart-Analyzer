#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大A智能分析系统 - A股中小盘智能筛选与多维度分析
"""

import akshare as ak
import pandas as pd
import numpy as np
import os
from datetime import datetime
from jinja2 import Template

MARKET_CAP_MIN = 20
MARKET_CAP_MAX = 200
PE_MAX = 60
PB_MAX = 5
TOP_N = 20


def fetch_a_share_realtime():
    try:
        df = ak.stock_zh_a_spot_em()
        df = df.rename(columns={
            '代码': 'code', '名称': 'name', '最新价': 'price',
            '涨跌幅': 'pct_change', '成交额': 'amount',
            '市盈率-动态': 'pe', '市净率': 'pb',
            '总市值': 'total_cap', '流通市值': 'float_cap'
        })
        cols = ['code', 'name', 'price', 'pct_change', 'amount', 'pe', 'pb', 'total_cap', 'float_cap']
        df = df[[c for c in cols if c in df.columns]].copy()
        for col in ['price', 'pct_change', 'amount', 'pe', 'pb', 'total_cap', 'float_cap']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()


def filter_small_mid_cap(df):
    if df.empty:
        return df
    cap_min = MARKET_CAP_MIN * 1e8
    cap_max = MARKET_CAP_MAX * 1e8
    mask = (
        df['total_cap'].between(cap_min, cap_max) &
        df['pe'].between(0, PE_MAX) &
        df['pb'].between(0, PB_MAX) &
        df['price'].notna() & (df['price'] > 0)
    )
    return df[mask].copy()


def score_stocks(df):
    if df.empty:
        return df
    df = df.copy()

    def normalize(series, ascending=True):
        s = series.copy()
        if s.max() == s.min():
            return pd.Series(50, index=s.index)
        norm = (s - s.min()) / (s.max() - s.min()) * 100
        return norm if ascending else 100 - norm

    scores = pd.DataFrame(index=df.index)
    scores['pe_score'] = normalize(df['pe'], ascending=False) * 0.25
    scores['pb_score'] = normalize(df['pb'], ascending=False) * 0.20
    scores['chg_score'] = normalize(df['pct_change'], ascending=True) * 0.20
    scores['amt_score'] = normalize(df['amount'], ascending=True) * 0.20
    scores['cap_score'] = normalize(df['total_cap'], ascending=False) * 0.15

    df['score'] = scores.sum(axis=1).round(2)
    return df.sort_values('score', ascending=False).head(TOP_N)


def fetch_index_data():
    indices = {
        '上证指数': '000001',
        '深证成指': '399001',
        '创业板指': '399006',
        '中证500': '000905',
    }
    result = []
    try:
        df = ak.stock_zh_index_spot_em()
        for name, code in indices.items():
            row = df[df['代码'] == code]
            if not row.empty:
                result.append({
                    'name': name,
                    'price': float(row['最新价'].values[0]),
                    'pct_change': float(row['涨跌幅'].values[0])
                })
            else:
                result.append({'name': name, 'price': 0, 'pct_change': 0})
    except Exception:
        for name in indices:
            result.append({'name': name, 'price': 0, 'pct_change': 0})
    return result


def generate_html(df, indices):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    update_date = datetime.now().strftime('%Y年%m月%d日')
    rows_data = []
    for i, (_, r) in enumerate(df.iterrows(), 1):
        cap_yi = round(r['total_cap'] / 1e8, 1) if pd.notna(r.get('total_cap')) else '-'
        rows_data.append({
            'rank': i,
            'code': r.get('code', '-'),
            'name': r.get('name', '-'),
            'price': f"{r['price']:.2f}" if pd.notna(r.get('price')) else '-',
            'pct_change': r.get('pct_change', 0),
            'pct_str': f"{r['pct_change']:+.2f}%" if pd.notna(r.get('pct_change')) else '-',
            'pe': f"{r['pe']:.1f}" if pd.notna(r.get('pe')) else '-',
            'pb': f"{r['pb']:.2f}" if pd.notna(r.get('pb')) else '-',
            'cap': f"{cap_yi}亿",
            'score': r.get('score', 0)
        })

    template_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'template.html')
    with open(template_path, encoding='utf-8') as f:
        template_str = f.read()
    html = Template(template_str).render(
        update_time=now,
        update_date=update_date,
        indices=indices,
        rows=rows_data,
        total_count=len(df)
    )
    out_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    df = fetch_a_share_realtime()
    if df.empty:
        return
    df = filter_small_mid_cap(df)
    df = score_stocks(df)
    indices = fetch_index_data()
    generate_html(df, indices)


if __name__ == '__main__':
    main()
