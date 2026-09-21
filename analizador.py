"""
Analizador léxico y sintáctico (versión unificada)
===================================================
Proyecto Taller de Compiladores (Ing. Michel Emanuel López Franco)

Este archivo une, en un solo módulo, las dos primeras fases del
traductor:

  1. ANALIZADOR LÉXICO   -> código fuente (texto)  =>  lista de tokens
  2. ANALIZADOR SINTÁCTICO -> lista de tokens        =>  árbol sintáctico
                                                          (o error)

Se conserva exactamente el mismo comportamiento que las dos versiones
por separado (analizador_lexico.py + analizador_sintactico.py):

  - Cada token trae el CÓDIGO NUMÉRICO (0-23) de la tabla LR(1) del
    proyecto, y al final de la entrada se agrega el token especial
    "$" (código 23).
  - Los errores léxicos NO detienen el análisis: se reportan y se
    sigue leyendo, para mostrar todos los errores en una sola pasada.
  - El sintáctico usa un motor LR genérico que carga la gramática y
    la tabla de acciones/goto desde datos/compilador.lr, y construye
    el árbol sintáctico completo con la pila de objetos
    (Terminal / NoTerminal / Estado).
  - Un error sintáctico sí detiene el análisis de inmediato.

Cambios respecto a tener los dos archivos separados:

  - Un solo import, un solo archivo para leer y mantener.
  - `analizador_lexico()` ya NO guarda los errores en un atributo de
    la función (`analizador_lexico.errores`, un patrón poco claro);
    ahora regresa directamente `(tokens, errores)`.
  - Se agregó una interfaz de línea de comandos con `argparse`
    (antes era un `if len(sys.argv) >= 2`), incluyendo la opción
    `--traza` para ver paso a paso el análisis shift-reduce.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# =============================================================================
# FASE 1: ANALIZADOR LÉXICO
# =============================================================================

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
_nl = re.compile(r'\n')
_ident = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
_entero = re.compile(r'[0-9]+')
_real = re.compile(r'[0-9]+\.[0-9]+')   # real = entero . entero (según el PDF del proyecto)
_cadena = re.compile(r'"(?:[^"\\]|\\.)*"')


def analizador_lexico(src: str) -> Tuple[List[Tok], List[str]]:
    """
    Recorre 'src' y regresa una tupla (tokens, errores):

      - tokens: la lista completa de tokens con su código numérico,
        incluyendo los tokens de error (código -1) intercalados donde
        ocurrieron, y terminando siempre con el token "$" (código 23).
      - errores: la lista de mensajes de error léxico, con su
        ubicación exacta (línea y columna).
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

    return toks, errores


# =============================================================================
# FASE 2: ANALIZADOR SINTÁCTICO
# =============================================================================

