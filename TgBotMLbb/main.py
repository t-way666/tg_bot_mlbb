import telebot
import pandas as pd
from functools import wraps
from config import BOT_TOKEN  # Импортируем токен из config.py

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# Загрузка данных из CSV-файла
try:
    df = pd.read_csv('characters.csv')
except FileNotFoundError:
    print("Ошибка: Файл 'characters.csv' не найден. Пожалуйста, убедитесь, что файл находится в той же директории, что и скрипт.")
    exit()  # Завершаем выполнение скрипта, если файл не найден

# --- Функции для работы с персонажами ---
def get_character_info(name, level=15):
    character = df[df['имя'].str.lower() == name.lower()]
    if character.empty:
        return None
    character = character.squeeze()  # Преобразуем DataFrame в Series

    response = f"✨ **Информация о {character['имя']} на уровне {level}** ✨\n\n **Роль:** {character['роль']}\n\n"
    response += f" **Характеристики без прироста по уровню:**\n"
    stats_without_growth = [
        'магическая сила (с уровнем не растет)',
        'коэффициент скорости атаки %',
        'скорость передвижения',
        'минимальная дальность базовой атаки',
        'максимальная дальность базовой атаки'
    ]

    for stat in stats_without_growth:
        if stat in character.index:
            response += f"- {stat}: {character[stat]}\n"
        else:
            response += f"- {stat}: данных нет\n"

    response += f"\n **Характеристики на уровне {level}:**\n"
    stats_with_growth = [
        ('ОЗ на 1 уровне', 'ОЗ на 15 уровне', 'ОЗ'),
        ('регенерация ОЗ на 1 уровне', 'регенерация ОЗ на 15 уровне', 'регенерация ОЗ'),
        ('мана/энергия на 1 уровне', 'мана/энергия на 15 уровне', 'мана'),
        ('регенерация маны/энергии на 1 уровне', 'регенерация маны/энергии на 15 уровне', 'регенерация маны'),
        ('физическая атака на 1 уровне', 'физическая атака на 15 уровне', 'физическая атака'),
        ('физическая защита на 1 уровне', 'физическая защита на 15 уровне', 'физическая защита'),
        ('магическая защита на 1 уровне', 'магическая защита на 15 уровне', 'магическая защита'),
        ('скорость атаки на 1 уровне', 'скорость атаки на 15 уровне', 'скорость атаки'),
    ]

    for base_stat, growth_stat, stat_name in stats_with_growth:
        if base_stat in character.index and growth_stat in character.index:
            base = character[base_stat]
            growth = (character[growth_stat] - base) / 14
            value = round(base + growth * (level - 1), 2)
            response += f"- {stat_name}: {value}\n"
        else:
            response += f"- {stat_name}: данных нет\n"

    return response

# --- Функция для получения списка характеристик ---
def list_characteristics():
    response = (
        "Список доступных характеристик (вы можете вводить полное название характеристик, либо же их короткие варианты - чтобы сэкономить время):\n\n"
        "Характеристики, которые растут или меняются с уровнем:\n"
        "ОЗ - основное здоровье\n"
        "РОЗ - регенерация ОЗ\n"
        "М/Э - мана/энергия\n"
        "РМ/Э - регенерация маны/энергии\n"
        "ФА - физическая атака\n"
        "ФЗ - физическая защита\n"
        "МЗ - магическая защита\n"
        "СА - скорость атаки\n\n"
        "Характеристики, которые не меняются от уровня:\n"
        "МС - магическая сила\n"
        "КСА - коэффициент скорости атаки %\n"
        "СП - скорость передвижения\n"
        "МинДБА - минимальная дальность базовой атаки\n"
        "МаксДБА - максимальная дальность базовой атаки"
    )
    return response

