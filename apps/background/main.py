import base64
import json
import os
import time
import uuid
import configparser

import sqlalchemy.orm

import datetime
from datetime import timedelta
import pytz

import requests

from PIL import Image, ImageFont, ImageDraw

import base64

# Setup Basic Variable
ISSUE_TITLE = os.getenv('ISSUE_TITLE')
TRIGGER = os.getenv('TRIGGER')

cp = configparser.ConfigParser()
if not os.path.exists('./secrets.ini'):
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
    AMAP_API_KEY = os.getenv('AMAP_API_KEY')
else:
    cp.read('./secrets.ini')
    PEXELS_API_KEY = cp['PEXELS']['API_KEY']
    AMAP_API_KEY = cp['AMAP']['API_KEY']

HITOKOTO_URL = 'https://international.v1.hitokoto.cn/?c=d&c=f&c=h&c=i&c=k&max_length=25'
PEXELS_ENDPOINT = 'https://api.pexels.com/v1/search'
AMAP_ENDPOINT = 'https://restapi.amap.com/v3/weather/weatherInfo'
GITHUB_ENDPOINT = "https://api.github.com/repos/Creep-Among-Projects/Creep-Among-Projects.github.io/actions/secrets" \
                  "/BING_COOKIE "
PEXELS_QUERY = 'nature'

GENERAL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                  'Safari/537.36 Edg/110.0.1587.46'
}

PEXELS_HEADERS = dict(**GENERAL_HEADERS, Authorization=PEXELS_API_KEY)

AMAP_PARAMS = {
    'city': '370112',
    'extensions': 'all',
    'key': AMAP_API_KEY
}

PEXELS_PARAMS = {
    'query': PEXELS_QUERY,
}

GITHUB_HEADERS = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer {}',
    'X-GitHub-Api-Version': '2022-11-28',
}

ICIBA_ENDPOINT = 'https://sentence.iciba.com/index.php'
ICIBA_PARAMS = {
    'callback': 'jQuery190012654789607849026_1587647616150',
    'c': 'dailysentence',
    'm': 'getdetail',
    'title': datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d"),
    '_': '1587647616178'
}

# Font
get_smileysans = lambda fontsize: ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=fontsize)
# smileysans = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=110)
# smileysans_bigger = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=125)
# smileysans_biggest = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=160)
# smileysans_weather_info = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=80)
qingkehuangyou_debug = ImageFont.truetype('./cache/ZCOOLQingKeHuangYou-Regular.ttf', size=30)
get_qingkehuangyou = lambda fontsize: ImageFont.truetype('./cache/ZCOOLQingKeHuangYou-Regular.ttf', size=fontsize)

# Logo
pexels_logo = Image.open('./cache/pexels_logo.png')
pexels_logo = pexels_logo.convert(mode='RGBA')
pexels_logo = pexels_logo.resize((int(pexels_logo.size[0] / 3), int(pexels_logo.size[1] / 3)))

# Setup Countdown
if str(ISSUE_TITLE).startswith('SETCountDown'):
    with open('./apps/background/countdown', 'w') as f:
        f.write(ISSUE_TITLE.lstrip('SETCountDown'))
    exit(0)
elif os.path.exists('./apps/background/countdown'):
    with open('./apps/background/countdown', 'r') as f:
        CD_TARGET = datetime.date(*[int(_) for _ in f.read().split('|')])
else:
    CD_TARGET = datetime.datetime(1970, 1, 1)


def transparent_back(img):
    img = img.convert('RGBA')
    L, H = img.size
    color_0 = img.getpixel((0, 0))
    for h in range(H):
        for l in range(L):
            dot = (l, h)
            color_1 = img.getpixel(dot)
            if color_1 == color_0:
                color_1 = color_1[:-1] + (0,)
                img.putpixel(dot, color_1)
    return img


# Init ORM
engine = sqlalchemy.engine.create_engine('sqlite:///./apps/background/db.db?check_same_thread=False', echo=False)
Base = sqlalchemy.orm.declarative_base()


class Background(Base):
    __tablename__ = 'backgrounds'
    ID = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    width = sqlalchemy.Column(sqlalchemy.Integer)
    height = sqlalchemy.Column(sqlalchemy.Integer)
    url = sqlalchemy.Column(sqlalchemy.String(200))
    photographer = sqlalchemy.Column(sqlalchemy.String(100))
    photographer_id = sqlalchemy.Column(sqlalchemy.Integer)
    avg_color = sqlalchemy.Column(sqlalchemy.String(7))
    src = sqlalchemy.Column(sqlalchemy.String(200))
    alt = sqlalchemy.Column(sqlalchemy.String(200))
    time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True),
                             default=datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")))


