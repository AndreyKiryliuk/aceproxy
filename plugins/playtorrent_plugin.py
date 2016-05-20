# -*- coding=utf-8 -*-

'''
This is the example of plugin.
Rename this file to helloworld_plugin.py to enable it.

To use it, go to http://127.0.0.1:8000/helloworld
'''

import traceback
import gevent
import gevent.monkey
from gevent.queue import Full
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
from datetime import datetime
import time

class Playtorrent(AceProxyPlugin):
    handlers = ('playtorrent', 'playpid')

    def __init__(self, AceConfig, AceStuff):
        self.params = None
        self.AceConfig = AceConfig
        self.AceStuff = AceStuff
        self.logger = logging.getLogger('playtorrent')

    def handle(self, connection, headers_only=False):
        self.connection = connection
        query = urlparse.urlparse(connection.path).query
        self.params = urlparse.parse_qs(query)

        # self.logger.debug('connection.reqtype=%s' % connection.reqtype)
        # self.logger.debug(len(connection.splittedpath))
        # self.logger.debug('connection.splittedpath=%s' % connection.splittedpath)

        if connection.reqtype == 'playtorrent':
            self.handlePlay(headers_only)


    def handlePlay(self, headers_only, channelName=None, channelIcon=None, fmt=None):
        logger = logging.getLogger('handlePlay')
        logger.debug("connection=%s" % (self.connection))
        self.connection.requrl = urlparse.urlparse(self.connection.path)
        self.connection.reqparams = urlparse.parse_qs(self.connection.requrl.query)
        self.connection.path = self.connection.requrl.path[:-1] if self.connection.requrl.path.endswith('/') else self.connection.requrl.path
        for key in self.connection.headers.dict:
            logger.debug("%s: %s" % (key, self.connection.headers.dict[key]))
        # Check if third parameter exists
        # …/pid/blablablablabla/video.mpg
        #                      |_________|
        # And if it ends with regular video extension
        try:
            if not self.connection.path.endswith(('.3gp', '.avi', '.flv', '.mkv', '.mov', '.mp4', '.mpeg', '.mpg', '.ogv', '.ts')):
                logger.error("Request seems like valid but no valid video extension was provided")
                self.connection.dieWithError(400)
                return
        except IndexError:
            logger.error("Index error")
            self.connection.dieWithError(400)  # 400 Bad Request
            return

        # Limit concurrent connections
        if 0 < self.AceConfig.maxconns <= self.AceStuff.clientcounter.total:
            logger.debug("Maximum connections reached, can't serve this")
            self.connection.dieWithError(503)  # 503 Service Unavailable
            return

        # Pretend to work fine with Fake UAs or HEAD request.
        useragent = self.connection.headers.get('User-Agent')
        fakeua = useragent and useragent in self.AceConfig.fakeuas
        if headers_only or fakeua:
            if fakeua:
                logger.debug("Got fake UA: " + self.connection.headers.get('User-Agent'))
            # Return 200 and exit
            self.connection.send_response(200)
            self.connection.send_header("Content-Type", "video/mpeg2")
            self.connection.end_headers()
            self.connection.closeConnection()
            return

        # Make list with parameters
        self.connection.params = list()
        for i in xrange(3, 8):
            try:
                self.connection.params.append(int(self.connection.splittedpath[i]))
            except (IndexError, ValueError):
                self.connection.params.append('0')

        self.connection.url = None
        self.connection.path_unquoted = urllib2.unquote(self.connection.splittedpath[2])
        contentid = self.connection.getCid(self.connection.reqtype, self.connection.path_unquoted)
        cid = contentid if contentid else self.connection.path_unquoted
        cid = str(datetime.now()) + ' ' + cid
        logger.debug("CID: " + cid)
        self.connection.client = Client(cid, self.connection, channelName, channelIcon)
        logger.debug("%s: client=%s" % (cid, self.connection.client))
        self.connection.vlcid = urllib2.quote(cid, '')
        logger.debug("%s: client=%s" % (cid, self.connection.client))
        self.connection.client = self.AceStuff.clientcounter.add(cid, self.connection.client)
        logger.debug("%s: client=%s" % (cid, self.connection.client))
        logger.debug("%s: connection=%s" % (cid, self.connection))
        shouldStart = True


        # Send fake headers if this User-Agent is in fakeheaderuas tuple
        if fakeua:
            logger.debug(
                "Sending fake headers for " + useragent)
            self.connection.send_response(200)
            self.connection.send_header("Content-Type", "video/mpeg3")
            self.connection.end_headers()
            # Do not send real headers at all
            self.connection.headerssent = True
        logger.debug("%s: client=%s" % (cid, self.connection.client))
        logger.debug("%s: connection=%s" % (cid, self.connection))
