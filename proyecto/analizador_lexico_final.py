"""
Analizador léxico (versión final)
-----------------------------------
Proyecto Taller Compiladores (Ing. Michel Emanuel López Franco)

Basado en el archivo "Mini Analizador.py" (expresiones regulares),
adaptado para cumplir exactamente lo que pide el profesor:

  1. Cada token regresa el CÓDIGO NUMÉRICO (0-23) de la tabla LR(1)
     del proyecto, no solo un nombre de texto.
  2. Al final de la entrada se agrega el token especial "$" (código 23).
  3. Los errores léxicos NO detienen el análisis: se reportan y se
     continúa leyendo, para poder mostrar todos los errores de una
     sola pasada (igual que en analizador_lexico_completo.py).

Se conservan las ventajas de tu versión original: reconocimiento con
expresiones regulares, soporte de comentarios de línea "//" y de
bloque "/* ... */", y el operador módulo "%".
"""

import re
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Tabla de códigos de token (debe coincidir con la tabla LR(1) del proyecto)
# ---------------------------------------------------------------------------
COD_IDENTIFICADOR = 0
COD_ENTERO = 1
COD_REAL = 2
COD_CADENA = 3
COD_TIPO = 4
COD_OPSUMA = 5
COD_OPMUL = 6
COD_OPRELAC = 7
COD_OPOR = 8
COD_OPAND = 9
COD_OPNOT = 10
COD_OPIGUALDAD = 11
COD_PYCOMA = 12
COD_COMA = 13
COD_PARIZQ = 14
COD_PARDER = 15
COD_LLAIZQ = 16
COD_LLADER = 17
COD_ASIGNACION = 18
COD_IF = 19
COD_WHILE = 20
COD_RETURN = 21
COD_ELSE = 22
COD_FIN = 23
COD_ERROR = -1

NOMBRE_CODIGO = {
    0: "IDENTIFICADOR", 1: "ENTERO", 2: "REAL", 3: "CADENA", 4: "TIPO",
    5: "OP_SUMA", 6: "OP_MUL", 7: "OP_RELAC", 8: "OP_OR", 9: "OP_AND",
    10: "OP_NOT", 11: "OP_IGUALDAD", 12: "PUNTO_Y_COMA", 13: "COMA",
    14: "PARENTESIS_IZQ", 15: "PARENTESIS_DER", 16: "LLAVE_IZQ",
    17: "LLAVE_DER", 18: "ASIGNACION", 19: "IF", 20: "WHILE",
    21: "RETURN", 22: "ELSE", 23: "$", -1: "ERROR",
}

# Palabras reservadas -> código
RESERVADAS_TIPO = {"int": COD_TIPO, "float": COD_TIPO, "void": COD_TIPO, "char": COD_TIPO}
RESERVADAS = {
    "if": COD_IF,
    "while": COD_WHILE,
    "return": COD_RETURN,
    "else": COD_ELSE,
}

# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------
@dataclass
class Tok:
    codigo: int     # código numérico (0-23), lo que pide la tabla LR(1)
    valor: str      # lexema
    linea: int
    columna: int

    @property
    def nombre(self):
        """Nombre legible del token, solo para depuración/impresión."""
        return NOMBRE_CODIGO.get(self.codigo, "?")

    def __str__(self):
        return f"<'{self.valor}', {self.codigo}:{self.nombre}>  (línea {self.linea}, col {self.columna})"


# ---------------------------------------------------------------------------
# Expresiones regulares base
# ---------------------------------------------------------------------------
_espacios = re.compile(r'[ \t\r]+')
_nl       = re.compile(r'\n')
_ident    = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
_entero   = re.compile(r'[0-9]+')
_real     = re.compile(r'[0-9]+\.[0-9]+')   # real = entero . entero (según el PDF del proyecto)
_cadena   = re.compile(r'"(?:[^"\\]|\\.)*"')


