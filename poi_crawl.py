import os
import time
import configparser
from requests import post
import csv
import logging
import json
import shutil
from bs4 import BeautifulSoup
from comment_crawl import GetComments

URL = 'https://m.ctrip.com/restapi/soa2/13342/json/getSightRecreationList'  # 获取景点列表数据
DetailURL = 'https://m.ctrip.com/restapi/soa2/18254/json/getPoiMoreDetail'  # 获取景点详情数据
TicketURL = 'https://m.ctrip.com/restapi/soa2/12530/json/getProductShelf'  # 获取票价数据
CityURL = 'https://m.ctrip.com/restapi/soa2/13342/json/SearchSightRecreation'  # 获取城市编号
isRestart = 0
isCrawlComment = 0
history = set()

data = {'fromChannel': 2,
        'index': 1,
        'count': 20,
        'districtId': 9,  # 可修改此处变更爬取城市
        'sortType': 0,
        'categoryId': 0,
        'lat': 0,
        'lon': 0,
        'showNewVersion': True,
        'locationFilterDistance': 300,
        'locationDistrictId': 0,
        'themeId': 0,
        'level2ThemeId': 0,
        'locationFilterId': 0,
        'locationFilterType': 0,
        'sightLevels': [],
        'ticketType': None,
        'commentScore': None,
        'showAgg': True,
        'fromNearby': '',
        'sourceFrom': 'sightlist',
        'themeName': '',
        'scene': '',
        'hiderank': '',
        'isLibertinism': False,
        'hideTop': False,
        'head': {'cid': '09031065211914680477',
                 'ctok': '',
                 'cver': '1.0',
                 'lang': '01',
                 'sid': '8888',
                 'syscode': '09',
                 'auth': '',
                 'xsid': '',
                 'extension': []}}

detail_data = {
    "poiId": 87211,
    "scene": "basic",
    "head": {
        "cid": "09031065211914680477",
        "ctok": "",
        "cver": "1.0",
        "lang": "01",
        "sid": "8888",
        "syscode": "09",
        "auth": "",
        "xsid": "",
        "extension": []
    }
}

ticket_data = {
    'head': {'cid': '09031065211914680477',
             'syscode': '09',
             'extension': [{'name': 'needNewStructureV2', 'value': 'true'},
                           {'name': 'crawlerKey',
                            'value': '0bd0f473f984aaf20ece34b437cce49e51d55d4baefe0ca56ac3559956a72691'},
                           {'name': 'fingerprintKeys',
                            'value': 'N1mwb6YgTeUNE4HEsYM9iqhWLYdte05EQLjd9WHYFsrb3IsNvUkj8Yo6jLMWgkvb1jfYUtEADwFmizljDYX7eGmw9ZvMcjhbvs1eoZYBgjO4yXY5XyN7vGDYDlwMpjQ3edSiFTYkYlYMNr9cEQ4wtTxZqYSajk1jLhW0YzYXYfoYnoiFTikZiMhj4Y9cEodiDlYldwO8yfpyFpYDzwhYpARsSwoTRfHEDcRtfyfoyahwT0JdfEtFJhOEgXR0YqoKaGymbi9kJnOJcBjkmRLbWPPxXOraSR18wq5E5fi0AecPjSYZNR1gwhLWm6wlgwNbRgzv8oYTOWA1JtHJFMjUSEgYN8jMgwQPvGSjsYzPEFDJ4GEk5eg5ykaW3AYnY0nE64JgMEZDe6OyStWOdY8YU7RdGwmHRUSENGRfoyoXyOLwc6J4BEBoESMwcqvTYQ0E5ojNSWgDWPbWaZYz4YbTYsUR90YTQWo6YdlYl0Ypoj4Uet1E1bW0Qeo9wbdeU8jPMYNsy8lEZbj65ElarpUj6zwZs'},
                           {'name': 'H5', 'value': 'H5'}]},
    'debug': False,
    'pageid': '214070',
    'contentType': 'json',
    'clientInfo': {'pageId': '214070',
                   'platformId': None,
                   'crnVersion': '2021-02-03 20:08:05',
                   'location': {'lat': '',
                                'lon': '',
                                'cityId': None,
                                'locatedCityId': None,
                                'districtId': None,
                                'locatedDistrictId': None},
                   'locale': 'zh-CN',
                   'currency': 'CNY'},
    'spotid': 229,
    'poiId': 75595,
    'locale': 'zh-CN',
    'currency': 'CNY',
    'platformId': None,
    'needFilter': True,
    'resourceLimit': True}

city_data = {
    'KeyWord': '',
    'DistrictId': 1,
    'CategoryId': 0,
    'head': {
        'cid': '09031065211914680477',
        'ctok': '',
        'cver': '1.0',
        'lang': '01',
        'sid': '8888',
        'syscode': '09',
        'auth': '',
        'xsid': '',
        'extension': []
    }
}


