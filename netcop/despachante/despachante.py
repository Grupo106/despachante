# -*- coding: utf-8 -*-
'''
Encargado de transformar las politicas creadas por el usuario en comandos que
el sistema operativo pueda reconocer.
'''
import os
import logging
import subprocess
from . import models, config
from datetime import datetime
from jinja2 import Environment, PackageLoader

log = logging.getLogger(__name__)


class Despachante:
    '''
    Traduce politicas de usuario en un script bash que sera interpretado por el
    sistema operativo.
    '''

    # Nombre del script que se creara para despachar las politicas. Conviene
    # que sea en una carpeta temporal para que se elimine cuando el sistema
    # operativo se reinicia
    SCRIPT_FILE = '/tmp/netcop-despachar-politicas'

    @property
    def fecha_ultimo_despacho(self):
        '''
        Obtiene la fecha y hora del ultimo despacho.
        Devuelve None si no se encontro despacho anterior.
        '''
        try:
            return datetime.fromtimestamp(os.path.getmtime(self.SCRIPT_FILE))
        except OSError:
            return None

    def hay_reglas_temporales(self):
        '''
        Devuelve verdadero en caso que existan politicas en la base de datos
        que posean un rango horario de validez.
        '''
        now = datetime.now()
        return (models.RangoHorario
                      .select(models.RangoHorario.dia == now.weekday())
                      .exists())

    def hay_cambio_de_politicas(self):
        '''
        Devuelve verdadero en caso que existan cambios en las politicas
        despachadas por ultima vez y las politicas vigentes en el momento
        actual.
        '''
        ultimo_despacho = self.fecha_ultimo_despacho
        # si no se encontro ultimo despacho, hay cambios de politicas
        if ultimo_despacho is None:
            log.info("No se encontro despacho previo")
            return True
        anterior = set(self.obtener_politicas(ultimo_despacho))
        ahora = set(self.obtener_politicas())
        log.debug("Politicas activas el ultimo despacho: %s" %
                  [str(p) for p in anterior])
        log.debug("Politicas activas ahora: %s" %
                  [str(p) for p in ahora])
        # si la diferencia es distinta de cero, hay cambios
        return len(anterior - ahora) + len(ahora - anterior) != 0

    def obtener_politicas(self, fecha=None):
        '''
        Obtiene una lista de politicas activas en la fecha pasada por
        parametro.

        En caso que no se pase fecha por parametro, obtiene las politicas
        activas en el momento actual.
        '''
        fecha = datetime.now() if fecha is None else fecha
        politicas = models.Politica.select().where(
            models.Politica.activa == True
        )
        return [p for p in politicas if p.esta_activa(fecha)]

    def despacho_necesario(self):
        '''
        Devuelve verdadero en caso que sea necesario un nuevo despacho.

        Sera necesario un nuevo despacho cuando no exista un despacho anterior,
        o cuando existan reglas temporales y haya que activar o desactivar
        politicas debido al paso del tiempo.
        '''
        reglas_temporales = self.hay_reglas_temporales()
        cambio_politicas = self.hay_cambio_de_politicas()
        log.debug("Hay reglas temporales? %s" % reglas_temporales)
        log.debug("Hay cambio politicas? %s" % cambio_politicas)
        return (self.fecha_ultimo_despacho is None or reglas_temporales and
                cambio_politicas)

    def despachar(self):
        '''
        Genera el script bash con las politicas activas en este momento y lo
        manda a ejecutar al sistema operativo.
        '''
        env = Environment(loader=PackageLoader('netcop.despachante'))
        template = env.get_template('main.jinja')
        politicas = self.obtener_politicas()
        contexto = {
            'politicas': politicas,
            'if_outside': config.NETCOP['outside'],
            'if_inside': config.NETCOP['inside'],
            'bw_bajada': config.NETCOP['velocidad_bajada'],
            'bw_subida': config.NETCOP['velocidad_subida'],
            'cant_alta_prioridad': len(
                [x for x in politicas if x.prioridad == x.PRIO_ALTA]
            ),
        }
        log.debug("Generando script")
        script = template.render(**contexto)
        log.debug("Escribiendo script en archivo %s" % self.SCRIPT_FILE)
        with open(self.SCRIPT_FILE, 'w') as f:
            for line in script.split('\n'):
                line = line.strip()
                if line:
                    f.write(line + '\n')
        # ejecuto script
        log.debug("Ejecutando script %s" % self.SCRIPT_FILE)
        subprocess.Popen(['/bin/sh', self.SCRIPT_FILE])
