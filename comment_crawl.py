import logging
import time
from requests import post
import csv

URL = 'https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList'  # 获取评论数据列表的URL
SizePerPage = 20    # 每页的数据量，最好不好随意改变
data = {"arg": {"resourceId": 229, "resourceType": 11, "pageIndex": 1, "pageSize": SizePerPage, "sortType": 3, "commentTagId": "0",
                "collapseType": 1, "channelType": 7, "videoImageSize": "700_392", "starType": 0},
        "head": {"cid": "09031065211914680477", "ctok": "", "cver": "1.0", "lang": "01", "sid": "8888", "syscode": "09",
                 "auth": None, "extension": [{"name": "protocal", "value": "https"}]}, "contentType": "json"}


def GetComments(Id, total):
    f = open(f'data/comments/{Id}.csv', 'w', encoding='utf-8')
    DATA = data.copy()
    DATA['arg']['resourceId'] = Id
    wr = csv.writer(f)
    times = total // SizePerPage
    for i in range(times):
        DATA['arg']['pageIndex'] = i + 1
        resp = post(URL, json=DATA)
        comments = resp.json()['result']['items']
        if not comments:
            print(resp.json())
            break
        for comment in comments:
            if comment.get('languageType', '') != "zh-cn" or len(comment['content']) < 10:
                continue
            userId = comment.get('userInfo')
            if userId:
                userId = userId.get('userId', 'null')

            rrr = [userId, comment['content'], comment['publishTime'], comment['usefulCount']]
            wr.writerow(rrr)
            print(comment['content'])

        time.sleep(1)
        resp.close()

    f.close()


if __name__ == '__main__':
    with open('data/pois.csv', 'r', encoding='utf-8') as f:
        rd = csv.reader(f)
        cnt = 0
        flag = 0
        for row in rd:
            if cnt == 0:
                cnt = 1
                continue
            ID = int(row[2])
            print(ID, row[0])
            GetComments(ID, int(row[11]))
