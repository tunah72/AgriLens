# YOLO26-seg - Joint leaf disease instance segmentation

Run `20260922T115556Z` | dataset `coffee_rice_v002` (repaired, leak-free grouped splits)

## Task
Instance segmentation of joint leaf disease. Detection classes: ['LeafMiner', 'PowderyMildew', 'Rust', 'AlgalLeafSpot', 'BrownSpot', 'Hispa', 'LeafBlast'].
`Healthy` is an image-level label, not a class: a healthy leaf is expected to produce no instance.

## Operating point
conf = 0.5 (selected on the validation split by mask-F1), NMS IoU = 0.7,
imgsz = 1024.

## Test metrics (COCO, original resolution)
- mask mAP@50: 0.6169
- mask mAP@50:95: 0.6106
- box mAP@50: 0.6169
- box mAP@50:95: 0.6011
- mIoU: 0.6986 | Dice: 0.8155
- background images returning nothing: 0.8029
- CPU latency: 205.35 ms/image (imgsz 1024)

## Known limits
- The model is closed-set. Out-of-domain images require the serving-side rejection gate;
  `background_clean_rate` only measures healthy leaves of the same domain.
- Rice labels come from two annotation protocols (studio whole-leaf vs field lesions) and the
  capture sessions correlate with classes; see `reports/` in the dataset version.
