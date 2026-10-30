"""
Centralized Configuration Loader for Pronunciation Assessment.
Merges configure.yaml with environment variables from .env or os.environ.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass


BASE_DIR = Path(__file__).resolve().parent

# Automatically load .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class ConfigurationError(Exception):
    """Raised when configuration values are missing, invalid, or contradictory."""
    pass


@dataclass
class AppConfig:
    name: str = "Pronunciation & Grammar Assessment"
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    debug: bool = True
    secret_key: str = "django-insecure-default-change-in-production"
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])


@dataclass
class AssessmentConfig:
    grammar_correction_enabled: bool = True
    feedback_enabled: bool = True
    pronunciation_scoring_enabled: bool = False
    fluency_scoring_enabled: bool = False
    grammar_provider: str = "ollama"  # 'ollama' | 't5' | 'rule_based'
    stt_provider: str = "whisper"     # 'whisper' | 'mock'
    whisper_model: str = "base"


@dataclass
class AudioConfig:
    max_upload_mb: int = 20
    max_duration_seconds: int = 180
    allowed_extensions: List[str] = field(
        default_factory=lambda: ["wav", "mp3", "m4a", "webm", "ogg"]
    )
    allowed_mime_types: List[str] = field(
        default_factory=lambda: [
            "audio/wav", "audio/x-wav", "audio/mpeg",
            "audio/mp3", "audio/mp4", "audio/x-m4a",
            "audio/webm", "audio/ogg"
        ]
    )
    media_root: str = "media"


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "qwen2.5:1.5b"
    url: str = "http://localhost:11434/api/generate"
    timeout_seconds: int = 60
    temperature: float = 0.2


@dataclass
class ScoringConfig:
    grammar_weight: float = 100.0
    pronunciation_weight: float = 0.0
    fluency_weight: float = 0.0


@dataclass
class MasterConfig:
    app: AppConfig = field(default_factory=AppConfig)
    assessment: AssessmentConfig = field(default_factory=AssessmentConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    database_url: str = "sqlite:///db.sqlite3"
    log_level: str = "INFO"

    def validate(self) -> None:
        """Validate config consistency."""
        if self.audio.max_upload_mb <= 0:
            raise ConfigurationError("audio.max_upload_mb must be a positive integer.")
        if self.audio.max_duration_seconds <= 0:
            raise ConfigurationError("audio.max_duration_seconds must be positive.")
        if self.llm.timeout_seconds <= 0:
            raise ConfigurationError("llm.timeout_seconds must be positive.")

        # Check weights for active metrics
        active_weights = 0.0
        if self.assessment.grammar_correction_enabled:
            active_weights += self.scoring.grammar_weight
        if self.assessment.pronunciation_scoring_enabled:
            active_weights += self.scoring.pronunciation_weight
        if self.assessment.fluency_scoring_enabled:
            active_weights += self.scoring.fluency_weight

        if active_weights <= 0:
            raise ConfigurationError("At least one enabled scoring metric must have a weight > 0.")


_CACHED_CONFIG: Optional[MasterConfig] = None


def load_yaml_config(yaml_file_path: Path) -> Dict[str, Any]:
    """Safely loads YAML configuration file without throwing if missing."""
    if not yaml_file_path.exists():
        return {}
    if yaml is None:
        # Fallback if pyyaml is not installed
        return {}
    try:
        with open(yaml_file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        raise ConfigurationError(f"Failed to parse configuration YAML at {yaml_file_path}: {exc}") from exc


def get_config(reload: bool = False) -> MasterConfig:
    """
    Centralized getter for application configuration.
    Priority: Environment Variables > configure.yaml > Dataclass Defaults.
    """
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None and not reload:
        return _CACHED_CONFIG

    yaml_data = load_yaml_config(BASE_DIR / "configure.yaml")

    app_data = yaml_data.get("app", {})
    assessment_data = yaml_data.get("assessment", {})
    audio_data = yaml_data.get("audio", {})
    llm_data = yaml_data.get("llm", {})
    scoring_data = yaml_data.get("scoring", {})

    # 1. App
    debug_val = os.getenv("DJANGO_DEBUG")
    debug_bool = debug_val.lower() in ("1", "true", "yes") if debug_val is not None else True
    allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS")
    allowed_hosts = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()] if allowed_hosts_env else ["localhost", "127.0.0.1", "0.0.0.0"]

    app_cfg = AppConfig(
        name=app_data.get("name", "Pronunciation & Grammar Assessment"),
        language=app_data.get("language", "en"),
        timezone=app_data.get("timezone", "Asia/Kolkata"),
        debug=debug_bool,
        secret_key=os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-dev-key"),
        allowed_hosts=allowed_hosts,
    )

    # 2. Assessment
    grammar_provider = os.getenv("GRAMMAR_CORRECTION_PROVIDER", assessment_data.get("grammar_provider", "ollama"))
    stt_provider = os.getenv("SPEECH_RECOGNITION_PROVIDER", assessment_data.get("stt_provider", "whisper"))
    whisper_model = os.getenv("WHISPER_MODEL", assessment_data.get("whisper_model", "base"))

    assessment_cfg = AssessmentConfig(
        grammar_correction_enabled=assessment_data.get("grammar_correction_enabled", True),
        feedback_enabled=assessment_data.get("feedback_enabled", True),
        pronunciation_scoring_enabled=assessment_data.get("pronunciation_scoring_enabled", False),
        fluency_scoring_enabled=assessment_data.get("fluency_scoring_enabled", False),
        grammar_provider=grammar_provider,
        stt_provider=stt_provider,
        whisper_model=whisper_model,
    )

    # 3. Audio
    max_mb_env = os.getenv("MAX_AUDIO_UPLOAD_MB")
    max_upload_mb = int(max_mb_env) if max_mb_env else audio_data.get("max_upload_mb", 20)
    max_dur_env = os.getenv("MAX_RECORDING_DURATION_SECONDS")
    max_dur = int(max_dur_env) if max_dur_env else audio_data.get("max_duration_seconds", 180)
    media_root = os.getenv("MEDIA_ROOT", "media")

    audio_cfg = AudioConfig(
        max_upload_mb=max_upload_mb,
        max_duration_seconds=max_dur,
        allowed_extensions=audio_data.get("allowed_extensions", ["wav", "mp3", "m4a", "webm", "ogg"]),
        allowed_mime_types=audio_data.get("allowed_mime_types", [
            "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3",
            "audio/mp4", "audio/x-m4a", "audio/webm", "audio/ogg"
        ]),
        media_root=media_root,
    )

    # 4. LLM
    llm_url = os.getenv("OLLAMA_URL", llm_data.get("url", "http://localhost:11434/api/generate"))
    llm_model = os.getenv("OLLAMA_MODEL", llm_data.get("model", "qwen2.5:1.5b"))
    timeout_env = os.getenv("OLLAMA_TIMEOUT")
    llm_timeout = int(timeout_env) if timeout_env else int(llm_data.get("timeout_seconds", 60))

    llm_cfg = LLMConfig(
        provider=llm_data.get("provider", "ollama"),
        model=llm_model,
        url=llm_url,
        timeout_seconds=llm_timeout,
        temperature=float(llm_data.get("temperature", 0.2)),
    )

    # 5. Scoring
    scoring_cfg = ScoringConfig(
        grammar_weight=float(scoring_data.get("grammar_weight", 100.0)),
        pronunciation_weight=float(scoring_data.get("pronunciation_weight", 0.0)),
        fluency_weight=float(scoring_data.get("fluency_weight", 0.0)),
    )

    config = MasterConfig(
        app=app_cfg,
        assessment=assessment_cfg,
        audio=audio_cfg,
        llm=llm_cfg,
        scoring=scoring_cfg,
        database_url=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

    config.validate()
    _CACHED_CONFIG = config
    return _CACHED_CONFIG
