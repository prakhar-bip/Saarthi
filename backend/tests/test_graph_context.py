import sys
import os
import json
from datetime import datetime

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.graph_store import GraphStore

def run_test():
    print("🧪 Running Sarthi Knowledge Graph Context Manager Unit Tests...")
    
    # 1. Initialize Mock Project Document
    project_doc = {
        "_id": "mock_project_123",
        "name": "TestECommerceApp",
        "category": "web",
        "generation_type": "full_stack"
    }

    # 2. Test Ingesting RequirementAnalyzerAgent Output
    req_output = {
        "project_overview": {
            "name": "TestECommerceApp",
            "description": "A high-performance online marketplace."
        },
        "tech_stack": {
            "backend": "fastapi",
            "frontend": "nextjs",
            "database": "mongodb"
        },
        "features": [
            "User registration and role-based login",
            "Product catalog browsing and searching",
            "Shopping cart operations",
            "Checkout and payment gateway integration"
        ]
    }
    
    graph = GraphStore.ingest_agent_output(project_doc, "RequirementAnalyzerAgent", req_output)
    project_doc["knowledge_graph"] = graph
    
    print("\n✅ Requirement Ingestion Complete:")
    print(f"   Nodes count: {len(graph['nodes'])}")
    print(f"   Edges count: {len(graph['edges'])}")
    
    # Verify nodes exist
    project_node = next((n for n in graph["nodes"] if n["label"] == "Project"), None)
    assert project_node is not None, "Project node not created!"
    assert project_node["properties"]["name"] == "TestECommerceApp"
    
    tech_node = next((n for n in graph["nodes"] if n["label"] == "TechStack"), None)
    assert tech_node is not None, "TechStack node not created!"
    assert tech_node["properties"]["backend"] == "fastapi"

    feature_nodes = [n for n in graph["nodes"] if n["label"] == "Feature"]
    assert len(feature_nodes) == 4, f"Expected 4 Feature nodes, got {len(feature_nodes)}"

    # 3. Test Ingesting DatabaseArchitectureAgent Output
    db_output = {
        "entities": [
            {
                "entity_name": "User",
                "description": "Application user",
                "fields": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "email", "type": "string", "required": True},
                    {"name": "password_hash", "type": "string", "required": True}
                ]
            },
            {
                "entity_name": "Product",
                "description": "Catalog item",
                "fields": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "price", "type": "float", "required": True}
                ]
            },
            {
                "entity_name": "Order",
                "description": "Customer purchase order",
                "fields": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "user_id", "type": "string", "required": True},
                    {"name": "total", "type": "float", "required": True}
                ]
            }
        ],
        "relationships": [
            {
                "from_entity": "User",
                "to_entity": "Order",
                "relationship_type": "one-to-many"
            }
        ]
    }
    
    graph = GraphStore.ingest_agent_output(project_doc, "DatabaseArchitectureAgent", db_output)
    project_doc["knowledge_graph"] = graph
    project_doc["db_architecture"] = db_output # Keep original for backup
    
    print("\n✅ Database Architecture Ingestion Complete:")
    print(f"   Nodes count: {len(graph['nodes'])}")
    print(f"   Edges count: {len(graph['edges'])}")
    
    db_nodes = [n for n in graph["nodes"] if n["label"] == "DBCollection"]
    assert len(db_nodes) == 3, f"Expected 3 DBCollection nodes, got {len(db_nodes)}"
    
    field_nodes = [n for n in graph["nodes"] if n["label"] == "SchemaField"]
    assert len(field_nodes) == 9, f"Expected 9 SchemaField nodes, got {len(field_nodes)}"
    
    # Check relationships
    ref_edge = next((e for e in graph["edges"] if "REFERENCES" in e["relation"]), None)
    assert ref_edge is not None, "Reference edge between collections was not created!"
    assert ref_edge["source"] == "entity_user"
    assert ref_edge["target"] == "entity_order"

    # 4. Test Ingesting APIAgent Output
    api_output = {
        "endpoints": [
            {
                "path": "/api/users/register",
                "method": "POST",
                "description": "Register a new User",
                "requires_auth": False
            },
            {
                "path": "/api/products",
                "method": "GET",
                "description": "Get all Products",
                "requires_auth": False
            },
            {
                "path": "/api/orders",
                "method": "POST",
                "description": "Create a purchase Order",
                "requires_auth": True
            }
        ]
    }
    
    graph = GraphStore.ingest_agent_output(project_doc, "APIAgent", api_output)
    project_doc["knowledge_graph"] = graph
    project_doc["api_architecture"] = api_output
    
    print("\n✅ API Endpoints Ingestion Complete:")
    print(f"   Nodes count: {len(graph['nodes'])}")
    print(f"   Edges count: {len(graph['edges'])}")
    
    api_nodes = [n for n in graph["nodes"] if n["label"] == "APIEndpoint"]
    assert len(api_nodes) == 3, f"Expected 3 APIEndpoint nodes, got {len(api_nodes)}"
    
    # Check automatically deduced endpoint -> entity MAPS_TO edge
    maps_edge = next((e for e in graph["edges"] if e["relation"] == "MAPS_TO" and e["source"] == "ep_post_api_users_register"), None)
    assert maps_edge is not None, "Deduced edge between User endpoint and collection node is missing!"
    assert maps_edge["target"] == "entity_user"

    # 5. Test Ingesting FrontendArchitectureAgent Output
    fe_output = {
        "pages": [
            {"page_name": "Dashboard", "route": "/dashboard", "protected": True},
            {"page_name": "Login", "route": "/login", "protected": False}
        ],
        "components": [
            {"component_name": "ProductGrid", "description": "Displays lists of products", "parent_page": "Dashboard"}
        ]
    }
    
    graph = GraphStore.ingest_agent_output(project_doc, "FrontendArchitectureAgent", fe_output)
    project_doc["knowledge_graph"] = graph
    
    print("\n✅ Frontend Ingestion Complete:")
    print(f"   Nodes count: {len(graph['nodes'])}")
    print(f"   Edges count: {len(graph['edges'])}")
    
    page_nodes = [n for n in graph["nodes"] if n["label"] == "WebPage"]
    assert len(page_nodes) == 2, f"Expected 2 WebPage nodes, got {len(page_nodes)}"
    
    comp_nodes = [n for n in graph["nodes"] if n["label"] == "UIComponent"]
    assert len(comp_nodes) == 1, f"Expected 1 UIComponent node, got {len(comp_nodes)}"
    
    # Check renders component edge
    render_edge = next((e for e in graph["edges"] if e["relation"] == "RENDERS_COMPONENT"), None)
    assert render_edge is not None, "RENDERS_COMPONENT edge is missing!"
    assert render_edge["source"] == "page_dashboard"
    assert render_edge["target"] == "comp_productgrid"

    # 6. Test Neighborhood Context Extraction & Reconstruct
    print("\n⚡ Testing get_pruned_context Reconstruction...")
    
    # database model agent should get DB schema
    db_agent_context = GraphStore.get_pruned_context(project_doc, "DatabaseModelGenerationAgent")
    assert "db_architecture" in db_agent_context, "Reconstructed db_architecture missing!"
    re_db = db_agent_context["db_architecture"]
    assert len(re_db["entities"]) == 3, f"Expected 3 reconstructed entities, got {len(re_db['entities'])}"
    user_entity = next((e for e in re_db["entities"] if e["entity_name"] == "User"), None)
    assert user_entity is not None, "Reconstructed User entity is missing!"
    assert len(user_entity["fields"]) == 3, f"Expected 3 fields for User entity, got {len(user_entity['fields'])}"
    assert len(re_db["relationships"]) == 1, "Reconstructed relationships missing!"
    
    # frontend code gen agent should get frontend structures
    fe_agent_context = GraphStore.get_pruned_context(project_doc, "FrontendCodeGenerationAgent")
    assert "frontend_architecture" in fe_agent_context, "Reconstructed frontend_architecture missing!"
    re_fe = fe_agent_context["frontend_architecture"]
    assert len(re_fe["pages"]) == 2, "Reconstructed pages missing!"
    assert len(re_fe["components"]) == 1, "Reconstructed components missing!"
    product_grid = re_fe["components"][0]
    assert product_grid["parent_page"] == "Dashboard", "Parent page link broken on reconstruction!"

    # 7. Verify KB structure
    print("\n⚡ Checking Knowledge Base structure in project doc...")
    kb = project_doc.get("knowledge_base", {})
    assert "entities" in kb, "KB entities missing!"
    assert "User" in kb["entities"], "User entity missing from KB!"
    assert "endpoints" in kb, "KB endpoints missing!"
    assert "POST_/api/users/register" in kb["endpoints"], "Signup route missing from KB!"
    assert "pages" in kb, "KB pages missing!"
    assert "Dashboard" in kb["pages"], "Dashboard page missing from KB!"
    assert "components" in kb, "KB components missing!"
    assert "ProductGrid" in kb["components"], "ProductGrid component missing from KB!"
    print("✅ Knowledge Base entries verified!")

    print("\n🔥 All tests passed successfully! Knowledge Graph Context Manager works perfectly.")

if __name__ == "__main__":
    run_test()
