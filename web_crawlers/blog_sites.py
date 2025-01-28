""" Implements scrape function for specific blog sites """

from web_crawlers import FireCrawl

class Eater(FireCrawl):
    homepage = "https://eater.com"
    query = "site:eater.com location:new york city"
    def scrape(self, urls):
        self.extract_info(urls, self.query)

class MichelinGuide(FireCrawl):
    homepage = "https://guide.michelin.com"  
    query = "site:guide.michelin.com location:new york city"

    def scrape(self, urls):
        self.extract_info(urls, self.query)

class TheInfatuation(FireCrawl):
    homepage = "https://theinfatuation.com"
    query = "site:theinfatuation.com location:new york city"

    def scrape(self, urls):
        self.extract_info(urls, self.query)