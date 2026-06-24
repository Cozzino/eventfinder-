import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

void main() {
  runApp(const EventFinderApp());
}

class EventFinderApp extends StatelessWidget {
  const EventFinderApp({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF176B5B),
      brightness: Brightness.light,
    ).copyWith(
      secondary: const Color(0xFFE76F51),
      surface: const Color(0xFFF7F8F5),
    );

    return MaterialApp(
      title: 'EventFinder',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: colorScheme,
        useMaterial3: true,
        scaffoldBackgroundColor: colorScheme.surface,
        cardTheme: const CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(8)),
            side: BorderSide(color: Color(0xFFDCE2DE)),
          ),
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