def getCityID(city_name):
    city_data['KeyWord'] = city_name
    city_res = post(CityURL, json=city_data).json()['districtResult']
    if len(city_res) == 0:
        logging.error('城市名错误！无结果')
        exit(0)

    elif len(city_res) >= 1:
        cityID = city_res[0]['districtId']
        if len(city_res) > 1:
            logging.warning(f'多个相似城市名结果，注意确认\n')
            print([i["districtName"] + "-" + i["name"] for i in city_res])

        print(f'目标城市：{city_res[0]["districtName"] + "-" + city_res[0]["name"]}\n')
        return cityID


def CalPrice(kv):
    sumSale = 0
    avg = 0
    for k, v in kv:
        sumSale += k
    for k, v in kv:
        try:
            avg += k / sumSale * v
        except:
            continue
    return avg


def GetTicketPrice(spotid, poiId):
    tdata = ticket_data.copy()
    tdata['spotid'] = spotid
    tdata['poiId'] = poiId
    ticket_res = post(TicketURL, json=tdata)
    dataa = ticket_res.json().get('data')
    if not dataa:
        return [0, 0, 0, 0]
    shelfGroup = dataa.get('shelfGroups')
    if not shelfGroup:
        return [0, 0, 0, 0]

    chengr = []
    laor = []
    xues = []
    ertong = []
    lr = 0
    xs = 0
    cr = 0
    et = 0
    tt = 0
    overall = []
    maxsales = 0
    for i in shelfGroup:
        ticketGroups = i.get('ticketGroups')
        if ticketGroups:
            for j in ticketGroups:
                sales = j.get('yearlySale')
                maxsales = max(sales, maxsales)
                if j.get('mainTicket', False):
                    tt = 1
                    subTickets = j.get('subTicketGroups')
                    if subTickets:
                        for sub in subTickets:
                            if '成人' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName', ''):
                                chengr.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                cr = 1
                            if '老人' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName', ''):
                                laor.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                lr = 1
                            if '学生' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName', ''):
                                xues.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                xs = 1
                            if '儿童' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName', ''):
                                ertong.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                et = 1
                            overall.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))

    if tt == 0:
        for i in shelfGroup:
            ticketGroups = i.get('ticketGroups')
            if ticketGroups:
                for j in ticketGroups:
                    sales = j.get('yearlySale')
                    if not sales == maxsales:
                        continue

                    subTickets = j.get('subTicketGroups')
                    if subTickets:
                        for sub in subTickets:
                            if '票' not in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName',
                                                                                                            '') \
                                    or sub['subTicketGroupInfo']['priceInfo']['price'] > 300:
                                continue

                            if '成人' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName',
                                                                                                         ''):
                                chengr.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                cr = 1
                            if '老人' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName',
                                                                                                         ''):
                                laor.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                lr = 1
                            if '学生' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName',
                                                                                                         ''):
                                xues.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                xs = 1
                            if '儿童' in sub['subTicketGroupInfo']['name'] + sub['subTicketGroupInfo'].get('subName',
                                                                                                         ''):
                                ertong.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                                et = 1
                            overall.append((sales, sub['subTicketGroupInfo']['priceInfo']['price']))
                    else:
                        logging.warning('无sub')

    if cr == 0:
        chengr = overall.copy()
    if lr == 0:
        laor = chengr.copy()
    if xs == 0:
        xues = chengr.copy()
    if et == 0:
        ertong = chengr.copy()

    crp = CalPrice(chengr)
    xsp = CalPrice(xues)
    lrp = CalPrice(laor)
    etp = CalPrice(ertong)

    ticket_res.close()
    return [crp, lrp, xsp, etp]


def GetDetail(poiId):
    ddata = detail_data.copy()
    ddata['poiId'] = poiId
    detail_res = post(DetailURL, json=ddata)
    templateList = detail_res.json().get('templateList')
    spendTime = ''
    opentime = ''
    desc = ''
    preferential = {}

    if not templateList:
        return [spendTime, opentime, desc, preferential]

    for i in templateList:
        if i.get('templateName') == '温馨提示':
            moduleList = i.get('moduleList')
            if moduleList:
                for j in moduleList:
                    if j.get('moduleName') == '开放时间':
                        mod = j.get('poiOpenModule')
                        spendTime = mod.get('playSpendTime')
                        opentime = str(mod)
                    elif j.get('moduleName') == '优待政策':
                        mod = j.get('preferentialModule').get('policyInfoList')
                        if mod:
                            for l in mod:
                                cus = l.get('customDesc')
                                preferential[cus] = []
                                for k in l.get('policyDetail'):
                                    lst = [k.get('limitation'), k.get('policyDesc')]
                                    preferential[cus].append(lst)


        elif i.get('templateName') == '信息介绍':
            moduleList = i.get('moduleList')
            if moduleList:
                for j in moduleList:
                    if j.get('moduleName') == '图文详情':
                        mod = j.get('introductionModule')
                        desc = mod.get('introduction')
                        soup = BeautifulSoup(desc, 'lxml')
                        desc = soup.text

    detail_res.close()
    return [spendTime, opentime, desc, preferential]


