================================================================================
COMPREHENSIVE TESTING GUIDE & VERIFICATION CHECKLIST
================================================================================

APPLICATION: Industrial Video Extensometer
HARDWARE: FLIR Blackfly S BFS-PGE-120S6C
ISSUE FIXED: Readonly NumPy array from PySpin causing cv2.circle()/cv2.line() crash

================================================================================
PRE-FLIGHT CHECKLIST
================================================================================

ENVIRONMENT:
    [✓] Python 3.11 installed
    [✓] PySpin SDK installed (Teledyne FLIR Spinnaker)
    [✓] OpenCV 4.13.0+ installed (pip install opencv-python)
    [✓] PyQt5 installed (pip install PyQt5)
    [✓] NumPy installed (pip install numpy)
    [✓] FLIR Blackfly S camera connected via USB 3.0+

DLL PATHS:
    [✓] C:\Program Files\Teledyne\Spinnaker\bin64 exists
        OR
    [✓] C:\Program Files\Point Grey Research\Spinnaker\bin64 exists

PROJECT STRUCTURE:
    [✓] main.py exists
    [✓] camera.py exists with .copy() fix
    [✓] tracking.py exists (updated)
    [✓] ui/main_window.py exists (rewritten)
    [✓] ui/marker_selection.py exists (rewritten)
    [✓] ui/__init__.py exists (or created empty)

================================================================================
STARTUP SEQUENCE TEST
================================================================================

TEST 1: Application Startup
────────────────────────────────────────────────────────────────────────────

COMMAND:
    python main.py

EXPECTED OUTPUT (console):
    [CAMERA] Stream mode: NewestOnly (live video)
    [CAMERA] Acquisition started
    (PyQt5 window appears with live video feed)

VISUAL CHECK:
    ✓ Window titled "Video Extensometer - FLIR Blackfly S"
    ✓ Video display shows live camera feed (should not freeze)
    ✓ No error dialogs
    ✓ Frame updates smoothly (~30 FPS)

FAILURE MODES:
    ✗ "No FLIR camera detected" → Check USB connection
    ✗ Window doesn't appear → Check PyQt5 installation
    ✗ Frozen video → Check camera settings
    ✗ Console errors → Check DLL paths


TEST 2: Button States
────────────────────────────────────────────────────────────────────────────

INITIAL STATE:
    [✓] "Capture & Select Markers" button: ENABLED
    [✓] "Start Tracking" button: DISABLED (grayed out)
    [✓] "Stop Tracking" button: DISABLED (grayed out)
    [✓] Gauge length input: EMPTY, ENABLED

PURPOSE:
    Ensures state machine prevents invalid operations


================================================================================
MARKER SELECTION TEST
================================================================================

TEST 3: Capture and Freeze Frame
────────────────────────────────────────────────────────────────────────────

ACTION:
    Click "Capture & Select Markers" button

EXPECTED:
    1. Video in main window FREEZES (stops updating)
    2. New window titled "Select Markers" opens
    3. Window shows frozen image (should be 40% of original size)
    4. Console shows:
       [MARKER SELECTION] Click 2 points on the image
       [MARKER SELECTION] Press 'q' or close window to confirm

FAILURE MODES:
    ✗ "Failed to capture frame" dialog → Camera connection issue
    ✗ Selector window doesn't open → Check OpenCV/cv2.namedWindow()
    ✗ Image doesn't appear → Check frame.copy() is writable


TEST 4: First Marker Selection
────────────────────────────────────────────────────────────────────────────

ACTION:
    Click on first marker location in the image

EXPECTED:
    1. Green filled circle (radius 20px) appears where clicked
    2. Label "M1" appears near circle
    3. Text at top left: "Points: 1/2"
    4. Console shows:
       [MARKER 1] Selected at (X, Y)

FAILURE MODES:
    ✗ Circle doesn't appear → Check temp.copy() is writable
    ✗ No coordinates printed → Mouse callback not triggered
    ✗ Multiple circles appear → Mouse callback called repeatedly


TEST 5: Second Marker Selection
────────────────────────────────────────────────────────────────────────────

ACTION:
    Click on second marker location

