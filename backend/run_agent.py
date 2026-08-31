#!/usr/bin/env python
"""
Saarthi Single-Agent CLI Runner.
Enables running and testing any single agent directly on a loaded project document
complete with context optimization, verification, and database persistence.
"""

import sys
import os
import asyncio
import argparse
from typing import Optional, List, Dict, Any

# Add backend directory to path to ensure app imports resolve correctly
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.services.workflow import run_single_agent, get_agent_db_key, finalize_project_delivery
from app.services.backtrack import BacktrackManager


async def run_cli():
    parser = argparse.ArgumentParser(
        description="Saarthi Single-Agent CLI Runner. Executes individual agents on an existing project document."
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="The ID of the target project in MongoDB."
    )
    parser.add_argument(
        "--agent",
        help="The PascalCase name of the agent to execute (e.g. DatabaseArchitectureAgent)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="If set, unsets/clears the database keys for this agent prior to execution to bypass idempotency."
    )
    parser.add_argument(
        "--assemble",
        action="store_true",
        help="If set, runs the codebase assembler (finalize_project_delivery) after the agent execution."
    )

    args = parser.parse_args()

    # Validate that either --agent or --assemble is specified
    if not args.agent and not args.assemble:
        parser.error("At least one of --agent or --assemble must be specified.")

    print("Initializing Sarthi CLI DB Connection...")
    await connect_to_mongo()
    db = get_database()

    try:
        project_id = args.project_id
        project_doc = await db.projects.find_one({"_id": project_id})
        
        if not project_doc:
            print(f"Project with ID '{project_id}' not found in database.")
            sys.exit(1)

        print(f"Loaded project '{project_doc.get('name')}' (ID: {project_id}).")

        # 1. Run agent if requested
        if args.agent:
            agent_name = args.agent
            
            # Check if agent is valid by trying to get its DB key
            try:
                db_key = get_agent_db_key(agent_name)
            except KeyError:
                valid_agents = list(BacktrackManager.AGENT_DB_KEYS.keys())
                print(
                    f"Unknown agent name: '{agent_name}'.\n"
                    f"Valid agents: {', '.join(valid_agents)}"
                )
                sys.exit(1)

            # If force-rerun is requested, clear the target agent's database keys
            if args.force:
                keys_to_clear = BacktrackManager.AGENT_DB_KEYS.get(agent_name, [db_key])
                unset_query = {key: "" for key in keys_to_clear}
                
                # Also unset synthesized_codebase / codebase / validation_logs / active_healing_context 
                # since we're force running this agent, downstream and compilation must be re-run later
                unset_query["synthesized_codebase"] = ""
                unset_query["codebase"] = ""
                unset_query["validation_logs"] = ""
                unset_query["active_healing_context"] = ""

                print(f"Force-run requested. Unsetting DB keys for {agent_name}: {list(unset_query.keys())}")
                await db.projects.update_one({"_id": project_id}, {"$unset": unset_query})
                
                # Reload clean project doc
                project_doc = await db.projects.find_one({"_id": project_id})

            print(f"Triggering execution of agent: {agent_name}")
            result = await run_single_agent(db, project_id, project_doc, agent_name)
            
            if result is None:
                print(f"Agent '{agent_name}' did not produce a new result (it might have been skipped or cached).")
            else:
                print(f"Agent '{agent_name}' successfully executed and persisted results to DB.")

        # 2. Run codebase assembly if requested
        if args.assemble:
            print("Triggering assembly of the complete connected codebase...")
            # Reload fresh project document
            project_doc = await db.projects.find_one({"_id": project_id})
            updated_doc = await finalize_project_delivery(db, project_id, project_doc)
            
            quality_report = updated_doc.get("quality_report", {})
            status = updated_doc.get("status")
            
            print(f"Codebase assembly complete! Status: {status}")
            if quality_report:
                print(f"Assembly Quality Report Status: {quality_report.get('status', 'N/A')}")
                errors = quality_report.get("errors", [])
                if errors:
                    print(f"Assembly Validation completed with {len(errors)} errors:")
                    for idx, err in enumerate(errors):
                        print(f"  {idx + 1}. [{err.get('module', 'general')}] {err.get('error')}")

    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}")
        sys.exit(1)
    finally:
        await close_mongo_connection()
        print("CLI DB connection closed.")


def main():
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
