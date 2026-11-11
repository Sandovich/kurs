# Сборщик погоды для «Курса» (запускает GitHub Actions): ветер на российских станциях (SYNOP через Ogimet, раз в час)
# и сетки прогноза всех моделей на весь район (когда опубликованная старше 2,5 ч). Пишет в папку out/: obs.json, grid_<модель>.json
import json, os, sys, time, urllib.request, urllib.error, datetime as dt
UA = {'User-Agent': 'KursWeather/1.0 (+https://sandovich.github.io/kurs)'}
def get(u, t=60):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read().decode('utf-8', 'replace')
ST = {  # станции у воды: WMO → (широта, долгота, название)
 '22802': (61.717, 30.717, 'Сортавала'), '22805': (61.367, 30.883, 'Валаам'), '22820': (61.817, 34.267, 'Петрозаводск'),
 '22727': (62.167, 34.3, 'Кондопога'), '22837': (61.017, 36.45, 'Вытегра'), '22892': (60.717, 28.733, 'Выборг'),
 '22912': (60.983, 32.983, 'Олонец'), '22913': (60.717, 33.55, 'Лодейное Поле'), '22917': (60.117, 32.317, 'Новая Ладога'),
 '26058': (59.389, 28.117, 'Нарва-Йыэсуу'), '26059': (59.367, 28.6, 'Кингисепп'), '26063': (59.8, 30.263, 'Пулково (Санкт-Петербург)'),
 '26072': (59.933, 31.0, 'Шлиссельбург'), '26045': (59.517, 26.55, 'Кунда')}
def synop(line):
    p = line.split(',', 6); wmo = p[0]; ts = dt.datetime(int(p[1]), int(p[2]), int(p[3]), int(p[4]), int(p[5]), tzinfo=dt.timezone.utc).timestamp()
    g = p[6].replace('=', '').split()
    if len(g) < 5 or g[0] != 'AAXX': return None
    iw = g[1][-1]; k = 1.94384 if iw in '01' else 1.0          # 0/1 — м/с, 3/4 — узлы
    nddff = g[4]
    if '/' in nddff[1:]: return None
    dd, ff = int(nddff[1:3]) * 10, int(nddff[3:5]); i = 5
    if ff == 99 and len(g) > 5 and g[5].startswith('00'): ff = int(g[5][2:5]); i = 6
    if dd > 360: return None
    gust = None
    if '333' in g:
        for q in g[g.index('333') + 1:]:
            if q in ('555', '444'): break
            if q[:3] in ('910', '911') and q[3:].isdigit(): gust = max(gust or 0, int(q[3:]) * k)
    return {'wmo': wmo, 't': int(ts), 'spd': round(ff * k, 1), 'dir': dd if ff else 0, 'gust': round(gust, 1) if gust else None}
def obs():
    beg = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)).strftime('%Y%m%d%H00'); last = {}
    for b in ('227', '228', '229', '260'):
        try: txt = get(f'https://www.ogimet.com/cgi-bin/getsynop?block={b}&begin={beg}')
        except Exception as e: print('ogimet', b, e); continue
        for ln in txt.splitlines():
            if ln[:5] not in ST: continue
            try: o = synop(ln)
            except Exception: o = None
            if o and (o['wmo'] not in last or last[o['wmo']]['t'] < o['t']): last[o['wmo']] = o
        time.sleep(2)
    st = [{'name': ST[w][2], 'lat': ST[w][0], 'lon': ST[w][1], 't': o['t'], 'spd': o['spd'], 'dir': o['dir'], 'gust': o['gust'], 'src': 'метеостанция Росгидромета (SYNOP)'} for w, o in last.items()]
    print('станций', len(st)); return {'v': 1, 'built': int(time.time()), 'st': st}
WXR = dict(s=59.2, n=62.0, w=26.8, e=33.6, st=.4)
def grid(model):
    Ny = round((WXR['n'] - WXR['s']) / WXR['st']) + 1; Nx = round((WXR['e'] - WXR['w']) / WXR['st']) + 1; la, lo = [], []
    for i in range(Ny):
        for j in range(Nx): la.append('%.3f' % (WXR['s'] + (WXR['n'] - WXR['s']) * i / (Ny - 1))); lo.append('%.3f' % (WXR['w'] + (WXR['e'] - WXR['w']) * j / (Nx - 1)))
    js = json.loads(get(f'https://api.open-meteo.com/v1/forecast?latitude={",".join(la)}&longitude={",".join(lo)}&hourly=wind_speed_10m,wind_direction_10m,wind_gusts_10m&wind_speed_unit=kn&forecast_days=5&timeformat=unixtime&models={model}', 60))
    if not isinstance(js, list): js = [js]
    return {'model': model, 's': WXR['s'], 'n': WXR['n'], 'w': WXR['w'], 'e': WXR['e'], 'N': Nx, 'Nx': Nx, 'Ny': Ny, 'reg': True, 'z': 8, 'fetched': int(time.time() * 1000), 'shared': True,
            'times': js[0]['hourly']['time'], 'spd': [x['hourly']['wind_speed_10m'] for x in js], 'dir': [x['hourly']['wind_direction_10m'] for x in js], 'gst': [x['hourly']['wind_gusts_10m'] for x in js]}
if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    json.dump(obs(), open('out/obs.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    # сетки прогноза для всех моделей «Курса»: при каждом запуске, но не чаще раза в 2,5 ч на модель
    # (таймер GitHub срабатывает неравномерно; так общий файл всегда свежий, а лимит Open-Meteo не тратится зря)
    RAW = 'https://raw.githubusercontent.com/' + os.environ.get('GITHUB_REPOSITORY', 'Sandovich/kurs') + '/data/'
    for m in ('ecmwf_ifs025', 'icon_seamless', 'gfs_seamless', 'metno_seamless', 'dmi_seamless', 'ecmwf_aifs025_single'):
        try:
            old = json.loads(get(RAW + f'grid_{m}.json', 15)).get('fetched', 0)
        except Exception: old = 0
        if 'grid' not in sys.argv and time.time() * 1000 - old < 2.5 * 3600e3: print('сетка свежая', m); continue
        try: json.dump(grid(m), open(f'out/grid_{m}.json', 'w'), separators=(',', ':')); print('сетка', m)
        except urllib.error.HTTPError as e:
            print('grid', m, e)
            if e.code == 429: print('лимит Open-Meteo — остальные модели в следующий раз'); break
        except Exception as e: print('grid', m, e)
        time.sleep(3)