EXPECTED:
    1. Second green circle appears at new location
    2. Label "M2" appears near second circle
    3. Blue line connects both circles (gauge line)
    4. Yellow text between circles: "XXXX.Xpx" (pixel distance)
    5. Text at top left: "Points: 2/2"
    6. Selector window CLOSES automatically
    7. Main window reappears with video unfrozen
    8. Success dialog shows:
       "2 markers selected"
       "Initial distance: XXXX.XX px"
    9. Console shows:
       [MARKER 2] Selected at (X, Y)
       EXITING SELECTOR
       [MARKER SELECTION] {2 markers selected}
       [MARKER POSITIONS] [(X1, Y1), (X2, Y2)]
       [INITIAL DISTANCE] XXXX.XX pixels

FAILURE MODES:
    ✗ Line doesn't appear → Check cv2.line() with writable frame
    ✗ Distance not calculated → Check pixel distance formula
    ✗ Window doesn't close → Check auto-confirm logic
    ✗ Points not scaled → Check scaling factor (1/0.4)


TEST 6: Marker Display (Pre-Tracking)
────────────────────────────────────────────────────────────────────────────

EXPECTED (back in main window):
    1. Video resumes playing
    2. Two RED outline circles (not filled) visible on video
    3. Blue line connecting the circles
    4. Text "Ready" appears near first marker
    5. Status shows: "Strain: 0.000000 | Status: Idle"
    6. Button states changed:
       - "Capture & Select Markers": Still ENABLED
       - "Start Tracking": Now ENABLED
       - "Stop Tracking": Still DISABLED

PURPOSE:
    Shows markers in "ready" state before tracking starts


================================================================================
GAUGE LENGTH INPUT TEST
================================================================================

TEST 7: Valid Gauge Length Input
────────────────────────────────────────────────────────────────────────────

ACTION:
    1. In "Gauge Length (mm)" field, enter "50"
    2. Click "Start Tracking" button

EXPECTED:
    1. No error dialog
    2. Button states change:
       - "Capture & Select Markers": DISABLED
       - "Start Tracking": DISABLED
       - "Stop Tracking": ENABLED
    3. Markers change to GREEN FILLED circles
    4. Console shows:
       [TRACKING START] Calibration: X.XXXXXX mm/px

PURPOSE:
    Validates gauge length and calibration calculation


TEST 8: Invalid Gauge Length Inputs
────────────────────────────────────────────────────────────────────────────

TEST 8A: Non-numeric input
    ACTION: Enter "abc" in gauge length, click Start
    EXPECTED: Error dialog "Gauge length must be a valid number (mm)"
    RESULT: [✓/✗]

TEST 8B: Negative value
    ACTION: Enter "-50" in gauge length, click Start
    EXPECTED: Error dialog "Gauge length must be positive"
    RESULT: [✓/✗]

TEST 8C: Zero value
    ACTION: Enter "0" in gauge length, click Start
    EXPECTED: Error dialog "Gauge length must be positive"
    RESULT: [✓/✗]

TEST 8D: Empty field
    ACTION: Leave gauge length empty, click Start
    EXPECTED: Error dialog "Gauge length must be a valid number (mm)"
    RESULT: [✓/✗]

PURPOSE:
    Ensures robust input validation


================================================================================
REAL-TIME TRACKING TEST
================================================================================

TEST 9: Optical Flow Tracking
────────────────────────────────────────────────────────────────────────────

SETUP:
    1. Markers selected
    2. Gauge length entered (50 mm)
    3. Tracking started

ACTION:
    Observe specimen under test (or move camera)

EXPECTED:
    1. Green filled circles (markers) visible on video
    2. Blue line connecting markers (gauge line)
    3. Circles move with the specimen
    4. Status updates every frame:
       "Strain: +0.0XXXXX | Distance: XX.XX mm | Status: Tracking"
    5. Strain value changes as markers move
    6. Console shows NO errors (no exception prints)

VERIFICATION:
    - Strain should be NEGATIVE when specimen compresses
      (current_distance < initial_distance)
    - Strain should be POSITIVE when specimen extends
      (current_distance > initial_distance)
    - Formula: strain = (current_mm - initial_mm) / initial_mm

