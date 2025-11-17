class LiveDetector:
    def __init__(self):
        self._state = {}

    def update(self, channel_id: str, current_video_id: str | None):
        prev = self._state.get(channel_id)
        self._state[channel_id] = current_video_id
        changed = prev != current_video_id
        now_live = current_video_id is not None
        return changed, now_live

