# ACERO Y SAL — RPG naval con buques reales

Juego web de rol y combate naval por turnos. Comandas una flota de **28 buques históricos reales**, formas oficiales, mejoras cada nave y completas operaciones inspiradas en la historia naval.

Sitio jugable: [`game/index.html`](game/index.html)

## Qué incluye

- **28 buques reales** con datos históricos: HMS Victory, USS Monitor, HMS Dreadnought, HMS Hood, Bismarck, USS Iowa, Yamato, USS Enterprise, Akagi, U-96, PT-109 y más.
- **8 roles de combate**: acorazados, portaaviones, cruceros, destructores, submarinos, lanchas torpederas, ironclads y fragatas.
- **Combate por turnos**: cañoneo, torpedos, maniobras evasivas, reparaciones y una habilidad especial por rol (andanada de precisión, oleada aérea, inmersión, cortina de humo, etc.).
- **Progresión RPG**: nivel de comandante, 5 habilidades, puntos de habilidad, XP por buque, módulos de cañones/blindaje/motores y 7 oficiales históricos con bonus.
- **Flota y astillero**: compra buques únicos, activa hasta 4 unidades según tu nivel, repara daños y asigna oficiales.
- **Operaciones dinámicas** con recompensas, operaciones especiales contra buques capitales y guardado automático en `localStorage`.
- **Códice histórico** con ficha, armamento, desplazamiento, tripulación e historia de cada buque.
- Interfaz responsive, sonido procedural (sin archivos externos) y funcionamiento 100% estático.

## Cómo jugar

Abre `game/index.html` en un navegador, o sirve la carpeta `game/` con cualquier servidor estático.

```bash
npx serve game
```

En el juego: elige buque insignia, ve a **Operaciones**, despliega tu flota y combate por turnos. Repara en **Flota** y compra unidades en **Astillero**.

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
    data.js      datos de buques, roles, oficiales y operaciones
    core.js      estado, guardado, estadísticas y gráficos SVG
    ui.js        cabecera, menú, mando, flota y modales
    screens.js   operaciones, astillero y códice
    battle.js    motor de combate, resultados e inicio
    game.css     estilos
server.mjs       servidor estático para App Hosting
firebase.json    Firebase Hosting + App Hosting
apphosting.yaml  configuración de Cloud Run
```

## Nota

Los valores de combate son una abstracción jugable. Los datos históricos (año, eslora, desplazamiento, tripulación y armamento) son aproximados y se incluyen con fines educativos.
