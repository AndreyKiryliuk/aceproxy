#!/usr/bin/python
# -*- coding: utf-8 -*-


import urllib
import urllib2
# from modules.PlaylistGenerator import PlaylistGenerator

siteUrl = 'rutor.info'
httpSiteUrl = 'http://' + siteUrl

# ru_film = '5'
# en_film = '1'
# nauka = '12'
# serial = '4'
# tv_video = '6'
# mult = '7'
# anime = '10'
# all_cat = '0'
#
# sort_data = '0'
# sort_sid = '2'
# sort_name = '6'
#
# tab = "[COLOR 00000000]_[/COLOR]"
# L = ['1', '2', '3', '4']

# http://rutor.org/search/0/12/000/2/ -- Науч поп
# http://rutor.org/search/0/5/000/2/ -- ru
# http://rutor.org/search/0/1/000/2/ -- en
# http://rutor.org/search/0/4/000/2/ -- serial
# http://rutor.org/search/0/6/000/2/ -- tv
# http://rutor.org/search/0/7/000/2/ -- mult
# http://rutor.org/search/0/10/000/2/ -- anime
# http://rutor.org/search/0/0/000/2/ -- all

# SLk1 = ["0", "1", "5", "4", "7", "10", "12", "6"]
# SLk2 = ["Все", "Зарубежные фильмы", "Русские фильмы", "Сериалы", "Мультфильмы", "Аниме", "Научно-популярное", "ТВ"]
# SLg = ["Все", "Арт-хаус", "Биография", "Боевик", "Вестерн", "Военный", "Детектив", "Детский", "Драма", "Исторический", "Комедия", "Короткометражка", "Криминал", "Мелодрама", "Мистика", "Мюзикл", "Нуар", "Пародия ", "Приключения", "Романтика", "Семейный", "Сказка", "Спорт", "Триллер", "Ужасы", "Фантастика", "Фэнтези", "Советское кино", "СССР", "Союзмультфильм", "Disney", "вампиры", "война", "детектив", "история", "киберпанк", "меха", "мистерия", "музыкальный", "паропанк", "повседневность", "полиция", "постапокалиптика", "психология", "романтика", "Эротика"]
# SLy = ["Все", "2014", "2013", "2012", "2011", "2010", "2009", "2008", "2007", "2006", "2005", "2004", "2003", "2002", "2001", "2000", "1999", "1998", "1997", "1996", "1995", "1994", "1993", "1992", "1991", "1990", "1989", "1988", "1987", "1986", "1985", "1984", "1983", "1982", "1981", "1980", "1979", "1978", "1977", "1976", "1975", "1974", "1973", "1972", "1971", "1970", "1969", "1968", "1967", "1966", "1965", "1964", "1963", "1962", "1961", "1960", "1959", "1958", "1957", "1956", "1955", "1954", "1953", "1952", "1951", "1950", "1949", "1948", "1947", "1946", "1945", "1944", "1943", "1942", "1941", "1940", "1939", "1938", "1937", "1936", "1935", "1934", "1933", "1932", "1931", "1930"]
# SLq = ["Все", "Blu-ray", "BDRemux", "BDRip", "HDRip", "WEB-DL", "WEB-DLRip", "HDTV", "HDTVRip", "DVD9", "DVD5", "DVDRip", "DVDScr", "DVB", "SATRip", "IPTVRip", "TVRip", "VHSRip", "TS", "CAMRip", "720p", "1080i"]
#
# SLk1 = ["0", "1", "5", "4", "7", "10", "12", "6"]
# "Все", "Зарубежные фильмы", "Русские фильмы", "Сериалы", "Мультфильмы", "Аниме", "Научно-популярное", "ТВ"
#
# CATEGORIES = [
# {'id': 0, 'title': "Все"},
# {'id': 1, 'title': "Зарубежные фильмы"},
# {'id': 5, 'title': "Русские фильмы"},
# {'id': 4, 'title': "Сериалы"},
# {'id': 7, 'title': "Мультфильмы"},
# {'id': 10, 'title': "Аниме"},
# {'id': 12, 'title': "Научно-популярное"},
# {'id': 6, 'title': "ТВ"},
# ]


