"""
Entity processing and validation utilities.

Provides functions for cleaning, normalizing, and validating extracted entities.
"""

import re
from typing import Any
from collections import Counter

from src.shared.logging import LoggerMixin


class EntityProcessor(LoggerMixin):
    """
    Processor for cleaning and validating extracted entities.

    Features:
    - Name normalization and cleaning
    - Duplicate detection and merging
    - Confidence adjustment based on heuristics
    - Type validation
    - Entity filtering
    """

    # Valid entity types as defined in the prompt
    VALID_TYPES = {
        "person", "organization", "location", "project", "technology",
        "concept", "event", "document", "date", "metric"
    }

    # Minimum confidence threshold
    MIN_CONFIDENCE = 0.4

    # Common stopwords that shouldn't be standalone entities
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "through", "during",
        "before", "after", "above", "below", "between", "among", "this", "that",
        "these", "those"
    }

    def __init__(self):
        """Initialize entity processor."""
        super().__init__()

    def process_entities(
        self,
        entities: list[dict[str, Any]],
        min_confidence: float | None = None
    ) -> list[dict[str, Any]]:
        """
        Process and validate a list of entities.

        Args:
            entities: Raw entities from LLM
            min_confidence: Minimum confidence threshold (optional)

        Returns:
            Cleaned and validated entities
        """
        if not entities:
            return []

        min_conf = min_confidence or self.MIN_CONFIDENCE

        self.logger.info("processing_entities", count=len(entities), min_confidence=min_conf)

        # Step 1: Clean individual entities
        cleaned = [self._clean_entity(e) for e in entities]

        # Step 2: Filter invalid entities
        valid = [e for e in cleaned if self._is_valid_entity(e, min_conf)]

        # Step 3: Merge duplicates
        merged = self._merge_duplicates(valid)

        # Step 4: Adjust confidence scores
        adjusted = [self._adjust_confidence(e) for e in merged]

        # Step 5: Sort by confidence (descending)
        sorted_entities = sorted(adjusted, key=lambda x: x["confidence"], reverse=True)

        self.logger.info(
            "entities_processed",
            original=len(entities),
            final=len(sorted_entities),
            filtered=len(entities) - len(sorted_entities)
        )

        return sorted_entities

    def _clean_entity(self, entity: dict[str, Any]) -> dict[str, Any]:
        """
        Clean individual entity fields.

        Args:
            entity: Raw entity dict

        Returns:
            Cleaned entity dict
        """
        cleaned = entity.copy()

        # Clean name
        if "name" in cleaned:
            name = str(cleaned["name"]).strip()
            # Remove extra whitespace
            name = re.sub(r'\s+', ' ', name)
            # Capitalize properly for person names
            if cleaned.get("type") == "person":
                name = self._capitalize_name(name)
            cleaned["name"] = name

        # Clean type
        if "type" in cleaned:
            cleaned["type"] = str(cleaned["type"]).strip().lower()

        # Clean description
        if "description" in cleaned:
            desc = str(cleaned["description"]).strip()
            # Limit to 120 characters as per spec
            if len(desc) > 120:
                desc = desc[:117] + "..."
            cleaned["description"] = desc

        # Ensure confidence is float
        if "confidence" in cleaned:
            try:
                cleaned["confidence"] = float(cleaned["confidence"])
            except (ValueError, TypeError):
                cleaned["confidence"] = 0.5

        # Ensure mentions is int
        if "mentions" in cleaned:
            try:
                cleaned["mentions"] = int(cleaned["mentions"])
            except (ValueError, TypeError):
                cleaned["mentions"] = 1

        return cleaned

    def _capitalize_name(self, name: str) -> str:
        """
        Properly capitalize person names.

        Args:
            name: Person name

        Returns:
            Capitalized name
        """
        # Handle special cases like "McDonald", "O'Brien", etc.
        parts = name.split()
        capitalized = []

        for part in parts:
            if "-" in part:
                # Handle hyphenated names
                capitalized.append("-".join(w.capitalize() for w in part.split("-")))
            elif part.startswith("Mc") or part.startswith("Mac"):
                # Handle Scottish/Irish names
                capitalized.append(part[0:2] + part[2:].capitalize())
            elif "'" in part:
                # Handle O'Brien, D'Angelo, etc.
                idx = part.index("'")
                capitalized.append(part[:idx+1] + part[idx+1:].capitalize())
            else:
                capitalized.append(part.capitalize())

        return " ".join(capitalized)

    def _is_valid_entity(self, entity: dict[str, Any], min_confidence: float) -> bool:
        """
        Validate entity meets requirements.

        Args:
            entity: Entity to validate
            min_confidence: Minimum confidence threshold

        Returns:
            True if valid
        """
        # Check required fields
        if not all(k in entity for k in ["name", "type", "confidence"]):
            self.logger.debug("entity_missing_required_fields", entity=entity.get("name"))
            return False

        # Check name is not empty or just whitespace
        name = entity["name"].strip()
        if not name or len(name) < 2:
            self.logger.debug("entity_name_too_short", name=name)
            return False

        # Check name is not just a stopword
        if name.lower() in self.STOPWORDS:
            self.logger.debug("entity_is_stopword", name=name)
            return False

        # Check type is valid
        if entity["type"] not in self.VALID_TYPES:
            self.logger.debug("entity_invalid_type", name=name, type=entity["type"])
            return False

        # Check confidence threshold
        if entity["confidence"] < min_confidence:
            self.logger.debug(
                "entity_low_confidence",
                name=name,
                confidence=entity["confidence"]
            )
            return False

        return True

    def _merge_duplicates(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Merge duplicate entities based on normalized names.

        Args:
            entities: List of entities

        Returns:
            Merged entities
        """
        if not entities:
            return []

        # Group by normalized name and type
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

        for entity in entities:
            key = (self._normalize_name(entity["name"]), entity["type"])
            if key not in groups:
                groups[key] = []
            groups[key].append(entity)

        # Merge each group
        merged = []
        for group in groups.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                merged.append(self._merge_group(group))

        return merged

    def _normalize_name(self, name: str) -> str:
        """
        Normalize entity name for comparison.

        Args:
            name: Entity name

        Returns:
            Normalized name
        """
        # Convert to lowercase, remove special chars, collapse whitespace
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _merge_group(self, group: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Merge a group of duplicate entities.

        Args:
            group: List of duplicate entities

        Returns:
            Merged entity
        """
        # Use the entity with highest confidence as base
        base = max(group, key=lambda x: x["confidence"])
        merged = base.copy()

        # Sum mentions
        if "mentions" in merged:
            merged["mentions"] = sum(e.get("mentions", 1) for e in group)

        # Average confidence (weighted by mentions if available)
        if all("mentions" in e for e in group):
            total_mentions = sum(e["mentions"] for e in group)
            weighted_conf = sum(e["confidence"] * e["mentions"] for e in group)
            merged["confidence"] = weighted_conf / total_mentions
        else:
            merged["confidence"] = sum(e["confidence"] for e in group) / len(group)

        # Use longest description
        descriptions = [e.get("description", "") for e in group]
        merged["description"] = max(descriptions, key=len) if descriptions else ""

        self.logger.debug(
            "entities_merged",
            name=merged["name"],
            count=len(group),
            final_confidence=merged["confidence"]
        )

        return merged

    def _adjust_confidence(self, entity: dict[str, Any]) -> dict[str, Any]:
        """
        Adjust confidence score based on heuristics.

        Args:
            entity: Entity to adjust

        Returns:
            Entity with adjusted confidence
        """
        adjusted = entity.copy()
        confidence = adjusted["confidence"]

        # Boost confidence for entities with multiple mentions
        if entity.get("mentions", 1) > 1:
            boost = min(0.1, entity["mentions"] * 0.02)
            confidence = min(1.0, confidence + boost)

        # Reduce confidence for very short names (might be acronyms or partial)
        if len(entity["name"]) <= 3 and entity["type"] not in ["technology", "metric"]:
            confidence = confidence * 0.9

        # Boost confidence for well-structured person names (First Last)
        if entity["type"] == "person" and len(entity["name"].split()) >= 2:
            confidence = min(1.0, confidence + 0.05)

        # Reduce confidence for generic-sounding names
        generic_patterns = [
            r'^project \d+$',
            r'^meeting \d+$',
            r'^document \d+$',
            r'^version \d+\.?\d*$'
        ]
        if any(re.match(pattern, entity["name"].lower()) for pattern in generic_patterns):
            confidence = confidence * 0.8

        adjusted["confidence"] = round(confidence, 3)

        return adjusted
