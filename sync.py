# -*- encoding: utf-8 -*-
import os
import re
import time
import json
import requests
from oauth_hook import OAuthHook
from werkzeug.http import parse_date

from zhejiangair import db, Feed, Bind

OAuthHook.consumer_key = os.environ.get('WEIBO_CONSUMER_KEY')
OAuthHook.consumer_secret = os.environ.get('WEIBO_CONSUMER_SECRET')


ZJA_TIMELINE_URL = 'http://api.twitter.com/1/statuses/user_timeline.json?user_id=536194664&screen_name=ZhejiangAir'
STATUSES_UPDATE_URL = 'http://api.t.sina.com.cn/statuses/update.json'

T_CO_RE = re.compile(r'http://t.co/[^ ]*')
BIT_LY_RE = re.compile(r'http://bit.ly/[^ ]*')


last_feed = Feed.query.order_by(Feed.id.desc()).first()
if last_feed:
    ZJA_TIMELINE_URL += '&since_id=' + str(last_feed.tid)

r = requests.get(ZJA_TIMELINE_URL)
if r.status_code == 200:
    for tweet in reversed(json.loads(r.content)):
        status = tweet['text']
        if not (u"空气质量" in status and u"浓度" in status and u"等级" in status):
            continue
        f = Feed(tweet['id'], status, parse_date(tweet['created_at']))
        db.session.add(f)
    db.session.commit()


bind = Bind.query.filter_by(to='weibo').first()
oauth_hook = OAuthHook(bind.token, bind.secret, header_auth=True)
client = requests.session(hooks={'pre_request': oauth_hook})
expander = requests.session()
for feed in Feed.query.filter_by(synced=False).order_by(Feed.id.asc()).all():
    status = feed.text
    status = T_CO_RE.sub(lambda match: expander.get(match.group(), allow_redirects=False).headers['location'], status)
    status = BIT_LY_RE.sub(lambda match: expander.get(match.group(), allow_redirects=False).headers['location'], status)
    r = client.post(STATUSES_UPDATE_URL, data={"status": status})
    if r.status_code != 200:
        print feed.tid, r.content
    feed.text = status
    feed.synced = True
    db.session.commit()
    time.sleep(2.1)
