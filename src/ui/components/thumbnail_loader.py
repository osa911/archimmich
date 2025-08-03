from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from queue import Queue
from threading import Lock

class ThumbnailLoader(QObject):
    thumbnail_loaded = pyqtSignal(str, QPixmap)  # asset_id, pixmap

    def __init__(self, api_manager):
        super().__init__()
        self.api_manager = api_manager
        self.queue = Queue()
        self.active = True
        self.lock = Lock()

        # Start worker thread
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.process_queue)
        self.thread.start()

    def add_to_queue(self, asset_id):
        """Add an asset ID to the thumbnail loading queue."""
        self.queue.put(asset_id)

    def process_queue(self):
        """Process the thumbnail loading queue."""
        while self.active:
            try:
                asset_id = self.queue.get(timeout=1)  # 1 second timeout
                with self.lock:
                    if not self.active:
                        break

                    try:
                        response = self.api_manager.get(f"/assets/{asset_id}/thumbnail", expected_type=None)
                        if response and not isinstance(response, dict):
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            self.thumbnail_loaded.emit(asset_id, pixmap)
                    except Exception as e:
                        print(f"Error loading thumbnail for {asset_id}: {str(e)}")

            except Exception:
                # Queue.get timeout, continue loop
                continue

    def stop(self):
        """Stop the thumbnail loader thread."""
        with self.lock:
            self.active = False
        self.thread.quit()
        self.thread.wait()