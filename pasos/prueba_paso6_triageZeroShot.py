import sys 
from pathlib import Path    

BASE_DIR=Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


from M1P1.prompts import renderizar_system


def main():
    prompt = renderizar_system("v1ZeroShot")
    print(prompt)

if __name__ == "__main__":
    main()