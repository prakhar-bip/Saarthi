import asyncio
import os
import sys

# Ensure backend/app can be imported
sys.path.append("c:/Users/prakh/OneDrive/Desktop/Sarthi/backend")

from app.agents.requirement_analyzer import RequirementAnalyzerAgent
from app.agents.planner import PlannerAgent
from app.agents.db_architect import DatabaseArchitectureAgent
from app.agents.backend_architect import BackendArchitectureAgent
from app.agents.api_agent import APIAgent
from app.agents.frontend_architect import FrontendArchitectureAgent
from app.agents.uiux_architect import UIUXArchitectAgent
from app.agents.auth_architect import AuthArchitectureAgent
from app.agents.realtime_architect import RealtimeArchitectureAgent
from app.agents.state_architect import StateManagementAgent
from app.agents.devops_architect import DevOpsArchitectureAgent
from app.agents.security_architect import SecurityArchitectureAgent
from app.agents.testing_architect import TestingArchitectureAgent
from app.agents.validation_architect import ValidationArchitectureAgent
from app.agents.optimization_architect import OptimizationArchitectureAgent
from app.agents.code_generation_planner import CodeGenerationPlannerAgent
from app.agents.persistence_architect import DatabaseModelGenerationAgent
from app.agents.backend_code_generator import BackendCodeGenerationAgent
from app.agents.api_implementation_generator import APIImplementationAgent
from app.agents.frontend_code_generator import FrontendCodeGenerationAgent
from app.agents.ui_component_generator import UIComponentGenerationAgent
from app.agents.state_implementation_generator import StateImplementationAgent
from app.agents.integration_generator import IntegrationGenerationAgent
from app.agents.build_compiler import BuildCompilationAgent
from app.agents.error_correction import ErrorCorrectionAgent
from app.agents.project_export import ProjectExportAgent
from app.agents.verifier_agent import VerifierAgent

