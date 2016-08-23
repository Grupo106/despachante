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

# Parametros por defecto
class Default:
    DATABASE = {
        'host': 'localhost',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres',
    }
    NETCOP = {
        'local_version': '/tmp/actualizador',
        'url_version': 'http://netcop.ftp.sh/version',
        'url_download': 'http://netcop.ftp.sh/descarga',
        'outside': 'eth0',
        'inside': 'eth1',
    }

config = configparser.ConfigParser()
config.read(NETCOP_CONFIG)

# guarda el resto de las configuraciones del modulo
for section in config.sections():
    conf = dict()
    for item in config.items(section):
        conf[item[0].lower()] = item[1]
    globals()[section.upper()] = conf

# establece opciones por default
sections = [a for a in dir(Default) if not a.startswith('__')]
for section in sections:
    if globals().get(section) is None:
        globals()[section] = getattr(Default, section)

del config, sections
