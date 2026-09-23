# Technical Report: Instance Segmentation of Foliar Diseases in Coffee and Rice

## 1. Problem Formulation

Automated diagnosis of foliar diseases in specialty crops requires precise instance segmentation to localize lesions, delineate irregular morphological boundaries, and quantify disease severity. This study addresses seven distinct foliar pathologies across two major agricultural domains:
- **Coffee (*Coffea canephora / arabica*)**: Leaf Miner (*Perileucoptera coffeella*), Powdery Mildew (*Oidium virescens*), Rust (*Hemileia vastatrix*), Algal Leaf Spot (*Cephaleuros virescens*).
- **Rice (*Oryza sativa*)**: Brown Spot (*Bipolaris oryzae*), Hispa (*Dicladispa armigera*), Leaf Blast (*Magnaporthe oryzae*).
- **Negative Control**: Asymptomatic (healthy) leaves containing zero disease instances.

### Evaluation Criteria
- **Detection & Boundary Quality**: Standard COCO evaluation metrics (Mask $mAP@50$, Mask $mAP@50:95$, Box $mAP@50$) computed at native image resolutions.
- **Pixel-Level Fidelity**: Mean Intersection over Union ($mIoU$) and Dice similarity coefficient.
- **False-Positive Suppression**: Background clean rate ($BCR$), defined as the proportion of asymptomatic leaves yielding zero false-positive predictions.
- **Operational Efficiency**: Inference latency on commodity multi-core CPUs at $1024 \times 1024$ input resolution, alongside serialized checkpoint footprint.

---

## 2. Candidate Architectures

Three structurally distinct architectural paradigms are selected for evaluation:

1. **YOLO26-seg (Real-Time Single-Stage CNN)**:
   An anchor-free, real-time convolutional network employing a C3k2 feature extractor and a lightweight prototype mask head. Prototypic mask representations decoupled from bounding box coordinates minimize computational overhead, targeting low-latency deployment on edge computing nodes.
2. **RF_DETR (Query-Based Vision Transformer)**:
   A modern DEtection TRansformer (DETR) variant employing a DINO-based query formulation. It replaces heuristic anchor generation and non-maximum suppression (NMS) with end-to-end bipartite Hungarian matching and multi-scale deformable self-attention, designed to capture complex, overlapping lesion patterns.
3. **Mask R-CNN (Canonical Two-Stage Baseline)**:
   A standard two-stage benchmark architecture comprising a ResNet-50-FPN backbone, a Region Proposal Network (RPN), and a RoIAlign operator extracting feature representations for parallel bounding box classification and binary mask prediction.

---

## 3. Training Methodology & Joint Strategy Rationale

### 3.1. Dataset and Protocol
Experiments utilize dataset `coffee_rice_v002`, partitioned into 70% training ($N = 2,342$), 15% validation ($N = 649$), and 15% held-out test ($N = 648$) splits. To prevent data leakage observed in naive random splits:
- Rice samples are partitioned via temporal burst grouping ($\le 10$ s capture interval) combined with 1024-bit perceptual hash deduplication.
- Coffee samples are partitioned by unique source plant and photograph identifiers.
- Healthy leaf images are preserved strictly as negative controls without instance masks.

### 3.2. Hyperparameter Configuration
- **Input Resolution**: $1024 \times 1024$ px.
- **Optimization**: AdamW optimizer ($lr_0 = 1 \times 10^{-3}$, $lr_f = 1 \times 10^{-2}$, weight decay $= 5 \times 10^{-4}$, cosine decay schedule over 120 epochs with 5 warmup epochs; batch size $= 8$).
- **Loss Formulation**: Box regression ($\lambda_{box} = 7.5$), classification ($\lambda_{cls} = 0.55$), distribution focal loss ($\lambda_{dfl} = 1.5$), with prototype mask loss.
- **Data Augmentation**: Mosaic ($0.9$), Copy-Paste ($0.2$), scale jitter ($\pm 50\%$), rotation ($\pm 15^\circ$), horizontal flip ($p = 0.5$), and vertical flip ($p = 0.2$).

### 3.3. Rationale for the Joint Multi-Domain Strategy

