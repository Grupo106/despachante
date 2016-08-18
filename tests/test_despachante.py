# -*- coding: utf-8 -*-
'''
Pruebas del despachante de clases de trafico.
'''
import unittest
import mock
from datetime import datetime, timedelta
from mock import Mock, MagicMock

from netcop.despachante import models, config, Despachante
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
        p = {Param.MAC: set()}
        # llamo metodo a probar
        flags = objetivo.obtener_parametros(p)
        # verifico que todo este bien
        assert '00:00:00:00:00:01' in p[Param.MAC]
        # preparo datos, debe ignorar que se especifico como destino
        objetivo = models.Objetivo(
            direccion_fisica='00:00:00:00:00:02',
            tipo=models.Objetivo.DESTINO
        )
        # llamo metodo a probar
        flags = objetivo.obtener_parametros(p)
        # verifico que todo este bien
        assert '00:00:00:00:00:02' in p[Param.MAC]

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
            p = {Param.IP_ORIGEN: set(),
                 Param.IP_DESTINO: set()}

            # creo objetivo como origen
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.ORIGEN
            )
            # llamo metodo a probar
            flags = objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p[Param.IP_ORIGEN]
            assert '192.168.2.0/24' in p[Param.IP_ORIGEN]

            # creo objetivo como destino
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.DESTINO
            )
            # llamo metodo a probar
            flags = objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p[Param.IP_DESTINO]
            assert '192.168.2.0/24' in p[Param.IP_DESTINO]

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

            p = {
                Param.TCP_ORIGEN: set(),
                Param.TCP_DESTINO: set(),
                Param.UDP_ORIGEN: set(),
                Param.UDP_DESTINO: set(),
            }

            # creo objetivo como origen
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.ORIGEN
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert 53 in p[Param.UDP_ORIGEN]
            assert 22 in p[Param.TCP_ORIGEN]
            assert 80 in p[Param.UDP_ORIGEN]
            assert 80 in p[Param.TCP_ORIGEN]

            # creo objetivo como destino
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.DESTINO
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert 53 in p[Param.UDP_DESTINO]
            assert 22 in p[Param.TCP_DESTINO]
            assert 80 in p[Param.UDP_DESTINO]
            assert 80 in p[Param.TCP_DESTINO]

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

            p = {
                Param.IP_ORIGEN: set(),
                Param.IP_DESTINO: set(),
                Param.TCP_ORIGEN: set(),
                Param.TCP_DESTINO: set(),
                Param.UDP_ORIGEN: set(),
                Param.UDP_DESTINO: set(),
            }

            # creo objetivo como origen
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.ORIGEN
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p[Param.IP_ORIGEN]
            assert '192.168.2.0/24' in p[Param.IP_ORIGEN]
            assert 53 in p[Param.UDP_ORIGEN]
            assert 22 in p[Param.TCP_ORIGEN]

            # creo objetivo como destino
            objetivo = models.Objetivo(
                clase=clase,
                tipo=models.Objetivo.DESTINO
            )
            # llamo metodo a probar
            objetivo.obtener_parametros(p)
            # verifico que todo este bien
            assert '192.168.1.0/24' in p[Param.IP_DESTINO]
            assert '192.168.2.0/24' in p[Param.IP_DESTINO]
            assert 53 in p[Param.UDP_DESTINO]
            assert 22 in p[Param.TCP_DESTINO]

            transaction.rollback()

    def test_flags_politica_restriccion_destino(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como destino.
        '''
        # preparo datos
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.update({
            Param.IP_DESTINO: ['192.168.0.0/24', '192.168.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.update({
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
        objetivo_mac.obtener_parametros = lambda x: x.update({
            Param.MAC: ['10:00:00:00:00:00', '20:00:00:00:00:00']
        })
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.update({
            Param.IP_ORIGEN: ['192.168.0.0/24', '192.168.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.update({
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
        objetivo_mac.obtener_parametros = lambda x: x.update({
            Param.MAC: ['10:00:00:00:00:00', '20:00:00:00:00:00']
        })
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.update({
            Param.IP_ORIGEN: ['192.168.0.0/24', '192.168.1.0/24'],
            Param.IP_DESTINO: ['172.16.0.0/24', '172.16.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.update({
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
        objetivo_mac.obtener_parametros = lambda x: x.update({
            Param.MAC: ['10:00:00:00:00:00', '20:00:00:00:00:00']
        })
        objetivo_ip = Mock()
        objetivo_ip.obtener_parametros = lambda x: x.update({
            Param.IP_ORIGEN: ['192.168.0.0/24', '192.168.1.0/24'],
            Param.IP_DESTINO: ['172.16.0.0/24', '172.16.1.0/24'],
        })
        objetivo_puerto = Mock()
        objetivo_puerto.obtener_parametros = lambda x: x.update({
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
        template = env.get_template("despachante.j2")
        script = template.render(politicas=[politica1, politica2, politica3,
                                            politica4],
                                 if_outside='eth0',
                                 if_inside='eth1')
        assert '1mbit' in script
        assert '2048kbit' in script
        assert '512kbit' in script
        assert 'DROP' in script

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
        mock.return_value = 1471446575.5391228
        assert despachante.fecha_ultimo_despacho == 1471446575.5391228
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
            politica3 = models.Politica.create(nombre='politica3')
            # politica1: rango no valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.day + 1,
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=2)).time(),
            )
            # politica1: rango valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.day,
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=1)).time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.day,
                hora_inicial=(now + timedelta(hours=1)).time(),
                hora_fin=(now + timedelta(hours=2)).time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.day + 1,
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
            politica3 = models.Politica.create(nombre='politica3')
            # politica1: rango no valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.day + 1,
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=now.time(),
            )
            # politica1: rango valido
            models.RangoHorario.create(
                politica=politica1,
                dia=now.day,
                hora_inicial=(now - timedelta(hours=2)).time(),
                hora_fin=now.time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.day,
                hora_inicial=(now - timedelta(hours=1)).time(),
                hora_fin=now.time(),
            )
            # politica2: rango no valido
            models.RangoHorario.create(
                politica=politica2,
                dia=now.day + 1,
                hora_inicial=(now - timedelta(hours=2)).time(),
                hora_fin=now.time(),
            )
            # una hora atras
            fecha = now - timedelta(hours=2)
            politicas = despachante.obtener_politicas(fecha)
            assert [_ for _ in politicas if _.nombre == 'politica1']
            assert not [_ for _ in politicas if _.nombre == 'politica2']
            assert [_ for _ in politicas if _.nombre == 'politica3']
            transaction.rollback()
