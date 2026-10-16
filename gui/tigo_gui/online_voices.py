"""Curated Microsoft Edge voice IDs; catalog browsing never sends reply text."""

VOICES = {
    # Multilingual voices are intentionally offered for Russian; the native
    # Dmitry voice was listed but returned no audio in live service probes.
    'en-US-AndrewMultilingualNeural': {'name': 'Andrew Multilingual', 'locale': 'ru_RU', 'gender': 'Male'},
    'en-US-BrianMultilingualNeural': {'name': 'Brian Multilingual', 'locale': 'ru_RU', 'gender': 'Male'},
    'ru-RU-SvetlanaNeural': {'name': 'Svetlana Online', 'locale': 'ru_RU', 'gender': 'Female'},
    'en-US-GuyNeural': {'name': 'Guy Online', 'locale': 'en_US', 'gender': 'Male'},
    'en-US-AriaNeural': {'name': 'Aria Online', 'locale': 'en_US', 'gender': 'Female'},
}
