import credentials as cred
import vk_botting
from pymysqlpool.pool import Pool  # Для работы с сервером и БД
import pymysql
import aiomysql
bot = vk_botting.Bot(vk_botting.when_mentioned_or_pm(), case_insensitive=True)
config = {'host': cred.host, 'user': cred.user, 'password': cred.password, 'db': cred.db, 'autocommit': True, 'charset': cred.charset, 'cursorclass': pymysql.cursors.DictCursor}
try:
    sqlpool = Pool(**config)
    sqlpool.init()
except Exception as exc:
    print(exc)


# async def abstract_request(query, values, response_needed=False):
#     pool = await aiomysql.create_pool(**config)
#     async with pool.acquire() as conn:
#         async with conn.cursor() as cur:
#             await cur.execute(query, values)
#         if response_needed:
#             resp = cur.fetchall()
#             pool.close()
#             return resp
#     await pool.wait_closed()

def mainmenu():
    keyboard = vk_botting.Keyboard()
    keyboard.add_button('Заполнить заново', vk_botting.KeyboardColor.PRIMARY)
    keyboard.add_button('Искать', vk_botting.KeyboardColor.PRIMARY)
    return keyboard


def like_menu():
    keyboard = vk_botting.Keyboard()
    keyboard.add_button('Топчег', vk_botting.KeyboardColor.PRIMARY)
    keyboard.add_button('Нахуй', vk_botting.KeyboardColor.PRIMARY)
    return keyboard


def your_sex_menu():
    keyboard = vk_botting.Keyboard()
    keyboard.add_button('Мужской', vk_botting.KeyboardColor.PRIMARY)
    keyboard.add_button('Женский', vk_botting.KeyboardColor.PRIMARY)
    return keyboard


def search_sex_menu():
    keyboard = vk_botting.Keyboard()
    keyboard.add_button('Парня', vk_botting.KeyboardColor.PRIMARY)
    keyboard.add_button('Девушку', vk_botting.KeyboardColor.PRIMARY)
    return keyboard


async def user_registration(ctx):
    user_info = dict(user_id=None, user_name=None, user_sex=None, search_sex=None, description=None)
    user_info['user_id'] = ctx.from_id
    await ctx.send('Для начала представься', keyboard=vk_botting.Keyboard.get_empty_keyboard())

    def verefy(message):
        return message.from_id == ctx.from_id

    msg = await bot.wait_for('message_new', check=verefy, timeout=3600)
    user_info['user_name'] = msg.text

    await ctx.send('Теперь скажи какого ты пола', keyboard=your_sex_menu())
    msg = await bot.wait_for('message_new', check=verefy, timeout=3600)
    if msg.text.lower() == 'мужской':
        user_info['user_sex'] = 1
    elif msg.text.lower() == 'женский':
        user_info['user_sex'] = 2

    await ctx.send('Кого ищешь?', keyboard=search_sex_menu())
    msg = await bot.wait_for('message_new', check=verefy, timeout=3600)
    if msg.text.lower() == 'парня':
        user_info['search_sex'] = 1
    elif msg.text.lower() == 'девушку':
        user_info['search_sex'] = 2

    await ctx.send('Пару слов о тебе', keyboard=vk_botting.Keyboard.get_empty_keyboard())
    msg = await bot.wait_for('message_new', check=verefy, timeout=3600)
    user_info['description'] = msg.text
    cursor = con.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id=%s', [user_info['user_id']])
    users = cursor.fetchall()
    if users != ():
        cursor.execute(f'DELETE FROM users WHERE user_id=%s', [user_info['user_id']])
    print(user_info)
    cursor.execute(f'INSERT INTO users (user_id, user_name, user_sex, search_sex, description) '
                           f'VALUES (%s, %s, %s, %s, %s)',
                           [user_info['user_id'], user_info['user_name'], user_info['user_sex'],
                            user_info['search_sex'], user_info['description']])
    cursor.close()
    await show_user_form(ctx)


async def show_user_form(ctx):
    cursor = con.cursor()
    cursor.execute(f'SELECT * FROM users WHERE user_id =%s', [ctx.from_id])
    user_form = cursor.fetchall()
    cursor.close()
    await ctx.send('Вот твоя анкета: \n' + str(user_form[0]['user_name']) + '\nЯ: ' + str(user_form[0]['user_sex']) +
                   '\nИщу: ' + str(user_form[0]['search_sex']) + '\n' + str(user_form[0]['description']),
                   keyboard=mainmenu())  # тут надо расписать красивую отправку сообщений


@bot.command(name='заполнить заново', has_spaces=True)
async def reregister(ctx):
    good_user = await bot.vk_request('groups.isMember', group_id=cred.muecyl_id, user_id=ctx.from_id)
    if good_user['response'] == 0:
        await ctx.send('Ты не муецилист')
    else:
        await user_registration(ctx)


@bot.command(name='начать')
async def begin(ctx):
    good_user = await bot.vk_request('groups.isMember', group_id=cred.muecyl_id, user_id=ctx.from_id)
    # print(good_user)
    if good_user['response'] == 0:
        await ctx.send('Ты не муецилист')
    else:
        cursor = con.cursor()
        cursor.execute(f'SELECT * FROM users WHERE user_id =%s', [ctx.from_id])
        user_form = cursor.fetchall()
        cursor.close()
        if user_form == ():
            await user_registration(ctx)
        else:
            await show_user_form(ctx)


def update_user_suggestions(user_id, user_sex, search_sex):
    cursor = con.cursor()
    cursor.execute('SHOW TABLES in muecyl')
    tables = cursor.fetchall()
    print(tables[0])
    table_exist = False
    for table in tables:
        if table['Tables_in_muecyl'] == ('s' + str(user_id)):
            table_exist = True
            break
    if not table_exist:
        cursor.execute(f'CREATE TABLE s%s (suggestion_id BIGINT)', [user_id])
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    for user in users:
        print(user['user_id'])
        print(user_id)
        print(user['user_sex'])
        print(search_sex)
        print(user['search_sex'])
        print(user_sex)
        cursor.execute(f'SELECT * FROM s%s WHERE suggestion_id = %s', [user_id, user['user_id']])
        if (cursor.fetchall() == ()) and (user['user_id'] != user_id) and (user['user_sex'] == search_sex) and (user['search_sex'] == user_sex):
            cursor.execute(f'INSERT INTO s%s (suggestion_id) VALUES (%s)', [user_id, user['user_id']])
    cursor.close()


@bot.command(name='искать')
async def search(ctx):
    cursor = con.cursor()
    cursor.execute(f'SELECT * FROM users WHERE user_id =%s', [ctx.from_id])
    user_info = cursor.fetchone()
    cursor.close()
    update_user_suggestions(ctx.from_id, user_info['user_sex'], user_info['search_sex'])
    cursor = con.cursor()
    cursor.execute(f'SELECT * FROM s%s', [ctx.from_id])
    suggested_users = cursor.fetchall()
    cursor.close()
    print(suggested_users)
    cur_user = 0;
    for user in suggested_users:
        cursor = con.cursor()
        cursor.execute(f'SELECT * FROM users WHERE user_id = %s', [user['suggestion_id']])
        user_to_suggest = cursor.fetchone()
        print(user_to_suggest)
        cursor.close()
        await ctx.send('Нашел для тебя\n' + user_to_suggest['user_name'] + '\n' + user_to_suggest['description'], keyboard=like_menu())
con = sqlpool.get_conn()
if not con.open:
    con.ping(True)

bot.run(cred.token)
