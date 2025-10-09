# Data Model: Remove Image Segmentation and Face Recognition Pipelines

**Feature**: Remove processing pipelines  
**Date**: 2025-10-09  
**Status**: Design

## Overview

This document describes the data model changes resulting from removing image segmentation and face recognition pipelines. The changes involve **removing** processing-related entities and **preserving** camera-focused entities.

---

## Entities Removed

### 1. Face Embeddings Database

**Previous State:**
- **Storage**: File-based pickle storage in project directory
- **Structure**: Dictionary mapping person names to face embeddings
- **Fields**:
  - `name` (str): Person's name
  - `embedding` (np.ndarray): Face feature vector (128-512 dimensions)
  - `model` (str): Model used for embedding extraction
  - `timestamp` (datetime): When enrolled

**Removal Impact:**
- ✅ No migration needed - embeddings database was local/temporary
- ✅ No persistent user data to preserve
- ⚠️ Users who enrolled faces will need to re-enroll if feature is ever re-added

**Rationale**: Face recognition feature completely removed, no need for embeddings storage.

---

### 2. Segmentation Detection Results (Transient)

**Previous State:**
- **Storage**: Transient (not persisted)
- **Structure**: YOLO detection results per frame
- **Fields**:
  - `boxes` (list): Bounding box coordinates
  - `masks` (list): Segmentation masks
  - `class_ids` (list): Detected object class IDs
  - `confidence` (list): Detection confidence scores
  - `track_ids` (list, optional): Object tracking IDs

**Removal Impact:**
- ✅ No persistent storage - purely transient data
- ✅ No migration needed

**Rationale**: Segmentation feature completely removed, detection results no longer generated.

---

### 3. Face Recognition Results (Transient)

**Previous State:**
- **Storage**: Transient (not persisted)
- **Structure**: DeepFace recognition results per frame
- **Fields**:
  - `faces` (list): Detected face locations
  - `identities` (list): Recognized person names or "Unknown"
  - `distances` (list): Recognition confidence distances
  - `embeddings` (list): Face embeddings for matching

**Removal Impact:**
- ✅ No persistent storage - purely transient data
- ✅ No migration needed

**Rationale**: Face recognition feature completely removed, recognition results no longer generated.

---

## Entities Preserved

### 1. VideoFrame

**Status**: ✅ **UNCHANGED**

**Purpose**: Represents a single camera frame with metadata

**Structure**:
```python
@dataclass(frozen=True)
class VideoFrame:
    data: np.ndarray        # Raw frame data (H×W×3 for RGB, H×W for mono)
    width: int              # Frame width in pixels
    height: int             # Frame height in pixels
    timestamp: int          # Frame timestamp (microseconds)
    frame_number: int       # Sequential frame number
```

**Contract**:
- Immutable value object (frozen dataclass)
- Validates dimensions on construction
- Represents raw camera frame without processing

**Usage**: Unchanged - continues to flow from camera → display without processing

---

### 2. CameraDevice

**Status**: ✅ **UNCHANGED**

**Purpose**: Hardware interface for camera operations

**Structure**:
```python
class CameraDevice:
    _handle: int                    # SDK camera handle
    _buffer: np.ndarray             # Frame buffer
    _capability: CameraCapability   # Camera capabilities
    
    # Methods preserved:
    def get_frame() -> VideoFrame
    def set_exposure_time(us: int) -> None
    def info() -> str
```

**Contract**:
- Context manager for resource lifecycle
- Provides raw frames via `get_frame()`
- Manages exposure settings
- No awareness of processing pipelines

**Usage**: Unchanged - camera operations independent of processing

---

### 3. ViewerSession

**Status**: ✅ **UNCHANGED**

**Purpose**: Manages single-viewer session state

**Structure**:
```python
class ViewerSession:
    _current_session: Optional[str]  # Active session hash
    _lock: threading.Lock            # Session mutex
    
    # Methods preserved:
    def try_start(session_hash: str) -> bool
    def end(session_hash: str) -> None
    def is_active(session_hash: str) -> bool
```

**Contract**:
- Enforces single viewer constraint
- Thread-safe session management
- No dependency on processing features

**Usage**: Unchanged - session management independent of processing

---

## Data Flow Changes

### Before Removal (With Processing)

```
Camera → VideoFrame → Processing Pipeline → Annotated Frame → Display
                           ↓
                    ┌──────┴──────┐
             Segmentation    Face Recognition
                  ↓                ↓
            Bounding Boxes    Identity Labels
                  ↓                ↓
            Overlay on Frame ─────┘
```

### After Removal (Simplified)

```
Camera → VideoFrame → Display
```

