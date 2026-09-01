# Mini Analizador Sintáctico (Shift-Reduce / LR)

Implementación en Python de un analizador sintáctico ascendente tipo
**shift-reduce** ("desplazar-reducir"), impulsado por una tabla de
acciones y GOTO, para el Seminario de Solución de Problemas de
Traductores de Lenguaje II (Ing. Michel Emanuel López Franco).

Archivo principal: `analizador_sintactico.py`

Resuelve los **Ejercicios 1 y 2** cuyas trazas (columnas
`pila | entrada | salida`) aparecen en el PDF de referencia, y
reproduce esas trazas **paso a paso, exactamente igual**, hasta
llegar al `aceptar` o a un `error`.

---

## 1. ¿Qué hace este programa?

Recibe una cadena de entrada (por ejemplo `"hola+mundo"`) y simula el
proceso de un **analizador LR**: mantiene una pila de símbolos y
estados, y en cada paso decide, según el estado actual en la cima de
la pila y el siguiente token de la entrada, si debe:

- **Desplazar (`shift`)**: meter el siguiente token a la pila y
  avanzar en la entrada.
- **Reducir (`reduce`)**: reconocer que los símbolos en la cima de la
  pila forman el lado derecho de una regla gramatical, sacarlos de
  la pila y meter en su lugar el símbolo no terminal correspondiente
  (por ejemplo, cambiar `id + id` por `E`).
- **Aceptar**: si se llegó al final de la entrada (`$`) y en la pila
  solo queda el símbolo inicial, la cadena es válida.
- **Reportar error**: si ninguna acción aplica para el estado y
  token actuales, la cadena no pertenece al lenguaje.

El programa imprime **cada uno de estos pasos** en una tabla, igual
que en el PDF de referencia, hasta llegar al resultado final
(aceptar o error).

---

## 2. Las dos gramáticas

### Ejercicio 1 — sin recursión

```
E -> id
E -> id + id
```

Solo admite un identificador solo (`a`) o exactamente dos
identificadores separados por `+` (`hola+mundo`). Cualquier otra
combinación (tres o más `+`, o un carácter que no sea letra) genera
error.

### Ejercicio 2 — recursiva a la derecha

```
E -> id + E
E -> id
```

Admite una cadena de cualquier longitud de identificadores separados
por `+` (`a`, `a+b`, `a+b+c+d+e+f`, ...), porque `E` puede volver a
aparecer dentro de su propia definición.

> **Nota:** el PDF subido a la conversación se llama `LR.pdf`, y su
> contenido son las trazas que corresponden a estos dos ejercicios.
> Si el enunciado real de "PracticaAnalizadorSintactico.pdf" define
> otra gramática o pide otros casos de prueba, se ajustan fácilmente
> las tablas (ver sección 5).

---

## 3. Cómo está construido (arquitectura del código)

### 3.1 `tokenizar(entrada)`

Convierte el texto de entrada en una lista de tokens `(tipo, lexema)`:

- Cualquier letra seguida de más letras se agrupa como token `id`.
- El carácter `+` es su propio token.
- Cualquier otro carácter (dígitos, símbolos) se marca como `otro`,
  porque ninguna de las dos gramáticas lo acepta — así se reproduce,
  por ejemplo, el error inmediato al analizar `"5"`.
- Al final de la lista siempre se agrega el token `$` (fin de
  cadena).

### 3.2 `Regla`, `Accion`, `TablaGramatica`

Tres estructuras (`dataclass`) que representan, respectivamente: una
regla de la gramática (con su número, el no terminal que produce y
cuántos símbolos hay que sacar de la pila al reducir), una entrada de
la tabla ACTION (desplazar a un estado, reducir con una regla, o
aceptar), y el conjunto completo de tablas (ACTION + GOTO + reglas)
que define una gramática.

### 3.3 `AnalizadorSintactico.analizar(entrada)`

Es el motor genérico. No sabe nada de una gramática en particular:
todo su comportamiento depende de la `TablaGramatica` que recibe al
crearse. En cada iteración:

