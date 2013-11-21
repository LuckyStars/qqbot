import configs
from webqqclient import *
import gevent
from gevent.queue import Queue, Empty


class QQBot:
    def __init__(self):
        self.client = WebQQClient()
        self.queue = Queue()
        self.apps = []
        for app_name in configs.apps:
            # get class from apps dir
            module = __import__("apps.{0}".format(app_name.lower()))
            module = getattr(module, app_name.lower())
            module = getattr(module, app_name)
            self.apps.append(module)
        pass

    def run(self):
        self.client.login(configs.qq, configs.password)
        #self.client.get_group_info()
        thread1 = gevent.spawn(self._update_group_info)
        #thread1 = gevent.spawn(self._heartbeat)
        thread2 = gevent.spawn(self._poll_msg)
        #self._poll_msg()
        thread3 = gevent.spawn(self._chat)

        threads = [thread1, thread2, thread3]
        gevent.joinall(threads)


    def _update_group_info(self):
        while True:
            self.client.get_group_info()
            gevent.sleep(60)

    def _heartbeat(self):
        while True:
            self.client.keep_alive()
            gevent.sleep(60)

    def _poll_msg(self):
        while True:
            print 'start'
            ret = self.client.poll_msg()
            print 'end'
            for msg in ret:
                self.queue.put(msg)
                print msg
                if msg['type'] == 'group_message':
                    print msg['content']
                    #self.client.send_group_msg(msg['from_uin'], msg['content'])

    def _chat(self):
        while True:
            try:
                msg = self.queue.get(timeout = 1)
                if msg['type'] != 'group_message':
                    continue
                for app in self.apps:
                    pat = re.compile(app.pattern)
                    if pat.match(msg['content']):
                        gid = msg['from_uin']
                        content = app().execute(msg, self.client.groups[gid]['minfo'])
                        self.client.send_group_msg(gid, content)
                        break
            except Empty:
                pass


if __name__ == '__main__':
    bot = QQBot()
    bot.run()

