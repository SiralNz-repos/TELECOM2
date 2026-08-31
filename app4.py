import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Simulador de Comunicación Digital",
    page_icon="📡",
    layout="wide"
)


# ============================================================
# TÍTULO
# ============================================================

st.title("📡 Simulador Interactivo de Comunicación Digital")

st.write("""
Este simulador muestra cómo un mensaje atraviesa las diferentes
etapas de un sistema de comunicación digital.
""")


# ============================================================
# FUNCIONES DE CONVERSIÓN
# ============================================================

def text_to_bits(text):
    """
    Convierte texto a bits utilizando UTF-8.
    """
    datos = text.encode("utf-8")

    return ''.join(
        format(byte, '08b')
        for byte in datos
    )


def bits_to_text(bits):
    """
    Convierte una secuencia de bits nuevamente a texto UTF-8.
    """

    # Eliminar bits incompletos
    longitud_valida = len(bits) - (len(bits) % 8)

    bits = bits[:longitud_valida]

    try:

        bytes_lista = []

        for i in range(0, len(bits), 8):

            byte = bits[i:i+8]

            bytes_lista.append(
                int(byte, 2)
            )

        return bytes(bytes_lista).decode(
            "utf-8",
            errors="replace"
        )

    except Exception:

        return "[Error de decodificación]"


# ============================================================
# CODIFICADOR DE CANAL
# REPETICIÓN X3
# ============================================================

def codificar_canal(bits):

    return ''.join(
        bit * 3
        for bit in bits
    )


# ============================================================
# DECODIFICADOR DE CANAL
# VOTACIÓN POR MAYORÍA
# ============================================================

def decodificar_canal(bits):

    resultado = []

    for i in range(0, len(bits), 3):

        bloque = bits[i:i+3]

        if len(bloque) < 3:
            continue

        unos = bloque.count('1')
        ceros = bloque.count('0')

        if unos > ceros:
            resultado.append('1')
        else:
            resultado.append('0')

    return ''.join(resultado)


# ============================================================
# CÁLCULO DE ERRORES
# ============================================================

def calcular_errores(bits_originales, bits_recibidos):

    longitud = min(
        len(bits_originales),
        len(bits_recibidos)
    )

    errores = sum(
        a != b
        for a, b in zip(
            bits_originales[:longitud],
            bits_recibidos[:longitud]
        )
    )

    if longitud == 0:
        ber = 0
    else:
        ber = errores / longitud

    return errores, ber


# ============================================================
# BARRA LATERAL
# ============================================================

st.sidebar.header("⚙ Parámetros de Simulación")


mensaje_original = st.sidebar.text_input(
    "📝 Mensaje de la Fuente:",
    "Hola Profe, esto es redes!"
)


sigma = st.sidebar.slider(
    "🔊 Nivel de Ruido AWGN (σ):",
    min_value=0.0,
    max_value=3.0,
    value=0.5,
    step=0.1
)


interferencia_activa = st.sidebar.checkbox(
    "⚡ Activar interferencia",
    value=False
)


amplitud_interferencia = 0.0

if interferencia_activa:

    amplitud_interferencia = st.sidebar.slider(
        "Amplitud de interferencia:",
        min_value=0.0,
        max_value=2.0,
        value=0.5,
        step=0.1
    )


mostrar_bits = st.sidebar.slider(
    "Cantidad de bits a visualizar:",
    min_value=10,
    max_value=100,
    value=30,
    step=10
)


st.sidebar.markdown("---")

st.sidebar.subheader("🎬 Control de Animación")


if "etapa" not in st.session_state:
    st.session_state.etapa = 1


if st.sidebar.button("⏮ Reiniciar"):
    st.session_state.etapa = 1


if st.sidebar.button("▶ Siguiente etapa"):

    if st.session_state.etapa < 9:
        st.session_state.etapa += 1


# ============================================================
# DIAGRAMA DEL SISTEMA
# ============================================================

st.markdown("## 🔄 Flujo del Sistema")


etapas = [
    "Fuente",
    "Codificador\nFuente",
    "Codificador\nCanal",
    "Modulador\nDigital",
    "Canal",
    "Demodulador\nDigital",
    "Decodificador\nCanal",
    "Decodificador\nFuente",
    "Salida"
]


cols = st.columns(len(etapas))


