# -*- coding: utf-8 -*-
'''
Este modulo define los objetos que seran guardados en la base de datos.

Utiliza el paquete *peewee* para el mapeo objeto-relacional. Permite realizar
las consultas a la base de datos en lenguaje python de forma sencilla sin
necesidad de escribir codigo SQL.
'''
import peewee as models
from . import config

# Identificador de grupo para servicios que esten en la red local
INSIDE = 'i'
# Identificador de grupo para servicios que esten en Internet
OUTSIDE = 'o'

# Declaro parametros de conexion de la base de datos
db = models.PostgresqlDatabase(config.BD_DATABASE,
                               host=config.BD_HOST,
                               user=config.BD_USER,
                               password=config.BD_PASSWORD)

class Flag:
    '''
    Declara flags que utiliza iptables.
    '''
    IP_ORIGEN = '--source'
    IP_DESTINO = '--destination'
    PUERTO_ORIGEN = '--source-port'
    PUERTO_DESTINO = '--destination-port'
    MAC_ORIGEN = '--mac-source'
    EXTENSION_MAC = '-m mac'
    EXTENSION_MULTIPORT = '-m multiport'
    PROTOCOLO = '--protocol'


class Param:
    '''
    Declara los parametros para generar las reglas de iptables.
    '''
    IP_ORIGEN = 'ip_origen'
    IP_DESTINO = 'ip_destino'
    UDP_ORIGEN = 'udp_origen'
    UDP_DESTINO = 'udp_destino'
    TCP_ORIGEN = 'tcp_origen'
    TCP_DESTINO = 'tcp_destino'
    MAC = 'mac'


class Protocolo:
    '''
    Define los numeros de protocolo.
    '''
    TCP = 6
    UDP = 17


class ClaseTrafico(models.Model):
    '''
    Una clase de trafico almacena los patrones a reconocer en los paquetes
    capturados.
    '''
    # Identificador de clases de sistema
    SISTEMA = 0
    id_clase = models.PrimaryKeyField()
    nombre = models.CharField(max_length=32)
    descripcion = models.CharField(max_length=160, default="")
    tipo = models.SmallIntegerField(default=0)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return u"%d: %s" % (self.id_clase, self.nombre)

    class Meta:
        database = db
        db_table = u'clase_trafico'


class CIDR(models.Model):
    '''
    El CIDR representa una subred. Se compone de una dirección de red y una
    máscara de subred representada con un prefijo que indica la cantidad de
    bits que contiene la máscara.

    Por ejemplo la subred 10.200.0.0 con máscara de subred 255.255.0.0 se
    representa como 10.200.0.0/16 siendo el prefijo 16, porque la mascara
    contiene 16 bits en uno.

    Si todos los bits de la mascara de subred están en uno representan a una
    red de host y el prefijo es 32.
    '''
    id_cidr = models.PrimaryKeyField()
    direccion = models.CharField(max_length=32)
    prefijo = models.SmallIntegerField(default=0)

    def __str__(self):
        return u"%s/%d" % (self.direccion, self.prefijo)

    class Meta:
        database = db
        db_table = u'cidr'


class Puerto(models.Model):
    '''
    Un puerto identifica una aplicacion en un host. Sirve para mantener muchas
    conversaciones al mismo tiempo con distintas aplicaciones.

    Los puertos se componen de un numero de 2 bytes sin signo (rango entre 0 y
    65535) y un protocolo que puede ser 6 (TCP) o 17 (UDP).
    '''
    id_puerto = models.PrimaryKeyField()
    numero = models.IntegerField()
    protocolo = models.SmallIntegerField(default=0)

    def __str__(self):
        proto = ''
        if self.protocolo == Protocolo.TCP:
            proto = '/tcp'
        elif self.protocolo == Protocolo.UDP:
            proto = '/udp'
        return u'%d%s' % (self.numero, proto)

    class Meta:
        database = db
        db_table = u'puerto'


