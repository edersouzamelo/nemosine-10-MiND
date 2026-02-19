import json, hashlib, sys, inspect, pkgutil, importlib
from pathlib import Path
import importlib.metadata as md

DIST="nemosine-mind"
PKG="nemosine_mind"

print("[MiND] version:", md.version(DIST))

def sha_dir(p):
    h=hashlib.sha256()
    p=Path(p)
    if not p.exists(): 
        return None
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()

def find_runner():
    pkg = importlib.import_module(PKG)
    # varre submódulos procurando funções candidatas
    candidates=[]
    for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        name = m.name
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        for fn_name in ["run", "run_loop", "execute", "process", "main"]:
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                candidates.append((name, fn_name, fn))
    return candidates

cands = find_runner()
if not cands:
    print("[FAIL] Não achei função runner (run/run_loop/execute/process/main) nos submódulos.")
    print("Ação: me diga qual arquivo/função você usa hoje pra rodar o loop.")
    sys.exit(2)

print("[INFO] candidatos encontrados (vou tentar o primeiro):")
for i,(m,fn,_) in enumerate(cands[:10], start=1):
    print(f"  {i}) {m}.{fn}")

mod_name, fn_name, fn = cands[0]
print("[TRY]", f"{mod_name}.{fn_name}")

# prepara input e diretórios
payload={"input":"determinismo","meta":{"case":"min"}}
Path("test_input.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

out1=Path("out1"); out2=Path("out2")
for o in [out1,out2]:
    if o.exists():
        for f in o.rglob("*"):
            if f.is_file(): f.unlink()
    o.mkdir(exist_ok=True)

# tenta chamar o runner com assinaturas comuns
def call_runner(outdir):
    sig = inspect.signature(fn)
    kwargs={}
    # heurísticas de parâmetros
    for p in sig.parameters.values():
        n=p.name.lower()
        if n in ["input_path","inputfile","input_file","input","payload"]:
            kwargs[p.name] = str(Path("test_input.json")) if "path" in n or "file" in n else payload
        elif n in ["out","outdir","out_dir","output","output_dir","path"]:
            kwargs[p.name] = str(outdir)
        elif n in ["persist","persist_path","log_path","jsonl_path","events_path"]:
            kwargs[p.name] = str(outdir / "events.jsonl")
    try:
        return fn(**kwargs)
    except TypeError as e:
        raise

try:
    call_runner(out1)
    call_runner(out2)
except TypeError as e:
    print("[FAIL] Achei runner, mas assinatura não bate com heurística.")
    print("Erro:", e)
    print("Assinatura:", str(inspect.signature(fn)))
    print("Arquivo:", mod_name)
    sys.exit(3)

h1=sha_dir(out1); h2=sha_dir(out2)
print("[HASH] out1:", h1)
print("[HASH] out2:", h2)

if h1 and h2 and h1==h2:
    print("[PASS] Determinismo OK (mesmo hash de diretório)")
else:
    print("[FAIL] Não determinístico ou nada gerado (hash diferente/None)")
