import json
import requests
from bs4 import BeautifulSoup
from time import sleep
from pathlib import Path
import shutil
import os
import re
from datetime import datetime
from tqdm import tqdm
from sys import exit
import sys

limit = 0


def get_data_file_path(filename):
    if getattr(sys, 'frozen', False):
        # Если приложение запущено из собранного файла
        base_path = sys._MEIPASS  # Путь к временной директории
    else:
        # Если приложение запущено из исходного кода
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, filename)


def make_user(link):
    """
    Создание папки с пользователем. Название папки - домен пользователя из меременной link.
    Внутрь сразу кладётся файл index с основной информацией.
    """
    try:
        if os.path.exists(link):  # Удаляем папку, если она была.
            shutil.rmtree(link)
        os.makedirs(link)
        # Читаем содержимое page.html
        with open(get_data_file_path('page.html'), 'r', encoding='utf-8') as read_file:
            content = read_file.read()
            with open(f'{link}/index.html', 'w', encoding='utf-8') as write_file:
                write_file.write(content)
    except Exception as e:
        input(e)
        exit()


months = {  # c ведущим нулем для адекватной сортировки
    '01': 'января',
    '02': 'февраля',
    '03': 'марта',
    '04': 'апреля',
    '05': 'мая',
    '06': 'июня',
    '07': 'июля',
    '08': 'августа',
    '09': 'сентября',
    '10': 'октября',
    '11': 'ноября',
    '12': 'декабря'
}

months_i = {  # i - именительный
    '01': 'январь',
    '02': 'февраль',
    '03': 'март',
    '04': 'апрель',
    '05': 'май',
    '06': 'июнь',
    '07': 'июль',
    '08': 'август',
    '09': 'сентябрь',
    '10': 'октябрь',
    '11': 'ноябрь',
    '12': 'декабрь'
}


def save_post(link, y, m, d, time, title, text, tags, url=''):
    """
    Добавление поста в страницу.
    Сначала проверяем есть ли файл с месяцем. Если нет-копируем template и переименовываем, согласно шаблону год-месяц.
    Чтобы добавить запись в шалон, заменяем скрытый div на div с постом, а потом обратно добавляем скрытый в низ. Так,
    при соедующем запуске, следующий пост снова добавится вниз.
    :param link:  домен пользователя
    :param y: год
    :param m: месяц
    :param d: день
    :param time: время поста
    :param title: заголовок
    :param text: текст в html
    :param tags: тэги
    :param url: ссылка на оригинальный пост
    :return:
    """
    m = m.zfill(2)
    page_path = Path(f"{link}/{y}-{m}.html")
    if not page_path.is_file():
        shutil.copyfile(get_data_file_path('page.html'), f'{link}/{y}-{m}.html')
    with open(f'{link}/{y}-{m}.html', 'r', encoding="utf-8") as page_pre:
        temp = page_pre.read()
    new_text = f"<div class='post'><div class='title'>{d} {months[m]} {y} {time} {title}</div><div class='text'>{text}</div><div class='tags'>{tags}</div><p>{url}</p></div>"
    temp = temp.replace("<div class='hidden'></div>", f"{new_text}<div class='hidden'></div>")
    with open(f'{link}/{y}-{m}.html', 'w', encoding="utf-8") as page_post:
        page_post.write(temp)
    sleep(1)


