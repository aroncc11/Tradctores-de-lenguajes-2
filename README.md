# Mini Analizador Léxico

Este proyecto implementa un analizador léxico sencillo en Python para reconocer dos tipos de elementos:

- Identificadores
- Números reales

También detecta errores léxicos cuando encuentra caracteres o secuencias que no cumplen las reglas definidas.

---

## 1. ¿Qué es un analizador léxico?

Un analizador léxico, también llamado scanner, es la primera etapa de un compilador o traductor. Su función es leer el código fuente carácter por carácter y dividirlo en unidades llamadas tokens.

Por ejemplo, si el código contiene:

```python
x1 = 3.1416
```

el analizador podría producir tokens como:

- `ID` -> `x1`
- `REAL` -> `3.1416`

El objetivo es identificar partes importantes del lenguaje antes de que un analizador sintáctico las procese.

---

## 2. Reglas que reconoce el programa

El código está diseñado para reconocer exactamente estas expresiones:

- Identificador: `letra (letra | digito)*`
- Real: `entero . entero+`

Donde:

- `letra` = cualquier letra del alfabeto
- `digito` = cualquier número del 0 al 9
- `entero` = una secuencia de dígitos

### Ejemplos válidos

- `x`
- `contador2`
- `m1x`
- `3.1416`
- `25.5`
- `10.0`

### Ejemplos no válidos

- `8` (porque no se considera un real válido en este programa; exige parte decimal)
- `3.` (falta al menos un dígito después del punto)
- `@` o `#` (caracteres no permitidos)

---

## 3. Cómo funciona el código

El archivo principal es `Mini Analizador.py`.

### 3.1 Clase `Token`

La clase `Token` representa cada elemento encontrado por el analizador. Tiene estos atributos:

- `tipo`: puede ser `ID`, `REAL` o `ERROR`
- `lexema`: el texto reconocido
- `linea`: número de línea donde aparece
- `columna`: posición inicial en la línea

También tiene un método `__str__` para imprimir el token de manera legible.

### 3.2 Funciones auxiliares

```python
def es_letra(c):
    return c.isalpha()

def es_digito(c):
    return c.isdigit()
```

Estas funciones verifican si un carácter es una letra o un dígito.

### 3.3 Clase `AnalizadorLexico`

La clase principal mantiene el estado del análisis:

- `codigo`: el texto de entrada
- `pos`: posición actual del cursor dentro del texto
- `linea`: número de línea actual
- `columna`: columna actual
- `tokens`: lista de tokens reconocidos
- `errores`: lista de mensajes de error

#### Métodos importantes

##### `_caracter_actual()`
Devuelve el carácter actual en la posición actual del análisis. Si ya terminó el texto, devuelve `None`.

##### `_avanzar()`
Mueve el cursor al siguiente carácter y actualiza la línea y la columna. Esto permite llevar el control de posiciones exactas.

##### `analizar()`
Es el método principal. Recorre el código carácter por carácter y decide qué hacer según el caso:

1. Si encuentra espacio, tabulación, salto de línea o retorno de carro, lo ignora.
2. Si el carácter es una letra, empieza a formar un identificador.
3. Si el carácter es un dígito, intenta formar un número real.
4. Si encuentra un carácter no permitido, lo marca como error léxico.

---

## 4. Estados del autómata

El programa sigue una lógica tipo autómata finito. Los estados aparecen descritos en el encabezado del archivo:

- `S0`: estado inicial
- `S1`: leyendo un identificador
- `S2`: leyendo la parte entera de un número
- `S3`: se leyó el punto decimal y espera al menos un dígito
- `S4`: leyendo la parte decimal del real

Esta estructura hace que el análisis sea determinista y fácil de seguir.

---

## 5. ¿Qué hace exactamente el programa?

El programa:

- Lee una cadena de texto llamada `codigo_fuente`
- La recorre carácter por carácter
- Ignora espacios y saltos de línea
- Reconoce identificadores
- Reconoce reales con formato `entero.entero+`
- Guarda los tokens encontrados junto con su línea y columna
- Registra los errores léxicos si una secuencia no es válida
- Muestra el resultado en consola

---

## 6. Ejemplo de uso

En la parte final del archivo, hay un bloque de prueba:

```python
if __name__ == "__main__":
    codigo_prueba = """
    x1 = 3.1416
    contador2 total 25.5
    y = 8
    m1x = 10.0
    """

    analizador = AnalizadorLexico(codigo_prueba)
    tokens = analizador.analizar()
```

Este ejemplo genera un análisis sobre este texto:

```text
x1 = 3.1416
contador2 total 25.5
y = 8
m1x = 10.0
```

### Resultado esperado

Se imprime una lista de tokens como:

```text
=== Tokens reconocidos ===
<ID, 'x1'>  (línea 2, col 5)
<REAL, '3.1416'>  (línea 2, col 9)
...
```

Y si hay errores, se muestran mensajes tipo:

```text
Línea 4, col 9: '8' no es un real válido (falta la parte decimal)
```

---

## 7. Importante sobre el comportamiento actual

Este programa está hecho para una gramática muy específica. Por eso:

- `x1` se reconoce como identificador
- `3.1416` se reconoce como real
- `25.5` se reconoce como real
- `8` no se acepta como real válido, porque la regla exige la parte decimal
- `3.` genera error porque después del punto debe haber al menos un dígito

Esto es clave para entender que el analizador no es un analizador de números enteros, sino de reales con el formato que se definió en el enunciado.

---

## 8. Estructura del programa

El código está organizado de forma clara en secciones:

1. Comentario inicial con descripción del problema
2. Definición de `Token`
3. Funciones de clasificación de caracteres
4. Clase `AnalizadorLexico`
5. Bloque de prueba principal

Esto facilita su lectura y posible modificación.

---

## 9. Cómo ejecutar el programa

Desde la terminal, ubícate en la carpeta del proyecto y ejecuta:

```bash
python "Mini Analizador.py"
```

En Windows PowerShell puede ser:

```powershell
python .\"Mini Analizador.py\"
```

O, si tienes Python asociado como `py`:

```powershell
py .\"Mini Analizador.py\"
```

---

## 10. Conclusión

Este proyecto demuestra de manera práctica cómo se construye un analizador léxico básico en Python. Permite entender conceptos clave como:

- reconocimiento de tokens
- recorrido de cadenas
- control de líneas y columnas
- manejo de errores léxicos
- diseño de un autómata finito simple

Es un ejemplo muy útil para empezar a estudiar compiladores, traductores de lenguaje y teoría de automatas.
