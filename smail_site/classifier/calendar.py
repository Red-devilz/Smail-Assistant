from bs4 import BeautifulSoup
from .main import get_html_message
from datetime import datetime


def check_exam_schedule(mail):
    return '14A' in mail.subject and 'Courses DR' in mail.sender


def get_exam_events(mail):
    html = BeautifulSoup(get_html_message(mail.message), 'html.parser')
    table = html.find('table', class_='MsoNormalTable')
    trs = table.find_all('tr')
    trs = trs[1:]
    data = []
    for tr in trs:
        tds = tr.find_all('td')
        datestr = tds[1].text.replace('\n', '')
        date = datetime.strptime(datestr, '%d.%m.%Y')
        start = date.replace(hour=9, minute=0).isoformat() + '+05:30'
        end = date.replace(hour=12, minute=0).isoformat() + '+05:30'
        entry = {
            "name": tds[0].text.replace('\n', ''),
            "start": start,
            "end": end
        }
        data.append(entry)
    return data
