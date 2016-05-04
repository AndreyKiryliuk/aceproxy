import gevent
from gevent.event import AsyncResult
from gevent.event import Event
import telnetlib
import logging
import json
import time
import threading
import traceback
import Queue
from collections import deque
from acemessages import *
import aceconfig
from aceconfig import AceConfig

class AceException(Exception):

    '''
    Exception from AceClient
    '''
    pass


class AceClient(object):

    def __init__(self, host, port, connect_timeout=5, result_timeout=10):
        # Receive buffer
        self._recvbuffer = None
        # Stream URL
        self._url = None
        # Ace stream socket
        self._socket = None
        # Result timeout
        self._resulttimeout = result_timeout
        # Shutting down flag
        self._shuttingDown = Event()
        # Product key
        self._product_key = None
        # Current STATUS
        self._status = None
        # Current STATE
        self._state = None
        # Current video position
        self._position = None
        # Available video position (loaded data)
        self._position_last = None
        # Buffered video pieces
        self._position_buf = None
        # Current AUTH
        self._auth = None
        self._gender = None
        self._age = None
        # Result (Created with AsyncResult() on call)
        self._result = AsyncResult()
        self._authevent = Event()
        # Result for getURL()
        self._urlresult = AsyncResult()
        # Result for GETCID()
        self._cidresult = AsyncResult()
        # Event for resuming from PAUSE
        self._resumeevent = Event()
        # Seekback seconds.
        self._seekback = 0
        # Did we get START command again? For seekback.
        self._started_again = False

        self._idleSince = time.time()
        self._lock = threading.Condition(threading.Lock())
        self._streamReaderConnection = None
        self._streamReaderState = None
        self._streamReaderQueue = deque()
        self._engine_version_code = 0;

        # Logger
        logger = logging.getLogger('AceClieimport tracebacknt_init')

        try:
            self._socket = telnetlib.Telnet(host, port, connect_timeout)
            logger.info("Successfully connected with Ace!")
        except Exception as e:
            raise AceException(
                "Socket creation error! Ace is not running? " + repr(e))

        # Spawning recvData greenlet
        gevent.spawn(self._recvData)
        gevent.sleep()

    def __del__(self):
        # Destructor just calls destroy() method
        self.destroy()

    def destroy(self):
        '''
        AceClient Destructor
        '''
        if self._shuttingDown.isSet():
        # Already in the middle of destroying
            return

        # Logger
        logger = logging.getLogger("AceClient_destroy")
        # We should resume video to prevent read greenlet deadlock
        self._resumeevent.set()
        # And to prevent getUrl deadlock
        self._urlresult.set()

        # Trying to disconnect
        try:
            logger.debug("Destroying client...")
            self._shuttingDown.set()
            self._write(AceMessage.request.SHUTDOWN)
        except:
            # Ignore exceptions on destroy
            pass
        finally:
            self._shuttingDown.set()

    def reset(self):
        self._started_again = False
        self._idleSince = time.time()
        self._streamReaderState = None

    def _write(self, message):
        try:
            logger = logging.getLogger("AceClient_write")
            logger.debug(message)
            self._socket.write(message + "\r\n")
        except EOFError as e:
            raise AceException("Write error! " + repr(e))

    def aceInit(self, gender=AceConst.SEX_MALE, age=AceConst.AGE_18_24, product_key=None, pause_delay=0, seekback=0):
        self._product_key = product_key
        self._gender = gender
        self._age = age
        # PAUSE/RESUME delay
        self._pausedelay = pause_delay
        # Seekback seconds
        self._seekback = seekback

        # Logger
        logger = logging.getLogger("AceClient_aceInit")

        # Sending HELLO
        self._write(AceMessage.request.HELLO)
        if not self._authevent.wait(self._resulttimeout):
            errmsg = "Authentication timeout. Wrong key?"
            logger.error(errmsg)
            raise AceException(errmsg)
            return

        if not self._auth:
            errmsg = "Authentication error. Wrong key?"
            logger.error(errmsg)
            raise AceException(errmsg)
            return

        logger.debug("aceInit ended")

    def _getResult(self):
        # Logger
        try:
            result = self._result.get(timeout=self._resulttimeout)
            if not result:
                raise AceException("Result not received")
        except gevent.Timeout:
            raise AceException("Timeout")

        return result

    def START(self, datatype, value):
        '''
        Start video method
        '''
        stream_type = 'output_format=http' if self._engine_version_code >= 3010500 and not AceConfig.vlcuse else ''
        self._urlresult = AsyncResult()
        self._write(AceMessage.request.START(datatype.upper(), value, stream_type))
        self._getResult()

    def STOP(self):
        '''
        Stop video method
        '''
        if self._state is not None and self._state != '0':
            self._result = AsyncResult()
            self._write(AceMessage.request.STOP)
            self._getResult()

    def LOADASYNC(self, datatype, url):
        self._result = AsyncResult()
        self._write(AceMessage.request.LOADASYNC(datatype.upper(), 0, {'url': url}))
        return self._getResult()

    def GETCID(self, datatype, url):
        contentinfo = self.LOADASYNC(datatype, url)
        self._cidresult = AsyncResult()
        self._write(AceMessage.request.GETCID(contentinfo.get('checksum'), contentinfo.get('infohash'), 0, 0, 0))
        cid = self._cidresult.get(True, 5)
        return '' if not cid or cid == '' else cid[2:]

    def GETCONTENTINFO(self, datatype, url):
        contentinfo = self.LOADASYNC(datatype, url)
        return contentinfo

    def getUrl(self, timeout=40):
        # Logger
        logger = logging.getLogger("AceClient_getURL")

        try:
            res = self._urlresult.get(timeout=timeout)
            return res
        except gevent.Timeout:
            errmsg = "getURL timeout!"
            logger.error(errmsg)
            raise AceException(errmsg)

    def startStreamReader(self, url, cid, counter, req_headers={}):
        logger = logging.getLogger("StreamReader")
        self._streamReaderState = 1
        logger.debug("Opening video stream: %s" % url)
        logger.debug("req_headers: %s" % str(req_headers))

        try:
            request = urllib2.Request(url, headers=req_headers)
            connection = self._streamReaderConnection = urllib2.urlopen(request)

            logger.debug("Ace Responce Code: %s" % connection.getcode())
            logger.debug('resp headers: %s' % connection.info().headers)
            logger.debug('resp info: %s' % connection.info())


            if url.endswith('.m3u8'):
                logger.debug("Can't stream HLS in non VLC mode: %s" % url)
                return

            if connection.getcode() not in (200, 206):
                logger.error("Failed to open video stream %s" % connection)
                return

            clients = counter.getClients(cid)
            if clients:
                for c in clients:
                    if c.handler.connected:
                        c.handler.send_response(connection.getcode())

                        FORWARD_HEADERS = ['Content-Range',
                                           'Connection',
                                           'Keep-Alive',
                                           'Content-Type',
                                           'Accept-Ranges',
                                           'Content-Length',
                                           ]
                        SKIP_HEADERS = ['Server', 'Date']

                        for k in connection.info().headers:
                            if k.split(':')[0] not in (FORWARD_HEADERS + SKIP_HEADERS):
                                logger.debug('NEW HEADERS: %s' % k.split(':')[0])
                        for h in FORWARD_HEADERS:
                            if connection.info().getheader(h):
                                c.handler.send_header(h, connection.info().getheader(h))
                                logger.debug('key=%s value=%s' % (h, connection.info().getheader(h)))
