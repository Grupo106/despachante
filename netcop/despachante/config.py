# -*- coding: utf-8 -*-
'''
Lee archivo de configuracion en formato INI ubicado en
'/etc/netcop/netcop.conf'

El formato del archivo esperado es

```ini
    [netcop]
    outside=eth0
    inside=eth1
    
    [database]
    host=
    database=netcop
    user=netcop
    password=netcop
```
'''
import configparser

NETCOP_CONFIG = '/etc/netcop/netcop.conf'

# Parametros de conexion de la base de datos por defecto
DEFAULT_BD_HOST = 'localhost'
DEFAULT_BD_DATABASE = 'postgres'
DEFAULT_BD_USER = 'postgres'
DEFAULT_BD_PASSWORD = 'postgres'

global BD_HOST, BD_DATABASE, BD_USER, BD_PASSWORD

config = configparser.ConfigParser()
config.read(NETCOP_CONFIG)

if config.has_section('database'):
    BD_HOST = config['database'].get('host', DEFAULT_BD_HOST)
    BD_DATABASE = config['database'].get('database', DEFAULT_BD_DATABASE)
    BD_USER = config['database'].get('user', DEFAULT_BD_USER)
    BD_PASSWORD = config['database'].get('password', DEFAULT_BD_PASSWORD)
else:
    BD_HOST = DEFAULT_BD_HOST
    BD_DATABASE = DEFAULT_BD_DATABASE
    BD_USER = DEFAULT_BD_USER
    BD_PASSWORD = DEFAULT_BD_PASSWORD
