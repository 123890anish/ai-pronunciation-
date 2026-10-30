"""
Assessment Upload and Recording Forms.
"""
from django import forms
from configure import get_config
from audio.validators import validate_audio_file


class AudioSubmissionForm(forms.Form):
    audio_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "accept": "audio/*,.wav,.mp3,.m4a,.webm,.ogg",
            "id": "audioFileInput",
        }),
        label="Audio Recording or File",
    )

    def clean_audio_file(self):
        audio = self.cleaned_data.get("audio_file")
        if not audio:
            raise forms.ValidationError("No audio file provided.")

        is_valid, error = validate_audio_file(
            file_or_path=audio,
            filename=audio.name,
            size_bytes=audio.size,
            content_type=audio.content_type,
        )
        if not is_valid:
            raise forms.ValidationError(error)

        return audio