for i, etapa in enumerate(etapas):

    with cols[i]:

        if i + 1 == st.session_state.etapa:

            st.markdown(
                f"""
                <div style="
                    background-color:#1f77b4;
                    color:white;
                    padding:15px;
                    border-radius:10px;
                    text-align:center;
                    font-weight:bold;
                    min-height:70px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                {etapa.replace(chr(10), "<br>")}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div style="
                    background-color:#eeeeee;
                    padding:15px;
                    border-radius:10px;
                    text-align:center;
                    min-height:70px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                {etapa.replace(chr(10), "<br>")}
                </div>
                """,
                unsafe_allow_html=True
            )


st.markdown("---")


# ============================================================
# 1. FUENTE
# ============================================================

bits_fuente = text_to_bits(
    mensaje_original
)


# ============================================================
# 2. CODIFICADOR DE FUENTE
#
# En esta simulación el mensaje ya está digitalizado.
# La conversión UTF-8 representa la codificación de fuente.
# ============================================================

bits_codificador_fuente = bits_fuente


# ============================================================
# 3. CODIFICADOR DE CANAL
# ============================================================

bits_codificados = codificar_canal(
    bits_codificador_fuente
)


# ============================================================
# 4. MODULADOR DIGITAL BPSK
# ============================================================

simbolos_tx = np.array([
    1.0 if bit == '1' else -1.0
    for bit in bits_codificados
])


# ============================================================
# 5. CANAL
# ============================================================

# Generador aleatorio
rng = np.random.default_rng()

# Ruido AWGN
ruido = rng.normal(
    0,
    sigma,
    len(simbolos_tx)
)


# Interferencia sinusoidal
indice = np.arange(
    len(simbolos_tx)
)


if interferencia_activa:

    interferencia = (
        amplitud_interferencia
        *
        np.sin(
            2 * np.pi * 0.08 * indice
        )
    )

else:

    interferencia = np.zeros(
        len(simbolos_tx)
    )


# Señal recibida
simbolos_rx = (
    simbolos_tx
    +
    ruido
    +
    interferencia
)


# ============================================================
# 6. DEMODULADOR DIGITAL
# ============================================================

bits_demod = ''.join(

    '1'
    if simbolo > 0
    else '0'

    for simbolo in simbolos_rx
)


# ============================================================
# 7. DECODIFICADOR DE CANAL
# ============================================================

bits_finales = decodificar_canal(
    bits_demod
)


# ============================================================
# 8. DECODIFICADOR DE FUENTE
# ============================================================

mensaje_recuperado = bits_to_text(
    bits_finales
)


# ============================================================
# CÁLCULO DE ERRORES
# ============================================================

errores_antes, ber_antes = calcular_errores(
    bits_codificados,
    bits_demod
)


errores_despues, ber_despues = calcular_errores(
    bits_fuente,
    bits_finales
)


# ============================================================
# MOSTRAR ETAPAS
# ============================================================


# ------------------------------------------------------------
# ETAPA 1
# ------------------------------------------------------------

if st.session_state.etapa >= 1:

    st.header("1️⃣ Fuente")

    st.info(
        "La fuente genera el mensaje original que se desea transmitir."
    )

    st.write(
        "### 📝 Mensaje generado:"
    )

    st.success(
        mensaje_original
    )


# ------------------------------------------------------------
# ETAPA 2
# ------------------------------------------------------------

if st.session_state.etapa >= 2:

    st.header("2️⃣ Codificador de Fuente")

    st.write("""
    En esta simulación el mensaje se representa digitalmente
    utilizando una codificación UTF-8.
    """)

    st.write(
        "### 🔢 Representación binaria"
    )

    st.code(
        bits_fuente[:mostrar_bits]
        +
        " ..."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Caracteres",
            len(mensaje_original)
        )

    with col2:

        st.metric(
            "Bits generados",
            len(bits_fuente)
        )


# ------------------------------------------------------------
# ETAPA 3
# ------------------------------------------------------------

if st.session_state.etapa >= 3:

    st.header("3️⃣ Codificador de Canal")

    st.write("""
    Para proteger la información se utiliza un código de repetición ×3.

    Cada bit se transmite tres veces.
    """)

    ejemplo_original = bits_fuente[:8]

    ejemplo_codificado = codificar_canal(
        ejemplo_original
    )

    st.write(
        "### Ejemplo"
    )

    st.code(
        f"""
Bits originales:

{ejemplo_original}

Bits codificados:

{ejemplo_codificado}
"""
    )


# ------------------------------------------------------------
# ETAPA 4
# ------------------------------------------------------------

