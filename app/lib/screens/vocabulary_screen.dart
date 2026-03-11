import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/tts_service.dart';

class VocabularyScreen extends StatefulWidget {
  final ApiService api;
  const VocabularyScreen({super.key, required this.api});

  @override
  State<VocabularyScreen> createState() => _VocabularyScreenState();
}

class _VocabularyScreenState extends State<VocabularyScreen>
    with SingleTickerProviderStateMixin {
  final _tts = TtsService();
  late TabController _tabCtrl;
  List _allItems = [];
  List _knownItems = [];
  List _learningItems = [];
  List _unknownItems = [];
  bool _loading = true;
  Map<String, dynamic> _stats = {};

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 4, vsync: this);
    _tts.init();
    _loadData();
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
      final results = await Future.wait([
        widget.api.getVocabulary(limit: 500),
        widget.api.getVocabularyStats(),
      ]);
      final all = (results[0]['items'] as List?) ?? [];
      setState(() {
        _allItems = all;
        _knownItems = all.where((v) => v['status'] == 'known').toList();
        _learningItems = all.where((v) => v['status'] == 'learning').toList();
        _unknownItems = all.where((v) => v['status'] == 'unknown').toList();
        _stats = results[1] as Map<String, dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _updateStatus(int id, String status) async {
    try {
      await widget.api.updateVocabulary(id, {'status': status});
      await _loadData();
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('词汇本'),
        bottom: TabBar(
          controller: _tabCtrl,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white60,
          indicatorColor: const Color(0xFFFFCC00),
          tabs: [
            Tab(text: '全部 (${_allItems.length})'),
            Tab(text: '未学 (${_unknownItems.length})'),
            Tab(text: '学习 (${_learningItems.length})'),
            Tab(text: '掌握 (${_knownItems.length})'),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabCtrl,
              children: [
                _buildList(_allItems),
                _buildList(_unknownItems),
                _buildList(_learningItems),
                _buildList(_knownItems),
              ],
            ),
    );
  }

  Widget _buildList(List items) {
    if (items.isEmpty) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.book, size: 48, color: Colors.grey),
            SizedBox(height: 8),
            Text('暂无词汇', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: items.length,
        itemBuilder: (_, i) {
          final v = items[i];
          return Card(
            margin: const EdgeInsets.only(bottom: 4),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: [
                  // TTS buttons
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      InkWell(
                        onTap: () => _tts.speak(v['german'] ?? ''),
                        child: Icon(Icons.volume_up,
                            color: Colors.blue.shade600, size: 22),
                      ),
                      const SizedBox(height: 4),
                      InkWell(
                        onTap: () => _tts.speakSlow(v['german'] ?? ''),
                        child: Icon(Icons.slow_motion_video,
                            color: Colors.orange.shade600, size: 18),
                      ),
                    ],
                  ),
                  const SizedBox(width: 12),
                  // Word info
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Flexible(
                              child: Text(v['german'] ?? '',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 16)),
                            ),
                            if (v['gender'] != null) ...[
                              const SizedBox(width: 6),
                              Text(v['gender'],
                                  style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.blue.shade400)),
                            ],
                          ],
                        ),
                        // IPA phonetics
                        if (v['phonetic'] != null &&
                            v['phonetic'].toString().isNotEmpty)
                          Text(v['phonetic'],
                              style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.purple.shade400,
                                  fontStyle: FontStyle.italic)),
                        Text(v['chinese'] ?? '',
                            style: TextStyle(
                                fontSize: 14, color: Colors.grey.shade600)),
                      ],
                    ),
                  ),
                  // Status menu
                  PopupMenuButton<String>(
                    icon: _statusIcon(v['status']),
                    onSelected: (s) => _updateStatus(v['id'], s),
                    itemBuilder: (_) => [
                      const PopupMenuItem(
                          value: 'unknown',
                          child: Row(children: [
                            Icon(Icons.circle, color: Colors.red, size: 14),
                            SizedBox(width: 8),
                            Text('未学'),
                          ])),
                      const PopupMenuItem(
                          value: 'learning',
                          child: Row(children: [
                            Icon(Icons.circle, color: Colors.orange, size: 14),
                            SizedBox(width: 8),
                            Text('学习中'),
                          ])),
                      const PopupMenuItem(
                          value: 'known',
                          child: Row(children: [
                            Icon(Icons.circle, color: Colors.green, size: 14),
                            SizedBox(width: 8),
                            Text('已掌握'),
                          ])),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _statusIcon(String? status) {
    switch (status) {
      case 'known':
        return const Icon(Icons.check_circle, color: Colors.green, size: 20);
      case 'learning':
        return const Icon(Icons.pending, color: Colors.orange, size: 20);
      default:
        return const Icon(Icons.circle_outlined, color: Colors.red, size: 20);
    }
  }
}
