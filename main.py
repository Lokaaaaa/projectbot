import datetime
import os
import random
import sqlite3
import sys
import asyncio
import time
import discord
import undetected_chromedriver
from undetected_chromedriver import find_chrome_executable
from discord.ext import commands
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
from vk_api import vk_api
import threading
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
import translators as ts
from selenium import webdriver
import secrets
start = datetime.datetime.now()
TOKEN_DICT = {
    "discord": "OTUxNDc4MDI0NzExMzM1OTU3.YioC9g.K3egOQBIRhOHxbWdxH86xPqkVmc",
    "vk_api": "732433add52f1c905b0b71b16c3b30d0ce05100c6007556125a06310bdfd165f6465f8d8a498beb96fd82",
    "telegram.ext": "5168539127:AAEbrYlNWbQaLmTlDMnKg6orzvEE3X-e6MA"
}
PREFIX = '\\o '
PARAM_DICT = {}
USER_INF_DICT  = {}
sorry= ["Мы не нашли подобную команду в нашем списке", "Извините, но данная команда отсутствует в нашем списке",
        "У нас еще нет такого функционала", "Возможно вы ошиблись при наборе команды "
        "\n Пропишите '\\o help_bot' для получения списка команд"]
COMMAND_HELPER_DICT = {"help_bot": "Отображает список доступных команд на данный момент в боте",
                       "help": "Дает больше информации по определенной команде",
                       "get_data": "Позволяет получить материал урока [Команда доступна только после регистрации]",
                       "register": "Регистрация данными аккаунта yandex [Первым словом идет логин вторым пароль]",
                       "new_task": "Получить случайную задачу для решения; \n"
                                   "Параметры доступные для указания: \n--sorted_'ad'/'dc' (По возрастанию/по убыванию)\n"
                                   "--nfp/sw/ons (not full points)/(solved wrong)/(only not solved)\n",
                       "solve_captcha": "Отправить решение капчи для входа в аккаунт"
                       }


def run_vk_bot(vk):
    for event in vk.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(event.obj.message['from_id'])


def run_ds_bot(bot):
    PARAM_DICT["DS_BOT"] = bot
    bot.add_cog(FetchDiscordCommands(bot))
    bot.run(TOKEN_DICT["discord"])


def run_tg_bot(updater):
    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, get_tg_messages)
    dp.add_handler(text_handler)
    updater.start_polling()
    updater.idle()


def started_working():
    print("ПРОГРАММА НАЧАЛА РАБОТАТЬ!")


def run_threads(vk, discord, telegram):
    discord = threading.Thread(target=run_ds_bot, args=(discord,))
    vk = threading.Thread(target=run_vk_bot, args=(vk,))
    started_workin = threading.Thread(target=started_working)
    [i.start() for i in [discord, vk, started_workin]]
    run_tg_bot(telegram)


def main():
    for i in range(1):
        chrome_options = undetected_chromedriver.ChromeOptions()
        driver = undetected_chromedriver.Chrome(options=chrome_options)
        if "web-drivers" not in PARAM_DICT:
            PARAM_DICT["web-drivers"] = [["FREE", driver]]
        else:
            PARAM_DICT["web-drivers"].append(["FREE", driver])
    PARAM_DICT["driver"] = PARAM_DICT["web-drivers"][0][1]
    bot = commands.Bot(command_prefix=PREFIX)
    vk_session_ = vk_api.VkApi(token=TOKEN_DICT["vk_api"])
    longpoll = VkBotLongPoll(vk_session_, "210954683")
    updater = Updater(TOKEN_DICT["telegram.ext"], use_context=True)
    run_threads(longpoll, bot, updater)


async def run_chrome_browser():
    chrome_options = undetected_chromedriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = undetected_chromedriver.Chrome(options=chrome_options)
    if "web-drivers" not in PARAM_DICT:
        PARAM_DICT["web-drivers"] = [["FREE", driver]]
    else:
        PARAM_DICT["web-drivers"].append(["FREE", driver])