**Key Changes**:
- ✅ Removed processing pipeline stage
- ✅ Direct camera-to-display flow
- ✅ No intermediate annotation step
- ✅ Lower latency (no processing delay)

---

## Configuration Changes

### Previous Configuration (in app.py)

```python
current_settings = {
    # Processing settings (REMOVED)
    "enable_segmentation": False,
    "model_size": "n",
    "confidence": 0.25,
    "enable_tracking": False,
    "selected_classes": None,
    "enable_face_recognition": False,
    "face_model": "Facenet",
    "face_detector": "retinaface",
    "face_threshold": 0.6,
    
    # Camera settings (PRESERVED)
    "auto_exposure": False,
    "exposure_time_ms": 30.0,
}
```

### New Configuration (Simplified)

```python
current_settings = {
    # Camera settings only
    "auto_exposure": False,
    "exposure_time_ms": 30.0,
}
```

**Changes**:
- ❌ Removed 9 processing configuration keys
- ✅ Kept 2 camera configuration keys
- ✅ 82% reduction in configuration complexity

---

## State Management Changes

### Previous State (With Processing)

```python
# Global processors (REMOVED)
seg_processor: Optional[SegmentationProcessor] = None
face_processor: Optional[FaceRecognitionProcessor] = None
embeddings_mgr = EmbeddingsManager()

# Session state (PRESERVED)
session_manager = ViewerSession()
lifecycle = SessionLifecycle(session_manager)
```

### New State (Simplified)

```python
# Session state only (PRESERVED)
session_manager = ViewerSession()
lifecycle = SessionLifecycle(session_manager)
```

**Changes**:
- ❌ Removed processor instances
- ❌ Removed embeddings manager
- ✅ Kept session and lifecycle management

---

## Interface Changes

### Frame Generator Interface

**Before:**
```python
def frame_stream(
    request: gr.Request,
    enable_segmentation: bool = False,
    model_size: str = "n",
    confidence: float = 0.25,
    enable_tracking: bool = False,
    selected_classes: Optional[list] = None,
    enable_face_recognition: bool = False,
    face_model: str = "Facenet512",
    face_detector: str = "retinaface",
    face_threshold: float = 0.6,
) -> Iterator[tuple[np.ndarray, str]]:
```

**After:**
```python
def frame_stream(
    request: gr.Request,
) -> Iterator[tuple[np.ndarray, str]]:
```

**Changes**:
- ❌ Removed 9 processing parameters
- ✅ Simplified to request-only input
- ✅ Output remains same: (frame, debug_info)

---

## Debug Info Structure

### Before (With Processing)

```python
debug_info = f"""
📹 Camera: {camera_status}
🎯 Segmentation: {detections_found}
👤 Face Recognition: {faces_recognized}

📊 Performance:
FPS: 15.2
Segmentation: 45.3ms
Face Recognition: 67.8ms
Total processing: 113.1ms
"""
```

### After (Simplified)

```python
debug_info = f"""
📹 Camera: {camera_status}

📊 Performance:
FPS: 28.5
Frame time: 35.1ms
"""
```

**Changes**:
- ❌ Removed segmentation and face recognition sections
- ❌ Removed processing time metrics
- ✅ Kept camera status and FPS
- ✅ More concise, camera-focused output

---

## Migration Notes

### For Users

**No Action Required:**
- Camera feed will continue to work
- All camera controls (exposure) preserved
- Performance will improve automatically

**Data Loss (If Applicable):**
- ⚠️ Enrolled faces will be lost (embeddings database not migrated)
- ℹ️ No other user data affected (processing was transient)

**Recommendation**: If users need face recognition in the future, it should be implemented as a separate service/plugin, not embedded in the camera application.

### For Developers

**Code Changes Required:**
- Remove imports of `src.segmentation` and `src.face_recognition`
- Update UI tests to remove processing expectations
- Remove processing dependencies from `pyproject.toml`

**Testing Changes Required:**
- Update `test_gradio_ui_contract.py` to remove processing UI tests
- Update `test_scenario_01_success.py` to remove processing assertions
- All camera-focused tests should pass without changes

---

## Summary

**Entities Removed**: 3 (face embeddings, segmentation results, face recognition results)  
**Entities Preserved**: 3 (VideoFrame, CameraDevice, ViewerSession)  
**Data Flow**: Simplified from 3-stage to 2-stage pipeline  
**Configuration**: Reduced from 11 keys to 2 keys (82% reduction)  
**Migration Impact**: No user data migration needed (processing was transient)

This data model change represents a **simplification and streamlining** of the application, removing all processing-related state while preserving core camera functionality.