#         while not self.connection:
#             logger.debug("%s wait self.connection.ace" % cid)
#             time.sleep(1)
#
#         while not self.connection.client.ace:
#             logger.debug("%s wait self.connection.client.ace" % cid)
#             time.sleep(1)
        try:
            # Initializing AceClient
            if shouldStart:
                if contentid:
                    self.connection.client.ace.START('PID', {'content_id': contentid})
                elif self.connection.reqtype == 'playpid':
                    self.connection.client.ace.START(
                        self.connection.reqtype, {'content_id': self.connection.path_unquoted, 'file_indexes': self.connection.params[0]})
                elif self.connection.reqtype == 'playtorrent':
                    paramsdict = dict(
                        zip(aceclient.acemessages.AceConst.START_TORRENT, self.connection.params))
                    paramsdict['url'] = self.connection.path_unquoted
                    self.connection.client.ace.START('torrent', paramsdict)
                logger.debug("START done")
                logger.debug("%s: connection=%s" % (cid, self.connection))
                # Getting URL
                self.connection.url = self.connection.client.ace.getUrl(self.AceConfig.videotimeout)
                logger.debug("getting url done")
                logger.debug("%s: connection=%s" % (cid, self.connection))
                # Rewriting host for remote Ace Stream Engine
                self.connection.url = self.connection.client.ace.url = self.connection.url.replace('127.0.0.1', self.AceConfig.acehost)
                # self.url = self.url.replace('127.0.0.1', '192.168.0.214')
                logger.debug('redirect to: %s' % self.connection.url)
                self.connection.send_response(302)
                self.connection.send_header("Location", self.connection.url)
                self.connection.end_headers()
                time.sleep(200)
                return

            self.connection.errorhappened = False

            if shouldStart:
                logger.debug("Got url " + self.connection.url)
                # If using VLC, add this url to VLC
                if self.AceConfig.vlcuse:
                    # Force ffmpeg demuxing if set in config
                    if self.AceConfig.vlcforceffmpeg:
                        self.connection.vlcprefix = 'http/ffmpeg://'
                    else:
                        self.connection.vlcprefix = ''

                    self.connection.client.ace.pause()
                    # Sleeping videodelay
                    gevent.sleep(self.AceConfig.videodelay)
                    self.connection.client.ace.play()

                    self.AceStuff.vlcclient.startBroadcast(
                        self.connection.vlcid, self.connection.vlcprefix + self.connection.url, self.AceConfig.vlcmux, self.AceConfig.vlcpreaccess)
                    # Sleep a bit, because sometimes VLC doesn't open port in
                    # time
                    gevent.sleep(0.5)

            # self.hanggreenlet = gevent.spawn(self.hangDetector)
            # logger.debug("hangDetector spawned")
            # gevent.sleep()

            # Building new VLC url
            if self.AceConfig.vlcuse:
                self.connection.url = 'http://' + self.AceConfig.vlchost + \
                    ':' + str(self.AceConfig.vlcoutport) + '/' + self.connection.vlcid
                logger.debug("VLC url " + self.connection.url)

                # Sending client headers to videostream
                self.connection.video = urllib2.Request(self.connection.url)
                for key in self.connection.headers.dict:
                    self.connection.video.add_header(key, self.connection.headers.dict[key])

                self.connection.video = urllib2.urlopen(self.connection.video)

                # Sending videostream headers to client
                if not self.connection.headerssent:
                    self.connection.send_response(self.connection.video.getcode())
                    if self.connection.video.info().dict.has_key('connection'):
                        del self.connection.video.info().dict['connection']
                    if self.connection.video.info().dict.has_key('server'):
                        del self.connection.video.info().dict['server']
                    if self.connection.video.info().dict.has_key('transfer-encoding'):
                        del self.connection.video.info().dict['transfer-encoding']
                    if self.connection.video.info().dict.has_key('keep-alive'):
                        del self.connection.video.info().dict['keep-alive']

                    for key in self.connection.video.info().dict:
                        self.connection.send_header(key, self.connection.video.info().dict[key])
                    # End headers. Next goes video data
                    self.connection.end_headers()
                    logger.debug("Headers sent")

                # Run proxyReadWrite
                self.connection.proxyReadWrite()
            else:
                if not fmt:
                    fmt = self.connection.reqparams.get('fmt')[0] if self.connection.reqparams.has_key('fmt') else None
