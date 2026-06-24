import 'package:flutter/material.dart';

import '../models/event.dart';

class EventCard extends StatelessWidget {
  const EventCard({required this.event, super.key});

  final Event event;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    event.title,
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                  ),
                ),
                if (event.qualityClass != null) ...[
                  const SizedBox(width: 12),
                  _QualityBadge(value: event.qualityClass!),
                ],
              ],
            ),
            const SizedBox(height: 12),
            _Metadata(icon: Icons.location_on_outlined, text: event.location),
            const SizedBox(height: 8),
            _Metadata(icon: Icons.calendar_today_outlined, text: _formatDate(event.startDate)),
            if (event.distanceKm != null) ...[
              const SizedBox(height: 8),
              _Metadata(
                icon: Icons.near_me_outlined,
                text: '${event.distanceKm!.toStringAsFixed(1)} km',
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'Data non disponibile';
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    return '$day/$month/${date.year}';
  }
}

class _Metadata extends StatelessWidget {
  const _Metadata({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: Theme.of(context).colorScheme.onSurfaceVariant),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: Theme.of(context).textTheme.bodyMedium)),
      ],
    );
  }
}

class _QualityBadge extends StatelessWidget {
  const _QualityBadge({required this.value});

  final String value;

  @override
  Widget build(BuildContext context) {
    final normalized = value.toUpperCase();
    final color = switch (normalized) {
      'HIGH' => const Color(0xFF176B5B),
      'MEDIUM' => const Color(0xFFB65C20),
      _ => const Color(0xFF6B7280),
    };
    return Semantics(
      label: 'Qualità $normalized',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: color.withAlpha(31),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          normalized,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: color,
                fontWeight: FontWeight.w700,
              ),
        ),
      ),
    );
  }
}
