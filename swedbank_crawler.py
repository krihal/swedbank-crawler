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

class SwedbankCrawler(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.url = "https://internetbank.swedbank.se/bviPrivat/privat?ns=1"
        self.filename = ""
        self.response = ""
        self.cj = cookielib.LWPCookieJar()
        self.br = mechanize.Browser()
        self.date = datetime.datetime.now().strftime("%m-%d")

    def set_options(self):
        self.br.set_cookiejar(self.cj)
        self.br.set_handle_equiv(True)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)
        self.br.follow_meta_refresh = True
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    def crawl(self):
        try:
            br = self.br
            br.open(self.url)
            br.select_form(nr=0)
            br.submit()
            br.select_form(nr=0)
            br.submit()
            br.select_form(nr=1)
            br["auth:kundnummer"] = self.username
            br["auth:metod_2"] = ["PIN6"]
            br.submit()
            br.select_form(nr=1)
            br["form:pinkod"] = self.password
            br.submit()
            br.select_form(nr=0)
            br.submit()
            for caption in ["Inneh", "versikt", "apitalspar"]:
                req = br.click_link(text_regex = re.compile(caption))
                br.open(req)
        except Exception, e:
            print e

        self.response = br.response().read()

    def __fund_name__(self, str):
        if re.search(".+>Andelar</span>.+", str):
            return
        self.lastfund = str.strip()

    def __print_fund_value__(self, str):
        fund = re.findall("\"[\w_]+\"", str)
        value = re.findall(">[\d\s\-]+,\d+<", str)

        if fund == [] or value == []:
            return
        
        fund = fund[0].translate(None, "\"")
        value = value[0].translate(None, "<> ")

        if re.match('\w+_verde$', fund):
            self.__write_file__(self.lastfund, ("%s;%s;%s" % (self.date, self.lastfund, value.replace(",", "."))))

    def __write_file__(self, filename, str):
        with open("data/" + filename.replace(" ", "_"), "a") as fd:
            fd.write(str + "\n")
            print "Writing file: %s" % filename

    def parse(self):
        linecnt = 0
        lines = self.response.split("\n")
        for line in lines:
            linecnt += 1

            match = re.search("td headers.+>.+[\w\d]+<", line)
            if match:
                self.__print_fund_value__(line)
                continue

            match = re.search("headers=\"rentefond_fond|aktiefond_fond|altplac_fond\">(\w+|\s+|\w)+", line)
            if match:            
                self.__fund_name__(lines[linecnt])
                continue
            
def usage():
    print "swedbank_crawler.py -u <username> -p <password>"
    sys.exit(2)

def main(argv):
    if len(argv) == 0:
        usage()

    username = None
    password = None

    try:
        opts, args = getopt.getopt(argv, "hu:p:", ["username=", "password=", "help"])
    except getopt.GetoptError:
        usage()        

    for opt, arg in opts:
        if opt == "-h":
            usage()
        elif opt in ("-u", "--user"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        else:
            usage()

    if None in (username, password):
        usage()

    try:
        swedbank = SwedbankCrawler(username, password)
        swedbank.set_options()
        swedbank.crawl()
        swedbank.parse()
    except Exception, e:
        print "Failed with error: %s" % e

if __name__ == '__main__':
    main(sys.argv[1:])
