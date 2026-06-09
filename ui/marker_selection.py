import cv2
import numpy as np


class MarkerSelector:
    """
    Production-grade marker selection tool for frozen frames.
    
    Workflow:
    1. User clicks Marker 1 -> Green circle + "P1" label appears immediately
    2. User clicks Marker 2 -> Green circle + "P2" label appears immediately
    3. Blue gauge line drawn between markers
    4. Pixel distance and coordinate info displayed
    5. User must press ENTER to confirm selection
    6. ESC key cancels selection
    
    This prevents accidental selection and ensures visual verification.
    """

    def __init__(self):
        self.points = []
        self.confirmed = False

    def click(self, event, x, y, flags, param):
        """
        Mouse callback handler for marker selection.
        Handles LBUTTONDOWN events only.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points) < 2:
                self.points.append((x, y))
                print(f"[MARKER SELECTION] Marker P{len(self.points)} selected at ({x}, {y})")

    def select(self, frame):
        """
        Professional marker selection workflow with persistent visual feedback.
        
        CRITICAL BEHAVIOR:
        1. Click P1 → Green circle + "P1" label PERMANENTLY VISIBLE
        2. Click P2 → Green circle + "P2" label PERMANENTLY VISIBLE
        3. When complete → Blue gauge line shown
        4. Operator presses ENTER to confirm
        5. Operator presses ESC to re-select
        
        Markers do NOT disappear on screen refresh - they persist in the display.
        
        Args:
            frame: Frozen image to select markers on (BGR numpy array, writable)
            
        Returns:
            list: [(x1, y1), (x2, y2)] if confirmed, [] if cancelled
        """
        self.points = []
        self.confirmed = False

        # CRITICAL: Ensure frame is writable - all drawing must work
        if not frame.flags.writeable:
            frame = frame.copy()

        window_name = "Professional Marker Selection"
        
        cv2.namedWindow(
            window_name,
            cv2.WINDOW_NORMAL
        )

        cv2.resizeWindow(
            window_name,
            1400,
            1000
        )

        cv2.setMouseCallback(
            window_name,
            self.click
        )

        print("\n[MARKER SELECTION] ════════════════════════════════════════")
        print("[MARKER SELECTION] PROFESSIONAL MARKER SELECTION WORKFLOW")
        print("[MARKER SELECTION] ════════════════════════════════════════")
        print("[MARKER SELECTION] Instructions:")
        print("[MARKER SELECTION]   1. Click at Marker 1 (P1) location")
        print("[MARKER SELECTION]   2. Click at Marker 2 (P2) location")
        print("[MARKER SELECTION]   3. Press ENTER to confirm selection")
        print("[MARKER SELECTION]   4. Press ESC to cancel and re-select")
        print("[MARKER SELECTION] ════════════════════════════════════════\n")

        while True:
            temp = frame.copy()

            # ===== DRAW SELECTED MARKERS (PERMANENTLY VISIBLE) =====
            for i, p in enumerate(self.points):
                # CRITICAL: Draw large green filled circle - MUST be visible
                cv2.circle(
                    temp,
                    p,
                    18,      # Slightly larger (was 15)
                    (0, 255, 0),  # Bright green
                    -1       # Filled
                )
                
                # Draw white border for contrast and visibility
                cv2.circle(
                    temp,
                    p,
                    18,
                    (255, 255, 255),  # White contour
                    3        # Thicker border (was 2)
                )

                # Draw marker label with professional appearance
                label = f"P{i + 1}"
                label_pos = (p[0] + 25, p[1] - 15)
                
                # Get text size for background rectangle
                text_size = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.2,
                    2
                )[0]
                
                # Draw green background for label (thick, opaque)
                cv2.rectangle(
                    temp,
                    (label_pos[0] - 8, label_pos[1] - text_size[1] - 8),
                    (label_pos[0] + text_size[0] + 8, label_pos[1] + 5),
                    (0, 255, 0),  # Bright green background
                    -1            # Filled
                )
                
                # Draw dark border on label for definition
                cv2.rectangle(
                    temp,
                    (label_pos[0] - 8, label_pos[1] - text_size[1] - 8),
                    (label_pos[0] + text_size[0] + 8, label_pos[1] + 5),
                    (0, 0, 0),  # Black border
                    2
                )
                
                # Draw marker label text (WHITE text on green for maximum contrast)
                cv2.putText(
                    temp,
                    label,
                    label_pos,
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.2,
                    (255, 255, 255),  # White text (high contrast)
                    2
                )

                # Display coordinates (permanent)
                coord_text = f"({p[0]}, {p[1]})"
                coord_pos = (p[0] - 80, p[1] + 50)
                
                # Coordinates with semi-transparent background
                cv2.putText(
                    temp,
                    coord_text,
                    coord_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),  # Cyan text
                    2
                )

            # ===== DRAW GAUGE LINE WHEN BOTH MARKERS SELECTED =====
            if len(self.points) == 2:
                # Thick blue gauge line connecting markers
                cv2.line(
                    temp,
                    self.points[0],
                    self.points[1],
                    (255, 0, 0),  # Bright blue
                    4             # Thick line (was 3)
                )

                # Calculate pixel distance
                pixel_dist = np.sqrt(
                    (self.points[0][0] - self.points[1][0]) ** 2 +
                    (self.points[0][1] - self.points[1][1]) ** 2
                )

                # Find midpoint
                mid_x = (self.points[0][0] + self.points[1][0]) // 2
                mid_y = (self.points[0][1] + self.points[1][1]) // 2

                # Distance text with background
                distance_text = f"Gauge Distance: {pixel_dist:.1f} px"
                dist_text_size = cv2.getTextSize(
                    distance_text,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    2
                )[0]
                
                # Distance background box
                cv2.rectangle(
                    temp,
                    (mid_x - dist_text_size[0]//2 - 10, mid_y - 50),
                    (mid_x + dist_text_size[0]//2 + 10, mid_y - 15),
                    (0, 0, 0),      # Black background
                    -1              # Filled
                )
                
                # Distance text (CYAN - high visibility)
                cv2.putText(
                    temp,
                    distance_text,
                    (mid_x - dist_text_size[0]//2, mid_y - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 255),  # Bright cyan
                    2
                )

            # ===== STATUS & INSTRUCTION PANEL =====
            status_y = 50
            
            # Selection status (top left)
            marker_status = f"Markers Selected: {len(self.points)}/2"
            status_bg_size = cv2.getTextSize(
                marker_status,
                cv2.FONT_HERSHEY_SIMPLEX,
                1.1,
                2
            )[0]
            
            cv2.rectangle(
                temp,
                (10, status_y - 35),
                (20 + status_bg_size[0], status_y),
                (0, 0, 0),  # Black background
                -1
            )
            
            cv2.putText(
                temp,
                marker_status,
                (20, status_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.1,
                (255, 255, 255),  # White text
                2
            )

            # Instructions (varies based on state)
            if len(self.points) < 2:
                instr_text = "CLICK to select Marker 1, then Marker 2"
                instr_color = (0, 255, 255)  # Yellow (action needed)
            else:
                instr_text = "ENTER: Confirm Selection  |  ESC: Re-select"
                instr_color = (0, 255, 0)    # Green (ready)

            instr_bg_size = cv2.getTextSize(
                instr_text,
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                2
            )[0]
            
            cv2.rectangle(
                temp,
                (10, status_y + 30),
                (20 + instr_bg_size[0], status_y + 85),
                (0, 0, 0),  # Black background
                -1
            )
            
            cv2.putText(
                temp,
                instr_text,
                (20, status_y + 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                instr_color,
                2
            )

            # ===== VERIFICATION PANEL (when both markers selected) =====
            if len(self.points) == 2:
                verify_text = "Markers Verified - Gauge Region Ready"
                verify_size = cv2.getTextSize(
                    verify_text,
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.1,
                    2
                )[0]
                
                # Bottom center verification banner
                verify_y = temp.shape[0] - 60
                
                cv2.rectangle(
                    temp,
                    (temp.shape[1]//2 - verify_size[0]//2 - 15, verify_y - 35),
                    (temp.shape[1]//2 + verify_size[0]//2 + 15, verify_y + 5),
                    (0, 200, 0),  # Bright green
                    -1
                )
                
                cv2.putText(
                    temp,
                    verify_text,
                    (temp.shape[1]//2 - verify_size[0]//2, verify_y - 10),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.1,
                    (255, 255, 255),  # White text on green
                    2
                )

            # PERMANENTLY DISPLAY FRAME (critical loop)
            cv2.imshow(window_name, temp)

            # ===== PROFESSIONAL KEYBOARD HANDLING =====
            key = cv2.waitKey(30) & 0xFF
            
            if key == 13:  # ENTER key (ASCII 13)
                if len(self.points) == 2:
                    print("[MARKER SELECTION] ✓ CONFIRMED by operator")
                    print(f"[MARKER SELECTION] P1: {self.points[0]}, P2: {self.points[1]}")
                    self.confirmed = True
                    cv2.destroyAllWindows()
                    return self.points
                else:
                    print("[MARKER SELECTION] ⚠ Cannot confirm: Please select exactly 2 markers")
                    
            elif key == 27:  # ESC key (ASCII 27)
                print("[MARKER SELECTION] ✗ CANCELLED by operator - returning to selection")
                self.points = []  # Clear selection for re-selection
                cv2.destroyAllWindows()
                return []
            
            elif key != 255:  # Any other key pressed
                print(f"[MARKER SELECTION] Key pressed: {key} (use ENTER to confirm or ESC to cancel)")

        # Fallback cleanup
        cv2.destroyWindow(window_name)
        return self.points if self.confirmed else []
