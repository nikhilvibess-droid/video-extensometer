from PyQt5 import QtWidgets, QtGui, QtCore
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class LiveGraphWidget(FigureCanvas):
    """
    High-performance real-time plotting canvas utilizing Matplotlib.
    Styled with a professional dark theme with a deep blue background.
    """
    def __init__(self, title, ylabel, line_color, is_strain_y=False, x_label="Time (s)", parent=None):
        # Professional midnight blue background
        self.fig = Figure(facecolor="#0a0f1d")
        super().__init__(self.fig)
        self.setParent(parent)

        # Configure margins to maximize plotting area and avoid empty spaces
        self.fig.subplots_adjust(left=0.12, right=0.96, top=0.92, bottom=0.18)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#0a0f1d")

        # Custom grid line styling (subtle gray-blue)
        self.ax.grid(True, color="#1e293b", linestyle="-", linewidth=0.5)

        # Style layout boundaries (spines) to blend in
        for spine in self.ax.spines.values():
            spine.set_color("#1e293b")
            spine.set_linewidth(1.0)

        # Configure tick labels with professional colors and size
        self.ax.tick_params(colors="#64748b", labelsize=11)

        # Configure axis labels with modern clean typography
        self.ax.set_xlabel(
            x_label,
            color="#94a3b8",
            fontsize=12,
            fontweight="bold",
            fontname="Segoe UI"
        )
        self.ax.set_ylabel(
            ylabel,
            color="#94a3b8",
            fontsize=12,
            fontweight="bold",
            fontname="Segoe UI"
        )

        # Initialize the plotting line with smooth anti-aliasing
        self.line, = self.ax.plot(
            [],
            [],
            color=line_color,
            linewidth=2.8,
            antialiased=True
        )

        self.is_strain_y = is_strain_y
        self.current_x = []
        self.current_y = []

    def clear(self):
        """
        Resets plot line and limits to defaults.
        """
        self.line.set_data([], [])
        self.current_x = []
        self.current_y = []
        self.ax.set_xlim(0, 10)
        if self.is_strain_y:
            self.ax.set_ylim(-0.5, 5.0)
        else:
            self.ax.set_ylim(0, 10)
        self.draw_idle()


