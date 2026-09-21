# Analizador Léxico y Sintáctico (versión unificada)

Implementación en Python de las dos primeras fases de un traductor
(compilador/intérprete) para un lenguaje de programación simplificado
tipo C: declaraciones de variables y funciones, tipos `int`/`float`,
control de flujo `if`/`else`/`while`, y expresiones aritméticas y
lógicas.

Todo el código vive en **un solo archivo**, `analizador.py`. Para
correrlo solo necesitas dos cosas en la misma carpeta:

```
analizador.py
datos/
  compilador.lr
```

(los archivos `.csv` e `.inf` de `datos/` son de referencia — para
verlos en Excel o consultar los códigos a mano — pero el programa no
los necesita para ejecutarse; solo lee `compilador.lr`).

---

## 1. Qué hace el proyecto

El archivo tiene dos fases conectadas, una detrás de otra en el mismo
módulo:

1. **Analizador léxico** (`analizador_lexico()`) — lee el código
   fuente carácter por carácter y lo convierte en una secuencia de
   **tokens** (identificadores, números, operadores, palabras
   reservadas, etc.), cada uno con su línea y columna.
2. **Analizador sintáctico** (`AnalizadorSintactico.analizar()`) —
   toma esa secuencia de tokens (no el texto original) y verifica que
   forme un programa gramaticalmente válido, usando un análisis
   ascendente LR (shift-reduce / desplazar-reducir).

Las dos fases están **conectadas de verdad**: el sintáctico nunca
vuelve a tokenizar nada por su cuenta, usa directamente la salida del
léxico.

```
código fuente (texto)
        │
        ▼
  analizador_lexico()   ──────►  tokens (con línea/columna)
        │                              │
        │ (errores léxicos             │
        │  se reportan aparte,         ▼
        │  no detienen el análisis)  AnalizadorSintactico.analizar()
        │                              │
        │                              ▼
        │                     aceptado (árbol) / error sintáctico
```

`analizar_programa()` es la función que amarra todo: corre el
léxico, filtra los tokens de error antes de pasarlos al sintáctico, y
arma el reporte final de texto (tokens + errores léxicos + resultado
sintáctico + árbol).

---

## 2. Los tokens del lenguaje

Cada token tiene un código numérico fijo (0-23), que es el mismo que
usa la tabla del analizador sintáctico para buscar sus acciones:

| Código | Token | Patrón / ejemplos |
|:---:|---|---|
| 0 | identificador | `letra (letra\|digito)*` |
| 1 | entero | `digito+` |
| 2 | real | `entero.entero` (un punto con al menos 1 dígito después) |
| 3 | cadena | `"texto entre comillas dobles"` |
| 4 | tipo | `int`, `float`, `void` |
| 5 | opSuma | `+`, `-` |
| 6 | opMul | `*`, `/`, `%` |
| 7 | opRelac | `<`, `>`, `<=`, `>=` |
| 8 | opOr | `\|\|` |
| 9 | opAnd | `&&` |
| 10 | opNot | `!` |
| 11 | opIgualdad | `==`, `!=` |
| 12 | `;` | punto y coma |
| 13 | `,` | coma |
| 14 / 15 | `(` `)` | paréntesis |
| 16 / 17 | `{` `}` | llaves |
| 18 | `=` | asignación |
| 19-22 | `if`, `while`, `return`, `else` | palabras reservadas |
| 23 | `$` | fin de la entrada (lo agrega el propio léxico) |

Las palabras reservadas se reconocen primero como identificador y
luego se reclasifican si el lexema coincide con la lista de
reservadas — así no hace falta un caso especial para cada palabra.

---

## 3. Cómo está construido el analizador léxico

`analizador_lexico(src)` reconoce cada categoría de token con una
**expresión regular** (identificador, entero, real, cadena), probadas
en orden en cada posición del texto, y regresa una tupla
`(tokens, errores)`:

- Mantiene un índice de lectura y contadores de línea/columna.
- El patrón de `real` se intenta **antes** que el de `entero`, para
  que `12.5` no se reconozca como el entero `12` dejando el `.5`
  suelto.