def analizador_lexico(src: str) -> List[Tok]:
    """
    Recorre 'src' y regresa la lista de tokens con su código numérico.
    Los errores léxicos se agregan a la lista de tokens (código -1) y
    también se acumulan en analizador_lexico.errores para revisarlos
    después de la llamada.
    """
    i = 0
    linea = 1
    col = 1
    n = len(src)
    toks: List[Tok] = []
    errores: List[str] = []

    def adv(m):
        nonlocal i, col
        s, e = m.span()
        texto = src[s:e]
        i = e
        col += (e - s)
        return texto

    while i < n:
        # saltar espacios
        m = _espacios.match(src, i)
        if m:
            adv(m)
            continue

        # comentario de línea
        if src.startswith("//", i):
            j = src.find("\n", i)
            if j < 0:
                j = n
            col += (j - i)
            i = j
            continue

        # comentario de bloque
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                errores.append(f"Línea {linea}, col {col}: comentario de bloque sin cerrar")
                i = n  # ya no se puede seguir leyendo de forma confiable
                break
            comentario = src[i:j + 2]
            nl_count = comentario.count("\n")
            if nl_count:
                linea += nl_count
                col = len(comentario.split("\n")[-1]) + 1
            else:
                col += len(comentario)
            i = j + 2
            continue

        # saltos de línea
        m = _nl.match(src, i)
        if m:
            adv(m)
            linea += 1
            col = 1
            continue

        li_actual, col_actual = linea, col

        # --- real: debe intentarse ANTES que entero (10.5 no es 10 y .5) ---
        m = _real.match(src, i)
        if m:
            lex = adv(m)
            toks.append(Tok(COD_REAL, lex, li_actual, col_actual))
            continue

        # entero seguido de "." sin dígitos después -> error léxico
        m = _entero.match(src, i)
        if m:
            lex = adv(m)
            if i < n and src[i] == ".":
                # consumimos el punto para reportar el lexema completo
                lex_err = lex + "."
                i += 1
                col += 1
                errores.append(f"Línea {li_actual}, col {col_actual}: real mal formado '{lex_err}'")
                toks.append(Tok(COD_ERROR, lex_err, li_actual, col_actual))
            else:
                toks.append(Tok(COD_ENTERO, lex, li_actual, col_actual))
            continue

        m = _cadena.match(src, i)
        if m:
            lex = adv(m)
            toks.append(Tok(COD_CADENA, lex, li_actual, col_actual))
            continue

        m = _ident.match(src, i)
        if m:
            lex = adv(m)
            if lex in RESERVADAS_TIPO:
                toks.append(Tok(RESERVADAS_TIPO[lex], lex, li_actual, col_actual))
            elif lex in RESERVADAS:
                toks.append(Tok(RESERVADAS[lex], lex, li_actual, col_actual))
            else:
                toks.append(Tok(COD_IDENTIFICADOR, lex, li_actual, col_actual))
            continue

        # --- operadores de dos caracteres primero ---
        two = src[i:i + 2]
        one = src[i]

        if two in ("==", "!=", "<=", ">=", "&&", "||"):
            codigo = {
                "&&": COD_OPAND, "||": COD_OPOR,
                "==": COD_OPIGUALDAD, "!=": COD_OPIGUALDAD,
                "<=": COD_OPRELAC, ">=": COD_OPRELAC,
            }[two]
            toks.append(Tok(codigo, two, li_actual, col_actual))
            i += 2
            col += 2
            continue

        if one in "+-":
            toks.append(Tok(COD_OPSUMA, one, li_actual, col_actual)); i += 1; col += 1; continue
        if one in "*/%":
            toks.append(Tok(COD_OPMUL, one, li_actual, col_actual)); i += 1; col += 1; continue
        if one in "<>":
            toks.append(Tok(COD_OPRELAC, one, li_actual, col_actual)); i += 1; col += 1; continue
        if one == "!":
            toks.append(Tok(COD_OPNOT, "!", li_actual, col_actual)); i += 1; col += 1; continue
        if one == "=":
            toks.append(Tok(COD_ASIGNACION, "=", li_actual, col_actual)); i += 1; col += 1; continue

        mapa_punc = {
            ";": COD_PYCOMA, ",": COD_COMA,
            "(": COD_PARIZQ, ")": COD_PARDER,
            "{": COD_LLAIZQ, "}": COD_LLADER,
        }
        if one in mapa_punc:
            toks.append(Tok(mapa_punc[one], one, li_actual, col_actual)); i += 1; col += 1; continue

        # carácter inválido: se reporta pero NO se detiene el análisis
        errores.append(f"Línea {li_actual}, col {col_actual}: carácter inválido '{one}'")
        toks.append(Tok(COD_ERROR, one, li_actual, col_actual))
        i += 1
        col += 1

    # marca de fin de cadena, símbolo $ (código 23)
    toks.append(Tok(COD_FIN, "$", linea, col))

    analizador_lexico.errores = errores
    return toks


# ---------------------------------------------------------------------------
# Programa de prueba
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    codigo_prueba = """
    int contador;
    float promedio;
    contador = 0;
    promedio = 12.5;

    while (contador <= 10) {
        if (contador != 5 && promedio >= 10.0) {
            promedio = promedio + 1.5;
        } else {
            promedio = promedio - 1;
        }
        contador = contador + 1;
    }

    if (contador == 10 || promedio < 0.0) {
        return promedio;
    }
    """

    tokens = analizador_lexico(codigo_prueba)

    print(f"{'Lexema':<15}{'Código':<8}Token")
    print("-" * 45)
    for t in tokens:
        print(f"{t.valor:<15}{t.codigo:<8}{t.nombre}")

    print("\n=== Errores léxicos ===")
    errores = analizador_lexico.errores
    print("Ninguno" if not errores else "\n".join(errores))