# --- Функция для сортировки персонажей по характеристике и уровню ---
def sort_characters_by_stat(stat, level):
    # Приведение вводимых характеристик к единообразному виду
    stat = stat.lower()
    stat_map = {
        'оз': 'ОЗ',
        'роз': 'регенерация ОЗ',
        'м/э': 'мана/энергия',
        'рм/э': 'регенерация маны/энергии',
        'фа': 'физическая атака',
        'фз': 'физическая защита',
        'мз': 'магическая защита',
        'са': 'скорость атаки',
        'мс': 'магическая сила (с уровнем не растет)',
        'кса': 'коэффициент скорости атаки %',
        'сп': 'скорость передвижения',
        'миндба': 'минимальная дальность базовой атаки',
        'максдба': 'максимальная дальность базовой атаки'
    }
    stat = stat_map.get(stat, stat)

    characters = []
    for _, character in df.iterrows():
        if stat in ['ОЗ', 'регенерация ОЗ', 'мана/энергия', 'регенерация маны/энергии', 'физическая атака', 'физическая защита', 'магическая защита', 'скорость атаки']:
            base_stat = f'{stat} на 1 уровне'
            growth_stat = f'{stat} на 15 уровне'
            if base_stat in character.index and growth_stat in character.index:
                base = character[base_stat]
                growth = (character[growth_stat] - base) / 14
                value = round(base + growth * (level - 1), 2)
            else:
                value = None
        else:
            value = character.get(stat, None)
        characters.append((character['имя'], value))

    characters.sort(key=lambda x: x[1] if x[1] is not None else float('-inf'), reverse=True)
    return characters

# --- Функции для рангов и звезд ---
def reset_user_data(user_id):
    user_data.pop(user_id, None)

def get_rank_and_level(stars):
    ranks = [
        {'name': 'Воин', 'levels': 3, 'stars_per_level': 3},
        {'name': 'Элита', 'levels': 3, 'stars_per_level': 4},
        {'name': 'Мастер', 'levels': 4, 'stars_per_level': 4},
        {'name': 'Грандмастер', 'levels': 5, 'stars_per_level': 5},
        {'name': 'Эпик', 'levels': 5, 'stars_per_level': 5},
        {'name': 'Легенда', 'levels': 5, 'stars_per_level': 5}
    ]

    for rank in ranks:
        total_stars = rank['levels'] * rank['stars_per_level']
        if stars < total_stars:
            level = rank['levels'] - stars // rank['stars_per_level']
            stars_in_level = stars % rank['stars_per_level']
            return rank['name'], level, stars_in_level
        stars -= total_stars

    if stars < 25:
        return 'Обычный мифик', None, stars
    if stars < 50:
        return 'Мифическая честь', None, stars - 25
    if stars < 100:
        return 'Мифическая слава', None, stars - 50
    return 'Мифический бессмертный', None, stars - 100

