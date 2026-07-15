# Guía de Desarrollo Paso a Paso - Proyecto Integrador de SO (ESPE)
## Proyecto: Mini Monitor de Recursos para Linux utilizando Python

Esta guía detalla las actividades, las plataformas/aplicaciones a utilizar, los comandos y el código de referencia para completar con éxito el proyecto de **Sistemas Operativos** a lo largo de las 5 semanas.

---

## 📅 Semana 1: Planificación, Arquitectura y Base de Datos

El objetivo de esta semana es establecer la infraestructura del proyecto, configurar el entorno colaborativo de desarrollo y estructurar el almacenamiento persistente de datos (CRUD).

### 🛠️ Herramientas y Aplicaciones
*   **Terminal de Linux (Bash)**
*   **GitHub (Plataforma Web)**
*   **Visual Studio Code (VSC)**
*   **SQLite (Motor de base de datos integrado en Python)**

### 📋 Pasos a Seguir

#### Paso 1: Configurar el Repositorio de Git y Entorno en VSC
1. **Crear el repositorio en GitHub:** Un miembro del equipo debe iniciar sesión en GitHub, crear un nuevo repositorio (público o privado) llamado `mini-monitor-recursos` y añadir a los demás integrantes como colaboradores en la sección de configuración (*Settings -> Collaborators*).
2. **Clonar el repositorio:** En la máquina Linux de cada integrante, abran la terminal y ejecuten:
   ```bash
   git clone https://github.com/USUARIO/mini-monitor-recursos.git
   cd mini-monitor-recursos
   ```
3. **Estructurar el espacio de trabajo:** Abran la carpeta clonada en Visual Studio Code escribiendo en la terminal:
   ```bash
   code .
   ```
4. Creen la estructura básica de archivos en Visual Studio Code:
   * `main.py` (Menú principal)
   * `database.py` (Manejo de Base de Datos y CRUD)
   * `monitor_cpu.py` (Lectura de CPU)
   * `monitor_ram.py` (Lectura de RAM)
   * `monitor_sistema.py` (Lectura de Disco, Red, Procesos)

#### Paso 2: Implementar la Base de Datos con SQLite
Utilizaremos **SQLite** porque no requiere instalar servidores adicionales y almacena todo en un único archivo (`monitor.db`).

1. Abran el archivo `database.py` en VSC y escriban el siguiente código inicial para crear la tabla de historial:
   ```python
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

   ```
2. Prueben la base de datos ejecutando en la terminal de VSC:
   ```bash
   python3 database.py
   ```

---

## 📅 Semana 2: Lectura de CPU y RAM desde `/proc`

El objetivo es obtener las métricas de hardware de forma directa leyendo el sistema de archivos virtual `/proc` de Linux, evitando el uso de librerías externas como `psutil`.

### 🛠️ Herramientas y Aplicaciones
*   **Visual Studio Code**
*   **Terminal de Linux** para validar información (`cat /proc/cpuinfo` y `cat /proc/meminfo`)

### 📋 Pasos a Seguir

#### Paso 1: Módulo de CPU (`monitor_cpu.py`)
1. **Analizar `/proc/cpuinfo`:** Este archivo contiene los detalles del procesador. Diseñaremos una función en Python para leer el número de núcleos y la frecuencia máxima.
2. Abran `monitor_cpu.py` e implementen el siguiente bloque:
   ```python
   def obtener_info_cpu():
       info = {"nucleos": 0, "modelo": "Desconocido", "frecuencia": "Desconocida"}
       with open('/proc/cpuinfo', 'r') as f:
           for line in f:
               if "model name" in line and info["modelo"] == "Desconocido":
                   info["modelo"] = line.split(":")[1].strip()
               if "cpu cores" in line and info["nucleos"] == 0:
                   info["nucleos"] = int(line.split(":")[1].strip())
               if "cpu MHz" in line and info["frecuencia"] == "Desconocida":
                   info["frecuencia"] = line.split(":")[1].strip() + " MHz"
       return info

   def obtener_uso_cpu_tiempo_real():
       # Para calcular el % de uso se deben leer dos veces los tiempos de /proc/stat
       # con una pequeña pausa de tiempo (e.g., 1 segundo)
       import time
       def leer_tiempos():
           with open('/proc/stat', 'r') as f:
               primera_linea = f.readline()
           campos = [float(x) for x in primera_linea.split()[1:5]] # user, nice, system, idle
           return sum(campos), campos[3] # (Total, Idle)

       total1, idle1 = leer_tiempos()
       time.sleep(1)
       total2, idle2 = leer_tiempos()

       diff_total = total2 - total1
       diff_idle = idle2 - idle1

       if diff_total == 0:
           return 0.0
       uso = (1.0 - (diff_idle / diff_total)) * 100
       return round(uso, 2)
   ```

