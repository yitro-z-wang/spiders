import scrapy
import sys
import urllib.parse
from html2text import HTML2Text
from ..items import FictionChapter
import unicodedata
import re

class Extractor:
  def get_title(self, r: scrapy.http.Response):
    raise NotImplementedError()

  def get_first_page_href(self, r: scrapy.http.Response):
    raise NotImplementedError()

  def get_next_page_href(self, r: scrapy.http.Response):
    raise NotImplementedError()

  def get_chapter_title(self, r: scrapy.http.Response):
    raise NotImplementedError()

  def get_chapter_text(self, r: scrapy.http.Response):
    raise NotImplementedError()

class UukanshuExtractor(Extractor):
  def __init__(self):
    self.text_maker = HTML2Text()
    self.text_maker.single_line_break = True
    self.text_maker.body_width = 0

  def get_title(self, r: scrapy.http.Response):
    title = r.css('.bookImg img').xpath('@alt').get()
    return title

  def get_first_page_href(self, r: scrapy.http.Response):
    return r.xpath(u'//a[contains(text(), "第1章")]/@href').get()

  def get_next_page_href(self, r: scrapy.http.Response):
    raise NotImplementedError()

  def get_chapter_title(self, r: scrapy.http.Response):
    return r.css('#timu').xpath('text()').get()

  def get_chapter_text(self, r: scrapy.http.Response):
    text = self.text_maker.handle(r.css('.uu_cont').get())
    text = unicodedata.normalize('NFKC', text)
    text = text.strip()
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'\s*uu看书\s*www\.uukanshu\.com\s*', '', text, flags=re.IGNORECASE)
    return text


extractors = {
  'www.uukanshu.com': UukanshuExtractor
}


class FictionSpider(scrapy.Spider):
  name = "fiction"

  def __init__(self, *args, **kwargs):
    super(FictionSpider, self).__init__(*args, **kwargs)
    self.title = None
    self.start_url = kwargs.get('start_url')
    if not self.start_url:
      sys.stderr.write('usage: scrapy crawl fiction -a start_url=')
      exit(-1)
    self.extractor = extractors[urllib.parse.urlparse(self.start_url).netloc]()

  def start_requests(self):
    yield scrapy.Request(url=self.start_url, callback=self.parse_homepage)

  def parse_homepage(self, response: scrapy.http.Response):
    self.title = self.extractor.get_title(response)
    first_page_href = self.extractor.get_first_page_href(response)
    yield response.follow(first_page_href, callback=self.parse_chapter)

  def parse_chapter(self, response: scrapy.http.Response):
    title = self.extractor.get_chapter_title(response)
    text = self.extractor.get_chapter_text(response)
    yield FictionChapter(title=title, text=text)
    # next_a = response.css('#next')
    # if next_a.xpath('text()').get() == '下一章':
    #   yield response.follow(next_a.attrib['href'], callback=self.parse_chapter)
