#!/usr/bin/python
#-*- coding: utf-8 -*-

import pygal

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, _app_ctx_stack
from numpy import arange, array, ones, linalg

DATABASE = 'swedbank.db'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('SWEDBANK', silent=True)

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as fd:
            db.cursor().executescript(fd.read())
            db.commit()

def get_db():
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'])
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db
    return top.sqlite_db

@app.teardown_appcontext
def close_db_connection(exception):
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

@app.route('/')
def show_entries():
    data = dict()
    db = get_db()
    cur = db.execute('select * from swedbank order by id')
    entries = cur.fetchall()

    for xid, time, value, name in entries:
        if not name in data.keys():
            data[name] = []
        data[name].append(value)
    for key in data.iterkeys():        
        x = arange(0, len(data[key]))
        A = array([x, ones(len(data[key]))])
        w = linalg.lstsq(A.T, data[key])[0]

        chart = pygal.Line()
        chart.title = key
        chart.x_labels = map(str, range(1, len(data[key])))
        chart.add('Regression', w[0] * x + w[1])
        chart.add(key, data[key])
        chart.render_to_file('static/%s.svg' % key)
    return render_template('show_entries.html', entries = data.iterkeys())

if __name__ == '__main__':
    app.run(host='0.0.0.0')
