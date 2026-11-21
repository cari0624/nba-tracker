import streamlit as st
import pandas as pd
from datetime import datetime
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

st.set_page_config(page_title="NBA Tracker", page_icon="🏀", layout="wide")

st.markdown("""
<style>
    .stApp {background: #0b1220;}
    [data-testid="stMetric"] {background: #111c2f; padding: 14px; border-radius: 12px;}
    h1, h2, h3 {color: #f5f7fb;}
</style>
""", unsafe_allow_html=True)

def current_nba_season():
    now = datetime.now()
    start = now.year if now.month >= 10 else now.year - 1
    return f"{start}-{str(start + 1)[-2:]}"

@st.cache_data(ttl=60, show_spinner=False)
def get_live_games():
    data = scoreboard.ScoreBoard().get_dict()
    # NBA live scoreboard commonly returns scoreboard.games.game
    games = data.get("scoreboard", {}).get("games", {}).get("game", [])
    if isinstance(games, dict):
        games = [games]
    rows = []
    for g in games:
        home = g.get("homeTeam", {})
        away = g.get("awayTeam", {})
        rows.append({
            "Visitante": f'{away.get("teamCity","")} {away.get("teamName","")}'.strip(),
            "Marcador": f'{away.get("score","-")} - {home.get("score","-")}',
            "Local": f'{home.get("teamCity","")} {home.get("teamName","")}'.strip(),
            "Estado": g.get("gameStatusText", g.get("gameStatus", "—")),
            "Periodo": g.get("period", "—"),
            "Reloj": g.get("gameClock", "—"),
        })
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600, show_spinner=False)
def find_player(name):
    matches = players.find_players_by_full_name(name)
    return matches

@st.cache_data(ttl=900, show_spinner=False)
def get_player_logs(player_id, season):
    endpoint = playergamelog.PlayerGameLog(
        player_id=player_id,
        season=season,
        season_type_all_star="Regular Season",
        timeout=30
    )
    return endpoint.get_data_frames()[0]

st.title("🏀 NBA TRACKER")
st.caption("Resultados, triples y tendencias de jugadores | Primera versión")

with st.sidebar:
    st.header("Controles")
    st.write(f"Temporada seleccionada: **{current_nba_season()}**")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Los marcadores se guardan en caché durante 60 segundos. La fuente NBA puede limitar solicitudes.")

tab_live, tab_player, tab_guide = st.tabs(["🔴 Resultados en vivo", "🎯 Jugadores y triples", "ℹ️ Acerca del proyecto"])

with tab_live:
    st.subheader("Marcadores de hoy")
    st.caption("Los partidos y estados se consultan desde el marcador en vivo de NBA.com.")
    try:
        games = get_live_games()
        if games.empty:
            st.info("No aparecen partidos en vivo o programados en este momento. Prueba de nuevo más tarde.")
        else:
            st.dataframe(games, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("No se pudieron cargar los marcadores. La fuente puede estar temporalmente no disponible o limitar solicitudes.")
        st.caption(f"Detalle técnico: {type(e).__name__}: {e}")

with tab_player:
    st.subheader("Historial y análisis de triples")
    player_name = st.text_input("Escribe el nombre de un jugador (por ejemplo: Stephen Curry)", value="Stephen Curry")
    season = st.text_input("Temporada NBA", value=current_nba_season(), help="Ejemplo: 2026-27")
    if st.button("Buscar estadísticas", type="primary"):
        with st.spinner("Consultando estadísticas..."):
            try:
                matches = find_player(player_name)
                active = [p for p in matches if p.get("is_active")]
                chosen = active[0] if active else (matches[0] if matches else None)
                if not chosen:
                    st.warning("No encontramos ese jugador. Revisa la escritura del nombre.")
                else:
                    st.session_state["nba_player_id"] = chosen["id"]
                    st.session_state["nba_player_name"] = chosen["full_name"]
                    st.session_state["nba_season"] = season
            except Exception as e:
                st.error("No se pudo buscar el jugador. Intenta nuevamente más tarde.")
                st.caption(f"Detalle técnico: {type(e).__name__}: {e}")

    if "nba_player_id" in st.session_state:
        try:
            logs = get_player_logs(st.session_state["nba_player_id"], st.session_state["nba_season"])
            if logs.empty:
                st.info("Todavía no hay registros para este jugador y temporada.")
            else:
                st.markdown(f"### {st.session_state['nba_player_name']}")
                logs = logs.copy()
                for col in ["FG3M", "FG3A", "PTS", "REB", "AST", "MIN"]:
                    if col in logs.columns:
                        logs[col] = pd.to_numeric(logs[col], errors="coerce")
                last5 = logs.head(5)
                last10 = logs.head(10)
                avg5 = last5["FG3M"].mean() if "FG3M" in last5 else 0
                avg10 = last10["FG3M"].mean() if "FG3M" in last10 else 0
                pct5 = (last5["FG3M"].sum() / last5["FG3A"].sum() * 100) if last5["FG3A"].sum() else 0
                c1, c2, c3 = st.columns(3)
                c1.metric("Triples promedio · últimos 5", f"{avg5:.2f}")
                c2.metric("Triples promedio · últimos 10", f"{avg10:.2f}")
                c3.metric("Efectividad 3PT · últimos 5", f"{pct5:.1f}%")

                threshold = st.select_slider("Evaluar línea de triples", options=[1, 2, 3, 4, 5], value=2)
                hits5 = int((last5["FG3M"] >= threshold).sum())
                hits10 = int((last10["FG3M"] >= threshold).sum())
                a, b = st.columns(2)
                a.metric(f"Partidos con {threshold}+ triples · últimos 5", f"{hits5}/5")
                b.metric(f"Partidos con {threshold}+ triples · últimos 10", f"{hits10}/10")
                st.caption("Frecuencia histórica, no probabilidad garantizada para el próximo partido.")
                show_cols = [c for c in ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "FG3M", "FG3A", "FG3_PCT", "REB", "AST"] if c in logs.columns]
                st.markdown("#### Últimos partidos")
                st.dataframe(logs[show_cols].head(10), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error("No se pudieron cargar los registros del jugador. Verifica la temporada y vuelve a intentarlo.")
            st.caption(f"Detalle técnico: {type(e).__name__}: {e}")

with tab_guide:
    st.subheader("Qué incluye esta primera versión")
    st.markdown("""
    - Marcadores consultados desde el feed en vivo de NBA.com.
    - Búsqueda de jugadores.
    - Historial de los últimos 5 y 10 partidos.
    - Promedio de triples y porcentaje de acierto.
    - Frecuencia con la que alcanza una línea de triples elegida.

    **Importante:** esta versión usa `nba_api`, una biblioteca comunitaria que consulta servicios de NBA.com. No es un servicio oficial con garantía de disponibilidad. Puede haber interrupciones, límites de solicitudes o cambios en los endpoints. Para un producto comercial o datos en vivo con SLA, conviene evaluar un proveedor con licencia como Sportradar.
    """)
    st.markdown("**Próximas mejoras:** calendario por fecha, lesiones y disponibilidad, comparación entre jugadores, base de datos histórica y predicciones calibradas.")
    st.caption("NBA Tracker · Prototipo personal")

st.divider()
st.caption("Los datos estadísticos son informativos. Las tendencias pasadas no garantizan resultados futuros.")
