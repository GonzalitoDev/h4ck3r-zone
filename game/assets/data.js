'use strict';

const SHIP_ROLES = {
  battleship: {
    label: 'Acorazado',
    special: { name: 'Andanada de precisión', desc: '1,5x daño de cañón ignorando el 40% del blindaje.', cd: 3, target: true, kind: 'precision' }
  },
  carrier: {
    label: 'Portaaviones',
    special: { name: 'Oleada aérea', desc: 'Ataca a toda la flota enemiga con 0,7x del poder aereo.', cd: 4, target: false, kind: 'airstrike' }
  },
  cruiser: {
    label: 'Crucero',
    special: { name: 'Fuego sostenido', desc: '1,25x daño e incendia al objetivo durante 2 turnos.', cd: 2, target: true, kind: 'burning' }
  },
  destroyer: {
    label: 'Destructor',
    special: { name: 'Cortina de humo', desc: 'Toda tu flota gana +25 de evasión durante 2 turnos.', cd: 3, target: false, kind: 'smoke' }
  },
  submarine: {
    label: 'Submarino',
    special: { name: 'Inmersion', desc: '+60 evasión y el próximo ataque sera crítico.', cd: 4, target: false, kind: 'dive' }
  },
  torpedo: {
    label: 'Lanchera torpedera',
    special: { name: 'Ataque relámpago', desc: '2,2x daño de torpedo ignorando el 50% del blindaje.', cd: 3, target: true, kind: 'torpedo_burst' }
  },
  ironclad: {
    label: 'Ironclad',
    special: { name: 'Embate', desc: '1,4x daño y reduce la velocidad del objetivo 2 turnos.', cd: 3, target: true, kind: 'ram' }
  },
  frigate: {
    label: 'Fragata histórica',
    special: { name: 'Bordada', desc: '1,3x daño y recupera el 12% del casco.', cd: 3, target: true, kind: 'board' }
  }
};

