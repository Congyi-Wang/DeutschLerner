import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/tts_service.dart';

class GrammarScreen extends StatefulWidget {
  final ApiService api;
  const GrammarScreen({super.key, required this.api});

  @override
  State<GrammarScreen> createState() => _GrammarScreenState();
}

class _GrammarScreenState extends State<GrammarScreen> {
  List<Map<String, dynamic>> _exercises = [];
  int _current = 0;
  int _correct = 0;
  bool _loading = true;
  String? _error;
  String? _moduleName;

  // Per-exercise state
  bool _answered = false;
  String? _selected;
  List<String> _selectedOrder = [];
  Map<String, String> _conjugationAnswers = {};

  final _tts = TtsService();

  @override
  void initState() {
    super.initState();
    _tts.init();
    _loadExercises();
  }

  Future<void> _loadExercises() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await widget.api.getGrammarExercises();
      setState(() {
        _exercises =
            (data['exercises'] as List).cast<Map<String, dynamic>>();
        _moduleName = data['module_name_cn'] as String?;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _nextExercise() {
    setState(() {
      _current++;
      _answered = false;
      _selected = null;
      _selectedOrder = [];
      _conjugationAnswers = {};
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_moduleName != null ? '语法练习 · $_moduleName' : '语法练习'),
        actions: [
          if (_exercises.isNotEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Text(
                  '${_current + 1}/${_exercises.length}',
                  style: const TextStyle(fontSize: 16),
                ),
              ),
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
                      Text(_error!,
                          style: const TextStyle(color: Colors.red)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                          onPressed: _loadExercises,
                          child: const Text('重试')),
                    ],
                  ),
                )
              : _exercises.isEmpty
                  ? const Center(child: Text('暂无练习题'))
                  : _current >= _exercises.length
                      ? _buildResult()
                      : _buildExercise(_exercises[_current]),
    );
  }