class Quotes(Base):
    __tablename__ = 'quotes'
    ID = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(36), unique=True)
    hitokoto = sqlalchemy.Column(sqlalchemy.String(100))
    typ = sqlalchemy.Column(sqlalchemy.String(1))
    src = sqlalchemy.Column(sqlalchemy.String(100))
    author = sqlalchemy.Column(sqlalchemy.String(50), nullable=True)
    creator = sqlalchemy.Column(sqlalchemy.String(50))
    time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True),
                             default=datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')))


class Weathers(Base):
    __tablename__ = 'weather'
    ID = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    data = sqlalchemy.Column(sqlalchemy.types.JSON)
    time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True),
                             default=datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')))


Base.metadata.create_all(engine, checkfirst=True)
session = sqlalchemy.orm.create_session(bind=engine)

# Print Basic Information
print('-' * 50)
print('Basic Information')
# print('IP Address\t\t:', requests.get('http://ip-api.com/json', headers=GENERAL_HEADERS).json()['query'])
print('Actions Trigger\t:', TRIGGER)
print(f'Issue Title\t\t: {ISSUE_TITLE}')
print('-' * 50)

# Fetch Image
pagination = 1
while True:
    pexels_search_result = requests.get(PEXELS_ENDPOINT, headers=PEXELS_HEADERS,
                                        params=dict(PEXELS_PARAMS, page=pagination)).json()
    for _ in pexels_search_result['photos']:
        if session.query(Background).filter_by(ID=_['id']).all():
            continue
        print('Get Image:', _['id'], _['alt'].replace(' ', '_'))
        new_image = Background(
            ID=_['id'],
            alt=_['alt'],
            avg_color=_['avg_color'],
            height=_['height'],
            photographer=_['photographer'],
            photographer_id=_['photographer_id'],
            src=_['src']['original'],
            url=_['url'],
            width=_['width']
        )
        session.add(new_image)
        session.commit()
        break
    else:
        if pagination >= 30:
            break
        time.sleep(0.1)
        pagination += 1
        continue
    break
if not str(ISSUE_TITLE).startswith('SETHitokoto'):
    while True:
        hitokoto_result = requests.get(HITOKOTO_URL, headers=GENERAL_HEADERS).json()
        if session.query(Quotes).filter_by(ID=hitokoto_result['id']).all():
            time.sleep(0.5)
            continue
        print('Quote\t:', hitokoto_result['hitokoto'])
        new_quote = Quotes(
            ID=hitokoto_result['id'],
            author=hitokoto_result['from_who'],
            creator=hitokoto_result['creator'],
            hitokoto=hitokoto_result['hitokoto'],
            src=hitokoto_result['from'],
            typ=hitokoto_result['type'],
            uuid=hitokoto_result['uuid']
        )
        session.add(new_quote)
        session.commit()
        break
    
    # iciba_result = json.loads(requests.get(ICIBA_ENDPOINT, params=ICIBA_PARAMS, headers=GENERAL_HEADERS).content.decode('unicode_escape')[42:-1])
    # quote = f'{iciba_result["content"]}\n{iciba_result["note"]}'
else:
    new_quote = Quotes(
        ID=time.time(),
        author='',
        creator='issue',
        hitokoto=ISSUE_TITLE.lstrip('SETHitokoto'),
        src='',
        typ='z',
        uuid=str(uuid.uuid4())
    )

weather_info = requests.get(AMAP_ENDPOINT, params=AMAP_PARAMS).json()
new_weather = Weathers(data=weather_info)
session.add(new_weather)
session.commit()
weather_info = weather_info['forecasts'][0]['casts']

with open(f'./cache/{new_image.ID}.jpg', 'wb') as f:
    try:
        print('Downloading... plz wait')
        f.write(requests.get(new_image.src, headers=GENERAL_HEADERS).content)
    except:
        exit()
print('Download Complete')