async def submit_work_end(function, driver_id, session_id, *args):
    driver = PARAM_DICT["web-drivers"][driver_id[0]][1][0]
    PARAM_DICT["web-drivers"][driver_id[0]][0] = "BUSY"
    await function(driver, args, session_id=session_id)
    PARAM_DICT["web-drivers"][driver_id[0]][0] = "FREE"


def get_tg_messages(update, context):
    print(update.message.text)


class FetchDiscordCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help_bot')
    async def help(self, ctx):
        await ctx.send(
            f'{PREFIX} register == Зарегистрироваться в аккаунте yandex\n'
            f'{PREFIX} get_data "название курса" == Получить весь материал определенного курса\n'
            f'{PREFIX} new_task Не обязательно: "params starting with --" == Получить случайную нерешенную задачу\n' # Позже к примеру учитывать нажатие определенным эмодзи если решено #!
            f'{PREFIX} leader_board == Показать таблицу рейтинга \n' #!
            f'{PREFIX} help_task "Название" == Помочь с задачей если решения есть в базе \n' #!
            f'{PREFIX} help_bot == Получить список о доступных командах \n'
            f"{PREFIX} help_command 'Команда' == Получить помощь по команде\n"
            f"{PREFIX} main_source == Указание главного по материалам курса"
            f"{PREFIX} solve_captcha 'text' == 'Отправить решение капчи' "
            )

    @commands.command(name="register")
    async def  register(self, ctx, login, password):
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        await ctx.send("Идёт авторизация, подождите...")
        result = await authorize_yandex_lyceum(login, password, str(ctx.message.author.id))
        if len(result) == 2 and result[1] == "Я панк":
            await ctx.send(result[0] + "Решай свою паганную капчу")
        elif len(result) == 2 and result[0] == "OK" and result[1]:
            random_token = secrets.token_hex(16)
            if not cur.execute(f"SELECT token FROM users WHERE discord='{str(ctx.message.author.id)}' ").fetchall(): #:  TODO :<
                cur.execute(f"INSERT INTO users (telegram, vkontakte, discord, token) VALUES (NULL, NULL, '{str(ctx.message.author.id)}', '{random_token}')")
                con.commit()
                await ctx.send(f"Вы зарегистрированы вот ваш токен: {random_token}")
        else:
            await ctx.send(result)

    @commands.command(name="get_data")
    async def get_data(self, ctx, *text):
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        token = cur.execute(f"SELECT token from users WHERE discord='{str(ctx.message.author.id)}' ").fetchall()
        if not token:
            await ctx.send("Not authorized")
            return
        await get_all_tasks_and_documentations_with_files(" ".join(text), token[0])
        import shutil
        shutil.make_archive("zip_archives/Received_Lessons", 'zip', 'Received_Lessons')
        await upload_on_mediafire("zip_archives/Received_Lessons.zip")
        shutil.rmtree("Received_Lessons")
        os.remove("zip_archives/Received_Lessons.zip")
        await ctx.send("Done getting all data! Now you can use commands\n Link to the archive: ")

    @commands.command(name="help_command")
    async def help_command(self, ctx, *text):
        await ctx.send(COMMAND_HELPER_DICT.get(" ".join(text), random.choice(sorry)))

    @commands.command(name="main_source")
    async def main_source(self, ctx):
        await ctx.send("""Всеми правами на материалы владеют: \nООО «ЯНДЕКС»\nАНО ДПО «ШАД»\n""")

    @commands.command(name="new_task")
    async def new_task(self, ctx, *args):
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        token = cur.execute(f"SELECT token from users WHERE discord='{str(ctx.message.author.id)}' ").fetchall()
        if not token:
            await ctx.send("Not authorized")
            return
        text = ["--nfp", "--sw", "--ons"]
        sorted_ = ["--sorted_ad", "--sorted_dc"]
        params = {}
        if any(i in args for i in text):
            params["only_something"] = list(filter(lambda y: y in args, text))[0]
        if any(i in sorted_ for i in args):
            params["sorted"] = list(filter(lambda t: t in sorted_, args))[0]


