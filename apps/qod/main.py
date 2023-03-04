import os
import time

import requests

import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm

import cv2
from PIL import Image, ImageDraw, ImageFont

GENERAL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                  'Safari/537.36 Edg/110.0.1587.46'
}

PEXELS_HEADERS = {
    'Authorization': os.getenv('PEXELS_API_KEY'),
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                  'Safari/537.36 Edg/110.0.1587.46'
}

PEXELS_QUERY = ['nature', 'sunset', 'sea']

HITOKOTO_URL = 'https://international.v1.hitokoto.cn/?c=d&c=f&c=h&c=i&c=k&max_length=25'

engine = sqlalchemy.engine.create_engine('sqlite:///./apps/qod/db.db?check_same_thread=False', echo=False)
Base = sqlalchemy.ext.declarative.declarative_base()


class Backgrounds(Base):
    __tablename__ = 'backgrounds'
    ID = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    pexels_id = sqlalchemy.Column(sqlalchemy.Integer)
    url = sqlalchemy.Column(sqlalchemy.String(200))
    avg_color = sqlalchemy.Column(sqlalchemy.String(7))
    src = sqlalchemy.Column(sqlalchemy.String(200))
    alt = sqlalchemy.Column(sqlalchemy.String(200))
    time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=sqlalchemy.func.current_timestamp())


class Quotes(Base):
    __tablename__ = 'quotes'
    ID = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(36))
    hitokoto = sqlalchemy.Column(sqlalchemy.String(100))
    typ = sqlalchemy.Column(sqlalchemy.String(1))
    src = sqlalchemy.Column(sqlalchemy.String(100))
    author = sqlalchemy.Column(sqlalchemy.String(50))
    time = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=sqlalchemy.func.current_timestamp())


Base.metadata.create_all(engine, checkfirst=True)
session = sqlalchemy.orm.create_session(bind=engine)

print('IP Address:', requests.get('http://ip-api.com/json', headers=GENERAL_HEADERS).json()['query'])

# Fetch Pexels Images
images_url = []

for _ in PEXELS_QUERY:
    for c in range(10):
        pexels_search_result = requests.get('https://api.pexels.com/v1/search', headers=PEXELS_HEADERS,
                                            params={'query': _, 'orientation': 'landscape', 'page': c}).json()
        for _i in pexels_search_result['photos']:
            if session.query(Backgrounds).filter_by(pexels_id=_i['id']).all():
                continue
            print('Picture Information', _i['id'], _i['alt'].replace(' ', '_'), sep='.')
            new_image = Backgrounds(
                alt=_i['alt'],
                avg_color=_i['avg_color'],
                pexels_id=_i['id'],
                src=_i['src']['original'],
                url=_i['url']
            )
            session.add(new_image)
            session.commit()
            images_url.append([_i['id'], _i['src']['original'], _i['avg_color']])
            break
        else:
            time.sleep(0.1)
            continue
        break
    else:
        print('No More Pictures!')

print(images_url)

# Download Pexels Images to Temporary Folder
downloaded_images = []
for _ in images_url:
    try:
        print('Downloading', _[0])
        with open(f'./cache/{_[0]}.jpg', 'wb') as f:
            f.write(requests.get(_[1], headers=GENERAL_HEADERS).content)
        downloaded_images.append([_[0], _[2]])
    except:
        pass

print('Download finished:', downloaded_images)

# Fetch Quotes
quotes = []
while len(quotes) < len(downloaded_images):
    hitokoto_result = requests.get(HITOKOTO_URL, headers=GENERAL_HEADERS).json()
    if session.query(Quotes).filter_by(hitokoto=hitokoto_result['hitokoto']).all():
        time.sleep(1)
        continue
    print('Quote:', hitokoto_result['hitokoto'])
    new_quote = Quotes(
        author=hitokoto_result['from_who'],
        hitokoto=hitokoto_result['hitokoto'],
        src=hitokoto_result['from'],
        typ=hitokoto_result['type'],
        uuid=hitokoto_result['uuid']
    )
    session.add(new_quote)
    session.commit()
    quotes.append(hitokoto_result)
    continue

print('Fetched Quotes:', *[_['hitokoto'] for _ in quotes])

# Combine Quotes and Backgrounds
qod = [[quotes[_], downloaded_images[_]] for _ in range(len(downloaded_images))]

# Mix Everything Up!
if not os.path.exists('./docs/qods/'):
    os.mkdir('./docs/qods')

for _ in qod:
    print('-' * 80)
    print('Image File:', f'./cache/{_[1][0]}.jpg')
    img1 = Image.open(f'./cache/{_[1][0]}.jpg')
    print('Image Format:', img1.format)
    print('Image Size:', img1.size)
    print('Image Mode:', img1.mode)
    img2 = img1.copy()
    img2.thumbnail((3840, 2160))
    # img2.save(f'./docs/qods/{_[1][0]}.bmp')

    smileysans_hitokoto = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=130)
    smileysans_source = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=90)
    smileysans_author = ImageFont.truetype('./cache/SmileySans-Oblique.ttf', size=50)
    source_text = f'{_[0]["from_who"]} - {_[0]["from"]}' if _[0]['from_who'] else f'{_[0]["from"]}'
    draw = ImageDraw.ImageDraw(img2)
    draw.text((img2.size[0] / 2, img2.size[1] / 2),
              text=_[0]['hitokoto'],
              fill=(255, 255, 255),
              font=smileysans_hitokoto,
              anchor='mm',
              align='center')
    draw.text((img2.size[0] / 2, img2.size[1] / 2 + 250),
              text=source_text,
              fill=(255, 255, 255),
              font=smileysans_source,
              anchor='mm',
              align='center')
    draw.text((img2.size[0] / 2, img2.size[1] - 200),
              text='By. 5925 Chen',
              fill=(255, 255, 255),
              font=smileysans_author,
              anchor='mm',
              align='center')
    img2.save(f'./docs/qods/{_[1][0]}.jpg')

# Write to MarkDown
with open('./docs/qod.md', 'a+') as f:
    print(qod)
    f.writelines([f'|{time.strftime("%Y-%m-%d", time.localtime())}|{_[1][0]}|'
                  f'{_[0]["hitokoto"]}|[图片链接](./qods/{_[1][0]}.jpg)|\n' for _ in qod])