- Reconoce comentarios de línea (`//`) y de bloque (`/* */`), llevando
  la cuenta de saltos de línea incluso dentro de un comentario
  multilínea.
- Los operadores de dos caracteres (`==`, `!=`, `<=`, `>=`, `&&`,
  `||`) se revisan antes que los de un solo carácter, para no
  confundir `<=` con `<` seguido de `=`.
- Cada token reconocido se guarda como un objeto `Tok` (`codigo`,
  `valor`, `linea`, `columna`).

**Manejo de errores léxicos:** cuando aparece un carácter que no
encaja en ningún patrón (por ejemplo `@`, `#`), o un número real mal
formado (un punto sin dígitos después, como `5.`), el error **no
detiene el análisis** — se agrega a la lista `errores` que regresa la
función junto con su ubicación exacta, y el analizador sigue leyendo
el resto del archivo. Esto permite ver *todos* los errores léxicos de
un archivo en una sola corrida, en vez de tener que corregir uno y
volver a ejecutar para ver el siguiente.

---

## 4. Cómo está construido el analizador sintáctico

### Lee directamente el archivo `.lr` (formato oficial de la práctica)

Cada gramática tiene tres archivos asociados en `datos/`, pero
**solo uno lo debe leer el programa**:

| Archivo | Para qué sirve | ¿Lo lee el programa? |
|---|---|---|
| `datos/compilador.csv` | Ver la tabla LR desde Excel | No |
| `datos/compilador_inf.txt` | Referencia: códigos de token y reglas en texto | No |
| `datos/compilador.lr` | La tabla LR codificada como matriz de enteros | **Sí** |

`cargar_gramatica_lr()` carga toda la gramática (reglas + tabla de
estados × columnas) desde `datos/compilador.lr`. El formato es:

```
<numReglas>
<numReglas líneas>: idColumnaIzquierda   longitud   nombreIzquierda
<numFilas> <numColumnas>
<numFilas líneas de numColumnas enteros>: la tabla LR
```

En la tabla, cada `celda[estado][columna]` es un solo entero:
positivo = desplazar/ir a ese estado; negativo = reducir con la regla
`-celda - 1` (si esa regla da `0`, es aceptar); cero = error.

### Sin traducir nombres entre léxico y sintáctico

La columna que se usa para buscar la acción de un **token** es
directamente su código numérico (`t.codigo`, 0-23) — el mismo que ya
produce `analizador_lexico()`. La columna para un **GOTO** (tras una
reducción) es el `idColumnaIzquierda` que la propia regla trae en el
`.lr`. No hace falta ningún diccionario intermedio que traduzca
nombres de columna — el léxico y el sintáctico ya "hablan" en los
mismos números.

### Pila de objetos

La pila no es una lista de enteros ni de tuplas: es una jerarquía de
clases —

```
ElementoPila            (clase base abstracta)
    ├── Terminal        símbolo terminal (identificador, +, ;, ...)
    ├── NoTerminal        símbolo no terminal (Expresion, Sentencia, ...)
    └── Estado            número de estado del autómata LR
```

— cada una con su propio método `muestra()`, así que la pila se
puede imprimir de forma legible en cualquier punto del análisis
(usa esto internamente `--traza`, ver sección 6).

### El algoritmo, paso a paso

En cada paso, `AnalizadorSintactico.analizar()` mira el estado actual
(la cima de la pila) y consulta `tabla[estado][token.codigo]`:

1. **Celda > 0 → desplazar (shift)** — mete el token a la pila con su
   nuevo estado, y avanza a leer el siguiente token.
2. **Celda < 0 y regla ≠ 0 → reducir** — saca de la pila `longitud`
   símbolos (más su estado cada uno); mete el no terminal
   correspondiente, buscando el nuevo estado con
   `tabla[estado_previo][idColumnaIzquierda]`.
3. **Celda < 0 y regla = 0 → aceptar** — el programa es
   sintácticamente correcto.
4. **Celda = 0 → error sintáctico.**

