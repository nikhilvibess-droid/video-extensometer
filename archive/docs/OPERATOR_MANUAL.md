# Video Extensometer - Operator Manual

## Professional Marker Selection Workflow

### Step 1: Live Video Feed
```
┌─────────────────────────────────────────┐
│  Live Camera Feed (Real-time)           │
│                                         │
│  [Specimen visible in frame]            │
│                                         │
│  [Capture & Select Markers] [live]      │
└─────────────────────────────────────────┘
```

### Step 2: Capture & Freeze
1. Position specimen in frame
2. Click **"Capture & Select Markers"** button
3. Frame freezes
4. Marker selection window opens

### Step 3: Select Marker 1 (P1)
```
┌─────────────────────────────────────────┐
│  Marker Selection Window                 │
│                                         │
│  Click to select markers (P1, then P2)  │
│  Selected: 0/2                          │
│                                         │
│  [Specimen with crosshairs]             │
│  ↑ Click on first gauge point           │
└─────────────────────────────────────────┘
```

**Action**: Click on the first gauge point
**Visual Feedback**: 
- ✓ Green circle appears immediately
- ✓ Label "P1" displayed
- ✓ Coordinates shown: (x, y)

### Step 4: Select Marker 2 (P2)
```
┌─────────────────────────────────────────┐
│  Marker Selection Window                 │
│                                         │
│  PRESS ENTER to Confirm | ESC to Cancel │
│  Selected: 2/2                          │
│                                         │
│  P1 ●━━━━━━━━━━━━━━━━━━━● P2            │
│     Green circles with gauge line       │
│     Distance: 1242.5 px                 │
│                                         │
│  Confirm or cancel selection            │
└─────────────────────────────────────────┘
```

**Action**: Click on the second gauge point
**Visual Feedback**:
- ✓ Second green circle appears
- ✓ Label "P2" displayed
- ✓ Blue gauge line drawn between markers
- ✓ Pixel distance calculated and displayed
- ✓ Instructions change to confirmation prompt

### Step 5: Verify & Confirm
**Verification Steps**:
1. ✓ Both markers visible in green circles
2. ✓ Gauge line connects correct points
3. ✓ Distance seems reasonable
4. ✓ Coordinates match specimen region

**Confirmation**:
- **Press ENTER** to confirm selection
  - Window closes
  - Success dialog appears
  - Markers stored for tracking
  
- **Press ESC** to cancel and reselect
  - Window closes
  - Returns to live feed
  - Click "Capture & Select Markers" again

### Step 6: Confirmation Dialog
```
┌─────────────────────────────────────────┐
│  Markers Confirmed                      │
│                                         │
│  ✓ 2 markers successfully selected      │
│                                         │
│  P1: (425, 320)                         │
│  P2: (1667, 320)                        │
│                                         │
│  Gauge Distance: 1242.5 px              │
│                                         │
│  Ready to start tracking.               │
│  Enter gauge length and press            │
│  'Start Tracking'.                       │
│                                         │
│  [OK]                                   │
└─────────────────────────────────────────┘
```

Shows:
- ✓ Marker coordinates
- ✓ Gauge distance in pixels
- ✓ Next steps

### Step 7: Enter Gauge Length
```
┌─────────────────────────────────────────┐
│  Video Extensometer - FLIR Blackfly S   │
│                                         │
│  [Live video with P1 and P2 visible]    │
│  Status: READY - Enter Gauge Length...  │
│                                         │
│  Gauge Length (mm): [25.0_________]     │
│                                         │
│  [Capture...] [Start Tracking]  [Stop]  │
│                                         │
│  Strain: 0.000000 | Status: Ready       │
└─────────────────────────────────────────┘
```

**Action**:
1. Enter the actual gauge length in mm
2. Example: 25.0 (for 25 mm gauge)

**Important**: 
- Must match the distance between your selected markers on the specimen
- Measured with calipers or specimen documentation

### Step 8: Start Real-Time Tracking
```
┌─────────────────────────────────────────┐
│  Video Extensometer - FLIR Blackfly S   │
│                                         │
│  [Live video with tracking]             │
│  P1 ●━━━━━━━━━ ● P2 (markers moving)   │
│                                         │
│  [Capture...] [Start Tracking]  [Stop]  │
│                                         │
│  Strain: +0.002341 | Distance: 25.058mm │
│  Status: Tracking                       │
└─────────────────────────────────────────┘
```

**After Starting**:
- ✓ Markers track specimen deformation in real-time
- ✓ Strain calculated continuously
- ✓ Blue gauge line updates with specimen movement
- ✓ Distance displayed in real gauge units (mm)

### Step 9: Stop Tracking
**Click "Stop Tracking"** to pause measurements

Markers remain visible on screen for verification

---

## Troubleshooting

### Problem: Markers Not Appearing After Click

**Cause**: Frame frozen but selection window not responding