class ClaseCIDR(models.Model):
    '''
    Relaciona una clase de trafico con un CIDR.
    '''
    clase = models.ForeignKeyField(ClaseTrafico, related_name='redes',
                                   db_column='id_clase')
    cidr = models.ForeignKeyField(CIDR, related_name='clases',
                                  db_column='id_cidr')
    grupo = models.FixedCharField(max_length=1)

    def __str__(self):
        return u"clase=%d cidr=%d %s" % (self.clase.id_clase,
                                         self.cidr.id_cidr,
                                         self.grupo)

    class Meta:
        database = db
        db_table = u'clase_cidr'
        primary_key = models.CompositeKey('clase', 'cidr')


class ClasePuerto(models.Model):
    '''
    Relaciona una clase de trafico con un puerto.
    '''
    clase = models.ForeignKeyField(ClaseTrafico, related_name='puertos',
                                   db_column='id_clase')
    puerto = models.ForeignKeyField(Puerto, related_name='clases',
                                    db_column='id_puerto')
    grupo = models.FixedCharField(max_length=1)

    def __str__(self):
        return u"clase=%d puerto=%d %s" % (self.clase.id_clase,
                                           self.puerto.id_puerto,
                                           self.grupo)

    class Meta:
        database = db
        db_table = u'clase_puerto'
        primary_key = models.CompositeKey('clase', 'puerto')


class Politica(models.Model):
    '''
    Define una regla sobre el trafico creada por el usuario.
    '''
    id_politica = models.PrimaryKeyField()
    nombre = models.CharField(max_length=63)
    descripcion = models.CharField(max_length=255, null=True)
    activa = models.BooleanField(default=True)
    prioridad = models.SmallIntegerField(null=True)
    velocidad_maxima = models.IntegerField(null=True)

    def __init__(self, *args, **kwargs):
        '''
        Inicializa diccionario de parametros.
        '''
        self.parametros = {
            getattr(Param, attr): set()
            for attr in dir(Param) if not attr.startswith('__')
        }
        return super(Politica, self).__init__(*args, **kwargs)


    def flags(self):
        '''
        Devuelve una lista de diccionarios con los flags necesarios para
        configurar el iptables para que capture los hosts definidos en la
        política.
        '''
        lista = list()
        for objetivo in self.objetivos:
            objetivo.obtener_parametros(self.parametros)

        for flags in self.flags_mac():
            lista.append(flags)
        return lista

    def flags_mac(self):
        params = self.parametros
        if params[Param.MAC]:
            lista = list()
            for mac in params[Param.MAC]:
                flags = {Flag.MAC_ORIGEN: mac, Flag.EXTENSION_MAC: ''}
                for flag in self.flags_puerto():
                    flags.update(flag)
                lista.append(flags)
            return lista
        else:
            return self.flags_puerto()

    def flags_puerto(self):
        params = self.parametros
        if (params[Param.TCP_ORIGEN] or params[Param.TCP_DESTINO] or
                params[Param.UDP_ORIGEN] or params[Param.UDP_DESTINO]):
            lista = list()
            if params[Param.TCP_ORIGEN] or params[Param.TCP_DESTINO]:
                flags = {Flag.EXTENSION_MULTIPORT: '', Flag.PROTOCOLO: 'tcp'}
                if params[Param.TCP_ORIGEN]:
                    flags[Flag.PUERTO_ORIGEN] = ",".join(str(x) for x in params[Param.TCP_ORIGEN])
                if params[Param.TCP_DESTINO]:
                    flags[Flag.PUERTO_DESTINO] = ",".join(str(x) for x in params[Param.TCP_DESTINO])
                flags.update(self.flags_redes())
                lista.append(flags)
            if params[Param.UDP_ORIGEN] or params[Param.UDP_DESTINO]:
                flags = {Flag.EXTENSION_MULTIPORT: '', Flag.PROTOCOLO: 'udp'}
                if params[Param.UDP_ORIGEN]:
                    flags[Flag.PUERTO_ORIGEN] = ",".join(str(x) for x in params[Param.UDP_ORIGEN])
                if params[Param.UDP_DESTINO]:
                    flags[Flag.PUERTO_DESTINO] = ",".join(str(x) for x in params[Param.UDP_DESTINO])
                flags.update(self.flags_redes())
                lista.append(flags)
            return lista
        else:
            return [self.flags_redes()]

    def flags_redes(self):
        flags = dict()
        params = self.parametros
        if params[Param.IP_ORIGEN]:
            flags[Flag.IP_ORIGEN] = ",".join(params[Param.IP_ORIGEN])
        if params[Param.IP_DESTINO]:
            flags[Flag.IP_DESTINO] = ",".join(params[Param.IP_DESTINO])
        return flags

    @property
    def origenes(self):
        '''
        Devuelve una lista con todos los objetivos que definen los hosts de
        origen.
        '''
        return self.objetivos.select().where(Objetivo.tipo == Objetivo.ORIGEN)

    @property
    def destinos(self):
        '''
        Devuelve una lista con todos los objetivos que definen los hosts de
        destino.
        '''
        return self.objetivos.select().where(Objetivo.tipo == Objetivo.DESTINO)


    class Meta:
        database = db
        db_table = u'politica'


