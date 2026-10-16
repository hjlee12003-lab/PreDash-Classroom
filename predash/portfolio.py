"""Manual portfolio calculations; no broker credentials or external requests."""
import json
import math


def calculate(rows, cash=0):
    def number(value):
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError('금액·수량·환율·목표비중은 0 이상의 유한한 숫자여야 합니다.')
        return value
    cash = number(cash)
    result = []
    for row in rows:
        if not str(row.get('종목', '')).strip():
            continue
        qty, cost, price, fx, target = [number(row.get(k, 0)) for k in
            ('수량', '평균매수가', '현재가', '환율', '목표비중')]
        if fx <= 0 or target > 100:
            raise ValueError('환율은 0보다 커야 하고 목표비중은 100% 이하여야 합니다.')
        invested, value = qty * cost * fx, qty * price * fx
        result.append({'종목': str(row['종목']).strip(), '분류': str(row.get('분류', '기타')),
                       '투자원금': invested, '평가액': value, '평가손익': value-invested,
                       '수익률 (%)': (value/invested-1)*100 if invested else None,
                       '목표비중 (%)': target})
    if sum(r['목표비중 (%)'] for r in result) > 100.000001:
        raise ValueError('종목 목표비중 합계는 100%를 초과할 수 없습니다. 나머지는 현금 목표입니다.')
    total = cash + sum(r['평가액'] for r in result)
    for r in result:
        r['현재비중 (%)'] = r['평가액']/total*100 if total else 0
        r['차이 (%p)'] = r['현재비중 (%)']-r['목표비중 (%)']
        r['목표대비 금액'] = total*r['목표비중 (%)']/100-r['평가액']
    cost = sum(r['투자원금'] for r in result)
    pnl = sum(r['평가손익'] for r in result)
    return {'rows': result, 'total': total, 'cost': cost, 'pnl': pnl,
            'rate': pnl/cost*100 if cost else None,
            'cash_weight': cash/total*100 if total else 0}


def restore(raw):
    obj = json.loads(raw)
    if obj.get('version') != 1 or not isinstance(obj.get('holdings'), list):
        raise ValueError('지원하지 않는 백업 형식입니다.')
    if len(obj['holdings']) > 300:
        raise ValueError('최대 300종목까지 복원할 수 있습니다.')
    calculate(obj['holdings'], obj.get('cash', 0))
    return obj


def render():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    from zoneinfo import ZoneInfo
    st.title('나의 투자관리')
    st.caption('보유자산과 목표비중을 한눈에 · 직접 입력한 가격 기준 · 실시간 시세 아님')
    with st.expander('사용 방법 · 백업 복원'):
        st.write('수량·평균매수가·현재가를 입력하세요. 원화 자산 환율은 1, 외화 자산은 1외화당 원화를 입력합니다. 목표비중은 현금을 포함한 총자산 기준입니다.')
        st.info('입력 내용은 현재 접속 세션에만 유지됩니다. 로그아웃·접속 종료 전에 JSON 백업을 내려받고 다음 접속 때 복원하세요.')
        upload = st.file_uploader('투자관리 JSON 백업', type=['json'], key='portfolio_upload')
        if st.button('백업 복원', disabled=upload is None):
            try:
                obj = restore(upload.getvalue())
                st.session_state.manual_rows = obj['holdings']
                st.session_state.manual_cash = float(obj.get('cash', 0))
                st.session_state.manual_revision = st.session_state.get('manual_revision', 0)+1
                st.rerun()
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                st.error('백업 형식 또는 숫자를 확인하세요. 기존 입력은 유지됩니다.')
    st.session_state.setdefault('manual_rows', [])
    st.session_state.setdefault('manual_cash', 0.0)
    st.session_state.setdefault('manual_revision', 0)
    cash = st.number_input('현금 · 원화 환산 금액', min_value=0.0, step=100000.0, key='manual_cash')
    columns = ['종목', '분류', '수량', '평균매수가', '현재가', '환율', '목표비중']
    data = pd.DataFrame(st.session_state.manual_rows, columns=columns)
    for col in columns[2:]:
        data[col] = pd.to_numeric(data[col], errors='coerce').astype(float)
    edited = st.data_editor(data, num_rows='dynamic', hide_index=True, use_container_width=True,
        key=f"manual_editor_{st.session_state.manual_revision}", column_config={
            '종목': st.column_config.TextColumn(required=True),
            '분류': st.column_config.SelectboxColumn(options=['국내주식','해외주식','국내ETF','해외ETF','채권','기타'], required=True, default='국내주식'),
            **{c: st.column_config.NumberColumn(min_value=0.0, required=True, default=1.0 if c=='환율' else 0.0) for c in columns[2:]}})
    rows = edited.to_dict('records')
    try:
        report = calculate(rows, cash)
    except (ValueError, TypeError, OverflowError) as exc:
        st.error(f'입력값을 확인하세요: {exc}')
        return
    # The editor retains its own base frame until a restore explicitly resets it.
    a,b,c,d = st.columns(4)
    a.metric('총자산 · 현금 포함', f"{report['total']:,.0f}원")
    b.metric('평가손익', f"{report['pnl']:+,.0f}원")
    c.metric('보유자산 수익률', '—' if report['rate'] is None else f"{report['rate']:+.2f}%")
    d.metric('현금비중', f"{report['cash_weight']:.1f}%")
    st.caption('수수료·세금·배당·실현손익 제외. 매수가와 현재가에 동일한 입력 환율을 적용하므로 환차손익은 포함하지 않습니다.')
    if report['rows']:
        left,right = st.columns([2,3])
        with left:
            st.subheader('자산 배분')
            chart = pd.DataFrame(report['rows']).groupby('분류')['평가액'].sum()
            chart.loc['현금'] = chart.get('현금', 0)+cash
            st.bar_chart(chart, color='#38664b')
        with right:
            st.subheader('목표비중 점검')
            st.dataframe(pd.DataFrame(report['rows']), hide_index=True, use_container_width=True)
            st.caption('차이가 양수면 목표 초과, 음수면 목표 미달입니다. 목표대비 금액은 입력한 목표와의 산술 차이입니다.')
        if any(abs(r['차이 (%p)']) >= 5 for r in report['rows']):
            st.info('목표비중과 5%p 이상 차이 나는 종목이 있습니다. 가격 기준일과 투자계획을 확인하세요.')
    else:
        st.info('위 표의 새 행에 첫 보유종목을 추가하세요. 실제 보유자료는 미리 입력되어 있지 않습니다.')
    backup = {'version':1, 'saved_at':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(), 'cash':cash, 'holdings':rows}
    st.download_button('투자관리 JSON 백업', json.dumps(backup,ensure_ascii=False,allow_nan=False,indent=2), 'my-portfolio.json', 'application/json')
    if report['rows']:
        st.download_button('평가내역 CSV', pd.DataFrame(report['rows']).to_csv(index=False).encode('utf-8-sig'), 'portfolio-report.csv', 'text/csv')
