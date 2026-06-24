class Event {
  const Event({
    required this.id,
    required this.title,
    this.city,
    this.province,
    this.startDate,
    this.qualityClass,
    this.distanceKm,
  });

  final String id;
  final String title;
  final String? city;
  final String? province;
  final DateTime? startDate;
  final String? qualityClass;
  final double? distanceKm;

  factory Event.fromJson(Map<String, dynamic> json) {
    return Event(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? 'Evento senza titolo',
      city: _nullableString(json['city']),
      province: _nullableString(json['province']),
      startDate: DateTime.tryParse(json['start_date'] as String? ?? ''),
      qualityClass: _nullableString(json['quality_class']),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
    );
  }

  String get location {
    final parts = [city, province]
        .where((value) => value != null && value.isNotEmpty)
        .cast<String>()
        .toList();
    return parts.isEmpty ? 'Località non disponibile' : parts.join(', ');
  }

  static String? _nullableString(Object? value) {
    final text = value?.toString().trim();
    return text == null || text.isEmpty ? null : text;
  }
}