const SHIPS = [
  {
    id: 'victory', name: 'HMS Victory', role: 'frigate', nation: 'Reino Unido', year: 1765, tier: 1,
    length: '69 m', displacement: '3.556 t', crew: '850', armament: '104 cañones de avancarga',
    stats: { hp: 240, armor: 24, firepower: 56, torpedo: 0, aa: 0, speed: 8, evade: 5 },
    cost: 650, unlockLevel: 1,
    history: 'Navío insignia del almirante Horatio Nelson en la batalla de Trafalgar (1805). Se conserva en Portsmouth como museo flotante.'
  },
  {
    id: 'constitution', name: 'USS Constitution', role: 'frigate', nation: 'Estados Unidos', year: 1797, tier: 1,
    length: '62 m', displacement: '2.200 t', crew: '450', armament: '44 cañones',
    stats: { hp: 230, armor: 22, firepower: 48, torpedo: 0, aa: 0, speed: 13, evade: 10 },
    cost: 700, unlockLevel: 1,
    history: 'Fragata de la Armada de los Estados Unidos bautizada por George Washington. Sigue a flote y es el buque de guerra mas antiguo en servicio.'
  },
  {
    id: 'monitor', name: 'USS Monitor', role: 'ironclad', nation: 'Estados Unidos', year: 1862, tier: 1,
    length: '52 m', displacement: '987 t', crew: '62', armament: '2 cañones Dahlgren de 279 mm',
    stats: { hp: 300, armor: 62, firepower: 44, torpedo: 0, aa: 0, speed: 8, evade: 6 },
    cost: 700, unlockLevel: 1,
    history: 'Primer ironclad de la Union. Se enfrento al CSS Virginia en el duelo de Hampton Roads, el primer combate entre buques blindados.'
  },
  {
    id: 'virginia', name: 'CSS Virginia', role: 'ironclad', nation: 'Estados Confederados', year: 1862, tier: 1,
    length: '84 m', displacement: '4.100 t', crew: '250', armament: '10 cañones y espolon de hierro',
    stats: { hp: 330, armor: 66, firepower: 42, torpedo: 0, aa: 0, speed: 5, evade: 4 },
    cost: 750, unlockLevel: 1,
    history: 'Ironclad confederado construido sobre el casco del USS Merrimack. Combatió al USS Monitor en 1862.'
  },
  {
    id: 'warrior', name: 'HMS Warrior', role: 'ironclad', nation: 'Reino Unido', year: 1860, tier: 1,
    length: '127 m', displacement: '9.210 t', crew: '705', armament: '40 cañones',
    stats: { hp: 360, armor: 60, firepower: 50, torpedo: 0, aa: 0, speed: 14, evade: 9 },
    cost: 900, unlockLevel: 2,
    history: 'Primer ironclad oceanico del mundo. Su casco de hierro y su velocidad lo hicieron invulnerable a la artillería de su época.'
  },
  {
    id: 'pt109', name: 'PT-109', role: 'torpedo', nation: 'Estados Unidos', year: 1942, tier: 1,
    length: '24 m', displacement: '56 t', crew: '17', armament: '4 tubos de torpedo y 2 cañones de 20 mm',
    stats: { hp: 150, armor: 4, firepower: 16, torpedo: 88, aa: 8, speed: 41, evade: 62 },
    cost: 450, unlockLevel: 1,
    history: 'Lanchera torpedera Elco de la Armada de EE. UU. Alcanzo fama por el mando del teniente John F. Kennedy en el Pacífico en 1943.'
  },
  {
    id: 'mikasa', name: 'Mikasa', role: 'battleship', nation: 'Japón', year: 1902, tier: 2,
    length: '132 m', displacement: '15.140 t', crew: '830', armament: '4x305 mm y 14x152 mm',
    stats: { hp: 450, armor: 58, firepower: 64, torpedo: 10, aa: 0, speed: 18, evade: 12 },
    cost: 1400, unlockLevel: 3,
    history: 'Buque insignia del almirante Togo en la batalla de Tsushima (1905). Es el ultimo acorazado pre-dreadnought que se conserva.'
  },
  {
    id: 'dreadnought', name: 'HMS Dreadnought', role: 'battleship', nation: 'Reino Unido', year: 1906, tier: 2,
    length: '161 m', displacement: '18.420 t', crew: '700', armament: '10x305 mm',
    stats: { hp: 500, armor: 62, firepower: 80, torpedo: 0, aa: 0, speed: 21, evade: 12 },
    cost: 1800, unlockLevel: 4,
    history: 'Inicio la carrera armamentística naval del siglo XX: su diseno "all-big-gun" dejo obsoletos a todos los acorazados anteriores.'
  },
  {
    id: 'vondertann', name: 'SMS Von der Tann', role: 'battleship', nation: 'Alemania', year: 1910, tier: 2,
    length: '171 m', displacement: '19.370 t', crew: '923', armament: '8x280 mm',
    stats: { hp: 470, armor: 46, firepower: 72, torpedo: 20, aa: 0, speed: 27, evade: 22 },
    cost: 1700, unlockLevel: 4,
    history: 'Primer crucero de batalla alemán. Combatió en Jutlandia (1916) y sobrevivió pese a recibir numerosos impactos.'
  },
  {
    id: 'texas', name: 'USS Texas', role: 'battleship', nation: 'Estados Unidos', year: 1914, tier: 2,
    length: '175 m', displacement: '27.000 t', crew: '1.042', armament: '10x356 mm',
    stats: { hp: 540, armor: 70, firepower: 78, torpedo: 0, aa: 15, speed: 21, evade: 12 },
    cost: 2000, unlockLevel: 5,
    history: 'Acorazado veterano de ambas guerras mundiales. Apoyo los desembarcos de Normandía y es hoy un museo en Texas.'
  },
  {
    id: 'belfast', name: 'HMS Belfast', role: 'cruiser', nation: 'Reino Unido', year: 1939, tier: 3,
    length: '187 m', displacement: '11.550 t', crew: '781', armament: '12x152 mm y 6 tubos de torpedo',
    stats: { hp: 430, armor: 42, firepower: 62, torpedo: 35, aa: 48, speed: 32, evade: 32 },
    cost: 1600, unlockLevel: 3,
    history: 'Crucero ligero británico. Participo en la caza del Scharnhorst y en el Día D. Hoy es museo en Londres.'
  },
  {
    id: 'indianapolis', name: 'USS Indianapolis', role: 'cruiser', nation: 'Estados Unidos', year: 1932, tier: 3,
    length: '186 m', displacement: '9.950 t', crew: '621', armament: '9x203 mm',
    stats: { hp: 420, armor: 36, firepower: 60, torpedo: 30, aa: 38, speed: 32, evade: 30 },
    cost: 1550, unlockLevel: 3,
    history: 'Crucero pesado que transporto componentes de la bomba atómica. Fue hundido por un submarino japones en 1945.'
  },
  {
    id: 'fletcher', name: 'USS Fletcher', role: 'destroyer', nation: 'Estados Unidos', year: 1942, tier: 3,
    length: '115 m', displacement: '2.500 t', crew: '273', armament: '5x127 mm y 10 tubos de torpedo',
    stats: { hp: 290, armor: 18, firepower: 44, torpedo: 82, aa: 45, speed: 36, evade: 54 },
    cost: 1450, unlockLevel: 1,
    history: 'Primer buque de la clase de destructores mas numerosa de la historia. Participo en casi todas las campañas del Pacífico.'
  },
  {
    id: 'kelly', name: 'HMS Kelly', role: 'destroyer', nation: 'Reino Unido', year: 1939, tier: 3,
    length: '108 m', displacement: '1.760 t', crew: '183', armament: '6x120 mm y 10 tubos de torpedo',
    stats: { hp: 260, armor: 16, firepower: 38, torpedo: 72, aa: 28, speed: 36, evade: 55 },
    cost: 1300, unlockLevel: 3,
    history: 'Destructor de la clase K, buque insignia de Lord Mountbatten. Combatió en Noruega y en la evacuacion de Creta.'
  },
  {
    id: 'yukikaze', name: 'Yukikaze', role: 'destroyer', nation: 'Japón', year: 1940, tier: 3,
    length: '118 m', displacement: '2.490 t', crew: '228', armament: '6x127 mm y 8 tubos de torpedo',
    stats: { hp: 280, armor: 18, firepower: 40, torpedo: 80, aa: 28, speed: 35, evade: 52 },
    cost: 1400, unlockLevel: 4,
    history: 'El "destructor afortunado": sobrevivió a la guerra sin sufrir daños graves pese a combatir en las mayores batallas navales japonesas.'
  },
  {
    id: 'u96', name: 'U-96', role: 'submarine', nation: 'Alemania', year: 1940, tier: 3,
    length: '67 m', displacement: '769 t', crew: '45', armament: '14 torpedos y cañón de 88 mm',
    stats: { hp: 220, armor: 12, firepower: 12, torpedo: 94, aa: 6, speed: 19, evade: 38 },
    cost: 1500, unlockLevel: 1,
    history: 'U-boat tipo VIIC de la Batalla del Atlántico. Su patrulla de 1941 inspiro la novela y la pelicula "Das Boot".'
  },
  {
    id: 'nautilus', name: 'USS Nautilus (SS-168)', role: 'submarine', nation: 'Estados Unidos', year: 1930, tier: 3,
    length: '113 m', displacement: '2.915 t', crew: '88', armament: '16 tubos de torpedo y 2x152 mm',
    stats: { hp: 250, armor: 14, firepower: 20, torpedo: 88, aa: 12, speed: 17, evade: 28 },
    cost: 1350, unlockLevel: 3,
    history: 'Submarino de crucero de la Armada de EE. UU. Realizo misiones de reconocimiento en Midway y en las islas Gilbert.'
  },
  {
    id: 'grafSpee', name: 'Admiral Graf Spee', role: 'cruiser', nation: 'Alemania', year: 1936, tier: 3,
    length: '186 m', displacement: '16.020 t', crew: '1.150', armament: '6x283 mm',
    stats: { hp: 500, armor: 50, firepower: 70, torpedo: 45, aa: 30, speed: 28, evade: 24 },
    cost: 2400, unlockLevel: 6,
    history: 'El "acorazado de bolsillo" que atacó el tráfico mercante aliado en el Atlántico Sur hasta la batalla del Río de la Plata.'
  },
  {
    id: 'hood', name: 'HMS Hood', role: 'battleship', nation: 'Reino Unido', year: 1920, tier: 3,
    length: '262 m', displacement: '46.680 t', crew: '1.418', armament: '8x381 mm',
    stats: { hp: 650, armor: 54, firepower: 86, torpedo: 0, aa: 30, speed: 31, evade: 22 },
    cost: 2600, unlockLevel: 6,
    history: 'Orgullo de la Royal Navy durante dos decadas. Fue hundido por el Bismarck en 1941 con la pérdida de casi toda su tripulación.'
  },
  {
    id: 'prinzEugen', name: 'Prinz Eugen', role: 'cruiser', nation: 'Alemania', year: 1940, tier: 3,
    length: '212 m', displacement: '18.750 t', crew: '1.600', armament: '8x203 mm y 12 tubos de torpedo',
    stats: { hp: 520, armor: 52, firepower: 68, torpedo: 48, aa: 42, speed: 32, evade: 28 },
    cost: 2200, unlockLevel: 5,
    history: 'Crucero pesado alemán que acompañó al Bismarck en la Operación Rheinübung. Sobrevivio a la guerra y fue usado como buque objetivo nuclear.'
  },
  {
    id: 'warspite', name: 'HMS Warspite', role: 'battleship', nation: 'Reino Unido', year: 1915, tier: 4,
    length: '196 m', displacement: '32.500 t', crew: '1.200', armament: '8x381 mm',
    stats: { hp: 740, armor: 76, firepower: 86, torpedo: 0, aa: 45, speed: 24, evade: 16 },
    cost: 3000, unlockLevel: 6,
    history: 'Veterana de Jutlandia, Narvik, Calabria y Normandía. Acumulo mas condecoraciones de batalla que cualquier otro buque británico.'
  },
  {
    id: 'nagato', name: 'Nagato', role: 'battleship', nation: 'Japón', year: 1920, tier: 4,
    length: '225 m', displacement: '39.120 t', crew: '1.368', armament: '8x410 mm',
    stats: { hp: 750, armor: 72, firepower: 88, torpedo: 0, aa: 40, speed: 26, evade: 16 },
    cost: 3200, unlockLevel: 7,
    history: 'Buque insignia de la Flota Combinada al mando de Yamamoto al inicio de la Guerra del Pacífico. Sobrevivio a la guerra como buque objetivo.'
  },
  {
    id: 'bismarck', name: 'Bismarck', role: 'battleship', nation: 'Alemania', year: 1940, tier: 4,
    length: '251 m', displacement: '50.300 t', crew: '2.200', armament: '8x380 mm',
    stats: { hp: 760, armor: 78, firepower: 90, torpedo: 0, aa: 55, speed: 30, evade: 18 },
    cost: 3800, unlockLevel: 7,
    history: 'Acorazado alemán que hundió al HMS Hood en 1941. Fue perseguido y destruido por la Royal Navy dias despues.'
  },
  {
    id: 'iowa', name: 'USS Iowa', role: 'battleship', nation: 'Estados Unidos', year: 1943, tier: 4,
    length: '270 m', displacement: '57.400 t', crew: '2.700', armament: '9x406 mm',
    stats: { hp: 800, armor: 80, firepower: 96, torpedo: 0, aa: 72, speed: 33, evade: 20 },
    cost: 4200, unlockLevel: 8,
    history: 'Clase de acorazados rapidos de la Armada de EE. UU. Sus 33 nudos y su artillería de 406 mm los hicieron temibles escoltas de portaaviones.'
  },
  {
    id: 'yamato', name: 'Yamato', role: 'battleship', nation: 'Japón', year: 1941, tier: 4,
    length: '263 m', displacement: '72.800 t', crew: '2.700', armament: '9x460 mm',
    stats: { hp: 860, armor: 84, firepower: 100, torpedo: 0, aa: 58, speed: 27, evade: 14 },
    cost: 4800, unlockLevel: 9,
    history: 'El acorazado mas grande jamas construido. Sus cañones de 460 mm eran los mayores montados a flote. Hundido en 1945.'
  },
  {
    id: 'enterprise', name: 'USS Enterprise (CV-6)', role: 'carrier', nation: 'Estados Unidos', year: 1938, tier: 4,
    length: '252 m', displacement: '25.500 t', crew: '2.200', armament: '90 aviones embarcados',
    stats: { hp: 620, armor: 32, firepower: 84, torpedo: 42, aa: 68, speed: 32, evade: 26 },
    cost: 4000, unlockLevel: 8,
    history: 'La "Big E" fue el buque mas condecorado de la Armada de EE. UU. en la Segunda Guerra Mundial. Combatió en Midway, Guadalcanal y Okinawa.'
  },
  {
    id: 'akagi', name: 'Akagi', role: 'carrier', nation: 'Japón', year: 1927, tier: 4,
    length: '261 m', displacement: '36.500 t', crew: '2.000', armament: '91 aviones embarcados',
    stats: { hp: 600, armor: 28, firepower: 82, torpedo: 46, aa: 52, speed: 31, evade: 24 },
    cost: 3700, unlockLevel: 7,
    history: 'Portaaviones de la Flota Combinada. Lanzo el ataque a Pearl Harbor y fue hundido en la batalla de Midway en 1942.'
  },
  {
    id: 'arkRoyal', name: 'HMS Ark Royal', role: 'carrier', nation: 'Reino Unido', year: 1938, tier: 4,
    length: '244 m', displacement: '22.000 t', crew: '1.600', armament: '72 aviones embarcados',
    stats: { hp: 580, armor: 26, firepower: 74, torpedo: 40, aa: 58, speed: 30, evade: 24 },
    cost: 3500, unlockLevel: 7,
    history: 'Portaaviones británico clave en la caza del Bismarck: sus Swordfish danaron el timón del acorazado alemán.'
  }
];

