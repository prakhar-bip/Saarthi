import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class RealtimeArchitectureAgent:
    """
    RealtimeArchitectureAgent for Sarthi.
    Designs WebSocket channels, event broadcasting, realtime state sync, and pub/sub messaging patterns.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "RealtimeArchitectureAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def design(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        theme_styling: Dict[str, Any],
        auth_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all previous pipeline architectures to design the realtime systems model.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
            "theme_styling": theme_styling,
            "auth_architecture": auth_architecture,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(self._get_fallback_realtime_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design realtime communication, websocket channels, event flows, pub/sub, notifications, authentication, and frontend sync contracts."
        )

        user_content = f"""
Analyze the following inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}
Theme Styling: {json.dumps(theme_styling, indent=2)}
Authentication Architecture: {json.dumps(auth_architecture, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "realtime_strategy": {{
    "communication_model": "e.g. WebSockets for bi-directional streaming, Pub/Sub events for async distribution",
    "event_architecture": "e.g. Event-driven broadcasting via Redis broker and FastAPI WebSockets",
    "scalability_strategy": "e.g. Horizontal scaling using Redis pub/sub adapter with multi-instance socket servers",
    "synchronization_strategy": "e.g. Optimistic UI state updates with back-end database synchronization confirmations"
  }},
  "websocket_architecture": {{
    "enabled": false,
    "websocket_channels": ["/ws/v1/channel_name"],
    "channel_groups": ["group_name"],
    "connection_strategy": ["e.g. Auto-reconnect with exponential backoff on client"]
  }},
  "event_driven_architecture": {{
    "event_types": ["event_name"],
    "event_sources": ["component_or_service_name"],
    "event_consumers": ["listener_component_or_service"],
    "event_flow_patterns": ["e.g. Source -> Publish to topic -> Broadcast"]
  }},
  "notification_architecture": {{
    "notification_types": ["type_name"],
    "delivery_channels": ["e.g. In-app toast notifications"],
    "priority_rules": ["rules_description"],
    "notification_workflows": ["workflow_description"]
  }},
  "frontend_realtime_sync": {{
    "live_components": ["component_name"],
    "sync_states": ["state_variable_name"],
    "realtime_ui_flows": ["flow_description"]
  }},
  "backend_realtime_systems": {{
    "event_processors": ["processor_service_name"],
    "async_services": ["service_name"],
    "background_event_handlers": ["handler_name"]
  }},
  "pubsub_architecture": {{
    "enabled": false,
    "message_brokers": ["Redis/RabbitMQ/Kafka"],
    "topic_groups": ["topic_name"],
    "subscription_patterns": ["pattern_description"]
  }},
  "websocket_authentication": {{
    "authentication_required": false,
    "auth_flow": ["step_1", "step_2"],
    "connection_security_rules": ["rule_description"]
  }},
  "distributed_scalability": {{
    "horizontal_scaling": false,
    "load_distribution_strategy": ["strategy_description"],
    "high_frequency_event_groups": ["event_group_name"]
  }},
  "realtime_workflows": [
    {{
      "workflow_name": "workflow_title",
      "event_flow": [
        "step_1",
        "step_2"
      ]
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_websocket_generation": [],
    "important_notes_for_frontend_generation": [],
    "important_notes_for_backend_generation": []
  }}
}}
"""

        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(parse_json_response(raw_response), self.agent_name, agent_inputs)
        except Exception as e:
            return enrich_agent_output(self._get_fallback_realtime_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

    def _get_fallback_realtime_architecture(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Detect requirements
        features = requirements.get("features", []) or []
        db_entities = db_architecture.get("entities", []) if db_architecture else []
        pages = frontend_architecture.get("pages", []) if frontend_architecture else []
        scale = requirements.get("scalability", {}) or {}
        
        # Check if realtime or notifications are needed
        realtime_req = scale.get("realtime_features", True)
        
        # Build logical websocket channels based on features
        websocket_channels = []
        live_components = []
        sync_states = []
        event_types = []
        
        if realtime_req or any("realtime" in f.lower() or "live" in f.lower() or "timer" in f.lower() or "breathing" in f.lower() for f in features):
            websocket_channels.append("/ws/v1/sync")
            live_components.append("RealtimeSyncWrapper")
            sync_states.append("active_sync_session")
            event_types.append("state_synced")

        # Map breathing timer features
        if any("timer" in f.lower() or "breathing" in f.lower() for f in features):
            websocket_channels.append("/ws/v1/breathing")
            live_components.append("BreathingRingContainer")
            sync_states.append("active_breathing_timer_seconds")
            event_types.append("breathing_phase_changed")
            
        # Map dashboard updates
        if any("dashboard" in f.lower() or "trends" in f.lower() for f in features):
            websocket_channels.append("/ws/v1/dashboard")
            live_components.append("MoodTrendsLineChart")
            sync_states.append("stress_score_history_list")
            event_types.append("stress_logged")

        # Default fallback channels if none added
        if not websocket_channels:
            websocket_channels.append("/ws/v1/updates")
            live_components.append("UpdatesBanner")
            sync_states.append("system_updates_count")
            event_types.append("system_alert")

        # Notification details
        notif_types = ["Milestone Achieved", "General Information Alert"]
        if any("stress" in f.lower() or "mood" in f.lower() for f in features):
            notif_types.append("High Stress Alert Warning")

        entity_names = [e.get("entity_name") for e in db_entities]
        
        return {
            "status": "success",
            "realtime_strategy": {
                "communication_model": "WebSockets for bi-directional streaming, Pub/Sub events for async distribution",
                "event_architecture": "Event-driven broadcasting via Redis broker and FastAPI WebSockets" if realtime_req else "WebSockets state connection logic",
                "scalability_strategy": "Horizontal scaling using Redis pub/sub adapter with multi-instance socket servers" if realtime_req else "Single instance state container",
                "synchronization_strategy": "Optimistic UI state updates with back-end database synchronization confirmations"
            },
            "websocket_architecture": {
                "enabled": True,
                "websocket_channels": websocket_channels,
                "channel_groups": [c.split("/")[-1] for c in websocket_channels],
                "connection_strategy": [
                    "Auto-reconnect with exponential backoff on client side",
                    "Keep-alive heartbeats sent every 30 seconds"
                ]
            },
            "event_driven_architecture": {
                "event_types": event_types,
                "event_sources": [f"{c}Widget" for c in live_components] + ["SystemWorker"],
                "event_consumers": ["React Dashboard UI", "NotificationLogger", "AnalyticsService"],
                "event_flow_patterns": ["Source -> Publish to topic -> Redis pub/sub broadcast -> Client websocket sockets"]
            },
            "notification_architecture": {
                "notification_types": notif_types,
                "delivery_channels": ["In-app toast notifications", "Local browser notifications"],
                "priority_rules": [
                    "General alerts mapped to Info priority",
                    "System warnings or critical milestones mapped to High priority"
                ],
                "notification_workflows": [
                    "Action triggers database insert -> Emit notification payload -> Dispatch websocket message -> Re-render alert badge"
                ]
            },
            "frontend_realtime_sync": {
                "live_components": live_components,
                "sync_states": sync_states,
                "realtime_ui_flows": [
                    "Re-render components in place on receiving websocket state message",
                    "Dispatch toast animation triggers on notification payload arrival"
                ]
            },
            "backend_realtime_systems": {
                "event_processors": ["FastAPI Websocket router connections manager"],
                "async_services": ["Redis background tasks listener"] if realtime_req else ["Asyncio background tasks"],
                "background_event_handlers": ["Database transaction event triggers updates propagation"]
            },
            "pubsub_architecture": {
                "enabled": realtime_req,
                "message_brokers": ["Redis"] if realtime_req else [],
                "topic_groups": [f"{c.split('/')[-1]}_updates" for c in websocket_channels],
                "subscription_patterns": ["Broadcast pattern for group channels", "Point-to-point websocket connection for private user alerts"]
            },
            "websocket_authentication": {
                "authentication_required": True,
                "auth_flow": [
                    "Retrieve query param token from websocket connection URL path",
                    "Verify signature on server using JWT verification layers",
                    "Reject handshake upgrading if signature is invalid"
                ],
                "connection_security_rules": [
                    "Enforce TLS (wss://) connections in production",
                    "Rate limit connection attempts per IP client to prevent DOS"
                ]
            },
            "distributed_scalability": {
                "horizontal_scaling": realtime_req,
                "load_distribution_strategy": ["Sticky session load balancing mapping users to same nodes"] if realtime_req else ["Standard round-robin load balancer"],
                "high_frequency_event_groups": [f"{c.split('/')[-1]}_updates" for c in websocket_channels]
            },
            "realtime_workflows": [
                {
                    "workflow_name": "Broadcast realtime state sync",
                    "event_flow": [
                        "Realtime change occurs on server or background worker.",
                        "Server publishes update payload to message broker.",
                        "Broker broadcasts event to all active websocket channel listeners.",
                        "Client UI receives state update and triggers reactive render."
                    ]
                }
            ],
            "future_generation_context": {
                "important_notes_for_websocket_generation": [
                    "Use fastapi.WebSocket class routers to manage active connections client mappings."
                ],
                "important_notes_for_frontend_generation": [
                    "Protect websocket reconnect loop with exponential backoff backoffs to avoid server overloading.",
                    "Handle tab blur/focus transitions to disconnect and reconnect sockets gracefully."
                ],
                "important_notes_for_backend_generation": [
                    "Utilize aioredis or redis-py asyncio pub/sub client for non-blocking sub listening loops."
                ]
            }
        }
