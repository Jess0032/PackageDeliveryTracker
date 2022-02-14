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

@bot.on(NewMessage(pattern='/start'))
async def add_elements(event):
    text = """Bienvenido al bot Rastreador de paquetes, para empezar a rastrear un paquete envie **/add 
    CODIGOPAQUETE** esto comprobará el estado de su paquete cada cierto tiempo y le notificará cuando este cambie. 
    Para dejar de rastrear un paquete envie **/del CODIGOPAQUETE**. Para conocer los códigos que está rastreando 
    envie **/codes** Para conocer el estado del paquete en el momento actual envie **/status CODIGOPAQUETE** 
    
    BOT NO OFICIAL"""
    await event.respond(text)

@bot.on(NewMessage(pattern='\/add (.+)'))
async def add_elements(event):
    code = str.upper(event.pattern_match.group(1))
    await event.respond(db.add(str.upper(code), '', event.peer_id.user_id))


@bot.on(NewMessage(pattern='\/del (.+)'))
async def del_elements(event):
    code = str.upper(event.pattern_match.group(1))
    await event.respond(db.delete(event.peer_id.user_id, code))


@bot.on(NewMessage(pattern='\/codes'))
async def get_elements(event):
    check_token()
    await check_changes(event.peer_id.user_id)
    codes = db.get_items(event.peer_id.user_id)
    for element in codes:
        await event.respond(f'code: **{element.id}** status: **{element.status}**')


@bot.on(NewMessage(pattern='\/status (.+)'))
async def status(event):
    check_token()
    await check_changes(event.peer_id.user_id)
    code = event.pattern_match.group(1)
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


def check_token():
    global token
    page = requests.get('https://www.correos.cu/rastreador-de-envios/').text
    token = re.search('<input type="hidden" id="side" value="(\w+)">', page).group(1)


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
        if status['datos']:
            last = status['datos'][0]
            if elementInDb.status != last['estado']:
                message = f"‼️‼️NUEVO ESTADO PARA EL PAQUETE **{elementInDb.id}** ({status['timeline']}) \n" + \
                        datos_string.format(last['oficina_origen'],
                                            last['oficina_destino'],
                                            last['estado'], last['fecha'])
                await bot.send_message(user, message)
                if last['estado'] == "ENTREGADO":
                    db.delete(user, elementInDb.id)
                else:
                    db.update(elementInDb.id, last['estado'])
    print('checkeado')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_status())
    loop.run_forever()
