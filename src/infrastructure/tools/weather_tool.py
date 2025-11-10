"""
Weather tool for getting weather information for a location.
"""

from typing import Any
import urllib.parse

from src.domain.entities.tool import BaseTool, ToolParameter
from src.infrastructure.tools.web_fetch_tool import WebFetchTool
from src.shared.logging import LoggerMixin


class WeatherTool(BaseTool, LoggerMixin):
    """
    Weather tool for getting current weather and forecasts.

    Uses weather websites directly since search engines block weather queries.
    """

    def __init__(self):
        """Initialize weather tool."""
        self.web_fetch = WebFetchTool()

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return """Get current weather and forecast for a specific location.

Use this tool when the user asks about:
- Current weather conditions
- Temperature
- Weather forecast
- Climate information for a city/location

This tool works for cities in Spain and worldwide.

Examples:
- "What's the weather in Madrid?"
- "Weather forecast for Illescas"
- "Current temperature in Barcelona"
"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="location",
                type="string",
                description="City name (e.g., 'Madrid', 'Illescas', 'Barcelona')",
                required=True,
            ),
            ToolParameter(
                name="country",
                type="string",
                description="Country name (optional, defaults to Spain)",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute weather lookup.

        Args:
            location: City name
            country: Country (optional)

        Returns:
            Weather information dictionary

        Raises:
            ValueError: If location is missing
        """
        location = kwargs.get("location")
        country = kwargs.get("country", "España")

        if not location:
            raise ValueError("Missing required parameter: location")

        # Normalize location name for URL
        location_normalized = location.lower().strip()

        self.logger.info(
            "weather_tool_executing",
            location=location,
            country=country,
        )

        try:
            # Try tiempo.com first (works well for Spain)
            url = f"https://www.tiempo.com/{location_normalized}.htm"

            self.logger.info("fetching_weather_from_url", url=url)
            result = await self.web_fetch.execute(url=url)

            if result.get("status") == "success":
                self.logger.info(
                    "weather_tool_success",
                    location=location,
                    source="tiempo.com",
                    content_length=len(result["content"]),
                )

                return {
                    "location": location,
                    "country": country,
                    "source": "tiempo.com",
                    "url": url,
                    "title": result["title"],
                    "weather_info": result["content"],
                    "status": "success",
                }

            # Fallback to eltiempo.es
            url_alt = f"https://www.eltiempo.es/{location_normalized}.html"
            self.logger.info("trying_alternative_source", url=url_alt)
            result_alt = await self.web_fetch.execute(url=url_alt)

            if result_alt.get("status") == "success":
                self.logger.info(
                    "weather_tool_success",
                    location=location,
                    source="eltiempo.es",
                    content_length=len(result_alt["content"]),
                )

                return {
                    "location": location,
                    "country": country,
                    "source": "eltiempo.es",
                    "url": url_alt,
                    "title": result_alt["title"],
                    "weather_info": result_alt["content"],
                    "status": "success",
                }

            # Both failed
            error_msg = f"Could not find weather information for {location}"
            self.logger.warning("weather_tool_no_data", location=location)

            return {
                "location": location,
                "country": country,
                "error": error_msg,
                "status": "error",
                "suggestion": "Try a different city name or check the spelling",
            }

        except Exception as e:
            error_msg = f"Failed to get weather: {str(e)}"
            self.logger.error("weather_tool_error", location=location, error=str(e))

            return {
                "location": location,
                "country": country,
                "error": error_msg,
                "status": "error",
            }
