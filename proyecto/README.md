# Analizador Léxico — Proyecto Taller Compiladores

Implementación en Python del analizador léxico (*scanner*) para el
**Proyecto Taller Compiladores** (Ing. Michel Emanuel López Franco),
correspondiente al Seminario de Solución de Problemas de Traductores
de Lenguaje II.

Archivo principal: `analizador_lexico_final.py`

> Esta versión parte de un analizador basado en expresiones regulares
> (`re`) compartido por un compañero de clase, y se adaptó para
> cumplir exactamente lo que pide el profesor: códigos numéricos de
> token (0-23), el token de fin de cadena `$`, y que el análisis no
> se detenga ante un error léxico.

---

## 1. ¿Qué hace este programa?

Recibe una cadena de texto con código fuente y la recorre de
izquierda a derecha, comparando en cada posición varias
**expresiones regulares** (una por cada categoría de token:
identificador, entero, real, cadena, etc.) para decidir qué unidad
léxica sigue. Por cada token reconocido devuelve:

- el **lexema** (el texto exacto que se leyó, p. ej. `"contador"`),
- el **código numérico** del token (p. ej. `0` para identificador),
- la **línea** y **columna** donde comenzó.

Al final de la cadena de entrada agrega siempre el token especial
`$` (código `23`), que marca el fin de la entrada para la gramática
LR(1) del proyecto.

Si encuentra un carácter o una secuencia que no corresponde a ningún
patrón válido, no detiene el análisis: reporta un **error léxico** y
continúa, para poder mostrar todos los errores de una sola pasada.

---

## 2. Reglas léxicas reconocidas

| Categoría          | Regla / patrón                                   |
|---------------------|---------------------------------------------------|
| Identificador        | `letra (letra \| digito)*`                        |
| Entero                | `digito+`                                          |
| Real                   | `entero . entero`  (punto seguido de al menos 1 dígito) |
| Cadena                 | `" ... "` (texto entre comillas dobles)            |
| Palabras reservadas | `if, while, return, else, int, float, void`        |
| Operador de suma     | `+  -`                                             |
| Operador de mult.     | `*  /`                                             |
| Operador relacional  | `<  >  <=  >=`                                     |
| Operador de igualdad | `==  !=`                                           |
| Operador and           | `&&`                                               |
| Operador or             | `\|\|`                                             |
| Operador not            | `!`                                                |
| Asignación             | `=`                                                 |
| Delimitadores          | `;  ,  (  )  {  }`                                 |

> **Nota sobre supuestos:** el enunciado del proyecto no detalla el
> patrón exacto de `cadena`, así que se asumió la convención habitual
> de comillas dobles. También se agrupó `int`, `float` y `void` bajo
> el código `4` ("tipo"), aunque `void` no aparece explícitamente en
> la lista de palabras reservadas del PDF. Si el profesor definió
> otra regla, solo hay que ajustar el diccionario `PALABRAS_RESERVADAS`.

---

## 3. Tabla de códigos de token

Estos códigos deben coincidir con la columna correspondiente en la
tabla LR(1) del proyecto (`compilador09b.xlsx`):

| Código | Token           | Código | Token   |
|:---:|-----------------|:---:|---------|
| 0   | identificador   | 12  | `;`     |
| 1   | entero          | 13  | `,`     |
| 2   | real            | 14  | `(`     |
| 3   | cadena          | 15  | `)`     |
| 4   | tipo            | 16  | `{`     |
| 5   | opSuma          | 17  | `}`     |
| 6   | opMul           | 18  | `=`     |
| 7   | opRelac         | 19  | `if`    |
| 8   | opOr            | 20  | `while` |
| 9   | opAnd           | 21  | `return`|
| 10  | opNot           | 22  | `else`  |
| 11  | opIgualdad      | 23  | `$`     |

---

## 4. Cómo está construido (arquitectura del código)

El analizador reconoce los tokens con **expresiones regulares**
(módulo `re` de Python), no con un autómata escrito a mano: cada
categoría léxica tiene su propio patrón, y en cada posición del
texto se intenta hacer *match* con el patrón adecuado.

### 4.1 Clase `Tok`

Estructura simple (`dataclass`) que guarda el lexema (`valor`), el
**código numérico** del token, la línea y la columna donde empezó.
La propiedad `nombre` traduce el código a un nombre legible (usando
el diccionario `NOMBRE_CODIGO`), solo para depuración/impresión —
internamente lo que importa para la gramática LR(1) es `codigo`.

### 4.2 Expresiones regulares base

