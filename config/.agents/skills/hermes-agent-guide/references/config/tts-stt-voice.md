# TTS/STT/ボイスモード設定

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#tts-configuration

## TTS 設定

```yaml
tts:
  provider: "edge"              # edge | elevenlabs | openai | minimax | neutts | mistral | gemini | xai
  speed: 1.0
  edge:
    voice: "en-US-AriaNeural"
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"
```

## STT 設定

```yaml
stt:
  provider: "local"             # local | groq | openai | mistral
  local:
    model: "base"               # tiny | base | small | medium | large-v3
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