**El árbol sintáctico:** cada vez que se reduce, los símbolos que se
sacan de la pila no se descartan — se guardan como `hijos` del nuevo
`NoTerminal` que se crea. Así, cuando el análisis termina en
"aceptar", `analizar()` regresa la raíz del árbol sintáctico completo
(el nodo `programa`, con toda su estructura debajo). El método
`NoTerminal.imprimir_arbol()` lo muestra como árbol de texto con
conectores (`├──`, `└──`), como en el ejemplo de la sección 8.

**Manejo de errores sintácticos:** a diferencia del léxico, un error
sintáctico **sí detiene el análisis** de inmediato (excepción
`ErrorSintactico`), reportando la línea y columna exactas del token
que no encajaba en ninguna regla. No se intenta "adivinar" cómo
seguir, porque hacerlo suele producir una cascada de errores falsos
que no reflejan el problema real.

### El puente entre léxico y sintáctico

`analizar_programa()` conecta ambas fases:

1. Corre `analizador_lexico(codigo_fuente)`.
2. Descarta del flujo hacia el sintáctico los tokens marcados como
   error léxico (código `-1`) — no tendría sentido darle significado
   gramatical a un carácter que ni siquiera es un token válido — pero
   conserva la lista de errores léxicos para reportarla aparte.
3. Entrega el resto de los tokens, tal cual, al analizador sintáctico
   (mismos objetos `Tok`, mismo código numérico).

---

## 5. Estructura de archivos

```
analizador.py                  Léxico + sintáctico, en un solo módulo
README.md                      Este archivo
documento_diseno.md            Documento de diseño (entregable académico)
datos/
  compilador.lr                 Tabla LR + reglas (esto SÍ lo lee el programa)
  compilador.csv                 La misma tabla, para verla en Excel
  compilador_inf.txt              Códigos de token y reglas, de referencia
ejemplos/
  ejemploN_*.txt                   Programas de entrada de muestra
  salidaN_*.txt                     Salida real que produce el analizador
```

Dentro de `analizador.py`, el código está dividido con separadores en
tres bloques, en este orden:

```
# FASE 1: ANALIZADOR LÉXICO        -> Tok, códigos de token, analizador_lexico()
# FASE 2: ANALIZADOR SINTÁCTICO    -> ElementoPila, GramaticaLR, AnalizadorSintactico, analizar_programa()
# INTERFAZ DE LÍNEA DE COMANDOS     -> main(), argparse
```

---

## 6. Cómo correrlo

Analizar cualquier archivo de código fuente (pipeline completo,
léxico + sintáctico):

```bash
python3 analizador.py ejemplos/ejemplo1_valido.txt
```

Esto imprime, en orden:

1. La lista de tokens reconocidos, con línea y columna.
2. Los errores léxicos encontrados (o "Ninguno").
3. El resultado del análisis sintáctico: aceptado (con el árbol
   sintáctico completo), o el error sintáctico con su ubicación
   exacta.

Sin argumentos, corre con un programa de ejemplo incluido en el
propio archivo:

```bash
python3 analizador.py
```

Para ver el análisis sintáctico **paso a paso** (pila / entrada /
acción shift-reduce, útil para depurar o para explicar el
funcionamiento del autómata LR):

```bash
python3 analizador.py ejemplos/ejemplo1_valido.txt --traza
```

Si la carpeta `datos/` no está junto al script (por ejemplo, la
moviste a otro lugar), indícalo con `--datos`:

```bash
python3 analizador.py mi_codigo.txt --datos /ruta/a/datos
```

Para analizar tu propio código y guardar la salida:

```bash
python3 analizador.py mi_codigo.txt > mi_salida.txt
```

Ver todas las opciones disponibles:

```bash
python3 analizador.py --help
```

---

## 7. Ejemplos incluidos

Diez programas de muestra (7 originales + 3 nuevos): 4 se aceptan sin
problema (`ejemplo1`, `4`, `5`, `8`) y 6 están diseñados a propósito
para fallar (`ejemplo2`, `3`, `6`, `7`, `9`, `10`), cada uno mostrando
un tipo de error distinto.

