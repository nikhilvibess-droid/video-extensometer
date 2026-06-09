import cv2
import numpy as np
from math import sqrt


class MarkerTracker:
    """
    Pyramid Lucas-Kanade optical flow tracker.
    Tracks 2 markers (gauge points) across consecutive frames.
    """

    def __init__(self):
        """Initialize tracker with LK parameters optimized for industrial markers."""
        self.p0 = None  # Initial points in format required by calcOpticalFlowPyrLK

        # Lucas-Kanade parameters
        self.lk_params = dict(
            winSize=(21, 21),        # 21x21 search window
            maxLevel=3,              # 3 pyramid levels
            criteria=(
                cv2.TERM_CRITERIA_EPS |
                cv2.TERM_CRITERIA_COUNT,
                30,                  # 30 max iterations
                0.01                 # 0.01 epsilon
            )
        )

    def distance(self, p1, p2):
        """
        Euclidean distance between two 2D points.
        
        Args:
            p1: (x, y) tuple or numpy array
            p2: (x, y) tuple or numpy array
            
        Returns:
            float: Distance in pixels
        """
        return sqrt(
            (p1[0] - p2[0]) ** 2 +
            (p1[1] - p2[1]) ** 2
        )

    def initialize(self, points):
        """
        Initialize tracker with marker positions.
        
        Args:
            points: List of [(x1, y1), (x2, y2)] coordinates
        """
        # Convert to format required by calcOpticalFlowPyrLK
        self.p0 = np.array(
            points,
            dtype=np.float32
        ).reshape(-1, 1, 2)
        print(f"[TRACKER INIT] Initialized with {len(self.p0)} points")

    def track(self, old_gray, gray):
        """
        Track markers between consecutive frames using pyramid LK optical flow.
        
        Args:
            old_gray: Previous grayscale frame
            gray: Current grayscale frame
            
        Returns:
            numpy array: Updated marker positions or None if tracking fails
        """
        if self.p0 is None:
            return None

        try:
            # Calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(
                old_gray,
                gray,
                self.p0,
                None,
                **self.lk_params
            )

        except Exception as e:
            print(f"[TRACKER ERROR] Optical flow failed: {e}")
            return None

        if p1 is None:
            return None

        # Filter good points (status == 1)
        good = p1[st == 1]

        # Require exactly 2 tracked markers
        if len(good) != 2:
            return None

        # Update initial points for next frame
        self.p0 = good.reshape(-1, 1, 2)

        return good