#### Paso 2: Módulo de RAM (`monitor_ram.py`)
1. **Analizar `/proc/meminfo`:** Contiene los datos dinámicos de memoria en kilobytes (kB).
2. En `monitor_ram.py`, capturen y transformen la información a Gigabytes (GB):
   ```python
   def obtener_info_ram():
       mem_info = {}
       with open('/proc/meminfo', 'r') as f:
           for line in f:
               partes = line.split()
               if len(partes) >= 2:
                   clave = partes[0].replace(':', '')
                   valor = int(partes[1])
                   mem_info[clave] = valor

       total = mem_info.get('MemTotal', 0) / (1024 * 1024) # De kB a GB
       libre = mem_info.get('MemFree', 0) / (1024 * 1024)
       disponible = mem_info.get('MemAvailable', total) / (1024 * 1024)
       usado = total - disponible

       swap_total = mem_info.get('SwapTotal', 0) / (1024 * 1024)
       swap_libre = mem_info.get('SwapFree', 0) / (1024 * 1024)
       swap_usado = swap_total - swap_libre

       return {
           "total": round(total, 2),
           "usado": round(usado, 2),
           "libre": round(libre, 2),
           "swap_total": round(swap_total, 2),
           "swap_usado": round(swap_usado, 2)
       }
   ```

---

## 📅 Semana 3: Disco, Red, Usuarios y Procesos

El objetivo es capturar el almacenamiento, el tráfico de red, las sesiones de usuario y el estado de los procesos usando llamadas al sistema operativo a través de Python.

### 🛠️ Herramientas y Aplicaciones
*   **Visual Studio Code**
*   **Terminal de Linux** para probar comandos (`df -h`, `who`, `ps`)

### 📋 Pasos a Seguir

#### Paso 1: Módulo de Sistema (`monitor_sistema.py`)
1. **Métricas de Disco:** Utilizaremos `subprocess` para ejecutar el comando `df -h /` de Linux y capturar su salida.
2. **Métricas de Red:** Usaremos `subprocess` para llamar a `ip addr` o leeremos directamente de `/proc/net/dev`.
3. **Módulo de Usuarios:** Utilizaremos el comando `who`.
4. Escriban en `monitor_sistema.py`:
   ```python
    import subprocess

    def obtener_uso_disco():
        # Ejecuta 'df -h /' y captura la salida
        resultado = subprocess.check_output(['df', '-h', '/']).decode('utf-8')
        lineas = resultado.strip().split('
    ')
        # El resultado de interés está en la segunda línea
        datos = lineas[1].split()
        return {
            "total": datos[1],
            "usado": datos[2],
            "libre": datos[3],
            "porcentaje": datos[4]
        }

    def obtener_usuarios_conectados():
        resultado = subprocess.check_output(['who']).decode('utf-8')
        return resultado.strip()

    def obtener_procesos():
        # Listar el PID, Nombre del Proceso, Estado y Usuario propietario
        # Se limita a los primeros 10 procesos para no saturar la pantalla
        comando = ['ps', '-eo', 'pid,comm,state,user', '--sort=-%cpu']
        resultado = subprocess.check_output(comando).decode('utf-8')
        lineas = resultado.strip().split('
    ')
        return "
    ".join(lineas[:15]) # Devuelve la cabecera + los 14 procesos más activos
   ```

---

## 📅 Semana 4: Concurrencia (Fork y Hilos) e Implementación del CRUD

Este es el núcleo de la materia de Sistemas Operativos. El sistema debe ser capaz de procesar hilos de manera concurrente para actualizar la información sin bloquear la interfaz y crear procesos hijos con `fork()`.

### 🛠️ Herramientas y Aplicaciones
*   **Visual Studio Code**
*   **Biblioteca estándar de Python (`threading`, `os`)**

### 📋 Pasos a Seguir

#### Paso 1: Implementar Hilos (`threading`)
1. Los hilos permiten ejecutar tareas en paralelo. Crearemos un hilo secundario que se encargue de registrar automáticamente capturas del sistema en la base de datos en segundo plano cada 30 segundos, mientras el hilo principal maneja el menú visual.
2. Añadan esto en un nuevo archivo o directamente en la lógica de integración:
   ```python
   import threading
   import time
   import datetime
   from monitor_cpu import obtener_uso_cpu_tiempo_real
   from monitor_ram import obtener_info_ram
   import sqlite3

   def background_logger():
       print("\n[Hilo Segundo Plano] Iniciado. Guardando telemetría cada 30 segundos...")
       while True:
           cpu = obtener_uso_cpu_tiempo_real()
           ram = obtener_info_ram()["usado"]
           fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           
           conn = sqlite3.connect('monitor.db')
           cursor = conn.cursor()
           cursor.execute(
               "INSERT INTO historial (fecha, cpu_uso, ram_uso, comentario) VALUES (?, ?, ?, ?)",
               (fecha, cpu, ram, "Captura automática por hilo de fondo")
           )
           conn.commit()
           conn.close()
           time.sleep(30)
   ```

