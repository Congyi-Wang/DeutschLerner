import 'package:flutter_tts/flutter_tts.dart';

class TtsService {
  static final TtsService _instance = TtsService._();
  factory TtsService() => _instance;
  TtsService._();

  final FlutterTts _tts = FlutterTts();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
    await _tts.setLanguage('de-DE');
    await _tts.setPitch(1.0);
    _initialized = true;
  }

  Future<void> speak(String text) async {
    await init();
    await _tts.stop();
    await _tts.setSpeechRate(0.45);
    await _tts.speak(text);
  }

  Future<void> speakSlow(String text) async {
    await init();
    await _tts.stop();
    await _tts.setSpeechRate(0.2);
    await _tts.speak(text);
  }

  Future<void> stop() async {
    await _tts.stop();
  }
}