async def run_tests():
    print("Initializing Sarthi agents test runner...")
    verifier = VerifierAgent()

    # Mocks for verification
    blueprint = {
        "name": "ShopCart",
        "idea": "An e-commerce platform with products, orders, and user logins.",
        "features": [
            "User login registration",
            "Browse catalog of items",
            "Add products to cart and checkout"
        ],
        "tech_stack": "React, FastAPI, PostgreSQL database"
    }

    # 1. RequirementAnalyzer
    print("\n[1] Testing RequirementAnalyzer fallback...")
    req_output = RequirementAnalyzerAgent()._get_fallback_requirements(blueprint, "Ocean Blue")
    is_ok, msg = await verifier.verify("RequirementAnalyzerAgent", req_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 2. Planner
    print("\n[2] Testing Planner fallback...")
    planning_output = PlannerAgent()._get_fallback_planning(req_output)
    is_ok, msg = await verifier.verify("PlannerAgent", planning_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 3. DatabaseArchitecture
    print("\n[3] Testing DatabaseArchitecture fallback...")
    db_output = DatabaseArchitectureAgent()._get_fallback_db_architecture(req_output, planning_output)
    is_ok, msg = await verifier.verify("DatabaseArchitectureAgent", db_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg
    entities = [e["entity_name"] for e in db_output["entities"]]
    print("Entities:", entities)
    assert "Portfolio" not in entities, "Fintech entities should not be in the output!"

    # 4. BackendArchitecture
    print("\n[4] Testing BackendArchitecture fallback...")
    backend_output = BackendArchitectureAgent()._get_fallback_backend_architecture(req_output, planning_output, db_output)
    is_ok, msg = await verifier.verify("BackendArchitectureAgent", backend_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 5. API
    print("\n[5] Testing API fallback...")
    api_output = APIAgent()._get_fallback_api_architecture(req_output, planning_output, db_output, backend_output)
    is_ok, msg = await verifier.verify("APIAgent", api_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 6. FrontendArchitecture
    print("\n[6] Testing FrontendArchitecture fallback...")
    frontend_output = FrontendArchitectureAgent()._get_fallback_frontend_architecture(req_output, planning_output, db_output, backend_output, api_output)
    is_ok, msg = await verifier.verify("FrontendArchitectureAgent", frontend_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 7. UIUXArchitect
    print("\n[7] Testing UIUXArchitect fallback...")
    uiux_output = UIUXArchitectAgent()._get_fallback_theme_styling(req_output, planning_output, db_output, backend_output, api_output, frontend_output)
    is_ok, msg = await verifier.verify("UIUXArchitectAgent", uiux_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 8. AuthArchitecture
    print("\n[8] Testing AuthArchitecture fallback...")
    auth_output = AuthArchitectureAgent()._get_fallback_auth_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output)
    is_ok, msg = await verifier.verify("AuthArchitectureAgent", auth_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 9. RealtimeArchitecture
    print("\n[9] Testing RealtimeArchitecture fallback...")
    realtime_output = RealtimeArchitectureAgent()._get_fallback_realtime_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output)
    is_ok, msg = await verifier.verify("RealtimeArchitectureAgent", realtime_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 10. StateManagement
    print("\n[10] Testing StateManagement fallback...")
    state_output = StateManagementAgent()._get_fallback_state_management(req_output, planning_output, db_output, backend_output, api_output, frontend_output, auth_output, realtime_output)
    is_ok, msg = await verifier.verify("StateManagementAgent", state_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 11. DevOpsArchitecture
    print("\n[11] Testing DevOpsArchitecture fallback...")
    devops_output = DevOpsArchitectureAgent()._get_fallback_devops_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output, uiux_output, auth_output, realtime_output, state_output)
    is_ok, msg = await verifier.verify("DevOpsArchitectureAgent", devops_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 12. SecurityArchitecture
    print("\n[12] Testing SecurityArchitecture fallback...")
    security_output = SecurityArchitectureAgent()._get_fallback_security_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output, uiux_output, auth_output, realtime_output, state_output, devops_output)
    is_ok, msg = await verifier.verify("SecurityArchitectureAgent", security_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 13. TestingArchitecture
    print("\n[13] Testing TestingArchitecture fallback...")
    testing_output = TestingArchitectureAgent()._get_fallback_testing_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output, uiux_output, auth_output, realtime_output, state_output, devops_output, security_output)
    is_ok, msg = await verifier.verify("TestingArchitectureAgent", testing_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 14. ValidationArchitecture
    print("\n[14] Testing ValidationArchitecture fallback...")
    validation_output = ValidationArchitectureAgent()._get_fallback_validation_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output, uiux_output, auth_output, realtime_output, state_output, devops_output, security_output, testing_output)
    is_ok, msg = await verifier.verify("ValidationArchitectureAgent", validation_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 15. OptimizationArchitecture
    print("\n[15] Testing OptimizationArchitecture fallback...")
    optimization_output = OptimizationArchitectureAgent()._get_fallback_optimization_architecture(req_output, planning_output, db_output, backend_output, api_output, frontend_output, uiux_output, auth_output, realtime_output, state_output, devops_output, security_output, testing_output, validation_output)
    is_ok, msg = await verifier.verify("OptimizationArchitectureAgent", optimization_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 16. CodeGenerationPlanner
    print("\n[16] Testing CodeGenerationPlanner fallback...")
    planner_args = {
        "requirements": req_output,
        "planning": planning_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "frontend_architecture": frontend_output,
        "theme_styling": uiux_output,
        "auth_architecture": auth_output,
        "realtime_architecture": realtime_output,
        "state_management": state_output,
        "devops_architecture": devops_output,
        "security_architecture": security_output,
        "testing_architecture": testing_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output
    }
    codegen_plan = CodeGenerationPlannerAgent()._get_fallback_code_generation_plan(**planner_args)
    is_ok, msg = await verifier.verify("CodeGenerationPlannerAgent", codegen_plan)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 17. DatabaseModelGeneration
    print("\n[17] Testing DatabaseModelGeneration fallback...")
    db_model_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan
    }
    db_model_output = DatabaseModelGenerationAgent()._get_fallback_database_model_generation(**db_model_args)
    is_ok, msg = await verifier.verify("DatabaseModelGenerationAgent", db_model_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 18. BackendCodeGeneration
    print("\n[18] Testing BackendCodeGeneration fallback...")
    be_gen_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output
    }
    be_code_output = BackendCodeGenerationAgent()._get_fallback_backend_generation(**be_gen_args)
    is_ok, msg = await verifier.verify("BackendCodeGenerationAgent", be_code_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 19. APIImplementation
    print("\n[19] Testing APIImplementation fallback...")
    api_impl_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output
    }
    api_impl_output = APIImplementationAgent()._get_fallback_api_implementation(**api_impl_args)
    is_ok, msg = await verifier.verify("APIImplementationAgent", api_impl_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 20. FrontendCodeGeneration
    print("\n[20] Testing FrontendCodeGeneration fallback...")
    fe_gen_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output
    }
    fe_code_output = FrontendCodeGenerationAgent()._get_fallback_frontend_generation(**fe_gen_args)
    is_ok, msg = await verifier.verify("FrontendCodeGenerationAgent", fe_code_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 21. UIComponentGeneration
    print("\n[21] Testing UIComponentGeneration fallback...")
    ui_gen_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output,
        "frontend_code_generation": fe_code_output
    }
    ui_comp_output = UIComponentGenerationAgent()._get_fallback_ui_component_generation(**ui_gen_args)
    is_ok, msg = await verifier.verify("UIComponentGenerationAgent", ui_comp_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 22. StateImplementation
    print("\n[22] Testing StateImplementation fallback...")
    state_impl_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output,
        "frontend_code_generation": fe_code_output,
        "ui_component_generation": ui_comp_output
    }
    state_impl_output = StateImplementationAgent()._get_fallback_state_implementation(**state_impl_args)
    is_ok, msg = await verifier.verify("StateImplementationAgent", state_impl_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 23. IntegrationGeneration
    print("\n[23] Testing IntegrationGeneration fallback...")
    integ_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output,
        "frontend_code_generation": fe_code_output,
        "ui_component_generation": ui_comp_output,
        "state_implementation": state_impl_output
    }
    integ_output = IntegrationGenerationAgent()._get_fallback_integration_generation(**integ_args)
    is_ok, msg = await verifier.verify("IntegrationGenerationAgent", integ_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 24. BuildCompilation
    print("\n[24] Testing BuildCompilation fallback...")
    build_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_planner": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output,
        "frontend_code_generation": fe_code_output,
        "ui_component_generation": ui_comp_output,
        "state_implementation": state_impl_output,
        "integration_generation": integ_output
    }
    build_output = BuildCompilationAgent()._get_fallback_build_compilation(**build_args)
    is_ok, msg = await verifier.verify("BuildCompilationAgent", build_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 25. ErrorCorrection
    print("\n[25] Testing ErrorCorrection fallback...")
    error_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "auth_architecture": auth_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_plan": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output,
        "frontend_code_generation": fe_code_output,
        "ui_component_generation": ui_comp_output,
        "state_implementation": state_impl_output,
        "integration_generation": integ_output,
        "build_compilation": build_output
    }
    error_output = ErrorCorrectionAgent()._get_fallback_error_correction(**error_args)
    is_ok, msg = await verifier.verify("ErrorCorrectionAgent", error_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    # 26. ProjectExport
    print("\n[26] Testing ProjectExport fallback...")
    export_args = {
        "requirements": req_output,
        "db_architecture": db_output,
        "backend_architecture": backend_output,
        "api_architecture": api_output,
        "frontend_architecture": frontend_output,
        "auth_architecture": auth_output,
        "devops_architecture": devops_output,
        "validation_architecture": validation_output,
        "optimization_architecture": optimization_output,
        "code_generation_plan": codegen_plan,
        "database_model_generation": db_model_output,
        "backend_code_generation": be_code_output,
        "api_implementation": api_impl_output,
        "frontend_code_generation": fe_code_output,
        "ui_component_generation": ui_comp_output,
        "state_implementation": state_impl_output,
        "integration_generation": integ_output,
        "build_compilation": build_output,
        "error_correction": error_output
    }
    export_output = ProjectExportAgent()._get_fallback_project_export(**export_args)
    is_ok, msg = await verifier.verify("ProjectExportAgent", export_output)
    print("Result:", is_ok, msg)
    assert is_ok, msg

    print("\nSUCCESS: All 26 Sarthi fallback stages verified successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
