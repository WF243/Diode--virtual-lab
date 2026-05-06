import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="Diode Lab Simulator", layout="wide")
st.markdown("""
<style>

/* خلفية الصفحة */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #e3f2fd, #f8fbff);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #dbeafe, #eff6ff);
}

/* العناوين */
h1, h2, h3 {
    color: #1d4ed8;
}

/* كروت */
.card {
    background-color: white;
    padding: 18px;
    border-radius: 20px;
    border: none;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    margin-bottom: 16px;
}

/* زر */
.stButton > button {
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    color: white;
    border-radius: 12px;
    font-weight: bold;
    border: none;
    padding: 0.5rem 1rem;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.block-container { padding-top: 1.2rem; }
h1, h2, h3 { color: #0057B8; }
.card {
    background-color: white;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 16px;
}
.lamp-off, .lamp-dim, .lamp-on, .lamp-breakdown {
    width: 95px; height: 95px; border-radius: 50%; margin: auto;
}
.lamp-off {
    background: radial-gradient(circle, #ff6b6b, #8b0000);
    box-shadow: 0 0 10px #8b0000;
}
.lamp-dim {
    background: radial-gradient(circle, #ffe066, #cc8b00);
    box-shadow: 0 0 25px #ffd43b;
    animation: pulseDim 1.5s infinite;
}
.lamp-on {
    background: radial-gradient(circle, #fff3bf, #ffd43b);
    box-shadow: 0 0 45px #ffd43b, 0 0 85px #fab005;
    animation: pulseOn 1s infinite;
}
.lamp-breakdown {
    background: radial-gradient(circle, #ff8787, #c92a2a);
    box-shadow: 0 0 60px red;
    animation: shake 0.25s infinite;
}
@keyframes pulseDim {
    0% { box-shadow: 0 0 12px #ffd43b; }
    50% { box-shadow: 0 0 30px #ffd43b; }
    100% { box-shadow: 0 0 12px #ffd43b; }
}
@keyframes pulseOn {
    0% { box-shadow: 0 0 25px #ffd43b; }
    50% { box-shadow: 0 0 65px #fab005; }
    100% { box-shadow: 0 0 25px #ffd43b; }
}
@keyframes shake {
    0% { transform: translateX(0px); }
    25% { transform: translateX(3px); }
    50% { transform: translateX(-3px); }
    75% { transform: translateX(3px); }
    100% { transform: translateX(0px); }
}
</style>
""", unsafe_allow_html=True)

q = 1.6e-19
k = 1.38e-23

st.title("💡 Diode Lab Simulator")
st.markdown("### ✨ Interactive Electronics Lab ✨")
st.markdown("---")
st.write("Interactive diode lab: circuit, lamp state, I–V curve, knee point, selected point, and data table.")

# Reset setup
if "T" not in st.session_state:
    st.session_state.T = 300
if "R" not in st.session_state:
    st.session_state.R = 1000.0
if "Vs" not in st.session_state:
    st.session_state.Vs = 0.0

st.sidebar.header("Controls")

if st.sidebar.button("🔄 Reset"):
    st.session_state.T = 300
    st.session_state.R = 1000.0
    st.session_state.Vs = 0.0

diode_type = st.sidebar.selectbox("Diode type", ["PN Diode", "Zener Diode", "LED"])
material = st.sidebar.selectbox("Material", ["Silicon (Si)", "Germanium (Ge)"])

led_color = None
if diode_type == "LED":
    led_color = st.sidebar.selectbox("LED color", ["Red", "Green", "Blue / White"])

T = st.sidebar.slider("Temperature (K)", 250, 400, key="T")
R = st.sidebar.number_input("Series resistance R (Ω)", min_value=1.0, key="R")
Vs = st.sidebar.slider("Source voltage Vs (V)", -10.0, 10.0, key="Vs", step=0.1)

bias_type = "Forward Bias" if Vs > 0 else "Reverse Bias" if Vs < 0 else "No Bias"
st.sidebar.subheader("Bias Type")
if Vs > 0:
    st.sidebar.success(bias_type)
elif Vs < 0:
    st.sidebar.warning(bias_type)
else:
    st.sidebar.info(bias_type)

VT = k * T / q

# Barrier voltage
if material == "Silicon (Si)":
    Vbarrier = 0.7
    mat_short = "Si"