if st.session_state.etapa >= 4:

    st.header("4️⃣ Modulador Digital")

    st.write("""
    Se utiliza modulación BPSK.
    """)

    st.markdown("""

    **Regla de modulación:**

    - Bit `1` → amplitud `+1`
    - Bit `0` → amplitud `-1`

    """)

    st.code(
        f"""
Bits:

{bits_codificados[:20]}

Símbolos BPSK:

{simbolos_tx[:20]}
"""
    )


# ------------------------------------------------------------
# ETAPA 5
# ------------------------------------------------------------

if st.session_state.etapa >= 5:

    st.header("5️⃣ Canal de Comunicación")

    st.write("""
    La señal transmitida atraviesa un canal afectado por
    ruido gaussiano AWGN y, opcionalmente, interferencia.
    """)

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Ruido σ",
            sigma
        )

    with col2:

        st.metric(
            "Interferencia",
            "ACTIVA"
            if interferencia_activa
            else "DESACTIVADA"
        )

    with col3:

        st.metric(
            "Amplitud interferencia",
            amplitud_interferencia
        )


# ------------------------------------------------------------
# ETAPA 6
# ------------------------------------------------------------

if st.session_state.etapa >= 6:

    st.header("6️⃣ Demodulador Digital")

    st.write("""
    El receptor toma una decisión utilizando un umbral en cero.
    """)

    st.markdown("""

    - Señal recibida > 0 → bit `1`
    - Señal recibida < 0 → bit `0`

    """)

    st.code(
        bits_demod[:mostrar_bits]
        +
        " ..."
    )


# ------------------------------------------------------------
# ETAPA 7
# ------------------------------------------------------------

if st.session_state.etapa >= 7:

    st.header("7️⃣ Decodificador de Canal")

    st.write("""
    Como cada bit fue repetido tres veces, el receptor utiliza
    votación por mayoría para recuperar el bit original.
    """)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Errores antes de corrección",
            errores_antes
        )

    with col2:

        st.metric(
            "BER antes de corrección",
            f"{ber_antes:.4f}"
        )

    st.code(
        f"""
Ejemplo:

Transmitido:
111

Recibido:
101

Votación:

1 + 0 + 1

Resultado:
1
"""
    )


# ------------------------------------------------------------
# ETAPA 8
# ------------------------------------------------------------

if st.session_state.etapa >= 8:

    st.header("8️⃣ Decodificador de Fuente")

    st.write("""
    Los bits recuperados se agrupan nuevamente en bytes
    y se convierten al texto original.
    """)

    st.code(
        bits_finales[:mostrar_bits]
        +
        " ..."
    )


# ------------------------------------------------------------
# ETAPA 9
# ------------------------------------------------------------

if st.session_state.etapa >= 9:

    st.header("9️⃣ Salida del Sistema")

    st.write("""
    En esta etapa se observa la información que finalmente
    consiguió recuperar el receptor después de atravesar
    todo el sistema de comunicación.
    """)

    # ========================================================
    # COMPARACIÓN
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📤 Mensaje enviado")

        st.info(
            mensaje_original
        )

    with col2:

        st.subheader("📥 Mensaje real recibido")

        if mensaje_original == mensaje_recuperado:

            st.success(
                mensaje_recuperado
            )

        else:

            st.error(
                mensaje_recuperado
            )

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    st.markdown("---")

    st.subheader("🔍 Resultado de la transmisión")


    if mensaje_original == mensaje_recuperado:

        st.success("""
        🎉 TRANSMISIÓN EXITOSA

        El mensaje que llegó al receptor es exactamente
        igual al mensaje enviado.
        """)

    else:

        st.warning("""
        ⚠️ TRANSMISIÓN CON ERRORES

        El mensaje mostrado arriba representa lo que
        realmente pudo reconstruir el receptor.
        """)


    # ========================================================
    # MOSTRAR BITS
    # ========================================================

    with st.expander("🔢 Ver información digital final"):

        st.write("### Bits originales enviados")

        st.code(
            bits_fuente[:100]
            +
            (" ..." if len(bits_fuente) > 100 else "")
        )


        st.write("### Bits que llegaron después de la corrección")

        st.code(
            bits_finales[:100]
            +
            (" ..." if len(bits_finales) > 100 else "")
        )


    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    st.markdown("### 📊 Estadísticas finales")

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Errores antes de corrección",
            errores_antes
        )


    with col2:

        st.metric(
            "Errores después de corrección",
            errores_despues
        )


    with col3:

        porcentaje_correcto = (
            (1 - ber_despues) * 100
        )

        st.metric(
            "Información recuperada",
            f"{porcentaje_correcto:.2f}%"
        )
# ============================================================
# GRÁFICAS
# ============================================================

