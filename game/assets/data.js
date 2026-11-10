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
  },
  {
    id: 'seydlitz', name: 'SMS Seydlitz', role: 'battleship', nation: 'Alemania', year: 1913, tier: 2,
    length: '200 m', displacement: '28.550 t', crew: '1.068', armament: '10x280 mm',
    stats: { hp: 500, armor: 50, firepower: 76, torpedo: 20, aa: 0, speed: 28, evade: 24 },
    cost: 1900, unlockLevel: 5,
    history: 'Crucero de batalla alemán que resistió graves daños en Jutlandia. Su regreso a puerto con más de 5.000 toneladas de agua a bordo es legendario.'
  },
  {
    id: 'derfflinger', name: 'SMS Derfflinger', role: 'battleship', nation: 'Alemania', year: 1914, tier: 2,
    length: '210 m', displacement: '26.600 t', crew: '1.112', armament: '8x305 mm',
    stats: { hp: 520, armor: 52, firepower: 80, torpedo: 20, aa: 0, speed: 26, evade: 22 },
    cost: 2000, unlockLevel: 5,
    history: 'Apodado "el perro de hierro" por su resistencia en Jutlandia. Hundió al HMS Queen Mary con una salva en la santabárbara.'
  },
  {
    id: 'queenElizabeth', name: 'HMS Queen Elizabeth', role: 'battleship', nation: 'Reino Unido', year: 1915, tier: 2,
    length: '196 m', displacement: '33.000 t', crew: '950', armament: '8x381 mm',
    stats: { hp: 600, armor: 72, firepower: 82, torpedo: 0, aa: 20, speed: 24, evade: 14 },
    cost: 2400, unlockLevel: 5,
    history: 'Primer acorazado rápido de la Royal Navy. Su clase combinó cañones de 381 mm y 24 nudos, marcando un nuevo estándar.'
  },
  {
    id: 'arizona', name: 'USS Arizona', role: 'battleship', nation: 'Estados Unidos', year: 1916, tier: 2,
    length: '185 m', displacement: '31.400 t', crew: '1.512', armament: '12x356 mm',
    stats: { hp: 580, armor: 74, firepower: 80, torpedo: 0, aa: 20, speed: 21, evade: 12 },
    cost: 2200, unlockLevel: 5,
    history: 'Acorazado de la clase Pennsylvania. Se hundió en Pearl Harbor el 7 de diciembre de 1941 y hoy es un memorial.'
  },
  {
    id: 'princeOfWales', name: 'HMS Prince of Wales', role: 'battleship', nation: 'Reino Unido', year: 1941, tier: 4,
    length: '227 m', displacement: '43.786 t', crew: '1.500', armament: '10x356 mm',
    stats: { hp: 700, armor: 78, firepower: 88, torpedo: 0, aa: 60, speed: 28, evade: 18 },
    cost: 3400, unlockLevel: 7,
    history: 'Combatió al Bismarck junto al Hood y llevó a Churchill a Terranova. Fue hundido por aviones japoneses junto al Repulse en 1941.'
  },
  {
    id: 'kingGeorgeV', name: 'HMS King George V', role: 'battleship', nation: 'Reino Unido', year: 1940, tier: 4,
    length: '227 m', displacement: '42.000 t', crew: '1.422', armament: '10x356 mm',
    stats: { hp: 720, armor: 80, firepower: 86, torpedo: 0, aa: 55, speed: 28, evade: 18 },
    cost: 3500, unlockLevel: 8,
    history: 'Buque insignia de la Home Fleet. Participó en la caza final del Bismarck y en la escolta de convoyes del Ártico.'
  },
  {
    id: 'rodney', name: 'HMS Rodney', role: 'battleship', nation: 'Reino Unido', year: 1927, tier: 4,
    length: '216 m', displacement: '41.000 t', crew: '1.640', armament: '9x406 mm',
    stats: { hp: 700, armor: 76, firepower: 90, torpedo: 0, aa: 40, speed: 23, evade: 14 },
    cost: 3200, unlockLevel: 7,
    history: 'Acorazado de la clase Nelson. Junto al King George V redujo al Bismarck a un casco ardiendo en 1941.'
  },
  {
    id: 'scharnhorst', name: 'Scharnhorst', role: 'battleship', nation: 'Alemania', year: 1939, tier: 4,
    length: '235 m', displacement: '38.700 t', crew: '1.968', armament: '9x280 mm',
    stats: { hp: 690, armor: 74, firepower: 82, torpedo: 0, aa: 45, speed: 31, evade: 22 },
    cost: 3400, unlockLevel: 7,
    history: 'Crucero de batalla alemán que hundió al portaaviones HMS Glorious. Fue hundido en la batalla de North Cape en 1943.'
  },
  {
    id: 'gneisenau', name: 'Gneisenau', role: 'battleship', nation: 'Alemania', year: 1938, tier: 4,
    length: '235 m', displacement: '38.100 t', crew: '1.840', armament: '9x280 mm',
    stats: { hp: 680, armor: 72, firepower: 80, torpedo: 0, aa: 45, speed: 31, evade: 22 },
    cost: 3300, unlockLevel: 7,
    history: 'Gemelo del Scharnhorst. Participó en la Operación Cerberus, el audaz paso por el Canal de la Mancha en 1942.'
  },
  {
    id: 'vittorioVeneto', name: 'Vittorio Veneto', role: 'battleship', nation: 'Italia', year: 1940, tier: 4,
    length: '238 m', displacement: '45.963 t', crew: '1.830', armament: '9x381 mm',
    stats: { hp: 710, armor: 76, firepower: 88, torpedo: 0, aa: 50, speed: 30, evade: 20 },
    cost: 3500, unlockLevel: 8,
    history: 'Acorazado de la clase Littorio. Combatió en Matapan y estuvo a punto de ser alcanzado por un torpedo aéreo británico.'
  },
  {
    id: 'roma', name: 'Roma', role: 'battleship', nation: 'Italia', year: 1942, tier: 4,
    length: '240 m', displacement: '45.963 t', crew: '1.920', armament: '9x381 mm',
    stats: { hp: 730, armor: 78, firepower: 90, torpedo: 0, aa: 55, speed: 30, evade: 20 },
    cost: 3700, unlockLevel: 8,
    history: 'Uno de los acorazados más modernos de Italia. Fue hundido por bombas guiadas Fritz X alemanas en 1943.'
  },
  {
    id: 'richelieu', name: 'Richelieu', role: 'battleship', nation: 'Francia', year: 1940, tier: 4,
    length: '248 m', displacement: '48.500 t', crew: '1.550', armament: '8x380 mm',
    stats: { hp: 720, armor: 80, firepower: 92, torpedo: 0, aa: 50, speed: 30, evade: 20 },
    cost: 3700, unlockLevel: 8,
    history: 'Acorazado francés con toda su artillería principal montada en dos torres cuádruples a proa. Sirvió con los Aliados desde 1943.'
  },
  {
    id: 'washington', name: 'USS Washington', role: 'battleship', nation: 'Estados Unidos', year: 1941, tier: 4,
    length: '222 m', displacement: '45.500 t', crew: '1.772', armament: '9x406 mm',
    stats: { hp: 730, armor: 78, firepower: 90, torpedo: 0, aa: 60, speed: 28, evade: 18 },
    cost: 3600, unlockLevel: 8,
    history: 'Acorazado de la clase North Carolina. En 1942 hundió al acorazado japonés Kirishima en la batalla nocturna de Guadalcanal.'
  },
  {
    id: 'northCarolina', name: 'USS North Carolina', role: 'battleship', nation: 'Estados Unidos', year: 1941, tier: 4,
    length: '222 m', displacement: '45.500 t', crew: '2.339', armament: '9x406 mm',
    stats: { hp: 720, armor: 77, firepower: 88, torpedo: 0, aa: 65, speed: 28, evade: 18 },
    cost: 3500, unlockLevel: 8,
    history: 'Primer acorazado rápido de la clase North Carolina. Escoltó portaaviones y participó en casi todas las campañas del Pacífico.'
  },
  {
    id: 'shokaku', name: 'Shōkaku', role: 'carrier', nation: 'Japón', year: 1941, tier: 4,
    length: '257 m', displacement: '32.000 t', crew: '1.660', armament: '84 aviones embarcados',
    stats: { hp: 590, armor: 24, firepower: 84, torpedo: 48, aa: 55, speed: 34, evade: 26 },
    cost: 3800, unlockLevel: 8,
    history: 'Portaaviones japonés de la clase Shōkaku. Atacó Pearl Harbor, combatió en el Mar de Coral y fue hundido en Filipinas en 1944.'
  },
  {
    id: 'zuikaku', name: 'Zuikaku', role: 'carrier', nation: 'Japón', year: 1941, tier: 4,
    length: '257 m', displacement: '32.000 t', crew: '1.660', armament: '84 aviones embarcados',
    stats: { hp: 590, armor: 24, firepower: 84, torpedo: 48, aa: 55, speed: 34, evade: 26 },
    cost: 3800, unlockLevel: 8,
    history: 'Último portaaviones japonés veterano de Pearl Harbor en ser hundido, durante la batalla del Cabo Engaño en 1944.'
  },
  {
    id: 'yorktown', name: 'USS Yorktown (CV-5)', role: 'carrier', nation: 'Estados Unidos', year: 1937, tier: 4,
    length: '251 m', displacement: '25.500 t', crew: '2.170', armament: '90 aviones embarcados',
    stats: { hp: 610, armor: 30, firepower: 82, torpedo: 44, aa: 60, speed: 34, evade: 26 },
    cost: 3800, unlockLevel: 8,
    history: 'Portaaviones de la clase Yorktown. Dañado en el Mar de Coral, se reparó en 72 horas para luchar en Midway, donde fue hundido.'
  },
  {
    id: 'illustrious', name: 'HMS Illustrious', role: 'carrier', nation: 'Reino Unido', year: 1940, tier: 3,
    length: '230 m', displacement: '23.000 t', crew: '1.200', armament: '36 aviones embarcados',
    stats: { hp: 580, armor: 35, firepower: 76, torpedo: 42, aa: 60, speed: 30, evade: 24 },
    cost: 3400, unlockLevel: 7,
    history: 'Portaaviones británico con cubierta blindada. Resistió graves impactos de bombas en el Mediterráneo y escoltó convoyes a Malta.'
  },
  {
    id: 'samuelRoberts', name: 'USS Samuel B. Roberts (DE-413)', role: 'destroyer', nation: 'Estados Unidos', year: 1944, tier: 3,
    length: '93 m', displacement: '1.837 t', crew: '224', armament: '2x127 mm y 3 tubos de torpedo',
    stats: { hp: 230, armor: 12, firepower: 32, torpedo: 80, aa: 30, speed: 28, evade: 56 },
    cost: 900, unlockLevel: 4,
    history: 'Destructor de escolta que se enfrentó a acorazados japoneses en Samar (1944). La "destructora que peleó como un acorazado".'
  },
  {
    id: 'haida', name: 'HMCS Haida', role: 'destroyer', nation: 'Canadá', year: 1943, tier: 3,
    length: '115 m', displacement: '2.500 t', crew: '261', armament: '6x120 mm y 8 tubos de torpedo',
    stats: { hp: 280, armor: 18, firepower: 42, torpedo: 80, aa: 35, speed: 36, evade: 54 },
    cost: 1500, unlockLevel: 4,
    history: 'Destructor tribal de la Marina Real Canadiense. Hundió más tonelaje enemigo que cualquier otro buque canadiense; hoy es museo.'
  },
  {
    id: 'blyskawica', name: 'ORP Błyskawica', role: 'destroyer', nation: 'Polonia', year: 1937, tier: 3,
    length: '114 m', displacement: '2.400 t', crew: '192', armament: '7x120 mm y 6 tubos de torpedo',
    stats: { hp: 270, armor: 16, firepower: 40, torpedo: 78, aa: 30, speed: 39, evade: 56 },
    cost: 1500, unlockLevel: 4,
    history: 'El "Relámpago" polaco escapó a Gran Bretaña en 1939 y combatió en Narvik. Es uno de los destructores mejor conservados del mundo.'
  },
  {
    id: 'campbeltown', name: 'HMS Campbeltown', role: 'destroyer', nation: 'Reino Unido', year: 1942, tier: 2,
    length: '95 m', displacement: '1.190 t', crew: '150', armament: '4x102 mm',
    stats: { hp: 210, armor: 10, firepower: 28, torpedo: 0, aa: 15, speed: 25, evade: 40 },
    cost: 700, unlockLevel: 3,
    history: 'Destructor cargado de explosivos que embistió la esclusa de Saint-Nazaire en 1942, inutilizando el dique seco alemán.'
  },
  {
    id: 'tang', name: 'USS Tang (SS-306)', role: 'submarine', nation: 'Estados Unidos', year: 1943, tier: 3,
    length: '95 m', displacement: '1.830 t', crew: '87', armament: '24 torpedos',
    stats: { hp: 240, armor: 12, firepower: 20, torpedo: 94, aa: 8, speed: 20, evade: 36 },
    cost: 1800, unlockLevel: 5,
    history: 'Submarino más exitoso de la Armada de EE. UU. en la Segunda Guerra Mundial: hundió 33 buques antes de perderse en 1944.'
  },
  {
    id: 'upholder', name: 'HMS Upholder', role: 'submarine', nation: 'Reino Unido', year: 1940, tier: 3,
    length: '77 m', displacement: '1.400 t', crew: '55', armament: '10 tubos de torpedo',
    stats: { hp: 230, armor: 12, firepower: 16, torpedo: 90, aa: 6, speed: 18, evade: 34 },
    cost: 1600, unlockLevel: 4,
    history: 'Submarino británico más exitoso del Mediterráneo. Al mando de David Wanklyn hundió numerosos transportes del Eje.'
  },
  {
    id: 'i19', name: 'I-19', role: 'submarine', nation: 'Japón', year: 1940, tier: 3,
    length: '108 m', displacement: '3.660 t', crew: '100', armament: '6 tubos de torpedo y 1 hidroavión',
    stats: { hp: 250, armor: 14, firepower: 18, torpedo: 92, aa: 8, speed: 24, evade: 32 },
    cost: 1700, unlockLevel: 5,
    history: 'Submarino japonés que lanzó la salva más devastadora de la guerra: un solo torpedo alcanzó al USS Wasp y otro al USS O\'Brien.'
  },
  {
    id: 'hermione', name: 'Hermione', role: 'frigate', nation: 'Francia', year: 1779, tier: 1,
    length: '44 m', displacement: '1.166 t', crew: '250', armament: '32 cañones',
    stats: { hp: 220, armor: 20, firepower: 44, torpedo: 0, aa: 0, speed: 12, evade: 12 },
    cost: 650, unlockLevel: 1,
    history: 'Fragata francesa que llevó al marqués de Lafayette a América en 1780. Una réplica navega hoy desde Rochefort.'
  },
  {
    id: 'alabama1862', name: 'CSS Alabama', role: 'cruiser', nation: 'Estados Confederados', year: 1862, tier: 1,
    length: '67 m', displacement: '1.100 t', crew: '145', armament: '8 cañones',
    stats: { hp: 230, armor: 12, firepower: 40, torpedo: 0, aa: 0, speed: 13, evade: 18 },
    cost: 700, unlockLevel: 2,
    history: 'Corsario confederado que capturó o hundió más de 60 mercantes de la Unión. Fue hundido por el USS Kearsarge en 1864.'
  },
  {
    id: 'olympia', name: 'USS Olympia', role: 'cruiser', nation: 'Estados Unidos', year: 1892, tier: 2,
    length: '104 m', displacement: '5.870 t', crew: '411', armament: '8x203 mm',
    stats: { hp: 400, armor: 40, firepower: 54, torpedo: 10, aa: 0, speed: 21, evade: 18 },
    cost: 1200, unlockLevel: 3,
    history: 'Crucero protegido y buque insignia del comodoro Dewey en la batalla de Manila Bay (1898).'
  },
  {
    id: 'aurora', name: 'Aurora', role: 'cruiser', nation: 'Rusia', year: 1900, tier: 2,
    length: '127 m', displacement: '6.731 t', crew: '570', armament: '8x152 mm',
    stats: { hp: 410, armor: 38, firepower: 52, torpedo: 10, aa: 0, speed: 19, evade: 16 },
    cost: 1200, unlockLevel: 3,
    history: 'Crucero protegido ruso. El disparo de su cañón de proa en 1917 anunció el asalto al Palacio de Invierno.'
  },
  {
    id: 'victoria1887', name: 'HMS Victoria', role: 'ironclad', nation: 'Reino Unido', year: 1887, tier: 2,
    length: '103 m', displacement: '10.470 t', crew: '583', armament: '2x413 mm',
    stats: { hp: 480, armor: 66, firepower: 60, torpedo: 0, aa: 0, speed: 16, evade: 8 },
    cost: 1500, unlockLevel: 3,
    history: 'Acorazado insignia del Mediterráneo. Se hundió en 1893 tras ser embestido accidentalmente por el HMS Camperdown.'
  },
  {
    id: 'missouri', name: 'USS Missouri', role: 'battleship', nation: 'Estados Unidos', year: 1944, tier: 4,
    length: '270 m', displacement: '57.000 t', crew: '2.700', armament: '9x406 mm',
    stats: { hp: 810, armor: 80, firepower: 97, torpedo: 0, aa: 75, speed: 33, evade: 20 },
    cost: 4500, unlockLevel: 9,
    history: 'Acorazado de la clase Iowa. En su cubierta se firmó la rendición de Japón en 1945 y volvió al servicio en la Guerra del Golfo.'
  },
  {
    id: 'newJersey', name: 'USS New Jersey', role: 'battleship', nation: 'Estados Unidos', year: 1943, tier: 4,
    length: '270 m', displacement: '57.000 t', crew: '2.700', armament: '9x406 mm',
    stats: { hp: 800, armor: 80, firepower: 96, torpedo: 0, aa: 72, speed: 33, evade: 20 },
    cost: 4400, unlockLevel: 9,
    history: 'El acorazado más condecorado de la Armada de EE. UU. Combatió en el Pacífico, Corea y Vietnam antes de convertirse en museo.'
  },
  {
    id: 'vanguard', name: 'HMS Vanguard', role: 'battleship', nation: 'Reino Unido', year: 1946, tier: 4,
    length: '248 m', displacement: '51.000 t', crew: '1.975', armament: '8x381 mm',
    stats: { hp: 780, armor: 79, firepower: 92, torpedo: 0, aa: 65, speed: 30, evade: 20 },
    cost: 4300, unlockLevel: 9,
    history: 'El último acorazado construido por el Reino Unido. Usó torres de 381 mm heredadas de los cruceros de batalla de la Gran Guerra.'
  },
  {
    id: 'jeanBart', name: 'Jean Bart', role: 'battleship', nation: 'Francia', year: 1940, tier: 4,
    length: '248 m', displacement: '48.500 t', crew: '1.550', armament: '8x380 mm',
    stats: { hp: 740, armor: 80, firepower: 92, torpedo: 0, aa: 55, speed: 32, evade: 20 },
    cost: 4000, unlockLevel: 9,
    history: 'Acorazado francés de la clase Richelieu. Combatió en Casablanca y fue modernizado tras la guerra con artillería antiaérea.'
  },
  {
    id: 'alaska', name: 'USS Alaska', role: 'battleship', nation: 'Estados Unidos', year: 1944, tier: 4,
    length: '246 m', displacement: '34.253 t', crew: '1.517', armament: '9x305 mm',
    stats: { hp: 650, armor: 60, firepower: 82, torpedo: 0, aa: 70, speed: 33, evade: 24 },
    cost: 3200, unlockLevel: 8,
    history: 'Considerado un "gran crucero", combinaba cañones de 305 mm con 33 nudos. Fue diseñado para cazar cruceros enemigos.'
  },
  {
    id: 'renown', name: 'HMS Renown', role: 'battleship', nation: 'Reino Unido', year: 1916, tier: 3,
    length: '242 m', displacement: '32.000 t', crew: '1.200', armament: '6x381 mm',
    stats: { hp: 620, armor: 56, firepower: 82, torpedo: 0, aa: 40, speed: 32, evade: 24 },
    cost: 2800, unlockLevel: 6,
    history: 'Crucero de batalla británico. Participó en la caza del Scharnhorst y del Gneisenau, y escoltó convoyes en el Atlántico.'
  },
  {
    id: 'repulse', name: 'HMS Repulse', role: 'battleship', nation: 'Reino Unido', year: 1916, tier: 3,
    length: '242 m', displacement: '32.000 t', crew: '1.200', armament: '6x381 mm',
    stats: { hp: 610, armor: 54, firepower: 80, torpedo: 0, aa: 40, speed: 32, evade: 24 },
    cost: 2700, unlockLevel: 6,
    history: 'Crucero de batalla británico. Fue hundido por aviones japoneses junto al Prince of Wales frente a Malasia en 1941.'
  },
  {
    id: 'kirishima', name: 'Kirishima', role: 'battleship', nation: 'Japón', year: 1915, tier: 3,
    length: '222 m', displacement: '36.600 t', crew: '1.360', armament: '8x356 mm',
    stats: { hp: 620, armor: 60, firepower: 82, torpedo: 0, aa: 30, speed: 30, evade: 20 },
    cost: 2600, unlockLevel: 6,
    history: 'Crucero de batalla japonés. Fue hundido por el USS Washington en la batalla nocturna de Guadalcanal en 1942.'
  },
  {
    id: 'haruna', name: 'Haruna', role: 'battleship', nation: 'Japón', year: 1915, tier: 3,
    length: '222 m', displacement: '36.600 t', crew: '1.360', armament: '8x356 mm',
    stats: { hp: 620, armor: 60, firepower: 82, torpedo: 0, aa: 30, speed: 30, evade: 20 },
    cost: 2500, unlockLevel: 6,
    history: 'Crucero de batalla japonés, el último de su clase en ser hundido. Fue atacado en su fondeadero de Kure en 1945.'
  },
  {
    id: 'wasp', name: 'USS Wasp (CV-7)', role: 'carrier', nation: 'Estados Unidos', year: 1940, tier: 3,
    length: '225 m', displacement: '19.900 t', crew: '2.167', armament: '76 aviones embarcados',
    stats: { hp: 520, armor: 20, firepower: 76, torpedo: 42, aa: 55, speed: 29, evade: 26 },
    cost: 3200, unlockLevel: 7,
    history: 'Portaaviones ligero de la Armada de EE. UU. Transportó cazas a Malta y fue hundido por el I-19 en 1942.'
  },
  {
    id: 'formidable', name: 'HMS Formidable', role: 'carrier', nation: 'Reino Unido', year: 1939, tier: 3,
    length: '240 m', displacement: '23.000 t', crew: '1.200', armament: '36 aviones embarcados',
    stats: { hp: 570, armor: 35, firepower: 74, torpedo: 40, aa: 60, speed: 30, evade: 24 },
    cost: 3200, unlockLevel: 7,
    history: 'Portaaviones blindado de la clase Illustrious. Combatió en el Mediterráneo y en el Pacífico, y sobrevivió a varios ataques kamikaze.'
  },
  {
    id: 'baltimore', name: 'USS Baltimore', role: 'cruiser', nation: 'Estados Unidos', year: 1943, tier: 3,
    length: '205 m', displacement: '17.000 t', crew: '1.142', armament: '9x203 mm',
    stats: { hp: 480, armor: 48, firepower: 70, torpedo: 30, aa: 50, speed: 33, evade: 26 },
    cost: 2400, unlockLevel: 6,
    history: 'Crucero pesado de la clase Baltimore. Sirvió en el Pacífico y en la Guerra de Corea; su diseño influyó en los cruceros de misiles.'
  },
  {
    id: 'tone', name: 'Tone', role: 'cruiser', nation: 'Japón', year: 1938, tier: 3,
    length: '201 m', displacement: '15.200 t', crew: '874', armament: '8x203 mm',
    stats: { hp: 470, armor: 46, firepower: 68, torpedo: 60, aa: 40, speed: 35, evade: 28 },
    cost: 2300, unlockLevel: 6,
    history: 'Crucero pesado japonés especializado en reconocimiento con hidroaviones. Participó en Midway y en la campaña de Guadalcanal.'
  },
  {
    id: 'atlanta', name: 'USS Atlanta', role: 'cruiser', nation: 'Estados Unidos', year: 1941, tier: 3,
    length: '165 m', displacement: '7.400 t', crew: '623', armament: '16x127 mm',
    stats: { hp: 380, armor: 30, firepower: 62, torpedo: 30, aa: 65, speed: 32, evade: 32 },
    cost: 1900, unlockLevel: 5,
    history: 'Crucero antiaéreo de la clase Atlanta. Su batería de 127 mm era devastadora contra aviones; fue hundido en Guadalcanal.'
  },
  {
    id: 'jervis', name: 'HMS Jervis', role: 'destroyer', nation: 'Reino Unido', year: 1939, tier: 3,
    length: '108 m', displacement: '1.700 t', crew: '183', armament: '6x120 mm y 10 tubos de torpedo',
    stats: { hp: 250, armor: 16, firepower: 38, torpedo: 74, aa: 28, speed: 36, evade: 55 },
    cost: 1300, unlockLevel: 4,
    history: 'Destructor líder de la clase J. Combatió en Narvik, el Mediterráneo y Normandía. Fue el destructor británico más condecorado de la guerra.'
  },
  {
    id: 'johnston', name: 'USS Johnston (DD-557)', role: 'destroyer', nation: 'Estados Unidos', year: 1943, tier: 3,
    length: '115 m', displacement: '2.100 t', crew: '273', armament: '5x127 mm y 10 tubos de torpedo',
    stats: { hp: 260, armor: 18, firepower: 42, torpedo: 82, aa: 45, speed: 36, evade: 54 },
    cost: 1400, unlockLevel: 4,
    history: 'Destructor que cargó contra la flota japonesa en Samar (1944). Su capitán recibió la Medalla de Honor por su resistencia.'
  },
  {
    id: 'shimakaze', name: 'Shimakaze', role: 'destroyer', nation: 'Japón', year: 1943, tier: 4,
    length: '129 m', displacement: '2.570 t', crew: '267', armament: '6x127 mm y 15 tubos de torpedo',
    stats: { hp: 300, armor: 18, firepower: 46, torpedo: 92, aa: 30, speed: 39, evade: 58 },
    cost: 2000, unlockLevel: 6,
    history: 'El destructor más rápido de la Segunda Guerra Mundial. Sus 15 tubos de torpedo lo convertían en una amenaza letal.'
  },
  {
    id: 'turbulent', name: 'HMS Turbulent', role: 'submarine', nation: 'Reino Unido', year: 1941, tier: 3,
    length: '84 m', displacement: '1.090 t', crew: '59', armament: '10 tubos de torpedo',
    stats: { hp: 230, armor: 10, firepower: 16, torpedo: 90, aa: 6, speed: 15, evade: 34 },
    cost: 1600, unlockLevel: 5,
    history: 'Submarino británico de la clase T. Hundió más de 90.000 toneladas en el Mediterráneo antes de desaparecer en 1943.'
  },
  {
    id: 'silversides', name: 'USS Silversides (SS-236)', role: 'submarine', nation: 'Estados Unidos', year: 1941, tier: 3,
    length: '95 m', displacement: '2.410 t', crew: '80', armament: '24 torpedos',
    stats: { hp: 250, armor: 14, firepower: 20, torpedo: 90, aa: 8, speed: 20, evade: 34 },
    cost: 1800, unlockLevel: 5,
    history: 'Submarino de la clase Gato. Fue uno de los más exitosos del Pacífico y hoy es museo en Michigan.'
  },
  {
    id: 'bogue', name: 'USS Bogue (CVE-9)', role: 'carrier', nation: 'Estados Unidos', year: 1942, tier: 2,
    length: '151 m', displacement: '16.200 t', crew: '890', armament: '24 aviones embarcados',
    stats: { hp: 450, armor: 18, firepower: 64, torpedo: 36, aa: 40, speed: 18, evade: 18 },
    cost: 2200, unlockLevel: 5,
    history: 'Portaaviones de escolta. Su grupo aéreo hundió más submarinos alemanes que cualquier otra unidad aliada en el Atlántico.'
  },
  {
    id: 'achilles', name: 'HMS Achilles', role: 'cruiser', nation: 'Reino Unido', year: 1933, tier: 3,
    length: '169 m', displacement: '7.000 t', crew: '550', armament: '8x152 mm',
    stats: { hp: 380, armor: 34, firepower: 56, torpedo: 30, aa: 30, speed: 32, evade: 30 },
    cost: 1800, unlockLevel: 4,
    history: 'Crucero ligero neozelandés. Combatió al Admiral Graf Spee en la batalla del Río de la Plata en 1939.'
  },
  {
    id: 'portland', name: 'USS Portland (CA-33)', role: 'cruiser', nation: 'Estados Unidos', year: 1933, tier: 3,
    length: '186 m', displacement: '10.000 t', crew: '807', armament: '9x203 mm',
    stats: { hp: 430, armor: 40, firepower: 62, torpedo: 25, aa: 40, speed: 32, evade: 28 },
    cost: 2200, unlockLevel: 5,
    history: 'Crucero pesado presente en el Mar de Coral y Midway. En Guadalcanal escoltó al USS Enterprise y sobrevivió a la campaña.'
  },
  {
    id: 'fubuki', name: 'Fubuki', role: 'destroyer', nation: 'Japón', year: 1928, tier: 2,
    length: '118 m', displacement: '2.000 t', crew: '219', armament: '6x127 mm y 9 tubos de torpedo',
    stats: { hp: 250, armor: 16, firepower: 38, torpedo: 76, aa: 20, speed: 38, evade: 54 },
    cost: 1200, unlockLevel: 4,
    history: 'Primer destructor japonés de la clase especial. Su diseño revolucionó los destructores y marcó el estándar de la época.'
  },
  {
    id: 'hipper', name: 'Admiral Hipper', role: 'cruiser', nation: 'Alemania', year: 1939, tier: 3,
    length: '206 m', displacement: '18.600 t', crew: '1.600', armament: '8x203 mm y 12 tubos de torpedo',
    stats: { hp: 490, armor: 50, firepower: 68, torpedo: 50, aa: 40, speed: 32, evade: 26 },
    cost: 2300, unlockLevel: 6,
    history: 'Crucero pesado alemán. Hundió al destructor HMS Glowworm y combatió en la batalla del Mar de Barents en 1942.'
  },
  {
    id: 'furious', name: 'HMS Furious', role: 'carrier', nation: 'Reino Unido', year: 1917, tier: 2,
    length: '239 m', displacement: '22.000 t', crew: '1.200', armament: '36 aviones embarcados',
    stats: { hp: 540, armor: 26, firepower: 70, torpedo: 38, aa: 50, speed: 30, evade: 22 },
    cost: 3000, unlockLevel: 6,
    history: 'Uno de los primeros portaaviones de la Royal Navy. Sus aviones atacaron al Tirpitz en 1944 y participaron en la campaña de Noruega.'
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
    id: 'spruance', name: 'Raymond Spruance', title: 'Táctico de Midway',
    bonus: 'evade', value: 0.08, cost: 1900, unlockLevel: 4,
    desc: 'Evasión +8%. Anticipa la maniobra enemiga y coloca la flota en ventaja.'
  },
  {
    id: 'jellicoe', name: 'John Jellicoe', title: 'Comandante de la Grand Fleet',
    bonus: 'armor', value: 0.10, cost: 2000, unlockLevel: 5,
    desc: 'Blindaje efectivo +10%. Mantiene la línea de batalla firme bajo fuego.'
  },
  {
    id: 'scheer', name: 'Reinhard Scheer', title: 'Almirante de la Flota de Alta Mar',
    bonus: 'evade', value: 0.10, cost: 2100, unlockLevel: 5,
    desc: 'Evasión +10%. Rompe el cerco enemigo con maniobras audaces.'
  },
  {
    id: 'halsey', name: 'William Halsey', title: 'Comandante del Tercer Grupo de Trabajo',
    bonus: 'damage', value: 0.10, cost: 2500, unlockLevel: 6,
    desc: 'Daño +10%. Agresividad y velocidad en cada ataque.'
  },
  {
    id: 'mitscher', name: 'Marc Mitscher', title: 'Táctico de portaaviones',
    bonus: 'accuracy', value: 0.07, cost: 2300, unlockLevel: 6,
    desc: 'Puntería +7%. Coordina ataques aéreos y navales con precisión.'
  },
  {
    id: 'vian', name: 'Philip Vian', title: 'Comandante de destructores',
    bonus: 'torpedo', value: 0.18, cost: 2000, unlockLevel: 5,
    desc: 'Daño de torpedo +18%. Especialista en ataques nocturnos.'
  },
  {
    id: 'horton', name: 'Max Horton', title: 'Comandante de submarinos',
    bonus: 'repair', value: 0.40, cost: 1800, unlockLevel: 4,
    desc: 'Reparaciones +40%. Sus tripulaciones sobreviven a lo imposible.'
  },
  {
    id: 'somerville', name: 'James Somerville', title: 'Comandante de la Fuerza H',
    bonus: 'accuracy', value: 0.07, cost: 2200, unlockLevel: 6,
    desc: 'Puntería +7%. Coordina ataques rápidos con precisión desde el Mediterráneo.'
  },
  {
    id: 'fraser', name: 'Bruce Fraser', title: 'Comandante de la Home Fleet',
    bonus: 'damage', value: 0.12, cost: 2600, unlockLevel: 7,
    desc: 'Daño +12%. Su mando firme convierte cada salva en un golpe decisivo.'
  },
  {
    id: 'nagumo', name: 'Chūichi Nagumo', title: 'Almirante de portaaviones',
    bonus: 'accuracy', value: 0.06, cost: 2400, unlockLevel: 6,
    desc: 'Puntería +6%. Sincroniza oleadas aéreas con la artillería naval.'
  },
  {
    id: 'admFletcher', name: 'Frank Jack Fletcher', title: 'Comandante de la Fuerza 17',
    bonus: 'evade', value: 0.12, cost: 2100, unlockLevel: 5,
    desc: 'Evasión +12%. Mantiene la flota fuera del alcance enemigo.'
  },
  {
    id: 'kinkaid', name: 'Thomas Kinkaid', title: 'Comandante del Séptimo Ejército',
    bonus: 'armor', value: 0.12, cost: 2300, unlockLevel: 6,
    desc: 'Blindaje efectivo +12%. Prepara la flota para resistir el combate cercano.'
  },
  {
    id: 'wanklyn', name: 'David Wanklyn', title: 'Comandante del HMS Upholder',
    bonus: 'torpedo', value: 0.20, cost: 2200, unlockLevel: 5,
    desc: 'Daño de torpedo +20%. El as de los submarinos británicos en el Mediterráneo.'
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

/* ---------- campaña narrativa ---------- */

const CAMPAIGN = [
  {
    id: 'c01', chapter: 'I', name: 'Primera patrulla', level: 1,
    desc: 'Una lancha enemiga hostiga a los pesqueros de la costa. Es tu primera misión de guerra.',
    narrative: 'El almirante te entrega el mando con una sola orden: "Mantén la ruta abierta". El mar está en calma, pero la guerra ya ha comenzado.',
    enemyIds: ['pt109'], boss: false,
    rewards: { credits: 260, xp: 80 }
  },
  {
    id: 'c02', chapter: 'II', name: 'El duelo de los ironclads', level: 2,
    desc: 'Dos viejos blindados bloquean el estuario y amenazan el puerto aliado.',
    narrative: 'El humo de los ironclads se alza sobre la niebla. Sus cascos de hierro parecen invulnerables, pero todo buque tiene un punto débil.',
    enemyIds: ['monitor', 'virginia'], boss: false,
    rewards: { credits: 400, xp: 120, officer: 'cunningham' }
  },
  {
    id: 'c03', chapter: 'III', name: 'Cazadores del Pacífico', level: 3,
    desc: 'Dos cruceros enemigos atacan el tráfico mercante en aguas abiertas.',
    narrative: 'La inteligencia ha detectado dos cruceros hostiles. Debes alcanzarlos antes de que desaparezcan entre las islas.',
    enemyIds: ['olympia', 'aurora'], boss: false,
    rewards: { credits: 550, xp: 160, ship: 'aurora' }
  },
  {
    id: 'c04', chapter: 'IV', name: 'Aguas del Atlántico', level: 4,
    desc: 'La flota de alta mar envía dos cruceros de batalla para romper el bloqueo.',
    narrative: 'Los cruceros de batalla alemanes son rápidos y están bien protegidos. La línea de batalla aliada se prepara para el impacto.',
    enemyIds: ['seydlitz', 'derfflinger'], boss: false,
    rewards: { credits: 700, xp: 200, officer: 'scheer' }
  },
  {
    id: 'c05', chapter: 'V', name: 'El Mediterráneo en llamas', level: 5,
    desc: 'Dos acorazados enemigos escoltan un convoy de suministros vital.',
    narrative: 'El calor del Mediterráneo y el humo de los cañones se mezclan. Si el convoy llega a puerto, la campaña se prolongará meses.',
    enemyIds: ['queenElizabeth', 'arizona'], boss: false,
    rewards: { credits: 900, xp: 250, officer: 'jellicoe' }
  },
  {
    id: 'c06', chapter: 'VI', name: 'Los gemelos de acero', level: 6,
    desc: 'El Scharnhorst y el Gneisenau han roto el bloqueo. Debes detenerlos.',
    narrative: 'Los dos cruceros de batalla alemanes avanzan en línea. Su artillería es rápida y su velocidad, endiablada. No habrá segunda oportunidad.',
    enemyIds: ['scharnhorst', 'gneisenau'], boss: true,
    rewards: { credits: 1200, xp: 320, ship: 'scharnhorst' }
  },
  {
    id: 'c07', chapter: 'VII', name: 'Tormenta sobre el Pacífico', level: 7,
    desc: 'Dos portaaviones japoneses lanzan una ofensiva sobre la flota aliada.',
    narrative: 'Las cubiertas de vuelo enemigas lanzan oleadas tras oleadas. La defensa antiaérea y la elección del momento lo decidirán todo.',
    enemyIds: ['akagi', 'shokaku'], boss: false,
    rewards: { credits: 1500, xp: 380, officer: 'mitscher' }
  },
  {
    id: 'c08', chapter: 'VIII', name: 'La flota del Duce', level: 8,
    desc: 'La Regia Marina concentra dos acorazados modernos para cortar el Mediterráneo.',
    narrative: 'Los acorazados italianos son rápidos y están armados con cañones de 381 mm. El control del Mediterráneo está en juego.',
    enemyIds: ['vittorioVeneto', 'roma'], boss: true,
    rewards: { credits: 1800, xp: 450, officer: 'halsey' }
  },
  {
    id: 'c09', chapter: 'IX', name: 'El mayor acorazado', level: 9,
    desc: 'El Yamato y el Nagato bloquean el avance final. Es el duelo de titanes.',
    narrative: 'Nunca has visto un buque tan grande. Sus cañones de 460 mm pueden hundirte de un solo impacto. La historia se escribirá hoy.',
    enemyIds: ['yamato', 'nagato'], boss: true,
    rewards: { credits: 2200, xp: 520, ship: 'yamato' }
  },
  {
    id: 'c10', chapter: 'X', name: 'ACERO FINAL', level: 10,
    desc: 'La flota enemiga reúne al Yamato, al Bismarck y al Enterprise para su última ofensiva.',
    narrative: 'Todo el teatro de operaciones converge en una sola batalla. Tu flota, tus oficiales y tu experiencia son la última línea de defensa.',
    enemyIds: ['yamato', 'bismarck', 'enterprise'], boss: true,
    rewards: { credits: 3000, xp: 800, ship: 'iowa', officer: 'nimitz' }
  }
];

/* ---------- logros ---------- */

function campaignCount(s) {
  return (s.campaign && s.campaign.cleared) ? Object.keys(s.campaign.cleared).length : 0;
}

function killed(s, role) {
  return (s.stats && s.stats.kills && s.stats.kills[role]) || 0;
}

const ACHIEVEMENTS = [
  { id: 'first_win', name: 'Primera victoria', desc: 'Gana tu primera operación.', reward: { credits: 150, xp: 50 }, check: function (s) { return (s.missionsWon || 0) >= 1; } },
  { id: 'wins_5', name: 'Veterano', desc: 'Gana 5 operaciones.', reward: { credits: 250, xp: 80 }, check: function (s) { return (s.missionsWon || 0) >= 5; } },
  { id: 'wins_10', name: 'Comandante de guerra', desc: 'Gana 10 operaciones.', reward: { credits: 400, xp: 140 }, check: function (s) { return (s.missionsWon || 0) >= 10; } },
  { id: 'wins_25', name: 'Leyenda naval', desc: 'Gana 25 operaciones.', reward: { credits: 900, xp: 300 }, check: function (s) { return (s.missionsWon || 0) >= 25; } },
  { id: 'fleet_5', name: 'Escuadrón', desc: 'Reúne 5 buques en tu flota.', reward: { credits: 250, xp: 60 }, check: function (s) { return (s.fleet || []).length >= 5; } },
  { id: 'fleet_10', name: 'Flota de batalla', desc: 'Reúne 10 buques en tu flota.', reward: { credits: 600, xp: 160 }, check: function (s) { return (s.fleet || []).length >= 10; } },
  { id: 'level_5', name: 'Capitán de corbeta', desc: 'Alcanza el nivel 5 de comandante.', reward: { credits: 300, xp: 60 }, check: function (s) { return (s.commander && s.commander.level) >= 5; } },
  { id: 'level_10', name: 'Almirante', desc: 'Alcanza el nivel 10 de comandante.', reward: { credits: 800, xp: 200 }, check: function (s) { return (s.commander && s.commander.level) >= 10; } },
  { id: 'officers_3', name: 'Estado mayor', desc: 'Contrata 3 oficiales.', reward: { credits: 300, xp: 70 }, check: function (s) { return (s.officers || []).length >= 3; } },
  { id: 'officers_7', name: 'Círculo de almirantes', desc: 'Contrata 7 oficiales.', reward: { credits: 700, xp: 180 }, check: function (s) { return (s.officers || []).length >= 7; } },
  { id: 'sink_10', name: 'Cazador', desc: 'Hunde 10 buques enemigos.', reward: { credits: 300, xp: 90 }, check: function (s) { return (s.stats && s.stats.sunk || 0) >= 10; } },
  { id: 'sink_50', name: 'Azote de los mares', desc: 'Hunde 50 buques enemigos.', reward: { credits: 900, xp: 300 }, check: function (s) { return (s.stats && s.stats.sunk || 0) >= 50; } },
  { id: 'specials_20', name: 'Maestro de maniobras', desc: 'Usa 20 habilidades especiales.', reward: { credits: 400, xp: 120 }, check: function (s) { return (s.stats && s.stats.specials || 0) >= 20; } },
  { id: 'campaign_5', name: 'Media campaña', desc: 'Completa 5 capítulos de la campaña.', reward: { credits: 700, xp: 200 }, check: function (s) { return campaignCount(s) >= 5; } },
  { id: 'campaign_10', name: 'Acero final', desc: 'Completa toda la campaña.', reward: { credits: 2000, xp: 600 }, check: function (s) { return campaignCount(s) >= 10; } },
  { id: 'boss_win', name: 'Matagigantes', desc: 'Gana una operación especial.', reward: { credits: 500, xp: 150 }, check: function (s) { return (s.stats && s.stats.bossWins || 0) >= 1; } },
  { id: 'rich_15000', name: 'Magnate naval', desc: 'Acumula 15.000 créditos.', reward: { credits: 300, xp: 100 }, check: function (s) { return (s.commander && s.commander.credits) >= 15000; } },
  { id: 'carrier_3', name: 'Cazaportaviones', desc: 'Hunde 3 portaaviones enemigos.', reward: { credits: 600, xp: 180 }, check: function (s) { return killed(s, 'carrier') >= 3; } },
  { id: 'battleship_5', name: 'Rompeblindajes', desc: 'Hunde 5 acorazados enemigos.', reward: { credits: 700, xp: 220 }, check: function (s) { return killed(s, 'battleship') >= 5; } }
];
