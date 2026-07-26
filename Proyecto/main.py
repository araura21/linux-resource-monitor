# Menu principal

import os
import sys
import threading
import time
from datetime import datetime

from database import init_db
from monitor_cpu import obtener_info_cpu
from monitor_ram import obtener_info_ram
from monitor_disco import obtener_info_disco
from monitor_red import obtener_interfaces_red
from monitor_procesos import obtener_procesos
from monitor_usuarios import obtener_usuarios_conectados
from crud import (
    guardar_snapshot,
    listar_monitoreos,
    ver_detalle_monitoreo,
    actualizar_monitoreo,
    eliminar_monitoreo,
    existe_monitoreo,
    obtener_monitoreo_completo,
)


def capturar_snapshot():
    return {
        'fecha': datetime.now(),
        'cpu': obtener_info_cpu(),
        'ram': obtener_info_ram(),
        'disco': obtener_info_disco(),
        'red': obtener_interfaces_red(),
        'procesos': obtener_procesos(limite=20),
        'usuarios': obtener_usuarios_conectados(),
    }


def _imprimir_snapshot(snapshot):
    print(f"\n--- Estado del sistema: {snapshot['fecha'].strftime('%Y-%m-%d %H:%M:%S')} ---")

    cpu = snapshot['cpu']
    print(f"CPU: {cpu['nucleos']} núcleos | {cpu['frecuencia']:.2f} MHz | uso {cpu['uso_porcentaje']}%")

    ram = snapshot['ram']
    print(f"RAM: {ram['usada_mb']} / {ram['total_mb']} MB usados ({ram['porcentaje']}%) | swap usada: {ram['swap_usada_mb']} MB")

    disco = snapshot['disco']
    if disco.get('error'):
        print(f"Disco: error al leer -> {disco['error']}")
    else:
        print(f"Disco: {disco['usado_gb']} / {disco['total_gb']} GB usados ({disco['porcentaje']}%)")

    print("Interfaces de red:")
    if snapshot['red']:
        for iface in snapshot['red']:
            print(f"  - {iface['nombre_interfaz']} ({iface['direccion_ip']}): "
                  f"enviados {iface['bytes_enviados']} B, recibidos {iface['bytes_recibidos']} B")
    else:
        print("  (sin interfaces detectadas)")

    print(f"Procesos capturados (top {len(snapshot['procesos'])} por %CPU):")
    for proceso in snapshot['procesos'][:5]:
        print(f"  - PID {proceso['pid']} {proceso['nombre']} ({proceso['usuario']}): "
              f"CPU {proceso['cpu']}% MEM {proceso['memoria']}%")
    if len(snapshot['procesos']) > 5:
        print(f"  ... y {len(snapshot['procesos']) - 5} más")

    print("Usuarios conectados:")
    if snapshot['usuarios']:
        for usuario in snapshot['usuarios']:
            print(f"  - {usuario['usuario']} en {usuario['terminal']} desde {usuario['hora_inicio']}")
    else:
        print("  (nadie conectado)")
    print()


def hilo_captura_automatica(intervalo=30, detener_event=None):
    if detener_event is None:
        detener_event = threading.Event()

    while not detener_event.is_set():
        capturar_snapshot() 
        hora = datetime.now().strftime('%H:%M:%S')
        print(f"\n[Captura automática] Snapshot guardado a las {hora}")

        for _ in range(intervalo):
            if detener_event.is_set():
                break
            time.sleep(1)


def _pedir_id_monitoreo(mensaje="Ingresa el id del monitoreo: "):
    texto = input(mensaje).strip()
    try:
        return int(texto)
    except ValueError:
        print("El id debe ser un número entero.\n")
        return None


def _opcion_ver_estado():
    snapshot = capturar_snapshot()
    _imprimir_snapshot(snapshot)

    respuesta = input("¿Deseas guardar esta captura? (s/n): ").strip().lower()
    if respuesta == 's':
        comentario = input("Comentario opcional (Enter para dejar en blanco): ").strip()
        guardar_snapshot(snapshot, comentario)
    print()


def _opcion_consultar():
    filas = listar_monitoreos(limite=10)
    if not filas:
        print()
        return

    respuesta = input("\n¿Ver detalle de algún id? (Enter para omitir): ").strip()
    if respuesta:
        try:
            monitoreo_id = int(respuesta)
            ver_detalle_monitoreo(monitoreo_id)
        except ValueError:
            print("El id debe ser un número entero.")
    print()


def _opcion_actualizar():
    filas = listar_monitoreos(limite=10)
    if not filas:
        print()
        return

    monitoreo_id = _pedir_id_monitoreo("\nIngresa el id del monitoreo a actualizar: ")
    if monitoreo_id is None:
        return

    comentario = input("Nuevo comentario (Enter para no modificarlo): ").strip()
    etiqueta = input("Nueva etiqueta (Enter para no modificarla): ").strip()

    actualizar_monitoreo(
        monitoreo_id,
        comentario=comentario if comentario else None,
        etiqueta=etiqueta if etiqueta else None,
    )
    print()


