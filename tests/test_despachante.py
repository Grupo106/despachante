# -*- coding: utf-8 -*-
'''
Pruebas del despachante de clases de trafico.
'''
import unittest

from netcop.despachante import models, config


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

    def test_destinos(self):
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

    @unittest.skip("no implementado")
    def test_flags_objetivo(self):
        pass

    @unittest.skip("no implementado")
    def test_flags_politica(self):
        pass
