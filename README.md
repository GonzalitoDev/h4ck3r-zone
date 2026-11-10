# ACERO Y SAL — RPG naval con buques reales

Juego web de rol y combate naval por turnos. Comandas una flota de **28 buques históricos reales**, formas oficiales, mejoras cada nave y completas operaciones inspiradas en la historia naval.

Sitio jugable: [`game/index.html`](game/index.html)

## Qué incluye

- **28 buques reales** con datos históricos: HMS Victory, USS Monitor, HMS Dreadnought, HMS Hood, Bismarck, USS Iowa, Yamato, USS Enterprise, Akagi, U-96, PT-109 y más.
- **8 roles de combate**: acorazados, portaaviones, cruceros, destructores, submarinos, lanchas torpederas, ironclads y fragatas.
- **Combate por turnos**: cañoneo, torpedos, maniobras evasivas, reparaciones y una habilidad especial por rol (andanada de precisión, oleada aérea, inmersión, cortina de humo, etc.).
- **Puente de mando**: pilota tu buque en tiempo real con WASD/flechas, joystick táctil o clic para disparar. Acelera, gira, deja estela, esquiva islas y hunde blancos de práctica para ganar créditos.
- **Progresión RPG**: nivel de comandante, 5 habilidades, puntos de habilidad, XP por buque, módulos de cañones/blindaje/motores y 7 oficiales históricos con bonus.
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

En **Puente** puedes tomar el timón y manejar el buque libremente:

- `W` / `↑` acelerar, `S` / `↓` reducir o dar atrás.
- `A` / `←` y `D` / `→` girar.
- `Espacio` dispara una andanada por ambas bandas; clic en el mar dispara hacia ese punto.
- En móvil usa el joystick y el botón **FUEGO**.
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
```

## Nota

Los valores de combate son una abstracción jugable. Los datos históricos (año, eslora, desplazamiento, tripulación y armamento) son aproximados y se incluyen con fines educativos.
