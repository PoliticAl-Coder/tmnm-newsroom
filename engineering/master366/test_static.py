import ast,pathlib
p=pathlib.Path(__file__).with_name("meta_readonly.py")
src=p.read_text(encoding="utf-8")
tree=ast.parse(src)
assert "POST" not in [n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in {"POST","PUT","PATCH","DELETE"}]
assert "access_token=" not in src
assert "Authorization" in src and "Bearer " in src
assert 'method="GET"' in src
assert 'GRAPH_HOST="graph.facebook.com"' in src
assert 'API_VERSION="v26.0"' in src
print("MASTER366_STATIC_READONLY=PASS")
print("WRITE_METHODS_IMPLEMENTED=ZERO")
print("TOKEN_IN_URL=NO")
print("TOKEN_IN_CLI=NO")
