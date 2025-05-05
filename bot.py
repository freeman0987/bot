"""
Проект: Телеграм бот
Библиотеки: python-telegram-bot, openai

ctrl + ПКМ  - перенесет к переменной где создана
ctrl + /    - однострочный коммент

"""
# region

# conda create -n myenv python=3.12
# conda install python=3.13 ..
# conda activate myenv
# conda info --envs

# python --version

# end region

from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from gpt import *
from util import *                                           # Разница с import util


# Обработка команды /start
async def start(update, context):
    dialog.mode = 'main'
    text = load_message('main')                               # переменная text = подгружаем main.txt (без await потому что функция не ассинхронная)
    await send_photo(update, context, 'main')           # Фото вместе со /start
    await send_text(update, context, text)                    # Передаем text после /start
    await show_main_menu(update, context,
                         {
                            'start': 'главное меню бота',
                            'profile': 'генерация Tinder-профля 😎',
                            'opener': 'сообщение для знакомства 🥰',
                            'message': 'переписка от вашего имени 😈',
                            'date': 'переписка со звездами 🔥',
                            'gpt': 'задать вопрос чату GPT 🧠'
                                    })


# Обработка команды /gpt (аналогично как /start)
async def gpt(update, context):
    dialog.mode = 'gpt'
    text = load_message('gpt')
    await send_photo(update, context, 'gpt')
    await send_text(update, context, text)


# Обработка сообщений gpt (передается в обработке ответов в if)
async def gpt_dialog(update, context):
    text = update.message.text                                                                # Получаем собщение пользователя из чата
    prompt = load_prompt('gpt')                                                               # Хороший тон (load вызвана в другом файле txt)
    answer = await chatgpt.send_question(prompt, text)                                       # Хороший тон использовать txt файл, не писать текстом
    # answer = await chatgpt.send_question("напиши четкий и короткий ответ на вопрос", text)  # Передаем в чат gpt (задание, текст пользователя)
    await send_text(update, context, answer)                                                 # Присылаем ответ от gpt пользователю


# /date и оформление команды:  вывод кнопок, сообщения, фото
async def date(update, context):
    dialog.mode = 'date'
    text = load_message('date')
    await send_photo(update, context, 'date')
    await send_text_buttons(update, context, text,
                            {
                            'date_grande': 'Ариана Гранде',
                            'date_robbie': 'Марго Робби',
                            'date_zendaya': 'Зендея',
                            'date_gosling': 'Райан Гослинг',
                            'date_hardy': 'Том Харди'
                                    })

# логика общения человека с gpt
async def date_dialog(update, context):
    text = update.message.text                                             # получаем текст пользователя
    my_message = await send_text(update, context, 'typing...')
    answer = await chatgpt.add_message(text)                               # добавляем_add текст (await можно сохранить)
    # await send_text(update, context, answer)                             # отправляем ответ
    await my_message.edit_text(answer)

# Логика ответа, подгрузки фото, промпта, передача задания для gpt
async def date_button(update, context):
    query = update.callback_query.data                                     # в query передается = date_grande etc
    await update.callback_query.answer()                                   # Телеграм рекомендует добавлять...

    await send_photo(update, context, query)                               # ! Узнать как query получает фото как-то путанно
    await send_text(update, context, "Отличный выбор! Пригласите девушку (парня) на свидание за 5 сообщений")

    prompt = load_prompt(query)                                            # ! Также только текст подгружаем
    chatgpt.set_prompt(prompt)                                             # Задание для gpt


# /message
async def message(update, context):
    dialog.mode = 'message'
    text = load_message('message')
    await send_photo(update, context, 'message')
    await send_text_buttons(update, context, text,
                            {
                            'message_next': 'следущее сообщение',
                            'message_date': 'Пригласить на свидание'
                                    })
    dialog.list.clear()                                                   # очищаем перед заходом в message_dialog


async def message_button(update, context):
    query = update.callback_query.data                                    # в query передается = date_grande etc
    await update.callback_query.answer()                                  # Разработчики телеграмм рекомендуют

    prompt = load_prompt(query)
    user_chat_history = '\n\n'.join(dialog.list)                          # Объеденить список по разделителю \n\n
    my_message = await send_text(update, context, 'ChatGPT 🧠processing...')
    answer = await chatgpt.send_question(prompt, user_chat_history)
    await my_message.edit_text(answer)


async def message_dialog(update, context):
    text = update.message.text
    dialog.list.append(text)

# /profile бработка команды ее вызов
async def profile(update, context):
    dialog.mode = 'profile'
    text = load_message('profile')
    await send_photo(update, context, 'profile')
    await send_text(update, context, text)

    # стираем чтобы при след вызове не накапливалось
    dialog.user.clear()
    dialog.count = 0                                                    # счетчик вопросов
    await send_text(update, context, 'Сколько вам лет?')


async def profile_dialog(update, context):
    text = update.message.text
    dialog.count += 1

    if dialog.count == 1:
        dialog.user["age"] = text
        await send_text(update, context, 'Кем вы работаете ?')
    elif dialog.count == 2:
        dialog.user["occupation"] = text
        await send_text(update, context, 'У вас есть хобби?')
    elif dialog.count == 3:
        dialog.user["hobby"] = text
        await send_text(update, context, 'Что вам НЕ нравится в людях?')
    elif dialog.count == 4:
        dialog.user["annoys"] = text
        await send_text(update, context, 'Цель знакомства?')
    elif dialog.count == 5:
        dialog.user["goals"] = text

        prompt = load_prompt('profile')
        user_info = dialog_user_info_to_str(dialog.user)

        my_message = await send_text(update, context, "ChatGPT 🧠 processing...")
        answer = await chatgpt.send_question(prompt, user_info)
        await my_message.edit_text(answer)

