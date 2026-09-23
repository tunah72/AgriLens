# YOLO26-seg - Rice leaf disease instance segmentation

Run `20260922T182638Z` | dataset `coffee_rice_v002` (repaired, leak-free grouped splits)

## Task
Instance segmentation of rice leaf disease. Detection classes: ['BrownSpot', 'Hispa', 'LeafBlast'].
`Healthy` is an image-level label, not a class: a healthy leaf is expected to produce no instance.

## Operating point
conf = 0.6 (selected on the validation split by mask-F1), NMS IoU = 0.7,
imgsz = 1024.

## Test metrics (COCO, original resolution)
- mask mAP@50: 0.3587
- mask mAP@50:95: 0.3516
- box mAP@50: 0.3587
- box mAP@50:95: 0.3576
- mIoU: 0.4574 | Dice: 0.6146
- background images returning nothing: 0.5048
- CPU latency: 270.64 ms/image (imgsz 1024)

## Known limits
- The model is closed-set. Out-of-domain images require the serving-side rejection gate;
  `background_clean_rate` only measures healthy leaves of the same domain.
- Rice labels come from two annotation protocols (studio whole-leaf vs field lesions) and the
  capture sessions correlate with classes; see `reports/` in the dataset version.
