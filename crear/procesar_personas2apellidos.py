from pathlib import Path

def main():
    input_file = Path("data-pura") / "personas.txt"
    output_file = Path("data-procesada") / "apellidos.csv"
    apellidos_set = set()

    with input_file.open("r", encoding="utf-8") as f:
        for linea in f:
            partes = linea.strip().split()
            if len(partes) >= 3:
                apepat, apemat = partes[0], partes[1]
                apellidos_set.add(apepat)
                apellidos_set.add(apemat)

    apellidos_ordenados = sorted(apellidos_set)

    with output_file.open("w", encoding="utf-8") as f_out:
        for i, apellido in enumerate(apellidos_ordenados):
            if i < len(apellidos_ordenados) - 1:
                f_out.write(f"{apellido}\n")
            else:
                f_out.write(f"{apellido}")

    print(f"{len(apellidos_ordenados)} apellidos únicos guardados en {output_file}.")

if __name__ == "__main__":
    main()