#### Paso 2: Implementar Procesos (`os.fork()`)
1. El `fork()` duplica el proceso actual, creando un proceso hijo. Esto solo funciona en entornos Unix (Linux/macOS).
2. Lo usaremos cuando el usuario solicite "Exportar un Reporte Histórico" para que el proceso hijo realice la escritura en el disco mientras el proceso padre sigue respondiendo al usuario de inmediato.
   ```python
   import os
   import sys

   def exportar_reporte_con_fork():
       pid = os.fork()
       
       if pid == 0:
           # --- PROCESO HIJO ---
           print(f"\n[Proceso Hijo - PID: {os.getpid()}] Generando archivo de reporte...")
           time.sleep(2) # Simulando carga de trabajo pesada
           
           conn = sqlite3.connect('monitor.db')
           cursor = conn.cursor()
           cursor.execute("SELECT * FROM historial")
           registros = cursor.fetchall()
           
           with open('reporte_sistema.txt', 'w') as f:
               f.write("=== REPORTE HISTÓRICO DEL SISTEMA ===\n")
               for reg in registros:
                   f.write(f"ID: {reg[0]} | Fecha: {reg[1]} | CPU: {reg[2]}% | RAM: {reg[3]} GB | Nota: {reg[4]}\n")
           
           conn.close()
           print(f"[Proceso Hijo] ¡Reporte exportado como 'reporte_sistema.txt' con éxito!")
           sys.exit(0) # Termina el proceso hijo de manera limpia
       else:
           # --- PROCESO PADRE ---
           print(f"[Proceso Padre] Delegada la exportación al proceso hijo (PID: {pid}).")
           print("[Proceso Padre] Puedes seguir usando el monitor de inmediato.")
   ```

#### Paso 3: Completar las operaciones CRUD en `database.py`
Aseguren de tener las funciones correspondientes para Insertar, Leer, Modificar y Eliminar en `database.py`:
```python
# C (Create) -> Registrar una captura manual
def crear_registro(cpu, ram, comentario):
    import datetime
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO historial (fecha, cpu_uso, ram_uso, comentario) VALUES (?, ?, ?, ?)", (fecha, cpu, ram, comentario))
    conn.commit()
    conn.close()

# R (Read) -> Consultar el historial
def consultar_historial():
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historial ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos

# U (Update) -> Modificar un comentario
def actualizar_comentario(id_registro, nuevo_comentario):
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE historial SET comentario = ? WHERE id = ?", (nuevo_comentario, id_registro))
    conn.commit()
    conn.close()

# D (Delete) -> Eliminar registros
def eliminar_registro(id_registro):
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historial WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()
```

---

## 📅 Semana 5: Integración, Pruebas y Entregables Finales

El objetivo es unir todas las piezas, depurar errores, compilar el reporte en formato académico e iniciar el proceso de defensa.

### 🛠️ Herramientas y Aplicaciones
*   **Visual Studio Code** (Menú de consola e integración)
*   **Overleaf / LaTeX** (Plantilla IEEE de Artículo Científico)
*   **OBS Studio** en Linux (Grabación de video demostrativo)
*   **Google Slides / Canva** (Presentación de diapositivas)

### 📋 Pasos a Seguir

