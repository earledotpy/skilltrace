from compiler.common import sqlite_export_all, ValidationError
def main():
    try:
        path = sqlite_export_all()
        print(f"[OK] Exported SQLite database: {path}")
    except ValidationError as exc:
        print(f"[INVALID SQLITE EXPORT] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