async def authorize_yandex_lyceum(login, password, users_id):
    driver = PARAM_DICT["driver"]
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys(Keys.CONTROL + 't')
    driver.get("https://passport.yandex.ru/auth/add?origin=market_desktop_header&retpath=https%3A%2F%2Fmarket.yandex.ru%2F%3Fclid%3D1601%26loggedin%3D1%26loggedin%3D1")
    await asyncio.sleep(1.2)
    time.sleep(3)
    try:
        email = driver.find_element(By.CLASS_NAME, "Button2 Button2_size_l Button2_view_default")
        email.click()
    except Exception:
        print("ok")
    try:
        email = list(filter(lambda t: t.text == "Почта", BeautifulSoup(driver.page_source, "lxml").find_all("span", class_="Button2-Text")))
        if email:
            print(email)
            email[0].click()
        else:
            raise Exception
    except Exception:
        print("ok")
    input_login = driver.find_element(By.ID, "passp-field-login")
    input_login.send_keys(login)
    try:
        signin = driver.find_element(By.CLASS_NAME,
                                     "Button2 Button2_size_l Button2_view_action Button2_width_max Button2_type_submit")
    except Exception:
        signin = driver.find_element(By.ID, "passp:sign-in")
    signin.click()
    await asyncio.sleep(0.5)
    try:
        driver.find_element(By.CLASS_NAME, "Textinput-Hint Textinput-Hint_state_error")
        return "НЕВЕРНЫЙ ЛОГИН"
    except Exception:
        try:
            driver.find_element(By.ID, "field:input-login:hint")
            return "НЕВЕРНЫЙ ЛОГИН"
        except Exception:
            print("ok")
    try:
        input_password = driver.find_element(By.ID, "passp-field-passwd")
    except Exception:
        input_password = driver.find_element(By.CLASS_NAME, "Textinput-Control")
    input_password.send_keys(password)
    try:
        signin = driver.find_element(By.CLASS_NAME,
                                     "Button2 Button2_size_l Button2_view_action Button2_width_max Button2_type_submit")
    except Exception:
        signin = driver.find_element(By.ID, "passp:sign-in")
    if signin:
        signin.click()
    else:
        return "Something went wrong :rofl:"
    try:
        captcha = driver.find_element(By.CLASS_NAME, "captcha__image")
        return captcha.get_attribute("src"), "Я панк"
    except Exception:
       print("ok")
    try:
        if BeautifulSoup(driver.page_source, "lxml").find("div", attrs={"id": "field:input-passwd:hint", "role": "alert"}):
            return "НЕВЕРНЫЙ ПАРОЛЬ"
        elif BeautifulSoup(driver.page_source, "lxml").find("div", class_="Textinput-Hint Textinput-Hint_state_error"):
            return "НЕВЕРНЫЙ ПАРОЛЬ"
        else:
            raise Exception
    except Exception:
        print("ok")
    await asyncio.sleep(2)
    time.sleep(4)
    try:
        form = driver.find_element(By.CLASS_NAME, "auth-challenge__call-form")
        button = form.find_elements(By.TAG_NAME, "div")[1]
        button.click()
    except Exception:
        print("ok")
    await asyncio.sleep(1.2)
    time.sleep(3)
    DONE = {"YES": False, "counter": 0}
    def code_is_right(code):
        if not code.content.isdigit():
            return False
        if DONE["YES"]:
            return True
        try:
            input_ = driver.find_element(By.CLASS_NAME, "Textinput-Control")
            input_.send_keys(code, Keys.ENTER)
        except Exception:
            time.sleep(3)
            try:
                input_ = driver.find_element(By.ID, "passp-field-phoneCode")
                input_.send_keys(code, Keys.ENTER)
            except Exception:
                print("ok all fine gbye")
                return True
        try:
            driver.find_element(By.CLASS_NAME, "Textinput-Hint Textinput-Hint_state_error")
            time.sleep(5)
            DONE["counter"] += 1
            if DONE["counter"] // 5 == 5:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "Button2 Button2_size_l Button2_view_pseudo Button2_width_max"))).click()
                DONE["counter"] = 0
            message = PARAM_DICT["DS_BOT"].wait_for('message', check=code_is_right)
            code_is_right(message)
        except Exception:
            DONE["YES"] = True
            return True
    message = await PARAM_DICT["DS_BOT"].wait_for('message', check=code_is_right)
    while not message:
        await asyncio.sleep(5)
        print("Спим")
    driver.get("https://lyceum.yandex.ru/courses/")
    await asyncio.sleep(3)
    lessons = BeautifulSoup(driver.page_source, "lxml").find_all("h4", class_="course-card__title")
    USER_INF_DICT[str(users_id)] = [lessons]
    return "OK", [i.text for i in lessons]


