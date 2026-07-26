# Lectura de RAM

def _leer_meminfo():

    datos = {}
    with open('/proc/meminfo', 'r') as f:
        for linea in f:
            partes = linea.split(':')
            clave = partes[0].strip()
            valor = partes[1].strip().split()[0]
            datos[clave] = int(valor)
    return datos


def obtener_info_ram():
    meminfo = _leer_meminfo()

    total_kb = meminfo.get('MemTotal', 0)

    libre_kb = meminfo.get('MemFree', 0)

    if 'MemAvailable' in meminfo:
        usada_kb = total_kb - meminfo['MemAvailable']
    else:

        buffers_kb = meminfo.get('Buffers', 0)
        cached_kb = meminfo.get('Cached', 0)
        usada_kb = total_kb - libre_kb - buffers_kb - cached_kb

    swap_total_kb = meminfo.get('SwapTotal', 0)
    swap_free_kb = meminfo.get('SwapFree', 0)
    swap_usada_kb = swap_total_kb - swap_free_kb

    total_mb = total_kb / 1024
    usada_mb = usada_kb / 1024
    libre_mb = libre_kb / 1024
    swap_usada_mb = swap_usada_kb / 1024

    porcentaje = (usada_mb / total_mb) * 100 if total_mb > 0 else 0.0

    return {
        'total_mb': round(total_mb, 2),
        'usada_mb': round(usada_mb, 2),
        'libre_mb': round(libre_mb, 2),
        'swap_usada_mb': round(swap_usada_mb, 2),
        'porcentaje': round(porcentaje, 2),
    }


if __name__ == '__main__':
    info = obtener_info_ram()
    print("Información de RAM obtenida desde /proc/meminfo:")
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
