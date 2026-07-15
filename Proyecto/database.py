# Manejo de Base de Datos y CRUD

import sqlite3

def init_db():
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()

    # Tabla principal de monitoreos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monitoreos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hostname TEXT,
        comentario TEXT,
        
        cpu_nucleos INTEGER,
        cpu_frecuencia REAL,
        cpu_uso REAL,
        
        mem_total REAL,
        mem_usada REAL,
        mem_libre REAL,
        mem_swap REAL,
        mem_porcentaje REAL,
        
        disco_total REAL,
        disco_usado REAL,
        disco_libre REAL,
        disco_porcentaje REAL,
        
        bytes_enviados REAL,
        bytes_recibidos REAL,
        
        load_1 REAL,
        load_5 REAL,
        load_15 REAL
    )
    ''')

    # Tabla de procesos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS procesos_capturados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitoreo_id INTEGER,
        pid INTEGER,
        nombre TEXT,
        estado TEXT,
        usuario TEXT,
        memoria REAL,
        cpu REAL,
        FOREIGN KEY (monitoreo_id) REFERENCES monitoreos(id) ON DELETE CASCADE
    )
    ''')

    # Tabla de usuarios conectados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios_conectados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitoreo_id INTEGER,
        usuario TEXT,
        terminal TEXT,
        hora_inicio TEXT,
        FOREIGN KEY (monitoreo_id) REFERENCES monitoreos(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()
    print("Base de datos inicializada exitosamente con todas las tablas.")

if __name__ == '__main__':
    init_db()