Prior to architecture-level benchmarking, two fine-tuning paradigms were evaluated on the YOLO26-seg baseline:
1. **Separated Pipeline**: Domain-isolated models for Coffee (4 classes) and Rice (3 classes) gated by an upstream classifier.
2. **Joint Multi-Domain Pipeline**: A single consolidated model trained over all 7 classes simultaneously.

```mermaid
flowchart LR
    subgraph S1["Separated Pipeline (Cascaded)"]
        In1[Input Image] --> Cls[Domain Classifier]
        Cls -->|Coffee| MC[Coffee Model<br/>11.0 MB]
        Cls -->|Rice| MR[Rice Model<br/>11.0 MB]
    end

    subgraph S2["Joint Pipeline (Unified)"]
        In2[Input Image] --> MJ[Joint Model<br/>11.0 MB]
        MJ --> Out[7-Class Diagnoses]
    end
```

#### Table 3.1: Task Fidelity Across Agricultural Domains

| Target Domain | Evaluation Metric / Class | Separated Baseline | Joint Multi-Domain | $\Delta$ (Joint - Sep) | Relative Change |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Coffee** | Domain Mask mAP@50 | **0.7281** | 0.7194 | -0.0087 | -1.2% (98.8% retention) |
| | Domain Mask mAP@50:95 | **0.7234** | 0.7151 | -0.0083 | -1.1% (98.9% retention) |
| | `LeafMiner` AP@50 | 0.5378 | **0.5855** | +0.0477 | +8.9% |
| | `Rust` AP@50 | 0.7793 | **0.7799** | +0.0006 | +0.1% |
| | `AlgalLeafSpot` AP@50 | **0.7535** | 0.7497 | -0.0038 | -0.5% |
| | `PowderyMildew` AP@50 | **0.8416** | 0.7624 | -0.0792 | -9.4% |
| **Rice** | Domain Mask mAP@50 | 0.3587 | **0.4803** | **+0.1216** | **+33.9%** |
| | Domain Mask mAP@50:95 | 0.3516 | **0.4712** | **+0.1196** | **+34.0%** |
| | `Hispa` AP@50 | 0.1731 | **0.4388** | **+0.2657** | **+153.5%** |
| | `LeafBlast` AP@50 | 0.4816 | **0.5402** | +0.0586 | +12.2% |
| | `BrownSpot` AP@50 | 0.4215 | **0.4618** | +0.0403 | +9.6% |

#### Table 3.2: Operational Viability and Serving Characteristics

| Evaluation Dimension | Separated Pipeline | Joint Pipeline | Comparative Delta / Effect |
| :--- | :---: | :---: | :--- |
| **Combined Mask mAP@50 (COCO)** | — *(Partitioned)* | **0.6169** | Single-pass multi-domain benchmark |
| **Combined Mask mAP@50:95 (COCO)** | — *(Partitioned)* | **0.6106** | Native multi-scale localization |
| **Semantic Overlap (mIoU / Dice)** | — | **0.6986 / 0.8155** | Global pixel overlap across all test data |
| **Background Clean Rate ($BCR$)** | 50.48% (Rice) / 0.00% (Coffee) | **80.29% (167/208)** | $\Delta = +29.81\text{ pp}$ false-positive reduction |
| **Operating Threshold ($conf$)** | 0.55 (Coffee) / 0.60 (Rice) | **0.50** | Single calibrated operating point |
| **Inference Latency (CPU, $1024^2$)** | 211.92 ms / 270.64 ms | **205.35 ms** | $-3.1\%$ to $-24.1\%$ latency reduction |
| **Active Memory Footprint (ONNX)** | 22.0 MB (2 $\times$ 11.0 MB) | **11.0 MB (1 $\times$ 11.0 MB)** | $-50\%$ memory allocation |
| **Pipeline Failure Modes** | Triage error propagation | **Zero routing overhead** | Eliminates cascading triage risk |

#### Empirical Analysis

1. **Cross-Domain Feature Transfer**:
   Rice foliar lesions exhibit low contrast, irregular spatial extents, and high background interference on narrow blades. Joint training enables early convolutional layers to share spatial feature representations (chlorotic halos, necrotic margins) learned across both leaf morphologies. This yields a $+0.1216$ increase in Rice Mask $mAP@50$, driven primarily by `Hispa` ($\Delta = +0.2657$). Coffee performance demonstrates high stability, retaining $98.8\%$ of domain mask $mAP@50$ ($0.7281 \to 0.7194$).