if st.session_state.etapa >= 4:

    st.markdown("---")

    st.header("📊 Visualización de las Señales")


    limite_grafica = min(
        mostrar_bits,
        len(simbolos_tx)
    )


    # --------------------------------------------------------
    # GRÁFICA BPSK
    # --------------------------------------------------------

    fig1, ax1 = plt.subplots(
        figsize=(12, 4)
    )


    ax1.stem(
        np.arange(limite_grafica),
        simbolos_tx[:limite_grafica]
    )


    ax1.axhline(
        0,
        linestyle="--",
        linewidth=1
    )


    ax1.set_title(
        "Señal Transmitida - BPSK"
    )


    ax1.set_xlabel(
        "Índice del símbolo"
    )


    ax1.set_ylabel(
        "Amplitud"
    )


    ax1.grid(
        True,
        alpha=0.4
    )


    st.pyplot(fig1)

    plt.close(fig1)


# ============================================================
# GRÁFICA DEL CANAL
# ============================================================

if st.session_state.etapa >= 5:

    fig2, ax2 = plt.subplots(
        figsize=(12, 5)
    )


    x = np.arange(
        limite_grafica
    )


    ax2.stem(
        x,
        simbolos_tx[:limite_grafica],
        label="Transmitido"
    )


    ax2.scatter(
        x,
        simbolos_rx[:limite_grafica],
        label="Recibido"
    )


    ax2.axhline(
        0,
        linestyle="--",
        linewidth=1
    )


    ax2.set_title(
        "Efecto del Canal: Señal Transmitida vs Recibida"
    )


    ax2.set_xlabel(
        "Índice del símbolo"
    )


    ax2.set_ylabel(
        "Amplitud"
    )


    ax2.legend()


    ax2.grid(
        True,
        alpha=0.4
    )


    st.pyplot(fig2)

    plt.close(fig2)


# ============================================================
# GRÁFICA DEL RUIDO
# ============================================================

if st.session_state.etapa >= 5:

    fig3, ax3 = plt.subplots(
        figsize=(12, 4)
    )


    ax3.plot(
        x,
        ruido[:limite_grafica],
        label="Ruido AWGN"
    )


    if interferencia_activa:

        ax3.plot(
            x,
            interferencia[:limite_grafica],
            label="Interferencia"
        )


    ax3.set_title(
        "Perturbaciones Introducidas por el Canal"
    )


    ax3.set_xlabel(
        "Índice del símbolo"
    )


    ax3.set_ylabel(
        "Amplitud"
    )


    ax3.legend()


    ax3.grid(
        True,
        alpha=0.4
    )


    st.pyplot(fig3)

    plt.close(fig3)


# ============================================================
# TEORÍA
# ============================================================

st.markdown("---")

st.header(
    "📖 Teoría del Sistema de Comunicación Digital"
)


with st.expander(
    "📥 Bloques del Transmisor",
    expanded=False
):

    st.markdown("""
    
### Fuente

Genera la información original.

Puede ser:

- Voz
- Texto
- Música
- Video
- Datos

### Codificador de Fuente

Convierte o representa la información de manera eficiente.

Puede realizar:

- Digitalización
- Compresión
- Reducción de redundancia

### Codificador de Canal

Añade redundancia controlada para:

- Detectar errores
- Corregir errores

### Modulador Digital

Convierte los bits en señales adecuadas para ser transmitidas.

Ejemplos:

- BPSK
- QPSK
- QAM
- FSK

    """)


with st.expander(
    "🌊 Canal de Transmisión",
    expanded=False
):

    st.markdown("""

El canal es el medio físico por el cual viaja la información.

Ejemplos:

- Aire
- Radio
- Fibra óptica
- Cable coaxial
- Par trenzado

Durante la transmisión pueden aparecer:

### Ruido

Señales aleatorias que alteran la información.

### Interferencia

Señales externas que se mezclan con la señal transmitida.

### Atenuación

Reducción de la potencia de la señal durante su propagación.

    """)


with st.expander(
    "📤 Bloques del Receptor",
    expanded=False
):

    st.markdown("""

### Demodulador Digital

Recupera los bits a partir de la señal recibida.

### Decodificador de Canal

Utiliza la redundancia para detectar y corregir errores.

### Decodificador de Fuente

Reconstruye la información original.

### Salida

Entrega finalmente el mensaje recuperado.

    """)


# ============================================================
# PIE DE PÁGINA
# ============================================================

st.markdown("---")

st.caption(
    "Simulador educativo de un sistema de comunicaciones digitales | BPSK + AWGN + Código de Repetición"
)