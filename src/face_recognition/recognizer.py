"""
Face recognition engine using DeepFace.
Generates embeddings and matches faces against database.
"""

import logging
from typing import Optional

import cv2
import numpy as np
from deepface import DeepFace
from deepface.modules.verification import find_distance

# PIL is optional in some environments; import if available
try:
    from PIL import Image
except Exception:
    Image = None


from src.face_recognition.config import FaceRecognitionConfig
from src.face_recognition.embeddings_manager import EmbeddingsManager

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """
    Face recognition engine.

    Generates embeddings and matches faces against enrolled database.
    """

    def __init__(self, config: FaceRecognitionConfig, embeddings_mgr: EmbeddingsManager):
        """
        Initialize face recognizer.

        Args:
            config: Face recognition configuration
            embeddings_mgr: Embeddings database manager
        """
        self._config = config
        self._embeddings_mgr = embeddings_mgr
        self._model = None
        logger.info(f"Face recognizer initialized with {config.model_name} model")

    def generate_embedding(self, face_image: np.ndarray | str) -> np.ndarray:
        """
        Generate embedding for a face image with robust fallbacks.

        If `face_image` is a numpy array (cropped face from detector) we try to
        generate an embedding with `enforce_detection=False`. If DeepFace still
        fails to detect a face, retry after converting the array to RGB and
        forcing uint8 contiguous layout. This handles common issues from camera
        frames (BGR ordering, float arrays, or unusual memory layout).
        """

        def _call_deepface(img, enforce_flag):
            return DeepFace.represent(
                img_path=img,
                model_name=self._config.model_name,
                detector_backend=self._config.detector_backend,
                enforce_detection=enforce_flag,
                align=self._config.align_faces,
            )

        # Prepare image and enforcement flag
        img_input = face_image
        enforce_flag = self._config.enforce_detection

        if isinstance(face_image, np.ndarray):
            img = face_image
            # Convert grayscale to 3-channel
            if img.ndim == 2:
                img = np.stack([img, img, img], axis=-1)

            # If float image in 0..1, scale
            if np.issubdtype(img.dtype, np.floating):
                if img.max() <= 1.0:
                    img = (img * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    img = img.astype(np.uint8)

            # Ensure contiguous and uint8
            img = np.ascontiguousarray(img)
            if img.dtype != np.uint8:
                img = img.astype(np.uint8)

            # Attempt to convert BGR->RGB since OpenCV frames are often BGR
            try:
                # Only convert if it looks like BGR (3 channels)
                if img.shape[-1] == 3:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                else:
                    img_rgb = img
            except Exception:
                img_rgb = img

            img_input = img_rgb
            # For cropped faces, skip strict detection initially
            enforce_flag = False

        # First attempt
        try:
            embedding_objs = _call_deepface(img_input, enforce_flag)
        except Exception:
            # Don't log full trace for transient failures; retry quietly
            logger.debug("First DeepFace attempt failed, retrying with relaxed settings")
            # Retry with a safer configuration: enforce_detection=False and RGB array
            try:
                retry_img = img_input
                # Ensure numpy array and uint8 contiguous
                if isinstance(retry_img, np.ndarray):
                    retry_img = np.ascontiguousarray(retry_img)
                    if retry_img.dtype != np.uint8:
                        retry_img = retry_img.astype(np.uint8)

                    # Ensure RGB
                    try:
                        if retry_img.shape[-1] == 3:
                            retry_img = cv2.cvtColor(retry_img, cv2.COLOR_BGR2RGB)
                    except Exception:
                        pass

                embedding_objs = _call_deepface(retry_img, False)
            except Exception as second_exc:
                logger.warning(
                    "DeepFace failed on both attempts; skipping embedding for this face",
                )
                raise RuntimeError(f"Failed to generate embedding: {second_exc}") from second_exc

        # Normalize DeepFace output
        if embedding_objs is None:
            raise RuntimeError("No embedding returned by DeepFace")

        if isinstance(embedding_objs, dict):
            embedding_list = [embedding_objs]
        else:
            embedding_list = embedding_objs

        if len(embedding_list) == 0:
            raise RuntimeError("No face detected for embedding generation")

        if len(embedding_list) > 1:
            logger.warning(f"Multiple faces detected ({len(embedding_list)}), using first face")

        # Extract embedding robustly
        emb_obj = embedding_list[0]
        if isinstance(emb_obj, dict):
            emb = emb_obj.get("embedding") or emb_obj.get("represent") or emb_obj.get("vec")
        else:
            emb = None

        if emb is None:
            # Sometimes DeepFace returns list of floats directly
            try:
                emb = np.array(embedding_list[0])
            except Exception:
                raise RuntimeError("Unable to extract embedding from DeepFace result")

        embedding = np.array(emb, dtype=float)
        logger.debug(f"Generated {embedding.size}-dim embedding with {self._config.model_name}")
        return embedding

    def recognize_face(self, face_embedding: np.ndarray) -> tuple[Optional[str], float]:
        """
        Recognize a face by comparing embedding against database.

        Args:
            face_embedding: Face embedding to match

        Returns:
            Tuple of (name, distance):
                - name: Matched person's name, or None if no match
                - distance: Distance to closest match (lower = better)

        Note:
            Returns (None, 1.0) if database is empty or no match below threshold
        """
        if len(self._embeddings_mgr) == 0:
            logger.debug("Database is empty, no recognition possible")
            return None, 1.0

        # Get embeddings filtered by current model to avoid dimension mismatches
        all_embeddings = self._embeddings_mgr.get_all_embeddings(
            model_name=self._config.model_name
        )

        # Check if any compatible embeddings exist
        if len(all_embeddings) == 0:
            logger.debug(
                f"No embeddings compatible with {self._config.model_name} "
                f"(database has {len(self._embeddings_mgr)} faces from other models)"
            )
            return None, 1.0

        # Find closest match
        min_distance = float("inf")
        best_match = None

        for name, stored_embedding in all_embeddings.items():
            # Calculate distance using DeepFace's distance function
            distance = find_distance(
                alpha_embedding=face_embedding,
                beta_embedding=stored_embedding,
                distance_metric=self._config.distance_metric,
            )

            if distance < min_distance:
                min_distance = distance
                best_match = name

        # Check if below threshold
        if min_distance <= self._config.recognition_threshold:
            logger.debug(f"Recognized '{best_match}' with distance {min_distance:.3f}")
            return best_match, min_distance
        else:
            logger.debug(
                f"No match below threshold ({min_distance:.3f} > {self._config.recognition_threshold})"
            )
            return None, min_distance

    def enroll_face(self, name: str, face_image: np.ndarray | str) -> dict:
        """
        Enroll a new face in the database.

        Args:
            name: Person's name
            face_image: Face image as numpy array or file path

        Returns:
            Dictionary with enrollment info:
                - name: Person's name
                - embedding_dim: Embedding dimension
                - model: Model used
                - success: True if successful

        Raises:
            ValueError: If name is empty or face extraction fails
            RuntimeError: If embedding generation fails
        """
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        name = name.strip()

        try:
            # Generate embedding
            embedding = self.generate_embedding(face_image)

            # Store in database
            self._embeddings_mgr.add_face(
                name=name,
                embedding=embedding.tolist(),
                model_name=self._config.model_name,
                distance_metric=self._config.distance_metric,
            )

            logger.info(f"Successfully enrolled '{name}' with {len(embedding)}-dim embedding")

            return {
                "name": name,
                "embedding_dim": len(embedding),
                "model": self._config.model_name,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Enrollment failed for '{name}': {e}")
            raise

    def verify_faces(
        self, face1_embedding: np.ndarray, face2_embedding: np.ndarray
    ) -> tuple[bool, float]:
        """
        Verify if two face embeddings belong to the same person.

        Args:
            face1_embedding: First face embedding
            face2_embedding: Second face embedding

        Returns:
            Tuple of (is_same, distance):
                - is_same: True if faces match (below threshold)
                - distance: Distance between embeddings
        """
        distance = find_distance(
            alpha_embedding=face1_embedding,
            beta_embedding=face2_embedding,
            distance_metric=self._config.distance_metric,
        )

        is_same = distance <= self._config.recognition_threshold

        return is_same, distance
