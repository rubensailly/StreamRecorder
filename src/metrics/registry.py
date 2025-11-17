from prometheus_client import Counter, Gauge, Histogram

poll_duration_seconds = Histogram('poll_duration_seconds', 'Duration of a polling cycle')
poll_errors_total = Counter('poll_errors_total', 'Number of poll errors')
last_poll_timestamp = Gauge('last_poll_timestamp', 'Unix timestamp of last successful poll')

active_recordings = Gauge('active_recordings', 'Number of currently active recording sessions')
channel_state = Gauge('channel_state', 'State of channel (0=idle,1=recording,2=stopping,3=error,4=waiting)', ['channel'])
recording_segments_total = Counter('recording_segments_total', 'Total segments produced', ['channel', 'video'])
recording_bytes_total = Counter('recording_bytes_total', 'Total bytes recorded', ['channel', 'video'])
recording_restarts_total = Counter('recording_restarts_total', 'Number of ffmpeg restarts', ['channel', 'video'])

disk_used_bytes = Gauge('disk_used_bytes', 'Used disk bytes for recording root')
disk_free_bytes = Gauge('disk_free_bytes', 'Free disk bytes for recording root')

channels_total = Gauge('channels_total', 'Total number of channels monitored')

CHANNEL_STATE_CODES = {
    'idle': 0,
    'recording': 1,
    'stopping': 2,
    'error': 3,
    'waiting': 4,
}
