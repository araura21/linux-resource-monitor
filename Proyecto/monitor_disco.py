# Lectura de Disco

import subprocess


def obtener_info_disco(punto_montaje='/'):

    resultado = subprocess.run(
        ['df', '-B1', punto_montaje],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:

        return {
            'total_gb': None,
            'usado_gb': None,
            'libre_gb': None,
            'porcentaje': None,
            'error': resultado.stderr.strip(),
        }

    try:
        lineas = resultado.stdout.strip().split('\n')

        datos = ' '.join(lineas[1:]).split()

        porcentaje_texto = datos[-2].replace('%', '')
        libre_bytes = int(datos[-3])
        usado_bytes = int(datos[-4])
        total_bytes = int(datos[-5])

        total_gb = total_bytes / (1024 ** 3)
        usado_gb = usado_bytes / (1024 ** 3)
        libre_gb = libre_bytes / (1024 ** 3)
        porcentaje = float(porcentaje_texto)

        return {
            'total_gb': round(total_gb, 2),
            'usado_gb': round(usado_gb, 2),
            'libre_gb': round(libre_gb, 2),
            'porcentaje': round(porcentaje, 2),
        }
    except (IndexError, ValueError) as e:

        return {
            'total_gb': None,
            'usado_gb': None,
            'libre_gb': None,
            'porcentaje': None,
            'error': f"No se pudo parsear la salida de df: {e}",
        }


if __name__ == '__main__':
    info = obtener_info_disco()
    print("Información de Disco obtenida con 'df -B1 /':")
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
