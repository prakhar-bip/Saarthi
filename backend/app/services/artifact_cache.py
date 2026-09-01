"""
Deterministic Artifact Cache for Sarthi AI pipeline.
Provides multi-tier caching (in-memory + MongoDB) keyed on:
- project_id
- agent_name
- agent_version
- input_hash
- dependency_hash
- prompt_version
- model
- configuration

Survives backtracking: unaffected artifacts retain valid cache entries.
"""
from typing import Dict, Any, Optional, List
import hashlib
import json
import time
from app.models.artifact import Artifact
from app.services.dependency_dag import DependencyDAG, AGENT_TO_ARTIFACT, ARTIFACT_TO_DB_KEY


class ArtifactCache:
    """Manages deterministic artifact caching across agent invocations."""

    # In-memory fast cache: cache_key -> dict
    _memory_cache: Dict[str, Dict[str, Any]] = {}
    _stats: Dict[str, int] = {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "invalidations": 0,
    }

    @classmethod
    def compute_cache_key(
        cls,
        project_id: str,
        agent_name: str,
        agent_version: str = "1.0.0",
        input_hash: str = "default_input",
        dependency_hash: str = "root",
        prompt_version: str = "1.0",
        model: str = "",
        configuration: str = ""
    ) -> str:
        """Calculates a deterministic sha256 cache key."""
        raw = (
            f"{project_id}:{agent_name}:{agent_version}:"
            f"{input_hash}:{dependency_hash}:{prompt_version}:"
            f"{model}:{configuration}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def compute_input_hash(cls, inputs: Any) -> str:
        """Computes deterministic hash from agent inputs."""
        serialized = json.dumps(inputs, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    @classmethod
    async def get(
        cls,
        db: Any,
        project_id: str,
        agent_name: str,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached artifact if cache hit occurs and status is valid.
        Returns None on CACHE MISS.
        """
        # 1. In-memory lookup
        if cache_key in cls._memory_cache:
            entry = cls._memory_cache[cache_key]
            if entry.get("status") == "valid" and entry.get("project_id") == project_id:
                cls._stats["hits"] += 1
                return entry.get("content")

        # 2. Database lookup
        if db is not None:
            try:
                record = await db.artifact_cache.find_one({
                    "_id": cache_key,
                    "project_id": project_id,
                    "status": "valid"
                })
                if record:
                    content = record.get("content")
                    if content:
                        cls._memory_cache[cache_key] = record
                        cls._stats["hits"] += 1
                        return content
            except Exception:
                pass

        cls._stats["misses"] += 1
        return None

    @classmethod
    async def set(
        cls,
        db: Any,
        project_id: str,
        agent_name: str,
        cache_key: str,
        content: Dict[str, Any],
        input_hash: str = "",
        dependency_hash: str = "",
        agent_version: str = "1.0.0",
        summary: str = "",
        key_decisions: Optional[list] = None,
    ) -> None:
        """Persists artifact to memory and MongoDB cache."""
        art_type = AGENT_TO_ARTIFACT.get(agent_name, agent_name.lower())
        record = {
            "_id": cache_key,
            "artifact_id": f"art-{cache_key[:12]}",
            "artifact_type": art_type,
            "project_id": project_id,
            "agent_name": agent_name,
            "agent_version": agent_version,
            "input_hash": input_hash,
            "dependency_hash": dependency_hash,
            "status": "valid",
            "created_at": time.time(),
            "content": content,
            "summary": summary,
            "key_decisions": key_decisions or [],
        }

        # Store in memory
        cls._memory_cache[cache_key] = record
        cls._stats["sets"] += 1

        # Store in MongoDB
        if db is not None:
            try:
                await db.artifact_cache.update_one(
                    {"_id": cache_key},
                    {"$set": record},
                    upsert=True
                )
            except Exception:
                pass

    @classmethod
    async def invalidate(cls, db: Any, project_id: str, agent_name: str) -> None:
        """Invalidates all cache entries for a specific agent in a project."""
        art_type = AGENT_TO_ARTIFACT.get(agent_name, agent_name.lower())
        
        # Invalidate in memory
        keys_to_del = [
            k for k, v in cls._memory_cache.items()
            if v.get("project_id") == project_id and (v.get("agent_name") == agent_name or v.get("artifact_type") == art_type)
        ]
        for k in keys_to_del:
            cls._memory_cache.pop(k, None)

        cls._stats["invalidations"] += len(keys_to_del) + 1

        # Invalidate in MongoDB
        if db is not None:
            try:
                await db.artifact_cache.update_many(
                    {
                        "project_id": project_id,
                        "$or": [{"agent_name": agent_name}, {"artifact_type": art_type}]
                    },
                    {"$set": {"status": "invalidated"}}
                )
            except Exception:
                pass

    @classmethod
    async def invalidate_downstream(
        cls,
        db: Any,
        project_id: str,
        responsible_agent: str
    ) -> List[str]:
        """
        Invalidates cache for the responsible agent and ALL topologically affected downstream agents.
        Unaffected agents retain their cache hits.
        Returns list of invalidated agent names.
        """
        affected_agents = DependencyDAG.get_affected_agents(responsible_agent)
        for ag in affected_agents:
            await cls.invalidate(db, project_id, ag)
        return affected_agents

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Returns cache telemetry stats."""
        total = cls._stats["hits"] + cls._stats["misses"]
        hit_rate = round((cls._stats["hits"] / max(1, total)) * 100, 2)
        return {
            **cls._stats,
            "total_queries": total,
            "hit_rate_percent": hit_rate,
        }

    @classmethod
    def clear_all(cls) -> None:
        """Clears in-memory cache (used for testing)."""
        cls._memory_cache.clear()
        cls._stats = {"hits": 0, "misses": 0, "sets": 0, "invalidations": 0}
