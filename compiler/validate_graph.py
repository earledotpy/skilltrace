from compiler.common import validate_graph, print_validation_ok, ValidationError
def main():
    try:
        g = validate_graph()
        print_validation_ok("Graph layer loaded successfully", Nodes=len(g["nodes"]), Edges=len(g["edges"]))
        for state, count in sorted(g["state_counts"].items()):
            print(f"{state}: {count}")
    except ValidationError as exc:
        print(f"[INVALID GRAPH] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()
