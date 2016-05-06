
import os
import threading
from collections import deque
import logging
import time
# import aceconfig
from aceconfig import AceConfig
import psutil
from subprocess import PIPE
import Queue


class Client:

    def __init__(self, cid, handler, channelName, channelIcon):
        self.cid = cid
        self.handler = handler
        self.channelName = channelName
        self.channelIcon = channelIcon
        self.ace = None
        self.lock = threading.Condition(threading.Lock())
        self.queue = deque()

    def handle(self, shouldStart, url, fmt=None, req_headers=None):
        logger = logging.getLogger("ClientHandler")

        logger.debug('tut 461')

        if shouldStart:
            self.handler.send_response(302)
            self.handler.send_header("Location", url)
            self.handler.end_headers()
        # time.sleep(200)
#            logger.debug('tut 361')
#            self.ace._streamReaderState = 1
#            gevent.spawn(self.ace.startStreamReader, url, self.cid, AceStuff.clientcounter, req_headers)
#            gevent.sleep()
#        else:
#            logger.debug('tut 361')
#            self.ace._streamReaderState = 1
#            gevent.spawn(self.ace.startStreamReader, url, self.cid, AceStuff.clientcounter, req_headers)
#            gevent.sleep()

#        with self.ace._lock:
#            start = time.time()
#            while self.handler.connected and self.ace._streamReaderState == 1:
#                remaining = start + 115.0 - time.time()
#                if remaining > 0:
#                    self.ace._lock.wait(remaining)
#                else:
#                    logger.warning("Video stream not opened in 5 seconds - disconnecting")
#                   self.handler.dieWithError()
#                    return

#           if self.handler.connected and self.ace._streamReaderState != 2:
#               logger.warning("No video stream found")
#               self.handler.dieWithError()
#               return

#         if self.handler.connected:
#             self.handler.send_response(200)
#             self.handler.send_header("Connection", "Keep-Alive")
#             self.handler.send_header("Keep-Alive", "timeout=15, max=100")
#             self.handler.send_header("Content-Type", "video/x-matroska")
#             self.handler.send_header("Accept-Ranges", "bytes")
#             self.handler.send_header("Content-Length", "7602181228")
#             self.handler.end_headers()

        if AceConfig.transcode:
            if not fmt or not AceConfig.transcodecmd.has_key(fmt):
                fmt = 'default'
            if AceConfig.transcodecmd.has_key(fmt):
                # DEVNULL = open(os.devnull, 'wb')
                if AceConfig.loglevel == logging.DEBUG:
                    stderr = None
                else:
                    open(os.devnull, 'wb')

                transcoder = psutil.Popen(AceConfig.transcodecmd[fmt], bufsize=AceConfig.readchunksize,
                                      stdin=PIPE, stdout=self.handler.wfile, stderr=stderr)
                out = transcoder.stdin
            else:
                transcoder = None
                out = self.handler.wfile
        else:
            transcoder = None
            out = self.handler.wfile

        try:
            while self.handler.connected and self.ace._streamReaderState == 2:
                try:
                    data = self.getChunk(60.0)

                    if data and self.handler.connected:
                        try:
                            out.write(data)
                        except:
                            break
                    else:
                        break
                except Queue.Empty:
                    logger.debug("No data received in 60 seconds - disconnecting")
        finally:
            if transcoder:
                transcoder.kill()

    def addChunk(self, chunk, timeout):
        start = time.time()
        with self.lock:
            while(self.handler.connected and (len(self.queue) == AceConfig.readcachesize)):
                remaining = start + timeout + time.time()
                if remaining > 0:
                    self.lock.wait(remaining)
                else:
                    raise Queue.Full
            if self.handler.connected:
                self.queue.append(chunk)
                self.lock.notifyAll()

    def getChunk(self, timeout):
        start = time.time()
        with self.lock:
            while(self.handler.connected and (len(self.queue) == 0)):
                remaining = start + timeout - time.time()
                if remaining > 0:
                    self.lock.wait(remaining)
                else:
                    raise Queue.Empty
            if self.handler.connected:
                chunk = self.queue.popleft()
                self.lock.notifyAll()
                return chunk
            else:
                return None

    def destroy(self):
        with self.lock:
            self.handler.closeConnection()
            self.lock.notifyAll()
            self.queue.clear()

    def __eq__(self, other):
        return self is other
