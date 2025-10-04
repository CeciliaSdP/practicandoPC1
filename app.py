import streamlit as st
from dataclasses import dataclass, asdict
from datetime import time, datetime
from typing import List, Dict
import hashlib

# -------------------------
# Configuración de página
# -------------------------
st.set_page_config(
    page_title="Horario – Streamlit",
    page_icon="🗓️",
    layout="wide"
)

st.title("🗓️ Horario semanal (demo sin dataset)")
st.caption("Agrega actividades desde la barra lateral y visualízalas en un horario semanal básico.")

# -------------------------
# Modelo simple de actividad
# -------------------------
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

@dataclass
class Actividad:
    dia: str                 # Uno de DIAS
    titulo: str              # p. ej., "PLE B1"
    inicio: time             # hora de inicio
    fin: time                # hora de fin
    lugar: str = ""          # opcional
    nota: str = ""           # opcional

def _hex_color_from_text(text: str) -> str:
    """
    Genera un color pastel basado en el título para diferenciar actividades.
    """
    h = hashlib.md5(text.encode()).hexdigest()
    # Tomamos 3 bytes y los llevamos a una paleta pastel
    r = (int(h[0:2], 16) + 200) // 2
    g = (int(h[2:4], 16) + 200) // 2
    b = (int(h[4:6], 16) + 200) // 2
    return f"#{r:02x}{g:02x}{b:02x}"

def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def _overlaps(hh: int, act: Actividad) -> bool:
    """
    Indica si la actividad toca la franja [hh:00, hh+1:00).
    """
    start = _to_minutes(act.inicio)
    end = _to_minutes(act.fin)
    block_start = hh * 60
    block_end = (hh + 1) * 60
    return (start < block_end) and (end > block_start)

# -------------------------
# Estado
# -------------------------
if "actividades" not in st.session_state:
    # Ejemplo inicial (puedes borrar)
    st.session_state.actividades: List[Actividad] = [
        Actividad("Lunes", "PLE B1", time(9, 0), time(11, 0), "Aula 3"),
        Actividad("Martes", "Reunión equipo", time(15, 0), time(16, 0), "Zoom"),
        Actividad("Viernes", "Oficina PLE", time(10, 30), time(12, 0), "IGR Lima"),
    ]

# -------------------------
# Sidebar: formulario
# -------------------------
st.sidebar.header("➕ Agregar actividad")
with st.sidebar.form("form_actividad", clear_on_submit=False):
    dia = st.selectbox("Día", DIAS, index=0)
    col1, col2 = st.columns(2)
    with col1:
        inicio = st.time_input("Inicio", value=time(9, 0), step=300)
    with col2:
        fin = st.time_input("Fin", value=time(10, 0), step=300)
    titulo = st.text_input("Título", value="Clase/Evento")
    lugar = st.text_input("Lugar (opcional)", value="")
    nota = st.text_area("Nota (opcional)", value="", height=70)
    agregar = st.form_submit_button("Agregar")

if agregar:
    if fin <= inicio:
        st.sidebar.error("La hora de fin debe ser mayor que la de inicio.")
    else:
        st.session_state.actividades.append(
            Actividad(dia, titulo.strip(), inicio, fin, lugar.strip(), nota.strip())
        )
        st.sidebar.success("Actividad agregada ✅")

if st.sidebar.button("🗑️ Limpiar horario"):
    st.session_state.actividades.clear()
    st.sidebar.info("Horario vacío.")

# -------------------------
# Parámetros de vista
# -------------------------
st.subheader("Vista del horario")
colA, colB, colC = st.columns([1.2, 1, 1.2])
with colA:
    start_hour = st.number_input("Hora inicio del día", min_value=5, max_value=12, value=7, step=1)
with colB:
    end_hour = st.number_input("Hora fin del día", min_value=13, max_value=23, value=21, step=1)
with colC:
    grid_step = st.selectbox("Granularidad (para etiquetas internas)", ["1h"], index=0)

HORAS = list(range(int(start_hour), int(end_hour)))

# -------------------------
# Render HTML (tabla)
# -------------------------
def render_horario(acts: List[Actividad]) -> str:
    """
    Genera una tabla HTML con días en columnas y horas en filas.
    En cada celda, muestra chips de actividades que cruzan esa hora.
    """
    # Indexar por día
    por_dia: Dict[str, List[Actividad]] = {d: [] for d in DIAS}
    for a in acts:
        por_dia[a.dia].append(a)

    # CSS básico
    css = """
    <style>
      .tbl { width: 100%; border-collapse: collapse; table-layout: fixed; font-family: Inter, system-ui, sans-serif; }
      .tbl th, .tbl td { border: 1px solid #e5e7eb; padding: 6px; vertical-align: top; }
      .tbl th { background: #f8fafc; font-weight: 600; }
      .hour { width: 70px; text-align: right; color: #64748b; white-space: nowrap; }
      .chip {
          display: inline-block; padding: 4px 8px; margin: 2px 2px;
          border-radius: 8px; font-size: 12px; line-height: 1.1;
          border: 1px solid rgba(0,0,0,0.05);
      }
      .chip small { display: block; color: rgba(0,0,0,0.6); font-size: 10px; }
      .cell { min-height: 40px; }
    </style>
    """

    # Encabezado
    html = css + "<table class='tbl'>"
    html += "<thead><tr><th class='hour'>Hora</th>"
    for d in DIAS:
        html += f"<th>{d}</th>"
    html += "</tr></thead><tbody>"

    # Filas por hora
    for hh in HORAS:
        etiqueta = f"{hh:02d}:00"
        html += f"<tr><td class='hour'><b>{etiqueta}</b></td>"
        for d in DIAS:
            # Actividades que cruzan la franja de esta hora y este día
            celdas = []
            for a in por_dia[d]:
                if _overlaps(hh, a):
                    col = _hex_color_from_text(a.titulo or "x")
                    rango = f"{a.inicio.strftime('%H:%M')}–{a.fin.strftime('%H:%M')}"
                    subt = a.lugar if a.lugar else a.nota
                    subline = f"<small>{rango}" + (f" · {subt}</small>" if subt else "</small>")
                    chip = f"<span class='chip' style='background:{col};'>{a.titulo}{subline}</span>"
                    celdas.append(chip)
            html += f"<td class='cell'>{''.join(celdas)}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

st.markdown(render_horario(st.session_state.actividades), unsafe_allow_html=True)

# -------------------------
# Descarga JSON (opcional)
# -------------------------
st.divider()
st.write("💾 **Exporta/respáldalo** (opcional):")
if st.button("Exportar horario a JSON"):
    import json
    data = [asdict(a) for a in st.session_state.actividades]
    st.download_button("Descargar JSON", data=json.dumps(data, ensure_ascii=False, indent=2), file_name="horario.json", mime="application/json")
