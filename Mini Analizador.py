"""
Analizador léxico (scanner)
----------------------------
Seminario de Solución de Problemas de Traductores de Lenguaje II
Reconoce dos categorías de tokens a partir de las siguientes reglas:

    identificador = letra (letra | digito)*
    real          = entero . entero+          (entero = digito+)

El analizador se implementa como un autómata finito determinista (AFD)
recorrido carácter por carácter, tal como se explicó en el reporte sobre
analizadores léxicos.

Estados del autómata:
    S0  -> estado inicial
    S1  -> leyendo un identificador (letra ya leída)
    S2  -> leyendo la parte entera de un número
    S3  -> se leyó el punto decimal, se espera al menos un dígito
    S4  -> leyendo la parte decimal de un número real (estado de aceptación)
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Definición de un token
# ---------------------------------------------------------------------------
@dataclass
class Token:
    tipo: str      # "ID", "REAL" o "ERROR"
    lexema: str    # cadena de caracteres reconocida
    linea: int
    columna: int

    def __str__(self):
        return f"<{self.tipo}, '{self.lexema}'>  (línea {self.linea}, col {self.columna})"


# ---------------------------------------------------------------------------
# Funciones auxiliares de clasificación de caracteres
# ---------------------------------------------------------------------------
def es_letra(c):
    return c.isalpha()


def es_digito(c):
    return c.isdigit()


# ---------------------------------------------------------------------------
# Analizador léxico
# ---------------------------------------------------------------------------
class AnalizadorLexico:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.tokens = []
        self.errores = []

    def _caracter_actual(self):
        if self.pos < len(self.codigo):
            return self.codigo[self.pos]
        return None

    def _avanzar(self):
        c = self._caracter_actual()
        if c == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        self.pos += 1

    def analizar(self):
        while self._caracter_actual() is not None:
            c = self._caracter_actual()

            # Ignorar espacios en blanco, tabuladores y saltos de línea
            if c in (" ", "\t", "\n", "\r"):
                self._avanzar()
                continue

            linea_inicio, col_inicio = self.linea, self.columna

            # --- S0 -> S1 : inicio de identificador -----------------------
            if es_letra(c):
                lexema = c
                self._avanzar()
                while self._caracter_actual() is not None and (
                    es_letra(self._caracter_actual()) or es_digito(self._caracter_actual())
                ):
                    lexema += self._caracter_actual()
                    self._avanzar()
                self.tokens.append(Token("ID", lexema, linea_inicio, col_inicio))
                continue

            # --- S0 -> S2 : inicio de número (entero o real) ---------------
            if es_digito(c):
                lexema = c
                self._avanzar()
                # S2: parte entera
                while self._caracter_actual() is not None and es_digito(self._caracter_actual()):
                    lexema += self._caracter_actual()
                    self._avanzar()

                # ¿hay punto decimal? -> S3
                if self._caracter_actual() == ".":
                    lexema += "."
                    self._avanzar()

                    # S3 -> S4 : se requiere al menos un dígito tras el punto
                    if self._caracter_actual() is not None and es_digito(self._caracter_actual()):
                        while self._caracter_actual() is not None and es_digito(self._caracter_actual()):
                            lexema += self._caracter_actual()
                            self._avanzar()
                        self.tokens.append(Token("REAL", lexema, linea_inicio, col_inicio))
                    else:
                        # Error léxico: el punto no fue seguido de dígitos
                        self.tokens.append(Token("ERROR", lexema, linea_inicio, col_inicio))
                        self.errores.append(
                            f"Línea {linea_inicio}, col {col_inicio}: número real mal formado '{lexema}'"
                        )
                else:
                    # Cadena de dígitos sin punto: no cumple la definición de
                    # "real" (entero.entero+), se reporta como error léxico.
                    self.tokens.append(Token("ERROR", lexema, linea_inicio, col_inicio))
                    self.errores.append(
                        f"Línea {linea_inicio}, col {col_inicio}: '{lexema}' no es un real válido "
                        f"(falta la parte decimal)"
                    )
                continue

            # --- carácter no reconocido por la gramática --------------------
            self.tokens.append(Token("ERROR", c, linea_inicio, col_inicio))
            self.errores.append(f"Línea {linea_inicio}, col {col_inicio}: carácter no válido '{c}'")
            self._avanzar()

        return self.tokens


# ---------------------------------------------------------------------------
# Programa de prueba
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    codigo_prueba = """
    x1 = 3.1416
    contador2 total 25.5
    y = 8
    m1x = 10.0
    """

    analizador = AnalizadorLexico(codigo_prueba)
    tokens = analizador.analizar()

    print("=== Tokens reconocidos ===")
    for t in tokens:
        print(t)

    print("\n=== Errores léxicos ===")
    if analizador.errores:
        for e in analizador.errores:
            print(e)
    else:
        print("Ninguno")