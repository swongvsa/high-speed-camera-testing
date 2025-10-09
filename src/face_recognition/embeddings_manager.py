"""
Face embeddings database management.
Stores and retrieves face embeddings with associated names.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """
    Manages face embeddings database.

    Stores embeddings as JSON for portability and ease of inspection.
    Each entry contains: name, embedding (list of floats), model info.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize embeddings manager.

        Args:
            db_path: Path to database file. Defaults to ~/.face_recognition_db/embeddings.json
        """
        if db_path is None:
            db_dir = Path.home() / ".face_recognition_db"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "embeddings.json")

        self.db_path = Path(db_path)
        self.embeddings: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """Load embeddings from disk."""
        if self.db_path.exists():
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    self.embeddings = data
                    logger.info(
                        f"Loaded {len(self.embeddings)} face(s) from {self.db_path}"
                    )
            except Exception as e:
                logger.error(f"Failed to load embeddings: {e}")
                self.embeddings = {}
        else:
            logger.info(f"No existing database found at {self.db_path}")
            self.embeddings = {}

    def _save(self) -> None:
        """Save embeddings to disk."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w") as f:
                json.dump(self.embeddings, f, indent=2)
            logger.debug(f"Saved {len(self.embeddings)} face(s) to {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")
            raise

    def add_face(
        self,
        name: str,
        embedding: list[float],
        model_name: str,
        distance_metric: str,
    ) -> None:
        """
        Add or update a face in the database.

        Args:
            name: Person's name (used as unique identifier)
            embedding: Face embedding vector
            model_name: Model used to generate embedding
            distance_metric: Distance metric for this embedding

        Raises:
            ValueError: If embedding is empty or invalid
        """
        if not embedding or len(embedding) == 0:
            raise ValueError("Embedding cannot be empty")

        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        name = name.strip()

        self.embeddings[name] = {
            "name": name,
            "embedding": embedding,
            "model_name": model_name,
            "distance_metric": distance_metric,
        }

        self._save()
        logger.info(
            f"Added face '{name}' with {model_name} ({len(embedding)}-dim embedding)"
        )

    def remove_face(self, name: str) -> bool:
        """
        Remove a face from the database.

        Args:
            name: Person's name

        Returns:
            True if face was removed, False if not found
        """
        name = name.strip()
        if name in self.embeddings:
            del self.embeddings[name]
            self._save()
            logger.info(f"Removed face '{name}'")
            return True
        else:
            logger.warning(f"Face '{name}' not found in database")
            return False

    def get_embedding(self, name: str) -> Optional[np.ndarray]:
        """
        Get embedding for a specific person.

        Args:
            name: Person's name

        Returns:
            Embedding as numpy array, or None if not found
        """
        name = name.strip()
        if name in self.embeddings:
            return np.array(self.embeddings[name]["embedding"])
        return None

    def get_all_embeddings(self, model_name: Optional[str] = None) -> dict[str, np.ndarray]:
        """
        Get all embeddings in the database, optionally filtered by model.

        Args:
            model_name: If provided, only return embeddings from this model

        Returns:
            Dictionary mapping names to embedding arrays
        """
        if model_name is None:
            # Return all embeddings (backward compatible)
            return {
                name: np.array(data["embedding"])
                for name, data in self.embeddings.items()
            }
        else:
            # Filter by model name to avoid dimension mismatches
            compatible = {
                name: np.array(data["embedding"])
                for name, data in self.embeddings.items()
                if data.get("model_name") == model_name
            }

            # Log if some embeddings were filtered out
            total = len(self.embeddings)
            filtered = len(compatible)
            if filtered < total:
                logger.debug(
                    f"Filtered to {filtered}/{total} embeddings compatible with {model_name}"
                )

            return compatible

    def list_faces(self) -> list[str]:
        """
        Get list of all enrolled faces.

        Returns:
            List of names
        """
        return list(self.embeddings.keys())

    def get_face_info(self, name: str) -> Optional[dict]:
        """
        Get full information about a face.

        Args:
            name: Person's name

        Returns:
            Dictionary with name, embedding, model_name, distance_metric
        """
        name = name.strip()
        return self.embeddings.get(name)

    def clear_all(self) -> None:
        """Remove all faces from database."""
        self.embeddings = {}
        self._save()
        logger.info("Cleared all faces from database")

    def __len__(self) -> int:
        """Return number of enrolled faces."""
        return len(self.embeddings)

    def __contains__(self, name: str) -> bool:
        """Check if a name exists in database."""
        return name.strip() in self.embeddings
