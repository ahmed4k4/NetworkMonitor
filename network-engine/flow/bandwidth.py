import time
from collections import defaultdict, deque


class BandwidthTracker:

    def __init__(self, window_seconds=1):

        self.window_seconds = window_seconds

        self.samples = deque()

        self.total_bytes = 0

        self.peak_bps = 0

        # Per-device tracking
        self.device_total_bytes = defaultdict(int)
        self.device_peak_bps = defaultdict(float)

    def add(self, byte_count, device_id=None, direction="TOTAL"):

        now = time.time()

        self.samples.append(
            (now, byte_count, device_id, direction)
        )

        self.total_bytes += byte_count

        if device_id:
            self.device_total_bytes[device_id] += byte_count

        self._cleanup(now)

        current_bytes = sum(
            size
            for timestamp, size, _, _
            in self.samples
        )

        elapsed = max(
            self.window_seconds,
            0.001,
        )

        current_bps = (
            current_bytes * 8
        ) / elapsed

        if current_bps > self.peak_bps:

            self.peak_bps = current_bps

        # Track per-device speed
        if device_id:
            device_window_bytes = sum(
                size
                for timestamp, size, dev_id, dir_
                in self.samples
                if dev_id == device_id
            )

            device_bps = (
                device_window_bytes * 8
            ) / elapsed

            if device_bps > self.device_peak_bps[device_id]:
                self.device_peak_bps[device_id] = device_bps

    def _cleanup(self, now):

        limit = (
            now - self.window_seconds
        )

        while (
            self.samples
            and self.samples[0][0] < limit
        ):

            self.samples.popleft()

    def current_bps(self):

        now = time.time()

        self._cleanup(now)

        total = sum(
            size
            for _, size, _, _
            in self.samples
        )

        return (
            total * 8
        ) / max(
            self.window_seconds,
            0.001,
        )

    def device_current_bps(self, device_id):
        """Current download+upload speed for a specific device in bps"""
        now = time.time()
        self._cleanup(now)

        device_bytes = sum(
            size
            for timestamp, size, dev_id, _
            in self.samples
            if dev_id == device_id
        )

        return (
            device_bytes * 8
        ) / max(
            self.window_seconds,
            0.001,
        )

    def device_download_bps(self, device_id):
        """Current download speed for a specific device in bps"""
        now = time.time()
        self._cleanup(now)

        device_bytes = sum(
            size
            for timestamp, size, dev_id, direction
            in self.samples
            if dev_id == device_id and direction == "DOWNLOAD"
        )

        return (
            device_bytes * 8
        ) / max(
            self.window_seconds,
            0.001,
        )

    def device_upload_bps(self, device_id):
        """Current upload speed for a specific device in bps"""
        now = time.time()
        self._cleanup(now)

        device_bytes = sum(
            size
            for timestamp, size, dev_id, direction
            in self.samples
            if dev_id == device_id and direction == "UPLOAD"
        )

        return (
            device_bytes * 8
        ) / max(
            self.window_seconds,
            0.001,
        )

    def device_total_bytes(self, device_id):
        return self.device_total_bytes.get(device_id, 0)

    def current_mbps(self):

        return self.current_bps() / 1_000_000

    def peak_mbps(self):

        return self.peak_bps / 1_000_000