ori_image = Image.open(f'./cache/{new_image.ID}.jpg')
print('-' * 50)
print('Image Info')
print('Image Size\t\t:', ori_image.size)
print('Image Format\t:', ori_image.format)
print('Image Mode\t\t:', ori_image.mode)
print('-' * 50)
print('Resizing...')
if ori_image.size[0] / ori_image.size[1] == 3840 / 2160:
    resized_image = ori_image.copy()
elif ori_image.size[0] / ori_image.size[1] > 3840 / 2160:
    resized_image = ori_image.crop(((ori_image.size[0] - 3840 / 2160 * ori_image.size[1]) / 2, 0,
                                    ori_image.size[0] - (ori_image.size[0] - 3840 / 2160 * ori_image.size[1]) / 2,
                                    ori_image.size[1]))
else:
    resized_image = ori_image.crop((0, (ori_image.size[1] - 2160 / 3840 * ori_image.size[0]) / 2, ori_image.size[0],
                                    ori_image.size[1] - (ori_image.size[1] - 2160 / 3840 * ori_image.size[0]) / 2))
resized_image = resized_image.resize((3840, 2160))
# resized_image.save('./cache/resized.jpg')

# Mix Everything UP!!!
opacity_color = (int(new_image.avg_color[1:3], 16), int(new_image.avg_color[3:5], 16),
                 int(new_image.avg_color[5:7], 16), 128)
draw = ImageDraw.ImageDraw(resized_image, mode='RGBA')
draw.rectangle([(0, 0), (3840, 800)], fill=opacity_color)
'''
quote = f'{new_quote.hitokoto}    --{new_quote.author} {new_quote.src}' if new_quote.author \
    else f'{new_quote.hitokoto}    --{new_quote.src}'
'''
try:
    quote = f'{iciba_result["content"]}\n{iciba_result["note"]}'
except:
    quote = f'{new_quote.hitokoto}    --{new_quote.author} {new_quote.src}' if new_quote.author \
        else f'{new_quote.hitokoto}    --{new_quote.src}'

weather_text = f'天气预报：\n{"-" * 28}\n' + \
               f'\n{"-" * 28}\n'.join([f'日期：{_["date"]}\n'
                                       f'天气：{_["dayweather"]}/{_["nightweather"]}\n'
                                       f'温度：{_["nighttemp_float"]} ~ {_["daytemp_float"]}\n'
                                       f'风级：{_["daypower"]}'
                                       for _ in weather_info])
draw.multiline_text((3000, 400),
                    text=weather_text,
                    fill=(255, 255, 255),
                    font=get_qingkehuangyou(70),
                    anchor='la',
                    align='left')

draw.multiline_text((1920, 70),
                    text=quote,
                    fill=(255, 255, 255),
                    font=get_smileysans(125),
                    anchor='ma',
                    align='center')

debug_info = f'''
调试信息：
生成日期: {datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).isoformat()}
触发器: {TRIGGER}
'''
draw.multiline_text((20, 10),
                    text=debug_info,
                    fill=(255, 255, 255),
                    font=qingkehuangyou_debug,
                    anchor='la',
                    align='left')

resized_image.paste(pexels_logo, (3840 - 238, 2160 - 150), pexels_logo)
resized_image.save(f'./docs/backgrounds_no_countdown/{new_image.ID}.jpg')

if CD_TARGET - datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')).date() >= timedelta(days=0):
    draw.text((1920, 375),
              text=f'距离设定的日期：{CD_TARGET.year}年{CD_TARGET.month}月{CD_TARGET.day}日还有',
              fill=(255, 255, 255),
              font=get_smileysans(130),
              anchor='ma',
              align='center')
    draw.text((1920, 550),
              text=f'{(CD_TARGET - datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).date()).days}天',
              fill=(255, 255, 255),
              font=get_smileysans(180),
              anchor='ma',
              align='center')

resized_image.save(f'./docs/backgrounds/{new_image.ID}.jpg')
with open('./docs/background.md', 'a+', encoding='utf-8') as f:
    f.writelines(f'|{datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).date().isoformat()}|{new_image.ID}|{new_quote.hitokoto}'
                 f'|[图片链接](./backgrounds/{new_image.ID}.jpg)|{TRIGGER}|\n')

with open('./docs/background_no_cd.md', 'a+', encoding='utf-8') as f:
    f.writelines(f'|{datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).date().isoformat()}|{new_image.ID}|{new_quote.hitokoto}'
                 f'|[图片链接](./backgrounds_no_countdown/{new_image.ID}.jpg)|{TRIGGER}|\n')
