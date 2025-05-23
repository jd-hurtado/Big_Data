import happybase
import pandas as pd

try:
    # 1. Establecer conexión con HBase
    connection = happybase.Connection('localhost')
    print("Conexión establecida con HBase")
    
    # 2. Crear la tabla con las familias de columnas  
    table_name = 'analisis_redes'
    families = {
        'info': dict(),      # Información general de la actividad
        'video': dict(),     # Informacion relacionada a la interaccion con videos
        'details': dict()    # Detalles específicos de interacciones, publicaciones y demas
    }
    
    # Eliminar la tabla si ya existe
    if table_name.encode() in connection.tables():
        print(f"Eliminando tabla existente - {table_name}")
        connection.delete_table(table_name, disable=True)

    # Crear nueva tabla
    connection.create_table(table_name, families)
    table = connection.table(table_name)
    print(f"Tabla '{table_name}' creada exitosamente")

    # 3. Cargar datos desde un CSV
    csv_file_path = 'Redes_Sociales.csv'
    activity_data = pd.read_csv(csv_file_path)

    for _, row in activity_data.iterrows():
        row_key = str(row['activity_id']).encode()
        data = {
            b'info:user_id': str(row['user_id']).encode(),
            b'info:platform': str(row['platform']).encode(),
            b'info:type': str(row['type']).encode(),
            b'info:duration_seconds': str(row['duration_seconds']).encode(),
            b'info:search_term': str(row['search_term']).encode(),
            b'info:date': str(row['date']).encode(),
            b'video:video_id': str(row['details_video_id']).encode(),
            b'video:title': str(row['details_title']).encode(),
            b'details:post_id': str(row['details_post_id']).encode(),
            b'details:content': str(row['details_content']).encode(),
            b'details:reaction_type': str(row['details_reaction_type']).encode()
        }
        table.put(row_key, data)

    print("Datos cargados exitosamente")

    
    # === CONSULTAS DE LA ACTIVIDAD ===

    # 	CONSULTAS DE SELECCIÓN, FILTRADO Y RECORRIDO SOBRE LOS DATOS. 
    # 1. Consultas y Análisis de Datos (Se consultan 5 datos de cada actividad)
    print("\n=== Primeras 3 actividades en la base de datos ===")
    count = 0
    for key, data in table.scan():
        if count < 3:
            print(f"\nActividad ID: {key.decode()}")
            print(f"Usuario: {data[b'info:user_id'].decode()}")
            print(f"Plataforma: {data[b'info:platform'].decode()}")
            print(f"Tipo de actividad: {data[b'info:type'].decode()}")
            print(f"Fecha: {data[b'info:date'].decode()}")
            count += 1

    # 2. Consultas y Análisis de Datos (Se consultan 3 datos de cada actividad)
    print("\n=== Primeras 10 actividades cargadas en la base de datos ===")
    count = 0
    for key, data in table.scan(limit=10):
        print(f"Actividad ID: {key.decode()}, Tipo: {data[b'info:type'].decode()}, Plataforma: {data[b'info:platform'].decode()}")
        count += 1

    # 3. Actividades de tipo 'reaction' (Busca todos los registros que tengan una reaccion (details_reaction_type))
    print("\n=== Actividades con detalles de reaccion en la publicación ===")
    for key, data in table.scan():
        if data[b'info:type'].decode() == 'reaction':
            print(f"\nID: {key.decode()} | Usuario: {data[b'info:user_id'].decode()} | Plataforma: {data[b'info:platform'].decode()}")
            if b'details:reaction_type' in data:
                print(f"Tipo de reacción: {data[b'details:reaction_type'].decode()}")

    # 4. Filtrar actividades de tipo 'search' (Se filtran todas las actividades que hayan buscado algo en las redes)
    print("\n=== Consultas: Filtrar actividades tipo 'search' ===")
    for key, data in table.scan(filter=b"SingleColumnValueFilter('info', 'type', =, 'binary:search')"):
        print(f"Actividad ID: {key.decode()}, Término buscado: {data.get(b'info:search_term', b'').decode()}")

    # 5. Filtrar actividades realizadas en 'YouTube'
    print("\n=== Consultas: Filtrar actividades en 'YouTube' ===")
    for key, data in table.scan(filter=b"SingleColumnValueFilter('info', 'platform', =, 'binary:YouTube')"):
        print(f"Actividad ID: {key.decode()}, Usuario: {data.get(b'info:user_id', b'').decode()}")

    # 6. Actividades con duración mayor a 400 segundos
    print("\n=== Actividades con una duración mayor a 400 segundos ===")
    for key, data in table.scan():
        duration = int(data.get(b'info:duration_seconds', b'0').decode())
        if duration > 400:
            print(f"\nID: {key.decode()} | Plataforma: {data[b'info:platform'].decode()} | Duración: {duration}")

    # 7. Conteo de actividades por plataforma en la base de datos (YouTube, Instagram, Facebook, Twitter)
    print("\n=== Conteo de actividades por plataforma ===")
    platform_stats = {}
    for key, data in table.scan():
        platform = data[b'info:platform'].decode()
        platform_stats[platform] = platform_stats.get(platform, 0) + 1

    for platform, total in platform_stats.items():
        print(f"{platform}: {total} actividades")

    # 8. Promedio de duración en segundos por tipo de actividad (Busqueda, Tiempo de visulización, Comentario, Reacción)
    print("\n=== Duración promedio por tipo de actividad ===")
    durations = {}
    counts = {}

    for key, data in table.scan():
        activity_type = data[b'info:type'].decode()
        duration = int(data.get(b'info:duration_seconds', b'0').decode())
        durations[activity_type] = durations.get(activity_type, 0) + duration
        counts[activity_type] = counts.get(activity_type, 0) + 1

    for activity_type in durations:
        avg = durations[activity_type] / counts[activity_type]
        print(f"{activity_type}: {avg:.2f} segundos")

    # OPERACIONES DE ESCRITURA ACTUALIZACIONES
    # 9. Actualizar un contenido específico de una actividad
    print("\n=== Actualizando contenido de post para la actividad A005 ===")
    table.put(b'A005', {
        b'details:content': b'Contenido actualizado: Excelente'
    })
    print("Contenido actualizado correctamente.")

    # 10. Actualización de una reaccion a una actividad
    print("\n=== Actualización de una reacción a una actividad existente ===")
    table.put(b'activity_002', {b'details:reaction_type': b'love'})
    print("Reacción actualizada correctamente: activity_002")

    # 11. Consulta para verificar actualización de la reacción
    print("\n=== Verificar actualización ===")
    updated_row = table.row(b'activity_002')
    print(f"Detalles después de actualización: {updated_row.get(b'details:reaction_type', b'').decode()}")

    # 12. Eliminar una reacción realizada a un post por un usuario
    print("\n=== Eliminando tipo de reacción del post en la actividad A009 ===")
    table.delete(b'A009', columns=[b'details:reaction_type'])
    print("Reacción eliminada.")
    
    # OPERACIONES DE ESCRITURA INSERCIONES
    # 13. Inserción de una nueva actividad a la base de datos
    print("\n=== Inserción de nueva actividad ===")
    new_activity = {
        b'info:user_id': b'new_user_01',
        b'info:platform': b'Instagram',
        b'info:type': b'like',
        b'info:date': b'2025-10-05T12:00:00',
        b'details:post_id': b'P100',
        b'details:reaction_type': b'like'
    }
    table.put(b'activity_101', new_activity)
    print("Nueva actividad insertada: activity_101")

    # OPERACIONES DE ESCRITURA ELIMINACIÓN
    # 14. Consulta previa a la eliminación
    print("\n=== Consulta previa a eliminación ===")
    row = table.row(b'activity_101')
    print(f"Datos antes de eliminar: {row}")

    # 15. Eliminación
    print("\n=== Eliminación de la actividad ===")
    table.delete(b'activity_101')
    print("Actividad eliminada: activity_101")

    # 16. Consulta posterior a la eliminación
    print("\n=== Consulta posterior a eliminación ===")
    row = table.row(b'activity_101')
    if not row:
        print("La actividad no existe, confirmación de eliminación.")
    else:
        print(f"Datos encontrados: {row}")

except Exception as e:
    print(f"Error al ejecutar el script: {e}")

finally:
    # Cerrar la conexión con HBase
    connection.close()
    print("Conexión cerrada")
