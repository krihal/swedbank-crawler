#!/usr/bin/python
#-*- coding: utf-8 -*-

import re
import os
import mechanize
import cookielib
import datetime
import codecs
import time
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

        self.__set_options__()
        self.__crawl__()
        self.__parse__()

    def __set_options__(self):
        self.br.set_cookiejar(self.cj)
        self.br.set_handle_equiv(True)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)
        self.br.follow_meta_refresh = True
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    def __crawl__(self):
        try:
            self.br.open(self.url)
            self.br.select_form(nr=0)
            self.br.submit()
            self.br.select_form(nr=0)
            self.br.submit()
            self.br.select_form(nr=1)
            self.br["auth:kundnummer"] = self.username
            self.br["auth:metod_2"] = ["PIN6"]
            self.br.submit()
            self.br.select_form(nr=1)
            self.br["form:pinkod"] = self.password
            self.br.submit()
            self.br.select_form(nr=0)
            self.br.submit()
            req = self.br.click_link(text_regex=re.compile("Inneh"))
            self.br.open(req)
            req = self.br.click_link(text_regex=re.compile("versikt"))
            self.br.open(req)
            req = self.br.click_link(text_regex=re.compile("apitalspar"))
            self.br.open(req)
        except Exception, e:
            print e

        self.response = self.br.response().read()

    def __print_fund_name__(self, str):
        if re.search(".+>Andelar</span>.+", str):
            return

        print "\n%s:" % str.strip()

        return "\n%s:" % str.strip()

    def __print_fund_value__(self, str):
        fund = re.findall("\"[a-z_]+\"", str)
        value = re.findall(">[0-9 ]+,[0-9]+<", str)

        if fund == [] or value == []:
            return
        
        fund = fund[0].replace("\"", "")
        value = value[0].replace(">", "").replace("<", "").replace(" ", "")

        fund = fund.replace("altplac_andel", "Andel")
        fund = fund.replace("altplac_kurs", "Kurs")
        fund = fund.replace("altplac_anskverde", "Anskaffningsvärde")
        fund = fund.replace("altplac_verde", "Värde")
        fund = fund.replace("altplac_forendrkr", "Förändring")
        fund = fund.replace("altplac_forendrproc", "Förändringsprocent")

        fund = fund.replace("aktiefond_andel", "Andel")
        fund = fund.replace("aktiefond_kurs", "Kurs")
        fund = fund.replace("aktiefond_anskverde", "Anskaffningsvärde")
        fund = fund.replace("aktiefond_verde", "Värde")
        fund = fund.replace("aktiefond_forendrproc", "Förändringsprocent")
        fund = fund.replace("aktiefond_forendrkr", "Förändring")

        fund = fund.replace("rentefond_andel", "Andel")
        fund = fund.replace("rentefond_kurs", "Kurs")
        fund = fund.replace("rentefond_anskverde", "Anskaffningsvärde")
        fund = fund.replace("rentefond_verde", "Värde")
        fund = fund.replace("rentefond_forendrproc", "Förändringsprocent")
        fund = fund.replace("rentefond_forendrkr", "Förändring")
    
        print "  %s: %s" % (fund, value)

        return "  %s: %s" % (fund, value)

    def __parse__(self):
        lines = self.response.split("\n")
        linecnt = 0
        for line in lines:
            linecnt += 1
            match = re.search("td headers.+>.+([A-Za-z]|[0-9])+<", line)
            if match:
                self.__print_fund_value__(line)
                continue

            match = re.search("headers=\"rentefond_fond|aktiefond_fond|altplac_fond\">(\w+|\s+|\w)+", line)
            if match:            
                self.__print_fund_name__(lines[linecnt])
                continue
        
if __name__ == '__main__':
    s = SwedbankCrawler("USERNAME", "PINCODE")
