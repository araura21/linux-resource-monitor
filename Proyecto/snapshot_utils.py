
import os
import sys
import time
from datetime import datetime

from monitor_cpu import obtener_info_cpu
from monitor_ram import obtener_info_ram
from monitor_disco import obtener_info_disco
from monitor_red import obtener_interfaces_red
from monitor_procesos import obtener_procesos
from monitor_usuarios import obtener_usuarios_conectados
from crud import guardar_snapshot, obtener_monitoreo_completo


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


def hilo_captura_automatica(intervalo=30, detener_event=None, on_guardado=None):
    
    while not detener_event.is_set():
        snapshot = capturar_snapshot()
        monitoreo_id = guardar_snapshot(snapshot, comentario='Captura automática (hilo de fondo)')

        hora = datetime.now().strftime('%H:%M:%S')
        print(f"\n[Captura automática] Snapshot guardado a las {hora} (id {monitoreo_id})")

        if on_guardado is not None:
            on_guardado(snapshot, monitoreo_id)

        for _ in range(intervalo):
            if detener_event.is_set():
                break
            time.sleep(1)


def generar_reporte_archivo(monitoreo_id, datos, nombre_archivo=None):
    if nombre_archivo is None:
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
 
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"reporte_sistema_{monitoreo_id}_{timestamp}.txt"

    pid = os.fork()

    if pid == 0:
        datos = obtener_monitoreo_completo(monitoreo_id)
        generar_reporte_archivo(monitoreo_id, datos, nombre_archivo)
        print(f"[Proceso hijo PID {os.getpid()}] Reporte generado: {nombre_archivo}")
        sys.stdout.flush()
        os._exit(0)

    print(f"[Proceso padre] Se creó el proceso hijo con PID {pid} para exportar el reporte")
    os.waitpid(pid, 0)
    print(f"[Proceso padre] El proceso hijo {pid} terminó, reporte listo.\n")
    return nombre_archivo
