import re
import datetime

import scrapy
from scraper.items import ProgramItem, DancefloorEventItem, DancefloorEventDetailsItem, \
    RoomItem, SlotItem

from notifhain.event.models import Program, DancefloorEvent

import logging
logger = logging.getLogger('scrapy')


class BerghainProgramSpider(scrapy.Spider):
    name = "berghain-program"
    allowed_domains = ["berghain.de"]
    base_url = "http://berghain.de"
    start_urls = [
        "http://berghain.de/events/",
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.ProgramPipeline': 400
        }
    }

    def parse(self, response):
        for month_element in response.css(".navi_level3_events ul li"):
            program_item = ProgramItem()
            program_item["name"] = month_element.css("::text").extract_first()
            month_url = month_element.css("::attr(href)").extract_first()
            program_item["url"] = response.urljoin(month_url)
            yield program_item


class BerghainEventSpider(scrapy.Spider):
    name = "berghain-events"
    allowed_domains = ["berghain.de"]
    base_url = "http://berghain.de/event"
    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.EventPipeline': 400
        }
    }

    def start_requests(self):
        for program in Program.objects.uncompleted():
            logger.info("crawl program events" + program.name)
            yield scrapy.Request(program.url, meta={"program": program}, callback=self.parse)

    def parse(self, response):
        program = response.meta["program"]
        for event in response.css(".col_teaser_type_dancefloor"):
            item = DancefloorEventItem()
            item["name"] = event.css("h4 a span::text").extract_first()
            item["date_string"] = event.css("h4 a::text").extract_first().strip()
            url = event.css("h4 a::attr(href)").extract_first()
            item["url"] = response.urljoin(url)
            item["program"] = program
            yield item


class BerghainEventDetailSpider(scrapy.Spider):
    name = "berghain-event-details"
    allowed_domains = ["berghain.de"]
    base_url = "http://berghain.de/event"
    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.EventDetailsPipeline': 400
        }
    }

    def __init__(self, send_email=False, publish_to_rr=False, **kwargs):
        super().__init__(**kwargs)
        self.send_email = send_email
        self.publish_to_rr = publish_to_rr

    def start_requests(self):
        for event in DancefloorEvent.objects.new():
            logger.info(event.url)
            yield scrapy.Request(event.url, meta={"event": event}, callback=self.parse)

    def split_artist_name(self, name):
        return re.split(" x |, | b2b | & ", name)

    def parse(self, response):
        item = DancefloorEventDetailsItem()
        event = response.meta["event"]
        item["event"] = event
        timetable_exists = response.css(".running_order_time").extract_first()
        if event.is_completed is not None and not timetable_exists:
            logger.info("no update")
            # if not the first run
            # if timetable still doesn't exist
            return
        item["is_completed"] = timetable_exists and True or False
        item["has_timetable"] = timetable_exists and True or False
        date = response.css("h2::text").extract_first()
        name = response.css("h2 span:nth-child(1)::text").extract_first()
        time = response.css("h2 span:nth-child(2)::text").extract_first()
        item["name"] = "%s%s%s" % (date, name, time)
        item["date_string"] = date
        time_string = time
        item["time_string"] = time_string.replace("/ Start ", "")
        item["description"] = "".join(response.css(".content .col_content:nth-child(3) p::text").extract())
        item["url"] = response.url
        item["rooms"] = []
        for i, running_order in enumerate(response.css(".content .col_context h4.type_dancefloor_color::text").extract()):
            room_item = RoomItem()
            room_item["name"] = running_order
            room_item["slots"] = []
            slot_items = response.css(".content .col_context ul.running_order")[i].css("li")
            last = len(slot_items) - 1
            for j, slot in enumerate(slot_items):
                slot_item = SlotItem()
                slot_name = " ".join([s.strip() for s in slot.css(".running_order_name *::text").extract()])
                if slot_name:
                    artist_name = slot.css(".running_order_name::text").extract_first()
                    slot_item["artists"] = self.split_artist_name(artist_name.strip())
                    slot_item["name"] = slot_name.strip()
                time = slot.css(".running_order_time::text").extract_first()
                if time:
                    slot_item["time"] = time.strip()
                    if j == last:
                        slot_item["is_closing"] = True
                is_live_set = slot.css(".running_order_name b").extract_first()
                if is_live_set:
                    slot_item["is_live_set"] = True
                slot_item["order"] = j
                room_item["slots"].append(slot_item)
            item["rooms"].append(room_item)
        yield item


class BerghainEventUpdateSpider(BerghainEventDetailSpider):
    name = "berghain-event-update"

    def start_requests(self):
        for event in DancefloorEvent.objects.uncompleted().till_sunday():
            logger.info(event.url)
            yield scrapy.Request(event.url, meta={"event": event}, callback=self.parse)
