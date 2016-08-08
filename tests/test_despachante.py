# -*- coding: utf-8 -*-
'''
Pruebas del despachante de clases de trafico.
'''
import unittest
from mock import Mock

from netcop.despachante import models, config
from netcop.despachante.models import Flag, Param


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

    def test_origenes(self):
        '''
        Prueba obtener los hosts de origen de una politica.
        '''
        # creo transaccion para descartar cambios generados en la base
        with models.db.atomic() as transaction:
            # preparo datos
            politica = models.Politica.create(nombre='foo')
            models.Objetivo.create(direccion_fisica='00:00:00:00:00:01',
                                   politica=politica,
                                   tipo=models.Objetivo.ORIGEN)
            models.Objetivo.create(direccion_fisica='00:00:00:00:00:02',
                                   politica=politica,
                                   tipo=models.Objetivo.DESTINO)
            # llamo metodo a probar
            lista = politica.origenes
            # verifico que todo este bien
            assert len(lista) == 1
            assert lista[0].direccion_fisica == '00:00:00:00:00:01'
            # descarto cambios en la base de datos
            transaction.rollback()

    def test_destinos(self):
        '''
        Prueba obtener los hosts de destino de una politica.
        '''
        # creo transaccion para descartar cambios generados en la base
        with models.db.atomic() as transaction:
            # preparo datos
            politica = models.Politica.create(nombre='foo')
            models.Objetivo.create(direccion_fisica='00:00:00:00:00:01',
                                   politica=politica,
                                   tipo=models.Objetivo.ORIGEN)
            models.Objetivo.create(direccion_fisica='00:00:00:00:00:02',
                                   politica=politica,
                                   tipo=models.Objetivo.DESTINO)
            # llamo metodo a probar
            lista = politica.destinos
            # verifico que todo este bien
            assert len(lista) == 1
            assert lista[0].direccion_fisica == '00:00:00:00:00:02'
            # descarto cambios en la base de datos
            transaction.rollback()

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

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_restriccion_destino(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como destino.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_restriccion_origen(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como origen.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_restriccion_origen_destino(self):
        '''
        Prueba obtener los flags de una politica de restriccion que solo defina
        objetivos como origen y destino.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_limitacion_destino(self):
        '''
        Prueba obtener los flags de una politica de limitacion que solo defina
        objetivos como destino.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_limitacion_origen(self):
        '''
        Prueba obtener los flags de una politica de limitacion que solo defina
        objetivos como origen.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_limitacion_origen_destino(self):
        '''
        Prueba obtener los flags de una politica de limitacion que solo defina
        objetivos como origen y destino.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_priorizacion_destino(self):
        '''
        Prueba obtener los flags de una politica de priorizacion que solo
        defina objetivos como destino.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_priorizacion_origen(self):
        '''
        Prueba obtener los flags de una politica de priorizacion que solo
        defina objetivos como origen.
        '''
        pass

    @unittest.skip("NO IMPLEMENTADO")
    def test_flags_politica_priorizacion_origen_destino(self):
        '''
        Prueba obtener los flags de una politica de priorizacion que solo
        defina objetivos como origen y destino.
        '''
        pass
