#! /usr/bin/env python
# encoding:utf-8

'''
1日分のツイートをまとめてFacebookに投稿する
'''

import tweepy, codecs, sys, httplib2
from datetime import datetime, timedelta
from urllib import urlencode
from xml.sax.saxutils import escape

sys.stdout = codecs.lookup('utf_8')[-1](sys.stdout)

# 設定情報
# 空文字になってるところは適切な値ですべて埋めるべし
config = dict(
    twitter = dict(
        consumer_key = '',
        consumer_secret = '',
        access_key = '',
        access_secret = '',
        screen_name = '',
        max_tweets = 100,
    ),
    facebook = dict(
        access_token = '',
        user_id = '',
        message_size = 410,
    ),
)

def getMyTweetsInYesterday():
    '''昨日の自分のツイートを得る'''
    consumer_key = config['twitter']['consumer_key']
    consumer_secret = config['twitter']['consumer_secret']
    access_key = config['twitter']['access_key']
    access_secret = config['twitter']['access_secret']
    screen_name = config['twitter']['screen_name']
    max_tweets = config['twitter']['max_tweets']
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    tweets = []
    
    yesterday = datetime.now() - timedelta(days = 1)
    _from = yesterday.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    _to = _from + timedelta(days = 1)
    
    for i, status in enumerate(tweepy.Cursor(api.user_timeline, screen_name = screen_name).items()):
        if not status.in_reply_to_status_id:
            # UTCからJSTに変換
            status.created_at += timedelta(hours = 9)
            if status.created_at < _to:
                if status.created_at >= _from:
                    tweets.append(status)
                    # print status.created_at, status.text
                else:
                    break
        if i > max_tweets:
            break
    
    return tweets

def createMessages(tweets):
    '''facebookに投稿するためのメッセージを作成する'''
    message_size = config['facebook']['message_size']
    
    yesterday = datetime.now() - timedelta(days = 1)
    messages = []
    
    if tweets:
        tweets.reverse()
        # message_sizeを超えないように分割する
        i = 1
        message = u'%d月%d日のツイート一覧（%d/%s）\n' % (
            yesterday.month,
            yesterday.day,
            i,
            '%d',
        )
        for tweet in tweets:
            line = u'%02d:%02d %s\n' % (
                tweet.created_at.hour,
                tweet.created_at.minute,
                tweet.text,
            )
            if len(message) + len(line) > message_size:
                messages.append(message)
                i += 1
                message = u'%d月%d日のツイート一覧（%d/%s）\n' % (
                    yesterday.month,
                    yesterday.day,
                    i,
                    '%d',
                )
            message += line
        messages.append(message)
        
        # 1/?の表記を完成させる
        for j, message in enumerate(messages):
            messages[j] = message % i
    
    return messages

def sendMessagesToFacebook(messages):
    '''メッセージをfacebookに投稿する'''
    access_token = config['facebook']['access_token']
    user_id = config['facebook']['user_id']
    
    if messages:
        for message in messages:
            http = httplib2.Http()
            data = dict(
                access_token = access_token,
                message = escape(message.encode('utf-8')),
            )
            response, content = http.request(
                'https://graph.facebook.com/%s/feed' % user_id,
                'POST',
                urlencode(data),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            #print response, content
            #print message

def main():
    tweets = getMyTweetsInYesterday()
    messages = createMessages(tweets)
    sendMessagesToFacebook(messages)

if __name__ == "__main__":
    main()