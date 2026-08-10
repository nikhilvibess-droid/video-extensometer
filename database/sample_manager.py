import os
import tempfile
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from database.db_manager import DatabaseManager

SAMPLE_INTERVAL_SECONDS = 0.1
BATCH_SIZE = 2000


class SampleManager:
    """Collects tracking samples in memory and persists them linked to a report."""

    def __init__(self):
        self.db = DatabaseManager()
        self._active = False
        self._buffer = []
        self._last_recorded_elapsed = -1.0

    def start_session(self):
        self._active = True
        self._buffer = []
        self._last_recorded_elapsed = -1.0

    def discard_session(self):
        self._active = False
        self._buffer = []
        self._last_recorded_elapsed = -1.0

    @property
    def is_active(self):
        return self._active

    @property
    def pending_count(self):
        return len(self._buffer)

    def maybe_record(self, elapsed_time, distance_mm, extension_mm, strain):
        """Record a sample at 10 Hz using values from the tracking engine."""
        if not self._active:
            return

        if (
            self._last_recorded_elapsed >= 0
            and (elapsed_time - self._last_recorded_elapsed)
            < (SAMPLE_INTERVAL_SECONDS - 1e-9)
        ):
            return

        self._last_recorded_elapsed = elapsed_time
        self._buffer.append(
            (float(elapsed_time), float(distance_mm), float(extension_mm), float(strain))
        )

        print(
            "[SAMPLE SAVED]\n"
            f"Elapsed Time: {elapsed_time:.3f}\n"
            f"Distance: {distance_mm:.3f}\n"
            f"Extension: {extension_mm:.3f}\n"
            f"Strain: {strain:.6f}"
        )

    def flush_to_report(self, report_id):
        """Persist buffered samples to test_samples and clear the session."""
        samples = list(self._buffer)
        self.discard_session()

        if not samples:
            print(
                "[TIMELINE COMPLETE]\n"
                f"Report ID: {report_id}\n"
                "Total Samples Recorded: 0"
            )
            return 0

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            (report_id, s[0], s[1], s[2], s[3], timestamp)
            for s in samples
        ]

        with self.db._write_lock:
            cur = self.db.conn.cursor()
            try:
                cur.execute("BEGIN")
                for offset in range(0, len(rows), BATCH_SIZE):
                    cur.executemany(
                        """
                        INSERT INTO test_samples(
                            report_id,
                            elapsed_time,
                            distance_mm,
                            extension_mm,
                            strain,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        rows[offset : offset + BATCH_SIZE],
                    )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()

        print(
            "[TIMELINE COMPLETE]\n"
            f"Report ID: {report_id}\n"
            f"Total Samples Recorded: {len(samples)}"
        )
        return len(samples)

    def get_samples(self, report_id):
        cur = self.db.conn.cursor()
        cur.execute(
            """
            SELECT elapsed_time, distance_mm, extension_mm, strain
            FROM test_samples
            WHERE report_id = ?
            ORDER BY elapsed_time ASC
            """,
            (report_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    def get_timeline_stats(self, report_id):
        cur = self.db.conn.cursor()
        cur.execute(
            """
            SELECT
                COUNT(*),
                MAX(strain),
                AVG(strain),
                MAX(extension_mm),
                AVG(extension_mm),
                MAX(elapsed_time)
            FROM test_samples
            WHERE report_id = ?
            """,
            (report_id,),
        )
        row = cur.fetchone()
        cur.close()

        if not row or row[0] == 0:
            return {
                "total_samples": 0,
                "max_strain": None,
                "avg_strain": None,
                "max_extension": None,
                "avg_extension": None,
                "test_duration": None,
            }

        return {
            "total_samples": row[0],
            "max_strain": row[1],
            "avg_strain": row[2],
            "max_extension": row[3],
            "avg_extension": row[4],
            "test_duration": row[5],
        }

    def delete_samples_for_report(self, report_id):
        with self.db._write_lock:
            cur = self.db.conn.cursor()
            cur.execute(
                "DELETE FROM test_samples WHERE report_id = ?",
                (report_id,),
            )
            cur.execute("COMMIT")
            cur.close()

    @staticmethod
    def format_duration(seconds):
        if seconds is None:
            return "—"
        total = max(0, int(seconds))
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def generate_timeline_chart_images(samples, report_id):
        """Render strain vs time and distance vs time charts for PDF embedding."""
        if not samples:
            return None, None

        times = [s[0] for s in samples]
        distances = [s[1] for s in samples]
        strains = [s[2] * 100.0 for s in samples]

        temp_dir = tempfile.gettempdir()
        strain_path = os.path.join(
            temp_dir, f"vex_strain_timeline_{report_id}.png"
        )
        distance_path = os.path.join(
            temp_dir, f"vex_distance_timeline_{report_id}.png"
        )

        fig, ax = plt.subplots(figsize=(6.5, 2.8), facecolor="#0a0f1d")
        ax.set_facecolor("#0a0f1d")
        ax.plot(times, strains, color="#fbbf24", linewidth=2.0)
        ax.set_xlabel("Time (s)", color="#94a3b8", fontsize=10)
        ax.set_ylabel("Strain (%)", color="#94a3b8", fontsize=10)
        ax.set_title("Strain vs Time", color="#f8fafc", fontsize=11, fontweight="bold")
        ax.tick_params(colors="#64748b", labelsize=9)
        ax.grid(True, color="#1e293b", linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        fig.tight_layout()
        fig.savefig(strain_path, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6.5, 2.8), facecolor="#0a0f1d")
        ax.set_facecolor("#0a0f1d")
        ax.plot(times, distances, color="#38bdf8", linewidth=2.0)
        ax.set_xlabel("Time (s)", color="#94a3b8", fontsize=10)
        ax.set_ylabel("Distance (mm)", color="#94a3b8", fontsize=10)
        ax.set_title("Distance vs Time", color="#f8fafc", fontsize=11, fontweight="bold")
        ax.tick_params(colors="#64748b", labelsize=9)
        ax.grid(True, color="#1e293b", linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        fig.tight_layout()
        fig.savefig(distance_path, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)

        return strain_path, distance_path
