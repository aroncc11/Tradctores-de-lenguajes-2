"""
Práctica 3 — Analizador Sintáctico LR(1) con pila de objetos
----------------------------------------------------------------
Seminario de Solución de Problemas de Traductores de Lenguaje II
(Prof. Ing. Michel Emanuel López Franco)

Esta versión modifica el analizador de la práctica anterior
(analizador_sintactico.py, que se deja como respaldo en
analizador_sintactico_respaldo.py) para que la pila ya no guarde
tuplas (símbolo, estado), sino OBJETOS, siguiendo el mismo patrón
que el ejemplo de "Alumno / Bachillerato / Licenciatura" del PDF:

    ElementoPila            <- clase base (equivalente a "Alumno")
        ├── Terminal        <- símbolo terminal (id, +, $)
        ├── NoTerminal       <- símbolo no terminal (E)
        └── Estado            <- número de estado del autómata LR (0,1,2,3,4)

Cada subclase sobreescribe el método virtual `muestra()`, así que al
imprimir la pila, cada objeto sabe representarse a sí mismo — igual
que en el ejemplo del PDF donde cada tipo de Alumno tenía su propio
`muestra()`.

La clase `Pila` ya no usa `list` de enteros: su `push()` y `pop()`
reciben y regresan objetos `ElementoPila*` (en Python, instancias de
`ElementoPila` o de sus subclases).
"""

from typing import Dict, List, Tuple, Optional


# ---------------------------------------------------------------------------
# Jerarquía de clases para los elementos de la pila
# ---------------------------------------------------------------------------
class ElementoPila:
    """
    Clase base para todo lo que se puede meter a la pila del analizador.
    Equivale a la clase "Alumno" del ejemplo del PDF: no se crean
    instancias de ElementoPila directamente, solo de sus subclases.
    """

    def muestra(self) -> str:
        """Método virtual: cada subclase decide cómo representarse."""
        raise NotImplementedError("Las subclases deben implementar muestra()")

    def __str__(self) -> str:
        return self.muestra()


class Terminal(ElementoPila):
    """Símbolo terminal de la gramática (un token): id, +, $, etc."""

    def __init__(self, lexema: str, tipo: Optional[str] = None):
        self.lexema = lexema
        self.tipo = tipo or lexema

    def muestra(self) -> str:
        return self.lexema


class NoTerminal(ElementoPila):
    """Símbolo no terminal de la gramática, p. ej. E."""

    def __init__(self, nombre: str):
        self.nombre = nombre

    def muestra(self) -> str:
        return self.nombre


class Estado(ElementoPila):
    """Número de estado del autómata LR (lo que en la traza aparece como 0,1,2,3,4...)."""

    def __init__(self, numero: int):
        self.numero = numero

    def muestra(self) -> str:
        return str(self.numero)


# ---------------------------------------------------------------------------
# Pila de objetos (equivalente a la clase Pila del PDF, con push/pop de
# ElementoPila* en lugar de enteros)
# ---------------------------------------------------------------------------
class Pila:
    def __init__(self):
        self._elementos: List[ElementoPila] = []

    def push(self, elemento: ElementoPila) -> None:
        self._elementos.append(elemento)

    def pop(self) -> ElementoPila:
        return self._elementos.pop()

    def top(self) -> ElementoPila:
        return self._elementos[-1]

    def __len__(self) -> int:
        return len(self._elementos)

    def muestra(self) -> str:
        """Representación compacta, como en el análisis manual: $0a2+3..."""
        return "$" + "".join(e.muestra() for e in self._elementos)

    def muestra_detallada(self) -> str:
        """
        Representación línea por línea, igual que pila.muestra() en el
        ejemplo del PDF (cada objeto imprime su propia información
        aprovechando el polimorfismo de muestra()).
        """
        lineas = ["Pila (de arriba hacia abajo):"]
        for elemento in reversed(self._elementos):
            lineas.append(f"  [{type(elemento).__name__}] {elemento.muestra()}")
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Tokenizador (igual que en la práctica anterior)
# ---------------------------------------------------------------------------
def tokenizar(entrada: str) -> List[Tuple[str, str]]:
    tokens = []
    i = 0
    n = len(entrada)
    while i < n:
        c = entrada[i]
        if c.isspace():
            i += 1
            continue
        if c.isalpha():
            j = i
            while j < n and entrada[j].isalpha():
                j += 1
            tokens.append(("id", entrada[i:j]))
            i = j
            continue
        if c == "+":
            tokens.append(("+", "+"))
            i += 1
            continue
        tokens.append(("otro", c))
        i += 1
    tokens.append(("$", "$"))
    return tokens


