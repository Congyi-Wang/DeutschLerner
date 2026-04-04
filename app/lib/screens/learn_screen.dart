import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/tts_service.dart';

class LearnScreen extends StatefulWidget {
  final ApiService api;
  final bool autoStart;
  final Map<String, dynamic>? preloadedChapter;
  const LearnScreen({
    super.key,
    required this.api,
    this.autoStart = false,
    this.preloadedChapter,
  });

  @override
  State<LearnScreen> createState() => _LearnScreenState();
}

class _LearnScreenState extends State<LearnScreen> {
  final _inputCtrl = TextEditingController();
  final _tts = TtsService();
  Map<String, dynamic>? _result;
  Map<String, dynamic>? _level;
  bool _loading = false;
  String? _error;

  // Default suggestions (used when no level info or A1 completed)
  static const _defaultSuggestions = [
    '在超市购物',
    '去餐厅点餐',
    '问路和交通',
    '看医生',
    '租房子',
    '工作面试',
    '德国节日',
    '天气和季节',
  ];

  // Module-specific suggestions
  static const _moduleSuggestions = {
    1: ['打招呼', '自我介绍', '告别用语', '礼貌用语', '认识朋友'],
    2: ['数字练习', '几点了', '星期几', '我的一天', '日常安排'],
    3: ['我的家庭', '兴趣爱好', '周末活动', '运动', '朋友聚会'],
    4: ['超市购物', '餐厅点餐', '食物饮料', '问路', '价格付款'],
    5: ['我的房间', '找房子', '坐公交', '买火车票', '旅行计划'],
    6: ['身体部位', '看医生', '今天天气', '季节和衣服', '邮局银行'],
  };

  List<String> get _suggestions {
    if (_level != null && _level!['module_id'] != null) {
      final moduleId = _level!['module_id'] as int;
      return _moduleSuggestions[moduleId] ?? _defaultSuggestions;
    }
    return _defaultSuggestions;
  }

  @override
  void initState() {
    super.initState();
    _tts.init();
    if (widget.preloadedChapter != null) {
      _result = widget.preloadedChapter;
    } else if (widget.autoStart) {
      _loadLevelThenAutoStart();
    } else {
      _loadLevel();
    }
  }

  Future<void> _loadLevel() async {
    try {
      final lv = await widget.api.getLevel();
      if (mounted) setState(() => _level = lv);
    } catch (_) {}
  }

  Future<void> _loadLevelThenAutoStart() async {
    try {
      final lv = await widget.api.getLevel();
      if (mounted) setState(() => _level = lv);
    } catch (_) {}
    _inputCtrl.text = _suggestions[DateTime.now().day % _suggestions.length];
    _generate();
  }

