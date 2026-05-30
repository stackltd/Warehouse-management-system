import subprocess
import sys

if __name__ == "__main__":
    cmd = f'"{sys.executable}" -m pipdeptree --freeze --warn silence'
    raw_output = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, encoding="cp866"
    ).stdout

    all_lines = raw_output.split("\n")
    result = [line for line in all_lines if line and not line.startswith(" ")]

    with open("_requirements.txt", "w", encoding="utf-8") as obj:
        obj.write("\n".join(result))

    print(f"Успешно создано! Записано строк: {len(result)}")
