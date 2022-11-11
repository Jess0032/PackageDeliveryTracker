import asyncio
import json
import re
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp as aiohttp
from telethon.errors import UserIsBlockedError

from telethon.events import NewMessage
import logging

from strings import *
from config import *

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s]%(name)s:%(message)s', level=logging.WARNING)

token = ""

date_format = lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S').strftime('%d %B, %Y %I:%M:%S %p')


def string_status(code, status):
    text = string_data1.format(code=str.upper(code),
                               country=status['p_origen'] or "DESCONOCIDO",
                               timeline=status['timeline'])

    timeline = ''.join(f"**🟦️ {len(status['datos']) - i}**" + string_data2.format(item['oficina_origen'],
                                                                                   item['oficina_destino'],
                                                                                   item['estado'],
                                                                                   date_format(item['fecha']))
                       for i, item in enumerate(status['datos']))

    return text + (timeline or no_data)


@bot.on(NewMessage(pattern='/start'))
async def welcome(event):
    await event.respond(welcome_string)


@bot.on(NewMessage(pattern='\/add\s*(\w*)'))
async def add_elements(event):
    try:
        if time_wape_up:
            await event.respond(time_wape_up_string.format(time_wape_up-datetime.now()))
            return
        if not (code := event.pattern_match.group(1)):
            await event.respond(not_argumnts.format(command='add'))
            return

        async with aiohttp.ClientSession() as session:
            status = await get_status_package_from_api(session, code)

        if status['timeline'] == "ENTREGADO":
            await event.respond(delivered)
            await event.respond(string_status(code, status))
            return

        db_respond = db.add(str.upper(code), str(event.peer_id.user_id),
                            {'status': status['datos'][0]['estado'],
                             'destination': status['datos'][0]['oficina_destino']}
                            if status['datos'] else {'status': '', 'destination': ''})

        await event.respond(db_respond)

        if db_respond == success_add:
            await event.respond(string_status(code, status))

    except aiohttp.ClientConnectorError as e:
        await event.respond(client_error)

    except Exception as e:
        print(e)


@bot.on(NewMessage(pattern='\/del\s*(\w*)'))
async def del_elements(event):
    try:
        if not (code := event.pattern_match.group(1)):
            await event.respond(not_argumnts.format(command='del'))
            return

        await event.respond(db.delete(str(event.peer_id.user_id), str.upper(code)))

    except aiohttp.ClientConnectorError as e:
        await event.respond(client_error)

    except Exception as e:
        print(e)


@bot.on(NewMessage(pattern='\/codes'))
async def get_codes_trackin(event):
    try:
        text = ''.join(
            codes.format(code=package[0], status=json.loads(package[1])["status"],
                         destination=json.loads(package[1])["destination"])
            for package in db.get_packages_from_user(str(event.peer_id.user_id))
        )

        await event.respond(text or not_codes)

        await check_packages(db.get_packages_from_user(str(event.peer_id.user_id)), 1)
    except aiohttp.ClientConnectorError as e:
        await event.respond(client_error)
    except Exception as e:
        print(e)


@bot.on(NewMessage(pattern='\/status\s*(\w*)'))
async def status(event):
    try:
        if time_wape_up:
            await event.respond(time_wape_up_string.format(time_wape_up-datetime.now()))
            return
        if not (code := event.pattern_match.group(1)):
            await event.respond(not_argumnts.format(command='status'))
            return

        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            status = await get_status_package_from_api(session, code)
            await event.respond(string_status(code, status))

        await check_packages(db.get_packages_from_user(str(event.peer_id.user_id)), 1)

    except aiohttp.ClientConnectorError as e:
        await event.respond(client_error)
    except Exception as e:
        print(e)


async def get_status_package_from_api(session, codigo: str):
    data = {
        'codigo': codigo,
        'anno': str(datetime.now().year),
        'token': token,
        'user': ''
    }
    url = "https://www.correos.cu/wp-json/correos-api/enviosweb/"
    try:
        async with session.post(url, data=data) as response:
            response_json = await response.json()

        if response_json['error'] == "Ha consumido su cuota de peticiones.":
            await bot.send_message(ADMIN, json.dumps(response_json))
            global time_wape_up
            time_wape_up = datetime.now() + timedelta(minutes=10)
            await asyncio.sleep(600)
            time_wape_up = None

        if response_json['error'] == 'Token Inválido':
            print(response_json)
            await get_new_token()
            response_json = await get_status_package_from_api(session, codigo)

        return response_json

    except aiohttp.ClientConnectorError as e:
        print('Connection Error for ', codigo, e)
        await bot.send_message(ADMIN, f'Connection Error for {codigo}{str(e)}')
        raise e
    except Exception as e:
        print(e)


async def get_new_token():
    print('Getting new token')
    global token
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.correos.cu/rastreador-de-envios/') as response:
            token = re.search('<input type="hidden" id="side" value="(\w+)">', await response.text())[1]


async def check_packages(packages, time):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True)) as session:
        for package in packages:
            await check_changes(session, package)
            await asyncio.sleep(time)


async def cycle_check():
    await bot.send_message(ADMIN, bot_started)
    while True:
        packages = db.get_packages()
        start = datetime.now()
        await check_packages(packages, 13)
        log_text = f"Cycle made in {datetime.now() - start}, {len(packages)} checked, start at {start}"
        print(log_text)
        await bot.send_message(ADMIN, log_text)


async def check_changes(session, package):
    try:
        status = await get_status_package_from_api(session, package[0])
        status_fromdb = json.loads(package[1])

        if not status['datos'] or (status_fromdb['status'] == status['datos'][0]['estado']
                                   and status_fromdb['destination'] == status['datos'][0]['oficina_destino']):
            return

        last = status['datos'][0]

        message = new_state.format(package=package[0], timeline=status['timeline']) + \
                  string_data2.format(last['oficina_origen'],
                                      last['oficina_destino'],
                                      last['estado'], date_format(last['fecha'])) + view_all_timeline.format(
            package=package[0])

        for user in db.get_users_from_packages(package[0]):
            try:
                await bot.send_message(int(user), message)
            except UserIsBlockedError:
                for package in db.get_packages_from_user(user):
                    db.delete(user, package[0])

        if status['timeline'] == "ENTREGADO":
            db.delete_package(package[0])
        else:
            db.update(package[0], {'status': last['estado'], 'destination': last['oficina_destino']})

    except aiohttp.ClientConnectorError as e:
        print(e)
        await asyncio.sleep(600)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.get_event_loop_policy().get_event_loop().create_task(cycle_check())
    asyncio.get_event_loop_policy().get_event_loop().run_forever()