def _opcion_eliminar():

    monitoreo_id = _pedir_id_monitoreo("Ingresa el id del monitoreo a eliminar: ")
    if monitoreo_id is None:
        return

    confirmacion = input(
        f"¿Seguro que deseas eliminar el monitoreo {monitoreo_id}? Esta acción no se puede deshacer (s/n): "
    ).strip().lower()

    if confirmacion == 's':
        eliminar_monitoreo(monitoreo_id)
    else:
        print("Eliminación cancelada.")
    print()


def _generar_reporte_archivo(monitoreo_id, datos):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"reporte_sistema_{monitoreo_id}_{timestamp}.txt"

    monitoreo = datos['monitoreo']

    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write("=== REPORTE DE MONITOREO DEL SISTEMA ===\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Monitoreo id: {monitoreo_id}\n\n")

        f.write("--- Datos del sistema ---\n")
        for clave, valor in monitoreo.items():
            f.write(f"{clave}: {valor}\n")

        f.write("\n--- Procesos capturados ---\n")
        if datos['procesos']:
            for p in datos['procesos']:
                f.write(
                    f"PID {p['pid']:<8} {p['nombre']:<20} estado={p['estado']:<6} "
                    f"usuario={p['usuario']:<12} cpu={p['cpu']}% mem={p['memoria']}%\n"
                )
        else:
            f.write("(sin procesos registrados)\n")

        f.write("\n--- Usuarios conectados ---\n")
        if datos['usuarios']:
            for u in datos['usuarios']:
                f.write(f"{u['usuario']} en {u['terminal']} desde {u['hora_inicio']}\n")
        else:
            f.write("(sin usuarios registrados)\n")

        f.write("\n--- Interfaces de red ---\n")
        if datos['interfaces']:
            for i in datos['interfaces']:
                f.write(
                    f"{i['nombre_interfaz']} ({i['direccion_ip']}): "
                    f"enviados {i['bytes_enviados']} B, recibidos {i['bytes_recibidos']} B\n"
                )
        else:
            f.write("(sin interfaces registradas)\n")

    return nombre_archivo


def exportar_reporte(monitoreo_id):

    pid = os.fork()

    if pid == 0:
    
        datos = obtener_monitoreo_completo(monitoreo_id)
        nombre_archivo = _generar_reporte_archivo(monitoreo_id, datos)
        print(f"[Proceso hijo PID {os.getpid()}] Reporte generado: {nombre_archivo}")

        sys.stdout.flush()
        os._exit(0)
    else:
        print(f"[Proceso padre] Se creó el proceso hijo con PID {pid} para exportar el reporte")

        os.waitpid(pid, 0)
        print(f"[Proceso padre] El proceso hijo {pid} terminó, reporte listo.\n")


def _opcion_exportar():
    
    filas = listar_monitoreos(limite=10)
    if not filas:
        print()
        return

    monitoreo_id = _pedir_id_monitoreo("\nIngresa el id del monitoreo a exportar: ")
    if monitoreo_id is None:
        return

    if not existe_monitoreo(monitoreo_id):
        print(f"No existe un monitoreo con id {monitoreo_id}.\n")
        return

    exportar_reporte(monitoreo_id)


def _mostrar_menu():
    print("=== Mini Monitor de Recursos ===")
    print("1. Ver estado actual del sistema")
    print("2. Consultar monitoreos guardados")
    print("3. Actualizar comentario/etiqueta de un monitoreo")
    print("4. Eliminar un monitoreo")
    print("5. Exportar reporte a archivo")
    print("6. Salir")


def main():
   
    init_db()

    detener_event = threading.Event()
    hilo_bg = threading.Thread(
        target=hilo_captura_automatica,
        args=(30, detener_event),
        daemon=True,
    )
    hilo_bg.start()

    while True:
        _mostrar_menu()
        try:
            opcion = input("Elige una opción: ").strip()
        except (EOFError, KeyboardInterrupt):
            opcion = '6'
            print()

        if opcion == '1':
            _opcion_ver_estado()
        elif opcion == '2':
            _opcion_consultar()
        elif opcion == '3':
            _opcion_actualizar()
        elif opcion == '4':
            _opcion_eliminar()
        elif opcion == '5':
            _opcion_exportar()
        elif opcion == '6':
            print("Cerrando el monitor...")
            detener_event.set()
            hilo_bg.join(timeout=2)
            sys.exit(0)
        else:
            print("Opción inválida, intenta de nuevo.\n")


if __name__ == '__main__':
    main()
