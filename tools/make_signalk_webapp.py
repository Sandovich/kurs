# Собирает «Курс» как приложение для сервера Signal K на лодке (бортовой компьютер: OpenPlotter, Raspberry Pi, Victron Cerbo).
# Тогда «Курс» открывается с самого сервера по http://<адрес лодки>:3000/kurs-signalk/ и берёт приборы без интернета и без запрета браузера
# на смешение https и http. Запуск: python tools/make_signalk_webapp.py  → папка dist/kurs-signalk (её копируют на борт)
# Установка на борту: в папке ~/.signalk выполнить  npm install /путь/к/kurs-signalk  и перезапустить сервер Signal K.
import json, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'dist', 'kurs-signalk'); PUB = os.path.join(OUT, 'public')
ver = next(l for l in open(os.path.join(ROOT, 'index.html'), encoding='utf-8') if "const VER='" in l).split("const VER='")[1].split("'")[0]
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(PUB)
for f in ('index.html', 'sw.js', 'manifest.webmanifest', 'icon.svg'): shutil.copy(os.path.join(ROOT, f), PUB)
for d in ('data', 'map'): shutil.copytree(os.path.join(ROOT, d), os.path.join(PUB, d))
json.dump({'name': 'kurs-signalk', 'version': ver, 'description': 'Курс — погода, карта и переход для яхтсменов (Нева, Ладога, Финский залив). Берёт GPS, эхолот, ветер, лаг и AIS с сервера Signal K.',
           'keywords': ['signalk-webapp'], 'license': 'UNLICENSED', 'private': True,
           'signalk': {'displayName': 'Курс', 'appIcon': './icon.svg'}},
          open(os.path.join(OUT, 'package.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
n = sum(len(fs) for _, _, fs in os.walk(OUT)); sz = sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(OUT) for f in fs)
print(f'готово: {OUT}, версия {ver}, файлов {n}, {sz // 2**20} МБ')