# --- Декоратор для обработки команд ---
def command_handler(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if check_for_commands(message):
            return
        return func(message, *args, **kwargs)
    return wrapper

def check_for_commands(message):
    commands = {
        '/start': start,
        '/stars_calculate': stars_calculate,
        '/winrate_calculate': winrate_calculate,
        '/rank': get_rank,
        '/hero': handle_hero_command,
        '/characters_list': characters_list,
        '/sorting': sorting
    }
    command = message.text.split()[0].lower()
    if command in commands:
        reset_user_data(message.from_user.id)
        commands[command](message)
        return True
    return False

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def start(message):
    reset_user_data(message.from_user.id)
    start_text = (
        f'Привет, {message.from_user.first_name} {message.from_user.last_name or ""}!\n\n'
        'Добро пожаловать в нашего телеграм бота. Вот список доступных команд:\n\n'
        '<b>Доступные команды:</b>\n'
        '/start - Начало работы с ботом\n'
        '/stars_calculate - Расчет необходимого количества игр для достижения заданного количества звезд\n'
        '/winrate_calculate - Расчет необходимого количества побед для достижения заданного винрейта\n'
        '/rank - Узнать текущий ранг по количеству звезд\n'
        '/hero - Получить информацию о персонаже\n'
        '/characters_list - Получить список доступных характеристик\n'
        '/sorting - Сортировка персонажей по характеристикам\n'
        '\n'
        '<em>Дополнительные команды:</em>\n'
        'привет - Поздороваться с ботом\n'
        'id - Узнать свой ID'
    )
    bot.send_message(message.chat.id, start_text, parse_mode='html')

@bot.message_handler(commands=['stars_calculate'])
def stars_calculate(message):
    user_data[message.chat.id] = {}
    msg = bot.send_message(message.chat.id, "Введите ваш текущий винрейт (в процентах, от 0 до 100):")
    bot.register_next_step_handler(msg, process_winrate_step, message.chat.id)

@command_handler
def process_winrate_step(message, user_id):
    try:
        winrate = float(message.text)
        if not 0 <= winrate <= 100:
            raise ValueError
        user_data[user_id]['winrate'] = winrate
        msg = bot.send_message(message.chat.id, "Введите количество сыгранных матчей (положительное целое число):")
        bot.register_next_step_handler(msg, process_games_played_step, user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение для винрейта (от 0 до 100):")
        bot.register_next_step_handler(msg, process_winrate_step, user_id)

@command_handler
def process_games_played_step(message, user_id):
    try:
        games_played = int(message.text)
        if games_played <= 0:
            raise ValueError
        user_data[user_id]['games_played'] = games_played
        msg = bot.send_message(message.chat.id, "Введите количество полученных звезд (положительное число):")
        bot.register_next_step_handler(msg, process_stars_gained_step, user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите положительное целое число для сыгранных матчей:")
        bot.register_next_step_handler(msg, process_games_played_step, user_id)

@command_handler
def process_stars_gained_step(message, user_id):
    try:
        stars_gained = float(message.text)
        if stars_gained < 0:
            raise ValueError
        user_data[user_id]['stars_gained'] = stars_gained
        msg = bot.send_message(message.chat.id, "Введите целевое количество звезд (больше текущего):")
        bot.register_next_step_handler(msg, process_target_stars_step, user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите положительное число для полученных звезд:")
        bot.register_next_step_handler(msg, process_stars_gained_step, user_id)

@command_handler
def process_target_stars_step(message, user_id):
    try:
        target_stars = float(message.text)
        stars_gained = user_data[user_id]['stars_gained']
        if target_stars <= stars_gained:
            raise ValueError
        user_data[user_id]['target_stars'] = target_stars
        winrate = user_data[user_id]['winrate']
        games_played = user_data[user_id]['games_played']
        avg_stars_per_game = stars_gained / games_played
        if avg_stars_per_game == 0:
            bot.send_message(message.chat.id, "Среднее количество звезд за игру равно 0. Невозможно рассчитать необходимое количество игр.")
            reset_user_data(user_id)
            return
        stars_needed = target_stars - stars_gained
        games_needed = int(stars_needed / avg_stars_per_game)
        bot.send_message(message.chat.id, f'Вам нужно сыграть примерно {games_needed} игр, чтобы достичь {target_stars} звезд.')
        reset_user_data(user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение для целевого количества звезд (больше текущего):")
        bot.register_next_step_handler(msg, process_target_stars_step, user_id)

@bot.message_handler(commands=['winrate_calculate'])
def winrate_calculate(message):
    user_data[message.chat.id] = {}
    msg = bot.send_message(message.chat.id, "Введите ваш текущий винрейт (в процентах, от 0 до 100):")
    bot.register_next_step_handler(msg, process_current_winrate_step, message.chat.id)

@command_handler
def process_current_winrate_step(message, user_id):
    try:
        winrate = float(message.text)
        if not 0 <= winrate <= 100:
            raise ValueError
        user_data[user_id]['current_winrate'] = winrate
        msg = bot.send_message(message.chat.id, "Введите количество сыгранных матчей (положительное целое число):")
        bot.register_next_step_handler(msg, process_current_games_played_step, user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение для текущего винрейта (от 0 до 100):")
        bot.register_next_step_handler(msg, process_current_winrate_step, user_id)

@command_handler
def process_current_games_played_step(message, user_id):
    try:
        games_played = int(message.text)
        if games_played <= 0:
            raise ValueError
        user_data[user_id]['current_games_played'] = games_played
        msg = bot.send_message(message.chat.id, "Введите ваш средний винрейт в будущих играх (в процентах, от 0 до 100):")
        bot.register_next_step_handler(msg, process_average_future_winrate_step, user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите положительное целое число для количества сыгранных матчей:")
        bot.register_next_step_handler(msg, process_current_games_played_step, user_id)

@command_handler
def process_average_future_winrate_step(message, user_id):
    try:
        avg_future_winrate = float(message.text)
        if not 0 <= avg_future_winrate <= 100:
            raise ValueError
        user_data[user_id]['avg_future_winrate'] = avg_future_winrate
        current_winrate = user_data[user_id]['current_winrate']
        msg = bot.send_message(message.chat.id, f"Введите желаемый общий винрейт (в процентах, от {current_winrate:.2f} до 100):")
        bot.register_next_step_handler(msg, process_target_winrate_step, user_id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение для среднего будущего винрейта (от 0 до 100):")
        bot.register_next_step_handler(msg, process_average_future_winrate_step, user_id)

@command_handler
def process_target_winrate_step(message, user_id):
    try:
        target_winrate = float(message.text)
        current_winrate = user_data[user_id]['current_winrate']
        if not current_winrate <= target_winrate <= 100:
            raise ValueError
        user_data[user_id]['target_winrate'] = target_winrate
        calculate_required_games(message, user_id)
    except ValueError:
        current_winrate = user_data[user_id]['current_winrate']
        msg = bot.send_message(message.chat.id, f"Пожалуйста, введите корректное числовое значение для желаемого винрейта (от {current_winrate:.2f} до 100):")
        bot.register_next_step_handler(msg, process_target_winrate_step, user_id)

def calculate_required_games(message, user_id):
    current_winrate = user_data[user_id]['current_winrate']
    current_games_played = user_data[user_id]['current_games_played']
    avg_future_winrate = user_data[user_id]['avg_future_winrate']
    target_winrate = user_data[user_id]['target_winrate']

    if avg_future_winrate == 0:
        bot.send_message(message.chat.id, "Ваш средний будущий винрейт не может быть 0%.")
        reset_user_data(user_id)
        return

    if avg_future_winrate <= target_winrate:
        bot.send_message(message.chat.id, "Ваш средний будущий винрейт должен быть выше желаемого общего винрейта для достижения цели.")
        reset_user_data(user_id)
        return

    current_wins = (current_winrate / 100) * current_games_played
    target_wins = (target_winrate / 100) * (current_games_played + current_games_played * (target_winrate - current_winrate) / (avg_future_winrate - target_winrate))
    required_games = (target_wins - current_wins) / (avg_future_winrate / 100)

    if required_games <= 0:
        bot.send_message(message.chat.id, "Ваш текущий винрейт уже выше желаемого.")
        reset_user_data(user_id)
        return

    required_games = int(required_games)
    response = f"Чтобы достичь общего винрейта {target_winrate:.2f}%, вам нужно сыграть примерно {required_games} дополнительных игр с винрейтом {avg_future_winrate:.2f}%."
    bot.send_message(message.chat.id, response)
    reset_user_data(user_id)

@bot.message_handler(commands=['rank'])
def get_rank(message):
    msg = bot.send_message(message.chat.id, "Введите количество ваших звезд (положительное целое число):")
    bot.register_next_step_handler(msg, process_rank_step)

@command_handler
def process_rank_step(message):
    try:
        stars = int(message.text)
        if stars < 0:
            raise ValueError
        rank_name, level, stars_in_level = get_rank_and_level(stars)
        if level is not None:
            response = f'Ваш ранг: {rank_name}, уровень {level}, звёзд в уровне: {stars_in_level}.'
        else:
            response = f'Ваш ранг: {rank_name}, звёзд сверх уровня: {stars_in_level}.'
        bot.send_message(message.chat.id, response)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите положительное целое число для количества звёзд:")
        bot.register_next_step_handler(msg, process_rank_step)

@bot.message_handler(func=lambda message: message.text.strip().lower() == 'привет')
def greet(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Как могу помочь?")

@bot.message_handler(func=lambda message: message.text.strip().lower() == 'id')
def send_id(message):
    bot.send_message(message.chat.id, f"Ваш ID: {message.from_user.id}")

# --- Обработчик информации о персонаже ---
@bot.message_handler(commands=['hero'])
def handle_hero_command(message):
    user_data[message.chat.id] = {}
    msg = bot.send_message(message.chat.id, "Введите имя героя:")
    bot.register_next_step_handler(msg, process_hero_name_step)

@command_handler
def process_hero_name_step(message):
    user_id = message.chat.id
    hero_name = message.text.strip()
    user_data[user_id]['hero_name'] = hero_name
    msg = bot.send_message(user_id, "Введите уровень героя:")
    bot.register_next_step_handler(msg, process_hero_level_step)

@command_handler
def process_hero_level_step(message):
    user_id = message.chat.id
    try:
        hero_level = int(message.text.strip())
        hero_name = user_data[user_id]['hero_name']
        response = get_character_info(hero_name, hero_level)
        if response:
            bot.send_message(user_id, response, parse_mode='Markdown')
        else:
            bot.send_message(user_id, f"Извините, я не нашёл персонажа с именем {hero_name}. Попробуйте ещё раз.")
    except ValueError:
        bot.send_message(user_id, "Пожалуйста, введите корректное числовое значение для уровня героя.")
        msg = bot.send_message(user_id, "Введите уровень героя:")
        bot.register_next_step_handler(msg, process_hero_level_step)

# --- Обработчик списка характеристик ---
@bot.message_handler(commands=['characters_list'])
def characters_list(message):
    response = list_characteristics()
    bot.send_message(message.chat.id, response)

# --- Обработчик сортировки персонажей ---
@bot.message_handler(commands=['sorting'])
def sorting(message):
    user_id = message.chat.id
    user_data[user_id] = {'state': 'awaiting_sorting_characteristic'}
    bot.send_message(user_id, "Введите по какой характеристике вы хотите сортировать персонажей:")

@command_handler
def process_sorting_characteristic(message):
    user_id = message.chat.id
    characteristic = message.text.strip().lower()
    valid_characteristics = {
        'оз': 'ОЗ', 'роз': 'регенерация ОЗ', 'м/э': 'мана/энергия',
        'рм/э': 'регенерация маны/энергии', 'фа': 'физическая атака',
        'фз': 'физическая защита', 'мз': 'магическая защита',
        'са': 'скорость атаки', 'мс': 'магическая сила (с уровнем не растет)',
        'кса': 'коэффициент скорости атаки %', 'сп': 'скорость передвижения',
        'миндба': 'минимальная дальность базовой атаки', 'максдба': 'максимальная дальность базовой атаки'
    }
    characteristic = valid_characteristics.get(characteristic, characteristic)
    if characteristic not in valid_characteristics.values():
        bot.send_message(user_id, "Введенная характеристика некорректна. Пожалуйста, введите одну из следующих характеристик:\n" + list_characteristics())
        return
    user_data[user_id]['sorting_characteristic'] = characteristic
    user_data[user_id]['state'] = 'awaiting_sorting_level'
    bot.send_message(user_id, "Введите какой уровень должен быть у сортируемых персонажей:")

@command_handler
def process_sorting_level(message):
    user_id = message.chat.id
    try:
        level = int(message.text.strip())
        characteristic = user_data[user_id]['sorting_characteristic']
        characters = sort_characters_by_stat(characteristic, level)
        response = f"Сортировка персонажей по характеристике '{characteristic}' на уровне {level}:\n\n"
        for index, (name, value) in enumerate(characters, start=1):
            response += f"{index}. {name}: {value}\n"
        bot.send_message(user_id, response)
        user_data.pop(user_id)
    except ValueError:
        bot.send_message(user_id, "Пожалуйста, введите корректное числовое значение для уровня.")
        bot.send_message(user_id, "Введите какой уровень должен быть у сортируемых персонажей:")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id

    if user_id not in user_data:
        check_for_commands(message)
        return

    state = user_data[user_id].get('state')

    if state == 'awaiting_sorting_characteristic':
        process_sorting_characteristic(message)
    elif state == 'awaiting_sorting_level':
        process_sorting_level(message)
    elif state == 'awaiting_hero_name':
        process_hero_name_step(message)
    elif state == 'awaiting_hero_level':
        process_hero_level_step(message)
    else:
        if not check_for_commands(message):
            bot.reply_to(message, "Извините, я не понял вашу команду. Попробуйте ещё раз или используйте /start для получения списка команд.")

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=600, long_polling_timeout=600)