# Lectura de CPU

import time


def _leer_nucleos_y_frecuencia():

    nucleos = 0
    frecuencias = []

    with open('/proc/cpuinfo', 'r') as f:
        for linea in f:
            if linea.startswith('processor'):
                nucleos += 1
            elif linea.startswith('cpu MHz'):
                valor = linea.split(':')[1].strip()
                frecuencias.append(float(valor))

    frecuencia_promedio = sum(frecuencias) / len(frecuencias) if frecuencias else 0.0

    return nucleos, frecuencia_promedio


def _leer_tiempos_cpu():
    with open('/proc/stat', 'r') as f:
        primera_linea = f.readline()

    valores = primera_linea.split()[1:]
    tiempos = [int(v) for v in valores]

    tiempo_idle = tiempos[3] + tiempos[4]
    tiempo_total = sum(tiempos)

    return tiempo_idle, tiempo_total


def obtener_info_cpu(intervalo=1):
    nucleos, frecuencia = _leer_nucleos_y_frecuencia()

    idle_1, total_1 = _leer_tiempos_cpu()
    time.sleep(intervalo)
    idle_2, total_2 = _leer_tiempos_cpu()

    delta_idle = idle_2 - idle_1
    delta_total = total_2 - total_1

    if delta_total > 0:
        uso_porcentaje = (1 - (delta_idle / delta_total)) * 100
    else:
        uso_porcentaje = 0.0

    return {
        'nucleos': nucleos,
        'frecuencia': frecuencia,
        'uso_porcentaje': round(uso_porcentaje, 2),
    }


if __name__ == '__main__':
    info = obtener_info_cpu()
    print("Información de CPU obtenida desde /proc:")
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
