import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# Increase the limit to avoid DecompressionBombError for very large crawled images
Image.MAX_IMAGE_PIXELS = None

RICE_LABELS = ["Healthy", "BrownSpot", "Hispa", "LeafBlast", "Invalid"]

RICE_LABEL_VN = {
    "Healthy": "Khỏe mạnh",
    "BrownSpot": "Đốm nâu",
    "Hispa": "Sâu gai",
    "LeafBlast": "Bệnh đạo ôn",
    "Invalid": "Không hợp lệ",
}

COFFEE_LABELS = ["LeafMiner", "PowderyMildew", "Rust", "AlgalLeafSpot", "Invalid"]

COFFEE_LABEL_VN = {
    "LeafMiner": "Bệnh sâu vẽ bùa",
    "PowderyMildew": "Bệnh phấn trắng",
    "Rust": "Bệnh nấm rỉ sắt",
    "AlgalLeafSpot": "Bệnh đốm rong",
    "Invalid": "Không hợp lệ",
}

RICE_BADGE_COLOR = {
    "Healthy": ("#16a34a", "#ffffff"),
    "BrownSpot": ("#92400e", "#ffffff"),
    "Hispa": ("#7c3aed", "#ffffff"),
    "LeafBlast": ("#b91c1c", "#ffffff"),
    "Invalid": ("#6b7280", "#ffffff"),
}

COFFEE_BADGE_COLOR = {
    "LeafMiner": ("#ea580c", "#ffffff"),
    "PowderyMildew": ("#14b8a6", "#ffffff"),
    "Rust": ("#b91c1c", "#ffffff"),
    "AlgalLeafSpot": ("#16a34a", "#ffffff"),
    "Invalid": ("#6b7280", "#ffffff"),
}


def _build_highlight_css(human_col: int | None, ai_col: int | None) -> str:
    """Build CSS to highlight the human-selected label (solid blue) and AI prediction (blue outline)."""
    rules: list[str] = []

    base_selector = 'div[data-testid="stColumn"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]'

    rules.append(
        f"{base_selector} button {{"
        "  transition: all 0.2s ease-in-out;"
        "  white-space: pre-line !important;"
        "  min-height: 5rem !important;"
        "  line-height: 1.2 !important;"
        "  padding: 0.5rem !important;"
        "}"
    )

    # AI prediction – subtle blue outline/glow
    if ai_col is not None and ai_col != human_col:
        rules.append(
            f"{base_selector}:nth-child({ai_col}) button {{"
            "  background-color: rgba(59, 130, 246, 0.08) !important;"
            "  color: #3b82f6 !important;"
            "  border: 2px solid #3b82f6 !important;"
            "  font-weight: 600 !important;"
            "  box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);"
            "}"
        )

    # Human-selected label – solid primary blue (takes priority)
    if human_col is not None:
        rules.append(
            f"{base_selector}:nth-child({human_col}) button {{"
            "  background-color: #3b82f6 !important;"
            "  color: #ffffff !important;"
            "  border-color: #2563eb !important;"
            "  font-weight: 700 !important;"
            "  box-shadow: 0 0 15px rgba(59, 130, 246, 0.45);"
            "  transform: translateY(-1px);"
            "}"
        )

    return "<style>\n" + "\n".join(rules) + "\n</style>"


def _apply_edits(img: Image.Image, rotate: float, crop_pct: tuple[float, float, float, float]) -> Image.Image:
    """Apply rotation and crop to a PIL image.

    Args:
        img: Source PIL image.
        rotate: Degrees to rotate counter-clockwise (negative = clockwise).
        crop_pct: (left%, top%, right%, bottom%) each in [0, 50].

    Returns:
        Edited PIL image.
    """
    if rotate != 0:
        img = img.rotate(rotate, expand=True)

    cl, ct, cr, cb = crop_pct
    w, h = img.size
    left = int(w * cl / 100)
    top = int(h * ct / 100)
    right = w - int(w * cr / 100)
    bottom = h - int(h * cb / 100)
    # Guard against degenerate crops
    if right > left and bottom > top:
        img = img.crop((left, top, right, bottom))

    return img