FAILURE MODES:
    ✗ Circles don't appear → Check cv2.circle() with writable frame
    ✗ Line doesn't appear → Check cv2.line() with writable frame
    ✗ Strain doesn't update → Check tracking.track() return value
    ✗ Console shows "Optical flow failed" → Check image dimensions
    ✗ Strain always 0 → Check pixel_to_mm calibration


TEST 10: Tracking Loss Handling
────────────────────────────────────────────────────────────────────────────

ACTION:
    1. During tracking, move specimen rapidly (or cover camera)
    2. Observe optical flow behavior

EXPECTED:
    1. When tracking fails (insufficient points):
       Status shows: "Strain: 0.000000 | Status: Tracking Loss"
    2. Markers disappear from screen
    3. No crash or exception
    4. When specimen comes back in view, tracking resumes

PURPOSE:
    Ensures graceful handling of tracking loss


================================================================================
STOP TRACKING TEST
================================================================================

TEST 11: Stop Tracking Button
────────────────────────────────────────────────────────────────────────────

SETUP:
    Currently tracking

ACTION:
    Click "Stop Tracking" button

EXPECTED:
    1. Console shows: [TRACKING STOP] Tracking halted by user
    2. Markers display as RED OUTLINE circles (not filled)
    3. Text "Ready" appears
    4. Status shows: "Strain: 0.000000 | Status: Idle"
    5. Button states change:
       - "Capture & Select Markers": ENABLED
       - "Start Tracking": ENABLED
       - "Stop Tracking": DISABLED
    6. Video continues updating

PURPOSE:
    Allows mid-test pause and re-tracking


TEST 12: Re-track After Stop
────────────────────────────────────────────────────────────────────────────

ACTION:
    After stopping, click "Start Tracking" again

EXPECTED:
    1. Tracking resumes with SAME markers and gauge length
    2. Green circles appear again
    3. Strain calculation continues from current position
    4. No need to re-select markers

PURPOSE:
    Verifies marker state persistence


================================================================================
ROBUSTNESS TESTS
================================================================================

TEST 13: Quick Repeated Captures
────────────────────────────────────────────────────────────────────────────

ACTION:
    1. Capture markers
    2. Stop before tracking
    3. Immediately capture again
    4. Select different markers
    5. Start tracking with new markers

