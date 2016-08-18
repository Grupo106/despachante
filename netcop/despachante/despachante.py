# -*- coding: utf-8 -*-
'''
Encargado de transformar las politicas creadas por el usuario en comandos que
el sistema operativo pueda reconocer.
'''
import os

from . import models

# Nombre del script que se creara para despachar las politicas. Conviene que
# sea en una carpeta temporal para que se elimine cuando el sistema operativo
# se reinicia
SCRIPT_FILE = '/tmp/netcop-despachar-politicas'

class Despachante:
    '''
    Traduce politicas de usuario en un script bash que sera interpretado por el
    sistema operativo.
    '''

    @property
    def fecha_ultimo_despacho(self):
        '''
        Obtiene la fecha y hora del ultimo despacho efectuado en formato
        Unix-Time. Devuelve None si no se encontro despacho anterior.
        '''
        try:
            return os.path.getmtime(SCRIPT_FILE)
        except OSError:
            return None

    def hay_reglas_temporales(self):
        '''
        Devuelve verdadero en caso que existan politicas en la base de datos
        que posean un rango horario de validez.
        '''
        return models.RangoHorario.select().exists()

    def hay_cambio_de_politicas(self):
        '''
        Devuelve verdadero en caso que existan cambios en las politicas
        despachadas por ultima vez y las politicas vigentes en el momento
        actual.
        '''
        pass

    def obtener_politicas(self, fecha=None):
        '''
        Obtiene una lista de politicas activas en la fecha pasada por
        parametro.

        En caso que no se pase fecha por parametro, obtiene las politicas
        activas en el momento actual.
        '''
        politicas = models.Politica.select()
        return [politica for politica in politicas if politica.activa(fecha)]

    def despachar(self):
        '''
        Genera el script bash con las politicas activas en este momento y lo
        manda a ejecutar al sistema operativo.
        '''
        pass