else:
    Vbarrier = 0.3
    mat_short = "Ge"

if diode_type == "LED":
    mat_short = led_color
    if led_color == "Red":
        Vbarrier = 1.8
    elif led_color == "Green":
        Vbarrier = 2.2
    else:
        Vbarrier = 3.0

Vz = 5.1

# Educational exponential model
Iknee_mA = 0.25
steepness = 0.055

def forward_current_mA(V):
    if V <= 0:
        return 0.0
    return Iknee_mA * np.exp((V - Vbarrier) / steepness)

def current_mA(V):
    if diode_type == "Zener Diode" and V < 0:
        if V <= -Vz:
            return -((abs(V) - Vz) / R) * 1000
        return -0.001
    if V <= 0:
        return 0.0
    return forward_current_mA(V)

I_selected_mA = current_mA(Vs)

if diode_type == "Zener Diode" and Vs <= -Vz:
    lamp_state = "💥 BREAKDOWN"
    lamp_note = "Reverse voltage exceeded the Zener breakdown voltage."
elif abs(I_selected_mA) < 0.01:
    lamp_state = "🔴 OFF"
    lamp_note = "Current is too small."
elif abs(I_selected_mA) < 1:
    lamp_state = "🟡 DIM"
    lamp_note = "DIM means weak light."
else:
    lamp_state = "💡 ON"
    lamp_note = "The diode is conducting clearly."

def circuit_svg(diode_type):
    if diode_type == "Zener Diode":
        symbol = """
        <polygon points="540,135 540,205 610,170" fill="black"/>
        <line x1="615" y1="135" x2="615" y2="205" stroke="black" stroke-width="4"/>
        <line x1="615" y1="135" x2="633" y2="125" stroke="black" stroke-width="4"/>
        <line x1="615" y1="205" x2="597" y2="215" stroke="black" stroke-width="4"/>
        <text x="535" y="245" font-size="22">Zener</text>
        """
    elif diode_type == "LED":
        symbol = """
        <polygon points="540,135 540,205 610,170" fill="black"/>
        <line x1="615" y1="135" x2="615" y2="205" stroke="black" stroke-width="4"/>
        <line x1="640" y1="125" x2="680" y2="85" stroke="orange" stroke-width="4"/>
        <polyline points="665,85 680,85 680,100" fill="none" stroke="orange" stroke-width="4"/>
        <line x1="625" y1="110" x2="665" y2="70" stroke="orange" stroke-width="4"/>
        <polyline points="650,70 665,70 665,85" fill="none" stroke="orange" stroke-width="4"/>
        <text x="570" y="245" font-size="22">LED</text>
        """
    else:
        symbol = """
        <polygon points="540,135 540,205 610,170" fill="black"/>
        <line x1="615" y1="135" x2="615" y2="205" stroke="black" stroke-width="4"/>
        <text x="552" y="245" font-size="22">Diode</text>
        """
    return f"""
    <svg width="100%" height="280" viewBox="0 0 820 280">
      <rect x="10" y="10" width="800" height="260" rx="15" fill="white" stroke="#ddd"/>
      <line x1="90" y1="70" x2="210" y2="70" stroke="black" stroke-width="4"/>
      <polyline points="210,70 225,50 240,90 255,50 270,90 285,50 300,90 315,70"
                fill="none" stroke="black" stroke-width="4"/>
      <text x="255" y="40" font-size="28">R</text>
      <line x1="315" y1="70" x2="410" y2="70" stroke="black" stroke-width="4"/>
      <circle cx="445" cy="70" r="28" fill="white" stroke="black" stroke-width="4"/>
      <text x="435" y="80" font-size="28">A</text>
      <line x1="473" y1="70" x2="585" y2="70" stroke="black" stroke-width="4"/>
      <line x1="585" y1="70" x2="585" y2="135" stroke="black" stroke-width="4"/>
      {symbol}
      <line x1="585" y1="205" x2="585" y2="250" stroke="black" stroke-width="4"/>
      <line x1="585" y1="70" x2="735" y2="70" stroke="black" stroke-width="4"/>
      <line x1="735" y1="70" x2="735" y2="250" stroke="black" stroke-width="4"/>
      <circle cx="735" cy="160" r="32" fill="white" stroke="black" stroke-width="4"/>
      <text x="723" y="170" font-size="28">V</text>
      <line x1="735" y1="250" x2="90" y2="250" stroke="black" stroke-width="4"/>
      <line x1="90" y1="250" x2="90" y2="195" stroke="black" stroke-width="4"/>
      <line x1="60" y1="160" x2="120" y2="160" stroke="black" stroke-width="5"/>
      <line x1="70" y1="185" x2="110" y2="185" stroke="black" stroke-width="5"/>
      <line x1="90" y1="70" x2="90" y2="160" stroke="black" stroke-width="4"/>
      <line x1="90" y1="185" x2="90" y2="195" stroke="black" stroke-width="4"/>
      <text x="40" y="135" font-size="30">+</text>
      <text x="45" y="220" font-size="30">−</text>
      <text x="25" y="180" font-size="26" fill="red">Vs</text>
    </svg>
    """