| Archivo | Qué prueba | Resultado esperado |
|---|---|---|
| `ejemplo1_valido.txt` | Programa completo: declaraciones, función con parámetros, `while`, `if/else`, llamada a función | ✅ Aceptado |
| `ejemplo2_error_lexico.txt` | Real mal formado (`3.`) y carácter inválido (`@`) | ❌ 2 errores léxicos; falla también en sintáctico por los tokens faltantes |
| `ejemplo3_error_sintactico.txt` | Falta un `;` entre dos declaraciones | ❌ Error sintáctico, token inesperado |
| `ejemplo4_funciones_anidadas.txt` | Una función llama a otra dentro de una expresión | ✅ Aceptado |
| `ejemplo5_expresiones_complejas.txt` | Paréntesis, operador unario `-`, `!`, combinaciones de `&&`/`\|\|` | ✅ Aceptado |
| `ejemplo6_multiples_errores_lexicos.txt` | 3 errores léxicos distintos (`5.`, `#`, `?`) en un mismo archivo | ❌ Los 3 se reportan juntos, en una sola pasada |
| `ejemplo7_error_sintactico_parentesis.txt` | Falta cerrar el paréntesis de la condición de un `if` | ❌ Error sintáctico, token inesperado |
| `ejemplo8_valido.txt` | Lista de variables con coma (`int a, b;`), tipo `char`, cadena, función con dos parámetros, llamada a función como sentencia, `if` sin llaves ni `else`, y `return` sin valor | ✅ Aceptado |
| `ejemplo9_error_lexico_comentario.txt` | Comentario de bloque (`/* ... */`) que nunca se cierra | ❌ 1 error léxico ("comentario de bloque sin cerrar"); el analizador ya no puede leer el resto del archivo con confianza, así que también falla el sintáctico (token inesperado `$`, falta el `}` que quedó del otro lado del comentario) |
| `ejemplo10_error_sintactico_asignacion.txt` | Se escribe `if (x = 10)` en vez de `if (x == 10)` — el error clásico de confundir asignación con comparación | ❌ Error sintáctico: `=` no es válido dentro de una `<Expresion>` |

Los ejemplos 9 y 10 muestran dos tipos de fallo distintos a los de los
ejemplos 2, 3, 6 y 7: el 9 es un error léxico que además **arrastra**
un error sintáctico (por la pérdida de contenido), y el 10 es un error
puramente sintáctico con el léxico limpio (todos los tokens son
válidos, pero el orden no encaja en la gramática).

Cada `ejemploN_*.txt` tiene su `salidaN_*.txt` correspondiente con la
salida **real** que produce `analizador.py` (no una salida esperada
escrita a mano) — tokens, errores, y para los casos aceptados, el
árbol sintáctico completo. Para regenerarla, o probar con tu propio
código:

```bash
python3 analizador.py ejemplos/ejemploN_*.txt > ejemplos/salidaN_*.txt
```

Ejemplo de cómo se ve el árbol sintáctico para `int a; float b;`:

```
└── programa
    └── Definiciones
        ├── Definicion
        │   └── DefVar
        │       ├── int
        │       ├── a
        │       ├── ListaVar
        │       └── ;
        └── Definiciones
            ├── Definicion
            │   └── DefVar
            │       ├── float
            │       ├── b
            │       ├── ListaVar
            │       └── ;
            └── Definiciones
```

---

## 8. Limitaciones conocidas

- El patrón de `cadena` (texto entre comillas dobles) se asumió por
  convención; la especificación no detalla si admite escapes como
  `\"`.
- La palabra reservada `void` se agrupó bajo el token `tipo` junto
  con `int` y `float`, aunque no aparecía explícitamente en la lista
  original de palabras reservadas.
- El analizador sintáctico se detiene en el primer error (no
  implementa recuperación de errores sintácticos), a diferencia del
  léxico, que sí reporta todos los errores en una sola pasada.

Ver `documento_diseno.md` para la explicación completa de por qué se
tomó cada una de estas decisiones.