async def get_all_tasks_and_documentations_with_files(text, token):
    driver = PARAM_DICT["driver"]
    # important_lesson = list(filter(lambda b: b == text, BeautifulSoup(driver.page_source, "lxml").find_all("h4", class_="course-card__title")))
    # if not important_lesson:
    #     return "Нет такого курса"
    # important_lesson  = important_lesson[0]
    # undetected_chromedriver.Chrome().find_element().get_property()
    important_lesson = driver.find_element(By.XPATH, f"//h4[./text()='{text}']")
    if not important_lesson:
        print("NO SUCH ELEMENT")
        return
    important_lesson.click()
    await asyncio.sleep(3)
    # get_all_lessons = driver.find_elements(By.CLASS_NAME, "link-list__link")
    lessons_block = driver.find_element(By.CLASS_NAME, "link-list_type_main")
    get_all_lessons = lessons_block.find_elements(By.CLASS_NAME, "link-list__link")
    print(*get_all_lessons, len(get_all_lessons), sep="\n")
    all_links_of_lessons = [_.get_attribute("href") for _ in get_all_lessons]
    all_titles_of_lessons = [_.find_element(By.CLASS_NAME, "lesson-card__lesson-title").text for _ in get_all_lessons]
    os.mkdir("Received_Lessons")
    for i, lesson in enumerate(get_all_lessons):
        title = "".join(list(filter(lambda t: t not in """/\\:*?"<>|""", all_titles_of_lessons[i])))
        os.mkdir(f"Received_Lessons/{title}")
        go_through_lesson(all_links_of_lessons[i], i, title, token)


def go_through_lesson(lesson, n, lesson_title, token):
    driver = PARAM_DICT["driver"]
    driver.get(lesson)
    current_link_tasks = driver.current_url
    time.sleep(3)
    all_materials = driver.find_elements(By.CLASS_NAME, "material-list__material-link")
    all_titles = [material.find_element(By.CLASS_NAME, "material-list__material-title").text for material in all_materials]
    all_links = [material.get_attribute("href") for material in all_materials]
    all_tasks = driver.find_elements(By.CLASS_NAME, "student-task-list__task")
    all_tasks_links = [task.get_attribute("href") for task in all_tasks]
    all_tasks_titles = []
    for task in all_tasks_links:
        driver.get(task)
        time.sleep(3)
        all_tasks_titles.append(BeautifulSoup(driver.page_source, "lxml").find(
            "h1", class_="heading heading_level_1 yde1c4--task-header__heading").text)
    nfp_tasks = []
    sw_tasks = []
    all_other_tasks = []
    driver.get(current_link_tasks)
    time.sleep(3)
    all_tasks = driver.find_elements(By.CLASS_NAME, "student-task-list__task")
    for task in all_tasks:
        onf = task.find_elements(By.CLASS_NAME, "solution-status solution-status_type_accepted")
        if len(onf) > 0 and task.find_element(By.CLASS_NAME, "solution-status__score").text != \
            "".join(list(filter(lambda y: y.isdigit(), task.find_element(
                By.CLASS_NAME, "solution-status__max-score").text))):
            nfp_tasks.append(task.get_attribute("href"))
            continue
        sw = task.find_elements(By.CLASS_NAME, "solution-status solution-status_type_rework")
        if len(sw) > 0:
            sw_tasks.append(task.get_attribute("href"))
        else:
            all_other_tasks.append(task.get_attribute("href"))
    # nav-tab nav-tab_view_button
    # y6c2ac--task-description
    for task in sw_tasks + nfp_tasks:
        driver.get(task)
        time.sleep(3)
        driver.find_element(By.CLASS_NAME, "nav-tab nav-tab_view_button").click()
        time.sleep(2)
        text = BeautifulSoup(driver.page_source, "lxml").find("section", class_="y6c2ac--task-description").text
        with open(f"""ReceivedLessons/{lesson_title}/Tasks_{token}/{all_tasks_titles[all_tasks_links.index(task)]}.txt""", "a+", encoding="utf-8") as ope_file:
            ope_file.write(text)
    for j, material in enumerate(all_materials):
        type_of_data, data = fetch_material(all_links[j])
        title = "".join(list(filter(lambda t: t not in """/\\:*?"<>|""", all_titles[j])))
        with open(f"""Received_Lessons/{lesson_title}/{title}{j + 1}{'.html' if type_of_data else '.txt'}""", "a+", encoding='utf-8') as opened_file:
            opened_file.write(str(data))

