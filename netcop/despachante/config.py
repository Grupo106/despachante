# -*- coding: utf-8 -*-
'''
Lee archivo de configuracion en formato INI ubicado en
'/etc/netcop/netcop.config'

El formato del archivo esperado es

```ini
    [netcop]
    outside=eth0
    inside=eth1
    url_version=http://netcop.com/version
    url_download=http://netcop.com/download
    local_version=/var/local/netcop/version
    
    [database]
    host=
    database=netcop
    user=netcop
    password=netcop
```
'''
import configparser

NETCOP_CONFIG = '/etc/netcop/netcop.config'

# Parametros de conexion de la base de datos por defecto
class Default:
    BD_HOST = 'localhost'
    BD_DATABASE = 'postgres'
    BD_USER = 'postgres'
    BD_PASSWORD = 'postgres'

global BD_HOST, BD_DATABASE, BD_USER, BD_PASSWORD

config = configparser.ConfigParser()
config.read(NETCOP_CONFIG)

# guarda el resto de las configuraciones del modulo
for section in config.sections():
    conf = dict()
    for item in config.items(section):
        conf[item[0].lower()] = item[1]
    globals()[section] = conf

# establece opciones por default
if globals().get('DATABASE') is None:
    database = globals()['DATABASE'] = dict()
    database['host'] = Default.BD_HOST
    database['database'] = Default.BD_DATABASE
    database['user'] = Default.BD_USER
    database['password'] = Default.BD_PASSWORD
