import os

backend_dir = r"c:\Users\prakh\OneDrive\Desktop\Saarthi\backend"

def fix_contract_auditor():
    file_path = os.path.join(backend_dir, "app", "services", "contract_auditor.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """        db_reqs = reqs.get("database_requirements", {})
        master_entities = db_reqs.get("entities", [])
        auth_reqs = reqs.get("authentication", {})"""

    replacement = """        db_reqs = reqs.get("database_requirements", {})
        master_entities = db_reqs.get("entities", [])
        if not master_entities:
            master_entities = project_doc.get("db_architecture", {}).get("entities", [])
        auth_reqs = reqs.get("authentication", {})"""

    if target in content:
        content = content.replace(target, replacement)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed contract_auditor.py")
    else:
        print("Target not found in contract_auditor.py")


def fix_dependency_dag():
    file_path = os.path.join(backend_dir, "app", "services", "dependency_dag.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '"api_architecture":' in line and 'database_architecture' not in line:
            lines[i] = line.replace('[', '["database_architecture", ')
            print("Fixed dependency_dag.py")
            break
            
    content = '\n'.join(lines)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_api_contracts():
    file_path = os.path.join(backend_dir, "app", "services", "api_contracts.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    target = """def entity_resource_variants(entity_name: str) -> Set[str]:
    words = split_identifier(entity_name)
    singular = "-".join(words)
    plural = pluralize_resource(words)
    compact_singular = normalize_identifier(singular)
    compact_plural = normalize_identifier(plural)
    naive_plural = f"{compact_singular}s" if compact_singular else ""
    return {v for v in {singular, plural, compact_singular, compact_plural, naive_plural} if v}"""

    replacement = """def entity_resource_variants(entity_name: str) -> Set[str]:
    words = split_identifier(entity_name)
    singular = "-".join(words)
    plural = pluralize_resource(words)
    compact_singular = normalize_identifier(singular)
    compact_plural = normalize_identifier(plural)
    naive_plural = f"{compact_singular}s" if compact_singular else ""
    
    variants = {singular, plural, compact_singular, compact_plural, naive_plural}
    if words:
        last_word = words[-1]
        last_word_plural = pluralize_resource([last_word])
        variants.add(last_word)
        variants.add(last_word_plural)
        
    return {v for v in variants if v}"""

    if target in content:
        content = content.replace(target, replacement)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed api_contracts.py")
    else:
        print("Target not found in api_contracts.py")

fix_contract_auditor()
fix_dependency_dag()
fix_api_contracts()
