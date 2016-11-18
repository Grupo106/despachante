# -*- coding: utf-8 -*-
'''
Este modulo define los objetos que seran guardados en la base de datos.

Utiliza el paquete *peewee* para el mapeo objeto-relacional. Permite realizar
las consultas a la base de datos en lenguaje python de forma sencilla sin
necesidad de escribir codigo SQL.
'''
import itertools
import peewee as models
from datetime import datetime
from . import config

# Identificador de grupo para servicios que esten en la red local
INSIDE = 'i'
# Identificador de grupo para servicios que esten en Internet
OUTSIDE = 'o'

# Declaro parametros de conexion de la base de datos
db = models.PostgresqlDatabase(config.DATABASE['database'],
                               host=config.DATABASE['host'],
                               user=config.DATABASE['user'],
                               password=config.DATABASE['password'])


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
    PROTOCOLO = '-p'
    PRIORIDAD = (EXTENSION_MAC,
                 PROTOCOLO,
                 MAC_ORIGEN,
                 IP_ORIGEN,
                 IP_DESTINO,
                 PUERTO_ORIGEN,
                 PUERTO_DESTINO)


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
    PRIO_ALTA = 1
    PRIO_NORMAL = 3
    PRIO_BAJA = 7
    id_politica = models.PrimaryKeyField()
    nombre = models.CharField(max_length=63)
    descripcion = models.CharField(max_length=255, null=True)
    activa = models.BooleanField(default=True)
    prioridad = models.SmallIntegerField(null=True)
    velocidad_subida = models.IntegerField(null=True)
    velocidad_bajada = models.IntegerField(null=True)

    def __init__(self, *args, **kwargs):
        '''
        Inicializa diccionario de parametros.
        '''
        self.parametros = {
            getattr(Param, attr): set()
            for attr in dir(Param) if not attr.startswith('__')
        }
        return super(Politica, self).__init__(*args, **kwargs)

    def flags_dict(self):
        '''
        Devuelve una lista de diccionarios con los flags necesarios para
        configurar el iptables para que capture los hosts definidos en la
        política.
        '''
        for objetivo in self.objetivos:
            objetivo.obtener_parametros(self)

        return self.flags_bajada(
            self.flags_mac(
                self.flags_puerto(
                    self.flags_redes([])
                )
            )
        )

    def flags(self):
        '''
        Devuelve una lista de string con los flags necesarios para
        configurar el iptables para que capture los hosts definidos en la
        política.
        '''
        lista = list()
        for flags in self.flags_dict():
            linea = list()
            for key in Flag.PRIORIDAD:
                value = flags.get(key)
                if value is not None:
                    linea.append("%s %s" % (key, value))
            lista.append(" ".join(linea))
        return lista

    def flags_mac(self, lista):
        '''
        Devuelve los flags para que capture las mac-address definidas en los
        objetivos de la politica.
        '''
        if not self.hay_macs():
            return lista
        flags = [{Flag.MAC_ORIGEN: mac, Flag.EXTENSION_MAC: ''}
                 for mac in self.parametros[Param.MAC]]
        return self.producto_cartesiano(lista, flags)

    def flags_puerto(self, lista):
        '''
        Devuelve los flags para que capture los puertos definidos en los
        objetivos de la politica.
        '''
        if not self.hay_puertos():
            return lista
        PUERTOS = (
            ('tcp', Param.TCP_ORIGEN, Param.TCP_DESTINO),
            ('udp', Param.UDP_ORIGEN, Param.UDP_DESTINO),
        )
        ret = list()
        for proto, origen, destino in PUERTOS:
            if not self.parametros[destino]:
                for sport in self.parametros[origen]:
                    ret.append({
                        Flag.PROTOCOLO: proto,
                        Flag.PUERTO_ORIGEN: sport,
                    })
            elif not self.parametros[origen]:
                for dport in self.parametros[destino]:
                    ret.append({
                        Flag.PROTOCOLO: proto,
                        Flag.PUERTO_DESTINO: dport,
                    })
            else:
                for sport, dport in itertools.product(
                        self.parametros[origen],
                        self.parametros[destino]):
                    ret.append({
                        Flag.PROTOCOLO: proto,
                        Flag.PUERTO_ORIGEN: sport,
                        Flag.PUERTO_DESTINO: dport,
                    })
        return self.producto_cartesiano(lista, ret)

    def flags_redes(self, lista):
        '''
        Devuelve los flags para que capture las redes definidas en los
        objetivos de la politica.
        '''
        if not self.hay_redes():
            return lista
        flags = dict()
        if self.parametros[Param.IP_ORIGEN]:
            flags[Flag.IP_ORIGEN] = ",".join(
                self.parametros[Param.IP_ORIGEN]
            )
        if self.parametros[Param.IP_DESTINO]:
            flags[Flag.IP_DESTINO] = ",".join(
                self.parametros[Param.IP_DESTINO]
            )
        return self.producto_cartesiano(lista, [flags])

    def flags_bajada(self, lista):
        '''
        Como las reglas del trafico de bajada se aplican en la interfaz inside,
        se tienen que aplicar las reglas al reves, es decir los objetivos
        origen se transforman en destino y los destino se transforman en
        origen.
        '''
        if not self.velocidad_bajada and not self.prioridad:
            return lista
        pares = ((Flag.IP_ORIGEN, Flag.IP_DESTINO),
                 (Flag.PUERTO_ORIGEN, Flag.PUERTO_DESTINO),)
        ret = list(lista)
        for item in lista:
            # hago una copia de los flags eliminando los valores de los pares
            modificado = False
            nuevo = self.__item_bajada(item)
            # intercambio de pares
            for origen, destino in pares:
                if origen in item:
                    modificado = nuevo[destino] = item[origen]
                if destino in item:
                    modificado = nuevo[origen] = item[destino]
            # agrego nuevo item a la lista de flags
            if modificado:
                ret.append(nuevo)
        return ret

    def __item_bajada(self, item):
        '''
        Copia un diccionario de flags, eliminando keys no deseadas para aplicar
        los flags de bajada.
        '''
        indeseables = (Flag.IP_ORIGEN, Flag.IP_DESTINO, Flag.PUERTO_ORIGEN,
                       Flag.PUERTO_DESTINO)
        nuevo = item.copy()
        for key in indeseables:
            nuevo.pop(key, None)
        return nuevo

    def hay_puertos(self):
        '''
        Devuelve verdadero cuando se definan puertos TCP o UDP en la politica
        tanto como origen o como destino.
        '''
        return (self.parametros[Param.TCP_ORIGEN] or
                self.parametros[Param.TCP_DESTINO] or
                self.parametros[Param.UDP_ORIGEN] or
                self.parametros[Param.UDP_DESTINO])

    def hay_macs(self):
        '''
        Devuelve verdadero si se definen mac address en la politica.
        '''
        return self.parametros[Param.MAC]

    def hay_redes(self):
        '''
        Devuelve verdadero si se definen redes en la politica.
        '''
        return (self.parametros[Param.IP_ORIGEN] or
                self.parametros[Param.IP_DESTINO])

    def producto_cartesiano(self, lista1, lista2):
        '''
        Realiza el producto cartesiano entre dos listas de diccionarios.
        '''
        if not lista1:
            return lista2
        elif not lista2:
            return lista1
        else:
            lista = list()
            for flags1, flags2 in itertools.product(lista1, lista2):
                lista.append(dict(flags1, **flags2))
            return lista

    def esta_activa(self, fecha=None):
        '''
        Devuelve verdadero si la politica esta activa en la fecha pasada por
        parametro.

        Si no se pasa ninguna fecha por parametro, utiliza la fecha actual.
        '''
        if not self.activa:
            return False
        # si no tiene restriccion de horarios, esta activa
        if self.horarios.count() == 0:
            return True
        fecha = fecha or datetime.now()
        # Si existe algun rango activo
        for horario in self.horarios:
            if fecha in horario:
                return True
        return False

    def __eq__(self, item):
        '''
        Devuelve verdadero si dos politicas son iguales.
        '''
        return self.id_politica == item.id_politica

    def __hash__(self):
        '''
        Devuelve verdadero si dos politicas son iguales.
        '''
        return hash(self.id_politica)

    def __str__(self):
        return self.nombre.encode('utf-8')

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

    def obtener_parametros(self, politica):
        '''
        Completa el diccionario de parametros con los valores necesarios para
        que el iptables capture los hosts definidos en el objetivo.
        '''
        if self.direccion_fisica is not None:
            politica.parametros[Param.MAC].add(self.direccion_fisica)
        if self.clase is not None:
            self.parametros_subredes(politica)
            self.parametros_puertos(politica)
        return politica.parametros

    def parametros_subredes(self, politica):
        '''
        Obtiene los valores de parametros para que coincida las subredes de la
        clase.
        '''
        if self.clase and self.clase.redes.count() > 0:
            param = (Param.IP_ORIGEN if self.tipo == Objetivo.ORIGEN else
                     Param.IP_DESTINO)
            for item in self.clase.redes:
                politica.parametros[param].add(str(item.cidr))

    def parametros_puertos(self, politica):
        '''
        Obtiene los flags para que coincida los puertos de la clase.
        '''
        if self.clase and self.clase.puertos.count() > 0:
            for item in self.clase.puertos:
                for proto in (Protocolo.TCP, Protocolo.UDP):
                    param = self.definir_parametro_puerto(proto, item.puerto,
                                                          politica)
                    if param:
                        politica.parametros[param].add(item.puerto.numero)

    def definir_parametro_puerto(self, protocolo, puerto, politica):
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

    def __contains__(self, item):
        '''
        Devuelve verdadero si la fecha-hora (item) esta dentro del rango.
        '''
        return (item.weekday() == self.dia and
                self.hora_inicial <= item.time() < self.hora_fin)

    class Meta:
        database = db
        db_table = u'rango_horario'
