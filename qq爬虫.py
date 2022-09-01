import requests
import numpy as np
from urllib import request
import cv2
import re
import threading
import json
import time
#扫码登陆
def QZloginListen(res):
    image = np.asarray(bytearray(res.content), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    cv2.imshow('url_image_show', image)
    cv2.waitKey(60000)
def QZlogin():
    res=requests.get("https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.7760829555362458&daid=5&pt_3rd_aid=0")
    cookies=res.cookies.get_dict()
    qrsig=cookies["qrsig"]
    threading.Thread(target=QZloginListen,args=(res,)).start()
    #轮询
    ptqrtoken=getQZptqrtoken(qrsig)
    while True:
        res1=requests.get("https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptqrtoken="+str(ptqrtoken)+"&ptredirect=0&h=1&t=1&g=1&from_ui=1&aid=549000912&daid=5",cookies=cookies)
        r11=re.findall("ptuiCB\((.*?)\)",res1.text)
        r1=r11[0].split("','")
        code=int(r1[0][1:])
        if code==65:
            print("二维码过期，已刷新")
            cv2.destroyAllWindows()
            QZlogin()
        if code==67:
            print("验证中...请在手机上确认")
        if code==0:
            url=r1[2]
            print("验证成功")
            cv2.destroyAllWindows()
            #吐槽一句，不晓得为啥要加这句·，测试发现不加就挂机
            time.sleep(1)
            res2=requests.get(url,allow_redirects=False)
            if res2.status_code==302:
                cookies=res2.headers
                print("登陆成功")
                return res2.cookies.get_dict()
        time.sleep(1)
#计算ptrtoken
def getQZptqrtoken(qrsig):
    hash=0
    for c in qrsig:
        hash += (((hash << 5) & 0x7fffffff) + ord(c)) & 0x7fffffff;
    return  str(0x7fffffff & hash)
#计算gtk
def getQZgtk(pskey):
    hash=5381
    for c in pskey:
        hash += (((hash << 5) & 0x7fffffff) + ord(c)) & 0x7fffffff;
    return str(hash & 0x7fffffff)
#获取指定QQ资料
def getQZuserInfo(uin,cookies):
    vuin=cookies["uin"][1:]
    gtk=getQZgtk(cookies["p_skey"])
    res=requests.get("https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?uin="+uin+"&vuin="+vuin+"&format=json&fupdate=1&rd=0.01702994398051061&g_tk="+getQZgtk(cookies["p_skey"]),cookies=cookies)
    return res.text
#获取说说,返回说说源码,解析交给后人了,一页10条说说
def getQZSS(uin,page,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    vuin=cookies["uin"][1:]
    res=requests.get("https://user.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds_html_act_all?format=json&uin="+vuin+"&hostuin="+uin+"&scope=0&filter=all&flag=1&refresh=0&firstGetGroup=0&mixnocache=0&scene=0&begintime=undefined&icServerTime=&start="+str(page*10)+"&count=10&sidomain=qzonestyle.gtimg.cn&useutf8=1&outputhtmlfeed=1&refer=2&r=0.4629593313378182&g_tk="+gtk,cookies=cookies)
    r=re.compile("html:'(.*?)',opuin",re.S)
    r1=re.findall(r,res.text)
    return r1
#获取最近访客，以及空间说说数量
def getQZnum(uin,cookies):
    vuin=cookies["uin"][1:]
    gtk=getQZgtk(cookies["p_skey"])
    res=requests.get("https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/main_page_cgi?format=json&uin="+uin+"&param=3_"+uin+"_0|8_8_"+vuin+"_1_1_0_0_1|15|16&g_tk="+gtk,cookies=cookies)
    r=re.compile("_Callback[(](.*?)[)]",re.S)
    r1=re.findall(r,res.text)
    return r1[0]
#获取说说访客
def getQZSSvistor(uin,ssid,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    res=requests.get("https://h5.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_single?format=json&uin="+uin+"&appid=311&blogid="+ssid+"&param="+ssid+"&ref=qzfeeds&beginNum=1&num=1000&g_tk="+gtk,cookies=cookies)

    r=re.compile(r'_Callback[(](.*?)[)]',re.S)
    r1=re.findall(r,res.text)
    return r1[0]
#cookies转换
def cookiesToStr(cookies):
    r=""
    for k,v in cookies.items():
        r+=k+"="+v+";"
    return r
#获取说说点赞人员
def getQZSSlike(uin,ssid,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    vuin=cookies["uin"][1:]
    res=requests.get("https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?uin="+vuin+"&unikey=http://user.qzone.qq.com/"+uin+"/mood/"+ssid+".1^||^0&g_iframeUser=1&g_iframedescend=1&begin_uin=0&query_count=60&if_first_page=1&g_tk="+gtk,cookies=cookies)
    res.encoding=res.apparent_encoding
    r=re.compile(r'_Callback[(](.*?)[)]',re.S)
    r1=re.findall(r,res.text)
    return r1[0]
#获取隐藏说说，理论上可行
def getQZSShide(uin,page,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    h={
        "referer":"https://user.qzone.qq.com/p/h5/pc/api/sns.qzone.qq.com/cgi-bin/qzshare/cgi_qzsharegetmylistbytype?uin="+uin+"&spaceuin="+uin+"&g_iframeUser=1"
    }
    res=requests.get("https://user.qzone.qq.com/p/h5/pc/api/sns.qzone.qq.com/cgi-bin/qzshare/cgi_qzsharegetmylistbytype?g_iframeUser=1&uin="+uin+"&page="+str(page)+"&num=10&spaceuin="+uin+"&isfriend=0&ttype=0",headers=h,cookies=cookies)
    return res.text
#获取相册
def getQZXC(uin,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    vuin=cookies["uin"][1:]
    res=requests.get("https://user.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3?format=json&g_tk="+gtk+"&callback=shine0_Callback&t=262536731&hostUin="+uin+"&uin="+vuin+"&appid=4&inCharset=utf-8&outCharset=utf-8&source=qzone&plat=qzone&format=jsonp&notice=0&filter=1&handset=4&pageNumModeSort=40&pageNumModeClass=15&needUserInfo=1&idcNum=4&callbackFun=shine0&_=1662039195159",cookies=cookies)
    return res.text
#查看相册图片
def getQZXCphotos(uin,xcid,page,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    vuin=cookies["uin"][1:]
    res=requests.get("https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_list_photo?format=json&g_tk="+gtk+"&callback=shine3_Callback&t=489505819&mode=0&idcNum=4&hostUin="+uin+"&topicId="+xcid+"&noTopic=0&uin="+vuin+"&pageStart="+str(page*30)+"&pageNum=30&skipCmtCount=0&singleurl=1&batchId=&notice=0&appid=4&inCharset=utf-8&outCharset=utf-8&source=qzone&plat=qzone&outstyle=json&format=json&json_esc=1&callbackFun=shine3&_=1662040302299",cookies=cookies)
    return res.text
#获取相册评论
def getQZXCcomments(uin,xcid,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    vuin=cookies["uin"][1:]
    res=requests.get("https://user.qzone.qq.com/proxy/domain/app.photo.qzone.qq.com/cgi-bin/app/cgi_pcomment_xml_v2?g_tk="+gtk+"&callback=shine1_Callback&t=1662040766157&hostUin="+uin+"&uin="+vuin+"&appid=4&cmtType=1&start=0&num=0&order=1&inCharset=utf-8&outCharset=utf-8&source=qzone&plat=qzone&format=json&topicId="+xcid+"&callbackFun=shine1&_=1662040765770",cookies=cookies)
    return res.text
#获取相册访客
def getQZXCvistor(uin,xcid,cookies):
    gtk=getQZgtk(cookies["p_skey"])
    res=requests.get("https://user.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_simple?uin="+uin+"&mask=2&mod=2&contentid="+xcid+"&fupdate=1&g_tk="+gtk,cookies=cookies)
    return res.text





#测试代码
cookies=QZlogin()
#cookies={'skey': '@uL553hvGt', 'uin': 'o3483421977', 'p_skey': '1EWMs-tuNgyW9TnAEY*GxsZ4nsex20BjjWIjLAg-ixI_', 'p_uin': 'o3483421977', 'pt4_token': 'OE*Xs38HUYnUBC4V*HLbHSjtZwdcmQYSWrRKom*QkJc_'}   
print(cookies)

print(getQZuserInfo("3521714145",cookies))
print(getQZSShide("3521714145",1,cookies))
print(getQZnum("3521714145",cookies))
print(getQZXC("3521714145",cookies))
print(getQZSS("3521714145",1,cookies))
print(getQZXCphotos("3521714145","V11E60q14RNdUs",1,cookies))
print(getQZXCcomments("3521714145","V11E60q14RNdUs",cookies))