class GraphContainer(QtWidgets.QFrame):
    """
    A premium dark-themed container wrapping LiveGraphWidget.
    Includes a header with title, live HUD indicators, and control toolbar.
    """
    def __init__(self, title, ylabel, line_color, is_strain_y=False, x_label="Time (s)", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.ylabel = ylabel
        self.x_label = x_label
        self.is_strain_y = is_strain_y

        self.auto_scale_enabled = True
        self.latest_x = []
        self.latest_y = []

        self.setObjectName("graphContainerFrame")
        self.setup_ui(title, ylabel, line_color, is_strain_y, x_label)
        self.setup_toolbar()

        self.update_live_metrics()

    def setup_ui(self, title, ylabel, line_color, is_strain_y, x_label):
        # Round container with dark border styling
        self.setStyleSheet("""
            QFrame#graphContainerFrame {
                background-color: #0a0f1d;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QLabel#titleLabel {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 14px;
                font-weight: bold;
                border: none;
                background-color: transparent;
            }
            QLabel#indicatorLabel {
                color: #94a3b8;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 11px;
                border: none;
                background-color: transparent;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 2px;
                min-width: 22px;
                min-height: 22px;
            }
            QToolButton:hover {
                background-color: #1e293b;
                border-color: #334155;
            }
            QToolButton:checked {
                background-color: #2563eb;
                border-color: #2563eb;
            }
            QToolTip {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 10px;
            }
        """)

        # Main Layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)

        # Header Bar
        self.header = QtWidgets.QWidget()
        self.header.setStyleSheet("border: none; background-color: transparent;")
        self.header_layout = QtWidgets.QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(4, 2, 4, 2)
        self.header_layout.setSpacing(8)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("titleLabel")
        self.header_layout.addWidget(self.title_label)

        # Live readout label
        self.indicator_label = QtWidgets.QLabel("—")
        self.indicator_label.setObjectName("indicatorLabel")
        self.header_layout.addWidget(self.indicator_label)

        self.header_layout.addStretch()
        self.main_layout.addWidget(self.header)

        # Matplotlib Canvas (inset slightly to preserve rounded corners)
        self.canvas = LiveGraphWidget(title, ylabel, line_color, is_strain_y, x_label, parent=self)
        self.canvas.setStyleSheet("border: none; background-color: transparent;")
        self.main_layout.addWidget(self.canvas, 1)

    def setup_toolbar(self):
        self.export_png_btn = QtWidgets.QToolButton()
        self.export_png_btn.setToolTip("Download Graph")
        self.export_png_btn.setIcon(self.create_export_png_icon())
        self.export_png_btn.clicked.connect(self.export_png)
        self.header_layout.addWidget(self.export_png_btn)

    def create_export_png_icon(self):
        pixmap = QtGui.QPixmap(24, 24)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#94a3b8"), 2)
        painter.setPen(pen)
        painter.drawLine(12, 4, 12, 14)
        painter.drawLine(12, 14, 8, 10)
        painter.drawLine(12, 14, 16, 10)
        painter.drawLine(5, 18, 19, 18)
        painter.drawLine(5, 15, 5, 18)
        painter.drawLine(19, 15, 19, 18)
        painter.end()
        return QtGui.QIcon(pixmap)

    def run_auto_scale(self):
        """
        Calculates and applies the optimal bounding box for current data points
        plus the required 10% padding.
        """
        x = self.canvas.current_x
        y = self.canvas.current_y
        if len(x) == 0 or len(y) == 0:
            return

        xmin, xmax = min(x), max(x)
        ymin, ymax = min(y), max(y)

        xdiff = xmax - xmin
        ydiff = ymax - ymin

        x_pad = max(1.0, xdiff * 0.1)
        y_pad = max(0.01, ydiff * 0.1)

        self.canvas.ax.set_xlim(xmin - x_pad, xmax + x_pad)
        self.canvas.ax.set_ylim(ymin - y_pad, ymax + y_pad)
        self.canvas.draw_idle()

    # ==========================================
    # DATA INTERFACES & EXPORTS
    # ==========================================
    def update_data(self, x_list, y_list):
        """
        Updates the line series using smart downsampling to guarantee 60 FPS
        rendering speeds, whilst maintaining full raw precision data for exports.
        """
        self.latest_x = x_list
        self.latest_y = y_list

        if len(x_list) == 0:
            self.canvas.clear()
            return

        # Perform smart downsampling if list is large to maintain 60 FPS UI performance
        if len(x_list) > 1000:
            step = len(x_list) // 1000
            x_plot = list(x_list[::step])
            y_plot = list(y_list[::step])
            # Guarantee the last point is present
            if x_plot[-1] != x_list[-1]:
                x_plot.append(x_list[-1])
                y_plot.append(y_list[-1])
        else:
            x_plot = list(x_list)
            y_plot = list(y_list)

        # Scale Strain outputs to percentage (%) representation
        if self.is_strain_y:
            y_plot_scaled = [val * 100.0 for val in y_plot]
            y_original_scaled = [val * 100.0 for val in y_list]
        else:
            y_plot_scaled = y_plot
            y_original_scaled = y_list

        # Cache fully-detailed data for CSV/PNG exports
        self.canvas.current_x = list(x_list)
        self.canvas.current_y = y_original_scaled

        self.canvas.line.set_data(x_plot, y_plot_scaled)

        if self.auto_scale_enabled:
            xmin, xmax = min(x_list), max(x_list)
            ymin, ymax = min(y_original_scaled), max(y_original_scaled)

            xdiff = xmax - xmin
            ydiff = ymax - ymin

            x_pad = max(1.0, xdiff * 0.1)
            y_pad = max(0.01, ydiff * 0.1)

            self.canvas.ax.set_xlim(xmin - x_pad, xmax + x_pad)
            self.canvas.ax.set_ylim(ymin - y_pad, ymax + y_pad)

        self.canvas.draw_idle()

    def update_live_metrics(self, elapsed=None, fps=None, current_strain=None, current_distance=None):
        """
        Dynamically formats and overlays current telemetry values on the plot header.
        """
        time_str = "00:00:00"
        if elapsed is not None:
            s = int(elapsed)
            h = s // 3600
            m = (s % 3600) // 60
            sec = s % 60
            time_str = f"{h:02d}:{m:02d}:{sec:02d}"

        fps_str = f"{int(round(fps))}" if fps is not None else "—"

        if self.is_strain_y:
            strain_val = f"{current_strain * 100.0:+.3f} %" if current_strain is not None else "—"
            self.indicator_label.setText(
                f"Strain: <span style='color: #fbbf24; font-weight: bold;'>{strain_val}</span> | "
                f"Time: <span style='color: #f8fafc; font-weight: bold;'>{time_str}</span> | "
                f"FPS: <span style='color: #94a3b8; font-weight: bold;'>{fps_str}</span>"
            )
        else:
            dist_val = f"{current_distance:.2f} mm" if current_distance is not None else "—"
            self.indicator_label.setText(
                f"Distance: <span style='color: #22d3ee; font-weight: bold;'>{dist_val}</span> | "
                f"Time: <span style='color: #f8fafc; font-weight: bold;'>{time_str}</span> | "
                f"FPS: <span style='color: #94a3b8; font-weight: bold;'>{fps_str}</span>"
            )

    def append_point(self, x, y):
        """
        Appends a single new point to the graph data buffers and updates the line.
        """
        self.latest_x.append(x)
        self.latest_y.append(y)

        # Cap buffers at 10000 points
        if len(self.latest_x) > 10000:
            self.latest_x = self.latest_x[-10000:]
            self.latest_y = self.latest_y[-10000:]

        y_scaled = y * 100.0 if self.is_strain_y else y

        self.canvas.current_x.append(x)
        self.canvas.current_y.append(y_scaled)

        # Cap buffers at 10000 points
        if len(self.canvas.current_x) > 10000:
            self.canvas.current_x = self.canvas.current_x[-10000:]
            self.canvas.current_y = self.canvas.current_y[-10000:]

        # Update line data directly
        self.canvas.line.set_data(self.canvas.current_x, self.canvas.current_y)

        if self.auto_scale_enabled:
            xmin, xmax = min(self.canvas.current_x), max(self.canvas.current_x)
            ymin, ymax = min(self.canvas.current_y), max(self.canvas.current_y)

            xdiff = xmax - xmin
            ydiff = ymax - ymin

            x_pad = max(1.0, xdiff * 0.1)
            y_pad = max(0.01, ydiff * 0.1)

            self.canvas.ax.set_xlim(xmin - x_pad, xmax + x_pad)
            self.canvas.ax.set_ylim(ymin - y_pad, ymax + y_pad)

        self.canvas.draw_idle()

    def clear(self):
        """
        Discards active series, resets live indicators, and redraws empty grids.
        """
        self.latest_x = []
        self.latest_y = []
        self.canvas.clear()
        self.update_live_metrics()
        self.auto_scale_enabled = True

    def export_png(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Download Graph",
            f"{self.title_text.replace(' ', '_')}.png",
            "PNG Images (*.png)",
        )
        if file_path:
            try:
                self.canvas.fig.savefig(
                    file_path,
                    dpi=300,
                    facecolor=self.canvas.fig.get_facecolor(),
                    bbox_inches="tight",
                    pad_inches=0.15,
                )
                QtWidgets.QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Graph successfully saved as PNG image to:\n{file_path}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export plot: {e}"
                )