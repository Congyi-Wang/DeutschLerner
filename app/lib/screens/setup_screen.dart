import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SetupScreen extends StatefulWidget {
  final ApiService api;
  final VoidCallback onDone;

  const SetupScreen({super.key, required this.api, required this.onDone});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final _urlCtrl = TextEditingController(text: 'http://46.224.150.45/deutsch');
  final _keyCtrl = TextEditingController();
  bool _testing = false;
  String? _error;

  Future<void> _connect() async {
    setState(() {
      _testing = true;
      _error = null;
    });

    await widget.api.saveConfig(_urlCtrl.text.trim(), _keyCtrl.text.trim());
    final ok = await widget.api.testConnection();

    if (ok) {
      widget.onDone();
    } else {
      setState(() {
        _testing = false;
        _error = '无法连接服务器，请检查地址和API密钥';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // German flag icon
              Container(
                width: 80,
                height: 54,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Column(
                  children: [
                    Expanded(
                        child:
                            Container(color: const Color(0xFF1A1A1A))),
                    Expanded(
                        child:
                            Container(color: const Color(0xFFDD0000))),
                    Expanded(
                        child:
                            Container(color: const Color(0xFFFFCC00))),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'DeutschLerner',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const Text(
                '德语学习助手',
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 40),
              TextField(
                controller: _urlCtrl,
                decoration: const InputDecoration(
                  labelText: '服务器地址',
                  hintText: 'http://your-server:8000',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.dns),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _keyCtrl,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'API 密钥',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.key),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _testing ? null : _connect,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1A1A1A),
                    foregroundColor: Colors.white,
                  ),
                  child: _testing
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : const Text('连接', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