const SHIP_MAP = {};
SHIPS.forEach(function (ship) { SHIP_MAP[ship.id] = ship; });

const OFFICERS = [
  {
    id: 'nelson', name: 'Horatio Nelson', title: 'Almirante de la Royal Navy',
    bonus: 'accuracy', value: 0.06, cost: 1200, unlockLevel: 2,
    desc: 'Punteria de toda la flota +6%. Su instinto tactico inspira a la tripulación.'
  },
  {
    id: 'nimitz', name: 'Chester Nimitz', title: 'Comandante de la Flota del Pacífico',
    bonus: 'damage', value: 0.10, cost: 1800, unlockLevel: 4,
    desc: 'Daño de cañón +10%. Coordina ataques combinados con precision quirurgica.'
  },
  {
    id: 'tovey', name: 'John Tovey', title: 'Comandante de la Home Fleet',
    bonus: 'armor', value: 0.12, cost: 1600, unlockLevel: 3,
    desc: 'Blindaje efectivo +12%. Sabe mantener la formacion bajo fuego enemigo.'
  },
  {
    id: 'yamamoto', name: 'Isoroku Yamamoto', title: 'Almirante de la Flota Combinada',
    bonus: 'crit', value: 0.08, cost: 2200, unlockLevel: 5,
    desc: 'Probabilidad de crítico +8%. Busca el punto debil del enemigo con cada salva.'
  },
  {
    id: 'donitz', name: 'Karl Donitz', title: 'Comandante de la fuerza submarina',
    bonus: 'torpedo', value: 0.15, cost: 1700, unlockLevel: 4,
    desc: 'Daño de torpedo +15%. Sus maniobras de manada hacen letal cada lanzamiento.'
  },
  {
    id: 'cunningham', name: 'Andrew Cunningham', title: 'Comandante del Mediterráneo',
    bonus: 'repair', value: 0.35, cost: 1400, unlockLevel: 2,
    desc: 'Reparaciones de emergencia +35%. Sus ingenieros trabajan bajo cualquier fuego.'
  },
  {
    id: 'spruance', name: 'Raymond Spruance', title: 'Tactico de Midway',
    bonus: 'evade', value: 0.08, cost: 1900, unlockLevel: 4,
    desc: 'Evasion +8%. Anticipa la maniobra enemiga y coloca la flota en ventaja.'
  }
];