# /opener вызов команды
async def opener(update, context):
    dialog.mode = 'opener'
    text = load_message('opener')
    await send_photo(update, context, 'opener')
    await send_text(update, context, text)

    # стираем чтобы при след вызове не накапливалось
    dialog.user.clear()
    dialog.count = 0  # счетчик вопросов
    await send_text(update, context, 'Имя девушки?')


# логика диалога
async def opener_dialog(update, context):
    text = update.message.text
    dialog.count += 1

    if dialog.count == 1:
        dialog.user["name"] = text
        await send_text(update, context, 'Сколько ей лет ?')
    elif dialog.count == 2:
        dialog.user["age"] = text
        await send_text(update, context, 'Оценить ее внешность: 1-10 баллов')
    elif dialog.count == 3:
        dialog.user["handsome"] = text
        await send_text(update, context, 'Кем работает?')
    elif dialog.count == 4:
        dialog.user["occupation"] = text
        await send_text(update, context, 'Цель знакомства?')
    elif dialog.count == 5:
        dialog.user["goals"] = text

        prompt = load_prompt('opener')                                  # Задание
        user_info = dialog_user_info_to_str(dialog.user)

        my_message = await send_text(update, context, "ChatGPT 🧠 processing...")
        answer = await chatgpt.send_question(prompt, user_info)
        await my_message.edit_text(answer)


# Функция обработки ответов
async def hello(update, context):
    if dialog.mode == 'gpt':                                              # определяет в каком модуле мы общаемся
        await gpt_dialog(update, context)
    elif dialog.mode == 'date':
        await date_dialog(update, context)
    elif dialog.mode == 'message':
        await message_dialog(update, context)
    elif dialog.mode == 'profile':
        await profile_dialog(update, context)
    elif dialog.mode == 'opener':
        await opener_dialog(update, context)
    else:
        await send_text(update, context, '*Вы написали* '.lower()
                        + update.message.text)                            # дублирует сообщение
        await send_photo(update, context, 'avatar_main')            # Фото

        await send_text(update, context, f'Привет *{update.effective_user.username}* ')       # Ответ
        # await send_text(update, context, 'Готов к приключениям?')       # Ответ

        # Создаем кнопки в самом чате
        await send_text_buttons(update, context, 'Готов к приключениям ловелас😎?',
                                {
                                'start': 'да',
                                'stop': 'нет'
                                        })


# Функционал кнопок
async def hello_button(update, context):
    query = update.callback_query.data                                     # Получаем данные при нажатии на кнопку из объекта update
    if query == 'start':
        await send_text(update, context, f'Отлично! ❤️ выбери режим из меню \n\n  {'\t'*25} /start" \n\n Это приключение запомнится тебе!')
    else:
        await send_text(update, context, 'Подумай еще раз 😎 Взгляни на меню /start')


# Переключатель диалогов
dialog = Dialog()                                                          # создаем экземпляр класса Dialog()
dialog.mode = None                                                         # переменная для переключения режима диалога: /Start, /gpt ...
dialog.list = []                                                           # Не понятно почему через точку, что это ?
dialog.count = 0                                                           # Счетчик вопросов для profile
dialog.user = {}                                                           # Словарь с вопросами

chatgpt = ChatGptService(token='javcgkAld/r/7U60nS8WDUhWeWVYkZbhjQYpKBFGTvoj5842ast7Pxc54epaCxHRBWXa4vjUutckFaoaUmyOdt62mPPZjjrSFzHlklUvRxjKkD54HiY1iMRLus7TxOkcmPElgqCRPBocX6wJsuWbUTuGkgPNjhYwE08Bvau9oVOiaBcWnUrI/ewY+ccVqx7dnAN4A7RhT46B8BjZjVtU/H8jZakz1cJir+37f/KOL/cTVnmJo=')


# Передаём данные в движок telegram
app = ApplicationBuilder().token("7862010297:AAHwltMSAh9_Fi9mYQJMqkOapaBK0yvw5dE").build()

# Делаем Хендлеры - При получении надписи старт, вызовется функция start
app.add_handler(CommandHandler('Start', start))                   # Регистрируем команду /start в telegram
app.add_handler(CommandHandler('gpt', gpt))                       # Регистрируем команду /gpt в telegram
app.add_handler(CommandHandler('date', date))
app.add_handler(CommandHandler('message', message))
app.add_handler(CommandHandler('profile', profile))
app.add_handler(CommandHandler('opener', opener))

# & ~filters.COMMAND - чтобы не выводил ответы по нажатю на команды типа /gpt
# ~(Тильда значит нет) не обрабатывать
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, hello))      # Регестрируем обработчик в приложении


app.add_handler(CallbackQueryHandler(date_button, pattern="^date_.*"))       # Регулярное выражение, создаем отбор выражений через шаблон
app.add_handler(CallbackQueryHandler(message_button, pattern="^message_.*")) # Регулярное выражение, создаем отбор выражений через шаблон
app.add_handler(CallbackQueryHandler(hello_button))                          # CallbackQueryHandler Обработчик кнопок
app.run_polling()
