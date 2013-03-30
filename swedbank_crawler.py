#!/usr/bin/python
#-*- coding: utf-8 -*-

import re
import os
import sys
import time
import codecs
import getopt
import datetime
import mechanize
import cookielib

from pyquery import PyQuery
from sqlite3 import dbapi2 as sqlite3

class SwedbankCrawler(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.url = 'https://internetbank.swedbank.se/bviPrivat/privat?ns=1'
        self.filename = ""
        self.response = ""
        self.cj = cookielib.LWPCookieJar()
        self.br = mechanize.Browser()
        self.date = datetime.datetime.now().strftime('%m-%d')

    def crawl(self):
        try:
            br = self.br
            br.open(self.url)
            br.select_form(nr=0)
            br.submit()
            br.select_form(nr=0)
            br.submit()
            br.select_form(nr=1)
            br['auth:kundnummer'] = self.username
            br['auth:metod_2'] = ['PIN6']
            br.submit()
            br.select_form(nr=1)
            br['form:pinkod'] = self.password
            br.submit()
            br.select_form(nr=0)
            br.submit()
            for caption in ['Inneh', 'versikt', 'apitalspar']:
                req = br.click_link(text_regex = re.compile(caption))
                br.open(req)
        except Exception, e:
            print e

        self.response = br.response().read()

    def init_db(self):
        db = self.__get_db()

        try:
            with open('schema.sql') as fd:
                db.cursor().executescript(fd.read())
                db.commit()
        except Exception, e:
            print "Failed to open DB: %s" % e
            sys.exit(-2)
            
    def show_entries(self):
        db = self.__get_db()
        cur = db.execute('select * from swedbank')
        entries = cur.fetchall()
        return entries

    def __get_db(self):
        try:
            sqlite_db = sqlite3.connect('swedbank.db')
            sqlite_db.row_factory = sqlite3.Row
        except Exception, e:
            print "Failed to connect to DB (is the database initialized?): %s" % e
            sys.exit(-2)
        return sqlite_db

    def __fund_name(self, str):
        if re.search('.+>Andelar</span>.+', str):
            return
        self.lastfund = str.strip()

    def __print_fund_value(self, str):
        fund = re.findall('\"[\w_]+\"', str)
        value = re.findall('>[\d\s\-]+,\d+<', str)

        if not fund or not value:
            return
        
        fund = fund[0].translate(None, '\"')
        value = value[0].translate(None, '<> ')

        if re.match('\w+_verde$', fund):
            db = self.__get_db()
            cur = db.execute('insert into swedbank (value, name) values(?, ?)', 
                             (value.replace(',', '.'), self.lastfund))
            db.commit()

    def parse(self):
        linecnt = 0
        lines = self.response.split('\n')
        for line in lines:
            linecnt += 1

            match = re.search('td headers.+>.+[\w\d]+<', line)
            if match:
                self.__print_fund_value(line)
                continue

            match = re.search('headers=\"rentefond_fond|aktiefond_fond|altplac_fond\">(\w+|\s+|\w)+', line)
            if match:            
                self.__fund_name(lines[linecnt])
                continue
            
def usage():
    print 'swedbank_crawler.py -u <username> -p <password>'
    sys.exit(2)

def main(argv):
    if len(argv) == 0:
        usage()

    username = None
    password = None
    init_db = 0

    try:
        opts, args = getopt.getopt(argv, 'ihu:p:', ['init=', 'username=', 'password=', 'help'])
    except getopt.GetoptError:
        usage()        

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ('-u', '--user'):
            username = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-i', '--init'):
            init_db = 1
        else:
            usage()

    if None in (username, password):
        usage()

    try:
        swedbank = SwedbankCrawler(username, password)

        if init_db:
            swedbank.init_db()

        swedbank.crawl()
        swedbank.parse()
        print swedbank.show_entries()
    except Exception, e:
        print 'Failed with error: %s' % e

if __name__ == '__main__':
    main(sys.argv[1:])