2. **False-Positive Suppression on Negative Controls**:
   Healthy leaves present diverse venation and natural discolorations that trigger false detections in domain-isolated models ($BCR = 50.48\%$ on Rice). Co-training provides diverse negative supervision across both crop species, increasing $BCR$ to $80.29\%$ ($\Delta = +29.81\text{ pp}$).
3. **Operational Simplicity**:
   A separated deployment introduces an architectural dependency on an upstream crop-triage classifier. Triage errors directly cause out-of-domain failure in the downstream disease segmenter. The Joint architecture processes arbitrary input leaves in a single forward pass, eliminates intermediate routing latency, and halves active container memory from $22.0\text{ MB}$ to $11.0\text{ MB}$.
---

## 4. Empirical Results and Comparative Benchmark

### 4.1. Comparative Benchmark on Held-Out Test Set ($N = 648$)

Evaluation is conducted at full native resolution with non-maximum suppression ($IoU_{NMS} = 0.70$) and calibrated operating threshold ($conf = 0.50$).

| Architecture | Paradigm | Mask mAP@50 | Mask mAP@50:95 | Box mAP@50 | Box mAP@50:95 | mIoU | Dice | Background Clean Rate | CPU Latency (ms) | Checkpoint Size |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **YOLO26n-seg (Joint)** | Single-Stage CNN | **0.6169** | **0.6106** | **0.6169** | **0.6011** | **0.6986** | **0.8155** | **80.29%** | **205.35** | **11.0 MB (ONNX)** |
| **RF_DETR** | Query Transformer | — | — | — | — | — | — | — | — | — |
| **Mask R-CNN** | Two-Stage CNN | — | — | — | — | — | — | — | — | — |

*Note: Results for RF_DETR and Mask R-CNN will be integrated upon completion of ongoing training runs.*

### 4.2. Granular Class-Wise Breakdown (Joint Model)

| Domain | Pathology Class | Target Morphology | Mask mAP@50 | Mask mAP@50:95 | Box mAP@50 | Class IoU |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Coffee** | `LeafMiner` | Serpentine serpentine mines | 0.5855 | 0.5855 | 0.5855 | 0.7129 |
| **Coffee** | `PowderyMildew` | White superficial powdery patches | 0.7624 | 0.7624 | 0.7624 | 0.8344 |
| **Coffee** | `Rust` | Orange powdery pustules | 0.7799 | 0.7799 | 0.7799 | 0.8423 |
| **Coffee** | `AlgalLeafSpot` | Circular rust-colored necrotic spots | 0.7497 | 0.7497 | 0.7497 | 0.8080 |
| **Rice** | `BrownSpot` | Small oval dark brown lesions | 0.4618 | 0.4618 | 0.4618 | 0.6506 |
| **Rice** | `Hispa` | Elongate chlorotic feeding streaks | 0.4388 | 0.4388 | 0.4388 | 0.5299 |
| **Rice** | `LeafBlast` | Spindle-shaped necrotic centers | 0.5402 | 0.5402 | 0.5402 | 0.5123 |
| **Summary** | **Coffee Domain ($N = 187$)** | Broad-leaf foliage | **0.7194** | **0.7151** | **0.7194** | **0.7994** |
| **Summary** | **Rice Domain ($N = 461$)** | Narrow graminoid foliage | **0.4803** | **0.4712** | **0.4803** | **0.5643** |

---

## 5. Serving Optimization & Deployment Specification

To enable CPU deployment without PyTorch framework dependencies, the Joint checkpoint is exported to ONNX (opset 17).

- **Inference Specification**: Input tensor $\mathbf{X} \in \mathbb{R}^{1 \times 3 \times 1024 \times 1024}$, normalized to $[0, 1]$ via letterbox transformation. Output consists of bounding box predictions, 7-class probability distributions, and 32 prototype mask coefficients.
- **Operating Calibration**: Optimal operating point locked at $conf = 0.50$ via empirical validation Mask-F1 curve analysis.
- **Quantization Protocol**: Checkpoints are maintained in FP32 format for architecture benchmarking. Post-selection, INT8 dynamic and static quantization are benchmarked directly on the host CPU execution environment to evaluate hardware-specific throughput gains against fidelity degradation.
