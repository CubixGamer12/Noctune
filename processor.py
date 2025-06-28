import subprocess
import os
import tempfile

def process_audio(input_path, output_path=None, pitch=1.25, speed=1.1, reverb=0, bass=0):
    """
    Processes an audio file with given effects and saves it to a specified output path.
    If output_path is None, it creates and returns a temporary file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    # Tworzenie ścieżki wyjściowej, jeśli nie została podana
    if output_path is None:
        # Użyj modułu tempfile do stworzenia bezpiecznego pliku tymczasowego
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        output_path = temp_file.name
        temp_file.close()
    
    atempo = speed / pitch
    filters = [f"asetrate=44100*{pitch}", f"atempo={atempo}"]

    if reverb > 0:
        delay = int(60 + (reverb / 100) * 440)
        decay = round(0.3 + (reverb / 100) * 0.6, 2)
        filters.append(f"aecho=0.8:0.9:{delay}:{decay}")

    if bass > 0:
        bass_gain = max(0, min(bass, 30))
        filters.append(f"bass=g={bass_gain}:f=110:w=0.5")

    filter_chain = ",".join(filters)
    
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-filter:a', filter_chain,
        '-vn', output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr.decode()}")

    return output_path