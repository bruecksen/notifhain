import time
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
            if not settings.DEBUG:
                display = Display(visible=0, size=(800, 600))
                display.start()
            driver = webdriver.Chrome()
            driver.get('https://restrealitaet.de/r/login')
            print("login")
            username = driver.find_element_by_name('username')
            password = driver.find_element_by_name('password')
            username.send_keys(settings.RR_USERNAME)
            password.send_keys(settings.RR_PASSWORD)
            login = driver.find_element_by_css_selector(".loginform button")
            login.click()
            driver.implicitly_wait(1)
            driver.find_element_by_link_text('Bar').click()
            driver.implicitly_wait(1)
            driver.find_element_by_css_selector('button.new-btn').click()
            driver.implicitly_wait(1)
            title_element = driver.find_element_by_name('title')
            text_element = driver.find_element_by_name('text')
            title_element.send_keys(self.get_title(klubnacht))
            text = render_to_string('klubnacht-tt-rr.html', {'event': klubnacht})
            text_element.send_keys(text.strip())
            driver.implicitly_wait(3)
            driver.quit()
        print("stop-post-to-rr")
