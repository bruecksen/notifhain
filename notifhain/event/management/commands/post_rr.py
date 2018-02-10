from time import sleep
from django.core.management.base import BaseCommand
from django.template.defaultfilters import capfirst
from django.template.loader import render_to_string
from django.conf import settings

from notifhain.event.models import DancefloorEvent, Slot

from pyvirtualdisplay import Display
from selenium import webdriver


def berghainify(name):
    return name.replace("o", "[o]")


class Command(BaseCommand):

    display = None
    driver = None

    # Open headless chromedriver
    def start_driver(self):
        # if not settings.DEBUG:
        self.display = Display(visible=0, size=(800, 600))
        print("starting display...")
        self.display.start()
        print("starting driver...")
        self.driver = webdriver.Chrome()
        sleep(4)

    # Close chromedriver
    def close_driver(self):
        print('closing driver...')
        if self.display:
            self.display.stop()
        self.driver.quit()
        print('closed!')

    # Tell the browser to get a page
    def get_page(self, url):
        print('getting page...')
        self.driver.get(url)
        sleep(3)

    def get_title(self, klubnacht):
        appendix = ""
        closing_berghain = Slot.objects.filter(event_details__event=klubnacht, room__name="Running Order Berghain", name__contains="o").order_by("-order")
        if closing_berghain:
            closing_berghain = closing_berghain.first()
            if "o" in closing_berghain.name:
                appendix = " %s" % berghainify(closing_berghain.name)
        closing_pbar = Slot.objects.filter(event_details__event=klubnacht, room__name="Running Order Panorama Bar", name__contains="o").order_by("-order")
        if closing_pbar:
            closing_pbar = closing_pbar.first()
            if "o" in closing_pbar.name:
                appendix += "%s%s" % (appendix and ", ", berghainify(closing_pbar.name))
        return "%s %s%s" % (klubnacht.event_date.strftime("%d.%m"), capfirst(klubnacht.name.lower()), appendix)

    def handle(self, *args, **options):
        print("start-post-to-rr")
        klubnacht = DancefloorEvent.objects.get_next_klubnacht()
        if klubnacht and not klubnacht.is_posted_to_rr:
            print("%s %s" % (klubnacht.pk, klubnacht.name))
            self.start_driver()
            self.get_page('https://restrealitaet.de/r/login')
            username = self.driver.find_element_by_name('username')
            password = self.driver.find_element_by_name('password')
            username.send_keys(settings.RR_USERNAME)
            password.send_keys(settings.RR_PASSWORD)
            login = self.driver.find_element_by_css_selector(".loginform button")
            print("login...")
            login.click()
            self.driver.implicitly_wait(10)
            self.driver.find_element_by_link_text('Bar').click()
            self.driver.implicitly_wait(10)
            self.driver.find_element_by_css_selector('button.new-btn').click()
            self.driver.implicitly_wait(10)
            title_element = self.driver.find_element_by_name('title')
            text_element = self.driver.find_element_by_name('text')
            title_element.send_keys(self.get_title(klubnacht))
            text = render_to_string('klubnacht-tt-rr.html', {'event': klubnacht})
            text_element.send_keys(text.strip())
            sleep(3)
            self.close_driver()
