import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'daily_plan_screen.dart';
import 'vocabulary_screen.dart';
import 'learn_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  final ApiService api;
  const HomeScreen({super.key, required this.api});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  late final List<Widget> _pages;

  @override
  void initState() {
    super.initState();
    _pages = [
      DailyPlanScreen(api: widget.api),
      LearnScreen(api: widget.api),
      VocabularyScreen(api: widget.api),
      SettingsScreen(api: widget.api),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.today),
            selectedIcon: Icon(Icons.today, color: Color(0xFFDD0000)),
            label: '今日计划',
          ),
          NavigationDestination(
            icon: Icon(Icons.school),
            selectedIcon: Icon(Icons.school, color: Color(0xFFDD0000)),
            label: '学习',
          ),
          NavigationDestination(
            icon: Icon(Icons.list_alt),
            selectedIcon: Icon(Icons.list_alt, color: Color(0xFFDD0000)),
            label: '词汇',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings),
            selectedIcon: Icon(Icons.settings, color: Color(0xFFDD0000)),
            label: '设置',
          ),
        ],
      ),
    );
  }
}