EXPECTED:
    ✓ New markers tracked correctly
    ✓ Old marker positions forgotten
    ✓ No memory leaks (check Task Manager memory doesn't grow)

PURPOSE:
    Ensures state reset works properly


TEST 14: Long-Duration Tracking
────────────────────────────────────────────────────────────────────────────

ACTION:
    Run tracking for 1+ hour continuously

EXPECTED:
    ✓ No memory leaks (memory usage stable)
    ✓ No frame drops
    ✓ No cumulative errors in strain readings
    ✓ 30 FPS maintained throughout

MONITOR:
    - Task Manager > Performance > Memory (should stay constant)
    - Task Manager > Performance > CPU (should stay < 40%)

PURPOSE:
    Ensures production-ready stability


TEST 15: Graceful Window Close
────────────────────────────────────────────────────────────────────────────

ACTION:
    While tracking, click window close button (X)

EXPECTED:
    1. Console shows:
       [TRACKING STOP] Tracking halted by user
       [CAMERA] Acquisition stopped
       [CAMERA] Released all resources
       [SHUTDOWN] Application closed gracefully
    2. Window closes immediately (no hang)
    3. No orphaned processes

PURPOSE:
    Ensures proper resource cleanup


================================================================================
CRITICAL REGRESSION TESTS (Verifying the Fix)
================================================================================

TEST 16: Frame Writeability
────────────────────────────────────────────────────────────────────────────

PURPOSE:
    Verify the readonly array fix is working

ACTION:
    1. Start tracking
    2. Monitor console for any "readonly" errors
    3. Wait 100+ frames

EXPECTED:
    ✓ No OpenCV errors about readonly arrays
    ✓ No crashes on cv2.circle() or cv2.line()
    ✓ Markers draw successfully
    ✓ Console stays clean (no warnings)

PASS CRITERIA:
    100% of frames successfully drawn without errors

FAILURE:
    ✗ Any "readonly" error indicates fix didn't apply
    ✗ Crash on drawing = camera.py.copy() not working


TEST 17: Frame-by-Frame Verification
────────────────────────────────────────────────────────────────────────────

PURPOSE:
    Low-level verification of frame writeability

ACTION:
    Add temporary debug code to tracking loop:

    ```python
    print(f"Frame writable: {frame.flags.writeable}")
    print(f"Frame dtype: {frame.dtype}")
    print(f"Frame shape: {frame.shape}")
    ```

EXPECTED OUTPUT (each frame):
    Frame writable: True
    Frame dtype: uint8
    Frame shape: (2048, 2448, 3)

PASS CRITERIA:
    All frames show writable: True


TEST 18: Performance Regression
────────────────────────────────────────────────────────────────────────────

PURPOSE:
    Verify .copy() doesn't break 30 FPS target

MEASUREMENT:
    Run for 1000 frames and measure:
    - Average FPS
    - Min FPS
    - Max FPS
    - Frame latency

EXPECTED:
    ✓ Average FPS: 28-31 FPS
    ✓ Minimum FPS: > 25 FPS
    ✓ Latency: < 100ms
    ✓ CPU usage: < 40% on single core

PURPOSE:
    Ensures fix doesn't degrade performance below requirements


================================================================================
COMPARISON: BEFORE vs AFTER FIX
================================================================================

BEFORE (Broken):
    Action: Start tracking
    Result: CRASH on first cv2.circle()
            Error: "img marked as output argument, but provided NumPy 
                    array marked as readonly"
    Console output: None (crash immediate)

AFTER (Fixed):
    Action: Start tracking
    Result: Markers appear, tracking successful
    Console output: 
        [TRACKING START] Calibration: X.XXXXXX mm/px
        (no errors)
    Frame drawability: All frames writable


================================================================================
FINAL ACCEPTANCE CRITERIA
================================================================================

All of these must pass:

[✓] TEST 1: Application starts without errors
[✓] TEST 2: Button states correct initially
[✓] TEST 3: Capture freezes frame
[✓] TEST 4: First marker selectable
[✓] TEST 5: Second marker selectable, auto-close
[✓] TEST 6: Markers display in red "Ready" state
[✓] TEST 7: Valid gauge length accepted
[✓] TEST 8: Invalid inputs rejected with appropriate errors
[✓] TEST 9: Optical flow tracking works, strain updates
[✓] TEST 10: Tracking loss handled gracefully
[✓] TEST 11: Stop button works, state reverts
[✓] TEST 12: Re-tracking after stop works
[✓] TEST 13: Quick repeated captures work
[✓] TEST 14: 1+ hour stable operation (no leaks, stable FPS)
[✓] TEST 15: Window close cleanup is proper
[✓] TEST 16: No readonly array errors (THE KEY TEST)
[✓] TEST 17: All frames writable: True
[✓] TEST 18: Performance meets 28-31 FPS target

FINAL VERDICT: [PASS / FAIL]

If any test FAILS, do not consider application production-ready.

================================================================================
EMERGENCY TROUBLESHOOTING
================================================================================

SYMPTOM: Readonly array error still appears
FIX: 
    1. Verify camera.py line 108: frame = frame.copy()
    2. Verify file was saved (not cached)
    3. Restart Python interpreter
    4. Check file has correct indentation

SYMPTOM: Tracking loss immediately after starting
FIX:
    1. Ensure good lighting on specimen
    2. Check marker contrast (white/black on specimen)
    3. Verify marker size > 10 pixels on screen
    4. Try larger search window: winSize=(31, 31) in tracking.py

SYMPTOM: Memory leak (grows continuously)
FIX:
    1. Add frame.Release() if using PySpin API directly
    2. Verify camera.release() is called on close
    3. Check for circular references in state variables

SYMPTOM: Frames stuck/not updating
FIX:
    1. Verify camera is in "NewestOnly" buffer mode
    2. Check frame rate settings in camera.py
    3. Restart camera connection

SYMPTOM: Strain reading drifts over time
FIX:
    1. Increase tracking window size: winSize=(31, 31)
    2. Reduce lighting changes (ensure stable illumination)
    3. Verify specimen markers are high-contrast

================================================================================
