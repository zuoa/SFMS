#coding:utf-8
import os
from datetime import date
from tornado import web, ioloop, httpserver
from tornado.escape import json_encode, json_decode
import torndb
from config import  *


class BaseHandler(web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        self.db = torndb.Connection(DB_IP, DB_NAME, DB_USER, DB_PASSWD)
        super(BaseHandler, self).__init__(application, request, **kwargs)

    def __del__(self):
        self.db.close()

    def getMembers(self):
        return self.db.query('SELECT * FROM members')


class CreateHandler(BaseHandler):
    def get(self):
        self.render('create.html')

    def post(self):
        name = self.get_argument('name')
        desc = self.get_argument('desc')

        r = {}
        id =self.db.execute_lastrowid('INSERT INTO `features` (`name`, `desc`, `status`) VALUES(%s, %s, 0)', name, desc)
        for d in ('Android Phone', 'iPhone', 'Android Pad', 'iPad'):
            self.db.execute('INSERT INTO tasks (feature_id, progress, device, owner, priority) VALUES(%s, %s, %s, %s, %s)', id, 0, d, u'俞健', u'高')

        r['id'] = id
        self.write(json_encode(r))



class FeatureHandler(BaseHandler):
    def get(self, id):
        f = self.db.query("SELECT * from features where id=%s", id)[0]
        t = self.db.query("SELECT * from tasks where feature_id=%s", id)
        self.render('feature.html', feature_name=f.get("name"), feature_desc="", tasks=t)

    def post(self, id):
        tasks = json_decode(self.get_argument('tasks'))

        for t in tasks:
            exist = self.db.query('SELECT * FROM tasks WHERE feature_id=%s AND device=%s', id, t.get("device"))
            if  exist:
                self.db.execute('UPDATE tasks SET progress=%s, owner=%s, priority=%s  WHERE feature_id=%s AND device=%s', t.get("progress", 0), t.get("owner"), t.get("priority"), id, t.get("device"))
            else:
                self.db.execute('INSERT INTO tasks (feature_id, progress, device, owner, priority) VALUES(%s, %s, %s, %s, %s)', id, t.get("progress", 0), t.get("device"), t.get("owner"), t.get("priority"))


class EditHandler(BaseHandler):
    def get(self, id):
        f = self.db.query("SELECT * from features where id=%s", id)[0]
        tasks = self.db.query("SELECT * from tasks where feature_id=%s", id)
        members = self.db.query("SELECT * from members")
        priority = (u"高", u"中", u"低")


        for t in tasks:
            owner_option = ''
            for m in members:
                if t.get("owner") == m.get("name"):
                    owner_option += "<option selected>" + m.get("name") + "</option>"
                else:
                    owner_option += "<option>" + m.get("name") + "</option>"
            t['owner_option'] = owner_option

            priority_option = ''
            for p in priority:
                if t.get("priority") == p:
                    priority_option += "<option selected>" + p + "</option>"
                else:
                    priority_option += "<option>" +p + "</option>"
            t['priority_option'] = priority_option
        self.render('edit.html', feature_id=id, feature_name=f.get("name"), feature_desc=f.get("desc"), tasks=tasks)

    def post(self, id):
        tasks = json_decode(self.get_argument('tasks'))

        for t in tasks:
            exist = self.db.query('SELECT * FROM tasks WHERE feature_id=%s AND device=%s', id, t.get("device"))
            if  exist:
                self.db.execute('UPDATE tasks SET progress=%s, owner=%s, priority=%s  WHERE feature_id=%s AND device=%s', t.get("progress", 0), t.get("owner"), t.get("priority"), id, t.get("device"))
            else:
                self.db.execute('INSERT INTO tasks (feature_id, progress, device, owner, priority) VALUES(%s, %s, %s, %s, %s)', id, t.get("progress", 0), t.get("device"), t.get("owner"), t.get("priority"))




class Application(web.Application):
    def __init__(self):
        settings = dict(
            template_path = os.path.join(os.path.dirname(__file__), "template"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies = False,
            cookie_secret = "8B12CB2EEF49B4431EE27D1654060710",
            login_url = "/login",
            debug=True,
            autoescape = None
        )

        handlers = [
            (r"/f/create", CreateHandler),
            (r"/f/([0-9]+)", FeatureHandler),
            (r"/f/([0-9]+)/edit", EditHandler)
        ]

        web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    http_server = httpserver.HTTPServer(Application())
    http_server.listen(51216)
    print 'start server on', 51216
    ioloop.IOLoop.instance().start()