# ---------------------------------------------------------------------------
# Tabla de la gramática (reglas, ACTION, GOTO) — igual estructura que antes
# ---------------------------------------------------------------------------
class Regla:
    def __init__(self, numero: int, izq: str, derecha: str, longitud: int):
        self.numero = numero
        self.izq = izq            # no terminal que produce la regla, p. ej. "E"
        self.derecha = derecha    # texto descriptivo, solo para imprimir
        self.longitud = longitud  # cuántos SÍMBOLOS (no elementos de pila) se reducen


class Accion:
    def __init__(self, tipo: str, valor: int = None):
        self.tipo = tipo          # "shift", "reduce" o "aceptar"
        self.valor = valor        # estado destino (shift) o número de regla (reduce)


class TablaGramatica:
    def __init__(self, nombre: str, action: Dict[Tuple[int, str], Accion],
                 goto: Dict[Tuple[int, str], int], reglas: Dict[int, Regla]):
        self.nombre = nombre
        self.action = action
        self.goto = goto
        self.reglas = reglas


# ---------------------------------------------------------------------------
# Motor genérico shift-reduce, ahora con pila de objetos
# ---------------------------------------------------------------------------
class AnalizadorSintactico:
    def __init__(self, tabla: TablaGramatica):
        self.tabla = tabla

    def analizar(self, entrada: str, mostrar_traza: bool = True):
        tokens = tokenizar(entrada)
        pila = Pila()
        pila.push(Estado(0))  # estado inicial
        pos = 0

        if mostrar_traza:
            print(f"{'pila':<28}{'entrada':<20}salida")

        while True:
            estado_actual = pila.top().numero  # el tope siempre es un Estado
            tipo_token, lexema_token = tokens[pos]

            accion = self.tabla.action.get((estado_actual, tipo_token))

            pila_str = pila.muestra()
            entrada_str = "".join(l for _, l in tokens[pos:])

            if accion is None:
                if mostrar_traza:
                    print(f"{pila_str:<28}{entrada_str:<20}error")
                return False, f"Error sintáctico: token inesperado '{lexema_token}' en la posición {pos}"

            if accion.tipo == "shift":
                pila.push(Terminal(lexema_token, tipo_token))
                pila.push(Estado(accion.valor))
                pos += 1
                if mostrar_traza:
                    print(f"{pila_str:<28}{entrada_str:<20}d{accion.valor}")

            elif accion.tipo == "reduce":
                regla = self.tabla.reglas[accion.valor]
                # cada símbolo de la regla ocupa 2 elementos en la pila
                # (el símbolo mismo + el estado que le sigue)
                for _ in range(regla.longitud * 2):
                    pila.pop()
                estado_previo = pila.top().numero
                nuevo_estado = self.tabla.goto[(estado_previo, regla.izq)]
                pila.push(NoTerminal(regla.izq))
                pila.push(Estado(nuevo_estado))
                if mostrar_traza:
                    print(f"{pila_str:<28}{entrada_str:<20}r{regla.numero} {regla.izq}->{regla.derecha}")

            elif accion.tipo == "aceptar":
                if mostrar_traza:
                    print(f"{pila_str:<28}{entrada_str:<20}r0 (aceptar)")
                return True, "Cadena aceptada"


