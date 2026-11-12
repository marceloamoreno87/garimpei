"""All internal import edges, including TYPE_CHECKING imports."""

import sys

import grimp


def main() -> int:
    graph = grimp.build_graph("garimpei", exclude_type_checking_imports=False)
    cycles = [
        (module, target)
        for module in sorted(graph.modules)
        for target in sorted(graph.find_modules_directly_imported_by(module))
        if module == target or graph.chain_exists(target, module)
    ]
    print(f"Cycles: {len(graph.modules)} modules, {len(cycles)} cyclic edges")
    for source, target in cycles:
        print(f"{source} -> {target} -> ... -> {source}")
    return 1 if cycles else 0


if __name__ == "__main__":
    sys.exit(main())
