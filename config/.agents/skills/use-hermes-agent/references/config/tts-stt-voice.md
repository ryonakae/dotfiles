# TTS/STT/ボイスモード設定

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#tts-configuration

## TTS 設定

```yaml
tts:
  provider: "edge"              # edge | elevenlabs | openai | minimax | neutts | mistral | gemini | xai | piper
  speed: 1.0
  auto_speech_tags: false       # xAI TTS の natural pauses（v0.15.0、opt-in）
  edge:
    voice: "en-US-AriaNeural"
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"
  piper:                         # ローカル TTS（v0.12.0）
    model_path: ~/.hermes/voices/<model>.onnx
  providers:                     # pluggable TTS registry（v0.12.0）
    <custom-name>:
      type: plugin
```

`register_tts_provider()`（v0.15.0）でプラグインから TTS provider を登録可能。

## STT 設定

```yaml
stt:
  provider: "local"             # local | groq | openai | mistral
  local:
    model: "base"               # tiny | base | small | medium | large-v3
  providers:                     # pluggable STT registry（v0.15.0、register_transcription_provider()）
    <custom-name>:
      type: plugin
```

## ボイスモード設定

```yaml
voice:
  record_key: "ctrl+b"
  max_recording_seconds: 120
  auto_tts: false
  silence_threshold: 200
  silence_duration: 3.0
```
