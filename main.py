import streamlit as st
import math
import sqlite3
import json
import io
from datetime import date, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Nefrosys 1.0 - Sistema Clínico Nefrológico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONTROL DE AUTENTICACIÓN (LOGIN) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🩺 Nefrosys 1.0 - Acceso Restringido")
    st.markdown("### Sistema Clínico Especializado de Alta Precisión para Nefrología")
    st.markdown("---")
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("#### 🔐 Iniciar Sesión de Consultorio")
        with st.form("login_form"):
            usuario = st.text_input("Usuario o Registro Médico")
            password = st.text_input("Contraseña", type="password")
            submit_login = st.form_submit_button("Ingresar al Sistema")
            
            if submit_login:
                # Puedes cambiar aquí el usuario y la contraseña por defecto
                if usuario == "admin" and password == "nefrosys2026":
                    st.session_state.authenticated = True
                    st.success("¡Credenciales correctas! Cargando sistema...")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos. Verifique sus datos.")
    st.stop()  # Detiene la ejecución hasta que se autentique correctamente

# ==========================================
# A PARTIR DE AQUÍ EL SISTEMA ESTÁ DESBLOQUEADO
# ==========================================

st.title("🩺 Nefrosys 1.0")
st.markdown("### Sistema Clínico Especializado de Alta Precisión para Nefrología en Paraguay")
st.markdown("---")

