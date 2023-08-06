import logging, sys  # logging, apparently

# HTML
import urllib.request
from html.parser import HTMLParser

# Email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# Secrets
from secrets import get_gmail_account, get_gmail_pw

# Global configs
logging_level=logging.INFO
logging.basicConfig(stream=sys.stderr, level=logging_level)
URL_ROOT = 'https://kanpou.npb.go.jp'


def read_url(url):
  with urllib.request.urlopen(url) as webUrl:
    if webUrl.getcode() == 200:
      # read the data from the URL and print it
      data = webUrl.read()
      return data.decode('utf8')


class TodaysNewsContentsParser(HTMLParser):
  entry_type=None
  titles=[]
  hrefs=[]


  def handle_starttag(self, tag, attrs):
    self.entry_type = None
    logging.debug("Start tag: %s", tag)
    for attr in attrs:
      # News title is in class="text"
      if attr[0] == 'class' and attr[1] == 'text':
        self.entry_type = 'CLASS_TEXT'
      if attr[0] == 'href':
        self.hrefs.append(attr[1])
      logging.debug("     attr: %s", attr)


  def handle_endtag(self, tag):
    self.entry_type = None
    logging.debug("End tag  : %s", tag)


  def handle_data(self, data):
    # hrefs will be added prior to its corresponding title
    # Data could be ignored when hrefs' size is not larger (no new link added)
    if self.entry_type == 'CLASS_TEXT' and len(self.hrefs) > len(self.titles):
      self.titles.append(data)
    logging.debug("Data     : %s", data)


def extract_enclosed(s: str, before: str, after: str):
  """Return the first instance enclosed by `before` and `after` """
  begin = s.find(before) + len(before)
  end = s.find(after, begin)
  return s[begin:end]


def get_today_news_link():
  web_str = read_url(URL_ROOT + '/index.html')
  web_str = extract_enclosed(web_str, '<div id="todayBox" class="todayBox">', '</div>')
  logging.debug('Today\'s index.html')
  logging.debug(web_str)

  # first list item for today's news link
  return extract_enclosed(web_str, '<li><a href=".', '">本紙')


def get_today_news_contents(url: str):
  web_str = read_url(url)
  
  title = extract_enclosed(web_str, '<p class="date">', '</p>')
  title = title.strip(' \r\n')
  first_section = extract_enclosed(web_str, '<section>', '</section>')
  logging.debug(first_section)
  parser = TodaysNewsContentsParser()
  if '政令' in first_section:
    parser.feed(first_section)

  return (title, parser.titles, parser.hrefs)


def format_email_text_content(title, subtitles, links):
  content = f'{title}\n\n'
  for (subtitle, link) in zip(subtitles, links):
    content += f'{subtitle}\n'
    content += f'{URL_ROOT}{link}\n'
  return content


today_news_link = get_today_news_link()
logging.debug('Today\'s news link: %s', today_news_link)

title, subtitles, links = get_today_news_contents(URL_ROOT + today_news_link)
logging.debug('Today\'s title: %s', title)
logging.debug('Today\'s subtitles: %s', subtitles)
logging.debug('Links: %s', links)
text_content = format_email_text_content(title, subtitles, links)
logging.info(text_content)

email = get_gmail_account()
pw = get_gmail_pw()
content = MIMEMultipart()
content['subject'] = f'{title}'
content['from'] = email
content['to'] = email
content.attach(MIMEText(text_content))

with smtplib.SMTP(host='smtp.gmail.com', port='587') as smtp:
  try:
    smtp.starttls()
    smtp.login(email, pw)  # login with application code
    smtp.send_message(content)
    print('Complete!')
  except Exception as e:
    print('Error message: ', e)