def ru(x):return unicode(x, 'utf8', 'ignore')


def GET(target, referer, post=None):
    try:
        req = urllib2.Request(url=target, data=post)
        req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
        resp = urllib2.urlopen(req)
        http = resp.read()
        resp.close()
        return http
    except Exception, e:
        print 'HTTP ERROR', e


def cleartext(text):
    text = text.replace("http://s.rutor.info/", '/s/')
    text = text.replace('</td><td ><a class="downgif" href="', "', '")
    text = text.replace('"><img src="/s/t/d.gif" alt="D" /></a><a href="magnet:?xt=', "', '")
    text = text.replace('alt="M" /></a><a href="/torrent/', "', '")
    text = text.replace('</a></td> <td align="right">', "', '")
    text = text.replace('<img src="/s/t/com.gif" alt="C" /></td><td align="right">', "', '")
    text = text.replace('</td><td align="center"><span class="green"><img src="/s/t/arrowup.gif" alt="S" />', "', '")
    text = text.replace('</span><img src="/s/t/arrowdown.gif" alt="L" /><span class="red">', "', '")
    text = text.replace('">', "', '")
    text = text.replace('</span></td></tr>', "']")
    text = text.replace('</span>', "']")
    text = text.replace("</table>", "\r")
    return text

def formtext(http):
    http = http.replace(chr(10), "")  # .replace(chr(13),"")
    http = http.replace('&#039;', "").replace('colspan = "2"', "").replace('&nbsp;', "")  # исключить
    http = http.replace('</td></tr><tr class="gai"><td>', "\rflag1 ['")
    http = http.replace('</td></tr><tr class="gai">', "\rflag1 ")  # начало
    # http=http.replace('/></a>\r<a href',' *** ').replace('alt="C" /></td>\r<td align="right"',' *** ') #склеить
    http = http.replace('<tr class="tum"><td>', "\rflag1 ['").replace('<tr class="gai"><td>', "\rflag1 ['")  # разделить
    http = cleartext(http)
    return http


def upd(category, sort, text, n):
    try: n = str(int(n))
    except: n = "0"
    if text == '0':stext = ""
    elif text == '1':stext = text
    elif text <> '':stext = text
    stext = stext.replace("%", "%20").replace(" ", "%20").replace("?", "%20").replace("#", "%20")
    if stext == "":
        categoryUrl = httpSiteUrl + '/browse/' + n + '/' + category + '/0/' + sort
    else:
        if text == '1':categoryUrl = httpSiteUrl + '/search/' + n + '/' + category + '/000/' + sort + '/' + stext  # )xt( 0/1/110/0
        else: categoryUrl = httpSiteUrl + '/search/' + n + '/' + category + '/110/' + sort + '/' + stext

    print 'categoryUrl=%s' % categoryUrl
    http = GET(categoryUrl, httpSiteUrl, None)

    if http == None:
        print 'RuTor:', 'Сервер не отвечает', 1000
        return None
    else:
        http = formtext(http)

        LL = http.splitlines()
        return LL


def format_list(L):
    if L == None:
        return ["", "", "", "", "", "", "", "", ""]
    else:
        Ln = []
        i = 0
        for itm in L:
            i += 1
            if len(itm) > 6:
                if itm[:5] == "flag1":
#                     print itm
#                     print 'tut'
#                     print itm[6:]
#                     a = eval(itm[6:])
#                     print a
#                     exit()
                    try:Ln.append(eval(itm[6:]))
                    except: pass
        return Ln

def rulower(text):
    text = text.strip()
    text = text.lower()
    return text