# ---------------------------------------------------------------------------
# Ejercicio 1:  E -> id  |  E -> id + id
# ---------------------------------------------------------------------------
def construir_ejercicio1() -> TablaGramatica:
    reglas = {
        1: Regla(1, "E", "id", longitud=1),
        2: Regla(2, "E", "id + id", longitud=3),
    }
    action = {
        (0, "id"): Accion("shift", 2),
        (2, "+"): Accion("shift", 3),
        (2, "$"): Accion("reduce", 1),
        (3, "id"): Accion("shift", 4),
        (4, "$"): Accion("reduce", 2),
        (1, "$"): Accion("aceptar"),
    }
    goto = {
        (0, "E"): 1,
    }
    return TablaGramatica("Ejercicio 1: E -> id | id + id", action, goto, reglas)


# ---------------------------------------------------------------------------
# Ejercicio 2:  E -> id + E  |  E -> id     (recursión derecha)
# ---------------------------------------------------------------------------
def construir_ejercicio2() -> TablaGramatica:
    reglas = {
        1: Regla(1, "E", "id + E", longitud=3),
        2: Regla(2, "E", "id", longitud=1),
    }
    action = {
        (0, "id"): Accion("shift", 2),
        (2, "+"): Accion("shift", 3),
        (2, "$"): Accion("reduce", 2),
        (3, "id"): Accion("shift", 2),
        (4, "$"): Accion("reduce", 1),
        (1, "$"): Accion("aceptar"),
    }
    goto = {
        (0, "E"): 1,
        (3, "E"): 4,
    }
    return TablaGramatica("Ejercicio 2: E -> id + E | id", action, goto, reglas)


# ---------------------------------------------------------------------------
# Ejemplo directo de la pila de objetos (equivalente a la función
# "ejemplo()" del PDF con Alumno/Bachillerato/Licenciatura), para
# mostrar el polimorfismo de muestra() de forma aislada.
# ---------------------------------------------------------------------------
def ejemplo_pila_objetos():
    pila = Pila()
    pila.push(Estado(0))
    pila.push(Terminal("hola", "id"))
    pila.push(Estado(2))
    pila.push(Terminal("+", "+"))
    pila.push(Estado(3))
    pila.push(Terminal("mundo", "id"))
    pila.push(Estado(4))

    print(pila.muestra_detallada())
    print(f"\nRepresentación compacta: {pila.muestra()}")

    print("\n*********************************")
    pila.pop()  # saca el Estado(4)
    pila.pop()  # saca el Terminal("mundo")
    print(pila.muestra_detallada())


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "--ejemplo-pila":
        ejemplo_pila_objetos()
        sys.exit(0)

    ej1 = AnalizadorSintactico(construir_ejercicio1())
    ej2 = AnalizadorSintactico(construir_ejercicio2())

    if len(sys.argv) >= 3:
        numero_ejercicio = sys.argv[1]
        cadena = sys.argv[2]
        analizador = ej1 if numero_ejercicio == "1" else ej2

        print(f"Analizando '{cadena}' con el Ejercicio {numero_ejercicio}\n")
        ok, mensaje = analizador.analizar(cadena)
        print(f"\n>>> {mensaje}")
        sys.exit(0 if ok else 1)

    casos_ej1 = ["a", "hola+mundo", "5"]
    casos_ej2 = ["a+b+c+d+e+f"]

    print("=" * 60)
    print("EJERCICIO 1:  E -> id | id + id")
    print("=" * 60)
    for caso in casos_ej1:
        print(f"\nCadena de entrada: '{caso}'")
        ok, mensaje = ej1.analizar(caso)
        print(f"Resultado: {mensaje}")

    print("\n" + "=" * 60)
    print("EJERCICIO 2:  E -> id + E | id")
    print("=" * 60)
    for caso in casos_ej2:
        print(f"\nCadena de entrada: '{caso}'")
        ok, mensaje = ej2.analizar(caso)
        print(f"Resultado: {mensaje}")