```python
_espacios = re.compile(r'[ \t\r]+')
_ident    = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
_entero   = re.compile(r'[0-9]+')
_real     = re.compile(r'[0-9]+\.[0-9]+')
_cadena   = re.compile(r'"(?:[^"\\]|\\.)*"')
```

Cada una implementa directamente una de las reglas léxicas del
proyecto: `_ident` es `letra (letra|digito)*`, `_real` es
`entero.entero`, etc.

### 4.3 Función `analizador_lexico(src)`

Recorre la cadena `src` con un índice `i` que avanza conforme se
reconocen tokens (usando `.match(src, i)`, que ancla la búsqueda
justo en la posición actual). En cada vuelta del ciclo principal:

1. **Ignora** espacios en blanco, comentarios de línea (`// ...`) y
   comentarios de bloque (`/* ... */`), llevando la cuenta de línea y
   columna incluso dentro de comentarios multilínea.
2. Intenta `_real` **antes** que `_entero`, porque si se probara
   `_entero` primero, `12.5` se reconocería como el entero `12`
   dejando el `.5` suelto. Si después de un entero sigue un `.` que
   **no** tiene dígitos detrás, se reporta como real mal formado
   (por ejemplo `3.`).
3. Intenta `_cadena` (texto entre comillas dobles).
4. Intenta `_ident`: si el lexema coincide con `RESERVADAS_TIPO`
   (`int`, `float`, `void`, `char`) o `RESERVADAS` (`if`, `while`,
   `return`, `else`), usa ese código; si no, es identificador
   (código `0`).
5. Revisa los **operadores de dos caracteres** (`==`, `!=`, `<=`,
   `>=`, `&&`, `||`) antes que los de uno solo, para no confundir
   `<=` con `<` seguido de `=`.
6. Revisa los operadores y delimitadores de un solo carácter (`+ - *
   / % < > ! = ; , ( ) { }`) mediante comparaciones directas y un
   diccionario `mapa_punc`.
7. Si nada de lo anterior aplica, el carácter se marca como **error
   léxico** y se avanza uno a la vez, sin detener el análisis.

Al terminar de recorrer toda la entrada se agrega el token `$`
(código `23`).

### 4.4 Manejo de errores

A diferencia de una implementación que se detiene en el primer error
(`raise ValueError`), esta versión **acumula** los errores en una
lista y sigue analizando el resto del código. Los errores quedan
disponibles de dos formas después de llamar a la función:

- Como tokens con `codigo == -1` dentro de la lista devuelta.
- En `analizador_lexico.errores`, una lista de mensajes descriptivos
  con línea y columna (se guarda como atributo de la función misma,
  así que se consulta *después* de la llamada).

---

## 5. Ejemplo de uso

```python
from analizador_lexico_final import analizador_lexico

codigo_fuente = """
int contador;
contador = 0;
while (contador < 5) {
    contador = contador + 1;
}
"""

tokens = analizador_lexico(codigo_fuente)

for t in tokens:
    print(t)
```

Salida esperada (resumida):

```
<'int', 4:TIPO>                (línea 2, col 5)
<'contador', 0:IDENTIFICADOR>  (línea 2, col 9)
<';', 12:PUNTO_Y_COMA>         (línea 2, col 17)
<'contador', 0:IDENTIFICADOR>  (línea 3, col 5)
<'=', 18:ASIGNACION>           (línea 3, col 14)
<'0', 1:ENTERO>                (línea 3, col 16)
<';', 12:PUNTO_Y_COMA>         (línea 3, col 17)
<'while', 20:WHILE>            (línea 4, col 5)
<'(', 14:PARENTESIS_IZQ>       (línea 4, col 11)
<'contador', 0:IDENTIFICADOR>  (línea 4, col 12)
<'<', 7:OP_RELAC>              (línea 4, col 21)
<'5', 1:ENTERO>                (línea 4, col 23)
<')', 15:PARENTESIS_DER>       (línea 4, col 24)
<'{', 16:LLAVE_IZQ>            (línea 4, col 26)
...
<'$', 23:$>                    (fin de la entrada)
```

### 5.1 Ejemplo con número real

```python
analizador_lexico("float promedio; promedio = 12.5;")
```

Reconoce `float` → TIPO (4), `promedio` → IDENTIFICADOR (0),
`12.5` → REAL (2), correctamente separado como una sola unidad
léxica (no como `12`, `.`, `5` por separado) gracias a que el patrón
`_real` se intenta antes que `_entero`.

### 5.2 Ejemplo con operadores compuestos

```python
analizador_lexico("if (a >= 10 && b != 0) { return a; }")
```

Reconoce `>=` como un solo token `OP_RELAC`, `&&` como `OP_AND` y
`!=` como `OP_IGUALDAD`, gracias al paso 5 del algoritmo (revisión de
dos caracteres antes que uno).