const OFFICER_MAP = {};
OFFICERS.forEach(function (officer) { OFFICER_MAP[officer.id] = officer; });

const OPS_TEMPLATES = [
  { name: 'Patrulla del Atlántico Norte', desc: 'Una formacion enemiga amenaza la ruta de los convoyes. Interceptala antes de que desaparezca en la niebla.' },
  { name: 'Escolta de convoy', desc: 'Protege el convoy de suministros. El enemigo intentara romper la linea por cualquier medio.' },
  { name: 'Caza de corsarios', desc: 'Un buque enemigo esta atacando el tráfico mercante. Encuentralo y neutralizalo.' },
  { name: 'Emboscada en el estrecho', desc: 'Aguarda en aguas cerradas y golpea cuando la flota enemiga entre en el paso.' },
  { name: 'Duelo de acorazados', desc: 'Inteligencia confirma la presencia de unidades capitales. Solo el mejor comandante volvera a puerto.' },
  { name: 'Golpe al puerto', desc: 'La base enemiga concentra repuestos y combustible. Un ataque rapido puede cambiar el equilibrio.' },
  { name: 'Tormenta en el Pacífico', desc: 'El mal tiempo reduce la visibilidad. La flota que mantenga la formacion dominara el combate.' },
  { name: 'Sombra en las profundidades', desc: 'Rastros de submarinos enemigos han sido detectados. La caza comienza ahora.' },
  { name: 'Linea de bloqueo', desc: 'Rompe el bloqueo enemigo y abre un corredor para tus fuerzas.' },
  { name: 'Reconocimiento forzado', desc: 'Avanza hacia aguas hostiles y elimina cualquier resistencia para obtener información.' }
];

const BOSS_OPS = [
  { name: 'OPERACION ESPECIAL: Cacería del Bismarck', desc: 'El acorazado mas peligroso del Atlántico ha roto el bloqueo. Hundelo antes de que alcance puerto.', ship: 'bismarck' },
  { name: 'OPERACION ESPECIAL: Tormenta de acero', desc: 'El Yamato lidera una fuerza de choque hacia tu posicion. Detenlo a cualquier costo.', ship: 'yamato' },
  { name: 'OPERACION ESPECIAL: Golpe al portaaviones', desc: 'La flota enemiga depende de un portaaviones. Destruye su cubierta y rompe su ofensiva.', ship: 'enterprise' },
  { name: 'OPERACION ESPECIAL: Orgullo de la Royal Navy', desc: 'Una unidad capital enemiga bloquea el paso. La artillería pesada decidira el duelo.', ship: 'hood' }
];

const STARTERS = ['fletcher', 'belfast', 'u96'];