# --- CONEXIÓN Y CONFIGURACIÓN DE BASE DE DATOS SQLITE ---
def init_db():
    conn = sqlite3.connect("nefrosys.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                        cedula TEXT PRIMARY KEY,
                        nombre TEXT,
                        edad INT,
                        sexo TEXT,
                        etiologia TEXT,
                        acceso TEXT,
                        comorbilidades TEXT,
                        pa TEXT,
                        edemas TEXT,
                        diuresis TEXT,
                        proteinuria TEXT,
                        electrolitos TEXT,
                        mineral_oseo TEXT,
                        antropometria TEXT,
                        vacunacion TEXT,
                        biopsia TEXT,
                        obs TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial_consultas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT,
                        fecha TEXT,
                        resumen_evolucion TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT,
                        tipo TEXT,
                        resultado TEXT,
                        fecha TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS prescripciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT,
                        medicamento TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS controles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT,
                        estudio TEXT,
                        fecha TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS evolucion_tfg (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT,
                        tfg REAL,
                        fecha TEXT)''')
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# --- FUNCIÓN SEGURA PARA EXTRAER DATOS DE TUPLAS ---
def safe_get(p, index, default=""):
    try:
        return p[index] if p[index] is not None else default
    except IndexError:
        return default

# --- GENERADOR DE PDF REAL CON REPORTLAB ---
def generar_pdf_paciente(p, prescs):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("<b>REPORTE CLÍNICO OFICIAL - NEFROSYS 1.0</b>", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Fecha de Emisión:</b> {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Paciente:</b> {safe_get(p, 1)}", styles['Normal']))
    story.append(Paragraph(f"<b>Cédula de Identidad:</b> {safe_get(p, 0)} | <b>Edad:</b> {safe_get(p, 2)} años | <b>Sexo:</b> {safe_get(p, 3)}", styles['Normal']))
    story.append(Paragraph(f"<b>Etiología ERC:</b> {safe_get(p, 4)} | <b>Acceso Vascular:</b> {safe_get(p, 5)}", styles['Normal']))
    story.append(Paragraph(f"<b>PA:</b> {safe_get(p, 7)} mmHg | <b>Edemas:</b> {safe_get(p, 8)} | <b>Diuresis:</b> {safe_get(p, 9)}", styles['Normal']))
    story.append(Paragraph(f"<b>Antropometría (Peso Seco):</b> {safe_get(p, 13)}", styles['Normal']))
    story.append(Paragraph(f"<b>Perfil Mineral Óseo:</b> {safe_get(p, 12)} | <b>Vacunación:</b> {safe_get(p, 14)}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Comorbilidades:</b> {safe_get(p, 6)}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Tratamiento Farmacológico Activo:</b>", styles['Heading2']))
    if prescs:
        for m in prescs:
            story.append(Paragraph(f"- {m[1]}", styles['Normal']))
    else:
        story.append(Paragraph("Sin medicamentos registrados.", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Observaciones Clínicas:</b>", styles['Heading2']))
    story.append(Paragraph(safe_get(p, 16, "Sin observaciones."), styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Informe generado electrónicamente por Nefrosys 1.0 - Sistema Clínico Nefrológico Especializado.</i>", styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- BARRA LATERAL: CONSULTORIO & BOTÓN DE SALIDA ---
st.sidebar.header("🏥 Gestión de Consultorio")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.authenticated = False
    st.rerun()

cursor.execute("SELECT cedula, nombre FROM pacientes")
lista_pacientes_db = cursor.fetchall()

opcion_sidebar = st.sidebar.radio("Modo de Acceso", ["Seleccionar Paciente en Consulta", "Registrar Nuevo Paciente"])
paciente_activo_ci = None

if opcion_sidebar == "Registrar Nuevo Paciente":
    st.sidebar.subheader("Nuevo Paciente")
    with st.sidebar.form("form_sidebar_paciente"):
        n_nombre = st.text_input("Nombre y Apellido")
        n_cedula = st.text_input("Cédula (CI)")
        n_edad = st.number_input("Edad", min_value=1, value=50)
        n_sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
        n_etiologia = st.selectbox("Etiología ERC", ["Nefropatía Diabética", "Nefropatía Hipertensiva", "Glomerulopatía", "Otra"])
        n_acceso = st.selectbox("Acceso Vascular", ["Conservador", "FAV Funcionante", "Catéter Tunelizado", "Diálisis Peritoneal"])
        
        if st.form_submit_button("Guardar e Iniciar Consulta"):
            if n_nombre and n_cedula:
                try:
                    cursor.execute("INSERT OR REPLACE INTO pacientes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   (n_cedula, n_nombre, n_edad, n_sexo, n_etiologia, n_acceso, "", "", "", "", "", "", "", "", "", "", ""))
                    conn.commit()
                    st.sidebar.success(f"¡{n_nombre} guardado!")
                    paciente_activo_ci = n_cedula
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
            else:
                st.sidebar.error("Ingrese Nombre y Cédula.")
else:
    if lista_pacientes_db:
        dic_p = {p[0]: p[1] for p in lista_pacientes_db}
        paciente_activo_ci = st.sidebar.selectbox(
            "Seleccionar Paciente en Consulta",
            list(dic_p.keys()),
            format_func=lambda x: f"{dic_p[x]} (CI: {x})"
        )
    else:
        st.sidebar.warning("No hay pacientes registrados.")

# --- FICHA DE ATENCIÓN UNIFICADA ---
if paciente_activo_ci:
    cursor.execute("SELECT * FROM pacientes WHERE cedula = ?", (paciente_activo_ci,))
    p_info = cursor.fetchone()
    
    cursor.execute("SELECT tfg FROM evolucion_tfg WHERE cedula = ? ORDER BY id DESC LIMIT 1", (paciente_activo_ci,))
    ultimo_tfg_row = cursor.fetchone()
    tfg_activo = ultimo_tfg_row[0] if ultimo_tfg_row else 60.0
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 📋 Paciente Activo")
    st.sidebar.info(f"**{safe_get(p_info, 1)}**\n\nCI: {safe_get(p_info, 0)} | {safe_get(p_info, 2)} años\n\n**Último TFG:** {tfg_activo} mL/min\n\n**Acceso:** {safe_get(p_info, 5)}")
    
    tab_hce, tab_calc, tab_tto, tab_kfre, tab_dialisis, tab_pdf = st.tabs([
        "📋 Historia Clínica & Evolución", 
        "🧮 Calculadoras Nefrológicas", 
        "💊 Ajuste Fármacos & Tratamiento", 
        "📈 KFRE & Gráfico TFG", 
        "🩸 Diálisis & Controles", 
        "📄 Informe PDF & Respaldo"
    ])
    
    with tab_hce:
        st.header(f"Historia Clínica Nefrológica Ampliada: {safe_get(p_info, 1)}")
        
        with st.form("form_editar_paciente"):
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                ed_nombre = st.text_input("Nombre Completo", value=safe_get(p_info, 1))
                ed_edad = st.number_input("Edad", value=int(safe_get(p_info, 2, 50)))
                sexo_val = safe_get(p_info, 3, "Masculino")
                ed_sexo = st.selectbox("Sexo", ["Masculino", "Femenino"], index=0 if sexo_val=="Masculino" else 1)
                ed_etiologia = st.text_input("Etiología Principal de ERC", value=safe_get(p_info, 4))
                ed_acceso = st.text_input("Acceso Vascular", value=safe_get(p_info, 5))
                ed_comorb = st.text_input("Comorbilidades (HTA, DM2, etc.)", value=safe_get(p_info, 6))
                ed_antropometria = st.text_input("Antropometría (Peso Habitual, Peso Seco, Ganancia Interdialítica)", value=safe_get(p_info, 13), placeholder="Ej: Habitual: 72kg, Seco: 70kg, Δ: 2kg")
            with col_h2:
                ed_pa = st.text_input("Presión Arterial (PA mmHg)", value=safe_get(p_info, 7), placeholder="Ej: 140/90")
                ed_edemas = st.selectbox("Edemas / Balance Hídrico", ["Ausentes", "Edema leve miembros inferiores (+)", "Edema moderado (++)", "Edema severo / Anasarca (+++)", "Edema agudo de pulmón"])
                ed_diuresis = st.text_input("Volumen Urinario / Diuresis 24h", value=safe_get(p_info, 9), placeholder="Ej: 1500 mL/24h o Oliguria")
                ed_proteinuria = st.text_input("Proteinuria / Albuminuria Cuantitativa", value=safe_get(p_info, 10), placeholder="Ej: 1.2 g/24h")
                ed_electrolitos = st.text_input("Electrolitos (K+, Na+, Ác. Úrico)", value=safe_get(p_info, 11), placeholder="K: 4.8 mEq/L")
                ed_mineral = st.text_input("Perfil Mineral Óseo (PTH, Calcio, Fósforo)", value=safe_get(p_info, 12), placeholder="PTH: 250 pg/mL, Ca: 9.2, P: 4.8")
                ed_vacunacion = st.text_input("Cartilla de Vacunación Renal (Hepatitis B, Neumococo, Influenza)", value=safe_get(p_info, 14), placeholder="Hepatitis B: Completa, Neumococo: Al día")
                ed_biopsia = st.text_input("Antecedente de Biopsia Renal / Histopatología", value=safe_get(p_info, 15))
            
            ed_obs = st.text_area("Notas Clínicas, Plan y Evolución de la Consulta Actual", value=safe_get(p_info, 16))
            
            if st.form_submit_button("Guardar Ficha y Registrar Consulta en el Historial"):
                cursor.execute("""UPDATE pacientes SET nombre=?, edad=?, sexo=?, etiologia=?, acceso=?, comorbilidades=?, 
                                  pa=?, edemas=?, diuresis=?, proteinuria=?, electrolitos=?, mineral_oseo=?, antropometria=?, vacunacion=?, biopsia=?, obs=? WHERE cedula=?""",
                               (ed_nombre, ed_edad, ed_sexo, ed_etiologia, ed_acceso, ed_comorb, 
                                ed_pa, ed_edemas, ed_diuresis, ed_proteinuria, ed_electrolitos, ed_mineral, ed_antropometria, ed_vacunacion, ed_biopsia, ed_obs, paciente_activo_ci))
                
                hoy = str(date.today())
                resumen_evo = f"PA: {ed_pa} | Peso Seco/Antropometría: {ed_antropometria} | Edemas: {ed_edemas} | Mineral Óseo: {ed_mineral} | Nota: {ed_obs}"
                cursor.execute("INSERT INTO historial_consultas (cedula, fecha, resumen_evolucion) VALUES (?, ?, ?)", 
                               (paciente_activo_ci, hoy, resumen_evo))
                conn.commit()
                st.success("¡Ficha actualizada y consulta registrada en el historial evolutivo!")
                st.rerun()

        st.markdown("---")
        st.subheader("📚 Historial de Consultas Anteriores y Evolución")
        cursor.execute("SELECT fecha, resumen_evolucion FROM historial_consultas WHERE cedula = ? ORDER BY id DESC", (paciente_activo_ci,))
        consultas_previas = cursor.fetchall()
        
        if consultas_previas:
            for idx, c in enumerate(consultas_previas, 1):
                st.info(f"📅 **Consulta del {c[0]}**\n\n{c[1]}")
        else:
            st.markdown("*Aún no hay registros de consultas anteriores guardados para este paciente.*")

    with tab_calc:
        st.header("🧮 Calculadoras Nefrológicas de Alta Especialidad")
        
        sub_c_tfg, sub_c_fena, sub_c_agua, sub_c_ag, sub_c_feurea = st.tabs([
            "1. TFG & KDIGO", 
            "2. FENa (Sodio)", 
            "3. Agua Libre",
            "4. Brecha Aniónica & Delta",
            "5. FEUrea"
        ])
        
        with sub_c_tfg:
            st.subheader("Estadificación y Filtrado Glomerular")
            c1, c2, c3 = st.columns(3)
            with c1:
                scr = st.number_input("Creatinina Sérica (mg/dL)", value=1.4, step=0.1, key="scr_tfg")
            with c2:
                acr = st.number_input("Albuminuria ACR (mg/g)", value=45.0, key="acr_tfg")
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                calc_tfg_btn = st.button("Calcular TFG y KDIGO")
                
            if calc_tfg_btn:
                sexo_pac = safe_get(p_info, 3, "Masculino")
                edad_pac = int(safe_get(p_info, 2, 50))
                
                kappa = 0.7 if sexo_pac == "Femenino" else 0.9
                alfa = -0.329 if sexo_pac == "Femenino" else -0.411
                factor = 1.012 if sexo_pac == "Femenino" else 1.0
                tfg = 142 * (min(scr/kappa, 1.0) ** alfa) * (max(scr/kappa, 1.0) ** -1.209) * (0.9938 ** edad_pac) * factor
                
                g_est = "G1" if tfg >= 90 else ("G2" if tfg >= 60 else ("G3a" if tfg >= 45 else ("G3b" if tfg >= 30 else ("G4" if tfg >= 15 else "G5"))))
                a_est = "A1" if acr < 30 else ("A2" if acr <= 300 else "A3")
                
                st.success(f"**TFG Estimada:** {round(tfg, 2)} mL/min/1.73m² | **KDIGO:** {g_est} - {a_est}")
                
                hoy = str(date.today())
                res_txt = f"TFG: {round(tfg, 2)} ({g_est} - {a_est})"
                cursor.execute("INSERT INTO evolucion_tfg (cedula, tfg, fecha) VALUES (?, ?, ?)", (paciente_activo_ci, round(tfg, 2), hoy))
                cursor.execute("INSERT INTO historial (cedula, tipo, resultado, fecha) VALUES (?, ?, ?, ?)", (paciente_activo_ci, "TFG & KDIGO", res_txt, hoy))
                conn.commit()
                st.toast("¡Cálculo guardado automáticamente en el historial de TFG!")
                st.rerun()

        with sub_c_fena:
            st.subheader("Fracción de Excreción de Sodio (FENa)")
            fc1, fc2 = st.columns(2)
            with fc1:
                f_na_u = st.number_input("Sodio Urinario (mEq/L)", value=20.0, key="f_na_u")
                f_na_s = st.number_input("Sodio Sérico (mEq/L)", value=140.0, key="f_na_s")
            with fc2:
                f_cr_u = st.number_input("Creatinina Urinaria (mg/dL)", value=100.0, key="f_cr_u")
                f_cr_s = st.number_input("Creatinina Sérica (mg/dL)", value=1.5, key="f_cr_s")
                
            if st.button("Calcular FENa"):
                try:
                    fena = (f_na_u * f_cr_s) / (f_na_s * f_cr_u) * 100
                    interp = "Insuficiencia Prerrenal (FENa < 1%)" if fena < 1 else "Necrosis Tubular Aguda / Intrínseca (FENa > 1%)"
                    st.metric("Fracción de Excreción de Sodio (FENa)", f"{round(fena, 2)} %")
                    st.info(f"**Interpretación:** {interp}")
                except ZeroDivisionError:
                    st.error("Error por división cero.")

        with sub_c_agua:
            st.subheader("Aclaramiento / Déficit de Agua Libre")
            ac1, ac2 = st.columns(2)
            with ac1:
                na_ser = st.number_input("Sodio Sérico Actual (mEq/L)", value=150.0, key="na_ser")
                na_uri = st.number_input("Sodio Urinario (mEq/L)", value=100.0, key="na_uri")
            with ac2:
                vol_orina = st.number_input("Volumen Urinario 24h (Litros)", value=1.5, key="vol_orina")
                
            if st.button("Calcular Agua Libre"):
                try:
                    ch2o = vol_orina * (1 - (na_uri / na_ser))
                    st.metric("Aclaramiento de Agua Libre (CH2O)", f"{round(ch2o, 2)} L/24h")
                except ZeroDivisionError:
                    st.error("El sodio sérico no puede ser cero.")

        with sub_c_ag:
            st.subheader("Brecha Aniónica (Anion Gap) y Delta Ratio")
            ag1, ag2, ag3 = st.columns(3)
            with ag1:
                na_ag = st.number_input("Sodio (Na) mEq/L", value=140.0, key="na_ag")
            with ag2:
                cl_ag = st.number_input("Cloro (Cl) mEq/L", value=104.0, key="cl_ag")
            with ag3:
                hco3_ag = st.number_input("Bicarbonato (HCO3) mEq/L", value=22.0, key="hco3_ag")
                
            if st.button("Calcular Anion Gap & Delta Ratio"):
                anion_gap = na_ag - (cl_ag + hco3_ag)
                delta_ag = anion_gap - 12.0
                delta_hco3 = 24.0 - hco3_ag
                delta_ratio = delta_ag / delta_hco3 if delta_hco3 != 0 else 0
                
                st.metric("Brecha Aniónica (Anion Gap)", f"{round(anion_gap, 2)} mEq/L (Normal: 8-12)")
                st.metric("Delta Ratio", f"{round(delta_ratio, 2)}")
                if anion_gap > 12:
                    st.warning("⚠️ Acidosis metabólica con Anion Gap elevado.")
                else:
                    st.info("ℹ️ Brecha aniónica normal (posible acidosis hiperclorémica).")

        with sub_c_feurea:
            st.subheader("Excreción Fraccional de Urea (FEUrea)")
            fu1, fu2 = st.columns(2)
            with fu1:
                u_urea = st.number_input("Urea Urinaria (mg/dL)", value=400.0, key="u_urea")
                s_urea = st.number_input("Urea Sérica (mg/dL)", value=40.0, key="s_urea")
            with fu2:
                u_cr = st.number_input("Creatinina Urinaria (mg/dL)", value=100.0, key="u_cr_fe")
                s_cr = st.number_input("Creatinina Sérica (mg/dL)", value=1.5, key="s_cr_fe")
                
            if st.button("Calcular FEUrea"):
                try:
                    fe_urea = (u_urea * s_cr) / (s_urea * u_cr) * 100
                    interp_fe = "Prerrenal (FEUrea < 35%)" if fe_urea < 35 else "Intrínseca / NTA (FEUrea > 50%)"
                    st.metric("Excreción Fraccional de Urea (FEUrea)", f"{round(fe_urea, 2)} %")
                    st.info(f"**Interpretación:** {interp_fe}")
                except ZeroDivisionError:
                    st.error("Error por división cero.")

    with tab_tto:
        st.header("💊 Módulo de Ajuste Farmacológico Automatizado por TFG")
        st.info(f"📌 Evaluando fármacos para el paciente **{safe_get(p_info, 1)}** con un TFG actual de **{tfg_activo} mL/min/1.73m²**.")
        
        def sugerir_farmaco(nombre, tfg):
            if nombre == "Metformina":
                if tfg < 30: return "🔴 **CONTRAINDICADA.** Suspender de inmediato por alto riesgo de acidosis láctica."
                elif tfg < 45: return "🟡 **Ajustar dosis máxima a 1000 mg/día.** Requiere monitoreo estrecho de función renal."
                else: return "🟢 Dosis habitual permitida sin restricciones especiales."
            elif nombre == "Gabapentina":
                if tfg >= 60: return "🟢 300 - 400 mg cada 8 horas."
                elif tfg >= 30: return "🟡 200 - 300 mg cada 12 a 24 horas."
                elif tfg >= 15: return "🟠 200 - 300 mg cada 48 horas."
                else: return "🔴 100 - 300 mg administrado posterior a la sesión de hemodiálisis."
            elif nombre == "Enoxaparina":
                if tfg < 30: return "🟡 **Ajuste profiláctico / terapéutico:** Reducir la dosis un 50% o vigilar anti-Xa."
                else: return "🟢 Dosis estándar según indicación tromboprofiláctica."
            elif nombre == "Nitrofurantoína":
                if tfg < 45: return "🔴 **CONTRAINDICADA.** Ineficaz y con alta acumulación de toxicidad sistémica."
                else: return "🟢 Dosis habitual en infección urinaria baja."
            elif nombre == "Vancomicina":
                return "⚠️ **Requiere protocolo por niveles valle plasmáticos.** Espaciar intervalos y monitorizar función renal estrechamente."
            return "Consulte guía de ajuste renal específica para este fármaco."

        f_seleccionado = st.selectbox("Seleccione fármaco crítico a evaluar", ["Metformina", "Gabapentina", "Enoxaparina", "Nitrofurantoína", "Vancomicina"])
        dictamen = sugerir_farmaco(f_seleccionado, tfg_activo)
        st.warning(dictamen)
        
        st.markdown("---")
        st.subheader("Registro en Receta Activa del Paciente")
        nuevo_med = st.text_input("Nombre del Medicamento y Dosis sugerida")
        if st.button("Guardar en Receta"):
            if nuevo_med:
                cursor.execute("INSERT INTO prescripciones (cedula, medicamento) VALUES (?, ?)", (paciente_activo_ci, nuevo_med))
                conn.commit()
                st.success("¡Medicamento agregado al tratamiento activo!")
                st.rerun()
        
        st.markdown("### Medicación Actual Prescrita:")
        cursor.execute("SELECT id, medicamento FROM prescripciones WHERE cedula = ?", (paciente_activo_ci,))
        rx_lista = cursor.fetchall()
        if rx_lista:
            for rx in rx_lista:
                col_m1, col_m2 = st.columns([8, 2])
                col_m1.write(f"- {rx[1]}")
                if col_m2.button("Eliminar", key=f"del_rx_{rx[0]}"):
                    cursor.execute("DELETE FROM prescripciones WHERE id = ?", (rx[0],))
                    conn.commit()
                    st.rerun()
        else:
            st.info("No hay medicamentos registrados en este esquema.")

    with tab_kfre:
        st.header("Calculadora KFRE & Evolución de TFG")
        
        st.subheader("Calculadora KFRE (Riesgo de Fallo Renal)")
        k_tfg = st.number_input("TFG actual (mL/min/1.73m²)", value=float(tfg_activo))
        k_acr = st.number_input("ACR actual (mg/g)", value=100.0)
        if st.button("Calcular Riesgo KFRE"):
            sexo_val = safe_get(p_info, 3, "Masculino")
            is_m = 1 if sexo_val == "Masculino" else 0
            edad_val = int(safe_get(p_info, 2, 50))
            lp = -0.2201 * ((edad_val/10)-7.03) + 0.2467 * (is_m-0.564) - 0.5567 * ((k_tfg/5)-7.22) + 0.4510 * (math.log(k_acr/30)-0.147)
            r2 = (1 - (0.9832 ** math.exp(lp))) * 100
            r5 = (1 - (0.9365 ** math.exp(lp))) * 100
            st.metric("Riesgo a 2 Años", f"{round(r2, 2)} %")
            st.metric("Riesgo a 5 Años", f"{round(r5, 2)} %")
            
        st.markdown("---")
        st.subheader("📉 Evolución Histórica del Filtrado Glomerular (TFG)")
        cursor.execute("SELECT tfg FROM evolucion_tfg WHERE cedula = ?", (paciente_activo_ci,))
        tfgs = [r[0] for r in cursor.fetchall()]
        if tfgs:
            st.line_chart(tfgs)
        else:
            st.info("Aún no hay suficientes cálculos de TFG registrados para graficar.")

    with tab_dialisis:
        st.header("Controles y Estudios Pendientes")
        control_txt = st.text_input("Nombre del Estudio (Ej: Perfil Renal / Eco Doppler)")
        dias_c = st.number_input("Días para el control", value=90)
        if st.button("Programar Control"):
            f_meta = str(date.today() + timedelta(days=int(dias_c)))
            cursor.execute("INSERT INTO controles (cedula, estudio, fecha) VALUES (?, ?, ?)", (paciente_activo_ci, control_txt, f_meta))
            conn.commit()
            st.success("¡Control programado!")
            st.rerun()
            
        st.markdown("---")
        cursor.execute("SELECT estudio, fecha FROM controles WHERE cedula = ?", (paciente_activo_ci,))
        controles_lista = cursor.fetchall()
        if controles_lista:
            for c in controles_lista:
                st.warning(f"📌 {c[0]} — Fecha estimada: {c[1]}")
        else:
            st.info("No hay controles pendientes.")

    with tab_pdf:
        st.header("Generación de Informe y Reportes")
        cursor.execute("SELECT medicamento FROM prescripciones WHERE cedula = ?", (paciente_activo_ci,))
        prescs_pdf = cursor.fetchall()
        
        pdf_bytes = generar_pdf_paciente(p_info, prescs_pdf)
        st.download_button(
            label="📥 Descargar Informe Clínico Oficial en PDF",
            data=pdf_bytes,
            file_name=f"Informe_{safe_get(p_info, 1, 'Paciente').replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
else:
    st.info("👈 Selecciona o registra un paciente en la barra lateral izquierda para abrir su **Ficha de Atención** unificada.")