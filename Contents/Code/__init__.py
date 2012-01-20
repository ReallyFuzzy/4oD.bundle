# -*- coding: utf-8 -*-
import re
from string import ascii_uppercase

TITLE = '4oD'
ART = 'art-default.jpg'
ICON = 'icon-default.png'
ICON_SEARCH = 'icon-search.png'

BASE_URL               = 'http://www.channel4.com'
PROGRAMMES_CATEGORIES  = '%s/programmes/tags/4od' % BASE_URL
PROGRAMMES_FEATURED    = '%s/programmes/4od' % BASE_URL
PROGRAMMES_BY_DATE     = '%s/programmes/4od/episode-list/date/%%s' % BASE_URL
PROGRAMMES_BY_CATEGORY = '%s/programmes/tags/%%s/4od/title/page-%%%%d' % BASE_URL
PROGRAMMES_BY_LETTER   = '%s/programmes/atoz/%%s/4od/page-%%%%d' % BASE_URL
PROGRAMMES_SEARCH      = '%s/programmes/long-form-search/?q=%%s' % BASE_URL

###################################################################################################
def Start():
  Plugin.AddPrefixHandler('/video/4od', MainMenu, TITLE, ICON, ART)
  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

  MediaContainer.title1 = TITLE
  MediaContainer.viewGroup = 'List'
  MediaContainer.art = R(ART)

  DirectoryItem.thumb = R(ICON)
  VideoItem.thumb = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:9.0.1) Gecko/20100101 Firefox/9.0.1'

###################################################################################################
def MainMenu():
  dir = MediaContainer()

  dir.Append(Function(DirectoryItem(BrowseDate, title='Browse by Date')))
  dir.Append(Function(DirectoryItem(BrowseCategory, title='Browse by Category')))
  dir.Append(Function(DirectoryItem(BrowseAZ, title='Browse Alphabetically')))
  dir.Append(Function(DirectoryItem(FeaturedCategory, title='Featured')))
  dir.Append(Function(InputDirectoryItem(Search, title='Search', prompt='Search for Programmes', thumb=R(ICON_SEARCH))))
  dir.Append(PrefsItem('Preferences', thumb=R('icon-prefs.png')))

  return dir

