import json
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple

DEPENDENCY_MAP = {
    "RequirementAnalyzerAgent": [],
    "PlannerAgent": ["requirements"],
    "ResearchPlanningAgent": ["requirements", "planning", "codebase"],
    "DatabaseArchitectureAgent": ["requirements", "planning"],
    "DatabaseModelGenerationAgent": ["requirements", "planning", "db_architecture"],
    "BackendArchitectureAgent": ["requirements", "planning", "db_architecture"],
    "APIAgent": ["requirements", "planning", "db_architecture", "backend_architecture"],
    "APIImplementationAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "FrontendArchitectureAgent": ["requirements", "planning", "theme_styling"],
    "UIUXArchitectAgent": ["requirements", "planning", "theme_styling"],
    "UIComponentGenerationAgent": ["requirements", "planning", "theme_styling", "frontend_architecture"],
    "StateManagementAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "frontend_architecture"],
    "StateImplementationAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "frontend_architecture", "state_management"],
    "AuthArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "RealtimeArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "DevOpsArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "SecurityArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "auth_architecture"],
    "TestingArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "frontend_architecture"],
    "ValidationArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "frontend_architecture"],
    "OptimizationArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "frontend_architecture"],
    "CodeGenerationPlannerAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "devops_architecture", "security_architecture",
        "testing_architecture", "validation_architecture", "optimization_architecture"
    ],
    "BackendCodeGenerationAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "auth_architecture", "realtime_architecture", "state_management", "code_generation_plan"
    ],
    "FrontendCodeGenerationAgent": [
        "requirements", "planning", "implementation_plan", "frontend_architecture", "theme_styling",
        "state_management", "code_generation_plan"
    ],
    "IntegrationGenerationAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation"
    ],
    "BuildCompilationAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation",
        "integration_generation"
    ],
    "ErrorCorrectionAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation",
        "integration_generation", "build_compilation"
    ],
    "ProjectExportAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation",
        "integration_generation", "build_compilation", "error_correction"
    ]
}