1. Mira el **estado actual** (la cima de la pila) y el **token
   siguiente** de la entrada.
2. Busca en `ACTION[(estado, token)]` qué hacer:
   - Si es `shift`, mete el token en la pila con el nuevo estado y
     avanza la posición de lectura.
   - Si es `reduce`, saca de la pila tantos símbolos como indique la
     longitud de la regla, revisa qué estado quedó expuesto debajo,
     busca en `GOTO[(ese estado, no terminal de la regla)]` el nuevo
     estado, y mete el no terminal con ese estado.
   - Si es `aceptar`, termina y reporta éxito.
   - Si no hay ninguna acción definida para esa combinación, reporta
     **error sintáctico** de inmediato (sin importar en qué punto de
     la cadena esté).
3. Imprime la fila de la traza (`pila | entrada | salida`) en cada
   paso, para poder ver el proceso completo.

### 3.4 `construir_ejercicio1()` / `construir_ejercicio2()`

Cada función arma la `TablaGramatica` correspondiente (reglas,
ACTION y GOTO) siguiendo exactamente los estados que se ven en las
trazas del PDF (`d2`, `d3`, `d4`, reducciones `r1`/`r2`, aceptación
`r0`).

---

## 4. Cómo ejecutar el programa

### Modo demo (reproduce los casos del PDF)

```bash
python3 analizador_sintactico.py
```

Corre, en orden, los cuatro casos de referencia:

- Ejercicio 1 con `"a"` → aceptada.
- Ejercicio 1 con `"hola+mundo"` → aceptada.
- Ejercicio 1 con `"5"` → error inmediato.
- Ejercicio 2 con `"a+b+c+d+e+f"` → aceptada, con toda la cadena de
  reducciones a la derecha.

### Modo cadena propia

```bash
python3 analizador_sintactico.py 1 "hola+mundo"
python3 analizador_sintactico.py 2 "a+b+c+d"
```

El primer argumento (`1` o `2`) elige la gramática del Ejercicio 1 o
2; el segundo es la cadena que quieres analizar. Se imprime el
proceso completo, paso a paso, hasta el resultado final.

### Ejemplo de salida paso a paso

```
$ python3 analizador_sintactico.py 2 "x+y+z"
Analizando 'x+y+z' con el Ejercicio 2

pila                        entrada             salida
$                           x+y+z$              d2
$x2                         +y+z$               d3
$x2+3                       y+z$                d2
$x2+3y2                     +z$                 d3
$x2+3y2+3                   z$                  d2
$x2+3y2+3z2                 $                   r2 E->id
$x2+3y2+3E4                 $                   r1 E->id + E
$x2+3E4                     $                   r1 E->id + E
$E1                         $                   r0 (aceptar)

>>> Cadena aceptada
```

Cada línea muestra el estado exacto de la pila y de la entrada
restante en ese momento, y qué acción se tomó (`d<N>` = desplazar al
estado N, `r<N> ...` = reducir con la regla N, `r0 (aceptar)` = fin
exitoso, `error` = la cadena no pertenece al lenguaje).

---

## 5. Cómo extenderlo / usar con otra gramática

El motor `AnalizadorSintactico` no depende de estas dos gramáticas en
particular. Para agregar una tercera, se sigue el mismo patrón que
`construir_ejercicio1()`:

1. Definir las **reglas** (`Regla(numero, no_terminal, texto_para_imprimir, longitud)`).
2. Definir la tabla **ACTION**: para cada combinación
   `(estado, token)` que deba desplazar, reducir o aceptar.
3. Definir la tabla **GOTO**: para cada combinación
   `(estado, no_terminal)` que resulte después de una reducción.
4. Crear un `AnalizadorSintactico(TablaGramatica(...))` y llamar a
   `.analizar("tu cadena")`.

Si algún token no tiene entrada en `ACTION` para el estado actual, el
motor reporta error automáticamente — no es necesario escribir casos
de error a mano.
