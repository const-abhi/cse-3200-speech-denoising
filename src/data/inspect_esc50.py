
from pathlib import Path
import csv
import soundfile as sf
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ESC_ROOT = PROJECT_ROOT / "data" / "raw" / "ESC-50"
OUTPUT = PROJECT_ROOT / "data" / "metadata" / "esc50_inventory.csv"

# Locate metadata automatically
metadata_files = list(ESC_ROOT.rglob("esc50.csv"))

if not metadata_files:
    raise FileNotFoundError("Could not locate esc50.csv")

metadata_path = metadata_files[0]
audio_dir = metadata_path.parent.parent / "audio"

if not audio_dir.is_dir():
    raise FileNotFoundError(f"Audio directory not found: {audio_dir}")

rows = []
categories = Counter()
folds = Counter()
errors = []

with open(metadata_path, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for item in reader:
        filename = item["filename"]
        audio_path = audio_dir / filename

        try:
            info = sf.info(str(audio_path))

            rows.append({
                "filename": filename,
                "category": item["category"],
                "fold": item["fold"],
                "target": item["target"],
                "sample_rate_hz": info.samplerate,
                "channels": info.channels,
                "duration_seconds": round(
                    info.frames / info.samplerate, 4
                ),
                "relative_path": str(
                    audio_path.relative_to(PROJECT_ROOT)
                ),
                "status": "ok",
            })

            categories[item["category"]] += 1
            folds[item["fold"]] += 1

        except Exception as error:
            errors.append((filename, str(error)))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "filename", "category", "fold", "target",
    "sample_rate_hz", "channels", "duration_seconds",
    "relative_path", "status"
]

with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("\n========== ESC-50 SUMMARY ==========")
print("Total inspected:", len(rows))
print("Categories:", len(categories))
print("Folds:", dict(folds))
print("Errors:", len(errors))

print("\nCATEGORY COUNTS:")

for category, count in sorted(categories.items()):
    print(f"{category:25s} {count}")

if errors:
    print("\nERRORS:")
    for item in errors:
        print(item)

print("\nInventory saved to:", OUTPUT)

