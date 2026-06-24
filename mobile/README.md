# EventFinder Mobile

Flutter client for the EventFinder API.

## Requirements

- Flutter SDK with Dart 3.3 or newer
- Android Studio or another configured Flutter device
- EventFinder backend running locally

Verify the installation with `flutter doctor`.

## Run

From `mobile/`:

```bash
flutter pub get
flutter run
```

The default API URL is `http://127.0.0.1:8001`. Override it at build time:

```bash
flutter run --dart-define=EVENTFINDER_API_URL=http://192.168.1.10:8001
```

For the Android emulator, the host machine is available at `10.0.2.2`, not `127.0.0.1`:

```bash
flutter run --dart-define=EVENTFINDER_API_URL=http://10.0.2.2:8001
```

## Validation

```bash
flutter analyze
```

The Home screen requests `GET /events?limit=20` and handles loading, connection errors, empty results, pull-to-refresh, and event cards.
