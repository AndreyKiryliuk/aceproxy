# -*- coding=utf-8 -*-

'''
This is the example of plugin.
Rename this file to helloworld_plugin.py to enable it.

To use it, go to http://127.0.0.1:8000/helloworld
'''

import traceback
import gevent
import gevent.monkey
# from gevent.queue import Full
# from acehttp import AceStuff
# Monkeypatching and all the stuff
gevent.monkey.patch_all()
import aceclient
import base64
import json
import logging
import urllib2
import urlparse
import vlcclient
from modules.PluginInterface import AceProxyPlugin
from httpclient.httpclient import Client
# from datetime import datetime
import time
import uuid
import Cookie

VIDEO_DESTROY_DELAY = 3

class Playtorrent(AceProxyPlugin):
    handlers = ('playtorrent', 'playpid')

    def __init__(self, AceConfig, AceStuff):
        self.params = None
        self.AceConfig = AceConfig
        self.AceStuff = AceStuff
        self.logger = logging.getLogger('playtorrent')

    def handle(self, connection, headers_only=False):
        #self.connection = connection
        query = urlparse.urlparse(connection.path).query
        self.params = urlparse.parse_qs(query)

        # self.logger.debug('connection.reqtype=%s' % connection.reqtype)
        # self.logger.debug(len(connection.splittedpath))
        # self.logger.debug('connection.splittedpath=%s' % connection.splittedpath)

        if connection.reqtype == 'playtorrent':
            self.handlePlay(connection, headers_only)


    def handlePlay(self, connection, headers_only, channelName=None, channelIcon=None, fmt=None):
        logger = logging.getLogger('handlePlay')
        logger.debug("connection=%s" % (connection))
        connection.requrl = urlparse.urlparse(connection.path)
        connection.reqparams = urlparse.parse_qs(connection.requrl.query)
        connection.path = connection.requrl.path[:-1] if connection.requrl.path.endswith('/') else connection.requrl.path
        for key in connection.headers.dict:
            logger.debug("%s: %s" % (key, connection.headers.dict[key]))
        # Check if third parameter exists
        # …/pid/blablablablabla/video.mpg
        #                      |_________|
        # And if it ends with regular video extension
        try:
            if not connection.path.endswith(('.3gp', '.avi', '.flv', '.mkv', '.mov', '.mp4', '.mpeg', '.mpg', '.ogv', '.ts')):
                logger.error("Request seems like valid but no valid video extension was provided")
                connection.dieWithError(400)
                return
        except IndexError:
            logger.error("Index error")
            connection.dieWithError(400)  # 400 Bad Request
            return

        # Limit concurrent connections
        if 0 < self.AceConfig.maxconns <= self.AceStuff.clientcounter.total:
            logger.debug("Maximum connections reached, can't serve this")
            connection.dieWithError(503)  # 503 Service Unavailable
            return

        # Pretend to work fine with Fake UAs or HEAD request.
        useragent = connection.headers.get('User-Agent')
        fakeua = useragent and useragent in self.AceConfig.fakeuas
        if headers_only or fakeua:
            if fakeua:
                logger.debug("Got fake UA: " + connection.headers.get('User-Agent'))
            # Return 200 and exit
            connection.send_response(200)
            connection.send_header("Content-Type", "video/mpeg2")
            connection.end_headers()
            connection.closeConnection()
            return

        # Make list with parameters
        connection.params = list()
        for i in xrange(3, 8):
            try:
                connection.params.append(int(connection.splittedpath[i]))
            except (IndexError, ValueError):
                connection.params.append('0')

        connection.url = None
        connection.path_unquoted = urllib2.unquote(connection.splittedpath[2])
        contentid = connection.getCid(connection.reqtype, connection.path_unquoted)
        cid = contentid if contentid else connection.path_unquoted
        # cid = str(datetime.now()) + ' ' + cid
        uid = ''
        if "Cookie" in connection.headers:
            c = Cookie.SimpleCookie(connection.headers["Cookie"])
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print c['uid'].value
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            if c['uid'].value:
                uid = c['uid'].value
        if not uid:
            uid = uuid.uuid1().hex
        cid = cid + ' ' + uid
        logger.debug("CID: " + cid)
        
        
        connection.client = Client(cid, connection, channelName, channelIcon)
        logger.debug("%s: client=%s" % (cid, connection.client))
        connection.vlcid = urllib2.quote(cid, '')
        # connection.client = self.AceStuff.clientcounter.add(cid, connection.client)

        shouldStart = self.AceStuff.clientcounter.check_cid(cid)
        logger.debug("%s: shouldStart=%s" % (cid, shouldStart))
        while self.AceStuff.clientcounter.check_pt(cid, connection.client):
            logger.debug("%s: sleep1" % (cid,))
            time.sleep(1)

        self.AceStuff.clientcounter.add_pt(cid, connection.client)


        # shouldStart = self.AceStuff.clientcounter.add_pt(cid, connection.client)
        logger.debug("%s: client=%s" % (cid, connection.client))
        logger.debug("%s: connection=%s" % (cid, connection))



        # Send fake headers if this User-Agent is in fakeheaderuas tuple
        if fakeua:
            logger.debug(
                "Sending fake headers for " + useragent)
            connection.send_response(200)
            connection.send_header("Content-Type", "video/mpeg3")
            connection.end_headers()
            # Do not send real headers at all
            connection.headerssent = True
        logger.debug("%s: client=%s" % (cid, connection.client))
        logger.debug("%s: connection=%s" % (cid, connection))
