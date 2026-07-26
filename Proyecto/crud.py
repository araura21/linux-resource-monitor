# Operaciones CRUD sobre la base de datos (tabla monitoreos y sus relacionadas)

import socket

from database import get_connection


def _existe_monitoreo(cursor, monitoreo_id):

    cursor.execute('SELECT 1 FROM monitoreos WHERE id = ?', (monitoreo_id,))
    return cursor.fetchone() is not None


def existe_monitoreo(monitoreo_id):
    conn = get_connection()
    cursor = conn.cursor()
    resultado = _existe_monitoreo(cursor, monitoreo_id)
    conn.close()
    return resultado


def obtener_monitoreo_completo(monitoreo_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM monitoreos WHERE id = ?', (monitoreo_id,))
    columnas = [d[0] for d in cursor.description]
    fila = cursor.fetchone()

    if fila is None:
        conn.close()
        return None

    monitoreo = dict(zip(columnas, fila))

    cursor.execute(
        'SELECT pid, nombre, estado, usuario, memoria, cpu FROM procesos_capturados WHERE monitoreo_id = ?',
        (monitoreo_id,),
    )
    procesos = [
        {'pid': pid, 'nombre': nombre, 'estado': estado, 'usuario': usuario, 'memoria': memoria, 'cpu': cpu}
        for pid, nombre, estado, usuario, memoria, cpu in cursor.fetchall()
    ]

    cursor.execute(
        'SELECT usuario, terminal, hora_inicio FROM usuarios_conectados WHERE monitoreo_id = ?',
        (monitoreo_id,),
    )
    usuarios = [
        {'usuario': usuario, 'terminal': terminal, 'hora_inicio': hora_inicio}
        for usuario, terminal, hora_inicio in cursor.fetchall()
    ]

    cursor.execute(
        'SELECT nombre_interfaz, direccion_ip, bytes_enviados, bytes_recibidos FROM interfaces_red WHERE monitoreo_id = ?',
        (monitoreo_id,),
    )
    interfaces = [
        {
            'nombre_interfaz': nombre_interfaz,
            'direccion_ip': direccion_ip,
            'bytes_enviados': bytes_enviados,
            'bytes_recibidos': bytes_recibidos,
        }
        for nombre_interfaz, direccion_ip, bytes_enviados, bytes_recibidos in cursor.fetchall()
    ]

    conn.close()

    return {
        'monitoreo': monitoreo,
        'procesos': procesos,
        'usuarios': usuarios,
        'interfaces': interfaces,
    }


def guardar_snapshot(snapshot, comentario=''):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cpu = snapshot['cpu']
        ram = snapshot['ram']
        disco = snapshot['disco']

        cursor.execute('''
            INSERT INTO monitoreos (
                hostname, comentario,
                cpu_nucleos, cpu_frecuencia, cpu_uso,
                mem_total, mem_usada, mem_libre, mem_swap, mem_porcentaje,
                disco_total, disco_usado, disco_libre, disco_porcentaje
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            socket.gethostname(), comentario,
            cpu['nucleos'], cpu['frecuencia'], cpu['uso_porcentaje'],
            ram['total_mb'], ram['usada_mb'], ram['libre_mb'], ram['swap_usada_mb'], ram['porcentaje'],
            disco.get('total_gb'), disco.get('usado_gb'), disco.get('libre_gb'), disco.get('porcentaje'),
        ))

       
        monitoreo_id = cursor.lastrowid

        for proceso in snapshot['procesos']:
            cursor.execute('''
                INSERT INTO procesos_capturados (monitoreo_id, pid, nombre, estado, usuario, memoria, cpu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                monitoreo_id, proceso['pid'], proceso['nombre'], proceso['estado'],
                proceso['usuario'], proceso['memoria'], proceso['cpu'],
            ))

        for usuario in snapshot['usuarios']:
            cursor.execute('''
                INSERT INTO usuarios_conectados (monitoreo_id, usuario, terminal, hora_inicio)
                VALUES (?, ?, ?, ?)
            ''', (monitoreo_id, usuario['usuario'], usuario['terminal'], usuario['hora_inicio']))

        for iface in snapshot['red']:
            cursor.execute('''
                INSERT INTO interfaces_red (monitoreo_id, nombre_interfaz, direccion_ip, bytes_enviados, bytes_recibidos)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                monitoreo_id, iface['nombre_interfaz'], iface['direccion_ip'],
                iface['bytes_enviados'], iface['bytes_recibidos'],
            ))

        conn.commit()
        print(f"Snapshot guardado con id de monitoreo {monitoreo_id}.")
        return monitoreo_id
    except Exception as e:
        conn.rollback()
        print(f"Error al guardar el snapshot, se revirtieron los cambios: {e}")
        return None
    finally:
        conn.close()


def listar_monitoreos(limite=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, fecha, hostname, cpu_uso, mem_porcentaje, comentario, etiqueta
        FROM monitoreos
        ORDER BY fecha DESC
        LIMIT ?
    ''', (limite,))
    filas = cursor.fetchall()
    conn.close()

    if not filas:
        print("No hay monitoreos guardados todavía.")
        return []

    def _truncar(texto, ancho):
        texto = texto or '-'
        if len(texto) > ancho:
            return texto[:ancho - 3] + '...'
        return texto

    encabezado = f"{'ID':<5}{'Fecha':<21}{'Hostname':<15}{'CPU%':<8}{'MEM%':<8}{'Comentario':<20}{'Etiqueta':<15}"
    print(encabezado)
    print("-" * len(encabezado))
    for fila in filas:
        id_, fecha, hostname, cpu_uso, mem_porcentaje, comentario, etiqueta = fila
        cpu_txt = f"{cpu_uso:.1f}" if cpu_uso is not None else '-'
        mem_txt = f"{mem_porcentaje:.1f}" if mem_porcentaje is not None else '-'
        print(
            f"{id_:<5}{str(fecha):<21}{(hostname or '-'):<15}"
            f"{cpu_txt:<8}{mem_txt:<8}{_truncar(comentario, 20):<20}{_truncar(etiqueta, 15):<15}"
        )

    return filas


def ver_detalle_monitoreo(monitoreo_id):
    datos = obtener_monitoreo_completo(monitoreo_id)
    if datos is None:
        print(f"No existe un monitoreo con id {monitoreo_id}.")
        return False

    print(f"\n--- Detalle del monitoreo {monitoreo_id} ---")
    for clave, valor in datos['monitoreo'].items():
        print(f"  {clave}: {valor}")

    print(f"\nProcesos capturados ({len(datos['procesos'])}):")
    for p in datos['procesos']:
        print(f"  PID {p['pid']} {p['nombre']} ({p['usuario']}): estado {p['estado']}, CPU {p['cpu']}%, MEM {p['memoria']}%")

    print(f"\nUsuarios conectados ({len(datos['usuarios'])}):")
    for u in datos['usuarios']:
        print(f"  {u['usuario']} en {u['terminal']} desde {u['hora_inicio']}")

    print(f"\nInterfaces de red ({len(datos['interfaces'])}):")
    for i in datos['interfaces']:
        print(f"  {i['nombre_interfaz']} ({i['direccion_ip']}): enviados {i['bytes_enviados']} B, recibidos {i['bytes_recibidos']} B")

    return True


def actualizar_monitoreo(monitoreo_id, comentario=None, etiqueta=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not _existe_monitoreo(cursor, monitoreo_id):
            print(f"No existe un monitoreo con id {monitoreo_id}.")
            return False

        campos = []
        valores = []
        if comentario is not None:
            campos.append('comentario = ?')
            valores.append(comentario)
        if etiqueta is not None:
            campos.append('etiqueta = ?')
            valores.append(etiqueta)

        if not campos:
            print("No se especificó ningún campo para actualizar.")
            return False

        valores.append(monitoreo_id)
        query = f"UPDATE monitoreos SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
        print(f"Monitoreo {monitoreo_id} actualizado correctamente.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar el monitoreo: {e}")
        return False
    finally:
        conn.close()


def eliminar_monitoreo(monitoreo_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not _existe_monitoreo(cursor, monitoreo_id):
            print(f"No existe un monitoreo con id {monitoreo_id}.")
            return False

        cursor.execute('DELETE FROM monitoreos WHERE id = ?', (monitoreo_id,))
        conn.commit()
        print(f"Monitoreo {monitoreo_id} eliminado (junto con sus procesos, usuarios e interfaces asociados).")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar el monitoreo: {e}")
        return False
    finally:
        conn.close()
