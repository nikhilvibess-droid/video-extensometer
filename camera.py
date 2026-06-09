import os

dll_path = r"C:\Program Files\Teledyne\Spinnaker\bin64"
legacy_path = r"C:\Program Files\Point Grey Research\Spinnaker\bin64"

if os.path.exists(dll_path):
    os.add_dll_directory(dll_path)
elif os.path.exists(legacy_path):
    os.add_dll_directory(legacy_path)

import PySpin


class FLIRCamera:
    """
    FLIR Blackfly S camera interface using PySpin.
    
    Features:
    - Auto-initializes first available camera
    - Converts raw sensor data to BGR8 format
    - Returns WRITABLE numpy arrays (critical for OpenCV)
    - Implements NewestOnly buffer mode for live streaming
    """

    def __init__(self):
        """Initialize FLIR camera and acquisition parameters."""
        
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()

        if self.cam_list.GetSize() == 0:
            raise RuntimeError("No FLIR camera detected")

        self.cam = self.cam_list.GetByIndex(0)

        self.cam.Init()

        # Configure stream buffer handling for live video
        # "NewestOnly" drops old frames to prevent latency buildup
        nodemap = self.cam.GetTLStreamNodeMap()

        handling_mode = PySpin.CEnumerationPtr(
            nodemap.GetNode("StreamBufferHandlingMode")
        )

        if (
            PySpin.IsReadable(handling_mode)
            and PySpin.IsWritable(handling_mode)
        ):
            entry = handling_mode.GetEntryByName(
                "NewestOnly"
            )

            handling_mode.SetIntValue(
                entry.GetValue()
            )
            print("[CAMERA] Stream mode: NewestOnly (live video)")

        # Initialize image processor for color conversion
        self.converter = PySpin.ImageProcessor()

        # Use high-quality linear color processing
        self.converter.SetColorProcessing(
            PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR
        )

        self.cam.BeginAcquisition()
        print("[CAMERA] Acquisition started")

    def read(self):
        """
        Acquire and convert frame from FLIR camera.
        
        CRITICAL FIX: Returns WRITABLE memory by calling .copy()
        
        PySpin's ImageProcessor returns a temporary managed object
        whose underlying memory is READ-ONLY. This causes OpenCV
        drawing functions (circle, line) to fail with:
        "img marked as output argument, but provided NumPy array marked as readonly"
        
        Solution: Call .copy() to allocate new writable memory from the numpy array.
        
        Returns:
            tuple: (success: bool, frame: np.ndarray BGR8 writable or None)
        """
        try:
            image = self.cam.GetNextImage(2000)

        except PySpin.SpinnakerException:
            return False, None

        if image.IsIncomplete():
            image.Release()
            return False, None

        # Convert raw sensor data to BGR8 format
        frame = self.converter.Convert(
            image,
            PySpin.PixelFormat_BGR8
        ).GetNDArray()

        image.Release()

        # ===== CRITICAL =====
        # PySpin returns readonly references to managed memory.
        # OpenCV drawing operations require WRITABLE arrays.
        # Without this copy, cv2.circle() and cv2.line() crash!
        frame = frame.copy()
        # ====================

        return True, frame

    def release(self):
        """
        Stop acquisition and clean up camera resources.
        
        CRITICAL SHUTDOWN SEQUENCE:
        1. End acquisition on live stream
        2. Deinitialize camera
        3. Delete camera reference to release PySpin memory
        4. Clear camera list
        5. Release system instance
        
        This prevents: "Can't clear a camera because something still holds 
        a reference to the camera [-1004]"
        """
        try:
            # Stop live acquisition
            if self.cam:
                self.cam.EndAcquisition()
                print("[CAMERA] Acquisition stopped")
                
                # Deinitialize camera hardware
                self.cam.DeInit()
                print("[CAMERA] Camera deinitialized")
                
                # CRITICAL: Delete camera object reference
                # This allows PySpin to fully release internal memory
                del self.cam
                self.cam = None
                print("[CAMERA] Camera reference released")
                
        except PySpin.SpinnakerException as e:
            print(f"[CAMERA ERROR] Spinnaker cleanup error: {e}")
        except Exception as e:
            print(f"[CAMERA ERROR] Cleanup error: {e}")

        try:
            # Clear camera list
            if self.cam_list:
                self.cam_list.Clear()
                print("[CAMERA] Camera list cleared")
                
        except Exception as e:
            print(f"[CAMERA ERROR] Failed to clear camera list: {e}")

        try:
            # Release system instance
            if self.system:
                self.system.ReleaseInstance()
                print("[CAMERA] System instance released")
                
        except Exception as e:
            print(f"[CAMERA ERROR] Failed to release system: {e}")
        
        print("[CAMERA] All resources released successfully")