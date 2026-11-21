# NBA Tracker — Versión 1.0

Aplicación web inicial en español para consultar marcadores y estadísticas de triples.

## Archivos
- `app.py`: aplicación Streamlit.
- `requirements.txt`: dependencias necesarias.

## Cómo ejecutarla en Windows
1. Instala Python 3.10 o superior desde https://www.python.org/downloads/
2. Descomprime esta carpeta.
3. Abre la carpeta, haz clic en la barra de dirección del Explorador, escribe `cmd` y pulsa Enter.
4. Ejecuta:
   `py -m pip install -r requirements.txt`
5. Luego ejecuta:
   `py -m streamlit run app.py`
6. Se abrirá la aplicación en el navegador.

## Publicarla en internet
La opción sencilla para comenzar es Streamlit Community Cloud:
https://share.streamlit.io/
Necesitarás una cuenta de GitHub y subir `app.py` y `requirements.txt` a un repositorio. En Streamlit Community Cloud elige ese repositorio y `app.py` como archivo principal.

## Limitaciones conocidas
- `nba_api` es un proyecto comunitario que consulta endpoints de NBA.com. NBA.com puede limitar solicitudes o cambiar sus servicios.
- Los marcadores se almacenan en caché durante 60 segundos; el botón Actualizar fuerza una nueva consulta.
- El historial de jugadores consulta la temporada indicada en pantalla. Si la temporada aún no tiene partidos o el endpoint no responde, no habrá datos.
- Las predicciones todavía no son pronósticos probabilísticos. Esta versión muestra promedios y frecuencia histórica de cumplimiento de líneas.
- No introducir credenciales ni claves privadas en `app.py`.
