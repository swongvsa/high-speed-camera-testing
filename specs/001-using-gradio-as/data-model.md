# Data Model: Camera Feed Display

## Core Entities

### 1. CameraDevice
**Purpose**: Represents physical camera hardware and its capabilities

**Attributes**:
- `device_index`: int - Index in enumerated device list (0-based)
- `friendly_name`: str - Human-readable camera name
- `port_type`: str - Connection type (USB, GigE, etc.)
- `is_mono`: bool - True if monochrome, False if color
- `max_width`: int - Maximum horizontal resolution (pixels)
- `max_height`: int - Maximum vertical resolution (pixels)
- `handle`: int - SDK camera handle (opaque identifier)
- `is_initialized`: bool - Camera initialization state

**Validation Rules**:
- `device_index >= 0`
- `friendly_name` must not be empty
- `max_width > 0 and max_height > 0`
- `handle` must be set after successful initialization

**State Transitions**:
```
DISCOVERED → INITIALIZED → STREAMING → RELEASED
     ↓            ↓            ↓
   ERROR ← ← ← ← ← ← ← ← ← ← ERROR
```

**Relationships**:
- CameraDevice [1] → [N] VideoFrame (produces frames)
- CameraDevice [1] ← [1] ViewerSession (used by session)

### 2. VideoFrame
**Purpose**: Individual captured image from camera

**Attributes**:
- `data`: np.ndarray - Pixel data (H×W×C for color, H×W for mono)
- `width`: int - Frame width in pixels
- `height`: int - Frame height in pixels
- `channels`: int - 1 for mono, 3 for BGR color
- `timestamp`: float - Capture timestamp (seconds since epoch)
- `sequence_number`: int - Frame sequence ID (monotonic)
- `media_type`: int - SDK media type constant (MONO8/BGR8)

**Validation Rules**:
- `data.shape == (height, width, channels)` for color
- `data.shape == (height, width)` for mono
- `data.dtype == np.uint8`
- `channels in [1, 3]`
- `timestamp > 0`
- `sequence_number >= 0`

**Derived Properties**:
- `is_color`: bool = `channels == 3`
- `size_bytes`: int = `data.nbytes`

**Relationships**:
- VideoFrame [N] ← [1] CameraDevice (captured from)

### 3. ViewerSession
**Purpose**: Manages single active viewer connection

**Attributes**:
- `session_hash`: str - Gradio session identifier (UUID)
- `start_time`: datetime - When session started
- `is_active`: bool - Session currently active flag
- `camera`: CameraDevice | None - Associated camera (if any)

**Validation Rules**:
- `session_hash` must be unique
- Only one `ViewerSession` can have `is_active=True` at any time
- `camera` must be initialized if set

**State Transitions**:
```
PENDING → ACTIVE → TERMINATED
    ↓        ↓
  BLOCKED  RELEASED
```

**Relationships**:
- ViewerSession [1] → [0..1] CameraDevice (controls camera)

### 4. StreamState
**Purpose**: Application-level streaming control

**Attributes**:
- `is_streaming`: bool - Global streaming active flag
- `active_session_id`: str | None - Current session hash
- `frame_count`: int - Total frames streamed
- `error_count`: int - Frame capture errors
- `last_frame_time`: float - Timestamp of last successful frame

**Validation Rules**:
- `is_streaming=True` requires `active_session_id` is not None
- `frame_count >= 0`
- `error_count >= 0`

**Invariants**:
- At most one session can have streaming active
- If `is_streaming=False`, camera must be released

## Data Flow Diagram

```
[User Browser]
       ↓ (HTTP/WebSocket)
[Gradio Interface]
       ↓ (session events)
[ViewerSession] ← → [StreamState]
       ↓ (controls)
[CameraDevice]
       ↓ (captures)
[VideoFrame] → → → [Gradio Image Component]
       ↑ (displays)
[User Browser]
```

## Persistence Model

**No persistence required**:
- All entities are in-memory only
- Camera state persists in SDK driver
- Session state cleared on browser close
- No database, no file storage

**Memory Management**:
- Pre-allocate frame buffers on camera init
- Reuse same buffer for all frames (zero-copy)
- Release on camera shutdown or session end

## Error States & Recovery

### CameraDevice Errors
- **Error**: No cameras found
  - **Recovery**: Display message "No camera connected"

- **Error**: Camera init fails
  - **Recovery**: Try next camera in list, or show error

- **Error**: Frame capture timeout (>200ms)
  - **Recovery**: Skip frame, continue streaming

- **Error**: Connection lost during streaming
  - **Recovery**: Release resources, show reconnect option

### ViewerSession Errors
- **Error**: Second viewer attempts connection
  - **Recovery**: Block with message "Camera in use"

- **Error**: Session disconnect without cleanup
  - **Recovery**: Timeout-based cleanup (30s inactive)

### StreamState Errors
- **Error**: Excessive frame errors (>10 consecutive)
  - **Recovery**: Stop stream, reinitialize camera

## Thread Safety

**Concurrency Considerations**:
- `StreamState` access protected by `threading.Lock`
- `ViewerSession` creation/termination guarded by lock
- `CameraDevice` operations are thread-safe via SDK
- `VideoFrame` is immutable after creation (read-only)

**Lock Hierarchy** (to prevent deadlock):
1. Session lock (acquire first)
2. Camera lock (acquire second)
3. Never hold both simultaneously if possible

## Validation Summary

| Entity | Required Fields | Unique Constraints | State Validation |
|--------|----------------|-------------------|------------------|
| CameraDevice | device_index, friendly_name, handle | handle (per instance) | Must transition through INITIALIZED before STREAMING |
| VideoFrame | data, width, height, channels | sequence_number (per camera) | data.shape must match dimensions |
| ViewerSession | session_hash, start_time | session_hash (global) | Only one active=True globally |
| StreamState | is_streaming | N/A | is_streaming requires active_session_id |

Ready for Phase 1 contracts generation.
