# ACERO Y SAL — RPG naval con buques reales

Juego web de rol y combate naval por turnos. Comandas una flota de **58 buques históricos reales**, formas oficiales, mejoras cada nave y completas una campaña de 10 capítulos inspirada en la historia naval.

Sitio jugable: [`game/index.html`](game/index.html)

## Qué incluye

- **58 buques reales** con datos históricos: HMS Victory, USS Monitor, HMS Dreadnought, HMS Hood, Bismarck, USS Iowa, Yamato, USS Enterprise, Akagi, U-96, PT-109, Scharnhorst, Richelieu, Roma, Shōkaku, USS Tang y muchos más.
- **8 roles de combate**: acorazados, portaaviones, cruceros, destructores, submarinos, lanchas torpederas, ironclads y fragatas.
- **Combate por turnos**: cañoneo, torpedos, maniobras evasivas, reparaciones y una habilidad especial por rol (andanada de precisión, oleada aérea, inmersión, cortina de humo, etc.).
- **Puente de mando**: pilota tu buque en tiempo real con WASD/flechas, joystick táctil o clic para disparar. Acelera, gira, deja estela, esquiva islas y hunde blancos de práctica para ganar créditos.
- **Progresión RPG**: nivel de comandante, 7 habilidades, puntos de habilidad, XP por buque, módulos de cañones/blindaje/motores y 13 oficiales históricos con bonus.
- **Campaña narrativa de 10 capítulos** con flotas fijas, jefes históricos, recompensas únicas (buques y oficiales) y desbloqueo progresivo.
- **19 logros** con recompensas en créditos y XP.
- **Buscador y filtros** de buques por rol, nación y tier en Astillero y Códice.
- **Flota y astillero**: compra buques únicos, activa hasta 4 unidades según tu nivel, repara daños y asigna oficiales.
- **Operaciones dinámicas** con recompensas, operaciones especiales contra buques capitales y guardado automático en `localStorage`.
- **Guardado en la nube con Firebase**: autenticación anónima + Firestore. La partida se sincroniza automáticamente y se restaura al recargar.
- **Códice histórico** con ficha, armamento, desplazamiento, tripulación e historia de cada buque.
- Interfaz responsive, sonido procedural (sin archivos externos) y funcionamiento 100% estático.

## Cómo jugar

Abre `game/index.html` en un navegador, o sirve la carpeta `game/` con cualquier servidor estático.

```bash
npx serve game
```

En el juego: elige buque insignia, ve a **Operaciones**, despliega tu flota y combate por turnos. Repara en **Flota** y compra unidades en **Astillero**.

La pestaña **Campaña** ofrece 10 capítulos con historia, flotas fijas y recompensas exclusivas. **Mando** muestra los logros y las 7 habilidades del comandante.

En **Puente** puedes tomar el timón y manejar el buque con física naval:

- `W` / `↑` sube un paso el telégrafo de máquina; `S` / `↓` lo baja.
- El telégrafo va de **ATRÁS TODA** a **AVANTE FLANCO**, pasando por PARADO, DESPACIO, MEDIA y TODA.
- `A` / `←` y `D` / `→` mueven el timón de forma progresiva (hasta ±35°). Al soltar, el timón vuelve al centro.
- `Espacio` dispara una andanada por ambas bandas; clic en el mar dispara hacia ese punto.
- En móvil usa el joystick (máquina y timón analógicos) y el botón **FUEGO**.
- El buque tiene **inercia, deriva y radio de giro reales**: los acorazados aceleran y giran mucho más lento que un destructor.
- El HUD muestra **velocidad, rumbo, ángulo de timón, telégrafo, corriente y aviso de VARADO**.
- Cada blanco hundido otorga puntos y hasta 10 recompensas de práctica de 15 créditos por sesión.

## Base de datos en Firebase

El juego usa **Cloud Firestore** con autenticación anónima para guardar la partida en la nube:

- Al abrir el juego se crea una sesión anónima y se lee el documento `saves/{uid}`.
- Cada cambio se guarda en `localStorage` y se sincroniza con Firestore (con retardo de 1,2 s).
- El indicador `NUBE · ON` de la cabecera muestra el estado. Al pulsarlo se fuerza una sincronización.
- Si Firestore no está disponible, el juego sigue funcionando solo con `localStorage`.

Configuración ya aplicada en el proyecto `juego-e0d5f`:

- Firestore en modo producción con las reglas de `firestore.rules`:
  cada usuario solo puede leer y escribir su propio documento.
- Autenticación anónima habilitada.
- Configuración web pública en `game/assets/firebase-config.js`.
- Reglas desplegadas con `firebase deploy --only firestore:rules`.

### Sobre las cuotas y los aumentos

No hace falta pedir ningún aumento para este juego. Firestore incluye una cuota diaria gratuita muy superior a lo que consume una partida normal (lecturas, escrituras, eliminaciones y 1 GiB de almacenamiento), y el proyecto ya está en el plan Blaze por usar App Hosting.