#                         for k in connection.info().headers:
#                             logger.debug('key=%s value=%s' % (k.split(':')[0], connection.info().getheader(k.split(':')[0].lower())))
#                             c.handler.send_header(k.split(':')[0], connection.info().getheader(k.split(':')[0].lower()))
                        c.handler.end_headers()

            with self._lock:
                self._streamReaderState = 2
                self._lock.notifyAll()

            while True:
                data = None
                clients = counter.getClients(cid)

                try:
                    data = connection.read(AceConfig.readchunksize)
                except:
                    logger.debug("no get data")
                    break;

                if data and clients:
                    with self._lock:
                        if len(self._streamReaderQueue) == AceConfig.readcachesize:
                            self._streamReaderQueue.popleft()
                        self._streamReaderQueue.append(data)

                    for c in clients:
                        try:
                            c.addChunk(data, 5.0)
                        except Queue.Full:
                            if len(clients) > 1:
                                logger.debug("Disconnecting client: %s" % str(c))
                                c.destroy()
                elif not clients:
                    logger.debug("All clients disconnected - closing video stream")
                    break
                else:
                    logger.warning("No data received")
                    break
        except urllib2.URLError:
            logger.error("Failed to open video stream")
            logger.error(traceback.format_exc())
        except:
            logger.error(traceback.format_exc())
            if counter.getClients(cid):
                logger.error("Failed to read video stream")
        finally:
            self.closeStreamReader()
            with self._lock:
                self._streamReaderState = 3
                self._lock.notifyAll()
            counter.deleteAll(cid)

    def closeStreamReader(self):
        logger = logging.getLogger("StreamReader")
        c = self._streamReaderConnection

        if c:
            self._streamReaderConnection = None
            c.close()
            logger.debug("Video stream closed")

        self._streamReaderQueue.clear()

    def getPlayEvent(self, timeout=None):
        '''
        Blocking while in PAUSE, non-blocking while in RESUME
        '''
        return self._resumeevent.wait(timeout=timeout)

    def pause(self):
        self._write(AceMessage.request.PAUSE)

    def play(self):
        self._write(AceMessage.request.PLAY)

    def _recvData(self):
        '''
        Data receiver method for greenlet
        '''
        logger = logging.getLogger('AceClient_recvdata')

        while True:
            gevent.sleep()
            try:
                self._recvbuffer = self._socket.read_until("\r\n")
                self._recvbuffer = self._recvbuffer.strip()
                # logger.debug('<<< ' + self._recvbuffer)
            except:
                # If something happened during read, abandon reader.
                if not self._shuttingDown.isSet():
                    logger.error("Exception at socket read")
                    self._shuttingDown.set()
                return

            if self._recvbuffer:
                # Parsing everything only if the string is not empty
                if self._recvbuffer.startswith(AceMessage.response.HELLO):
                    # Parse HELLO
                    if 'version_code=' in self._recvbuffer:
                        v = self._recvbuffer.find('version_code=')
                        self._engine_version_code = int(self._recvbuffer[v + 13:v + 20])

                    if 'key=' in self._recvbuffer:
                        self._request_key_begin = self._recvbuffer.find('key=')
                        self._request_key = \
                            self._recvbuffer[self._request_key_begin + 4:self._request_key_begin + 14]
                        try:
                            self._write(AceMessage.request.READY_key(
                                self._request_key, self._product_key))
                        except urllib2.URLError as e:
                            logger.error("Can't connect to keygen server! " + \
                                repr(e))
                            self._auth = False
                            self._authevent.set()
                        self._request_key = None
                    else:
                        self._write(AceMessage.request.READY_nokey)

                elif self._recvbuffer.startswith(AceMessage.response.NOTREADY):
                    # NOTREADY
                    logger.error("Ace is not ready. Wrong auth?")
                    self._auth = False
                    self._authevent.set()

                elif self._recvbuffer.startswith(AceMessage.response.LOADRESP):
                    # LOADRESP
                    _contentinfo_raw = self._recvbuffer.split()[2:]
                    _contentinfo_raw = ' '.join(_contentinfo_raw)
                    _contentinfo = json.loads(_contentinfo_raw)
                    if _contentinfo.get('status') == 100:
                        logger.error("LOADASYNC returned error with message: %s"
                            % _contentinfo.get('message'))
                        self._result.set(False)
                    else:
                        logger.debug("Content info: %s", _contentinfo)
                        self._result.set(_contentinfo)

                elif self._recvbuffer.startswith(AceMessage.response.START):
                    # START
                    if not self._seekback or self._started_again or not self._recvbuffer.endswith(' stream=1'):
                        # If seekback is disabled, we use link in first START command.
                        # If seekback is enabled, we wait for first START command and
                        # ignore it, then do seeback in first EVENT position command
                        # AceStream sends us STOP and START again with new link.
                        # We use only second link then.
                        try:
                            self._url = self._recvbuffer.split()[1]
                            self._urlresult.set(self._url)
                            self._resumeevent.set()
                        except IndexError as e:
                            self._url = None
                    else:
                        logger.debug("START received. Waiting for %s." % AceMessage.response.LIVEPOS)

                elif self._recvbuffer.startswith(AceMessage.response.STOP):
                    pass

                elif self._recvbuffer.startswith(AceMessage.response.SHUTDOWN):
                    logger.debug("Got SHUTDOWN from engine")
                    self._socket.close()
                    return

                elif self._recvbuffer.startswith(AceMessage.response.AUTH):
                    try:
                        self._auth = self._recvbuffer.split()[1]
                        # Send USERDATA here
                        self._write(
                            AceMessage.request.USERDATA(self._gender, self._age))
                    except:
                        pass
                    self._authevent.set()

                elif self._recvbuffer.startswith(AceMessage.response.GETUSERDATA):
                    raise AceException("You should init me first!")

                elif self._recvbuffer.startswith(AceMessage.response.LIVEPOS):
                    self._position = self._recvbuffer.split()
                    self._position_last = self._position[2].split('=')[1]
                    self._position_buf = self._position[9].split('=')[1]
                    self._position = self._position[4].split('=')[1]

                    if self._seekback and not self._started_again:
                        self._write(AceMessage.request.SEEK(str(int(self._position_last) - \
                            self._seekback)))
                        logger.debug('Seeking back')
                        self._started_again = True

                elif self._recvbuffer.startswith(AceMessage.response.STATE):
                    self._state = self._recvbuffer.split()[1]

                elif self._recvbuffer.startswith(AceMessage.response.STATUS):
                    self._tempstatus = self._recvbuffer.split()[1].split(';')[0]
                    if self._tempstatus != self._status:
                        self._status = self._tempstatus
                        logger.debug("STATUS changed to " + self._status)

                    if self._status == 'main:err':
                        logger.error(
                            self._status + ' with message ' + self._recvbuffer.split(';')[2])
                        self._result.set_exception(
                            AceException(self._status + ' with message ' + self._recvbuffer.split(';')[2]))
                        self._urlresult.set_exception(
                            AceException(self._status + ' with message ' + self._recvbuffer.split(';')[2]))
                    elif self._status == 'main:starting':
                        self._result.set(True)
                    elif self._status == 'main:idle':
                        self._result.set(True)

                elif self._recvbuffer.startswith(AceMessage.response.PAUSE):
                    logger.debug("PAUSE event")
                    self._resumeevent.clear()

                elif self._recvbuffer.startswith(AceMessage.response.RESUME):
                    logger.debug("RESUME event")
                    gevent.sleep(self._pausedelay)
                    self._resumeevent.set()

                elif self._recvbuffer.startswith('##') or len(self._recvbuffer) == 0:
                    self._cidresult.set(self._recvbuffer)
                    logger.debug("CID: %s" % self._recvbuffer)