class DatasetLabeler:
    """Manages the labeling session: loading data, tracking labels, and persistence."""

    def __init__(self, input_path: str, dataset_type: str = "rice"):
        self._input_path = Path(input_path)
        self.dataset_type = dataset_type
        if dataset_type == "coffee":
            self.labels_list = COFFEE_LABELS
            self.label_vn = COFFEE_LABEL_VN
            self.badge_color = COFFEE_BADGE_COLOR
            self.title = "☕ Coffee Disease Labeler"
        else:
            self.labels_list = RICE_LABELS
            self.label_vn = RICE_LABEL_VN
            self.badge_color = RICE_BADGE_COLOR
            self.title = "🌾 Rice Disease Labeler"
        self._init_state()

    def _init_state(self):
        """Load the dataset into session state once."""
        if "records" not in st.session_state:
            st.session_state.records = self._load_input(self._input_path)
            st.session_state.labels = self._extract_existing_labels(st.session_state.records)
            st.session_state.index = self._first_unlabeled_index()
        # Per-image edit params: {idx: {"rotate": 0.0, "crop_left": 0.0, ...}}
        if "edits" not in st.session_state:
            st.session_state.edits = {}

    @property
    def records(self) -> list[dict]:
        return st.session_state.records

    @property
    def labels(self) -> dict[int, str]:
        return st.session_state.labels

    @property
    def index(self) -> int:
        return st.session_state.index

    @index.setter
    def index(self, value: int):
        if not self.records:
            st.session_state.index = 0
            return
        st.session_state.index = max(0, min(value, len(self.records) - 1))

    # I/O helpers

    @staticmethod
    def _load_input(path: Path) -> list[dict]:
        """Load data from JSON (array) or JSONL (one object per line)."""
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return []
        # Detect format: JSON array starts with '[', JSONL does not
        if content.startswith("["):
            return json.loads(content)
        else:
            return [json.loads(line) for line in content.splitlines() if line.strip()]

    @staticmethod
    def _extract_existing_labels(records: list[dict]) -> dict[int, str]:
        """Pull existing labels from annotations (priority) or AI predictions."""
        labels: dict[int, str] = {}
        for i, rec in enumerate(records):
            # 1. Try human annotations first
            annots = rec.get("annotations", [])
            if annots:
                if annots[0].get("was_cancelled"):
                    labels[i] = "Invalid"
                    continue

                result = annots[0].get("result", [])
                if result:
                    choices = result[0].get("value", {}).get("choices", [])
                    if choices:
                        labels[i] = choices[0]
                        continue

            # 2. Fall back to AI predictions
            preds = rec.get("predictions", [])
            if preds:
                result = preds[0].get("result", [])
                if result:
                    choices = result[0].get("value", {}).get("choices", [])
                    if choices:
                        labels[i] = choices[0]
        return labels

    def _first_unlabeled_index(self) -> int:
        for i in range(len(self.records)):
            if i not in self.labels:
                return i
        return 0

    def get_ai_prediction(self, idx: int) -> str | None:
        """Return the AI prediction for a record, if any.

        First checks the 'predictions' field.  If absent, infers the class
        from the parent folder name of the image (e.g. images/LeafBlast/img.png).
        """
        rec = self.records[idx]

        # 1. Explicit predictions field
        preds = rec.get("predictions", [])
        if preds:
            choices = preds[0].get("result", [{}])[0].get("value", {}).get("choices", [])
            if choices:
                return choices[0]

        # 2. Infer from image folder name
        image_path = rec.get("data", {}).get("image", "")
        if image_path:
            folder_name = Path(image_path).parent.name
            if folder_name in self.labels_list:
                return folder_name

        return None

    def export_results(self, include_unlabeled: bool = False) -> list[dict]:
        """Build Label-Studio-compatible JSON records with human annotations."""
        output = []
        for i, rec in enumerate(self.records):
            label = self.labels.get(i)
            # Always skip "Invalid" images
            if label == "Invalid":
                continue

            # If not including unlabeled, skip images without a human label
            if not include_unlabeled and not label:
                continue

            entry = {"data": rec["data"]}
            if label:
                entry["annotations"] = [
                    {
                        "result": [
                            {
                                "from_name": "choice",
                                "to_name": "image",
                                "type": "choices",
                                "value": {"choices": [label]},
                            }
                        ]
                    }
                ]

            # Keep original predictions for reference
            if "predictions" in rec:
                entry["predictions"] = rec["predictions"]
            output.append(entry)
        return output

    def export_zip(self, include_unlabeled: bool = False) -> bytes:
        """Build a ZIP file containing labeled_output.json + all valid images under images/.

        Image paths in the JSON are rewritten to relative 'images/<filename>'.

        Returns:
            ZIP file contents as bytes.
        """
        valid_records = self.export_results(include_unlabeled=include_unlabeled)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            json_entries = []
            for entry in valid_records:
                img_path = Path(entry["data"].get("image", ""))
                if img_path.exists():
                    # Use only the filename to avoid path conflicts
                    img_filename = img_path.name
                    zf.write(img_path, arcname=f"images/{img_filename}")
                    # Rewrite path to relative form
                    new_entry = dict(entry)
                    new_entry["data"] = dict(entry["data"])
                    new_entry["data"]["image"] = f"images/{img_filename}"
                    json_entries.append(new_entry)
                else:
                    # Include in JSON even if file is missing, skip image
                    json_entries.append(entry)

            json_bytes = json.dumps(json_entries, indent=2, ensure_ascii=False).encode("utf-8")
            zf.writestr("labeled_output.json", json_bytes)

        return buf.getvalue()

    def import_results(self, content: str):
        """Import previously exported labels back into the session.
        Handles both JSON (array) and JSONL (one object per line) formats.
        """
        content = content.strip()
        if content.startswith("["):
            imported = json.loads(content)
        else:
            imported = [json.loads(line) for line in content.splitlines() if line.strip()]

        # Precompute maps for faster matching
        path_to_idx = {rec["data"]["image"]: i for i, rec in enumerate(self.records)}
        name_to_idx = {Path(rec["data"]["image"]).name: i for i, rec in enumerate(self.records)}

        count = 0
        for entry in imported:
            img = entry.get("data", {}).get("image")
            if not img:
                continue

            # 1. Try exact path match
            idx = path_to_idx.get(img)

            # 2. If no exact match, try matching by filename (handles path differences)
            if idx is None:
                idx = name_to_idx.get(Path(img).name)

            if idx is None:
                continue

            annots = entry.get("annotations", [])
            if annots:
                if annots[0].get("was_cancelled"):
                    self.labels[idx] = "Invalid"
                    count += 1
                else:
                    result = annots[0].get("result", [])
                    if result:
                        choices = result[0].get("value", {}).get("choices", [])
                        if choices:
                            self.labels[idx] = choices[0]
                            count += 1
        return count

    # Navigation callbacks

    def _go_prev(self):
        if self.index > 0:
            self.index = self.index - 1

    def _go_next(self):
        if self.index < len(self.records) - 1:
            self.index = self.index + 1

    def _select_label(self, label: str):
        self.labels[self.index] = label

    def _get_edit_params(self, idx: int) -> dict:
        """Return the edit params dict for this index, initialising if needed."""
        if idx not in st.session_state.edits:
            st.session_state.edits[idx] = {
                "rotate": 0.0,
                "crop_left": 0.0,
                "crop_top": 0.0,
                "crop_right": 0.0,
                "crop_bottom": 0.0,
            }
        return st.session_state.edits[idx]

    def _detect_duplicates(self):
        """Identify exact duplicates by MD5 hash and mark them as Invalid."""
        seen_hashes = {}  # hash -> first_index
        duplicates_found = 0

        progress_text = "🔍 Scanning for duplicates..."
        progress_bar = st.progress(0, text=progress_text)

        for i, rec in enumerate(self.records):
            img_path = Path(rec["data"]["image"])
            if not img_path.exists():
                continue

            try:
                # Calculate MD5 hash of the file
                with open(img_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                if file_hash in seen_hashes:
                    # Duplicate found - mark as Invalid unless it already has a human label
                    # (Though usually we want to mask all duplicates)
                    self.labels[i] = "Invalid"
                    duplicates_found += 1
                else:
                    seen_hashes[file_hash] = i
            except Exception:
                continue

            # Update progress bar occasionally
            if i % 10 == 0 or i == len(self.records) - 1:
                progress_bar.progress(
                    (i + 1) / len(self.records), text=f"{progress_text} ({i + 1}/{len(self.records)})"
                )

        progress_bar.empty()
        return duplicates_found

    def _save_edited_image(self, idx: int) -> Path | None:
        """Apply current edits for `idx` and save next to the original.

        Returns the path to the saved edited file, or None on failure.
        """
        rec = self.records[idx]
        data = rec["data"]

        # Always edit from the original source to avoid cumulative degradation
        original_path = Path(data.get("image_original") or data.get("image", ""))
        if not original_path.exists():
            return None

        params = self._get_edit_params(idx)
        try:
            img = Image.open(original_path)
            img = _apply_edits(
                img,
                rotate=params["rotate"],
                crop_pct=(
                    params["crop_left"],
                    params["crop_top"],
                    params["crop_right"],
                    params["crop_bottom"],
                ),
            )
        except Exception:
            return None

        # Derive edited path: <stem>_edited<suffix>
        edited_path = original_path.with_name(original_path.stem + "_edited" + original_path.suffix)

        try:
            img.save(edited_path)
        except Exception:
            return None

        # Persist original path so we can revert later
        if "image_original" not in data:
            data["image_original"] = str(original_path)
        # Point the record to the edited file
        data["image"] = str(edited_path)
        return edited_path

    def _revert_image(self, idx: int):
        """Restore the record's image path to the original."""
        data = self.records[idx]["data"]
        original = data.get("image_original")
        if original:
            data["image"] = original
        # Reset edit params
        st.session_state.edits[idx] = {
            "rotate": 0.0,
            "crop_left": 0.0,
            "crop_top": 0.0,
            "crop_right": 0.0,
            "crop_bottom": 0.0,
        }

    # UI rendering

    def render(self):
        st.set_page_config(page_title=self.title, layout="wide")
        st.title(self.title)

        self._render_sidebar()
        self._inject_keyboard_nav()

        tab_label, tab_gallery = st.tabs(["🏷️ Labeler", "🖼️ Gallery"])
        with tab_label:
            self._render_main()
        with tab_gallery:
            self._render_gallery()

    def _render_sidebar(self):
        with st.sidebar:
            total = len(self.records)
            labeled = len(self.labels)
            st.metric("Progress (labeled images)", f"{labeled} / {total}")
            st.progress(labeled / total if total else 0)

            # Per-label counts
            counts = {}
            for lbl in self.labels.values():
                counts[lbl] = counts.get(lbl, 0) + 1
            if counts:
                st.markdown("**Label distribution:**")
                for lbl in self.labels_list:
                    if lbl in counts:
                        vn = self.label_vn.get(lbl, "")
                        st.write(f"- {lbl} ({vn}): **{counts[lbl]}**")

            st.divider()

            # Import / Export
            st.subheader("Import / Export")

            # Export Mode selection
            export_mode = st.radio(
                "Export Mode",
                ["Only labeled", "Labeled + Unlabeled"],
                help="Choose whether to include unlabeled images in the export. 'Invalid' images are always excluded.",
                key="export_mode",
            )
            include_unlabeled = export_mode == "Labeled + Unlabeled"

            # JSON-only export (kept)
            export_data = self.export_results(include_unlabeled=include_unlabeled)
            export_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Export labels (.json)",
                data=export_str,
                file_name="labeled_output.json",
                mime="application/json",
            )

            # ZIP export — JSON + images subfolder
            valid_count = len(export_data)
            zip_label = f"📦 Export dataset (.zip)  [{valid_count} images]"
            st.download_button(
                zip_label,
                data=self.export_zip(include_unlabeled=include_unlabeled),
                file_name="labeled_output.zip",
                mime="application/zip",
            )

            uploaded = st.file_uploader("📤 Import labels (.json, .jsonl)", type=["json", "jsonl"])
            if uploaded is not None:
                count = self.import_results(uploaded.read().decode("utf-8"))
                st.success(f"Imported {count} labels.")
                st.rerun()

            st.divider()
            st.subheader("Tools")
            if st.button(
                "🔍 Detect Duplicates", width="stretch", help="Mark bit-for-bit identical images as 'Invalid'"
            ):
                dups = self._detect_duplicates()
                if dups > 0:
                    st.success(f"Found and masked {dups} duplicate images.")
                    st.rerun()
                else:
                    st.info("No duplicates found.")

    def _render_main(self):
        if not self.records:
            st.warning("⚠️ No image records found in the dataset.")
            st.info(
                f"Dataset path: `{self._input_path}`\n\n"
                f"To generate crawled data, run:\n"
                f"```bash\npython -m crawl.pipeline --crop {self.dataset_type}\n```"
            )
            return

        idx = self.index
        rec = self.records[idx]
        data = rec["data"]
        # Navigation buttons using on_click callbacks
        col_prev, col_info, col_next = st.columns([1, 4, 1])
        with col_prev:
            st.button(
                "⬅ Prev",
                width="stretch",
                on_click=self._go_prev,
                disabled=(idx == 0),
            )
        with col_info:
            st.markdown(
                f"<h4 style='text-align:center; margin:0;'>Image {idx + 1} of {len(self.records)}</h4>",
                unsafe_allow_html=True,
            )
        with col_next:
            st.button(
                "Next ➡",
                width="stretch",
                on_click=self._go_next,
                disabled=(idx == len(self.records) - 1),
            )

        # Image + labeling side by side
        col_img, col_label = st.columns([3, 2])

        with col_img:
            img_path = Path(data["image"])
            if img_path.exists():
                st.image(str(img_path), width="stretch")
            else:
                st.error(f"Image not found: {img_path}")

            # Image editor
            self._render_image_editor(idx)

        with col_label:
            ai_pred = self.get_ai_prediction(idx)
            current_label = self.labels.get(idx)

            if ai_pred:
                vn_pred = self.label_vn.get(ai_pred, "")
                st.info(f"🤖 AI prediction: **{ai_pred}** ({vn_pred})")

            # Highlight human label (green) and AI prediction (blue)
            human_col = (
                (self.labels_list.index(current_label) + 1)
                if (current_label and current_label in self.labels_list)
                else None
            )
            ai_col = (self.labels_list.index(ai_pred) + 1) if (ai_pred and ai_pred in self.labels_list) else None
            if human_col or ai_col:
                st.markdown(_build_highlight_css(human_col, ai_col), unsafe_allow_html=True)

            # Label buttons
            st.markdown("**Choose label:**")
            btn_cols = st.columns(len(self.labels_list))
            for j, lbl in enumerate(self.labels_list):
                with btn_cols[j]:
                    vn_name = self.label_vn.get(lbl, "")
                    st.button(
                        f"{lbl}\n{vn_name}",
                        key=f"lbl_{lbl}_{idx}",
                        width="stretch",
                        on_click=self._select_label,
                        args=(lbl,),
                    )

            # Source info
            st.divider()
            st.caption(f"**Source:** {data.get('source_url', 'N/A')}")
            context = data.get("context", "")
            if context:
                with st.expander("📝 Context text", expanded=False):
                    st.write(context[:1000])

    def _render_image_editor(self, idx: int):
        """Render the collapsible image editor panel below the current image."""
        params = self._get_edit_params(idx)
        data = self.records[idx]["data"]
        original_path = Path(data.get("image_original") or data.get("image", ""))
        has_edits = bool(data.get("image_original"))  # original_path stored → edits were saved at least once

        with st.expander("✏️ Edit Image", expanded=False):
            # Controls
            rotate = st.slider(
                "Rotate (°)",
                min_value=-180.0,
                max_value=180.0,
                value=params["rotate"],
                step=1.0,
                key=f"edit_rotate_{idx}",
            )
            params["rotate"] = rotate

            st.markdown("**Crop (% from each edge)**")
            c1, c2 = st.columns(2)
            with c1:
                crop_left = st.slider("Left %", 0.0, 99.0, params["crop_left"], 0.5, key=f"edit_cl_{idx}")
                crop_top = st.slider("Top %", 0.0, 99.0, params["crop_top"], 0.5, key=f"edit_ct_{idx}")
            with c2:
                crop_right = st.slider("Right %", 0.0, 99.0, params["crop_right"], 0.5, key=f"edit_cr_{idx}")
                crop_bottom = st.slider("Bottom %", 0.0, 99.0, params["crop_bottom"], 0.5, key=f"edit_cb_{idx}")

            params["crop_left"] = crop_left
            params["crop_top"] = crop_top
            params["crop_right"] = crop_right
            params["crop_bottom"] = crop_bottom

            # Live preview
            any_edit = rotate != 0 or any([crop_left, crop_top, crop_right, crop_bottom])
            if any_edit and original_path.exists():
                try:
                    preview = Image.open(original_path)
                    preview = _apply_edits(
                        preview,
                        rotate=rotate,
                        crop_pct=(crop_left, crop_top, crop_right, crop_bottom),
                    )
                    st.image(preview, caption="Preview", width="stretch")
                except Exception as e:
                    st.warning(f"Preview failed: {e}")

            # Action buttons
            btn_save, btn_revert = st.columns(2)
            with btn_save:
                if st.button("💾 Save edits", key=f"edit_save_{idx}", width="stretch"):
                    saved = self._save_edited_image(idx)
                    if saved:
                        st.success(f"Saved → `{saved.name}`")
                        st.rerun()
                    else:
                        st.error("Save failed. Check the image path.")

            with btn_revert:
                revert_disabled = not has_edits
                if st.button(
                    "↩ Revert to original",
                    key=f"edit_revert_{idx}",
                    width="stretch",
                    disabled=revert_disabled,
                ):
                    self._revert_image(idx)
                    st.success("Reverted to original image.")
                    st.rerun()

            if has_edits:
                edited_name = Path(data["image"]).name
                st.caption(f"✅ Active edit: `{edited_name}`")

    def _inject_keyboard_nav(self):
        """Inject JavaScript to listen for keyboard shortcuts and update query-params."""
        params = st.query_params
        nav = params.get("nav", None)
        label_idx = params.get("label", None)

        if nav == "prev":
            self._go_prev()
            st.query_params.clear()
            st.rerun()
        elif nav == "next":
            self._go_next()
            st.query_params.clear()
            st.rerun()
        elif label_idx is not None:
            try:
                l_idx = int(label_idx)
                if 0 <= l_idx < len(self.labels_list):
                    self._select_label(self.labels_list[l_idx])
                    # Auto-advance after labeling
                    self._go_next()
            except (ValueError, IndexError):
                pass
            st.query_params.clear()
            st.rerun()

        # Inject JS listener
        # - ArrowLeft / h / H: Previous
        # - ArrowRight / l / L: Next
        # - 1-9: Select label N (1-indexed) and advance
        components.html(
            """
            <script>
            (function() {
                const win = window.parent;
                if (win.__keyNavAttached) return;
                win.__keyNavAttached = true;
                win.addEventListener('keydown', function(e) {
                    if (e.target.tagName === 'INPUT' ||
                        e.target.tagName === 'TEXTAREA' ||
                        e.target.isContentEditable) return;

                    const key = e.key.toLowerCase();
                    if (key === 'arrowleft' || key === 'h') {
                        win.location.href = win.location.pathname + '?nav=prev';
                    } else if (key === 'arrowright' || key === 'l') {
                        win.location.href = win.location.pathname + '?nav=next';
                    } else if (e.key >= '1' && e.key <= '9') {
                        const idx = parseInt(e.key) - 1;
                        win.location.href = win.location.pathname + '?label=' + idx;
                    }
                });
            })();
            </script>
            """,
            height=0,
        )

    def _render_gallery(self):
        """Show all images in a grid with their current label."""
        st.markdown("### 🖼️ Image Gallery")
        if not self.records:
            st.info("No images available in the gallery.")
            return
        filter_options = ["All"] + self.labels_list + ["Unlabeled"]
        col_filter, col_cols = st.columns([3, 1])
        with col_filter:
            selected_filter = st.selectbox(
                "Filter by label",
                filter_options,
                key="gallery_filter",
            )
        with col_cols:
            n_cols = st.number_input(
                "Columns",
                min_value=2,
                max_value=8,
                value=4,
                step=1,
                key="gallery_cols",
            )

        # Build filtered index list
        indices = []
        for i, _rec in enumerate(self.records):
            lbl = self.labels.get(i)
            if selected_filter == "All":
                indices.append(i)
            elif selected_filter == "Unlabeled" and lbl is None:
                indices.append(i)
            elif lbl == selected_filter:
                indices.append(i)

        if not indices:
            st.info("No images match the selected filter.")
            return

        st.caption(f"Showing {len(indices)} of {len(self.records)} images")

        # Render grid
        n_cols = int(n_cols)
        rows = [indices[i : i + n_cols] for i in range(0, len(indices), n_cols)]
        for row in rows:
            cols = st.columns(n_cols)
            for col, idx in zip(cols, row):
                rec = self.records[idx]
                img_path = Path(rec["data"]["image"])
                lbl = self.labels.get(idx)
                with col:
                    if img_path.exists():
                        st.image(str(img_path), width="stretch")
                    else:
                        st.markdown(
                            "<div style='background:#1e293b;height:120px;display:flex;"
                            "align-items:center;justify-content:center;border-radius:8px;"
                            "color:#94a3b8;font-size:0.75rem;'>No image</div>",
                            unsafe_allow_html=True,
                        )

                    # Label badge
                    if lbl:
                        bg, fg = self.badge_color.get(lbl, ("#3b82f6", "#fff"))
                        vn = self.label_vn.get(lbl, "")
                        st.markdown(
                            f"<div style='background:{bg};color:{fg};border-radius:6px;"
                            f"padding:2px 8px;font-size:0.75rem;font-weight:600;"
                            f"text-align:center;margin-top:2px;'>{lbl}<br>"
                            f"<span style='font-weight:400'>{vn}</span></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div style='background:#334155;color:#94a3b8;border-radius:6px;"
                            "padding:2px 8px;font-size:0.75rem;text-align:center;margin-top:2px;'"
                            ">Unlabeled</div>",
                            unsafe_allow_html=True,
                        )

                    # Jump to this image button
                    if st.button(
                        f"✏️ Label #{idx + 1}",
                        key=f"gallery_jump_{idx}",
                        width="stretch",
                    ):
                        self.index = idx
                        st.rerun()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Streamlit Plant Disease Labeler")
    parser.add_argument(
        "--input",
        type=str,
        default="datasets/raw/label_studio_import.json",
        help="Path to the JSON (or JSONL) file with image records",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["rice", "coffee"],
        default="rice",
        help="Type of dataset to label (rice or coffee)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    labeler = DatasetLabeler(args.input, args.type)
    labeler.render()


if __name__ == "__main__":
    main()
