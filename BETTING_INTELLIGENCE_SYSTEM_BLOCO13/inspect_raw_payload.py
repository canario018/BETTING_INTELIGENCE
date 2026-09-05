from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect(node, path="$", depth=0, max_depth=3):
    indent = "  " * depth
    if depth > max_depth:
        return
    if isinstance(node, dict):
        print(f"{indent}{path}: object ({len(node)} chaves)")
        for key, value in list(node.items())[:40]:
            child = f"{path}.{key}"
            if isinstance(value, (dict, list)):
                inspect(value, child, depth + 1, max_depth)
            else:
                print(f"{indent}  {child}: {type(value).__name__} = {str(value)[:120]}")
    elif isinstance(node, list):
        print(f"{indent}{path}: array ({len(node)} itens)")
        for i, value in enumerate(node[:5]):
            if isinstance(value, (dict, list)):
                inspect(value, f"{path}[{i}]", depth + 1, max_depth)
            else:
                print(f"{indent}  {path}[{i}]: {type(value).__name__} = {str(value)[:120]}")


def main():
    parser = argparse.ArgumentParser(description="Inspeciona a estrutura de um RAW JSON sem imprimir o arquivo inteiro.")
    parser.add_argument("file", help="Caminho do JSON, por exemplo data/raw/r7bet_latest.json")
    parser.add_argument("--depth", type=int, default=3, help="Profundidade máxima de inspeção (padrão: 3)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"Arquivo não encontrado: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    print(f"Arquivo: {path}")
    print(f"Bytes: {path.stat().st_size}")
    print(f"Raiz: {type(raw).__name__}")
    print("=" * 100)
    inspect(raw, max_depth=args.depth)


if __name__ == "__main__":
    main()
