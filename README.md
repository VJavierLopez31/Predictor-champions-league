**Motor Estadístico Predictivo - UEFA Champions League:**

Este proyecto es un sistema integral de extracción de datos (ETL) y análisis predictivo para el fútbol europeo. Utiliza la Distribución de Poisson para calcular las probabilidades conjuntas de mercados deportivos (1X2, Over/Under de Goles, Córneres, Remates al Arco y Tarjetas) basándose en los rendimientos históricos a lo largo de una temporada completa.

**Arquitectura y Tecnologías:**

El sistema está dividido en una arquitectura de 3 capas (Extracción, Almacenamiento y Presentación), separando la lógica de recolección de datos de la interfaz de usuario:

* Lenguaje: Python 3.x
* Base de Datos: MySQL (Almacenamiento local para evadir la latencia y los límites de cuota de la API).
* Frontend: Streamlit (Despliegue de dashboard web interactivo y reactivo).
* Fuente de Datos: API-Sports (RESTful API).

**Características Técnicas Destacadas:**

* Pipeline ETL con Tolerancia a Fallos: El script extractor.py implementa un sistema de memoria (consultando primero la base de datos) para descargar únicamente partidos faltantes. Posee un manejo estricto de Rate Limiting (pausas estratégicas y procesamiento por lotes) y tolerancia a fallos ante nodos de datos vacíos (común en rondas preliminares).
* Modelo Probabilístico Dinámico: En lugar de promediar equipos aislados, el motor calcula el valor lambda (promedio de eventos esperados) de cada equipo frente a toda la liga, eliminando sesgos analíticos.
* Validación de Entradas: La interfaz web extrae dinámicamente los equipos disponibles directamente de la base de datos MySQL, impidiendo errores de tipeo y fallos de ejecución.

