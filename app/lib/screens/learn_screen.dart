import 'package:flutter/material.dart';
import '../services/api_service.dart';

class LearnScreen extends StatefulWidget {
  final ApiService api;
  final bool autoStart;
  const LearnScreen({super.key, required this.api, this.autoStart = false});

  @override
  State<LearnScreen> createState() => _LearnScreenState();
}

class _LearnScreenState extends State<LearnScreen> {
  final _inputCtrl = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  final _suggestions = [
    '在超市购物',
    '去餐厅点餐',
    '问路和交通',
    '看医生',
    '租房子',
    '工作面试',
    '德国节日',
    '天气和季节',
  ];

  @override
  void initState() {
    super.initState();
    if (widget.autoStart) {
      _inputCtrl.text = _suggestions[DateTime.now().day % _suggestions.length];
      _generate();
    }
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
                  Text('AI正在生成学习内容...', style: TextStyle(color: Colors.grey)),
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

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Title
        Card(
          color: const Color(0xFF1A1A1A),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_result!['topic_title_de'] ?? '',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold)),
                Text(_result!['topic_title_cn'] ?? '',
                    style: const TextStyle(color: Color(0xFFFFCC00), fontSize: 16)),
                const SizedBox(height: 8),
                Text(_result!['summary_cn'] ?? '',
                    style: const TextStyle(color: Colors.white70, fontSize: 14)),
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

        // Vocabulary
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
                                Text(v['german'] ?? '',
                                    style: const TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold)),
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
                    ],
                  ),
                ),
              )),
        ],

        // Sentences
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
                      Text(s['german'] ?? '',
                          style: const TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
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
