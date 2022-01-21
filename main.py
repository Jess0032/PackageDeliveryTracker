import asyncio
import re
from datetime import datetime
import requests

from telethon.events import NewMessage
import logging

from config import *

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s]%(name)s:%(message)s', level=logging.WARNING)

datos_string: str = """
OFICINA_ORIGEN : **{}**
OFICINA_DESTINO : **{}**
ESTADO : **{}**
FECHA : **{}**

"""

token = ""


@bot.on(NewMessage(pattern='\/add (.+)'))
async def add_elements(event):
    print(event)
    code = str.upper(event.pattern_match.group(1))
    await event.respond(db.add(str.upper(code), '', event.peer_id.user_id))


@bot.on(NewMessage(pattern='\/del (.+)'))
async def del_elements(event):
    code = str.upper(event.pattern_match.group(1))
    event.respond(await db.delete(event.peer_id.user_id, code))


@bot.on(NewMessage(pattern='\/codes'))
async def get_elements(event):
    codes = await check_changes(event.peer_id.user_id)
    print(codes)
    for element in codes:
        await event.respond(f'code: **{element.id}** status: **{element.status}**')


@bot.on(NewMessage(pattern='\/status (.+)'))
async def status(event):
    check_token()
    code = event.pattern_match.group(1)
    await check_changes(event.peer_id.user_id)
    status = get_status_package(code)
    text = f"El paquete **{str.upper(code)}** se encuentra **{status['timeline']}**\n\n✅"
    list = status['datos']
    for i, item in enumerate(list):
        text += f"**🟦️ {len(list) - i}**" + datos_string.format(item['oficina_origen'],
                                                                 item['oficina_destino'],
                                                                 item['estado'], item['fecha'])
    await event.respond(text)


def get_status_package(codigo: str):
    data = {
        'codigo': codigo,
        'anno': str(datetime.now().year),
        'token': token,
        'user': ''
    }
    r = requests.post("https://www.correos.cu/wp-json/correos-api/enviosweb/", data=data)
    return r.json()


async def check_status():
    while True:
        check_token()
        for user in db.get_users():
            await check_changes(user[0])
        await asyncio.sleep(HOURS*60*60)


async def check_changes(user: int):
    itemsInDb = db.get_items(user)
    for elementInDb in itemsInDb:
        status = get_status_package(elementInDb.id)
        last = status['datos'][0]
        if elementInDb.status != last['estado']:
            message = f"‼️‼️NUEVO ESTADO PARA EL PAQUETE **{elementInDb.id}** ({status['timeline']}) \n" + \
                      datos_string.format(last['oficina_origen'],
                                          last['oficina_destino'],
                                          last['estado'], last['fecha'])
            await bot.send_message(user, message)
            db.update(elementInDb.id, last['estado'])
    print('checkeado')
    return itemsInDb


def check_token():
    global token
    page = requests.get('https://www.correos.cu/rastreador-de-envios/').text
    token = re.search('<input type="hidden" id="side" value="(\w+)">', page).group(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_status())
    loop.run_forever()
