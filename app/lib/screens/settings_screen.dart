import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  final ApiService api;
  const SettingsScreen({super.key, required this.api});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _stats;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      final stats = await widget.api.getStats();
      setState(() {
        _stats = stats;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Stats card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('学习统计',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  if (_loading)
                    const Center(child: CircularProgressIndicator())
                  else if (_stats != null) ...[
                    _statRow(
                        '总词汇', _stats!['vocabulary']?['total'] ?? 0),
                    _statRow(
                        '已掌握', _stats!['vocabulary']?['known'] ?? 0,
                        color: Colors.green),
                    _statRow(
                        '学习中', _stats!['vocabulary']?['learning'] ?? 0,
                        color: Colors.orange),
                    _statRow(
                        '未学', _stats!['vocabulary']?['unknown'] ?? 0,
                        color: Colors.red),
                    const Divider(),
                    _statRow(
                        '总句型', _stats!['sentences']?['total'] ?? 0),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // About card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('关于',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  _infoRow('应用', 'DeutschLerner v1.0.0'),
                  _infoRow('功能', '德语学习助手 (中文→德语)'),
                  _infoRow('AI', '多AI支持 (Claude, GPT, Gemini等)'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Connection test
          ElevatedButton.icon(
            onPressed: () async {
              final ok = await widget.api.testConnection();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content:
                        Text(ok ? '服务器连接正常' : '无法连接服务器'),
                    backgroundColor: ok ? Colors.green : Colors.red,
                  ),
                );
              }
            },
            icon: const Icon(Icons.wifi),
            label: const Text('测试服务器连接'),
          ),
        ],
      ),
    );
  }

  Widget _statRow(String label, int value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text('$value',
              style: TextStyle(
                  fontWeight: FontWeight.bold, color: color, fontSize: 16)),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey.shade600)),
          Flexible(child: Text(value, textAlign: TextAlign.end)),
        ],
      ),
    );
  }
}