**Solution**:
1. Wait 1-2 seconds after clicking
2. If still no response, press ESC
3. Click "Capture & Select Markers" again

---

### Problem: Gauge Line Incorrect

**Cause**: Selected wrong specimen points

**Solution**:
1. Press ESC to cancel
2. Click "Capture & Select Markers" again
3. Select precisely at the gauge points
4. Use zoom if needed (resize window)

---

### Problem: Distance Seems Wrong

**Cause**: Incorrect gauge length entered

**Solution**:
1. Stop tracking
2. Verify gauge length with calipers
3. Recapture and reselect markers
4. Re-enter correct gauge length

---

### Problem: Strain Goes Negative Unexpectedly

**Cause**: 
- Camera not stable
- Specimen moved during capture
- Lighting changed

**Solution**:
1. Stop tracking
2. Recapture frame
3. Reselect markers
4. Restart tracking

---

## Keyboard Shortcuts

| Key | Action | Status |
|-----|--------|--------|
| ENTER | Confirm marker selection | In selection window only |
| ESC | Cancel marker selection | In selection window only |
| Q | Exit (old mode - deprecated) | No longer used |

---

## Visual Indicators

### Marker Selection Window

| Color | Meaning |
|-------|---------|
| Green Circle | Selected marker (P1, P2) |
| Green Background | Marker label |
| White Border | Visibility enhancement |
| Blue Line | Gauge region reference |
| Cyan Text | Coordinates and distance |
| Yellow Text | Instruction (before 2 markers) |
| Green Text | Instruction (ready to confirm) |

### Live Video Feed

| Color | Meaning |
|-------|---------|
| Green Circle | Confirmed marker (tracking) |
| Green Circle | Ready marker (before tracking) |
| Blue Line | Gauge region being measured |
| White Border | Marker emphasis |

---

## Best Practices

### 1. Marker Selection
- ✓ Select at exact gauge points (not approximate)
- ✓ Ensure good contrast between marker and specimen
- ✓ Verify before pressing ENTER
- ✓ Use specimen geometry for accuracy (edges, holes)

### 2. Gauge Length Entry
- ✓ Measure with calibrated calipers (±0.01 mm)
- ✓ Measure between exact same points as selection
- ✓ Record measurement for test documentation
- ✓ Double-check before starting tracking

### 3. Lighting
- ✓ Ensure even illumination
- ✓ Avoid shadows on specimen
- ✓ Use constant light source
- ✓ Avoid reflections from camera lens

### 4. Camera Setup
- ✓ Camera mounted perpendicular to specimen
- ✓ Entire gauge region visible in frame
- ✓ No camera movement during test
- ✓ Sufficient depth of field (focus on markers)

---

## Performance Expectations

### Typical Accuracy
- Marker tracking: ±0.5 pixels (0.01-0.05 mm)
- Strain measurement: ±0.0001 (0.01% strain)
- Frame rate: 33 FPS (30ms per frame)
- Latency: <100ms (real-time display)

### Test Duration
- Short tests: 1-5 minutes
- Standard tests: 5-30 minutes
- Long tests: 30+ minutes (may require restart)

### Temperature Effects
- Ambient: 15-35°C
- Specimen: Room temperature
- Camera warm-up: 5 minutes recommended

---

## Maintenance

### Weekly
- ✓ Clean camera lens with lens cloth
- ✓ Check camera connection (not loose)
- ✓ Verify test results accuracy

### Monthly
- ✓ Clean specimen holder
- ✓ Verify calibration with standard gauge
- ✓ Test marker tracking on known specimen

### Quarterly
- ✓ Full system calibration
- ✓ Compare with lab standards
- ✓ Document any drift

---

## Data Export

After tracking session, results include:
- Time-stamped strain values
- Distance measurements
- Marker position history
- Test parameters

Data saved to `reports/` directory automatically

---

## Need Help?

### Emergency Shutdown
- Press ESC in marker selection window
- Click Stop Tracking button
- Close window normally
- If frozen: Press Alt+F4

### Error Messages
- **"Camera Error"**: Camera not connected, reconnect and restart
- **"Selection Error"**: Must select exactly 2 markers, try again
- **"Input Error"**: Gauge length must be positive number
- **"Tracking Loss"**: Markers lost during test, restart test

### Professional Support
Contact: [support contact information]
Email: [support email]
Phone: [support phone]

---

## Operator Certification

**Operator Name**: ___________________

**Date Trained**: ___________________

**Signature**: ___________________

**Topics Covered**:
- ✓ Marker selection procedure
- ✓ Keyboard controls (ENTER/ESC)
- ✓ Gauge length measurement
- ✓ Real-time tracking operation
- ✓ Error handling
- ✓ Emergency shutdown

---

**Version**: 1.0  
**Document Date**: 2026-06-06  
**System**: Video Extensometer with FLIR Blackfly S  
**Status**: Production Ready
