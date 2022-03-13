import asyncio
import json
import re
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp as aiohttp

from telethon.events import NewMessage
import logging

from strings import *
from config import *

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s]%(name)s:%(message)s', level=logging.WARNING)

token = ""


def string_status(code, status):
    text = string_data1.format(code=str.upper(code),
                               country=status['p_origen'] or "DESCONOCIDO",
                               timeline=status['timeline'])

    timeline = ''.join(f"**🟦️ {len(status['datos']) - i}**" + string_data2.format(item['oficina_origen'],
                                                                                item['oficina_destino'],
                                                                                item['estado'], item['fecha'])
                    for i, item in enumerate(status['datos']))

    return text+(timeline or no_data)


@bot.on(NewMessage(pattern='/start'))
async def welcome(event):
    await event.respond(welcome_string)


@bot.on(NewMessage(pattern='\/add\s*(\w*)'))
async def add_elements(event):

    if not (code := event.pattern_match.group(1)):
        await event.respond(not_argumnts.format(command='add'))
        return

    async with aiohttp.ClientSession() as session:
        status = await get_status_package_from_api(session, code)

    db_respond = db.add(str.upper(code), str(event.peer_id.user_id),
                        {'status': status['datos'][0]['estado'],
                         'destination': status['datos'][0]['oficina_destino']}
                        if status['datos'] else {'status': '', 'destination': ''})

    await event.respond(db_respond)

    if db_respond == 'Success insertion':
        await event.respond(string_status(code, status))


@bot.on(NewMessage(pattern='\/del\s*(\w*)'))
async def del_elements(event):
    if not (code := event.pattern_match.group(1)):
        await event.respond(not_argumnts.format(command='del'))
        return

    await event.respond(db.delete(str(event.peer_id.user_id), code))


@bot.on(NewMessage(pattern='\/codes'))
async def get_codes_trackin(event):
    async with aiohttp.ClientSession() as session:
        await check_packages(session, db.get_packages_from_user(str(event.peer_id.user_id)))

    text = ''.join(
        f'code: **{package[0]}** status: **{json.loads(package[1])["status"]}**\n'
        for package in db.get_packages_from_user(str(event.peer_id.user_id))
    )

    await event.respond(text or 'Usted no está rastreando ningún código aún.')


@bot.on(NewMessage(pattern='\/status\s*(\w*)'))
async def status(event):

    if not (code := event.pattern_match.group(1)):
        await event.respond(not_argumnts.format(command='status'))
        return

    async with aiohttp.ClientSession() as session:
        await check_packages(session, db.get_packages_from_user(str(event.peer_id.user_id)))

        status = await get_status_package_from_api(session, code)

    await event.respond(string_status(code, status))


async def get_status_package_from_api(session, codigo: str):
    data = {
        'codigo': codigo,
        'anno': str(datetime.now().year),
        'token': token,
        'user': ''
    }
    url = "https://www.correos.cu/wp-json/correos-api/enviosweb/"

    async with session.post(url, data=data) as response:
        response_json = await response.json()

    if response_json['error'] == 'Token Inválido':
        await get_new_token()
        response_json = await get_status_package_from_api(session, codigo)

    return response_json


async def get_new_token():
    global token
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.correos.cu/rastreador-de-envios/') as response:
            token = re.search('<input type="hidden" id="side" value="(\w+)">', await response.text()).group(1)


async def check_packages(session, packages):
    tasks = [asyncio.create_task(check_changes(session, package)) for package in packages]
    await asyncio.gather(*tasks, return_exceptions=True)

    return len(tasks)


async def check_status():
    start_time = datetime.now()
    async with aiohttp.ClientSession() as session:
        count = await check_packages(session, db.get_packages())

    print(f"Check status of {count} package in {(datetime.now() - start_time).total_seconds()} seconds.")


async def check_changes(session, package):
    status = await get_status_package_from_api(session, package[0])
    status_fromdb = json.loads(package[1])

    if not status['datos'] or (status_fromdb['status'] == status['datos'][0]['estado']
                                and status_fromdb['destination'] == status['datos'][0]['oficina_destino']):
        return

    last = status['datos'][0]

    message = new_state.format(package=package[0], timeline=status['timeline']) + \
              string_data2.format(last['oficina_origen'],
                                  last['oficina_destino'],
                                  last['estado'], last['fecha']) + view_all_timeline.format(package=package[0])

    for user in db.get_users_from_packages(package[0]):
        await bot.send_message(int(user), message)

    if status['timeline'] == "ENTREGADO":
        db.delete_package(package[0])
    else:
        db.update(package[0], {'status': last['estado'], 'destination': last['oficina_destino']})


if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    print("Iniciando...")
    scheduler.add_job(check_status, 'interval', hours=1, next_run_time=datetime.now())
    scheduler.start()
    asyncio.get_event_loop().run_forever()