#         while not connection:
#             logger.debug("%s wait connection.ace" % cid)
#             time.sleep(1)
#
#         while not connection.client.ace:
#             logger.debug("%s wait connection.client.ace" % cid)
#             time.sleep(1)
        try:
            connection.errorhappened = False
            # Initializing AceClient
            if shouldStart:
                if contentid:
                    connection.client.ace.START('PID', {'content_id': contentid})
                elif connection.reqtype == 'playpid':
                    connection.client.ace.START(
                        connection.reqtype, {'content_id': connection.path_unquoted, 'file_indexes': connection.params[0]})
                elif connection.reqtype == 'playtorrent':
                    paramsdict = dict(
                        zip(aceclient.acemessages.AceConst.START_TORRENT, connection.params))
                    paramsdict['url'] = connection.path_unquoted
                    connection.client.ace.START('torrent', paramsdict)
                logger.debug("START done")
                logger.debug("%s: connection=%s" % (cid, connection))
                # Getting URL
                connection.url = connection.client.ace.getUrl(self.AceConfig.videotimeout)
                logger.debug("getting url done")
                logger.debug("%s: connection=%s" % (cid, connection))
                # Rewriting host for remote Ace Stream Engine
                connection.url = connection.client.ace.url = connection.url.replace('127.0.0.1', self.AceConfig.acehost)
                connection.client.ace.req_headers = {}
                
#                 #connection.url = connection.client.ace.url = connection.url.replace('127.0.0.1', '176.124.137.239')
#                 #self.url = self.url.replace('127.0.0.1', '192.168.0.214')
#                 logger.debug('redirect to: %s' % connection.url)
#                 connection.send_response(302)
#                 connection.send_header("Location", connection.url)
#                 connection.end_headers()
#                 time.sleep(200)
#                 return

                logger.debug("Got url " + connection.url)
                # If using VLC, add this url to VLC
                if self.AceConfig.vlcuse:
                    # Force ffmpeg demuxing if set in config
                    if self.AceConfig.vlcforceffmpeg:
                        connection.vlcprefix = 'http/ffmpeg://'
                    else:
                        connection.vlcprefix = ''

                    connection.client.ace.pause()
                    # Sleeping videodelay
                    gevent.sleep(self.AceConfig.videodelay)
                    connection.client.ace.play()

                    self.AceStuff.vlcclient.startBroadcast(
                        connection.vlcid, connection.vlcprefix + connection.url, self.AceConfig.vlcmux, self.AceConfig.vlcpreaccess)
                    # Sleep a bit, because sometimes VLC doesn't open port in
                    # time
                    gevent.sleep(0.5)
            else:
                logger.debug('connection.url: %s' % connection.url)
                logger.debug('connection.client.ace.url: %s' % connection.client.ace.url)
                connection.url = connection.client.ace.url

#             self.hanggreenlet = gevent.spawn(connection.hangDetector)
#             logger.debug("hangDetector spawned")
#             gevent.sleep()

            # Building new VLC url
            if self.AceConfig.vlcuse:
                connection.url = 'http://' + self.AceConfig.vlchost + \
                    ':' + str(self.AceConfig.vlcoutport) + '/' + connection.vlcid
                logger.debug("VLC url " + connection.url)

                # Sending client headers to videostream
                connection.video = urllib2.Request(connection.url)
                for key in connection.headers.dict:
                    connection.video.add_header(key, connection.headers.dict[key])

                connection.video = urllib2.urlopen(connection.video)

                # Sending videostream headers to client
                if not connection.headerssent:
                    connection.send_response(connection.video.getcode())
                    if connection.video.info().dict.has_key('connection'):
                        del connection.video.info().dict['connection']
                    if connection.video.info().dict.has_key('server'):
                        del connection.video.info().dict['server']
                    if connection.video.info().dict.has_key('transfer-encoding'):
                        del connection.video.info().dict['transfer-encoding']
                    if connection.video.info().dict.has_key('keep-alive'):
                        del connection.video.info().dict['keep-alive']

                    for key in connection.video.info().dict:
                        connection.send_header(key, connection.video.info().dict[key])
                    # End headers. Next goes video data
                    connection.end_headers()
                    logger.debug("Headers sent")

                # Run proxyReadWrite
                # connection.proxyReadWrite()
                connection.client.handle(self.AceStuff, shouldStart, self.url, fmt, connection.headers)
            else:
                if not fmt:
                    fmt = connection.reqparams.get('fmt')[0] if connection.reqparams.has_key('fmt') else None

