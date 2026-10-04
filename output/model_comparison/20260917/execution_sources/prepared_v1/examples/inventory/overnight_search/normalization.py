"""Neutral import placement correction; submitted source text stays unchanged."""
import ast


IMPORT_NORMALIZATION_REVISION = "leading_numerical_imports_v1"


def normalize_leading_policy_imports(tree):
    """Hoist leading numerical imports, preserving every original AST line.

    OPT_PARAM extraction still reads the original source and original assignment
    line numbers. Conditional/nonleading imports and other modules remain subject
    to the unchanged validator. Ambiguous rebinding is not normalized.
    """
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if len(functions) != 1 or functions[0].name != "compute_order_amount":
        return tree, []
    fn = functions[0]
    start = int(bool(fn.body and isinstance(fn.body[0], ast.Expr)
                     and isinstance(fn.body[0].value, ast.Constant)
                     and isinstance(fn.body[0].value.value, str)))
    imports = []
    for node in fn.body[start:]:
        allowed = (isinstance(node, ast.Import)
                   and all(alias.name in {"math", "numpy"} for alias in node.names))
        allowed = allowed or (isinstance(node, ast.ImportFrom)
                              and node.module == "math" and node.level == 0)
        if not allowed:
            break
        imports.append(node)
    if not imports:
        return tree, []
    bound = {alias.asname or alias.name for node in imports for alias in node.names}
    arguments = {arg.arg for arg in (fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs)}
    if fn.args.vararg:
        arguments.add(fn.args.vararg.arg)
    if fn.args.kwarg:
        arguments.add(fn.args.kwarg.arg)
    remainder = fn.body[start + len(imports):]
    # Moving an import must not expose an unbound local or change an argument.
    local_bindings = {node.id for statement in remainder for node in ast.walk(statement)
                      if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))}
    local_bindings.update(alias.asname or alias.name
                          for statement in remainder for node in ast.walk(statement)
                          if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names)
    following = tree.body[tree.body.index(fn) + 1:]
    later_bindings = {node.id for statement in following for node in ast.walk(statement)
                      if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))}
    later_bindings.update(alias.asname or alias.name
                         for statement in following for node in ast.walk(statement)
                         if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names)
    if bound & (arguments | local_bindings | later_bindings | {fn.name}):
        return tree, []
    metadata = [dict(revision=IMPORT_NORMALIZATION_REVISION, action="hoist_leading_import",
                     original_line=node.lineno, original_end_line=node.end_lineno,
                     import_statement=ast.unparse(node)) for node in imports]
    fn.body[start:start + len(imports)] = []
    if not fn.body:
        fn.body = [ast.copy_location(ast.Pass(), imports[-1])]
    position = tree.body.index(fn)
    tree.body[position:position] = imports
    return tree, metadata
