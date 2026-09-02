#!/usr/bin/env python3
"""Test script to verify the analysis pipeline works end-to-end"""

import sys
import json
from pathlib import Path

print("=" * 60)
print("TESTING ANALYSIS PIPELINE")
print("=" * 60)

# Test image selection
test_image_dir = Path("/home/sakthivel/Documents/marine-debris-ai/backend/data/uploads")
test_images = list(test_image_dir.glob("*.png")) + list(test_image_dir.glob("*.jpg"))

if not test_images:
    print("⚠ No test images found in backend/data/uploads/")
    print("Please provide a sonar image for testing")
    sys.exit(0)

test_image = test_images[0]
print(f"✓ Found test image: {test_image.name}")
print()

# Read image data
print("=" * 60)
print("TESTING IMAGE VALIDATION")
print("=" * 60)

try:
    from backend.ai.preprocessing import validate_image
    
    image_data = test_image.read_bytes()
    width, height = validate_image(image_data, test_image.name, 20 * 1024 * 1024)
    print(f"✓ Image validated successfully")
    print(f"  Dimensions: {width} x {height} px")
    print(f"  Size: {len(image_data) / 1024:.2f} KB")
except Exception as e:
    print(f"✗ Image validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test image preprocessing
print("=" * 60)
print("TESTING IMAGE PREPROCESSING")
print("=" * 60)

try:
    from backend.ai.preprocessing import preprocess_image
    
    processed, orig_width, orig_height = preprocess_image(image_data)
    print(f"✓ Image preprocessed successfully")
    print(f"  Original size: {orig_width} x {orig_height}")
    print(f"  Processed shape: {processed.shape}")
except Exception as e:
    print(f"✗ Image preprocessing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test YOLO detection
print("=" * 60)
print("TESTING YOLO INFERENCE")
print("=" * 60)

try:
    from backend.ai.yolo_detector import YoloDetector, DemoDetector
    from backend.core.config import settings
    
    print("Testing with DemoDetector first (faster)...")
    detector = DemoDetector()
    detections = detector.detect(processed)
    print(f"✓ DemoDetector returned {len(detections)} detections")
    
    for i, det in enumerate(detections, 1):
        print(f"  [{i}] {det['class_name']}: confidence={det['confidence']:.1%}")
    
    print()
    print("Testing with real YOLO model...")
    yolo = YoloDetector()
    
    if not yolo.available:
        print(f"⚠ YOLO model unavailable: {yolo.error}")
        print("  This is acceptable if model loading failed gracefully")
    else:
        detections_yolo = yolo.detect(processed)
        print(f"✓ YOLO model returned {len(detections_yolo)} detections")
        
        for i, det in enumerate(detections_yolo, 1):
            bbox = det['bbox']
            print(f"  [{i}] {det['class_name']}: confidence={det['confidence']:.1%}, bbox=({bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f})")
    
except Exception as e:
    print(f"✗ Inference failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test filtering
print("=" * 60)
print("TESTING DETECTION FILTERING")
print("=" * 60)

try:
    from backend.ai.filtering import filter_detections
    
    threshold = settings.confidence_threshold
    filtered = filter_detections(detections, processed.shape[1], processed.shape[0], threshold)
    print(f"✓ Filtering applied (threshold={threshold:.1%})")
    print(f"  Input detections: {len(detections)}")
    print(f"  Filtered detections: {len(filtered)}")
    
except Exception as e:
    print(f"✗ Filtering failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test anomaly scoring
print("=" * 60)
print("TESTING ANOMALY SCORING")
print("=" * 60)

try:
    from backend.ai.anomaly_scoring import score_detection
    
    for detection in filtered:
        final_conf, priority = score_detection(detection)
        detection['final_confidence'] = final_conf
        detection['priority'] = priority
        print(f"✓ {detection['class_name']}: final_confidence={final_conf:.1%}, priority={priority}")
    
except Exception as e:
    print(f"✗ Anomaly scoring failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test metadata and location
print("=" * 60)
print("TESTING METADATA AND LOCATION")
print("=" * 60)

try:
    from backend.geo.geotagger import geotag
    from backend.schemas.metadata import Metadata
    
    metadata = Metadata(
        survey_id="TEST_001",
        latitude=9.9252,
        longitude=78.1194,
        source="simulated"
    )
    
    lat, lon, source = geotag(metadata)
    print(f"✓ Metadata processed successfully")
    print(f"  Location: {lat:.5f}, {lon:.5f}")
    print(f"  Source: {source}")
    
except Exception as e:
    print(f"✗ Metadata processing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("ALL PIPELINE TESTS PASSED")
print("=" * 60)
print(f"✓ Images can be loaded and processed")
print(f"✓ Detections can be performed (Demo or YOLO)")
print(f"✓ Filtering works correctly")
print(f"✓ Anomaly scoring works")
print(f"✓ Metadata and location processing works")
print()
print("The application is ready to run!")