col1, col2 = st.columns([1, 1.35])

with col1:
    st.subheader("Circuit")
    components.html(circuit_svg(diode_type), height=285)

    st.subheader("💡 Lamp Indicator")
    if "OFF" in lamp_state:
        lamp_class = "lamp-off"
    elif "DIM" in lamp_state:
        lamp_class = "lamp-dim"
    elif "ON" in lamp_state:
        lamp_class = "lamp-on"
    else:
        lamp_class = "lamp-breakdown"

    st.markdown(f"""
    <div class="card" style="text-align:center;">
        <div class="{lamp_class}"></div>
        <h2>{lamp_state}</h2>
        <p>{lamp_note}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Calculated Values")
    st.markdown(f"""
    <div class="card">
        <p><b>Thermal Voltage VT:</b> {VT:.5f} V</p>
        <p><b>V Barrier / Knee Voltage:</b> {Vbarrier:.2f} V</p>
        <p><b>Current at Vs:</b> {I_selected_mA:.4f} mA</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("---")
    st.subheader("I–V Characteristic")

    if diode_type == "LED":
        vmax = max(3.8, Vbarrier + 0.8)
    else:
        vmax = 1.2

    V = np.linspace(0, vmax, 800)
    I_mA = np.array([forward_current_mA(v) for v in V])

    knee_y = forward_current_mA(Vbarrier)
    selected_x = Vs if Vs > 0 else 0
    selected_y = current_mA(Vs) if Vs > 0 else 0

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=V, y=I_mA,
        mode="lines",
        name=f"{diode_type} ({mat_short})",
        line=dict(width=4, shape="spline")
    ))

    fig.add_trace(go.Scatter(
        x=[selected_x], y=[selected_y],
        mode="markers",
        name="Selected Point (Vs)",
        marker=dict(size=12)
    ))

    fig.add_trace(go.Scatter(
        x=[Vbarrier], y=[knee_y],
        mode="markers+text",
        name="Knee Point",
        text=["Knee"],
        textposition="bottom right",
        marker=dict(size=13, symbol="diamond")
    ))

    fig.add_shape(
        type="line",
        x0=Vbarrier, x1=Vbarrier,
        y0=0, y1=knee_y,
        line=dict(dash="dash", width=2)
    )

    fig.add_annotation(
        x=Vbarrier,
        y=0,
        text=f"{Vbarrier:.2f} V",
        showarrow=False,
        yshift=-25
    )

    ymax = max(10, min(np.max(I_mA), 80))
    fig.update_layout(
        title=f"{diode_type} I–V Curve",
        xaxis_title="Voltage (V)",
        yaxis_title="Current (mA)",
        height=480,
        yaxis=dict(range=[0, ymax]),
        transition=dict(duration=600, easing="cubic-in-out")
    )

    st.plotly_chart(fig, use_container_width=True)
st.markdown("---")
st.subheader("Data Table (Current in mA)")

table_voltages = np.array([
    0.00, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30,
    0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70,
    0.75, 0.80, 0.90, 1.00, 1.20, 1.50, 2.00, 2.50, 3.00
])

table_currents_mA = np.array([forward_current_mA(v) for v in table_voltages])

df = pd.DataFrame({
    "Voltage (V)": table_voltages,
    "Current (mA)": table_currents_mA
})

st.dataframe(df.style.format({
    "Voltage (V)": "{:.2f}",
    "Current (mA)": "{:.6f}"
}), use_container_width=True)

st.info("DIM means weak light. Knee Point = the approximate barrier voltage where the forward current starts increasing rapidly.")