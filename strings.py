welcome_string = """Bienvenido al bot Rastreador de paquetes, para empezar a rastrear un paquete envie:

**/add CODIGOPAQUETE** -Esto comprobará el estado de su paquete cada cierto tiempo y le notificará cuando este cambie.
 
**/del CODIGOPAQUETE** -Para dejar de rastrear un paquete.

**/codes** -Para conocer los paquetes que está rastreando actualmente.

**/status CODIGOPAQUETE** -Para conocer el estado del paquete en el momento actual. 

**BOT NO OFICIAL**"""

string_data1 = "El paquete **{code}** de orígen **{country}** se encuentra en el estado **{timeline}**\n\n✅"

string_data2: str = """
OFICINA_ORIGEN : **{}**
OFICINA_DESTINO : **{}**
ESTADO : **{}**
FECHA : **{}**

"""
no_data = "El código no se ha encontrado en este momento. Es posible que aún no esté en el sistema o que sea inválido. "

new_state = "‼️‼️NUEVO ESTADO PARA EL PAQUETE **{package}** ({timeline}) \n"

view_all_timeline = "Para ver la línea de tiempo entera de este paquete envie **/status {package}**"

not_argumnts = "Por favor escriba el código seguido del comando.\n**Ejemplo:** **/{command} H0470245**"

not_codes = "Usted no está rastreando ningún código aún."

alredy_exist = "Este código ya se está rastreando."

success_add = "Inserción exitosa. Cuando exista un cambio en el estado del paquete le notificaremos. Estado actual a " \
          "continuación. "

dont_exist = "Usted no esta rastreando ese paquete"

success_del = "Eliminado exitoso. Este paquete se dejará de rastrear"

max_exceeded = "Número máximo de paquetes rastreados por un usuario excedido"