def SearchN(category, sort, text, filtr, page='0', min_size=0, max_size=0, min_peers=0, max_peers=0):
    if text == "   ": text = "0"
    if text == "    ": text = "0"

    HideScr = 'true'
    HideTSnd = 'true'
    TitleMode = '1'
    EnabledFiltr = 'false'
    Filtr = ''

    RL = upd(category, sort, text, page)
    RootList = format_list(RL)
    k = 0
    TLD = []

    items = []

    defekt = 0
    for tTitle in RootList:
        if len(tTitle) == 9:
            tTitle.insert(6, " ")

        if len(tTitle) == 10 and int(tTitle[8]) > 0:

            size = tTitle[7]
            # print "size1='%s'" % size
            if size[-2:] == "MB":size = size[:-5] + "MB"

            if min_size or max_size:
                csize = 0
                if size[-2:] == "MB":
                    try:
                        csize = float(size[:-2])
                    except:
                        csize = 0
                elif size[-2:] == "GB":
                    csize = size[:-2]
                    try:
                        csize = float(size[:-2]) * 1024
                    except:
                        csize = 0
                if csize:
                    if not (min_size <= csize <= max_size):
                        continue

#             if len(size) == 3:size = size.center(10)
#             elif len(size) == 4:size = size.center(9)
#             elif len(size) == 5:size = size.center(8)
#             elif len(size) == 6:size = size.center(8)

            # print "size2='%s'" % size

            if len(tTitle[8]) == 1:sids = tTitle[8].center(9)
            elif len(tTitle[8]) == 2:sids = tTitle[8].center(8)
            elif len(tTitle[8]) == 3:sids = tTitle[8].center(7)
            elif len(tTitle[8]) == 4:sids = tTitle[8].center(6)
            else:sids = tTitle[8]

            if min_peers or max_peers:
                try:
                    if not (min_peers <= int(sids) <= max_peers):
                        continue
                except Exception, e:
                    print e
            #------------------------------------------------
            k += 1
            nnn = tTitle[1].rfind("/") + 1
            ntor = tTitle[1][nnn:]
            if k < 115:
                #   nnn=tTitle[1].rfind("/")+1
                #   ntor=xt(tTitle[1][nnn:])
                # dict=get_minfo(ntor)
                # try:dict=get_minfo(ntor)
                # except:dict={}
                # try:cover=dict["cover"]
                # except:cover=""
                pass
            #-------------------------------------------------

            # Title = "|"+sids+"|"+size+"|  "+tTitle[5]
            Title = "|" + sids + "|  " + tTitle[5]

            flt4 = 0
            flt2 = 0
            flt3 = 0
            ltl = rulower(Title)
            if filtr[4] == "" or ltl.find(rulower(filtr[4])) > 0: flt4 = 1
            if filtr[2] == "" or tTitle[5].find(filtr[2].replace("1990", "199").replace("1980", "198").replace("1970", "197").replace("1960", "196").replace("1950", "195").replace("1940", "194").replace("1930", "193")) > 0: flt2 = 1
            if filtr[3] == "" or Title.find(filtr[3]) > 0: flt3 = 1
            Sflt = flt4 + flt2 + flt3


            if HideScr == 'true':
                nH1 = Title.find("CAMRip")
                nH2 = Title.find(") TS")
                nH3 = Title.find("CamRip")
                nH4 = Title.find(" DVDScr")
                nH = nH1 + nH2 + nH3 + nH4
            else:
                nH = -1

            if HideTSnd == 'true':
                sH = Title.find("Звук с TS")
            else:
                sH = -1

            if TitleMode == '1':
                k1 = Title.find('/')
                if k1 < 0: k1 = Title.find('(')
                tmp1 = Title[:k1]
                n1 = Title.find('(')
                k2 = Title.find(' от ')
                if k2 < 0: k2 = None
                tmp2 = Title[n1:k2]
                Title = tmp1 + tmp2
                Title = Title.replace("| Лицензия", "")
                Title = Title.replace("| лицензия", "")
                Title = Title.replace("| ЛицензиЯ", "")


            tTitle5 = ru(tTitle[5].strip().replace("ё", "е"))
            nc = tTitle5.find(") ")
            nc2 = tTitle5.find("/ ")
            if nc2 < nc and nc2 > 0: nc = nc2
            CT = rulower(tTitle5[:nc]).strip()

            # Title=CT
            if Sflt == 3 and nH < 0 and sH < 0 and (CT not in TLD):

                # dict = get_minfo(ntor)
                # try:dict_info = get_minfo(ntor)
                # except:dict_info = {}
                dict_info = {}
