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
    await _tts.setVolume(1.0);

    // Try to select a high-quality German voice
    try {
      final voices = await _tts.getVoices;
      if (voices is List) {
        // Prefer Google or Samsung high-quality German voices
        final germanVoices = voices
            .where((v) =>
                v is Map &&
                (v['locale']?.toString().startsWith('de') == true ||
                 v['name']?.toString().toLowerCase().contains('german') == true))
            .toList();

        if (germanVoices.isNotEmpty) {
          // Prefer network/high-quality voices over local ones
          Map? bestVoice;
          for (final v in germanVoices) {
            if (v is Map) {
              final name = v['name']?.toString().toLowerCase() ?? '';
              // Prefer voices with these quality indicators
              if (name.contains('network') ||
                  name.contains('enhanced') ||
                  name.contains('premium') ||
                  name.contains('wavenet') ||
                  name.contains('neural')) {
                bestVoice = v;
                break;
              }
            }
          }
          // Fall back to any de-DE voice
          bestVoice ??= germanVoices.first as Map?;

          if (bestVoice != null && bestVoice['name'] != null) {
            await _tts.setVoice({
              'name': bestVoice['name'].toString(),
              'locale': bestVoice['locale']?.toString() ?? 'de-DE',
            });
          }
        }
      }
    } catch (_) {
      // Voice selection failed, use default
    }

    _initialized = true;
  }

  Future<void> speak(String text) async {
    await init();
    await _tts.stop();
    await _tts.setSpeechRate(0.5);
    await _tts.speak(text);
  }

  Future<void> speakSlow(String text) async {
    await init();
    await _tts.stop();
    await _tts.setSpeechRate(0.25);
    await _tts.speak(text);
  }

  Future<void> stop() async {
    await _tts.stop();
  }
}