#### Paso 1: Interfaz Principal en `main.py`
Junten el hilo en segundo plano, las lecturas y el menú en un único archivo ejecutable:
```python
import os
import threading
from monitor_cpu import obtener_info_cpu, obtener_uso_cpu_tiempo_real
from monitor_ram import obtener_info_ram
from monitor_sistema import obtener_uso_disco, obtener_usuarios_conectados, obtener_procesos
from database import init_db, crear_registro, consultar_historial, actualizar_comentario, eliminar_registro
from background_worker import background_logger, exportar_reporte_con_fork # supuestas funciones organizadas

def mostrar_telemetria_actual():
    os.system('clear')
    print("================ TELEMETRÍA EN TIEMPO REAL ================")
    cpu_info = obtener_info_cpu()
    print(f"CPU: {cpu_info['modelo']} ({cpu_info['nucleos']} núcleos)")
    print(f"Uso de CPU: {obtener_uso_cpu_tiempo_real()}%")
    
    ram = obtener_info_ram()
    print(f"RAM: Usada {ram['usado']} GB / Total {ram['total']} GB")
    
    disco = obtener_uso_disco()
    print(f"Disco (Raíz /): Usado {disco['usado']} / Total {disco['total']} ({disco['porcentaje']})")
    
    print("\nÚltimos procesos en ejecución:")
    print(obtener_procesos())
    input("\nPresione Enter para regresar al menú principal...")

def menu_crud():
    while True:
        os.system('clear')
        print("=== ADMINISTRACIÓN DE CAPTURAS (CRUD) ===")
        print("1. Guardar captura manual actual")
        print("2. Ver historial de capturas")
        print("3. Modificar comentario de captura")
        print("4. Eliminar registro de captura")
        print("5. Volver")
        opc = input("Seleccione: ")
        
        if opc == '1':
            cpu = obtener_uso_cpu_tiempo_real()
            ram = obtener_info_ram()["usado"]
            nota = input("Ingrese un comentario para esta captura: ")
            crear_registro(cpu, ram, nota)
            print("Captura almacenada con éxito.")
            time.sleep(1.5)
        elif opc == '2':
            print("\n--- HISTORIAL ---")
            for reg in consultar_historial():
                print(f"ID: {reg[0]} | Fecha: {reg[1]} | CPU: {reg[2]}% | RAM: {reg[3]} GB | Nota: {reg[4]}")
            input("\nPresione Enter para continuar...")
        elif opc == '3':
            id_reg = int(input("Ingrese el ID de la captura a modificar: "))
            nueva_nota = input("Nuevo comentario: ")
            actualizar_comentario(id_reg, nueva_nota)
            print("Comentario actualizado.")
            time.sleep(1)
        elif opc == '4':
            id_reg = int(input("ID de captura a eliminar: "))
            eliminar_registro(id_reg)
            print("Registro eliminado.")
            time.sleep(1)
        elif opc == '5':
            break

def main():
    init_db()
    
    # Iniciar el hilo de fondo para auto-guardado
    t = threading.Thread(target=background_logger, daemon=True)
    t.start()
    
    while True:
        os.system('clear')
        print("================ MINI MONITOR DE RECURSOS - LINUX ================")
        print("1. Mostrar telemetría actual")
        print("2. Administrar capturas históricas (CRUD)")
        print("3. Exportar Reporte Histórico (Uso de Fork)")
        print("4. Salir")
        opcion = input("Seleccione una opción: ")
        
        if opcion == '1':
            mostrar_telemetria_actual()
        elif opcion == '2':
            menu_crud()
        elif opcion == '3':
            exportar_reporte_con_fork()
            input("\nPresione Enter para continuar...")
        elif opcion == '4':
            print("Saliendo de la aplicación.")
            break

if __name__ == '__main__':
    main()
```

#### Paso 2: Redacción del Artículo IEEE
1. Ingresen a [Overleaf](https://www.overleaf.com/).
2. Creen un proyecto vacío y suban la plantilla oficial de la IEEE (*IEEE Conference Template*).
3. Redacten utilizando la estructura requerida:
   * **Resumen / Abstract:** Describan brevemente que crearon un monitor en Python usando el sistema de archivos `/proc`, hilos concurrentes y procesos paralelos (`fork()`).
   * **Metodología:** Expliquen el acceso a `/proc/stat` y `/proc/meminfo`.
   * **Resultados:** Adjunten capturas de pantalla de la terminal mostrando el monitor funcionando en tiempo real y el archivo de base de datos SQLite con los datos.

#### Paso 3: Grabación del Video Demostrativo
1. Instalen **OBS Studio** en su sistema Ubuntu / Linux:
   ```bash
   sudo apt update
   sudo apt install obs-studio
   ```
2. Configuren el lienzo en resolución **Full HD (1920x1080)** o **4K**, de forma **horizontal**.
3. Graben de forma fluida:
   * **Minutos 0-3:** Explicación del código fuente enfocado en los puntos obligatorios (`fork`, `threading`, lectura de `/proc`).
   * **Minutos 3-7:** Demostración en vivo en la terminal. Muestren cómo las lecturas de CPU varían, cómo se crean registros en la base de datos (CRUD) y cómo el hilo en segundo plano va agregando datos sin detener el sistema.

#### Paso 4: Presentación y Defensa (Diapositivas)
1. Usen **Canva** o **Google Slides** con un diseño formal y colores sobrios (azul marino, gris oscuro, verde oliva).
2. Estructuren exactamente en **10 diapositivas** para no exceder los 7 minutos de exposición asignados.
3. Practiquen las preguntas técnicas de la sustentación, especialmente sobre el funcionamiento de la tabla de descriptores de archivos al hacer `fork()` y cómo la concurrencia puede producir condiciones de carrera si dos hilos intentaran escribir al mismo archivo de base de datos a la vez sin un semáforo o bloqueo.