#                logger.debug('self.connection.headers=%s' % type(self.connection.headers))
#                logger.debug('self.connection.headers=%s' % str(self.connection.headers))
#                self.client.handle(shouldStart, self.url, fmt, self.headers)
#                logger.debug('tut 368')
                # Sending client headers to videostream
                if self.connection.url:
#                     self.url = self.url.replace('127.0.0.1', '192.168.0.214')
#                     logger.debug('redirect to: %s' % self.url)
#                     self.send_response(302)
#                     self.send_header("Location", self.url)
#                     self.end_headers()
#                     time.sleep(200)


#                    self.video = urllib2.Request(self.url)
#                    for key in self.headers.dict:
#                        self.video.add_header(key, self.headers.dict[key])
#                    logger.debug("%s: %s" % (key, self.headers.dict[key]))

#                    self.video = urllib2.urlopen(self.video)
                    request = urllib2.Request(self.connection.url, headers=self.connection.headers)
                    self.connection.video = urllib2.urlopen(request, timeout=120)

                    self.connection.send_response(self.connection.video.getcode())

                    FORWARD_HEADERS = ['Content-Range',
                                       'Connection',
                                       'Keep-Alive',
                                       'Content-Type',
                                       'Accept-Ranges',
                                       'X-Content-Duration',
                                       'Content-Length',
                                       ]
                    SKIP_HEADERS = ['Server', 'Date']

                    for k in self.connection.video.info().headers:
                        if k.split(':')[0] not in (FORWARD_HEADERS + SKIP_HEADERS):
                            logger.debug('NEW HEADERS: %s' % k.split(':')[0])
                    for h in FORWARD_HEADERS:
                        if self.connection.video.info().getheader(h):
                            self.connection.send_header(h, self.connection.video.info().getheader(h))
                            logger.debug('key=%s value=%s' % (h, self.connection.video.info().getheader(h)))

                    self.connection.end_headers()
                    logger.debug("Headers sent")

                    # Run proxyReadWrite
                    self.connection.proxyReadWrite()
                else:
                    self.connection.send_response(206)
                    self.connection.send_header('Content-Range', 'bytes 5016536819-5016606675/5016606676')
                    self.connection.send_header('Connection', 'Keep-Alive')
                    self.connection.send_header('Keep-Alive', 'timeout=15, max=100')
                    self.connection.send_header('Content-Type', 'video/x-matroska')
                    self.connection.send_header('Accept-Ranges', 'bytes')
                    self.connection.send_header('X-Content-Duration', '7882.00834298')
                    self.connection.send_header('Content-Length', '69857')
                    self.connection.end_headers()


        except (aceclient.AceException, vlcclient.VlcException, urllib2.URLError) as e:
            logger.error("Exception: " + repr(e))
            self.connection.errorhappened = True
            self.connection.dieWithError()
        except gevent.GreenletExit:
            # hangDetector told us about client disconnection
            logger.debug('greenletExit')
            pass
        except Exception:
            # Unknown exception
            logger.error(traceback.format_exc())
            self.connection.errorhappened = True
            self.connection.dieWithError()
        finally:
            pass
#             if self.AceConfig.videodestroydelay and not self.connection.errorhappened and self.AceStuff.clientcounter.count(cid) == 1:
#                 # If no error happened and we are the only client
#                 try:
#                     logger.debug("Sleeping for " + str(self.AceConfig.videodestroydelay) + " seconds")
#                     gevent.sleep(self.AceConfig.videodestroydelay)
#                 except:
#                     pass

            try:
                remaining = self.AceStuff.clientcounter.delete(cid, self.connection.client)
                self.connection.client.destroy()
                self.connection.ace = None
                self.connection.client = None
                if self.AceConfig.vlcuse and remaining == 0:
                    try:
                        self.AceStuff.vlcclient.stopBroadcast(self.connection.vlcid)
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



