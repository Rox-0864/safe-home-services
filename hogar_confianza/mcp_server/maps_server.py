import json

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool

from hogar_confianza.tools.maps_client import GoogleMapsClient

_client = GoogleMapsClient()


async def serve_mcp():
    server = Server("hogar-confianza-maps")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="geocode_address",
                description="Convierte una dirección en coordenadas geográficas (lat, lng) y dirección formateada",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Dirección completa (ej: Av. Reforma 222, Col. Juárez, CDMX, 06600)",
                        }
                    },
                    "required": ["address"],
                },
            ),
            Tool(
                name="validate_address",
                description="Valida si una dirección existe y retorna la dirección formateada por Google Maps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Dirección a validar",
                        }
                    },
                    "required": ["address"],
                },
            ),
            Tool(
                name="calc_distance",
                description="Calcula la distancia entre dos puntos geográficos",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "origin_lat": {"type": "number", "description": "Latitud del origen"},
                        "origin_lng": {"type": "number", "description": "Longitud del origen"},
                        "dest_lat": {"type": "number", "description": "Latitud del destino"},
                        "dest_lng": {"type": "number", "description": "Longitud del destino"},
                    },
                    "required": ["origin_lat", "origin_lng", "dest_lat", "dest_lng"],
                },
            ),
            Tool(
                name="search_places",
                description="Busca lugares por nombre o dirección (autocomplete)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Texto de búsqueda (ej: Reforma 222, CDMX)",
                        }
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "geocode_address":
            address = arguments.get("address", "")
            result = _client.geocode(address)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "validate_address":
            address = arguments.get("address", "")
            result = _client.geocode(address)
            if not result.get("success"):
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            geo = result.get("result")
            if geo is None:
                payload = {"success": True, "valid": False, "formatted_address": None, "suggestions": [],
                           "mock": result.get("mock", False)}
            else:
                payload = {"success": True, "valid": True, "formatted_address": geo["formatted_address"],
                           "lat": geo["lat"], "lng": geo["lng"], "suggestions": [],
                           "mock": result.get("mock", False)}
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

        elif name == "calc_distance":
            origin = {"lat": arguments.get("origin_lat"), "lng": arguments.get("origin_lng")}
            destination = {"lat": arguments.get("dest_lat"), "lng": arguments.get("dest_lng")}
            result = _client.distance_matrix(origin, destination)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "search_places":
            query = arguments.get("query", "")
            results = _client.places_autocomplete(query)
            payload = {"success": True, "results": results}
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

        return [TextContent(type="text", text="Tool not found")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hogar-confianza-maps",
                server_version="1.0.0",
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(serve_mcp())
