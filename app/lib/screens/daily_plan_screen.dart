import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/tts_service.dart';
import 'learn_screen.dart';

class DailyPlanScreen extends StatefulWidget {
  final ApiService api;
  const DailyPlanScreen({super.key, required this.api});

  @override
  State<DailyPlanScreen> createState() => _DailyPlanScreenState();
}

class _DailyPlanScreenState extends State<DailyPlanScreen> {
  Map<String, dynamic>? _plan;
  Map<String, dynamic>? _chapter;
  Map<String, dynamic>? _level;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // Load plan, chapter, and level in parallel
      final results = await Future.wait([
        widget.api.getDailyPlan(),
        widget.api.getTodayChapter().catchError((_) => <String, dynamic>{}),
        widget.api.getLevel().catchError((_) => <String, dynamic>{}),
      ]);
      setState(() {
        _plan = results[0];
        final ch = results[1];
        if (ch.isNotEmpty && ch['available'] == true) {
          _chapter = ch;
        }
        final lv = results[2];
        if (lv.isNotEmpty && lv['level'] != null) {
          _level = lv;
        }
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  IconData _taskIcon(String type) {
    switch (type) {
      case 'vocab_review':
        return Icons.replay;
      case 'forgotten_review':
        return Icons.psychology;
      case 'new_topic':
        return Icons.auto_awesome;
      case 'sentence_practice':
        return Icons.short_text;
      case 'quiz':
        return Icons.quiz;
      default:
        return Icons.task;
    }
  }

  Color _taskColor(String type) {
    switch (type) {
      case 'vocab_review':
        return const Color(0xFF2196F3);
      case 'forgotten_review':
        return const Color(0xFFFF9800);
      case 'new_topic':
        return const Color(0xFFDD0000);
      case 'sentence_practice':
        return const Color(0xFF4CAF50);
      case 'quiz':
        return const Color(0xFF9C27B0);
      default:
        return Colors.grey;
    }
  }

  void _openTask(Map<String, dynamic> task) {
    final type = task['type'] as String;

    if (type == 'new_topic') {
      // If we have a pre-generated chapter, use it
      if (_chapter != null) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => LearnScreen(
              api: widget.api,
              preloadedChapter: _chapter,
            ),
          ),
        );
      } else {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => LearnScreen(api: widget.api, autoStart: true),
          ),
        );
      }
      return;
    }

    if (type == 'vocab_review' || type == 'forgotten_review') {
      _showVocabReview(task);
      return;
    }

    if (type == 'sentence_practice') {
      _showSentencePractice(task);
      return;
    }

    if (type == 'quiz') {
      _showQuiz(task);
      return;
    }
  }

  void _showVocabReview(Map<String, dynamic> task) {
    final items = (task['data']['items'] as List?) ?? [];
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _ReviewPage(
          title: task['title_cn'] ?? '复习',
          items: items,
          api: widget.api,
        ),
      ),
    );
  }

  void _showSentencePractice(Map<String, dynamic> task) {
    final items = (task['data']['items'] as List?) ?? [];
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        builder: (_, ctrl) => _SentencePracticeSheet(
          controller: ctrl,
          title: task['title_cn'] ?? '句型练习',
          items: items,
        ),
      ),
    );
  }

  void _showQuiz(Map<String, dynamic> task) {
    final items = (task['data']['items'] as List?) ?? [];
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _QuizPage(items: items),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 28,
              height: 19,
              margin: const EdgeInsets.only(right: 8),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(3),
              ),
              child: Column(
                children: [
                  Expanded(child: Container(color: const Color(0xFF1A1A1A))),
                  Expanded(child: Container(color: const Color(0xFFDD0000))),
                  Expanded(child: Container(color: const Color(0xFFFFCC00))),
                ],
              ),
            ),
            const Text('DeutschLerner'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAll,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!, style: const TextStyle(color: Colors.red)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                          onPressed: _loadAll, child: const Text('重试')),
                    ],
                  ),
                )
              : _buildPlan(),
    );
  }

  Widget _buildPlan() {
    final greeting = _plan?['greeting'] ?? '';
    final tasks = (_plan?['tasks'] as List?) ?? [];
    final totalMin = _plan?['total_minutes'] ?? 0;
    final stats = _plan?['stats'] ?? {};
    final vocabStats = stats['vocabulary'] ?? {};

    return RefreshIndicator(
      onRefresh: _loadAll,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Pre-generated chapter banner
          if (_chapter != null) ...[
            Card(
              color: Colors.green.shade50,
              child: ListTile(
                leading: const Icon(Icons.auto_stories, color: Colors.green),
                title: Text(_chapter!['topic_title_de'] ?? '今日课程已就绪'),
                subtitle: Text(_chapter!['topic_title_cn'] ?? '点击开始学习'),
                trailing:
                    const Icon(Icons.chevron_right, color: Colors.green),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => LearnScreen(
                        api: widget.api,
                        preloadedChapter: _chapter,
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 8),
          ],

          // Level progress card
          if (_level != null && _level!['module_id'] != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFFDD0000),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            _level!['level'] ?? 'A1',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            '模块${_level!['module_id']}: ${_level!['module_name_cn'] ?? ''}',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                            ),
                          ),
                        ),
                        Text(
                          '${_level!['current_module_num']} / ${_level!['total_modules']}',
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: (_level!['progress_percent'] ?? 0) / 100.0,
                        minHeight: 8,
                        backgroundColor: Colors.grey.shade200,
                        valueColor: const AlwaysStoppedAnimation<Color>(
                            Color(0xFFDD0000)),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${_level!['vocab_count'] ?? 0} / ${_level!['target_vocab'] ?? 0} 词汇',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
          ],

          // Greeting card
          Card(
            color: const Color(0xFF1A1A1A),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(greeting,
                      style:
                          const TextStyle(color: Colors.white, fontSize: 16)),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.timer,
                          color: Color(0xFFFFCC00), size: 18),
                      const SizedBox(width: 4),
                      Text('$totalMin 分钟',
                          style: const TextStyle(
                              color: Color(0xFFFFCC00),
                              fontWeight: FontWeight.bold)),
                      const SizedBox(width: 16),
                      const Icon(Icons.book,
                          color: Color(0xFFFFCC00), size: 18),
                      const SizedBox(width: 4),
                      Text('${tasks.length} 个任务',
                          style: const TextStyle(
                              color: Color(0xFFFFCC00),
                              fontWeight: FontWeight.bold)),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Stats bar
          if ((vocabStats['total'] ?? 0) > 0) ...[
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _statBadge('总词汇', vocabStats['total'] ?? 0, Colors.grey),
                    _statBadge(
                        '已掌握', vocabStats['known'] ?? 0, Colors.green),
                    _statBadge(
                        '学习中', vocabStats['learning'] ?? 0, Colors.orange),
                    _statBadge(
                        '未学', vocabStats['unknown'] ?? 0, Colors.red),
                  ],
                ),
              ),
            ),
          ],

          const SizedBox(height: 16),
          const Text('今日任务',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),

          // Tasks
          ...tasks.map<Widget>((t) {
            final type = t['type'] as String;
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: _taskColor(type).withAlpha(30),
                  child: Icon(_taskIcon(type), color: _taskColor(type)),
                ),
                title: Text(t['title_cn'] ?? t['title'] ?? ''),
                subtitle: Text('${t['duration_minutes']} 分钟'),
                trailing:
                    const Icon(Icons.chevron_right, color: Colors.grey),
                onTap: () => _openTask(t),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _statBadge(String label, int value, Color color) {
    return Column(
      children: [
        Text('$value',
            style: TextStyle(
                fontSize: 20, fontWeight: FontWeight.bold, color: color)),
        Text(label,
            style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
      ],
    );
  }
}

// --- Sentence Practice Sheet with TTS ---
class _SentencePracticeSheet extends StatelessWidget {
  final ScrollController controller;
  final String title;
  final List items;
  final _tts = TtsService();

  _SentencePracticeSheet({
    required this.controller,
    required this.title,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: controller,
      padding: const EdgeInsets.all(16),
      itemCount: items.length + 1,
      itemBuilder: (_, i) {
        if (i == 0) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(title,
                style: const TextStyle(
                    fontSize: 20, fontWeight: FontWeight.bold)),
          );
        }
        final s = items[i - 1];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(s['german'] ?? '',
                          style: const TextStyle(
                              fontSize: 18, fontWeight: FontWeight.bold)),
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
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text(s['phonetic'],
                        style: TextStyle(
                            fontSize: 12,
                            color: Colors.purple.shade400,
                            fontStyle: FontStyle.italic)),
                  ),
                Text(s['chinese'] ?? '',
                    style: TextStyle(color: Colors.grey.shade600)),
                if (s['grammar_notes'] != null) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(s['grammar_notes'],
                        style: TextStyle(
                            fontSize: 13, color: Colors.blue.shade700)),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}

// --- Vocab Review Page with TTS ---
class _ReviewPage extends StatefulWidget {
  final String title;
  final List items;
  final ApiService api;

  const _ReviewPage(
      {required this.title, required this.items, required this.api});

  @override
  State<_ReviewPage> createState() => _ReviewPageState();
}

class _ReviewPageState extends State<_ReviewPage> {
  final _tts = TtsService();
  int _currentIndex = 0;
  bool _showAnswer = false;

  @override
  Widget build(BuildContext context) {
    if (widget.items.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.title)),
        body: const Center(child: Text('没有需要复习的词汇')),
      );
    }

    final item = widget.items[_currentIndex];
    return Scaffold(
      appBar: AppBar(
        title: Text(
            '${widget.title} (${_currentIndex + 1}/${widget.items.length})'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // German word
            Text(
              item['german'] ?? '',
              style:
                  const TextStyle(fontSize: 36, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            if (item['gender'] != null) ...[
              const SizedBox(height: 4),
              Text(item['gender'],
                  style:
                      TextStyle(fontSize: 16, color: Colors.grey.shade600)),
            ],
            // IPA
            if (item['phonetic'] != null &&
                item['phonetic'].toString().isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(item['phonetic'],
                  style: TextStyle(
                      fontSize: 14,
                      color: Colors.purple.shade400,
                      fontStyle: FontStyle.italic)),
            ],
            const SizedBox(height: 16),
            // TTS buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: Icon(Icons.volume_up,
                      color: Colors.blue.shade600, size: 32),
                  onPressed: () => _tts.speak(item['german'] ?? ''),
                  tooltip: '正常语速',
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.slow_motion_video,
                      color: Colors.orange.shade600, size: 28),
                  onPressed: () => _tts.speakSlow(item['german'] ?? ''),
                  tooltip: '慢速朗读',
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Answer
            if (_showAnswer) ...[
              Text(
                item['chinese'] ?? '',
                style: const TextStyle(fontSize: 24),
                textAlign: TextAlign.center,
              ),
              if (item['example'] != null) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(item['example'],
                      style: const TextStyle(
                          fontSize: 14, fontStyle: FontStyle.italic)),
                ),
              ],
              const SizedBox(height: 32),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _markButton('不认识', Colors.red, 'unknown', item['id']),
                  _markButton('学习中', Colors.orange, 'learning', item['id']),
                  _markButton('已掌握', Colors.green, 'known', item['id']),
                ],
              ),
            ] else ...[
              const SizedBox(height: 32),
              SizedBox(
                width: 200,
                height: 48,
                child: ElevatedButton(
                  onPressed: () => setState(() => _showAnswer = true),
                  child:
                      const Text('显示答案', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _markButton(String label, Color color, String status, dynamic id) {
    return ElevatedButton(
      onPressed: () async {
        if (id != null) {
          try {
            await widget.api.updateVocabulary(id, {'status': status});
          } catch (_) {}
        }
        if (_currentIndex < widget.items.length - 1) {
          setState(() {
            _currentIndex++;
            _showAnswer = false;
          });
        } else {
          if (mounted) Navigator.pop(context);
        }
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
      ),
      child: Text(label),
    );
  }
}

// --- Quiz Page ---
class _QuizPage extends StatefulWidget {
  final List items;
  const _QuizPage({required this.items});

  @override
  State<_QuizPage> createState() => _QuizPageState();
}

class _QuizPageState extends State<_QuizPage> {
  final _tts = TtsService();
  int _index = 0;
  int _correct = 0;
  bool _answered = false;
  int? _selectedOption;

  @override
  Widget build(BuildContext context) {
    if (_index >= widget.items.length) {
      return Scaffold(
        appBar: AppBar(title: const Text('测验结果')),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.emoji_events,
                  size: 64, color: Color(0xFFFFCC00)),
              const SizedBox(height: 16),
              Text('$_correct / ${widget.items.length}',
                  style: const TextStyle(
                      fontSize: 36, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text(
                  _correct == widget.items.length
                      ? 'Perfekt! 完美！'
                      : _correct > widget.items.length / 2
                          ? 'Gut gemacht! 做得好！'
                          : 'Weiter lernen! 继续努力！',
                  style: const TextStyle(fontSize: 18)),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('返回'),
              ),
            ],
          ),
        ),
      );
    }

    final item = widget.items[_index];
    final options = <String>[item['chinese']];
    for (final other in widget.items) {
      if (other['chinese'] != item['chinese'] && options.length < 4) {
        options.add(other['chinese']);
      }
    }
    while (options.length < 4) {
      options.add('---');
    }
    options.shuffle();

    return Scaffold(
      appBar: AppBar(
          title: Text('测验 (${_index + 1}/${widget.items.length})')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(item['german'] ?? '',
                style: const TextStyle(
                    fontSize: 32, fontWeight: FontWeight.bold)),
            if (item['gender'] != null)
              Text(item['gender'],
                  style: TextStyle(color: Colors.grey.shade600)),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: Icon(Icons.volume_up,
                      color: Colors.blue.shade600, size: 28),
                  onPressed: () => _tts.speak(item['german'] ?? ''),
                  tooltip: '正常语速',
                ),
                IconButton(
                  icon: Icon(Icons.slow_motion_video,
                      color: Colors.orange.shade600, size: 24),
                  onPressed: () => _tts.speakSlow(item['german'] ?? ''),
                  tooltip: '慢速朗读',
                ),
              ],
            ),
            const SizedBox(height: 24),
            ...List.generate(options.length, (i) {
              final isCorrect = options[i] == item['chinese'];
              Color? bgColor;
              if (_answered) {
                if (isCorrect) bgColor = Colors.green.shade100;
                if (_selectedOption == i && !isCorrect) {
                  bgColor = Colors.red.shade100;
                }
              }
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _answered
                        ? null
                        : () {
                            setState(() {
                              _answered = true;
                              _selectedOption = i;
                              if (isCorrect) _correct++;
                            });
                            Future.delayed(
                                const Duration(milliseconds: 800), () {
                              if (mounted) {
                                setState(() {
                                  _index++;
                                  _answered = false;
                                  _selectedOption = null;
                                });
                              }
                            });
                          },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: bgColor,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: Text(options[i],
                        style: const TextStyle(fontSize: 16)),
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
