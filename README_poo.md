# Práctica 3 — Analizador Sintáctico LR(1) con Pila de Objetos

Implementación en Python del analizador sintáctico shift-reduce
("desplazar-reducir"), donde la pila ya no guarda tuplas ni enteros,
sino **objetos**, siguiendo el mismo patrón del ejemplo `Alumno` /
`Bachillerato` / `Licenciatura` del PDF de la práctica (Prof. Ing.
Michel Emanuel López Franco).

Archivo principal: `analizador_sintactico_poo.py`

Resuelve los mismos **Ejercicios 1 y 2** de la práctica anterior,
pero con la pila reestructurada en una jerarquía de clases:

```
ElementoPila            (clase base abstracta, equivale a "Alumno")
    ├── Terminal        símbolo terminal: id, +, $
    ├── NoTerminal        símbolo no terminal: E
    └── Estado            número de estado del autómata (0,1,2,3,4)
```

---

## 1. ¿Qué cambia respecto a la práctica anterior?

En la práctica anterior (`analizador_sintactico.py`), la pila era una
lista de Python con tuplas `(símbolo, estado)`:

```python
pila = [("$", 0)]
pila.append((lexema_token, accion.valor))
```

Aquí, la pila es una clase propia (`Pila`) cuyos `push()`/`pop()`
reciben y regresan **objetos** `ElementoPila`, no tuplas ni enteros:

```python
pila = Pila()
pila.push(Estado(0))
pila.push(Terminal(lexema_token, tipo_token))
pila.push(Estado(accion.valor))
```

Cada tipo de objeto sabe representarse a sí mismo con su propio
método `muestra()` (polimorfismo) — igual que en el ejemplo del PDF,
donde `Bachillerato` y `Licenciatura` heredan de `Alumno` y cada uno
implementa su propio `muestra()`.

El comportamiento del análisis (qué acciones se toman, qué cadenas se
aceptan o rechazan) es exactamente el mismo; lo único que cambió es
la **estructura de datos interna** de la pila.

---

## 2. Las clases

### `ElementoPila` (clase base abstracta)

No se puede instanciar directamente (usa el módulo `abc` de Python,
con `@abstractmethod` en `muestra()`), igual que la clase `Alumno` del
PDF no está pensada para crear objetos `Alumno` sueltos. Define:

- `muestra()` — método virtual, cada subclase decide cómo imprimirse.
- `es_terminal()`, `es_no_terminal()`, `es_estado()` — métodos de
  ayuda para preguntar de qué tipo es un elemento sin tener que hacer
  `isinstance` a mano en el resto del código.

### `Terminal(ElementoPila)`

Representa un símbolo terminal (un token): guarda su `lexema` (el
texto exacto, p. ej. `"hola"`) y su `tipo` (p. ej. `"id"`).
`muestra()` regresa el lexema.

### `NoTerminal(ElementoPila)`

Representa un símbolo no terminal, por ahora solo `E`. `muestra()`
regresa su nombre.

### `Estado(ElementoPila)`

Representa un número de estado del autómata LR (los números que ves
en la traza: `d2`, `d3`, `d4`...). `muestra()` regresa el número como
texto.

### `Pila`

Reemplaza a la lista de Python. `push()` **valida el tipo**: si le
pasas algo que no es `ElementoPila`, lanza un error claro en vez de
fallar después en un lugar confuso. Tiene dos formas de imprimirse:

- `muestra()` — la representación compacta de siempre: `$0hola2+3mundo4`.
- `muestra_detallada()` — línea por línea, con el tipo de cada objeto,
  de arriba hacia abajo (como el `pila.muestra()` del ejemplo C++ del
  PDF, que imprime cada `Alumno` con su propia información).

---

## 3. Cómo ejecutar el programa

### Modo demo (reproduce los casos del PDF de la práctica anterior)

```bash
python3 analizador_sintactico_poo.py
```

### Modo cadena propia

