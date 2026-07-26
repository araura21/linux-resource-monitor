# Lectura de Red

import re
import subprocess


def _obtener_nombres_e_ips():
    resultado = subprocess.run(
        ['ip', '-4', 'addr', 'show'],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        return None 

    interfaces = {}
    nombre_actual = None

    for linea in resultado.stdout.split('\n'):
        match_nombre = re.match(r'^\d+:\s+([^:@]+)', linea)
        if match_nombre:
            nombre_actual = match_nombre.group(1).strip()
            interfaces[nombre_actual] = None  
            continue

        match_ip = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/\d+', linea)
        if match_ip and nombre_actual is not None:
            if interfaces[nombre_actual] is None:
                interfaces[nombre_actual] = match_ip.group(1)

    return interfaces


def _obtener_bytes_por_interfaz():
    bytes_por_interfaz = {}

    with open('/proc/net/dev', 'r') as f:
        lineas = f.readlines()

    for linea in lineas[2:]:
        nombre, _, resto = linea.partition(':')
        nombre = nombre.strip()
        columnas = resto.split()

        if len(columnas) < 9:
            continue

        bytes_recibidos = float(columnas[0])  
        bytes_enviados = float(columnas[8])   

        bytes_por_interfaz[nombre] = {
            'bytes_recibidos': bytes_recibidos,
            'bytes_enviados': bytes_enviados,
        }

    return bytes_por_interfaz


def obtener_interfaces_red():
    nombres_ips = _obtener_nombres_e_ips()
    bytes_por_interfaz = _obtener_bytes_por_interfaz()

    if nombres_ips is None:
        nombres_ips = {nombre: None for nombre in bytes_por_interfaz}

    resultado = []
    for nombre, direccion_ip in nombres_ips.items():
        stats = bytes_por_interfaz.get(nombre, {'bytes_enviados': 0.0, 'bytes_recibidos': 0.0})
        resultado.append({
            'nombre_interfaz': nombre,
            'direccion_ip': direccion_ip,
            'bytes_enviados': stats['bytes_enviados'],
            'bytes_recibidos': stats['bytes_recibidos'],
        })

    sin_loopback = [iface for iface in resultado if iface['nombre_interfaz'] != 'lo']
    hay_otra_con_ip = any(iface['direccion_ip'] is not None for iface in sin_loopback)

    if hay_otra_con_ip:
        return sin_loopback
    return resultado


if __name__ == '__main__':
    interfaces = obtener_interfaces_red()
    print("Interfaces de red obtenidas con 'ip -4 addr show' + /proc/net/dev:")
    for iface in interfaces:
        print(f"  {iface}")
