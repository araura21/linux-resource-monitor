# Lectura de Usuarios

import subprocess


def obtener_usuarios_conectados():
    resultado = subprocess.run(
        ['who'],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        return []

    usuarios = []
    salida = resultado.stdout.strip()

    if not salida:
        return usuarios

    for linea in salida.split('\n'):
        columnas = linea.split()
        if len(columnas) < 3:
            continue   
        
        usuario = columnas[0]
        terminal = columnas[1]
        hora_inicio = ' '.join(columnas[2:])

        usuarios.append({
            'usuario': usuario,
            'terminal': terminal,
            'hora_inicio': hora_inicio,
        })

    return usuarios


if __name__ == '__main__':
    usuarios = obtener_usuarios_conectados()
    print(f"Usuarios conectados obtenidos con 'who' ({len(usuarios)} sesión/es):")
    for usuario in usuarios:
        print(f"  {usuario}")