####################################################################################################
def BrowseDate(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  for i in range(30):
    date = Datetime.Now() - Datetime.Delta(days = i)
    date_key = date.strftime('%Y/%m/%d')
    date_label = date.strftime('%A %d %B')

    dir.Append(Function(DirectoryItem(Schedule, title=date_label), date=date_key))

  return dir

####################################################################################################
def Schedule(sender, date):
  dir = MediaContainer(title2=sender.itemTitle)

  programmes = HTML.ElementFromURL(PROGRAMMES_BY_DATE % date, cacheTime=1800).xpath('//li')
  for p in programmes:
    title = p.xpath('.//a/span/text()')[0].strip()
    time = p.xpath('.//span[@class="txTime"]')[0].text.strip()
    channel = p.xpath('.//span[@class="txChannel"]')[0].text.strip()
    url = p.xpath('.//a')[0].get('href').replace('4od#', '4od/player/')
    thumb = p.xpath('.//a/img')[0].get('src').replace('106x60.jpg', '625x352.jpg')

    dir.Append(VideoItem(Route(PlayVideo, url=url), title=title, infolabel=time + ' / ' + channel, thumb=Function(GetThumb, url=thumb)))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def BrowseCategory(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  categories = HTML.ElementFromURL(PROGRAMMES_CATEGORIES, cacheTime=CACHE_1DAY).xpath('//div[contains(@class,"category-nav")]//li/a')
  for c in categories:
    title = c.text
    tag = c.get('href').split('/')[3]

    dir.Append(Function(DirectoryItem(Programmes, title=title), tag=tag))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def BrowseAZ(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  # A to Z
  for char in list(ascii_uppercase):
    dir.Append(Function(DirectoryItem(Programmes, title=char), char=char))

  # 0-9
  dir.Append(Function(DirectoryItem(Programmes, title='0-9'), char='0-9'))

  return dir

####################################################################################################
def Programmes(sender, tag=None, char=None):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)

  if tag != None:
    content_url = PROGRAMMES_BY_CATEGORY % tag
  elif char != None:
    content_url = PROGRAMMES_BY_LETTER % char.lower()

  programmes = GetProgrammes(content_url)
  for p in programmes:
    dir.Append(Function(DirectoryItem(Series, title=p['title'], summary=p['summary'], thumb=Function(GetThumb, url=p['thumb'])), url=p['url'], thumb=p['thumb']))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def GetProgrammes(url, page=1):
  result = []

  try:
    programmes = HTML.ElementFromURL(url % (page), cacheTime=CACHE_1DAY).xpath('//div[contains(@class,"programmes")]//li')
    for p in programmes:
      prog = {}
      prog['title'] = p.xpath('./h3/a/span')[0].text.strip()
      prog['summary'] = p.xpath('./p[@class="synopsis"]/text()[1]')[0].strip()
      prog['url'] = p.xpath('./h3/a')[0].get('href') + '/4od'
      prog['thumb'] = p.xpath('./h3/a/img')[0].get('src').replace('145x82.jpg', '625x352.jpg')
      result.append(prog)

    # More pages?
    next_page = HTML.ElementFromURL(url % (page), cacheTime=CACHE_1DAY).xpath('//*[contains(@class,"nextUrl") and not(contains(@class,"endofresults"))]')
    if len(next_page) > 0:
      result.extend( GetProgrammes(url, page=page+1) )
  except:
    pass

  return result

####################################################################################################
def Series(sender, url, thumb):
  dir = MediaContainer(title2=sender.itemTitle)

  if url.find(BASE_URL) == -1:
    url = BASE_URL + url

  series = HTML.ElementFromURL(url, cacheTime=CACHE_1DAY).xpath('//div[contains(@class,"seriesLink")]//li/a')
  for s in series:
    title = s.text.strip()
    if (len(title) <= 2 and len(title) > 0):
      title = 'Series ' + title
    id = s.get('href').strip('#')

    dir.Append(Function(DirectoryItem(Episodes, title=title, thumb=Function(GetThumb, url=thumb)), url=url, id=id))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def Episodes(sender, url, id):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)

  episodes = HTML.ElementFromURL(url).xpath('//li[@id="' + id + '"]/ol/li')
  for e in episodes:
    title = e.get('data-episodetitle')  
    subtitle = e.get('data-episodeinfo');

    # Swap title and subtitle as for most series, at this point title is the series name rather than ep name.
    if (len(title) > 0 and len(subtitle) > 0):
      swap = title
      title = subtitle
      subtitle = swap

    summary = re.sub('<[^<]+?>', '', e.get('data-episodesynopsis'))

    try:
      broadcast = e.get('data-txdate')
      if broadcast != "":
        summary += '\n\nFirst broadcast: ' + broadcast
    except:
      pass

    thumb = e.get('data-image-url');
    episode_url = url + '/player/' + e.get('data-assetid')

    dir.Append(VideoItem(Route(PlayVideo, url=episode_url), title=title, subtitle=subtitle, summary=summary, thumb=Function(GetThumb, url=thumb)))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def FeaturedCategory(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  i = 0
  categories = HTML.ElementFromURL(PROGRAMMES_FEATURED).xpath('//li[@class="fourOnDemandCollection"]')
  for c in categories:
    title = c.xpath('./h2')[0].text.strip()
    i = i + 1

    dir.Append(Function(DirectoryItem(Featured, title=title), i=i))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def Featured(sender, i):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)

  programmes = HTML.ElementFromURL(PROGRAMMES_FEATURED).xpath('//li[@class="fourOnDemandCollection"][' + str(i) + ']//li')
  for p in programmes:
    url = p.xpath('./h3/a')[0].get('href')

    # Skip this item if the url doesn't contain '/4od'
    if url.find('/4od') != -1:
      title = p.xpath('./h3/a/span')[0].text.strip()
      summary = p.xpath('./p')[0].text.strip()
      thumb = p.xpath('./h3/a')[0].get('class')
      thumb = re.search('(\/[^"]+)', thumb).group(1) # Regex: start with a forward slash and catch everything except a double quote sign

      dir.Append(Function(DirectoryItem(Series, title=title, summary=summary, thumb=Function(GetThumb, url=thumb)), url=url, thumb=thumb))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')
  else:
    return dir

####################################################################################################
def Search(sender, query):
  dir = MediaContainer(title2=sender.itemTitle)

  result = JSON.ObjectFromURL(PROGRAMMES_SEARCH % ( String.Quote(query, usePlus=True) ))
  if len(result) > 0:
    for r in result['results']:
      title = r['value'].strip()
      url = r['siteUrl']
      thumb = None

      # Strip out /4oD from URL to get programme landing page with big logo.
      if (url.find('/4od')) > 0:
        thumb_url = url[0:-4]
        try:
          thumb = HTML.ElementFromURL(BASE_URL + thumb_url).xpath('//img[@id="heroImage"]')[0].get('src')
        except:
          thumb = None

      dir.Append(Function(DirectoryItem(Series, title=title, thumb=Function(GetThumb, url=thumb)), url=url, thumb=thumb))

  if len(dir) == 0:
    return MessageContainer('No results', 'Your search didn\'t return any results.')
  else:
    return dir

####################################################################################################
@route('/video/4od/v/p')
def PlayVideo(url):
  if url.find(BASE_URL) == -1:
    url = BASE_URL + url

  return Redirect(WebVideoItem(url))

####################################################################################################
def GetThumb(url):
  if url.find(BASE_URL) == -1:
    url = BASE_URL + url

  try:
    data = HTTP.Request(url, cacheTime=CACHE_1MONTH)
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))

####################################################################################################
def CalculateTime(timecode):
  milliseconds = 0
  d = re.search('([0-9]+) mins', timecode)
  milliseconds += int( d.group(1) ) * 60 * 1000
  return milliseconds