### 5.3 Ejemplo con comentarios

```python
analizador_lexico('int x = 5; // esto es un comentario\n/* y esto\n   también */ x = 6;')
```

Ambos tipos de comentario se descartan sin generar tokens, y las
líneas dentro del comentario de bloque sí se cuentan correctamente
para que la numeración de línea del resto del código sea correcta.

### 5.4 Ejemplo con error léxico

```python
tokens = analizador_lexico("x = 3.;  y @ 2")
print(analizador_lexico.errores)
```

- `3.` genera un error ("real mal formado"), porque después del
  punto no hay ningún dígito.
- `@` genera un error ("carácter inválido"), porque no pertenece a
  ningún patrón del lenguaje.
- El análisis continúa después de cada error y sigue reconociendo el
  resto de los tokens (`y`, `2`, `$`). Los mensajes de error quedan
  disponibles en `analizador_lexico.errores` después de la llamada.

---

## 6. Cómo ejecutar el programa

El archivo incluye un bloque `if __name__ == "__main__":` con un
ejemplo de programa completo (declaraciones, `while`, `if/else`,
operadores lógicos y relacionales). Para probarlo basta con ejecutar:

```bash
python3 analizador_lexico_final.py
```

Esto imprime una tabla con cada lexema, su código y su nombre de
token, además de un resumen de errores léxicos (si los hay).

---

## 7. Cómo se prueba (archivo de prueba + script de test)

Además del ejemplo interno del archivo principal, el proyecto incluye
dos archivos pensados específicamente para hacer pruebas sin tocar
`analizador_lexico_final.py`:

- **`prueba.txt`** — un archivo de código fuente de ejemplo que usa
  todos los tokens del lenguaje: declaraciones (`int`, `float`,
  `char`), asignaciones, una cadena, operadores aritméticos,
  relacionales, lógicos y de igualdad, `while`, `if/else`,
  comentarios de línea (`//`) y de bloque (`/* */`). Al final
  incluye, a propósito, dos líneas inválidas (`x = 3.;` y `y @ 2;`)
  para comprobar que el analizador reporta errores léxicos sin
  detener el análisis.

- **`test_analizador.py`** — script que abre un archivo de código
  fuente, le corre el analizador y muestra la tabla de tokens
  reconocidos junto con el resumen de errores. Por defecto usa
  `prueba.txt`, pero acepta cualquier otro archivo como argumento.

Los tres archivos (`analizador_lexico_final.py`, `prueba.txt` y
`test_analizador.py`) deben estar en la **misma carpeta**, porque el
script de prueba importa el analizador con:

```python
from analizador_lexico_final import analizador_lexico
```

### Cómo correr la prueba

```bash
python3 test_analizador.py
```

Para probar con tu propio código, en vez del archivo `prueba.txt` de
ejemplo:

```bash
python3 test_analizador.py mi_codigo.c
```

### Salida esperada

El script imprime, en este orden:

1. El nombre del archivo analizado y el total de tokens y errores
   encontrados.
2. Una tabla con cada lexema, su código numérico y su nombre de
   token (por ejemplo `int   4   TIPO`).
3. Una sección `=== Errores léxicos ===` con cada error y su
   ubicación (línea y columna), o `Ninguno` si el código no tiene
   errores.

Con el `prueba.txt` incluido, el resultado debe mostrar los 2 errores
esperados:

```
Línea 31, col 5: real mal formado '3.'
Línea 32, col 3: carácter inválido '@'
```

Si al correrlo con tu propio archivo aparecen errores que no
esperabas, revisa primero la línea y columna que indica el mensaje:
casi siempre es un carácter fuera de la gramática del proyecto (por
ejemplo `[`, `]`, `#`, `:`, etc., que no están contemplados) o un
número real mal escrito.

---

## 8. Cómo extenderlo

- **Nuevas palabras reservadas:** agregar la entrada en
  `RESERVADAS` o `RESERVADAS_TIPO`, según corresponda.
- **Nuevos operadores de un solo carácter:** agregar la comparación
  correspondiente (siguiendo el patrón de `if one in "+-": ...`)
  dentro de `analizador_lexico()`.
- **Nuevos operadores de dos caracteres:** agregar la entrada al
  conjunto `("==", "!=", "<=", ">=", "&&", "||")` y a su diccionario
  de códigos.
- **Cambiar el patrón de `cadena`, `real` o `tipo`:** basta con
  modificar la expresión regular correspondiente (`_cadena`,
  `_real`) o el diccionario `RESERVADAS_TIPO`.