Si algún día la consola muestra que se superó una cuota:

1. Revisa el consumo en Firebase Console → Firestore → Uso.
2. Para solicitar más capacidad: Google Cloud Console → IAM y administración → Cuotas, filtra por **Cloud Firestore**, selecciona la cuota y pulsa **Editar cuota** / **Solicitar aumento**.
3. Firestore escala solo; no hay que "aumentar la base de datos" manualmente.

> El guardado en la nube queda vinculado al navegador mediante la sesión anónima. Para llevarlo a otro dispositivo habría que añadir inicio de sesión con Google (siguiente paso opcional).

## Centro de Mando Nexus

La página **Nexus** (`/nexus/`) comparte la misma sesión y la misma base de datos que el juego. Desde ella puedes:

- Ver el estado de conexión con Firestore y el UID de la sesión anónima.
- Consultar la partida guardada: nivel, créditos, operaciones, flota y poder naval.
- **Descargar una copia** de la partida en JSON.
- **Restaurar una copia** en Firestore para usarla en otro navegador.

Enlace directo: https://h4ck3r-zone--juego-e0d5f.us-east4.hosted.app/nexus/

El acceso está protegido por las reglas de `firestore.rules`: cada sesión solo puede leer y escribir su documento `saves/{uid}`.

## Instalar en Linux Mint

### Opción A: paquete .deb

Descarga el paquete desde [Releases](https://github.com/GonzalitoDev/h4ck3r-zone/releases) y instálalo:

```bash
wget https://github.com/GonzalitoDev/h4ck3r-zone/releases/latest/download/acero-y-sal_1.1.0_all.deb
sudo apt install ./acero-y-sal_1.1.0_all.deb
```

Después búscalo en el menú como **ACERO Y SAL**. El lanzador sirve el juego localmente en `http://127.0.0.1:8787/` y abre el navegador.

Dependencias instaladas automáticamente: `python3`, `curl` y `xdg-utils`.

### Opción B: instalación de usuario (sin root)

```bash
git clone https://github.com/GonzalitoDev/h4ck3r-zone.git
cd h4ck3r-zone
bash packaging/linux/install-user.sh
```

Crea el lanzador en el menú y los archivos en `~/.local/share/acero-y-sal`.

### Desinstalar

```bash
sudo apt remove acero-y-sal
# o, si usaste la instalación de usuario:
rm -rf ~/.local/share/acero-y-sal ~/.local/share/applications/acero-y-sal.desktop ~/.local/share/icons/hicolor/scalable/apps/acero-y-sal.svg
```

### Construir el .deb

En Linux Mint/Ubuntu:

```bash
bash packaging/linux/build-deb.sh
# genera dist/acero-y-sal_<version>_all.deb
```

También se compila automáticamente en GitHub Actions al publicar un tag `v*` y adjunta el `.deb` al release.

## Publicar con Firebase

El proyecto está preparado para las dos opciones:

### Firebase Hosting (recomendado para sitio estático)

```bash
npm install -g firebase-tools
firebase login
firebase deploy --only hosting
```

La configuración ya apunta al proyecto `juego-e0d5f` (`.firebaserc`) y publica la carpeta `game/` (`firebase.json`).

### Firebase App Hosting

El backend `h4ck3r-zone` puede desplegar este repositorio directamente porque incluye:

- `package.json` con scripts `build` y `start` requeridos por App Hosting.
- `server.mjs`: servidor Express que sirve `game/` en `process.env.PORT`.
- `apphosting.yaml`: configuración de Cloud Run.
- `firebase.json` con el bloque `apphosting`.

```bash
firebase deploy --only apphosting
```

También puedes conectar el repositorio desde la consola de Firebase y cada `git push` desplegará automáticamente.

## Desarrollo local

```bash
npm install
npm start
# http://localhost:8080
```

## Estructura

```
game/
  index.html
  nexus/
    index.html      Centro de Mando Nexus: partida en la nube, copias y restauración
    nexus.css
    nexus.js
  assets/
    data.js            datos de buques, roles, oficiales y operaciones
    firebase-config.js configuración pública de la Web App de Firebase
    core.js            estado, guardado, estadísticas y gráficos SVG
    cloud.js           Firestore: sesión anónima y guardado en la nube
    ui.js              cabecera, menú, mando, flota y modales
    screens.js         operaciones, astillero y códice
    bridge.js          puente de mando: pilotaje, físicas, islas y cañones
    battle.js          motor de combate, resultados e inicio
    game.css           estilos
server.mjs             servidor estático para App Hosting
firebase.json          Firebase Hosting + Firestore + App Hosting
firestore.rules        reglas de seguridad de la base de datos
apphosting.yaml        configuración de Cloud Run
packaging/linux/       lanzador, icono, .desktop, instalador y build-deb.sh
.github/workflows/     compilación automática del paquete .deb
```

## Nota

Los valores de combate son una abstracción jugable. Los datos históricos (año, eslora, desplazamiento, tripulación y armamento) son aproximados y se incluyen con fines educativos.