  Widget _buildResult() {
    final pct =
        _exercises.isNotEmpty ? (_correct / _exercises.length * 100).round() : 0;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              pct >= 80 ? Icons.emoji_events : Icons.school,
              size: 64,
              color: pct >= 80 ? const Color(0xFFFFCC00) : Colors.blue,
            ),
            const SizedBox(height: 16),
            Text('$_correct / ${_exercises.length}',
                style:
                    const TextStyle(fontSize: 36, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(
              pct >= 80
                  ? 'Sehr gut! 做得好！'
                  : pct >= 50
                      ? 'Gut! 继续努力！'
                      : 'Weiter üben! 多多练习！',
              style: const TextStyle(fontSize: 18),
            ),
            const SizedBox(height: 8),
            Text('正确率: $pct%',
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _current = 0;
                      _correct = 0;
                      _answered = false;
                      _selected = null;
                      _selectedOrder = [];
                      _conjugationAnswers = {};
                    });
                    _loadExercises();
                  },
                  child: const Text('再来一组'),
                ),
                const SizedBox(width: 16),
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('返回'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExercise(Map<String, dynamic> ex) {
    final type = ex['type'] as String;
    switch (type) {
      case 'article':
        return _buildArticle(ex);
      case 'cloze':
        return _buildCloze(ex);
      case 'conjugation':
        return _buildConjugation(ex);
      case 'sentence_order':
        return _buildSentenceOrder(ex);
      default:
        return Center(child: Text('Unknown exercise type: $type'));
    }
  }

  // === Article Exercise (der/die/das) ===
  Widget _buildArticle(Map<String, dynamic> ex) {
    final german = ex['german'] as String;
    final chinese = ex['chinese'] as String;
    final correct = ex['correct'] as String;
    final options = (ex['options'] as List).cast<String>();

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('选择正确的冠词',
                style: TextStyle(color: Colors.blue, fontSize: 14)),
          ),
          const SizedBox(height: 32),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('___  ', style: TextStyle(fontSize: 28, color: Colors.grey.shade400)),
              Text(german,
                  style: const TextStyle(
                      fontSize: 28, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 8),
          Text(chinese, style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
          const SizedBox(height: 8),
          IconButton(
            icon: Icon(Icons.volume_up, color: Colors.blue.shade600),
            onPressed: () => _tts.speak('$correct $german'),
          ),
          const SizedBox(height: 32),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: options.map((opt) {
              Color? bg;
              Color textColor = Colors.black87;
              if (_answered) {
                if (opt == correct) {
                  bg = Colors.green.shade100;
                  textColor = Colors.green.shade800;
                } else if (opt == _selected && opt != correct) {
                  bg = Colors.red.shade100;
                  textColor = Colors.red.shade800;
                }
              }
              return SizedBox(
                width: 90,
                height: 48,
                child: ElevatedButton(
                  onPressed: _answered
                      ? null
                      : () {
                          setState(() {
                            _selected = opt;
                            _answered = true;
                            if (opt == correct) _correct++;
                          });
                          Future.delayed(const Duration(milliseconds: 1000),
                              () {
                            if (mounted) _nextExercise();
                          });
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: bg,
                    foregroundColor: textColor,
                  ),
                  child: Text(opt, style: const TextStyle(fontSize: 18)),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  // === Cloze Exercise ===
  Widget _buildCloze(Map<String, dynamic> ex) {
    final sentence = ex['sentence'] as String;
    final correct = ex['correct'] as String;
    final options = (ex['options'] as List).cast<String>();
    final hintCn = ex['hint_cn'] as String;
    final grammarCn = ex['grammar_cn'] as String;

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.purple.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('填入正确的词',
                style: TextStyle(color: Colors.purple, fontSize: 14)),
          ),
          const SizedBox(height: 24),
          Text(sentence,
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center),
          const SizedBox(height: 8),
          Text(hintCn,
              style: TextStyle(fontSize: 15, color: Colors.grey.shade600)),
          const SizedBox(height: 32),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            alignment: WrapAlignment.center,
            children: options.map((opt) {
              Color? bg;
              Color textColor = Colors.black87;
              if (_answered) {
                if (opt == correct) {
                  bg = Colors.green.shade100;
                  textColor = Colors.green.shade800;
                } else if (opt == _selected && opt != correct) {
                  bg = Colors.red.shade100;
                  textColor = Colors.red.shade800;
                }
              }
              return SizedBox(
                width: 140,
                height: 44,
                child: ElevatedButton(
                  onPressed: _answered
                      ? null
                      : () {
                          setState(() {
                            _selected = opt;
                            _answered = true;
                            if (opt == correct) _correct++;
                          });
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: bg,
                    foregroundColor: textColor,
                  ),
                  child: Text(opt, style: const TextStyle(fontSize: 16)),
                ),
              );
            }).toList(),
          ),
          if (_answered) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.lightbulb, size: 18, color: Colors.amber.shade700),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(grammarCn,
                        style: TextStyle(
                            fontSize: 13, color: Colors.amber.shade900)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _nextExercise,
              child: const Text('下一题'),
            ),
          ],
        ],
      ),
    );
  }

  // === Conjugation Exercise ===
  Widget _buildConjugation(Map<String, dynamic> ex) {
    final verb = ex['verb'] as String;
    final cells = (ex['cells'] as List).cast<Map<String, dynamic>>();
    final allForms = (ex['all_forms'] as List).cast<String>();

    // Check if all blanks are filled
    final blanks = cells.where((c) => c['is_blank'] == true).toList();
    final allFilled = blanks.every(
        (c) => _conjugationAnswers.containsKey(c['pronoun'] as String));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.teal.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('动词变位',
                style: TextStyle(color: Colors.teal, fontSize: 14)),
          ),
          const SizedBox(height: 16),
          Text(verb,
              style:
                  const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
          IconButton(
            icon: Icon(Icons.volume_up, color: Colors.blue.shade600),
            onPressed: () => _tts.speak(verb),
          ),
          const SizedBox(height: 16),
          ...cells.map((cell) {
            final pronoun = cell['pronoun'] as String;
            final answer = cell['answer'] as String;
            final isBlank = cell['is_blank'] as bool;

            if (!isBlank) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    SizedBox(
                        width: 80,
                        child: Text(pronoun,
                            style: const TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold))),
                    Text(answer, style: const TextStyle(fontSize: 16)),
                  ],
                ),
              );
            }

            final userAnswer = _conjugationAnswers[pronoun];
            final isCorrect = userAnswer == answer;

            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  SizedBox(
                      width: 80,
                      child: Text(pronoun,
                          style: const TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold))),
                  if (_answered) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: isCorrect
                            ? Colors.green.shade100
                            : Colors.red.shade100,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        isCorrect ? answer : '$userAnswer  ($answer)',
                        style: TextStyle(
                          fontSize: 16,
                          color: isCorrect
                              ? Colors.green.shade800
                              : Colors.red.shade800,
                        ),
                      ),
                    ),
                  ] else ...[
                    if (userAnswer != null)
                      Chip(
                        label: Text(userAnswer),
                        onDeleted: () {
                          setState(
                              () => _conjugationAnswers.remove(pronoun));
                        },
                      )
                    else
                      Container(
                        width: 120,
                        height: 36,
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey.shade300),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        alignment: Alignment.center,
                        child: Text('___',
                            style:
                                TextStyle(color: Colors.grey.shade400)),
                      ),
                  ],
                ],
              ),
            );
          }),
          if (!_answered) ...[
            const SizedBox(height: 16),
            const Text('选择正确的变位形式:',
                style: TextStyle(fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: allForms.map((form) {
                return ActionChip(
                  label: Text(form),
                  onPressed: () {
                    // Fill next empty blank
                    for (final c in blanks) {
                      final p = c['pronoun'] as String;
                      if (!_conjugationAnswers.containsKey(p)) {
                        setState(() => _conjugationAnswers[p] = form);
                        break;
                      }
                    }
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            if (allFilled)
              ElevatedButton(
                onPressed: () {
                  int correctCount = 0;
                  for (final c in blanks) {
                    if (_conjugationAnswers[c['pronoun']] ==
                        c['answer']) {
                      correctCount++;
                    }
                  }
                  setState(() {
                    _answered = true;
                    if (correctCount == blanks.length) _correct++;
                  });
                },
                child: const Text('检查'),
              ),
          ] else ...[
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _nextExercise,
              child: const Text('下一题'),
            ),
          ],
        ],
      ),
    );
  }

  // === Sentence Order Exercise ===
  Widget _buildSentenceOrder(Map<String, dynamic> ex) {
    final words = (ex['words'] as List).cast<String>();
    final correct = ex['correct'] as String;
    final hintCn = ex['hint_cn'] as String;

    final remaining =
        words.where((w) => !_selectedOrder.contains(w)).toList();
    final userSentence = _selectedOrder.join(' ');

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.orange.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('排列正确语序',
                style: TextStyle(color: Colors.orange, fontSize: 14)),
          ),
          const SizedBox(height: 16),
          Text(hintCn,
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
          const SizedBox(height: 24),

          // Answer area
          Container(
            width: double.infinity,
            constraints: const BoxConstraints(minHeight: 60),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(
                color: _answered
                    ? (userSentence == correct
                        ? Colors.green
                        : Colors.red)
                    : Colors.grey.shade300,
                width: 2,
              ),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                ..._selectedOrder.map((w) => GestureDetector(
                      onTap: _answered
                          ? null
                          : () =>
                              setState(() => _selectedOrder.remove(w)),
                      child: Chip(
                        label: Text(w,
                            style: const TextStyle(fontSize: 16)),
                      ),
                    )),
                if (_selectedOrder.isEmpty)
                  Text('点击下方单词组成句子',
                      style: TextStyle(
                          color: Colors.grey.shade400, fontSize: 14)),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Word bank
          if (!_answered)
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: remaining.map((w) {
                return ActionChip(
                  label: Text(w, style: const TextStyle(fontSize: 16)),
                  onPressed: () =>
                      setState(() => _selectedOrder.add(w)),
                );
              }).toList(),
            ),

          if (_answered) ...[
            const SizedBox(height: 12),
            if (userSentence != correct)
              Text('正确答案: $correct',
                  style:
                      TextStyle(color: Colors.green.shade700, fontSize: 15)),
            const SizedBox(height: 8),
            IconButton(
              icon: Icon(Icons.volume_up, color: Colors.blue.shade600),
              onPressed: () => _tts.speak(correct),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _nextExercise,
              child: const Text('下一题'),
            ),
          ] else if (remaining.isEmpty && _selectedOrder.isNotEmpty) ...[
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _answered = true;
                  if (userSentence == correct) _correct++;
                });
              },
              child: const Text('检查'),
            ),
          ],
        ],
      ),
    );
  }
}
