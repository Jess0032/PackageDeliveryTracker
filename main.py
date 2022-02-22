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
    text = """Bienvenido al bot Rastreador de paquetes, para empezar a rastrear un paquete envie:
**/add CODIGOPAQUETE** -Esto comprobará el estado de su paquete cada cierto tiempo y le notificará cuando este cambie. 
**/del CODIGOPAQUETE** -Para dejar de rastrear un paquete.  
**/codes** -Para conocer los paquetes que está rastreando actualmente.
**/status CODIGOPAQUETE** -Para conocer el estado del paquete en el momento actual. 
    
**BOT NO OFICIAL**"""
    await event.respond(text)


@bot.on(NewMessage(pattern='\/add\s+(\w+)'))
async def add_elements(event):
    code = str.upper(event.pattern_match.group(1))
    status = get_status_package(code)
    text = f"El paquete **{str.upper(code)}** se encuentra **{status['timeline']}**\n\n✅"
    list = status['datos']
    for i, item in enumerate(list):
        text += f"**🟦️ {len(list) - i}**" + datos_string.format(item['oficina_origen'],
                                                                 item['oficina_destino'],
                                                                 item['estado'], item['fecha'])

    await event.respond(db.add(str.upper(code), str(event.peer_id.user_id), status['datos'][0]['estado'] if status['datos'] else ''))
    await event.respond(text)


@bot.on(NewMessage(pattern='\/del\s+(\w+)'))
async def del_elements(event):
    code = str.upper(event.pattern_match.group(1))
    await event.respond(db.delete(str(event.peer_id.user_id), code))


@bot.on(NewMessage(pattern='\/codes'))
async def get_elements(event):
    check_token()
    text = ''
    for package in db.get_packages_from_user(str(event.peer_id.user_id)):
        await check_changes(package)
        text+=f'code: **{package[0]}** status: **{package[1]}**\n'
    if not text:
        text = 'Usted no está rastreando ningún código aún.'
    await event.respond(text)



@bot.on(NewMessage(pattern='\/status\s+(\w+)'))
async def status(event):
    check_token()
    for package in db.get_packages_from_user(str(event.peer_id.user_id)):
        await check_changes(package)
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
        for package in db.get_packages():
            await check_changes(package)
        await asyncio.sleep(HOURS*60*60)


async def check_changes(package):
    status = get_status_package(package[0])

    if status['datos']:
        last = status['datos'][0]
        if package[1] != last['estado']:
            message = f"‼️‼️NUEVO ESTADO PARA EL PAQUETE **{package[0]}** ({status['timeline']}) \n" + \
                        datos_string.format(last['oficina_origen'],
                                            last['oficina_destino'],
                                            last['estado'], last['fecha'])

            for user in db.get_users_from_packages(package[0]):
                await bot.send_message(int(user), message)

            if status['timeline'] == "ENTREGADO":
                db.delete_package(package[0])
            else:
                db.update(package[0], last['estado'])
    print('checkeado')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_status())
    loop.run_forever()
