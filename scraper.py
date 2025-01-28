import os
import logging as log

from web_crawlers import *

path = os.path.dirname(os.path.realpath(__file__))
log.basicConfig(filename=f'{path}/errors.log', level=log.ERROR, filemode='w', force = True)

def scraper(site: str, location: str, time=False):
    num_reviews, scraped_articles, nosnap = 0, 0, 0

    blog_sites = {"eater": Eater, "michelin": MichelinGuide, "infatuation": TheInfatuation}
    forum_sites = {}


    food_review_sites = {**blog_sites, **forum_sites}

    count = 0
    site = food_review_sites[site]()
    site_name = site.homepage

    query = f'site:{site_name} location:{location} ("best" OR "worst" OR "must-try")'
    if time:
        query = f'site:{site_name} location:{location} ("best" OR "worst" OR "must-try") after:2024-01-01' #Need some flexibility here or perform analysis on what every single site has. 

    collections = site.pull_collections(query)

    for collection in collections:
        num_articles += 1
        content_dup = []



if __name__ == "__main__":
    scraper('eater', 'new york')