class Objetivo(models.Model):
    '''
    Especifica los objetivos a los que se les va a aplicar la politica.
    '''
    ORIGEN = 'o'
    DESTINO = 'd'

    id_objetivo = models.PrimaryKeyField()
    politica = models.ForeignKeyField(Politica, related_name='objetivos',
                                      db_column='id_politica')
    clase = models.ForeignKeyField(ClaseTrafico, related_name='objetivos',
                                   db_column='id_clase', null=True)
    tipo = models.CharField(max_length=1, default='d')
    direccion_fisica = models.CharField(null=True)

    def obtener_parametros(self, parametros):
        '''
        Completa el diccionario de parametros con los valores necesarios para
        que el iptables capture los hosts definidos en el objetivo.
        '''
        if self.direccion_fisica is not None:
            parametros[Param.MAC].add(self.direccion_fisica)
        if self.clase is not None:
            self.parametros_subredes(parametros)
            self.parametros_puertos(parametros)
        return parametros

    def parametros_subredes(self, parametros):
        '''
        Obtiene los valores de parametros para que coincida las subredes de la
        clase.
        '''
        if self.clase and self.clase.redes.count() > 0:
            param = (Param.IP_ORIGEN if self.tipo == Objetivo.ORIGEN else
                     Param.IP_DESTINO)
            for item in self.clase.redes:
                parametros[param].add(str(item.cidr))

    def parametros_puertos(self, parametros):
        '''
        Obtiene los flags para que coincida los puertos de la clase.
        '''
        if self.clase and self.clase.puertos.count() > 0:
            for item in self.clase.puertos:
                for proto in (Protocolo.TCP, Protocolo.UDP):
                    param = self.definir_parametro_puerto(proto, item.puerto)
                    if param:
                        parametros[param].add(item.puerto.numero)

    def definir_parametro_puerto(self, protocolo, puerto):
        '''
        Defino el parametro que se va cargar segun si el objetivo es origen o
        destino y el protocolo del puerto.
        '''
        if protocolo == Protocolo.TCP:
            if puerto.protocolo in (0, Protocolo.TCP):
                if self.tipo == Objetivo.ORIGEN:
                    return Param.TCP_ORIGEN
                else:
                    return Param.TCP_DESTINO
        elif protocolo == Protocolo.UDP:
            if puerto.protocolo in (0, Protocolo.UDP):
                if self.tipo == Objetivo.ORIGEN:
                    return Param.UDP_ORIGEN
                else:
                    return Param.UDP_DESTINO


    class Meta:
        database = db
        db_table = u'objetivo'


class RangoHorario(models.Model):
    '''
    Especifica los rangos horarios en los que la politica esta activa.

    Atributos
    ----------
        * dia: Dia de la semana, entre 0 y 6 siendo 0 el dia domingo y 6 sabado
        * hora_inicial: Hora de inicio del rango valido
        * hora_fin: Hora de fin del rango valido
    '''
    id_rango_horario = models.PrimaryKeyField()
    politica = models.ForeignKeyField(Politica, related_name='horarios',
                                      db_column='id_politica')
    dia = models.SmallIntegerField()
    hora_inicial = models.TimeField()
    hora_fin = models.TimeField()


    class Meta:
        database = db
        db_table = u'rango_horario'
