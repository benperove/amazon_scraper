from __future__ import absolute_import
from bs4 import BeautifulSoup
from mechanize import Browser
import StringIO, cStringIO
from PIL import Image
import requests, cookielib
import sys, os, re, json, uuid


class Dbc(object):
    def __init__(self, url, html=None):
        self._url = url
        self.cap  = None
        self.br   = None
        if html is not None:
            self._html = html
        else:
            self._html = None
        self.user_agent             = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'
        self.referer                = 'https://amazon.com'
        self.html_parser            = 'html.parser'
        self._captcha_regexp        = re.compile(r'(?P<captcha>Robot\sCheck)', flags=re.I)
        self._captcha_result_regexp = re.compile(r'CAPTCHA\s[0-9]+\ssolved:\s(?P<cap>\w+)(\n|\r)[0-9]+\sSEND\s\{.*?\}(\r|\n)[0-9]+\sRECV\s(?P<json>\{.*?\})(\r|\n)[0-9]+\sCLOSE')


    def browser(self):
	'''setup mechanize browser instance'''
        if not self.br:
            br = Browser()
            cj = cookielib.LWPCookieJar()
            br.set_cookiejar(cj)
            #set user agents to maintain aws happiness
            br.addheaders = [('User-agent', self.user_agent), ('Referer', self.referer)]
            br.set_handle_equiv(True)
            br.set_handle_redirect(True)
            br.set_handle_referer(True)
            br.set_handle_robots(False)
            #br.set_handle_gzip(True) #experimental & probably unnecessary
            #proxy support
            #br.set_proxies({"http": "user:password@myproxy.example.com:3128"})
            #br.set_proxies({"http": "myproxy.example.com:3128"})
            #br.add_proxy_password("user", "password")
            self.br = br
        return self.br


    def process(self):
	'''detect captcha/solve via dbc service'''
        if self._url is None:
            print 'URL parameter missing'
            return False
        else:
            self.check()
            if self.captcha_result is True:
	        self.solvecaptcha()
                if self.cap is None:
                    print 'Failed to solve captcha'
                    return False
                self.submitcaptcha()
                if self._html is not False:
		    print 'Got it'
                    return self._html
	        else:
	            print 'Not this time'
                    return False
            else:
		print 'Evaded detection?'
		print 'self.cap: ' + self.cap
		return False
        print 'ended up here somehow - now what?'
        return False


    def check(self):
        '''looks for markup which indicates the presence of a captcha'''
        '''the html param is a response from requests.get'''
        '''this is strictly passthrough'''
        if self._html is not None and self._url is not None:
            soup = BeautifulSoup(self._html.text, self.html_parser)
            c    = self._captcha_regexp.search(self._html.text)
            if hasattr(soup.find('title', {'dir': 'ltr'}), 'text'):
                robot_check = soup.find('title', {'dir': 'ltr'}).text
                if robot_check == 'Robot Check':
                    print 'Captcha detected: ' + self._url
                    self.captcha_result = True
                    return self._html
            elif c:
                if c.group('captcha') is not None:
                    print 'Captcha detected: ' + self._url
                    self.captcha_result = True
                    return self._html
            else:
                print 'No captcha'
                return self._html
        else:
            print 'Missing either requests.response or URL' 
            return False


    def solvecaptcha(self):
        '''hook into captcha solving service here'''
        '''refreshes page to get a new form/captcha & maintain consitency between soup/mechanize'''  
        #reloading the page
        self.br.open(self._url)
        r = self.br.response()
        #identify captcha form by action - unreliable
        #br.select_form(predicate=select_form)
        self.br.select_form(nr=0)
        #instantiate soup from mechanize response
        html = r.read()
        soup = BeautifulSoup(html, self.html_parser)
        #get captcha img src url & download
        img  = soup.findAll('img')[0].attrs
        iurl = img['src']
        r    = requests.get(iurl)
        i    = Image.open(StringIO.StringIO(r.content))
        fn   = 'captcha' + str(uuid.uuid4()) + '.jpg'
        i.save(fn)
        #capture stdout from dbc
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO.StringIO()
        #call dbc
        sys.stdout = deathbycaptcha.main([fn])
        sys.stdout = old_stdout
        output     = mystdout.getvalue()
        #parse response from stdout, try to get results from two different places
        c          = self._captcha_result_regexp.search(output)
        cap1       = c.group('cap')
        cap2       = c.group('json') #used to be valid json response, but something changed recently
        if cap2:
            data = json.JSONDecoder().decode(cap2)
            cap2 = data['json']
        else:
            cap = None
        if cap1 is not None:
            self.cap = cap1
            return self.cap
        elif cap2 is not None:
            self.cap = cap2
            return self.cap
        else:
            self.cap = None
            return self.cap


    def submitcaptcha(self):
	'''submit captcha form & verify results''' 
        if self.cap is not None:
            print 'Trying: ' + self.cap
            self.br.form['field-keywords'] = self.cap #set the form field with the captcha answer
            response                       = self.br.submit() #sumbit the form
            html                           = response.read() #read the html response
            c                              = _captcha_regexp.search(html) #try regex match again
            soup                           = BeautifulSoup(html, self.html_parser)
            if hasattr(soup.find('title', {'dir': 'ltr'}), 'text'):
                robot_check = soup.find('title', {'dir': 'ltr'}).text
                if robot_check == 'Robot Check':
                    print 'Not solved'
                    return False
            elif c.group('captcha') is not None:
                print 'Not solved'
                return False
            else:
                print 'Solved'
                os.remove(fn)
                self._html.text = unicode(html)
                return self._html
        else:
            return False