if __name__ == '__main__':
    if not os.path.exists('data/'):
        os.mkdir('data')
    if not os.path.exists('data/comments'):
        os.mkdir('data/comments')

    conf = configparser.ConfigParser()
    conf.read('config.ini', encoding="utf-8")

    try:
        city = conf.get('poi', 'city')
    except:
        city = '北京'

    try:
        isRestart = int(conf.get('poi', 'isRestart'))
        isCrawlComment = int(conf.get('poi', 'isCrawlComment'))
        shutil.copyfile('data/pois.csv', 'data/back.csv')  # 写前备份
    except:
        pass

    data['districtId'] = getCityID(city)    # 获取城市编号

    if isRestart == 1:
        try:
            with open('data/pois.csv', 'r', encoding='utf-8') as rf:
                rd = csv.reader(rf)
                cnt = 0
                for r in rd:
                    cnt += 1
                    if cnt == 1:
                        continue
                    history.add(int(r[2]))

            f = open('data/pois.csv', 'a', encoding='utf-8')

        except FileNotFoundError:
            logging.error('无法续写，文件不存在')
            isRestart = 1
            f = open('data/pois.csv', 'w', encoding='utf-8')

    else:
        f = open('data/pois.csv', 'w', encoding='utf-8')

    wr = csv.writer(f)
    if isRestart == 0:
        wr.writerow(['名称', '英文名', 'id', 'poiID', '经度', '维度', '标签', '特色', '价格', '最低价格', '评价分数',
                     '评论数量', '封面图片', '成人票价格', '老人票价格', '学生票价格', '儿童票价格', '建议游玩', '开放时间', '介绍', '优待政策'])

    # 最大页数
    for page in range(1, 5000):
        print(f'开始爬取第{page}页')
        data['index'] = page
        poiListRes = post(URL, json=data)
        if not poiListRes.json().get('result'):
            print(poiListRes.json())
            break
        poiList = poiListRes.json()['result']['sightRecreationList']
        if len(poiList) == 0:  # 如果此页没有数据，说明爬取结束或者出错了
            break
        for poi in poiList:
            row = []
            ID = poi.get('id', '')
            print(poi.get('name'), end='')
            if isRestart and int(ID) in history:
                print(' 已存在')
                continue
            print()
            row.append(poi.get('name', ''))  # 名称
            row.append(poi.get('eName', ''))  # 英文名
            row.append(ID)  # id

            poiID = poi.get('poiId', '')
            row.append(poiID)  # poiId
            row.append(poi['coordInfo']['gDLat'])  # 经度
            row.append(poi['coordInfo']['gDLon'])  # 维度

            tagSet = set()
            tagSet.update(poi.get('resourceTags', []))
            tagSet.update(poi.get('tagNameList', []))
            tagSet.update(poi.get('themeTags', []))
            tagStr = '|'.join(tagSet)
            row.append(tagStr)  # 标签

            row.append('|'.join(poi.get('shortFeatures', [])))  # 特色

            row.append(poi.get('price', 0))  # 价格
            row.append(poi.get('displayMinPrice', 0))  # 最低价格

            commentScore = poi.get('commentScore')
            if not commentScore:
                commentScore = 0.0
            row.append(commentScore)  # 评价分数
            commentCount = poi.get('commentCount')
            if not commentCount:
                commentCount = 0
            row.append(commentCount)  # 评论数量

            row.append(poi.get('coverImageUrl', ''))  # 封面
            row += GetTicketPrice(spotid=ID, poiId=poiID)
            row += GetDetail(poiId=poiID)
            ertong = row[-1].get('儿童')
            yhbj = 0
            free = 0
            if ertong:
                for i in ertong:
                    if '半价' in i[1] or '优惠' in i[1]:
                        yhbj = 1
                    elif i[1] == '免费':
                        free = 1
                if yhbj == 0 and free == 1:
                    row[-5] = 0  # 儿童票免费

            wr.writerow(row)

            time.sleep(1)

            if isCrawlComment == 1: # 爬取评论
                try:
                    print(f'开始爬取{poi.get("name", "")}评论')
                    GetComments(ID, commentCount)
                except Exception as e:
                    print(e)
                    logging.error(f'爬取{poi.get("name", "")}评论错误！')

        time.sleep(2)

    f.close()
