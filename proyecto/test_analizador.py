"""
Script de prueba para el analizador léxico.

Lee un archivo de código fuente (por defecto "prueba.txt") y muestra
la tabla de tokens reconocidos junto con los errores léxicos, si los
hay.

Uso:
    python3 test_analizador.py                # usa prueba.txt
    python3 test_analizador.py otro_archivo.c  # usa otro archivo
"""

import sys
from analizador_lexico_final import analizador_lexico


def analizar_archivo(ruta: str):
    with open(ruta, "r", encoding="utf-8") as f:
        codigo_fuente = f.read()

    tokens = analizador_lexico(codigo_fuente)
    errores = analizador_lexico.errores

    print(f"Archivo analizado: {ruta}")
    print(f"Total de tokens:  {len(tokens)}")
    print(f"Total de errores: {len(errores)}\n")

    print(f"{'Lexema':<15}{'Código':<8}Token")
    print("-" * 45)
    for t in tokens:
        print(f"{t.valor:<15}{t.codigo:<8}{t.nombre}")

    print("\n=== Errores léxicos ===")
    print("Ninguno" if not errores else "\n".join(errores))


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "prueba.txt"
    analizar_archivo(ruta)