# ---------------------------------------------------------------------------
# Jerarquía de clases para los elementos de la pila
# ---------------------------------------------------------------------------
class ElementoPila(ABC):
    @abstractmethod
    def muestra(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.muestra()


class Terminal(ElementoPila):
    def __init__(self, lexema: str, codigo: int):
        self.lexema = lexema
        self.codigo = codigo

    def muestra(self) -> str:
        return self.lexema


class NoTerminal(ElementoPila):
    def __init__(self, nombre: str, hijos: Optional[List[ElementoPila]] = None):
        self.nombre = nombre
        self.hijos = hijos if hijos is not None else []

    def muestra(self) -> str:
        return self.nombre

    def imprimir_arbol(self, prefijo: str = "", es_ultimo: bool = True) -> None:
        """Imprime este nodo y sus descendientes como árbol de texto."""
        conector = "└── " if es_ultimo else "├── "
        print(prefijo + conector + self.muestra())
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
        for i, hijo in enumerate(self.hijos):
            ultimo = (i == len(self.hijos) - 1)
            if isinstance(hijo, NoTerminal):
                hijo.imprimir_arbol(nuevo_prefijo, ultimo)
            else:
                conector_hijo = "└── " if ultimo else "├── "
                print(nuevo_prefijo + conector_hijo + hijo.muestra())


class Estado(ElementoPila):
    def __init__(self, numero: int):
        self.numero = numero

    def muestra(self) -> str:
        return str(self.numero)


class Pila:
    def __init__(self):
        self._elementos: List[ElementoPila] = []

    def push(self, elemento: ElementoPila) -> None:
        if not isinstance(elemento, ElementoPila):
            raise TypeError(f"Pila.push() solo acepta ElementoPila, se recibió {type(elemento).__name__}")
        self._elementos.append(elemento)

    def pop(self) -> ElementoPila:
        return self._elementos.pop()

    def top(self) -> ElementoPila:
        return self._elementos[-1]

    def muestra(self) -> str:
        return "$" + "".join(e.muestra() for e in self._elementos)


# ---------------------------------------------------------------------------
# Regla de la gramática, tal como viene en el .lr: solo el índice de
# columna del no terminal izquierdo, su longitud y su nombre (no se
# guarda el lado derecho porque el .lr no lo trae, y no se necesita
# para poder reducir).
# ---------------------------------------------------------------------------
class Regla:
    def __init__(self, numero: int, id_columna_izq: int, longitud: int, nombre_izq: str):
        self.numero = numero
        self.id_columna_izq = id_columna_izq
        self.longitud = longitud
        self.nombre_izq = nombre_izq


class GramaticaLR:
    """Gramática completa: lista de reglas + tabla LR como matriz de enteros."""

    def __init__(self, reglas: Dict[int, Regla], tabla: List[List[int]]):
        self.reglas = reglas
        self.tabla = tabla


def cargar_gramatica_lr(ruta_lr: str) -> GramaticaLR:
    with open(ruta_lr, "r", encoding="utf-8") as f:
        lineas = [l.rstrip("\n") for l in f if l.strip() != ""]

    cursor = 0
    num_reglas = int(lineas[cursor]); cursor += 1

    reglas: Dict[int, Regla] = {}
    for i in range(num_reglas):
        id_col, longitud, nombre = lineas[cursor].split("\t")
        # las reglas del .lr vienen en orden R1..Rn -> numero = i+1
        reglas[i + 1] = Regla(i + 1, int(id_col), int(longitud), nombre)
        cursor += 1

    num_filas, num_columnas = (int(x) for x in lineas[cursor].split("\t")); cursor += 1

    tabla: List[List[int]] = []
    for i in range(num_filas):
        fila = [int(x) for x in lineas[cursor].split("\t")]
        if len(fila) != num_columnas:
            raise ValueError(f"La fila {i} del .lr tiene {len(fila)} columnas, se esperaban {num_columnas}")
        tabla.append(fila)
        cursor += 1

    return GramaticaLR(reglas, tabla)


# ---------------------------------------------------------------------------
# Motor genérico shift-reduce, indexado por enteros
# ---------------------------------------------------------------------------
class ErrorSintactico(Exception):
    def __init__(self, mensaje: str, linea: int, columna: int):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna


class AnalizadorSintactico:
    def __init__(self, gramatica: GramaticaLR):
        self.gramatica = gramatica

    def analizar(self, tokens: List[Tok], mostrar_traza: bool = False) -> NoTerminal:
        """
        Corre el análisis. Si la cadena es aceptada, regresa el nodo
        raíz del árbol sintáctico (un NoTerminal cuyo nombre es el
        símbolo inicial de la gramática, con sus hijos completos). Si
        hay un error, lanza ErrorSintactico.
        """
        pila = Pila()
        pila.push(Estado(0))
        pos = 0
        tabla = self.gramatica.tabla
        ultimo_reducido: Optional[NoTerminal] = None

        if mostrar_traza:
            print(f"{'pila':<40}{'entrada':<25}salida")

        while True:
            estado_actual = pila.top().numero
            token = tokens[pos]

            celda = tabla[estado_actual][token.codigo]
            pila_str = pila.muestra()
            entrada_str = " ".join(t.valor for t in tokens[pos:])

            if celda == 0:
                if mostrar_traza:
                    print(f"{pila_str:<40}{entrada_str:<25}error")
                raise ErrorSintactico(
                    f"token inesperado '{token.valor}' (tipo '{token.nombre}')",
                    token.linea, token.columna,
                )

            if celda > 0:
                # desplazar (shift): el token se apila junto con el nuevo estado
                pila.push(Terminal(token.valor, token.codigo))
                pila.push(Estado(celda))
                pos += 1
                if mostrar_traza:
                    print(f"{pila_str:<40}{entrada_str:<25}d{celda}")
                continue

            # celda < 0 -> reducir con la regla (-celda - 1)
            numero_regla = -celda - 1
            if numero_regla == 0:
                if mostrar_traza:
                    print(f"{pila_str:<40}{entrada_str:<25}r0 (aceptar)")
                return ultimo_reducido

            regla = self.gramatica.reglas[numero_regla]

            # sacar los 'longitud' símbolos (cada uno con su estado) y
            # guardarlos, en orden izquierda->derecha, como hijos del
            # nuevo nodo del árbol
            hijos: List[ElementoPila] = []
            for _ in range(regla.longitud):
                pila.pop()               # el Estado que acompañaba al símbolo
                hijos.append(pila.pop())  # el símbolo (Terminal o NoTerminal)
            hijos.reverse()

            estado_previo = pila.top().numero
            nuevo_estado = tabla[estado_previo][regla.id_columna_izq]
            nodo = NoTerminal(regla.nombre_izq, hijos=hijos)
            pila.push(nodo)
            pila.push(Estado(nuevo_estado))
            ultimo_reducido = nodo
            if mostrar_traza:
                print(f"{pila_str:<40}{entrada_str:<25}r{regla.numero} {regla.nombre_izq} (long {regla.longitud})")


# ---------------------------------------------------------------------------
# Puente entre el analizador léxico y el sintáctico
# ---------------------------------------------------------------------------
def construir_analizador_sintactico(carpeta_datos: str) -> AnalizadorSintactico:
    gramatica = cargar_gramatica_lr(os.path.join(carpeta_datos, "compilador.lr"))
    return AnalizadorSintactico(gramatica)


def analizar_programa(codigo_fuente: str, carpeta_datos: str, mostrar_traza: bool = False) -> str:
    """
    Corre el pipeline completo (léxico + sintáctico) sobre un programa
    y regresa un reporte de texto con: los tokens reconocidos, los
    errores léxicos (si los hay) y el resultado del análisis
    sintáctico.
    """
    lineas_reporte = []

    tokens, errores_lexicos = analizador_lexico(codigo_fuente)

    lineas_reporte.append("=== TOKENS RECONOCIDOS (analizador léxico) ===")
    for t in tokens:
        if t.codigo in (-1, 23):
            continue
        lineas_reporte.append(f"  {t}")

    lineas_reporte.append("")
    lineas_reporte.append("=== ERRORES LÉXICOS ===")
    if errores_lexicos:
        for e in errores_lexicos:
            lineas_reporte.append(f"  {e}")
    else:
        lineas_reporte.append("  Ninguno")

    lineas_reporte.append("")
    lineas_reporte.append("=== ANÁLISIS SINTÁCTICO ===")

    # los tokens de error léxico no son válidos para el sintáctico
    tokens_validos = [t for t in tokens if t.codigo != -1]

    analizador = construir_analizador_sintactico(carpeta_datos)
    try:
        raiz = analizador.analizar(tokens_validos, mostrar_traza=mostrar_traza)
        lineas_reporte.append("  Programa aceptado: es sintácticamente correcto.")
        lineas_reporte.append("")
        lineas_reporte.append("=== ÁRBOL SINTÁCTICO ===")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            raiz.imprimir_arbol()
        lineas_reporte.append(buffer.getvalue().rstrip())
    except ErrorSintactico as e:
        lineas_reporte.append(f"  Error sintáctico en línea {e.linea}, columna {e.columna}: {e.mensaje}")

    return "\n".join(lineas_reporte)


# =============================================================================
# INTERFAZ DE LÍNEA DE COMANDOS
# =============================================================================
def _programa_de_ejemplo() -> str:
    return """
    int suma(int a, int b) {
        return a + b;
    }

    int main() {
        int x;
        x = suma(2, 3);
        if (x > 4) {
            return x;
        } else {
            return 0;
        }
    }
    """


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analizador léxico y sintáctico (LR) para el lenguaje del proyecto.",
    )
    parser.add_argument(
        "archivo", nargs="?",
        help="Archivo de código fuente a analizar. Si se omite, corre un programa de ejemplo.",
    )
    parser.add_argument(
        "--datos", default=None,
        help="Carpeta con compilador.lr (por defecto: ./datos junto a este script).",
    )
    parser.add_argument(
        "--traza", action="store_true",
        help="Muestra paso a paso (pila / entrada / acción) del análisis sintáctico.",
    )
    args = parser.parse_args(argv)

    carpeta_base = os.path.dirname(os.path.abspath(__file__))
    carpeta_datos = args.datos or os.path.join(carpeta_base, "datos")

    if args.archivo:
        with open(args.archivo, "r", encoding="utf-8") as f:
            codigo = f.read()
    else:
        codigo = _programa_de_ejemplo()

    print(analizar_programa(codigo, carpeta_datos, mostrar_traza=args.traza))
    return 0


if __name__ == "__main__":
    sys.exit(main())
