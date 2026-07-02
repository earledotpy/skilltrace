from compiler.common import validate_interface, print_validation_ok, ValidationError
def main():
    try:
        data = validate_interface()
        i = data["interface"]
        print_validation_ok("Interface layer loaded successfully", Commands=len(i["commands"]), Views=len(i["views"]), Cards=len(i["cards"]))
        print(f"Active view: {i['state'].get('active_view_id')}")
    except ValidationError as exc:
        print(f"[INVALID INTERFACE] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
