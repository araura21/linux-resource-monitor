# Lectura de Procesos

import subprocess


def obtener_procesos(limite=20):

    resultado = subprocess.run(
        ['ps', '-eo', 'pid,comm,stat,user,%mem,%cpu', '--sort=-%cpu'],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        return []

    procesos = []
    lineas = resultado.stdout.strip().split('\n')[1:]  

    for linea in lineas:
        columnas = linea.split()
        if len(columnas) < 6:
            continue  

        pid = columnas[0]
        cpu = columnas[-1]
        mem = columnas[-2]
        usuario = columnas[-3]
        estado = columnas[-4]
        nombre = ' '.join(columnas[1:-4])

        try:
            procesos.append({
                'pid': int(pid),
                'nombre': nombre,
                'estado': estado,
                'usuario': usuario,
                'memoria': float(mem),
                'cpu': float(cpu),
            })
        except ValueError:
            continue  

    return procesos[:limite]


if __name__ == '__main__':
    procesos = obtener_procesos()
    print(f"Procesos obtenidos con 'ps' (top {len(procesos)} por %CPU):")
    for proceso in procesos:
        print(f"  {proceso}")