class GraphStore:
    """
    Manages the Dynamic Knowledge Graph for Sarthi projects.
    The graph is stored inside the MongoDB project document in the 'knowledge_graph' field:
    {
        "nodes": [{"id": str, "label": str, "properties": dict}],
        "edges": [{"source": str, "target": str, "relation": str}]
    }
    """

    @staticmethod
    def _get_or_create_graph(project_doc: Dict[str, Any]) -> Dict[str, Any]:
        kg = project_doc.get("knowledge_graph")
        if not kg or not isinstance(kg, dict):
            kg = {"nodes": [], "edges": []}
        if "nodes" not in kg:
            kg["nodes"] = []
        if "edges" not in kg:
            kg["edges"] = []
        return kg

    @staticmethod
    def _get_or_create_kb(project_doc: Dict[str, Any]) -> Dict[str, Any]:
        kb = project_doc.get("knowledge_base")
        if not kb or not isinstance(kb, dict):
            kb = {}
        for category in ("entities", "endpoints", "pages", "components", "configs"):
            if category not in kb:
                kb[category] = {}
        project_doc["knowledge_base"] = kb
        return kb

    @classmethod
    def add_node(cls, graph: Dict[str, Any], node_id: str, label: str, properties: Dict[str, Any]):
        # Remove existing node if any
        graph["nodes"] = [n for n in graph["nodes"] if n.get("id") != node_id]
        graph["nodes"].append({
            "id": node_id,
            "label": label,
            "properties": properties,
            "updated_at": datetime.utcnow().isoformat()
        })

    @classmethod
    def add_edge(cls, graph: Dict[str, Any], source: str, target: str, relation: str):
        edge_id = f"{source}_{relation}_{target}"
        # Remove existing edge if any
        graph["edges"] = [e for e in graph["edges"] if f"{e.get('source')}_{e.get('relation')}_{e.get('target')}" != edge_id]
        graph["edges"].append({
            "source": source,
            "target": target,
            "relation": relation
        })

    @classmethod
    def ingest_agent_output(cls, project_doc: Dict[str, Any], agent_name: str, output_data: Any) -> Dict[str, Any]:
        """
        Parses successful agent output and dynamically populates the project's knowledge_graph and knowledge_base.
        Returns the updated knowledge_graph dictionary.
        """
        if not isinstance(output_data, dict):
            return cls._get_or_create_graph(project_doc)

        graph = cls._get_or_create_graph(project_doc)
        kb = cls._get_or_create_kb(project_doc)

        try:
            # 1. Ingest Requirements (RequirementAnalyzerAgent)
            if agent_name == "RequirementAnalyzerAgent":
                overview = output_data.get("project_overview", {})
                cls.add_node(graph, "node_project", "Project", {
                    "name": overview.get("name", "SarthiApp"),
                    "description": overview.get("description", ""),
                    "category": project_doc.get("category", "web")
                })
                
                # Tech Stack Node
                tech_stack = output_data.get("tech_stack", {})
                cls.add_node(graph, "node_tech_stack", "TechStack", tech_stack)
                cls.add_edge(graph, "node_project", "node_tech_stack", "USES_STACK")

                # Feature Nodes
                features = output_data.get("features", [])
                for idx, feat in enumerate(features):
                    feat_id = f"feat_{idx}"
                    feat_desc = feat if isinstance(feat, str) else feat.get("description", "")
                    cls.add_node(graph, feat_id, "Feature", {"description": feat_desc})
                    cls.add_edge(graph, "node_project", feat_id, "HAS_FEATURE")
                
                kb["configs"]["requirements"] = output_data

            # 2. Ingest Database Architecture (DatabaseArchitectureAgent)
            elif agent_name == "DatabaseArchitectureAgent":
                entities = output_data.get("entities", [])
                for entity in entities:
                    if not isinstance(entity, dict):
                        continue
                    entity_name = entity.get("entity_name") or entity.get("name")
                    if not entity_name:
                        continue
                    
                    entity_id = f"entity_{entity_name.lower()}"
                    cls.add_node(graph, entity_id, "DBCollection", {
                        "name": entity_name,
                        "description": entity.get("description", "")
                    })
                    cls.add_edge(graph, "node_project", entity_id, "DEFINES_COLLECTION")

                    # Fields
                    fields = entity.get("fields", [])
                    for field in fields:
                        if not isinstance(field, dict):
                            continue
                        f_name = field.get("name")
                        if not f_name:
                            continue
                        field_id = f"field_{entity_name.lower()}_{f_name.lower()}"
                        cls.add_node(graph, field_id, "SchemaField", field)
                        cls.add_edge(graph, entity_id, field_id, "DEFINES_FIELD")
                    
                    # Store complete entity spec in KB
                    kb["entities"][entity_name] = entity

                # Relationships
                rels = output_data.get("relationships", [])
                for rel in rels:
                    if not isinstance(rel, dict):
                        continue
                    from_ent = rel.get("from_entity") or rel.get("from")
                    to_ent = rel.get("to_entity") or rel.get("to")
                    rel_type = rel.get("relationship_type") or rel.get("type", "one-to-many")
                    if from_ent and to_ent:
                        from_id = f"entity_{from_ent.lower()}"
                        to_id = f"entity_{to_ent.lower()}"
                        cls.add_edge(graph, from_id, to_id, f"REFERENCES_{rel_type.upper()}")
                
                kb["configs"]["relationships"] = rels

            # 3. Ingest API Architecture (APIAgent)
            elif agent_name == "APIAgent":
                endpoints = output_data.get("endpoints", [])
                for ep in endpoints:
                    if not isinstance(ep, dict):
                        continue
                    path = ep.get("path")
                    method = ep.get("method", "GET")
                    if not path:
                        continue
                    ep_id = f"ep_{method.lower()}_{path.replace('/', '_').strip('_')}"
                    cls.add_node(graph, ep_id, "APIEndpoint", {
                        "path": path,
                        "method": method,
                        "description": ep.get("description", ""),
                        "requires_auth": ep.get("requires_auth", False),
                        "request_body": ep.get("request_body", {}),
                        "response_payload": ep.get("response_payload", {})
                    })
                    cls.add_edge(graph, "node_project", ep_id, "EXPOSES_ROUTE")

                    # Deduce connected entities by URL parts or description
                    db_arch = project_doc.get("db_architecture", {}) or {}
                    db_entities = [e.get("entity_name", "").lower() for e in db_arch.get("entities", []) if isinstance(e, dict)]
                    for ent in db_entities:
                        if ent in path.lower() or ent in ep.get("description", "").lower():
                            cls.add_edge(graph, ep_id, f"entity_{ent}", "MAPS_TO")
                    
                    # Store complete endpoint details in KB
                    kb_key = f"{method}_{path}"
                    kb["endpoints"][kb_key] = ep
                
                kb["configs"]["api_strategy"] = output_data.get("api_strategy", {})
                kb["configs"]["global_configurations"] = output_data.get("global_configurations", {})
                kb["configs"]["security_schemes"] = output_data.get("security_schemes", {})
                kb["configs"]["error_architecture"] = output_data.get("error_architecture", {})

            # 4. Ingest Frontend Architecture (FrontendArchitectureAgent)
            elif agent_name == "FrontendArchitectureAgent":
                pages = output_data.get("pages", [])
                for page in pages:
                    if not isinstance(page, dict):
                        continue
                    p_name = page.get("page_name") or page.get("name")
                    route = page.get("route")
                    if not p_name or not route:
                        continue
                    page_id = f"page_{p_name.lower().replace(' ', '_')}"
                    cls.add_node(graph, page_id, "WebPage", {
                        "name": p_name,
                        "route": route,
                        "protected": page.get("protected", False)
                    })
                    cls.add_edge(graph, "node_project", page_id, "RENDERS_PAGE")
                    
                    # Store complete page details in KB
                    kb["pages"][p_name] = page

                components = output_data.get("components", [])
                for comp in components:
                    if not isinstance(comp, dict):
                        continue
                    c_name = comp.get("component_name") or comp.get("name")
                    if not c_name:
                        continue
                    comp_id = f"comp_{c_name.lower().replace(' ', '_')}"
                    cls.add_node(graph, comp_id, "UIComponent", {
                        "name": c_name,
                        "description": comp.get("description", ""),
                        "state_dependencies": comp.get("state_dependencies", [])
                    })
                    
                    # Connect UIComponent to WebPage
                    parent_page = comp.get("parent_page") or comp.get("page")
                    if parent_page:
                        page_id = f"page_{parent_page.lower().replace(' ', '_')}"
                        cls.add_edge(graph, page_id, comp_id, "RENDERS_COMPONENT")
                    else:
                        cls.add_edge(graph, "node_project", comp_id, "DEFINES_COMPONENT")
                    
                    # Store complete component details in KB
                    kb["components"][c_name] = comp
                
                kb["configs"]["frontend_strategy"] = output_data.get("frontend_strategy", {})

            # 5. Ingest UIUX Theme Styling (UIUXArchitectAgent)
            elif agent_name == "UIUXArchitectAgent":
                theme = output_data.get("theme_styling", {}) or output_data
                cls.add_node(graph, "node_theme", "Theme", theme)
                cls.add_edge(graph, "node_project", "node_theme", "STYLED_BY")
                
                # Store theme config in KB
                kb["configs"]["theme"] = theme
                
            else:
                # Catch-all: store output in KB configs
                kb["configs"][agent_name] = output_data

        except Exception as e:
            pass

        return graph

    @classmethod
    def get_pruned_context(cls, project_doc: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """
        Fetches relevant subgraph context for the specified agent, and reconstructs
        the legacy dictionary structure that the agent expects for backward compatibility.
        """
        graph = cls._get_or_create_graph(project_doc)
        kb = cls._get_or_create_kb(project_doc)
        
        # 1. Base Project Metadata & System Keys whitelist
        context = {}
        METADATA_WHITELIST = {
            "_id", "name", "category", "status", "generation_type", 
            "tech_stack", "active_healing_context", "initial_prompt",
            "backtrack_depth", "agent_retries", "progress", "step",
            "backtrack_history", "healing_history"
        }
        for k in METADATA_WHITELIST:
            if k in project_doc:
                context[k] = project_doc[k]

        # 2. Extract Sub-graph Nodes and Edges based on agent domain
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Subgraph extraction criteria
        req_nodes = [n for n in nodes if n.get("label") in ("Project", "TechStack", "Feature")]
        db_nodes = [n for n in nodes if n.get("label") in ("DBCollection", "SchemaField")]
        api_nodes = [n for n in nodes if n.get("label") == "APIEndpoint"]
        fe_nodes = [n for n in nodes if n.get("label") in ("WebPage", "UIComponent")]
        theme_nodes = [n for n in nodes if n.get("label") == "Theme"]

        # 3. Reconstruct legacy objects based on the target agent's required dependencies
        # Requirements
        reconstructed_reqs = {}
        project_node = next((n for n in req_nodes if n.get("label") == "Project"), None)
        if project_node:
            reconstructed_reqs["project_overview"] = {
                "name": project_node["properties"].get("name"),
                "description": project_node["properties"].get("description")
            }
        tech_node = next((n for n in req_nodes if n.get("label") == "TechStack"), None)
        if tech_node:
            reconstructed_reqs["tech_stack"] = tech_node["properties"]
        reconstructed_reqs["features"] = [n["properties"].get("description") for n in req_nodes if n.get("label") == "Feature"]
        reconstructed_reqs["database_requirements"] = [n["properties"].get("name") for n in db_nodes if n.get("label") == "DBCollection"]
        
        # Database Architecture (Pull from KB with Graph fallback)
        reconstructed_db = {"entities": [], "relationships": []}
        db_cols = [n for n in db_nodes if n.get("label") == "DBCollection"]
        for col in db_cols:
            col_name = col["properties"].get("name")
            kb_entity = kb["entities"].get(col_name)
            if kb_entity:
                reconstructed_db["entities"].append(kb_entity)
            else:
                # Graph fallback
                fields_for_col = []
                for field_node in [n for n in db_nodes if n.get("label") == "SchemaField"]:
                    field_id = field_node["id"]
                    has_edge = any(e for e in edges if e.get("source") == col["id"] and e.get("target") == field_id and e.get("relation") == "DEFINES_FIELD")
                    if has_edge:
                        fields_for_col.append(field_node["properties"])
                reconstructed_db["entities"].append({
                    "entity_name": col_name,
                    "description": col["properties"].get("description"),
                    "fields": fields_for_col
                })
            
        # Reconstruct relationships
        relationships_from_kb = kb["configs"].get("relationships")
        if relationships_from_kb:
            reconstructed_db["relationships"] = relationships_from_kb
        else:
            for edge in edges:
                if "REFERENCES_" in edge.get("relation", ""):
                    source_ent = edge["source"].replace("entity_", "")
                    target_ent = edge["target"].replace("entity_", "")
                    rel_type = edge["relation"].replace("REFERENCES_", "").lower()
                    reconstructed_db["relationships"].append({
                        "from_entity": source_ent.capitalize(),
                        "to_entity": target_ent.capitalize(),
                        "relationship_type": rel_type
                    })

        # API Architecture (Pull from KB with Graph fallback)
        reconstructed_api = {"endpoints": []}
        api_strategy_from_kb = kb["configs"].get("api_strategy")
        if api_strategy_from_kb:
            reconstructed_api["api_strategy"] = api_strategy_from_kb
            
        for ep in api_nodes:
            ep_path = ep["properties"].get("path")
            ep_method = ep["properties"].get("method")
            kb_key = f"{ep_method}_{ep_path}"
            kb_ep = kb["endpoints"].get(kb_key)
            if kb_ep:
                reconstructed_api["endpoints"].append(kb_ep)
            else:
                # Graph fallback
                reconstructed_api["endpoints"].append({
                    "path": ep_path,
                    "method": ep_method,
                    "description": ep["properties"].get("description"),
                    "requires_auth": ep["properties"].get("requires_auth"),
                    "request_body": ep["properties"].get("request_body"),
                    "response_payload": ep["properties"].get("response_payload")
                })
        
        # Inject other API components from KB
        for k in ("global_configurations", "security_schemes", "error_architecture"):
            kb_val = kb["configs"].get(k)
            if kb_val:
                reconstructed_api[k] = kb_val

        # Frontend Architecture (Pull from KB with Graph fallback)
        reconstructed_fe = {"pages": [], "components": []}
        frontend_strategy_from_kb = kb["configs"].get("frontend_strategy")
        if frontend_strategy_from_kb:
            reconstructed_fe["frontend_strategy"] = frontend_strategy_from_kb
            
        for pg in [n for n in fe_nodes if n.get("label") == "WebPage"]:
            pg_name = pg["properties"].get("name")
            kb_pg = kb["pages"].get(pg_name)
            if kb_pg:
                reconstructed_fe["pages"].append(kb_pg)
            else:
                # Graph fallback
                reconstructed_fe["pages"].append({
                    "page_name": pg_name,
                    "route": pg["properties"].get("route"),
                    "protected": pg["properties"].get("protected")
                })
        for comp in [n for n in fe_nodes if n.get("label") == "UIComponent"]:
            comp_name = comp["properties"].get("name")
            kb_comp = kb["components"].get(comp_name)
            if kb_comp:
                reconstructed_fe["components"].append(kb_comp)
            else:
                # Graph fallback
                parent_page_id = next((e["source"] for e in edges if e["target"] == comp["id"] and e["relation"] == "RENDERS_COMPONENT"), None)
                parent_page_name = ""
                if parent_page_id:
                    parent_node = next((n for n in fe_nodes if n["id"] == parent_page_id), None)
                    if parent_node:
                        parent_page_name = parent_node["properties"].get("name")
                reconstructed_fe["components"].append({
                    "component_name": comp_name,
                    "description": comp["properties"].get("description"),
                    "state_dependencies": comp["properties"].get("state_dependencies"),
                    "parent_page": parent_page_name
                })

        # Theme styling
        reconstructed_theme = kb["configs"].get("theme")
        if not reconstructed_theme:
            theme_node = next((n for n in theme_nodes), None)
            if theme_node:
                reconstructed_theme = theme_node["properties"]

        # 4. Inject reconstructed entities into the context matching legacy keys
        deps = DEPENDENCY_MAP.get(agent_name, [])

        if not deps or "requirements" in deps:
            context["requirements"] = reconstructed_reqs
        if not deps or "db_architecture" in deps:
            context["db_architecture"] = reconstructed_db
        if not deps or "backend_architecture" in deps:
            context["backend_architecture"] = project_doc.get("backend_architecture", {})
        if not deps or "api_architecture" in deps:
            context["api_architecture"] = reconstructed_api
        if not deps or "frontend_architecture" in deps:
            context["frontend_architecture"] = reconstructed_fe
        if not deps or "theme_styling" in deps:
            context["theme_styling"] = reconstructed_theme
        if not deps or "auth_architecture" in deps:
            context["auth_architecture"] = project_doc.get("auth_architecture", {})
        if not deps or "realtime_architecture" in deps:
            context["realtime_architecture"] = project_doc.get("realtime_architecture", {})
        if not deps or "devops_architecture" in deps:
            context["devops_architecture"] = project_doc.get("devops_architecture", {})
        if not deps or "security_architecture" in deps:
            context["security_architecture"] = project_doc.get("security_architecture", {})
        if not deps or "testing_architecture" in deps:
            context["testing_architecture"] = project_doc.get("testing_architecture", {})
        if not deps or "validation_architecture" in deps:
            context["validation_architecture"] = project_doc.get("validation_architecture", {})
        if not deps or "optimization_architecture" in deps:
            context["optimization_architecture"] = project_doc.get("optimization_architecture", {})
        if not deps or "implementation_plan" in deps:
            context["implementation_plan"] = project_doc.get("implementation_plan", {})
        if not deps or "code_generation_plan" in deps:
            context["code_generation_plan"] = project_doc.get("code_generation_plan", {})
        if not deps or "database_model_generation" in deps:
            context["database_model_generation"] = project_doc.get("database_model_generation", {})
        if not deps or "backend_code_generation" in deps:
            context["backend_code_generation"] = project_doc.get("backend_code_generation", {})
        if not deps or "api_implementation" in deps:
            context["api_implementation"] = project_doc.get("api_implementation", {})
        if not deps or "frontend_code_generation" in deps:
            context["frontend_code_generation"] = project_doc.get("frontend_code_generation", {})
        if not deps or "ui_component_generation" in deps:
            context["ui_component_generation"] = project_doc.get("ui_component_generation", {})
        if not deps or "state_implementation" in deps:
            context["state_implementation"] = project_doc.get("state_implementation", {})
        if not deps or "integration_generation" in deps:
            context["integration_generation"] = project_doc.get("integration_generation", {})
        if not deps or "build_compilation" in deps:
            context["build_compilation"] = project_doc.get("build_compilation", {})
        if not deps or "error_correction" in deps:
            context["error_correction"] = project_doc.get("error_correction", {})
        if not deps or "project_export" in deps:
            context["project_export"] = project_doc.get("project_export", {})
        if not deps or "codebase" in deps:
            context["codebase"] = project_doc.get("codebase", [])

        # Inject the active knowledge graph itself so graph-aware models can check relationships
        context["knowledge_graph"] = {
            "nodes": [n for n in nodes if n.get("label") in ("Project", "TechStack", "Feature", "DBCollection", "APIEndpoint", "WebPage", "UIComponent", "Theme")],
            "edges": edges
        }

        # Print/Log exact required fields for [GraphContextBuilder]
        pass

        return context
