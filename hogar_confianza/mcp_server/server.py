import json

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool

_SERVICES_CATALOG = {
        "limpieza": {"name": "Limpieza", "description": "Limpieza general de casas, oficinas, alfombras, ventanas",
                       "avg_price_range": "500-2000 MXN", "typical_duration": "2-4 horas"},
        "electricidad": {"name": "Electricidad", "description": "Instalaciones, reparaciones, cortocircuitos, lámparas",
                           "avg_price_range": "300-3000 MXN", "typical_duration": "1-3 horas"},
        "plomeria": {"name": "Plomería", "description": "Tuberías, fugas, drenajes, calentadores, cisternas",
                       "avg_price_range": "400-3500 MXN", "typical_duration": "1-4 horas"},
        "pintura": {"name": "Pintura", "description": "Pintura interior/exterior, acabados, texturizados",
                      "avg_price_range": "2000-8000 MXN", "typical_duration": "1-3 días"},
        "impermeabilizacion": {"name": "Impermeabilización", "description": "Azoteas, terrazas, muros, filtraciones",
                                 "avg_price_range": "3000-10000 MXN", "typical_duration": "2-4 días"},
        "carpinteria": {"name": "Carpintería", "description": "Muebles, puertas, closets, cocinas integrales",
                          "avg_price_range": "1000-15000 MXN", "typical_duration": "1-7 días"},
        "jardineria": {"name": "Jardinería", "description": "Jardines, poda, pasto, plantas, riego",
                         "avg_price_range": "500-4000 MXN", "typical_duration": "2-6 horas"},
        "albañileria": {"name": "Albañilería", "description": "Muros, pisos, losas, block, repello",
                          "avg_price_range": "2000-12000 MXN", "typical_duration": "2-7 días"},
        "cerrajeria": {"name": "Cerrajería", "description": "Chapas, candados, puertas de seguridad",
                         "avg_price_range": "300-2000 MXN", "typical_duration": "30 min - 2 horas"},
}

_SAFETY_TIPS = {
    "check_in_out": "Solicita check-in al llegar y check-out al irse. Toma foto al momento de la llegada.",
    "trusted_contact": "Designa un contacto de confianza que reciba notificaciones del check-in/out del proveedor.",
    "escrow": "Nunca pagues por adelantado. Usa el sistema de pago en garantía (escrow) que retiene el pago 48h.",
    "documents": "Solicita identificación oficial al proveedor antes de permitir la entrada. Verifica que coincida.",
    "insurance": "Verifica que el proveedor tenga seguro de responsabilidad civil. Protege tu patrimonio.",
    "panic": "Si te sientes inseguro, usa el botón de pánico. Tu seguridad es lo primero.",
    "background": "Todos los proveedores pasan por verificación de antecedentes. Verifica en la plataforma.",
}


async def serve_mcp():
    server = Server("hogar-confianza-catalog")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_service_info",
                description="Información detallada de un servicio del hogar: precios, duración, descripción",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_type": {
                            "type": "string",
                            "description": (
                                "Servicio: limpieza, electricidad, plomeria, pintura, "
                                "impermeabilizacion, carpinteria, jardineria, albañileria, cerrajeria"
                            ),
                        }
                    },
                    "required": ["service_type"],
                },
            ),
            Tool(
                name="get_safety_tips",
                description="Obtén consejos de seguridad para contratar servicios domésticos",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Tema específico o 'all' para todos los consejos",
                        }
                    },
                    "required": ["topic"],
                },
            ),
            Tool(
                name="list_service_categories",
                description="Lista todas las categorías de servicios disponibles",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "get_service_info":
            service_type = arguments.get("service_type", "").lower()
            info = _SERVICES_CATALOG.get(service_type)
            if not info:
                msg = f"Servicio '{service_type}' no encontrado. Usa list_service_categories."
                return [TextContent(type="text", text=json.dumps({"error": msg}, ensure_ascii=False))]
            return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False, indent=2))]

        elif name == "get_safety_tips":
            topic = arguments.get("topic", "all").lower()
            if topic == "all":
                return [TextContent(type="text", text=json.dumps(_SAFETY_TIPS, ensure_ascii=False, indent=2))]
            tip = _SAFETY_TIPS.get(topic)
            if not tip:
                keys = ", ".join(_SAFETY_TIPS.keys())
                msg = f"Tema '{topic}' no encontrado. Temas: {keys}"
                return [TextContent(type="text", text=json.dumps({"error": msg}, ensure_ascii=False))]
            payload = {"topic": topic, "tip": tip}
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

        elif name == "list_service_categories":
            categories = {k: v["name"] for k, v in _SERVICES_CATALOG.items()}
            return [TextContent(type="text", text=json.dumps(categories, ensure_ascii=False, indent=2))]

        return [TextContent(type="text", text="Tool not found")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hogar-confianza-catalog",
                server_version="1.0.0",
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(serve_mcp())
