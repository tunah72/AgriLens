# YOLO26-seg - Coffee leaf disease instance segmentation

Run `20260922T165810Z` | dataset `coffee_rice_v002` (repaired, leak-free grouped splits)

## Task
Instance segmentation of coffee leaf disease. Detection classes: ['LeafMiner', 'PowderyMildew', 'Rust', 'AlgalLeafSpot'].
`Healthy` is an image-level label, not a class: a healthy leaf is expected to produce no instance.

## Operating point
conf = 0.55 (selected on the validation split by mask-F1), NMS IoU = 0.7,
imgsz = 1024.

## Test metrics (COCO, original resolution)
- mask mAP@50: 0.7281
- mask mAP@50:95: 0.7234
- box mAP@50: 0.7281
- box mAP@50:95: 0.7075
- mIoU: 0.8093 | Dice: 0.8925
- background images returning nothing: 0.0
- CPU latency: 211.92 ms/image (imgsz 1024)

## Known limits
- The model is closed-set. Out-of-domain images require the serving-side rejection gate;
  `background_clean_rate` only measures healthy leaves of the same domain.
- Rice labels come from two annotation protocols (studio whole-leaf vs field lesions) and the
  capture sessions correlate with classes; see `reports/` in the dataset version.