#                 try:cover = dict_info["cover"]
#                 except:cover = ""
                dict_info['ntor'] = ntor
                UF = 0
                if EnabledFiltr == 'true' and Filtr <> "":
                    Fnu = Filtr.replace(",", '","')
                    Fnu = Fnu.replace('" ', '"')
                    F1 = eval('["' + Fnu + '", "4565646dsfs546546"]')
                    Tlo = rulower(Title)
                    try:Glo = rulower(dict_info['genre'])
                    except: Glo = "45664sdgd6546546"
                    for Fi in F1:
                        if Tlo.find(rulower(Fi)) >= 0:UF += 1
                        if Glo.find(rulower(Fi)) >= 0:UF += 1
                Tresh = ["Repack", " PC ", "XBOX", "RePack", "FB2", "TXT", "DOC", " MP3", " JPG", " PNG", " SCR"]
                for TRi in Tresh:
                    if tTitle[5].find(TRi) >= 0:UF += 1
                if UF == 0:
                    TLD.append(CT)
                    row_url = tTitle[1]
                    Title = Title.replace("&quot;", '"')

#                     listitem = xbmcgui.ListItem(Title, thumbnailImage=cover, iconImage=cover)
#                     try:listitem.setInfo(type="Video", infoLabels=dict_info)
#                     except: pass

#                     try:fanart = dict_info['fanart']
#                     except:fanart = cover

#                     print 'sids="%s"' % sids
#                     print 'size="%s"' % size
#                     print 'tTitle[5]="%s"' % tTitle[5]
#                     exit()

                    Title = "[%s]" % unicode(str(sids.strip() + " | " + size.strip() + " | " + tTitle[5].strip()), 'utf-8')
                    itemdict = {'title': Title,
                                'url': '/rutor/list/%s/' % urllib.quote_plus(httpSiteUrl + row_url),
                                'description_title': Title,
                                'description': '',
                                'type': 'channel'
                                }
                    items.append(itemdict)

#                     listitem.setProperty('fanart_image', fanart)
#                     purl = sys.argv[0] + '?mode=OpenCat2'\
#                         + '&url=' + urllib.quote_plus(row_url)\
#                         + '&title=' + urllib.quote_plus(str(sids + "|" + size + "| " + tTitle[5]))\
#                         + '&info=' + urllib.quote_plus(repr(dict))
#                     xbmcplugin.addDirectoryItem(handle, purl, listitem, True, totalItems=len(RootList) - defekt)
                else: defekt += 1
            else: defekt += 1

    return items


if __name__ == '__main__':

    category = '1'
    sort = '0'
    text = '0'
    n = '0'
    spr = ["", "", "", "", "", ""]
    url = '0'
    # playlist = SearchN(category, sort, text, spr, url)
    # print playlist.exportxml('127.0.0.1:8000')

    # RL = upd(category, sort, text, url)
    # RootList = format(RL)
    # print RootList
    url = 'http%3A%2F%2Fd.rutor.info%2Fdownload%2F499769'
    name = '+++67+++%7C+4.50GB+%7C+%D0%9F%D0%BB%D0%B5%D0%BC%D1%8F%D0%BD%D0%BD%D0%B8%D1%86%D1%8B+%D0%B3%D0%BE%D1%81%D0%BF%D0%BE%D0%B6%D0%B8+%D0%BF%D0%BE%D0%BB%D0%BA%D0%BE%D0%B2%D0%BD%D0%B8%D1%86%D1%8B+%2F+Die+Nichten+der+Frau+Oberst+%281980%29+BDRip+720p+%7C+A+'
    dict_info = {'ntor': '499967'}
    # res = OpenCat(url, name, dict_info)
    # print res
