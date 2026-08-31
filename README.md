# Simulador Interactivo de Comunicación Digital

Simulador educativo en Streamlit que muestra las etapas de un sistema
de comunicación digital: fuente, codificación de fuente, codificación
de canal (repetición ×3), modulación BPSK, canal con ruido AWGN e
interferencia, demodulación, decodificación de canal (votación por
mayoría) y decodificación de fuente.

## Cómo desplegar en Streamlit Community Cloud (gratis)

### 1. Sube el proyecto a GitHub
1. Crea una cuenta en [github.com](https://github.com) si no tienes una.
2. Crea un repositorio nuevo (puede ser público o privado), por ejemplo
   `simulador-comunicaciones`.
3. Sube estos dos archivos al repositorio:
   - `app3.py`
   - `requirements.txt`

   Puedes hacerlo arrastrando los archivos directamente en la interfaz
   web de GitHub ("Add file" → "Upload files"), sin necesidad de usar
   la terminal ni git.

### 2. Despliega en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io).
2. Inicia sesión con tu cuenta de GitHub (te pedirá autorizar acceso).
3. Haz clic en **"New app"**.
4. Selecciona:
   - **Repository:** el repositorio que acabas de crear
   - **Branch:** `main`
   - **Main file path:** `app3.py`
5. Haz clic en **"Deploy"**.
6. Espera 1-2 minutos mientras instala las dependencias. Cuando
   termine, tu app estará disponible en una URL del tipo:
   `https://tu-usuario-simulador-comunicaciones.streamlit.app`

### 3. Entrega en Classroom
- Copia esa URL y pégala como enlace de entrega en Classroom.
- Recomendado: adjunta también `app3.py` como respaldo, por si el
  docente prefiere revisar el código directamente o el link deja de
  estar disponible más adelante.

## Ejecutar localmente (opcional)
```bash
pip install -r requirements.txt
streamlit run app3.py
```