def fetch_material(link):
    driver = PARAM_DICT["driver"]
    driver.get(link)
    time.sleep(3)
    video, lesson_source = [None] * 2
    video = BeautifulSoup(driver.page_source, "lxml").find("iframe", attrs={'style': 'position: absolute; top: 0; left: 0; width: 100%; height: 100%;'})
    if not video:
        lesson_source = BeautifulSoup(driver.page_source, "lxml").find("section", class_="lesson-material__content")
    return 0 if video else 1, (video["src"] if video else lesson_source)
    # translated_text = ts.google(text, to_language=id_trans_dict[str(self.message.author.id)].split("-")[-1])


def fetch_queue():
    while True:
        for task, queue_elem in PARAM_DICT["queue"]:
            free_browser_session = list(filter(lambda y: y[0] == "FREE", PARAM_DICT["web-drivers"]))
            while not free_browser_session:
                free_browser_session = list(filter(lambda y: y[0] == "FREE", PARAM_DICT["web-drivers"]))
            # TODO: free_browser_session, task submit work end


async def upload_on_mediafire(path):
    from mediafire import MediaFireApi
    from mediafire import MediaFireUploader
    api = MediaFireApi()
    uploader = MediaFireUploader(api)
    session = api.user_get_session_token(
        email='vlad1020@mail.ru',
        password='GJCD5+Q+bj.fp7D',
        app_id='42511')

    api.session = session
    response = api.user_get_info()
    fd = open(path, 'rb')
    if PARAM_DICT["incr"]:
        PARAM_DICT["incr"] += 1
    else:
        PARAM_DICT["incr"] = 1
    result = uploader.upload(fd, f'okay{PARAM_DICT["incr"]}.txt',
                             folder_key='1234567890123')
    print(api.file_get_info(result.quickkey))


if __name__ == "__main__":
    sys.exit(main())

# TODO: Добавить обработку состояния заданий
# TODO: Добавить в базе данных отчет о быстродействии задач решенных учениками
# TODO: Создавать папки с отдельными html файлами для всех новых модулей а также учитывать решения учеников
# TODO: -> После команды для получения данных отправлять zip-archive с информацией в уроках
# TODO: Добавить рейтинг [Рейтинг быстродействия программ, Компактности, Подробности(Комментарии и тд), Баллам]
# TODO: Заносить все данные которые нужны в базы данных!!
# TODO: Добавить очередь для "обработки задачи" в браузерах selenium а так же работа с session box
# TODO: Оптимизировать вход в систему(чтобы не приходилось по пару раз прописывать) а так же оформить сообщения красиво
# TODO: Объединить ботов за счет поиска в базе данных логина и пароля а так же обработка сообщений ими
# TODO: В конце загрузить все на сервер, данные попробовать сохранять на облачном сервере mediafire

# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
# TODO: УСПЕТЬ!!!!
