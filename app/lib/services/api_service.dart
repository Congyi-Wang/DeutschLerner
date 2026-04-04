import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();
  static const _serverKey = 'server_url';
  static const _apiKeyKey = 'api_key';

  String _baseUrl = '';
  String _apiKey = '';

  Future<void> init() async {
    _baseUrl = await _storage.read(key: _serverKey) ?? '';
    _apiKey = await _storage.read(key: _apiKeyKey) ?? '';
  }

  bool get isConfigured => _baseUrl.isNotEmpty && _apiKey.isNotEmpty;

  Future<void> saveConfig(String serverUrl, String apiKey) async {
    // Normalize URL
    serverUrl = serverUrl.trimRight();
    if (serverUrl.endsWith('/')) {
      serverUrl = serverUrl.substring(0, serverUrl.length - 1);
    }
    _baseUrl = serverUrl;
    _apiKey = apiKey;
    await _storage.write(key: _serverKey, value: serverUrl);
    await _storage.write(key: _apiKeyKey, value: apiKey);
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'X-API-Key': _apiKey,
      };

  Future<Map<String, dynamic>> _get(String path) async {
    final resp = await http.get(
      Uri.parse('$_baseUrl$path'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception('API error ${resp.statusCode}: ${resp.body}');
    }
    return jsonDecode(resp.body);
  }

  Future<Map<String, dynamic>> _post(String path,
      {Map<String, dynamic>? body}) async {
    final resp = await http.post(
      Uri.parse('$_baseUrl$path'),
      headers: _headers,
      body: body != null ? jsonEncode(body) : null,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw Exception('API error ${resp.statusCode}: ${resp.body}');
    }
    return jsonDecode(resp.body);
  }

  Future<Map<String, dynamic>> _patch(String path,
      {Map<String, dynamic>? body}) async {
    final resp = await http.patch(
      Uri.parse('$_baseUrl$path'),
      headers: _headers,
      body: body != null ? jsonEncode(body) : null,
    );
    if (resp.statusCode != 200) {
      throw Exception('API error ${resp.statusCode}: ${resp.body}');
    }
    return jsonDecode(resp.body);
  }

  // Health check
  Future<bool> testConnection() async {
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/api/v1/health'))
          .timeout(const Duration(seconds: 5));
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // Daily Plan
  Future<Map<String, dynamic>> getDailyPlan() => _get('/api/v1/daily-plan');

  // Learning
  Future<Map<String, dynamic>> learnTopic(String input) =>
      _post('/api/v1/learn', body: {'input': input});

  Future<Map<String, dynamic>> reviewVocabulary({int count = 10}) =>
      _post('/api/v1/learn/review', body: {'count': count});

  // Vocabulary
  Future<Map<String, dynamic>> getVocabulary(
          {String? status, int limit = 100, int offset = 0}) =>
      _get(
          '/api/v1/vocabulary?limit=$limit&offset=$offset${status != null ? '&status=$status' : ''}');

  Future<Map<String, dynamic>> updateVocabulary(
          int id, Map<String, dynamic> updates) =>
      _patch('/api/v1/vocabulary/$id', body: updates);

  Future<Map<String, dynamic>> getVocabularyStats() =>
      _get('/api/v1/vocabulary/stats');

  // Chapter (pre-generated daily content)
  Future<Map<String, dynamic>> getTodayChapter() =>
      _get('/api/v1/chapter/today');

  Future<Map<String, dynamic>> getChapterByDate(String date) =>
      _get('/api/v1/chapter/$date');

  // Level / Progress
  Future<Map<String, dynamic>> getLevel() => _get('/api/v1/level');

  // Grammar exercises
  Future<Map<String, dynamic>> getGrammarExercises() =>
      _get('/api/v1/grammar/exercises');

  // Stats
  Future<Map<String, dynamic>> getStats() => _get('/api/v1/memory/stats');
}
