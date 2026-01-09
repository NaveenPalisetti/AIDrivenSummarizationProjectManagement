"""
Transcript Preprocessing Agent
- Chunks, cleans, or filters transcripts for downstream processing.
"""
class TranscriptPreprocessingAgent:
    def process(self, transcripts, chunk_size=500):
        # Example: chunk each transcript into pieces of chunk_size characters
        processed = []
        for t in transcripts:
            t = t.strip()
            if not t:
                continue
            # Simple chunking by character count
            for i in range(0, len(t), chunk_size):
                processed.append(t[i:i+chunk_size])
        return processed
