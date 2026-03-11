import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'screens/setup_screen.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const DeutschLernerApp());
}

class DeutschLernerApp extends StatelessWidget {
  const DeutschLernerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DeutschLerner',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.light,
        colorScheme: ColorScheme.light(
          primary: const Color(0xFFDD0000),
          secondary: const Color(0xFFFFCC00),
          surface: Colors.white,
          onPrimary: Colors.white,
          onSecondary: Colors.black,
        ),
        scaffoldBackgroundColor: const Color(0xFFF5F5F5),
        cardColor: Colors.white,
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1A1A1A),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        useMaterial3: true,
      ),
      home: const AppGate(),
    );
  }
}

class AppGate extends StatefulWidget {
  const AppGate({super.key});

  @override
  State<AppGate> createState() => _AppGateState();
}

class _AppGateState extends State<AppGate> {
  bool _loading = true;
  bool _configured = false;
  final _api = ApiService();

  @override
  void initState() {
    super.initState();
    _checkSetup();
  }

  Future<void> _checkSetup() async {
    await _api.init();
    setState(() {
      _configured = _api.isConfigured;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (!_configured) {
      return SetupScreen(
        api: _api,
        onDone: () => setState(() => _configured = true),
      );
    }
    return HomeScreen(api: _api);
  }
}
