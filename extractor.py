import requests
import mysql.connector
import time
from config import DB_CONFIG, API_CONFIG

def obtener_valor_stat(lista_estadisticas, tipo_stat):
    for item in lista_estadisticas:
        if item['type'] == tipo_stat:
            return int(item['value']) if item['value'] is not None else 0
    return 0

def ejecutar_extractor():
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor()
        
        cursor.execute("SELECT id_fixture FROM partidos_historicos")
        ids_existentes = {fila[0] for fila in cursor.fetchall()}
        
        print("Descargando calendario completo de la Champions League...")
        response = requests.get(API_CONFIG['url'], headers=API_CONFIG['headers'], params=API_CONFIG['params'])
        datos = response.json()
        
        todos_los_terminados = [p for p in datos.get('response', []) if p['fixture']['status']['short'] == 'FT']
        partidos_pendientes = [p for p in todos_los_terminados if p['fixture']['id'] not in ids_existentes]
        
        if not partidos_pendientes:
            print("¡Tu base de datos está 100% actualizada!")
            return

        print(f"Faltan {len(partidos_pendientes)} partidos por descargar.")
        
        lote_a_procesar = partidos_pendientes[:90]
        print(f"Procesando lote de {len(lote_a_procesar)} partidos hoy...\n")

        insertados = 0
        sql = """
            INSERT IGNORE INTO partidos_historicos 
            (id_fixture, fecha, competicion, equipo_local, equipo_visitante, 
            goles_local, goles_visitante, remates_arco_local, remates_arco_visitante, 
            corners_local, corners_visitante, amarillas_local, amarillas_visitante, 
            rojas_local, rojas_visitante) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for p in lote_a_procesar:
            id_fixture = p['fixture']['id']
            fecha = p['fixture']['date'][:10]
            local = p['teams']['home']['name']
            visitante = p['teams']['away']['name']
            gl, gv = p['goals']['home'], p['goals']['away']
            
            print(f"Procesando: {local} vs {visitante}...")
            
            url_stats = "https://v3.football.api-sports.io/fixtures/statistics"
            res_stats = requests.get(url_stats, headers=API_CONFIG['headers'], params={"fixture": id_fixture})
            datos_crudos_stats = res_stats.json()
            
            # Nuevo Hard Stop: Solo se detiene si la API escupe un error real de bloqueo
            if 'errors' in datos_crudos_stats and datos_crudos_stats['errors']:
                print(f"\n⚠️ ALERTA API: {datos_crudos_stats['errors']}")
                print("Deteniendo ejecución para proteger la base de datos.")
                break
                
            datos_stats = datos_crudos_stats.get('response', [])
            remates_L = remates_V = corners_L = corners_V = amarillas_L = amarillas_V = rojas_L = rojas_V = 0

            # Tolerancia a fallos: Si la API no tiene stats de este partido, pasará de largo y guardará ceros
            if not datos_stats:
                print(" -> (Sin estadísticas avanzadas. Guardando solo goles)")
            elif len(datos_stats) == 2:
                stats_L, stats_V = datos_stats[0]['statistics'], datos_stats[1]['statistics']
                
                remates_L, remates_V = obtener_valor_stat(stats_L, 'Shots on Goal'), obtener_valor_stat(stats_V, 'Shots on Goal')
                corners_L, corners_V = obtener_valor_stat(stats_L, 'Corner Kicks'), obtener_valor_stat(stats_V, 'Corner Kicks')
                amarillas_L, amarillas_V = obtener_valor_stat(stats_L, 'Yellow Cards'), obtener_valor_stat(stats_V, 'Yellow Cards')
                rojas_L, rojas_V = obtener_valor_stat(stats_L, 'Red Cards'), obtener_valor_stat(stats_V, 'Red Cards')
            
            valores = (id_fixture, fecha, p['league']['name'], local, visitante, gl, gv, 
                       remates_L, remates_V, corners_L, corners_V, amarillas_L, amarillas_V, rojas_L, rojas_V)
            
            cursor.execute(sql, valores)
            if cursor.rowcount > 0:
                insertados += 1
            
            time.sleep(6.5)
        
        conexion.commit()
        print(f"\nProceso finalizado. {insertados} nuevos partidos guardados.")

    except Exception as e:
        print(f"Error en la ejecución: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    ejecutar_extractor()