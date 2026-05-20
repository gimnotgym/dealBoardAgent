"""
음성 파일 → 텍스트 변환 (STT) 모듈
Whisper 모델 사용 (로컬 실행)
"""
import tempfile
import os
from pathlib import Path

SUPPORTED_AUDIO = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


def transcribe_audio(uploaded_file) -> str:
    """음성 파일을 텍스트로 변환합니다."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in SUPPORTED_AUDIO:
        return f"[지원하지 않는 오디오 형식: {suffix}]"

    try:
        import whisper
    except ImportError:
        return "[whisper 미설치: pip install openai-whisper]"

    # 임시 파일에 저장 후 Whisper 처리
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, language="ko")
        return result.get("text", "").strip()
    except Exception as e:
        return f"[음성 변환 오류: {e}]"
    finally:
        os.unlink(tmp_path)
