'''
Simple Client Counter for VLC VLM
'''
import threading
import logging
import time
import aceclient
import gevent
from aceconfig import AceConfig

class ClientCounter(object):

    def __init__(self):
        self.lock = threading.RLock()
        self.clients = dict()
        self.idleace = None
        self.total = 0
        gevent.spawn(self.checkIdle)

    def count(self, cid):
        with self.lock:
            clients = self.clients.get(cid)
            return len(clients) if clients else 0

    def getClients(self, cid):
        with self.lock:
            return self.clients.get(cid)

    def add(self, cid, client):
        with self.lock:
            clients = self.clients.get(cid)

            logging.error('%s: add' % cid)
            logging.error('%s: clients=%s' % (cid, clients))
            if clients:
                client.ace = clients[0].ace
                with client.ace._lock:
                    client.queue.extend(client.ace._streamReaderQueue)
                clients.append(client)
            else:
                logging.error('%s: self.idleace=%s' % (cid, self.idleace))
                if self.idleace:
                    client.ace = self.idleace
                    self.idleace = None
                else:
                    try:
                        client.ace = self.createAce()
                    except Exception as e:
                        logging.error('Failed to create AceClient: ' + repr(e))
                        raise e
                clients = [client]
                self.clients[cid] = clients

            self.total += 1
            logging.error('%s: end add %s' % (cid, len(clients)))
            logging.error('%s: end add %s' % (cid, client))
            # return len(clients)
            return client

    def delete(self, cid, client):
        with self.lock:
            if not self.clients.has_key(cid):
                return 0
            logging.error('%s: delete' % cid)
            clients = self.clients[cid]
            logging.error('%s: clients=%s' % (cid, clients))
            if client not in clients:
                return len(clients)

            try:
                if len(clients) > 1:
                    clients.remove(client)
                    return len(clients)
                else:
                    del self.clients[cid]
                    clients[0].ace.closeStreamReader()

                    logging.error('%s: self.idleace=%s' % (cid, self.idleace))
                    if self.idleace:
                        client.ace.destroy()
                    else:
                        try:
                            client.ace.STOP()
                            self.idleace = client.ace
                            self.idleace.reset()
                        except:
                            client.ace.destroy()

                    return 0
            finally:
                self.total -= 1

    def deleteAll(self, cid):
        clients = None

        try:
            with self.lock:
                if not self.clients.has_key(cid):
                    return

                clients = self.clients[cid]
                del self.clients[cid]
                self.total -= len(clients)
                clients[0].ace.closeStreamReader()

                if self.idleace:
                    clients[0].ace.destroy()
                else:
                    try:
                        clients[0].ace.STOP()
                        self.idleace = clients[0].ace
                        self.idleace.reset()
                    except:
                        clients[0].ace.destroy()
        finally:
            if clients:
                for c in clients:
                    c.destroy()

    def destroyIdle(self):
        with self.lock:
            try:
                if self.idleace:
                    self.idleace.destroy()
            finally:
                self.idleace = None

    def createAce(self):
        logger = logging.getLogger('createAce')
        ace = aceclient.AceClient(
                AceConfig.acehost, AceConfig.aceport, connect_timeout=AceConfig.aceconntimeout,
                result_timeout=AceConfig.aceresulttimeout)
        logger.debug("AceClient created")
        ace.aceInit(
                gender=AceConfig.acesex, age=AceConfig.aceage,
                product_key=AceConfig.acekey, pause_delay=AceConfig.videopausedelay,
                seekback=AceConfig.videoseekback)
        logger.debug("AceClient inited")
        return ace

    def checkIdle(self):
        while(True):
            gevent.sleep(60.0)
            with self.lock:
                ace = self.idleace
                if ace and (ace._idleSince + 60.0 <= time.time()):
                    self.idleace = None
                    ace.destroy()

