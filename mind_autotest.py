import subprocess, sys, json, hashlib
from pathlib import Path
import importlib.metadata as md

DIST = "nemosine-mind"
MOD = "nemosine_mind"

print("[MiND] version:", md.version(DIST))

# Tenta rodar via python -m
cmd = [sys.executable, "-m", MOD, "--help"]
cp = subprocess.run(cmd, capture_output=True, text=True)

if cp.returncode != 0:
    print("[FAIL] python -m nemosine_mind não executa.")
    print(cp.stderr)
    sys.exit(1)

print("[OK] CLI detectada via python -m")

# Agora tenta rodar loop mínimo (ajuste automático simples)
test_input = {
    "input": "determinismo",
    "meta": {"case": "min"}
}

Path("test_input.json").write_text(json.dumps(test_input), encoding="utf-8")

cmd = [sys.executable, "-m", MOD, "run", "--input", "test_input.json", "--out", "out1"]
subprocess.run(cmd)

cmd = [sys.executable, "-m", MOD, "run", "--input", "test_input.json", "--out", "out2"]
subprocess.run(cmd)

def hash_dir(p):
    h = hashlib.sha256()
    for f in sorted(Path(p).rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()

if Path("out1").exists() and Path("out2").exists():
    h1 = hash_dir("out1")
    h2 = hash_dir("out2")
    if h1 == h2:
        print("[PASS] Determinismo OK")
    else:
        print("[FAIL] Não determinístico")
else:
    print("[FAIL] Não gerou diretórios out1/out2")
