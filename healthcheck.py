import sys
from hogar_confianza.database.engine import get_engine, init_db
from hogar_confianza.database.seed import seed_providers

try:
    engine = get_engine()
    init_db(engine)
    seed_providers(engine)
    print("OK")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
