import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/event.dart';

class ApiService {
  ApiService({http.Client? client}) : _client = client ?? http.Client();

  static const String baseUrl = String.fromEnvironment(
    'EVENTFINDER_API_URL',
    defaultValue: 'http://127.0.0.1:8001',
  );

  final http.Client _client;

  Future<List<Event>> fetchEvents({int limit = 20}) async {
    final uri = Uri.parse('$baseUrl/events').replace(
      queryParameters: {'limit': '$limit'},
    );

    late http.Response response;
    try {
      response = await _client.get(uri).timeout(const Duration(seconds: 12));
    } on Exception catch (error) {
      throw ApiException('Impossibile collegarsi a EventFinder.', error);
    }

    if (response.statusCode != 200) {
      throw ApiException(
        'Il server ha restituito ${response.statusCode}.',
      );
    }

    try {
      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic> || decoded['items'] is! List) {
        throw const FormatException('Formato risposta non valido.');
      }
      return (decoded['items'] as List<dynamic>)
          .map((item) => Event.fromJson(item as Map<String, dynamic>))
          .toList(growable: false);
    } on FormatException catch (error) {
      throw ApiException('La risposta del server non è valida.', error);
    }
  }

  void close() => _client.close();
}

class ApiException implements Exception {
  const ApiException(this.message, [this.cause]);

  final String message;
  final Object? cause;

  @override
  String toString() => message;
}