  @override
  void dispose() {
    _tts.stop();
    _inputCtrl.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    if (_inputCtrl.text.trim().isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });
    try {
      final result = await widget.api.learnTopic(_inputCtrl.text.trim());
      setState(() {
        _result = result;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('学习新主题'),
      ),
      body: _loading
          ? const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('AI正在生成学习内容...',
                      style: TextStyle(color: Colors.grey)),
                ],
              ),
            )
          : _result != null
              ? _buildResult()
              : _buildInput(),
    );
  }

  Widget _buildInput() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('你想学什么？',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        const Text('输入一个话题、场景或语法点',
            style: TextStyle(color: Colors.grey)),
        const SizedBox(height: 16),
        TextField(
          controller: _inputCtrl,
          decoration: InputDecoration(
            hintText: '例如：在超市购物',
            border: const OutlineInputBorder(),
            suffixIcon: IconButton(
              icon: const Icon(Icons.send),
              onPressed: _generate,
            ),
          ),
          onSubmitted: (_) => _generate(),
        ),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Text(_error!, style: const TextStyle(color: Colors.red)),
        ],
        const SizedBox(height: 24),
        const Text('推荐话题', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _suggestions
              .map((s) => ActionChip(
                    label: Text(s),
                    onPressed: () {
                      _inputCtrl.text = s;
                      _generate();
                    },
                  ))
              .toList(),
        ),
      ],
    );
  }

  Widget _buildResult() {
    final vocab = (_result!['vocabulary'] as List?) ?? [];
    final sentences = (_result!['sentences'] as List?) ?? [];
    final grammarAnalysis = _result!['grammar_analysis'];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Title card
        Card(
          color: const Color(0xFF1A1A1A),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(_result!['topic_title_de'] ?? '',
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.bold)),
                    ),
                    IconButton(
                      icon: const Icon(Icons.volume_up, color: Color(0xFFFFCC00)),
                      onPressed: () =>
                          _tts.speak(_result!['topic_title_de'] ?? ''),
                      tooltip: '正常语速',
                    ),
                    IconButton(
                      icon: const Icon(Icons.slow_motion_video, color: Colors.orange),
                      onPressed: () =>
                          _tts.speakSlow(_result!['topic_title_de'] ?? ''),
                      tooltip: '慢速朗读',
                    ),
                  ],
                ),
                Row(
                  children: [
                    if (_result!['module_id'] != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        margin: const EdgeInsets.only(right: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFDD0000),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'A1·M${_result!['module_id']}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                    Expanded(
                      child: Text(_result!['topic_title_cn'] ?? '',
                          style: const TextStyle(
                              color: Color(0xFFFFCC00), fontSize: 16)),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(_result!['summary_cn'] ?? '',
                    style:
                        const TextStyle(color: Colors.white70, fontSize: 14)),
              ],
            ),
          ),
        ),

        // Stats
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            children: [
              Chip(
                  label: Text('+${_result!['vocab_added'] ?? 0} 词汇'),
                  backgroundColor: Colors.green.shade100),
              const SizedBox(width: 8),
              Chip(
                  label: Text('+${_result!['sentences_added'] ?? 0} 句型'),
                  backgroundColor: Colors.blue.shade100),
            ],
          ),
        ),

        // Vocabulary with IPA and TTS
        if (vocab.isNotEmpty) ...[
          const Text('核心词汇',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...vocab.map<Widget>((v) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Flexible(
                                  child: Text(v['german'] ?? '',
                                      style: const TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold)),
                                ),
                                if (v['gender'] != null) ...[
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: Colors.blue.shade50,
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(v['gender'],
                                        style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.blue.shade700)),
                                  ),
                                ],
                              ],
                            ),
                            // IPA phonetics
                            if (v['phonetic'] != null &&
                                v['phonetic'].toString().isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 2),
                                child: Text(v['phonetic'],
                                    style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.purple.shade400,
                                        fontStyle: FontStyle.italic)),
                              ),
                            Text(v['chinese'] ?? '',
                                style:
                                    TextStyle(color: Colors.grey.shade600)),
                            if (v['example_de'] != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text(v['example_de'],
                                    style: const TextStyle(
                                        fontSize: 13,
                                        fontStyle: FontStyle.italic)),
                              ),
                          ],
                        ),
                      ),
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: Icon(Icons.volume_up,
                                color: Colors.blue.shade600, size: 22),
                            onPressed: () => _tts.speak(v['german'] ?? ''),
                            tooltip: '正常语速',
                            constraints: const BoxConstraints(),
                            padding: const EdgeInsets.all(4),
                          ),
                          IconButton(
                            icon: Icon(Icons.slow_motion_video,
                                color: Colors.orange.shade600, size: 18),
                            onPressed: () => _tts.speakSlow(v['german'] ?? ''),
                            tooltip: '慢速朗读',
                            constraints: const BoxConstraints(),
                            padding: const EdgeInsets.all(4),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              )),
        ],

        // Sentences with TTS
        if (sentences.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('重点句型',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...sentences.map<Widget>((s) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(s['german'] ?? '',
                                style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold)),
                          ),
                          IconButton(
                            icon: Icon(Icons.volume_up,
                                color: Colors.blue.shade600, size: 20),
                            onPressed: () => _tts.speak(s['german'] ?? ''),
                            tooltip: '正常语速',
                            constraints: const BoxConstraints(),
                            padding: const EdgeInsets.all(4),
                          ),
                          IconButton(
                            icon: Icon(Icons.slow_motion_video,
                                color: Colors.orange.shade600, size: 18),
                            onPressed: () => _tts.speakSlow(s['german'] ?? ''),
                            tooltip: '慢速朗读',
                            constraints: const BoxConstraints(),
                            padding: const EdgeInsets.all(4),
                          ),
                        ],
                      ),
                      // IPA phonetics for sentence
                      if (s['phonetic'] != null &&
                          s['phonetic'].toString().isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 2, bottom: 4),
                          child: Text(s['phonetic'],
                              style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.purple.shade400,
                                  fontStyle: FontStyle.italic)),
                        ),
                      Text(s['chinese'] ?? '',
                          style: TextStyle(color: Colors.grey.shade600)),
                      if (s['grammar_note'] != null) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.amber.shade50,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.lightbulb,
                                  size: 16, color: Colors.amber.shade700),
                              const SizedBox(width: 6),
                              Expanded(
                                  child: Text(s['grammar_note'],
                                      style: TextStyle(
                                          fontSize: 13,
                                          color: Colors.amber.shade900))),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              )),
        ],

        // Grammar Analysis (new structured section)
        if (grammarAnalysis != null && grammarAnalysis is Map) ...[
          const SizedBox(height: 16),
          Card(
            color: Colors.indigo.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.analytics, size: 20, color: Colors.indigo),
                      SizedBox(width: 8),
                      Text('语法分析',
                          style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                              color: Colors.indigo)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (grammarAnalysis['points'] != null &&
                      grammarAnalysis['points'] is List)
                    ...((grammarAnalysis['points'] as List).map<Widget>((p) =>
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(p['name'] ?? '',
                                  style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                      color: Colors.indigo.shade700)),
                              const SizedBox(height: 4),
                              Text(p['explanation'] ?? '',
                                  style: const TextStyle(fontSize: 13)),
                              if (p['rule'] != null) ...[
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(
                                        color: Colors.indigo.shade100),
                                  ),
                                  child: Text(p['rule'],
                                      style: TextStyle(
                                          fontSize: 12,
                                          fontFamily: 'monospace',
                                          color: Colors.indigo.shade600)),
                                ),
                              ],
                              if (p['examples'] != null &&
                                  p['examples'] is List)
                                ...((p['examples'] as List).map<Widget>((ex) =>
                                    Padding(
                                      padding: const EdgeInsets.only(top: 4),
                                      child: Row(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          const Text('  - ',
                                              style: TextStyle(fontSize: 13)),
                                          Expanded(
                                            child: Text(ex.toString(),
                                                style: const TextStyle(
                                                    fontSize: 13,
                                                    fontStyle:
                                                        FontStyle.italic)),
                                          ),
                                        ],
                                      ),
                                    ))),
                            ],
                          ),
                        ))),
                ],
              ),
            ),
          ),
        ],

        // Grammar tips
        if (_result!['grammar_tips'] != null &&
            _result!['grammar_tips'].toString().isNotEmpty) ...[
          const SizedBox(height: 16),
          Card(
            color: Colors.green.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.school, size: 20),
                      SizedBox(width: 8),
                      Text('语法提示',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(_result!['grammar_tips']),
                ],
              ),
            ),
          ),
        ],

        // Exercise
        if (_result!['exercise'] != null &&
            _result!['exercise'].toString().isNotEmpty) ...[
          const SizedBox(height: 16),
          Card(
            color: Colors.purple.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.edit, size: 20),
                      SizedBox(width: 8),
                      Text('练习',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(_result!['exercise']),
                ],
              ),
            ),
          ),
        ],

        const SizedBox(height: 24),
        ElevatedButton.icon(
          onPressed: () {
            setState(() {
              _result = null;
              _inputCtrl.clear();
            });
          },
          icon: const Icon(Icons.add),
          label: const Text('学习新主题'),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}
