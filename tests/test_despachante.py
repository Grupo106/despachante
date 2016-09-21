# -*- coding: utf-8 -*-
'''
Pruebas del despachante de clases de trafico.
'''
import unittest
import mock
import jinja2
from datetime import datetime, timedelta
from mock import Mock

from netcop.despachante import models, Despachante, config
from netcop.despachante.models import Flag, Param
from jinja2 import Environment, PackageLoader


class DespachanteTests(unittest.TestCase):
    def setUp(self):
        models.db.create_tables(
            [
                models.ClaseTrafico,
                models.CIDR,
                models.Puerto,
                models.ClaseCIDR,
                models.ClasePuerto,
                models.Politica,
                models.Objetivo,
                models.RangoHorario,
            ],
            safe=True)

    def test_flags_objetivo_mac(self):
        '''
        Prueba obtener los flags de un objetivo que defina una mac address.

        Solamente se pueden especificar mac-address como origen de la regla.
        '''
        # preparo datos
        objetivo = models.Objetivo(
            direccion_fisica='00:00:00:00:00:01',
            tipo=models.Objetivo.ORIGEN
        )
        p = models.Politica()
        # llamo metodo a probar
        objetivo.obtener_parametros(p)
        # verifico que todo este bien
        assert '00:00:00:00:00:01' in p.parametros[Param.MAC]
        # preparo datos, debe ignorar que se especifico como destino
        objetivo = models.Objetivo(
            direccion_fisica='00:00:00:00:00:02',
            tipo=models.Objetivo.DESTINO
        )
        # llamo metodo a probar
        objetivo.obtener_parametros(p)
        # verifico que todo este bien
        assert '00:00:00:00:00:02' in p.parametros[Param.MAC]

    def test_flags_objetivo_redes(self):
        '''
        Prueba obtener los flags de un objetivo que defina una clase de trafico
        que define redes.
        '''
        # creo transaccion para descartar cambios generados en la base
        with models.db.atomic() as transaction:
            # preparo datos
            clase = models.ClaseTrafico.create(
                id_clase=60606060,
                nombre='foo',
                descripcion='bar',
            )
            cidr = [
                models.CIDR.create(
                    direccion='192.168.1.0',
                    prefijo=24,
                ),
                models.CIDR.create(
                    direccion='192.168.2.0',
                    prefijo=24,
                )
            ]
            for red in cidr:
                models.ClaseCIDR.create(clase=clase, cidr=red,
                                        grupo=models.OUTSIDE)
            p = models.Politica()

            # creo objetivo como origen
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.ORIGEN
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p.parametros[Param.IP_ORIGEN]
            assert '192.168.2.0/24' in p.parametros[Param.IP_ORIGEN]

            # creo objetivo como destino
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.DESTINO
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p.parametros[Param.IP_DESTINO]
            assert '192.168.2.0/24' in p.parametros[Param.IP_DESTINO]

            transaction.rollback()

    def test_flags_objetivo_puertos(self):
        '''
        Prueba obtener los flags de un objetivo que defina una clase de trafico
        que define puertos
        '''
        # creo transaccion para descartar cambios generados en la base
        with models.db.atomic() as transaction:
            # preparo datos
            clase = models.ClaseTrafico.create(
                id_clase=60606060,
                nombre='foo',
                descripcion='bar',
            )
            puertos = [
                models.Puerto.create(
                    numero=53,
                    protocolo=17,
                ),
                models.Puerto.create(
                    numero=22,
                    protocolo=6,
                ),
                models.Puerto.create(
                    numero=80,
                    protocolo=0,
                )
            ]
            for item in puertos:
                models.ClasePuerto.create(clase=clase, puerto=item,
                                          grupo=models.OUTSIDE)

            p = models.Politica()

            # creo objetivo como origen
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.ORIGEN
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert 53 in p.parametros[Param.UDP_ORIGEN]
            assert 22 in p.parametros[Param.TCP_ORIGEN]
            assert 80 in p.parametros[Param.UDP_ORIGEN]
            assert 80 in p.parametros[Param.TCP_ORIGEN]

            # creo objetivo como destino
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.DESTINO
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert 53 in p.parametros[Param.UDP_DESTINO]
            assert 22 in p.parametros[Param.TCP_DESTINO]
            assert 80 in p.parametros[Param.UDP_DESTINO]
            assert 80 in p.parametros[Param.TCP_DESTINO]

            transaction.rollback()

    def test_flags_objetivo_redes_puertos(self):
        '''
        Prueba obtener los flags de un objetivo que defina una clase de trafico
        que define redes y puertos
        '''
        # creo transaccion para descartar cambios generados en la base
        with models.db.atomic() as transaction:
            # preparo datos
            clase = models.ClaseTrafico.create(
                id_clase=60606060,
                nombre='foo',
                descripcion='bar',
            )
            cidr = [
                models.CIDR.create(
                    direccion='192.168.1.0',
                    prefijo=24,
                ),
                models.CIDR.create(
                    direccion='192.168.2.0',
                    prefijo=24,
                )
            ]
            puertos = [
                models.Puerto.create(
                    numero=53,
                    protocolo=17,
                ),
                models.Puerto.create(
                    numero=22,
                    protocolo=6,
                )
            ]
            for item in cidr:
                models.ClaseCIDR.create(clase=clase, cidr=item,
                                        grupo=models.OUTSIDE)
            for item in puertos:
                models.ClasePuerto.create(clase=clase, puerto=item,
                                          grupo=models.OUTSIDE)

            p = models.Politica()

            # creo objetivo como origen
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.ORIGEN
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p.parametros[Param.IP_ORIGEN]
            assert '192.168.2.0/24' in p.parametros[Param.IP_ORIGEN]
            assert 53 in p.parametros[Param.UDP_ORIGEN]
            assert 22 in p.parametros[Param.TCP_ORIGEN]

            # creo objetivo como destino
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.DESTINO
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p.parametros[Param.IP_DESTINO]
            assert '192.168.2.0/24' in p.parametros[Param.IP_DESTINO]
            assert 53 in p.parametros[Param.UDP_DESTINO]
            assert 22 in p.parametros[Param.TCP_DESTINO]

            transaction.rollback()

    def test_flags_politica_restriccion_destino(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como destino.
        '''
        # preparo datos
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.parametros.update({
            Param.IP_DESTINO: ['192.168.0.0/24', '192.168.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.parametros.update({
            Param.TCP_DESTINO: [22],
            Param.UDP_DESTINO: [53]
        })
        # Pruebo solo objetivo ip
        politica = models.Politica()
        politica.objetivos = [objetivo_ip]
        flags = politica.flags_dict()
        assert len(flags) == 1
        for item in flags:
            assert '192.168.0.0/24' in item[Flag.IP_DESTINO]
            assert '192.168.1.0/24' in item[Flag.IP_DESTINO]
            assert Flag.PROTOCOLO not in item
            assert Flag.PUERTO_ORIGEN not in item
            assert Flag.PUERTO_DESTINO not in item
        # Pruebo solo objetivo puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 2
        for item in flags:
            assert Flag.IP_DESTINO not in item
            assert Flag.IP_ORIGEN not in item
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_DESTINO]
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_DESTINO]
        # Pruebo objetivo ip y puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_ip, objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 2
        for item in flags:
            assert '192.168.0.0/24' in item[Flag.IP_DESTINO]
            assert '192.168.1.0/24' in item[Flag.IP_DESTINO]
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_DESTINO]
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_DESTINO]

    def test_flags_politica_restriccion_origen(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como origen.
        '''
        # preparo datos
        objetivo_mac = Mock()
        objetivo_mac.obtener_parametros = lambda x: x.parametros.update({
            Param.MAC: ['10:00:00:00:00:00', '20:00:00:00:00:00']
        })
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.parametros.update({
            Param.IP_ORIGEN: ['192.168.0.0/24', '192.168.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.parametros.update({
            Param.TCP_ORIGEN: [22],
            Param.UDP_ORIGEN: [53]
        })
        # Pruebo solo objetivo mac
        politica = models.Politica()
        politica.objetivos = [objetivo_mac]
        flags = politica.flags_dict()
        assert len(flags) == 2
        for item in flags:
            if '10:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '20:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            elif '20:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '10:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            else:
                assert False
            assert Flag.IP_ORIGEN not in item
            assert Flag.IP_DESTINO not in item
            assert Flag.PROTOCOLO not in item
            assert Flag.PUERTO_ORIGEN not in item
            assert Flag.PUERTO_DESTINO not in item
        # Pruebo solo objetivo ip
        politica = models.Politica()
        politica.objetivos = [objetivo_ip]
        flags = politica.flags_dict()
        assert len(flags) == 1
        for item in flags:
            assert '192.168.0.0/24' in item[Flag.IP_ORIGEN]
            assert '192.168.1.0/24' in item[Flag.IP_ORIGEN]
            assert Flag.PROTOCOLO not in item
            assert Flag.PUERTO_ORIGEN not in item
            assert Flag.PUERTO_DESTINO not in item
        # Pruebo solo objetivo puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 2
        for item in flags:
            assert Flag.IP_ORIGEN not in item
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_ORIGEN]
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_ORIGEN]
        # Pruebo objetivo ip y puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_ip, objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 2
        for item in flags:
            assert '192.168.0.0/24' in item[Flag.IP_ORIGEN]
            assert '192.168.1.0/24' in item[Flag.IP_ORIGEN]
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_ORIGEN]
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_ORIGEN]
        # Pruebo objetivo mac, ip y puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_mac, objetivo_ip, objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 4
        for item in flags:
            if '10:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '20:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            elif '20:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '10:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            else:
                assert False
            assert '192.168.0.0/24' in item[Flag.IP_ORIGEN]
            assert '192.168.1.0/24' in item[Flag.IP_ORIGEN]
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_ORIGEN]
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_ORIGEN]

    def test_flags_politica_restriccion_origen_destino(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como origen y destino.
        '''
        # preparo datos
        objetivo_mac = Mock()
        objetivo_mac.obtener_parametros = lambda x: x.parametros.update({
            Param.MAC: ['10:00:00:00:00:00', '20:00:00:00:00:00']
        })
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.parametros.update({
            Param.IP_ORIGEN: ['192.168.0.0/24', '192.168.1.0/24'],
            Param.IP_DESTINO: ['172.16.0.0/24', '172.16.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.parametros.update({
            Param.TCP_ORIGEN: [22],
            Param.UDP_ORIGEN: [53],
            Param.TCP_DESTINO: [80, 443],
            Param.UDP_DESTINO: [137],
        })
        # Pruebo solo objetivo ip y mac
        politica = models.Politica()
        politica.objetivos = [objetivo_ip, objetivo_mac]
        flags = politica.flags_dict()
        assert len(flags) == 2
        for item in flags:
            assert '192.168.0.0/24' in item[Flag.IP_ORIGEN]
            assert '192.168.1.0/24' in item[Flag.IP_ORIGEN]
            assert '172.16.0.0/24' in item[Flag.IP_DESTINO]
            assert '172.16.1.0/24' in item[Flag.IP_DESTINO]
            if '10:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '20:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            elif '20:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '10:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            else:
                assert False
            assert Flag.EXTENSION_MAC in item
            assert Flag.PROTOCOLO not in item
            assert Flag.PUERTO_ORIGEN not in item
            assert Flag.PUERTO_DESTINO not in item
        # Pruebo solo objetivo puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 3
        for item in flags:
            assert Flag.IP_ORIGEN not in item
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_ORIGEN]
                assert item[Flag.PUERTO_DESTINO] in (80, 443)
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_ORIGEN]
                assert 137 == item[Flag.PUERTO_DESTINO]
        # Pruebo objetivo ip y puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_ip, objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 3
        for item in flags:
            assert '192.168.0.0/24' in item[Flag.IP_ORIGEN]
            assert '192.168.1.0/24' in item[Flag.IP_ORIGEN]
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_ORIGEN]
                assert item[Flag.PUERTO_DESTINO] in (80, 443)
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_ORIGEN]
                assert 137 == item[Flag.PUERTO_DESTINO]
        # Pruebo objetivo mac, ip y puerto
        politica = models.Politica()
        politica.objetivos = [objetivo_mac, objetivo_ip, objetivo_puerto]
        flags = politica.flags_dict()
        assert len(flags) == 6
        for item in flags:
            if '10:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '20:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            elif '20:00:00:00:00:00' in item[Flag.MAC_ORIGEN]:
                assert '10:00:00:00:00:00' not in item[Flag.MAC_ORIGEN]
            else:
                assert False
            assert '192.168.0.0/24' in item[Flag.IP_ORIGEN]
            assert '192.168.1.0/24' in item[Flag.IP_ORIGEN]
            if item[Flag.PROTOCOLO] == 'tcp':
                assert 22 == item[Flag.PUERTO_ORIGEN]
                assert item[Flag.PUERTO_DESTINO] in (80, 443)
            if item[Flag.PROTOCOLO] == 'udp':
                assert 53 == item[Flag.PUERTO_ORIGEN]
                assert 137 == item[Flag.PUERTO_DESTINO]

    def test_template_restriccion(self):
        '''
        Prueba la generacion del template de restriccion.
        '''
        # preparo datos
        objetivo_mac = Mock()
        objetivo_mac.obtener_parametros = lambda x: x.parametros.update({
            Param.MAC: ['10:00:00:00:00:00', '20:00:00:00:00:00']
        })
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.parametros.update({
            Param.IP_ORIGEN: ['192.168.0.0/24', '192.168.1.0/24'],
            Param.IP_DESTINO: ['172.16.0.0/24', '172.16.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.parametros.update({
            Param.TCP_ORIGEN: [22],
            Param.UDP_ORIGEN: [53],
            Param.TCP_DESTINO: [80, 443],
            Param.UDP_DESTINO: [137],
        })
        # Pruebo objetivo mac, ip y puerto
        politica1 = models.Politica(id_politica=61)
        politica1.objetivos = [objetivo_mac, objetivo_ip, objetivo_puerto]
        politica2 = models.Politica(id_politica=62,
                                    velocidad_bajada='1mbit')
        politica2.objetivos = [objetivo_mac, objetivo_ip, objetivo_puerto]
        politica3 = models.Politica(id_politica=63,
                                    velocidad_bajada='2048kbit',
                                    velocidad_subida='512kbit')
        politica3.objetivos = [objetivo_mac, objetivo_ip, objetivo_puerto]
        politica4 = models.Politica(id_politica=64,
                                    prioridad=1)
        politica4.objetivos = [objetivo_mac, objetivo_ip, objetivo_puerto]
        env = Environment(loader=PackageLoader('netcop.despachante'))
        template = env.get_template("main.jinja")
        script = template.render(politicas=[politica1, politica2, politica3,
                                            politica4],
                                 if_outside='eth0',
                                 if_inside='eth1')
        assert '1mbit' in script
        assert '2048kbit' in script
        assert '512kbit' in script
        assert 'REJECT' in script

    def test_flags_puerto_origen_tcp_bajada(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto origen TCP con velocidad maxima de bajada
        '''
        politica = models.Politica(velocidad_bajada=1024)
        politica.parametros[Param.TCP_ORIGEN] = set([80])
        flags = politica.flags_bajada(politica.flags_puerto([]))
        assert flags[0].get(Flag.PUERTO_ORIGEN) == 80
        assert flags[1].get(Flag.PUERTO_DESTINO) == 80

    def test_flags_puerto_origen_tcp_subida(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto origen TCP con velocidad maxima de subida
        '''
        politica = models.Politica(velocidad_subida=1024)
        politica.parametros[Param.TCP_ORIGEN] = set([443])
        flags = politica.flags_bajada(politica.flags_puerto([]))
        assert len(flags) == 1
        assert flags[0].get(Flag.PUERTO_ORIGEN) == 443
        assert not flags[0].get(Flag.PUERTO_DESTINO)

    def test_flags_puerto_destino_tcp_bajada(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto destino TCP con velocidad maxima de bajada
        '''
        politica = models.Politica(velocidad_bajada=1024)
        politica.parametros[Param.TCP_DESTINO] = set([80])
        flags = politica.flags_bajada(politica.flags_puerto([]))
        assert flags[0].get(Flag.PUERTO_DESTINO) == 80
        assert flags[1].get(Flag.PUERTO_ORIGEN) == 80

    def test_flags_puerto_destino_tcp_subida(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto destino TCP con velocidad maxima de subida
        '''
        politica = models.Politica(velocidad_subida=1024)
        politica.parametros[Param.TCP_ORIGEN] = set([443])
        flags = politica.flags_bajada(politica.flags_puerto([]))
        assert len(flags) == 1
        assert flags[0].get(Flag.PUERTO_ORIGEN) == 443
        assert not flags[0].get(Flag.PUERTO_DESTINO)

    def test_flags_puerto_destino_subida_bajada(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto destino TCP con velocidad maxima de bajada
        '''
        politica = models.Politica(velocidad_bajada=1024,
                                   velocidad_subida=512)
        politica.parametros[Param.TCP_DESTINO] = set([80])
        flags = politica.flags_bajada(politica.flags_puerto([]))
        assert len(flags) == 2
        assert flags[0].get(Flag.PUERTO_DESTINO) == 80
        assert flags[1].get(Flag.PUERTO_ORIGEN) == 80

    def test_parametro_puerto_destino_tcp_subida(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto destino TCP con velocidad maxima de subida
        '''
        politica = models.Politica(velocidad_subida=1024)
        politica.parametros[Param.TCP_ORIGEN] = set([443])
        flags = politica.flags_bajada(politica.flags_puerto([]))
        assert len(flags) == 1
        assert flags[0].get(Flag.PUERTO_ORIGEN) == 443
        assert not flags[0].get(Flag.PUERTO_DESTINO)

    def test_parametro_puerto_destino_tcp(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto destino TCP sin limitacion
        '''
        objetivo = models.Objetivo(tipo=models.Objetivo.DESTINO)
        politica = models.Politica()
        puerto = models.Puerto(protocolo=models.Protocolo.TCP, numero=443)
        parametro = objetivo.definir_parametro_puerto(
            protocolo=models.Protocolo.TCP,
            puerto=puerto,
            politica=politica)
        assert parametro == models.Param.TCP_DESTINO

    def test_parametro_puerto_origen_tcp(self):
        '''
        Prueba obtener el parametro del puerto a utilizar.

        Puerto origen TCP sin limitacion
        '''
        objetivo = models.Objetivo(tipo=models.Objetivo.ORIGEN)
        politica = models.Politica()
        puerto = models.Puerto(protocolo=models.Protocolo.TCP, numero=443)
        parametro = objetivo.definir_parametro_puerto(
            protocolo=models.Protocolo.TCP,
            puerto=puerto,
            politica=politica)
        assert parametro == models.Param.TCP_ORIGEN

    def test_template_limitacion_puerto(self):
        '''
        Prueba la generacion del template de limitacion de puertos.
        '''
        # preparo datos
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.parametros.update({
            Param.TCP_ORIGEN: [80, 443],
        })
        limitacion = models.Politica(id_politica=1063,
                                     velocidad_bajada='2048',
                                     velocidad_subida='512')
        limitacion.objetivos = [objetivo_puerto]
        template = (Environment(loader=PackageLoader('netcop.despachante'))
                    .get_template("main.jinja"))
        script = template.render(politicas=[limitacion],
                                 if_outside='eth0',
                                 if_inside='eth1')
        assert '2048kbit' in script
        assert '512kbit' in script
        assert 'MARK' in script
        assert models.Flag.PUERTO_ORIGEN + ' 80' in script
        assert models.Flag.PUERTO_ORIGEN + ' 443' in script
        assert models.Flag.PUERTO_DESTINO + ' 80' in script
        assert models.Flag.PUERTO_DESTINO + ' 443' in script

    @mock.patch('os.path.getmtime')
    def test_sin_ultimo_despacho(self, mock):
        '''
        Prueba obtener la fecha de ultimo despacho, sin despachos anteriores.
        Debe devolver None.
        '''
        despachante = Despachante()
        mock.side_effect = OSError()
        assert despachante.fecha_ultimo_despacho is None
        assert mock.called

    @mock.patch('os.path.getmtime')
    def test_ultimo_despacho(self, mock):
        '''
        Prueba obtener la fecha de ultimo despacho.
        '''
        despachante = Despachante()
        mock.return_value = 1471446575
        assert (despachante.fecha_ultimo_despacho.isoformat() ==
                '2016-08-17T15:09:35')
        assert mock.called

    @mock.patch('netcop.despachante.models.RangoHorario.select')
    def test_hay_reglas_temporales(self, mock_select):
        '''
        Prueba que devuelva verdadero cuando haya reglas que dependan del
        tiempo.
        '''
        # preparo los mocks
        despachante = Despachante()
        mock_exists = Mock()
        mock_select.return_value = Mock()
        mock_select.return_value.exists = mock_exists
        # pruebo en caso de que no existan reglas temporales
        mock_exists.return_value = False
        assert not despachante.hay_reglas_temporales()
        assert mock_exists.called
        # pruebo en caso de que si existan reglas temporales
        mock_exists.reset_mock()
        mock_exists.return_value = True
        assert despachante.hay_reglas_temporales()
        assert mock_exists.called

    def test_politicas_activas_actual(self):
        '''
        Obtiene lista de politicas activas en tiempo actual.

        politica1: Rango horario valido (debe mostrarse)
        politica2: Rango horario invalido (no debe mostrarse)
        politica3: Sin rango horario (debe mostrarse)
        '''
        with models.db.atomic() as transaction:
            despachante = Despachante()
            now = datetime.now()
            politica1 = models.Politica.create(nombre='politica1')
            politica2 = models.Politica.create(nombre='politica2')
            models.Politica.create(nombre='politica3')
            # politica1: rango no valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.weekday() + 1,
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=2)).time(),
            )
            # politica1: rango valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.weekday(),
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=1)).time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.weekday(),
                hora_inicial=(now + timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=2)).time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.weekday() + 1,
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=2)).time(),
            )
            politicas = despachante.obtener_politicas()
            assert [_ for _ in politicas if _.nombre == 'politica1']
            assert not [_ for _ in politicas if _.nombre == 'politica2']
            assert [_ for _ in politicas if _.nombre == 'politica3']
            transaction.rollback()

    def test_politicas_activas_especifico(self):
        '''
        Obtiene lista de politicas activas en un tiempo especifico.

        politica1: Rango horario valido (debe mostrarse)
        politica2: Rango horario invalido (no debe mostrarse)
        politica3: Sin rango horario (debe mostrarse)
        '''
        with models.db.atomic() as transaction:
            despachante = Despachante()
            now = datetime.now()
            politica1 = models.Politica.create(nombre='politica1')
            politica2 = models.Politica.create(nombre='politica2')
            models.Politica.create(nombre='politica3')
            # politica1: rango no valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.weekday(),
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=now.time(),
            )
            # politica1: rango valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.weekday(),
                hora_inicial=(now - timedelta(hours=2)).time(),
                hora_fin=now.time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.weekday(),
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=now.time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.weekday() + 1,
                hora_inicial=(now - timedelta(hours=2)).time(),
                hora_fin=now.time(),
            )
            # dos horas atras
            fecha = now - timedelta(hours=2)
            politicas = despachante.obtener_politicas(fecha)
            assert [_ for _ in politicas if _.nombre == 'politica1']
            assert not [_ for _ in politicas if _.nombre == 'politica2']
            assert [_ for _ in politicas if _.nombre == 'politica3']
            transaction.rollback()

    @mock.patch.object(Despachante, 'fecha_ultimo_despacho')
    def test_hay_cambio_politicas(self, mock):
        '''
        Prueba la verificacion de cambios de politicas por rango horario.
        '''
        with models.db.atomic() as transaction:
            now = datetime.now()
            models.Politica.create(nombre='politica1')
            politica2 = models.Politica.create(nombre='politica2')
            models.RangoHorario.create(
                politica=politica2,
                dia=now.weekday(),
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=now.time(),
            )
            # pruebo en caso verdadero
            ultimo = now - timedelta(minutes=1)
            mock.__get__ = Mock(return_value=ultimo)
            despachante = Despachante()
            assert despachante.hay_cambio_de_politicas() is True
            # pruebo en caso falso
            ultimo = now - timedelta(hours=2)
            mock.__get__ = Mock(return_value=ultimo)
            assert despachante.hay_cambio_de_politicas() is False
            transaction.rollback()

    @mock.patch.object(Despachante, 'fecha_ultimo_despacho')
    def test_hay_cambio_politicas_sin_despacho_anterior(self, mock):
        '''
        Prueba la verificacion de cambios de politicas por rango horario en
        caso de que no haya despacho anterior.
        '''
        with models.db.atomic() as transaction:
            now = datetime.now()
            models.Politica.create(nombre='politica1')
            politica2 = models.Politica.create(nombre='politica2')
            models.RangoHorario.create(
                politica=politica2,
                dia=now.weekday(),
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=now.time(),
            )
            mock.__get__ = Mock(return_value=None)
            despachante = Despachante()
            assert despachante.hay_cambio_de_politicas() is True
            transaction.rollback()

    @mock.patch('subprocess.Popen')
    @mock.patch.object(jinja2.environment.Template, 'render')
    def test_despachar(self, mock_render, mock_popen):
        '''
        Prueba la creacion y ejecucion del script de politicas.
        '''
        with models.db.atomic() as transaction:
            models.Politica.create(nombre='politica1')
            models.Politica.create(nombre='politica2')
            despachante = Despachante()
            mock_open = mock.mock_open()
            with mock.patch('netcop.despachante.despachante.open', mock_open):
                despachante.despachar()
            assert mock_render.called
            assert mock_open.called
            assert mock_popen.called
            mock_open.assert_called_with(Despachante.SCRIPT_FILE, 'w')
            mock_popen.assert_called_with(['/bin/sh', Despachante.SCRIPT_FILE])
            transaction.rollback()