#                 connection.client.handle(self.AceStuff, shouldStart, connection.url, fmt, connection.headers)
#                 time.sleep(200)




                # Sending client headers to videostream
                if connection.url:
#                     #self.url = self.url.replace('127.0.0.1', '192.168.0.214')
#                     logger.debug('redirect to: %s' % connection.url)
#                     self.send_response(302)
#                     self.send_header("Location", connection.url)
#                     self.end_headers()
#                     time.sleep(200)


#                    self.video = urllib2.Request(self.url)
#                    for key in self.headers.dict:
#                        self.video.add_header(key, self.headers.dict[key])
#                    logger.debug("%s: %s" % (key, self.headers.dict[key]))

#                    self.video = urllib2.urlopen(self.video)
                    request = urllib2.Request(connection.url, headers=connection.headers)
                    connection.video = urllib2.urlopen(request, timeout=120)

                    connection.send_response(connection.video.getcode())

                    FORWARD_HEADERS = ['Content-Range',
                                       'Connection',
                                       'Keep-Alive',
                                       'Content-Type',
                                       'Accept-Ranges',
                                       'X-Content-Duration',
                                       'Content-Length',
                                       ]
                    SKIP_HEADERS = ['Server', 'Date']

                    for k in connection.video.info().headers:
                        if k.split(':')[0] not in (FORWARD_HEADERS + SKIP_HEADERS):
                            logger.debug('NEW HEADERS: %s' % k.split(':')[0])
                    for h in FORWARD_HEADERS:
                        if connection.video.info().getheader(h):
                            connection.send_header(h, connection.video.info().getheader(h))
                            logger.debug('key=%s value=%s' % (h, connection.video.info().getheader(h)))
                    
                    connection.send_header('Set-Cookie', 'uid=%s' % uid)
                    connection.end_headers()
                    logger.debug("Headers sent")

                    # Run proxyReadWrite
                    connection.proxyReadWrite()
                else:
                    connection.send_response(206)
                    connection.send_header('Content-Range', 'bytes 5016536819-5016606675/5016606676')
                    connection.send_header('Connection', 'Keep-Alive')
                    connection.send_header('Keep-Alive', 'timeout=15, max=100')
                    connection.send_header('Content-Type', 'video/x-matroska')
                    connection.send_header('Accept-Ranges', 'bytes')
                    connection.send_header('X-Content-Duration', '7882.00834298')
                    connection.send_header('Content-Length', '69857')
                    connection.end_headers()


        except (aceclient.AceException, vlcclient.VlcException, urllib2.URLError) as e:
            logger.error("Exception: " + repr(e))
            connection.errorhappened = True
            connection.dieWithError()
        except gevent.GreenletExit:
            # hangDetector told us about client disconnection
            logger.debug('greenletExit')
            pass
        except Exception:
            # Unknown exception
            logger.error(traceback.format_exc())
            connection.errorhappened = True
            connection.dieWithError()
        finally:
            pass
            if connection.errorhappened and self.AceStuff.clientcounter.count_pt(cid) == 0:
                # If no error happened and we are the only client
                try:
                    logger.debug("Sleeping for " + str(VIDEO_DESTROY_DELAY) + " seconds")
                    gevent.sleep(VIDEO_DESTROY_DELAY)
                except:
                    pass

            try:
                logger.debug("%s: client=%s" % (cid, connection.client))
                remaining = self.AceStuff.clientcounter.delete_pt(cid, connection.client)
                if connection.client:
                    connection.client.destroy()
                connection.ace = None
                connection.client = None
                if self.AceConfig.vlcuse and remaining == 0:
                    try:
                        self.AceStuff.vlcclient.stopBroadcast(connection.vlcid)
                    except:
                        pass
                logger.debug("END REQUEST")
            except:
                logger.error(traceback.format_exc())

    def getCid(self, reqtype, url):
        cid = ''

        if reqtype == 'torrent':
            if url.startswith('http'):
                if url.endswith('.acelive') or  url.endswith('.acestream'):
                    try:
                        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
                        f = base64.b64encode(urllib2.urlopen(req, timeout=5).read())
                        req = urllib2.Request('http://api.torrentstream.net/upload/raw', f)
                        req.add_header('Content-Type', 'application/octet-stream')
                        cid = json.loads(urllib2.urlopen(req, timeout=3).read())['content_id']
                    except:
                        pass

                    if cid == '':
                        logging.debug("Failed to get CID from WEB API")
                        try:
                            with self.AceStuff.clientcounter.lock:
                                if not self.AceStuff.clientcounter.idleace:
                                    self.AceStuff.clientcounter.idleace = self.AceStuff.clientcountself.AceStuffeAce()
                                cid = self.AceStuff.clientcounter.idleace.GETCID(reqtype, url)
                        except:
                            logging.debug("Failed to get CID from engine")

        return None if not cid or cid == '' else cid