```bash
python3 analizador_sintactico_poo.py 1 "hola+mundo"
python3 analizador_sintactico_poo.py 2 "a+b+c+d"
```

El primer argumento (`1` o `2`) elige la gramática; el segundo es la
cadena a analizar. Se imprime la traza compacta de siempre
(`pila | entrada | salida`).

### Modo detallado (`--detallado`)

```bash
python3 analizador_sintactico_poo.py 2 "a+b+c" --detallado
```

Además de la traza compacta, imprime **antes de cada acción** la
pila completa, objeto por objeto, mostrando el tipo real de cada uno
(`Terminal`, `NoTerminal` o `Estado`). Es la forma más clara de ver
en qué momento exacto aparece cada tipo de `ElementoPila`: al
principio solo hay `Terminal`/`Estado` (mientras se desplaza), y en
cuanto ocurre la primera reducción aparece el primer `NoTerminal`.

Ejemplo de un paso de la salida (analizando `"a+b+c"` con el
Ejercicio 2, justo cuando reduce por primera vez):

```
=== Paso 6 (estado 2, siguiente token: '$') ===
Pila (de arriba hacia abajo):
  [Estado] 2
  [Terminal] c
  [Estado] 3
  [Terminal] +
  [Estado] 2
  [Terminal] b
  [Estado] 3
  [Terminal] +
  [Estado] 2
  [Terminal] a
  [Estado] 0
Entrada restante: $
-> Acción: reducir con regla 2 (E -> id)

=== Paso 7 (estado 4, siguiente token: '$') ===
Pila (de arriba hacia abajo):
  [Estado] 4
  [NoTerminal] E
  [Estado] 3
  ...
```

Antes del paso 7 la pila solo tenía `Terminal` y `Estado`; en cuanto
se reduce `id -> E`, aparece el primer `[NoTerminal] E`.

### Modo `--ejemplo-pila` (equivalente al `ejemplo()` del PDF)

```bash
python3 analizador_sintactico_poo.py --ejemplo-pila
```

Reproduce, de forma aislada (sin correr ningún análisis sintáctico
completo), el mismo tipo de prueba que el `ejemplo()` del PDF con
`Alumno`/`Bachillerato`/`Licenciatura`: mete varios objetos a la
pila, la imprime, saca uno con `pop()`, y la vuelve a imprimir — para
comprobar que el polimorfismo y el `push`/`pop` funcionan igual que
en el ejemplo original, sin mezclarlo con la lógica del parser.

---

## 4. Validaciones que agrega esta versión

- **`ElementoPila` no se puede instanciar directamente** (es una
  clase abstracta real, con `abc.ABC`): solo existen objetos
  `Terminal`, `NoTerminal` o `Estado`.
- **`Pila.push()` valida el tipo**: si se intenta meter algo que no
  sea `ElementoPila`, lanza `TypeError` con un mensaje claro.
- **`Pila.pop()` / `Pila.top()` de una pila vacía** lanzan
  `IndexError` con un mensaje explícito, en vez de fallar con un
  error confuso de Python.

Estas validaciones no cambian el comportamiento del análisis — solo
hacen que, si algo se usa mal (por error, al extender el código para
una práctica futura), el problema se detecte de inmediato y con un
mensaje entendible.

---

## 5. Cómo extenderlo

- **Agregar un nuevo tipo de símbolo no terminal**: no se necesita
  ninguna clase nueva — `NoTerminal("OtroSímbolo")` ya funciona,
  porque `NoTerminal` no está atada a un nombre fijo.
- **Agregar una gramática nueva**: igual que en la práctica anterior,
  se define con `Regla`, `Accion` y `TablaGramatica`, y se construye
  con una función `construir_...()` que arma las tablas ACTION/GOTO.
- **Ver el contenido exacto de la pila en cualquier punto**: usa
  `pila.muestra_detallada()` en vez de `pila.muestra()`.
