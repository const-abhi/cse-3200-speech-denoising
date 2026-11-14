
from pathlib import Path
import csv
import soundfile as sf
from collections import Counter

# Locate the project directory automatically
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_ROOT = PROJECT_ROOT / "data" / "raw" / "voicebank-demand"
OUTPUT_FILE = PROJECT_ROOT / "data" / "metadata" / "voicebank_inventory.csv"

# Preserve the dataset's original train/test separation
SPLITS = {
    "train": DATA_ROOT / "clean_trainset_28spk_wav",
    "test": DATA_ROOT / "clean_testset_wav",
}

rows = []
split_counts = {}
errors = []

for split, folder in SPLITS.items():

    if not folder.is_dir():
        print(f"WARNING: Directory not found: {folder}")
        continue

    wav_files = sorted(folder.rglob("*.wav"))
    split_counts[split] = len(wav_files)

    print(f"\nInspecting {split} dataset: {len(wav_files)} files")

    for index, wav_path in enumerate(wav_files, start=1):

        try:
            info = sf.info(str(wav_path))

            # VoiceBank filenames conventionally start with speaker ID.
            speaker_id = wav_path.stem.split("_")[0]

            rows.append({
                "filename": wav_path.name,
                "speaker_id": speaker_id,
                "split": split,
                "relative_path": str(wav_path.relative_to(PROJECT_ROOT)),
                "sample_rate_hz": info.samplerate,
                "channels": info.channels,
                "num_samples": info.frames,
                "duration_seconds": round(
                    info.frames / info.samplerate, 4
                ),
                "subtype": info.subtype,
                "status": "ok",
            })

        except Exception as error:
            errors.append((wav_path, str(error)))
            print(f"Could not inspect: {wav_path.name}: {error}")

        if index % 500 == 0:
            print(f"  Processed {index}/{len(wav_files)}")

# Save inventory
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "filename",
    "speaker_id",
    "split",
    "relative_path",
    "sample_rate_hz",
    "channels",
    "num_samples",
    "duration_seconds",
    "subtype",
    "status",
]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Print summary
print("\n========== DATASET SUMMARY ==========")

for split, count in split_counts.items():
    split_rows = [r for r in rows if r["split"] == split]
    speakers = {r["speaker_id"] for r in split_rows}

    print(f"\n{split.upper()}")
    print("Files:", count)
    print("Unique speakers:", len(speakers))
    print("Sample rates:", dict(Counter(
        r["sample_rate_hz"] for r in split_rows
    )))
    print("Total duration (hours):", round(
        sum(r["duration_seconds"] for r in split_rows) / 3600, 2
    ))

print("\nTotal successfully inspected:", len(rows))
print("Inspection errors:", len(errors))
print("Inventory saved to:", OUTPUT_FILE)

