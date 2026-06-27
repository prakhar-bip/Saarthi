import json
import random
from loguru import logger
from typing import Dict, Any, List
from app.services.llm_router import get_llm_completion
from app.agents.context import parse_json_response

class DynamicCustomizationAgent:
    """
    DynamicCustomizationAgent applies styling changes, branding names, and unique student ID headers
    to codebase files dynamically before project export. This prevents plagiarism checks and makes 
    the project unique for every student.
    """
    def __init__(self):
        self.agent_name = "DynamicCustomizationAgent"

    async def customize_codebase(
        self,
        codebase: List[Dict[str, Any]],
        project_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        logger.info("[CustomizationAgent] Initializing dynamic customization pass...")
        
        # 1. Generate or extract dynamic brand name
        reqs = project_doc.get("requirements", {}) or {}
        idea = reqs.get("idea", "") or project_doc.get("name", "PlacementProject")
        
        # Call LLM to suggest branding attributes and colors
        system_prompt = (
            "You are a Creative Brand Architect in Sarthi.\n"
            "Your job is to generate a unique branding concept and color palette for a project "
            "so that it looks completely custom-designed. Your response must be in valid JSON format."
        )
        
        user_prompt = (
            f"Generate a custom brand concept for a project with this description:\n{idea}\n\n"
            "Provide:\n"
            "1. A unique brand name (e.g., instead of E-Shop use 'ZenCart' or 'SwiftBuy')\n"
            "2. A primary color hex code (harmonious, modern HSL or hex, e.g. '#3b82f6')\n"
            "3. A secondary color hex code\n"
            "4. A unique tagline\n\n"
            "Format your output EXACTLY as this JSON structure:\n"
            "{\n"
            '  "brand_name": "ZenCart",\n'
            '  "primary_color": "#4f46e5",\n'
            '  "secondary_color": "#10b981",\n'
            '  "tagline": "Seamless Commerce for Modern Teams"\n'
            "}"
        )
        
        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            brand_info = parse_json_response(raw_response)
        except Exception as e:
            logger.error(f"[CustomizationAgent] LLM failed: {e}. Using fallback defaults.")
            brand_info = {
                "brand_name": "SaarthiProject_" + str(random.randint(100, 999)),
                "primary_color": "#3b82f6",
                "secondary_color": "#10b981",
                "tagline": "Enterprise Grade Solution"
            }

        brand_name = brand_info.get("brand_name", "SaarthiProject")
        primary_color = brand_info.get("primary_color", "#3b82f6")
        secondary_color = brand_info.get("secondary_color", "#10b981")
        tagline = brand_info.get("tagline", "Placement Verification App")
        
        # Create a unique Student Verification ID for anti-plagiarism headers
        random_id = f"PL-2026-{random.randint(1000, 9999)}-{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
        
        logger.info(f"[CustomizationAgent] Selected Brand Name: {brand_name}, Student Code: {random_id}")
        
        customized_codebase = []
        for file in codebase:
            path = file.get("path", "")
            content = file.get("content", "")
            if not path or not content:
                customized_codebase.append(file)
                continue
                
            # Copy file records
            new_file = dict(file)
            
            # 2. Add verification header comments based on file type
            header = ""
            if path.endswith((".py", ".sh", ".ps1", "Dockerfile", "docker-compose.yml", ".yml", ".yaml")):
                header = (
                    f"# =========================================================================\n"
                    f"# Student ID: {random_id}\n"
                    f"# Project Brand: {brand_name} - {tagline}\n"
                    f"# Generated on: 2026-06-27\n"
                    f"# =========================================================================\n\n"
                )
            elif path.endswith((".js", ".jsx", ".ts", ".tsx", ".css")):
                header = (
                    f"/**\n"
                    f" * Student ID: {random_id}\n"
                    f" * Project Brand: {brand_name} - {tagline}\n"
                    f" * Generated on: 2026-06-27\n"
                    f" */\n\n"
                )
            elif path.endswith(".java"):
                header = (
                    f"/**\n"
                    f" * Student Verification ID: {random_id}\n"
                    f" * Module: {brand_name}\n"
                    f" */\n\n"
                )
            
            if header:
                # Add header only if not already present
                if "Student ID" not in content and "Student Verification ID" not in content:
                    content = header + content
            
            # 3. Apply branding name substitutions
            content = content.replace("Saarthi Project", brand_name)
            content = content.replace("Sarthi Project", brand_name)
            content = content.replace("Saarthi App", brand_name)
            content = content.replace("Sarthi App", brand_name)
            
            # 4. Modify styling configurations (e.g. Tailwind or CSS variables)
            if "tailwind.config" in path:
                # Dynamically substitute colors
                content = content.replace("#4f46e5", primary_color)  # Default indigo-600
                content = content.replace("#10b981", secondary_color) # Default emerald-500
            elif path.endswith("globals.css") or path.endswith("index.css"):
                # Sub styling variables in CSS
                content = content.replace("--primary: 221.2 83.2% 53.3%", f"--primary: {primary_color}")
                content = content.replace("--secondary: 210 40% 96.1%", f"--secondary: {secondary_color}")
                
            new_file["content"] = content
            customized_codebase.append(new_file)
            
        logger.info("[CustomizationAgent] Dynamic customization pass completed.")
        return customized_codebase
