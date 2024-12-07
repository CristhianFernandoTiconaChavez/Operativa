import streamlit as st
from pyvis.network import Network
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import tempfile

# Configurar la página
st.set_page_config(
    page_title="Problema de Transporte",  # Título que aparece en la pestaña
    page_icon="🚌",  # Ícono en la pestaña (puedes usar emojis o un archivo .ico)
    layout="wide",  # Opciones: "centered" (centrado) o "wide" (ancho completo)
    initial_sidebar_state="expanded"  # Opciones: "expanded", "collapsed", "auto"
)

#################################################################################
# FUNCIONES 
#################################################################################

def resolver_problema_transporte(costos, oferta, demanda):
    num_origenes = len(oferta)
    num_destinos = len(demanda)
    problema = LpProblem("Problema_Transporte", LpMinimize)
    variables = [[LpVariable(f"x_{i}_{j}", lowBound=0) for j in range(num_destinos)] for i in range(num_origenes)]
    problema += lpSum(costos[i][j] * variables[i][j] for i in range(num_origenes) for j in range(num_destinos))
    for i in range(num_origenes):
        problema += lpSum(variables[i][j] for j in range(num_destinos)) <= oferta[i], f"Oferta_{i}"
    for j in range(num_destinos):
        problema += lpSum(variables[i][j] for i in range(num_origenes)) >= demanda[j], f"Demanda_{j}"
    problema.solve()
    return {
        "estado": LpStatus[problema.status],
        "costo_total": problema.objective.value(),
        "variables": {(i, j): variables[i][j].varValue for i in range(num_origenes) for j in range(num_destinos)}
    }

#################################################################################
# SIDEBAR
#################################################################################

st.sidebar.title("Nodos")

# Configurar nodos
num_origenes = st.sidebar.number_input("Número de orígenes", min_value=1, value=3)
num_destinos = st.sidebar.number_input("Número de destinos", min_value=1, value=3)
origenes = [f"Origen {i+1}" for i in range(num_origenes)]
destinos = [f"Destino {j+1}" for j in range(num_destinos)]

# Matriz de costos inicial (con corrección)
if "matriz_costos" not in st.session_state or len(st.session_state["matriz_costos"]) != num_origenes:
    st.session_state["matriz_costos"] = [[float('inf')] * num_destinos for _ in range(num_origenes)]
else:
    # Ajustar dinámicamente la matriz si cambian los destinos
    for fila in st.session_state["matriz_costos"]:
        if len(fila) < num_destinos:
            fila.extend([float('inf')] * (num_destinos - len(fila)))
        elif len(fila) > num_destinos:
            del fila[num_destinos:]
    if len(st.session_state["matriz_costos"]) < num_origenes:
        st.session_state["matriz_costos"].extend(
            [[float('inf')] * num_destinos for _ in range(num_origenes - len(st.session_state["matriz_costos"]))]
        )
    elif len(st.session_state["matriz_costos"]) > num_origenes:
        del st.session_state["matriz_costos"][num_origenes:]

# Configuración de rutas
st.sidebar.title("Rutas")
origen_seleccionado = st.sidebar.selectbox("Seleccionar nodo de origen", origenes)
destino_seleccionado = st.sidebar.selectbox("Seleccionar nodo de destino", destinos)
costo = st.sidebar.number_input("Costo de la ruta", min_value=0.0, step=0.1)

if "rutas" not in st.session_state:
    st.session_state["rutas"] = []

if st.sidebar.button("Agregar ruta"):
    indice_origen = origenes.index(origen_seleccionado)
    indice_destino = destinos.index(destino_seleccionado)
    st.session_state["rutas"].append((origen_seleccionado, destino_seleccionado, costo))
    st.session_state["matriz_costos"][indice_origen][indice_destino] = costo
    st.sidebar.success(f"Ruta de {origen_seleccionado} a {destino_seleccionado} con costo {costo} agregada.")

# Configurar oferta y demanda
st.sidebar.title("Oferta y Demanda")
oferta = st.sidebar.text_input("Oferta por origen (separada por comas)", value=",".join(["0"] * num_origenes))
demanda = st.sidebar.text_input("Demanda por destino (separada por comas)", value=",".join(["0"] * num_destinos))

# Mostrar rutas agregadas
st.sidebar.title("Rutas Definidas")
for ruta in st.session_state["rutas"]:
    st.sidebar.write(f"{ruta[0]} → {ruta[1]}: ${ruta[2]}")

#################################################################################
# GRÁFICO
#################################################################################
titulo = """
<div>
    <h2 style='text-align:center; color: white;'>UNIVERSIDAD MAYOR DE SAN ANDRÉS</h2>
    <h2 style='text-align:center; color: white;'>FACULTAD DE CIENCIAS PURAS Y NATURALES</h2>
    <h2 style='text-align:center; color: white;'>CARRERA DE INFORMÁTICA</h2>
    <h2 style='text-align:center; color: white;'>PROBLEMA TRANSPORTE</h2>
    <br>
</div>
"""
st.markdown(titulo, unsafe_allow_html=True)

# Crear gráfico interactivo
red = Network(height="600px", width="100%", directed=True)
red.toggle_physics(False)

posicion_origen_x, posicion_destino_x = -450, 450
espaciado = 100

for i, origen in enumerate(origenes):
    red.add_node(origen, label=f"Origen {i+1}", color="blue", x=posicion_origen_x, y=-i * espaciado, physics=False)

for j, destino in enumerate(destinos):
    red.add_node(destino, label=f"Destino {j+1}", color="green", x=posicion_destino_x, y=-j * espaciado, physics=False)

for ruta in st.session_state["rutas"]:
    red.add_edge(ruta[0], ruta[1], label=f"${ruta[2]}", color="black")

with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as archivo_temp:
    red.save_graph(archivo_temp.name)
    st.components.v1.html(archivo_temp.read().decode("utf-8"), height=600)

#################################################################################
# RESULTADOS
#################################################################################

if st.button("Resolver problema"):
    try:
        oferta = [float(x) for x in oferta.split(",")]
        demanda = [float(x) for x in demanda.split(",")]
        if len(oferta) != num_origenes or len(demanda) != num_destinos:
            st.error("La oferta o la demanda no coinciden con el número de orígenes o destinos.")
            st.stop()
        solucion = resolver_problema_transporte(st.session_state["matriz_costos"], oferta, demanda)
        st.subheader("Resultados")
        st.write(f"Estado: {solucion['estado']}")
        st.write(f"Costo Total: ${solucion['costo_total']}")
        tabla_variables = [
            {
                "Origen": origenes[i],
                "Destino": destinos[j],
                "Unidades": solucion["variables"][(i, j)],
                "Costo": st.session_state["matriz_costos"][i][j],
            }
            for i in range(num_origenes)
            for j in range(num_destinos)
        ]
        st.dataframe(tabla_variables)
    except Exception as e:
        st.error(f"Error: {e}")

integrantes = """
<div>
    <h5>INTEGRANTES:</h5>
    <ul style='padding-left: 40px;'>
        Cussi Cori Mariluz Ibonne<br>
        Huanca Chura Jesika Karina<br>
        Rojas Reas Ana Gabriela<br>
        Zarco Silvestre Marlene Rocío<br>
        Ticona Chavez Cristhian Fernando<br>
    </ul>
    <p><strong>DOCENTE:</strong> LIC. MARIO AMILCAR MIRANDA GONZALES</p>
    <p><strong>MATERIA:</strong> INVESTIGACIÓN OPERATIVA I</p>
</div>
"""
st.markdown(integrantes, unsafe_allow_html=True)
