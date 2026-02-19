from __future__ import annotations

import os

def main() -> None:
    """
    Entry-point mínimo para permitir:
      python -m nemosine_mind
    """
    # Import tardio para não quebrar import do pacote
    from . import main as app_main  # src/nemosine_mind/main.py

    # Preferência: se existir app FastAPI, subir com uvicorn
    # (não inventa flags aqui; objetivo é existir um entrypoint executável)
    host = os.getenv("MIND_HOST", "127.0.0.1")
    port = int(os.getenv("MIND_PORT", "8000"))

    try:
        import uvicorn
    except Exception as e:
        raise SystemExit("uvicorn não instalado no ambiente. instale com: pip install uvicorn") from e

    # tenta achar "app" dentro do main.py
    app = getattr(app_main, "app", None)
    if app is None:
        raise SystemExit("Não encontrei variável 'app' (FastAPI) em nemosine_mind.main")

    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