def main():
    '''
    Сохранение дневника работает следующим образом:
    - создается папка с шаблонами
    - скрипт идет в календарь дневника и ищет список годов, в которых были посты (y)
        - для каждого года идем в страницу в годом и ищем список дней, в которые были посты (m)
            - для каждого дня ищем посты и кладем пост в страицу с именем год-месяц.хтмл
    - проход по всем файлам и замена шаблона левого меню на настоящее меню, а так же название бложика
    :return:
    '''
    # Проверка файла с куками.
    if not os.path.isfile('diary.ru.json'):
        input(
            'Файла diary.ru.json, с куками нет. Создайте его по инструкции https://github.com/Uk141800/diary.ru_saver')
        exit()
    # Заносим файл в переменную
    with open('diary.ru.json') as f:
        try:
            cookies_file = json.load(f)
            cookies = {}
            for k in cookies_file:
                cookies[k['name']] = k['value']
        except Exception as e:
            print(e)
            input(
                'Файл diary.ru.json некорретный. Пересоздайте его по инструкции https://github.com/Uk141800/diary.ru_saver')
            exit()
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'}

    link = input(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tВставьте ссылку вроде такой: https://906.diary.ru/ или пустое поле для https://906.diary.ru/\n")
    link = 'https://906.diary.ru/' if len(link) == 0 else link

    # убираем протокол, если он есть. Должна остаться ссылка формата домен.diary.ru
    # todo сделать регуляркой
    if link.startswith('https://'):
        link = link[8:]
    if link.startswith('http://'):
        link = link[7:]
    if link.endswith('.diary.ru/'):
        link = link[0:len(link) - 10]
    if link.endswith('.diary.ru'):
        link = link[0:len(link) - 9]

    # Проверка файла с куками
    response = requests.get(f'http://{link}.diary.ru/?calendar', cookies=cookies, headers=headers)
    if 'Пожалуйста заполните поля для авторизации:' in response.text:
        input(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tЧто-то не так с файлом diary.ru.json. Пересоздайте его по инструкции https://github.com/Uk141800/diary.ru_saver")
        exit()
    elif response.status_code != 200:
        input(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tНекорректный адрес дневника.")
        exit()
    else:
        match = re.search(r'<title>(.*?)</title>', response.text)
        diary_title = match.group(1)[12:]  # Получаем название дневеника
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\t{diary_title}")

    make_user(link)

    try:
        response = requests.get(f'http://{link}.diary.ru/?calendar', cookies=cookies, headers=headers)
    except Exception as e:
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tЧто-то пошло не так. Возможно проблемы с сетью. Попробуйте позже.\nТекст ошибки:\n")
        input(e)
        exit()
    page = BeautifulSoup(response.text, 'lxml')

    years = page.find("div", {"id": "content"})
    years = years.find_all('a')
    year_links = []
    for i in years:
        if '?calendar&year=20' in i['href']:
            year_links.append(i['href'])

    print(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tПолучен список годов, когда были посты. Всего таких годов: {len(year_links)}")
    print(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tТеперь я загружу все дни, когда были посты и начнем веселье.")
    days_link = []
    for current_year in tqdm(year_links, colour="green", bar_format='{l_bar}{bar:40}{r_bar}{bar:-10b}'):
        while True:
            sleep(3)  # ограничиаем запросы, чтобы не получать ошибку 429 too many request
            try:
                response = requests.get(current_year, cookies=cookies, headers=headers)
            except Exception as e:
                print(e)
                sleep(4)
                continue
            page = BeautifulSoup(response.text, 'lxml')
            active_days = page.find("div", {"id": "content"})
            active_days = active_days.find_all('a')

            for i in active_days:
                if '?date=' in i['href']:
                    days_link.append(i['href'])
            break
    print(
        f"\r{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tДни загружены.\nВсего дней с постами - {len(days_link)}")

    counter = 0
    for day_link in tqdm(days_link, colour="green", bar_format='{l_bar}{bar:40}{r_bar}{bar:-10b}'):
        sleep(2)
        if counter > limit and limit > 0:
            break
        counter += 1

        y, m, d = day_link[day_link.find('date=') + 5:].split('-')
        while True:
            try:
                response = requests.get(day_link + '&sort=created_at', cookies=cookies, headers=headers)
                if str(response.status_code).startswith('2'):
                    break
                else:
                    print(f"\r{response.status_code}", end='')
                    continue
            except:
                sleep(5)
                continue
        page = BeautifulSoup(response.text, 'lxml')
        current_day_posts = page.findAll(True, {"class": ["singlePost countFirst", "singlePost countSecond"]})
        for post in current_day_posts:
            url_link = post.find("a", string="URL")
            url_link = str(url_link).replace('URL', 'URL')

            header = post.find('div', {"class": ["postTitle", "postTitle header"]})
            try:
                creation_time = header.findAll('span')[1].text
            except:
                creation_time = header.findAll('span')[0].text

            if header.find('h2') is not None:
                try:
                    title = header.findAll('h2')[1].text.strip()
                except:
                    title = header.findAll('h2')[0].text.strip()
            else:
                title = ''

            post_block = post.find('div', {'class': 'paragraph'})
            post_text_html = post_block.contents

            post_text = ""
            for i in post_text_html:
                post_text += str(i)

            # это на самом деле не нужно. Пост в html и пробелы игнорируются. Но просто некрасиво, а хочется красиво
            post_text = post_text.replace(
                '                                                                                ', '')
            post_text = post_text.replace('                                    ', '')
            post_text = post_text.replace('                                ', '')
            post_text = post_text.replace('\n', '')
            post_text = post_text.replace('<em>', '')
            post_text = post_text.replace('</em>', '')
            post_text = post_text.replace('<a href="/', f'<a href="http://{link}.diary.ru/')

            # убираем р с тегами
            attag = re.search(r'<p class="tags atTag">.*?</p>', post_text, flags=re.DOTALL)
            if attag:
                attag = attag.group(0)  # тег р с содержимым
                post_text = post_text.replace(attag, '')
                tags = re.findall(r'<a [^>]*>(.*?)</a>', attag)
                tags = '@темы: ' + ', '.join(tags)
            else:
                tags = ''

            # some text fix
            if post_text.endswith('<br/>'):
                post_text = post_text[:-5]
            if post_text.endswith('<br>'):
                post_text = post_text[:-4]
            if post_text.endswith('<br/'):
                post_text = post_text[:-4]
            # print(f"|{post_text}|")
            save_post(link, y, m, d, creation_time, title, post_text, tags, url_link)
        if counter > limit and limit > 0:
            break

    menu_html = "<div class='year'><a href='index.html'>Главная</a><ul><li></li></ul></div>"

    menu = {}
    files = os.listdir(link)
    for file in files:
        if file.endswith('.html') and file.startswith('20'):
            if file[:4] not in menu.keys():
                menu[file[:4]] = []
            menu[file[:4]].append(file[5:file.find('.')])

    # создние html для меню
    for year, months in menu.items():
        menu_html += f"<div class='year'>{year}<ul>\n"
        for month in months:
            menu_html += f"<li><a href='{year}-{month}.html' target=_top>{months_i[month]}</a></li>\n"
        menu_html += "</ul></div>\n\n"
    # добавление меню в каждый хтмл файл
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tДобавляю меню")
    # todo Не забыть переделать на регулярку
    files = os.listdir(link)
    for file in files:
        if not file.endswith('html'):
            continue
        with open(f'{link}/{file}', 'r', encoding="utf-8") as page_pre:
            temp = page_pre.read()
        temp = temp.replace('<div id="menu"></div>', f'<div id="menu">{menu_html}</div>')
        temp = temp.replace("<div id='diary_name'></div>", f"<div id='diary_name'>{diary_title}</div>")
        with open(f'{link}/{file}', 'w', encoding="utf-8") as page_post:
            page_post.write(temp)

    # отдельно - создание index.html
    with open(f'{link}/index.html', 'r', encoding="utf-8") as page_pre:
        temp = page_pre.read()
    temp = temp.replace("<div class='hidden'>",
                        f'<h3>Diary.ru saver</h3><p>Версия сохранятора от 2024-08-20</p><p>Архив создан: {datetime.now()}</p>')
    with open(f'{link}/index.html', 'w', encoding="utf-8") as page_post:
        page_post.write(temp)
    input(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tГотово")


if __name__ == '__main__':
    main()
