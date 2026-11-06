# 오피넷 '반경 내 주유소' API로 대전 주유소·충전소 가격을 모아 prices.json에 저장해요.
# GitHub Actions에서 하루 몇 번 실행돼요. 키는 저장소 Secret(OPINET_KEY)에서 받아요.
import json, os, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

KEY = os.environ.get('OPINET_KEY', '').strip()
CIRCLES = [[345924, 415781], [345924, 424281], [339424, 414781], [347924, 411781], [336424, 405781], [336924, 420781], [348924, 413281], [348424, 406281], [344424, 427281]]   # KATEC 좌표, 반경 4.7km 원 9개로 지도 속 모든 곳을 덮어요
RADIUS = 5000
PRODS = ['B027', 'D047', 'K015']   # 휘발유, 경유, 자동차부탄(LPG)

def call(prod, x, y):
    q = urllib.parse.urlencode({'out': 'json', 'x': x, 'y': y, 'radius': RADIUS, 'sort': 2, 'prodcd': prod, 'certkey': KEY})
    for attempt in range(3):
        try:
            with urllib.request.urlopen('https://www.opinet.co.kr/api/aroundAll.do?' + q, timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))['RESULT']['OIL']
        except Exception as e:
            print('retry', prod, x, y, e, file=sys.stderr); time.sleep(3)
    raise SystemExit('오피넷 호출 실패')

def main():
    if not KEY:
        print('OPINET_KEY 없음: 건너뜀'); return
    st = {}
    for prod in PRODS:
        for x, y in CIRCLES:
            for o in call(prod, x, y):
                s = st.setdefault(o['UNI_ID'], {'n': o['OS_NM'], 'b': o.get('POLL_DIV_CD') or o.get('POLL_DIV_CO'), 'x': round(float(o['GIS_X_COOR']), 1), 'y': round(float(o['GIS_Y_COOR']), 1), 'p': {}})
                if o.get('PRICE'): s['p'][prod] = int(float(o['PRICE']))
            time.sleep(0.3)
    if len(st) < 100:
        raise SystemExit(f'결과가 너무 적어요({len(st)}곳): 덮어쓰지 않아요')
    now = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
    json.dump({'updated': now, 'st': st}, open('prices.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    print(now, len(st), 'stations')

main()
